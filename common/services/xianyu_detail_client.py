"""
闲鱼商品详情客户端

功能：
1. 使用账号 Cookie 调用闲鱼网页版商品详情接口 mtop.taobao.idle.pc.detail
2. 通过统一的 mtop 调用模块处理令牌过期刷新、Session过期/风控切换账号
3. 解析卖家真实用户ID（sellerDO.sellerId）与卖家昵称，返回完整详情数据
4. fetch_comments：读取商品评论区（Phase 0 探针 / 线索池扫描专用，只读，
   接口名与字段结构待人工抓包确认）

返回结构区分四种情况：
- success=True：成功，含 seller_user_id / seller_nick / detail
- account_invalid=True：账号不可用（Session过期/验证/挤爆），调用方应切换账号
- item_invalid=True：商品级明确失败（下架/不存在/跨境等），应停止重试
- 其余：临时失败（网络异常/重试耗尽），可下次重试
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from common.services.xianyu_mtop import mtop_call

DETAIL_API = "mtop.taobao.idle.pc.detail"
DETAIL_VERSION = "1.0"

# ---------------------------------------------------------------------------
# 评论区读取（Phase 0 探针 / 线索池扫描，只读）
# ---------------------------------------------------------------------------
# 2026-09-03 抓包/直连探测结论（logs/comment_api_capture.json + mtop 直连试探）：
#   1. goofish PC 网页版商品详情页无评论区（3.5万人想要的商品也没有），详情接口
#      mtop.taobao.idle.pc.detail 的返回中也不内嵌评论正文，仅有 newComment 标志位。
#   2. 评论区为 APP 端功能，对应 mtop 接口为 mtop.taobao.idle.item.comment.list。
#      已直连验证：v1.0 存在且为唯一版本；未登录时返回
#      FAIL_BIZ_COMMON_NEED_LOGIN（需要有效登录态 Cookie 才能拿到数据）。
#   3. 入参/响应结构因当前账号 Session 过期（FAIL_SYS_SESSION_EXPIRED）暂无法确认，
#      待账号重新扫码登录后用本方法探针一次即可收敛。
# TODO: 待有效登录态确认的项：
#   - 入参分页字段风格（currentPage/pageSize 还是 page/pageSize，当前按前者）
#   - 响应中评论列表路径与条目字段映射（见 _COMMENT_LIST_PATHS/_COMMENT_FIELD_CANDIDATES）
#   - 总数字段名（totalCount/count/commentCount）
COMMENT_API = "mtop.taobao.idle.item.comment.list"  # 已直连验证存在（2026-09-03）
COMMENT_API_VERSION = "1.0"  # 已验证唯一可用版本（2.0~7.0 均不存在）

# 评论列表在返回 data 中的候选路径（TODO: 抓包确认后收敛为单一路径）
_COMMENT_LIST_PATHS = [
    ("commentList",),
    ("comments",),
    ("commentDOList",),
    ("data", "commentList"),
    ("data", "comments"),
]

# 评论条目的候选字段名（TODO: 抓包确认后收敛为确定映射）
_COMMENT_FIELD_CANDIDATES = {
    "comment_id": ("commentId", "id"),
    "commenter_name": ("commenterNick", "nick", "userNick", "userName"),
    "commenter_user_id": ("commentUserId", "userId", "commenterId"),
    "content": ("content", "commentContent", "text"),
    # 注意：该值可能是毫秒时间戳或格式化字符串，统一转 str 存储，由调用方按实际格式解析
    "comment_time": ("gmtCreate", "createTime", "commentTime"),
}


def extract_comment_list(raw_data: Any) -> list:
    """从接口返回 data 中按候选路径查找评论条目列表；找不到返回空列表。"""
    for path in _COMMENT_LIST_PATHS:
        node = raw_data
        ok = True
        for key in path:
            if not isinstance(node, dict) or key not in node:
                ok = False
                break
            node = node[key]
        if ok and isinstance(node, list):
            return node
    return []


def parse_comment_entry(entry: Any) -> Dict[str, Any]:
    """把单条原始评论解析为统一结构（候选字段名提取，抓包确认后收敛）。

    统一结构的 key 与后续 xy_lead_comments 表字段对齐：
    comment_id / commenter_name / commenter_user_id / content / comment_time，
    未命中的字段值为 None。
    """
    parsed: Dict[str, Any] = {
        "comment_id": None,
        "commenter_name": None,
        "commenter_user_id": None,
        "content": None,
        "comment_time": None,
    }
    if not isinstance(entry, dict):
        return parsed
    for field, candidates in _COMMENT_FIELD_CANDIDATES.items():
        for key in candidates:
            value = entry.get(key)
            if value not in (None, ""):
                parsed[field] = str(value)
                break
    return parsed


class XianyuItemDetailClient:
    """闲鱼商品详情客户端（单账号）"""

    def __init__(self, cookie_id: str, cookies_str: str, owner_id: Optional[int] = None, proxy: Optional[str] = None):
        self.cookie_id = cookie_id
        self.cookies_str = cookies_str
        self.owner_id = owner_id
        self.proxy = proxy

    async def get_detail(self, item_id: str) -> Dict[str, Any]:
        """调用商品详情接口。

        Returns:
            {
              success: bool,
              account_invalid: bool,   # True 表示账号不可用，应切换账号
              item_invalid: bool,      # True 表示商品级明确失败，应停止重试
              seller_user_id: str|None,
              seller_nick: str|None,
              detail: dict|None,       # 详情接口返回的 data
              error: str,
            }
        """
        result = await mtop_call(
            self.cookie_id, self.cookies_str, DETAIL_API, DETAIL_VERSION, {"itemId": str(item_id)},
            owner_id=self.owner_id,
            extra_params={"spm_cnt": "a21ybx.item.0.0"},
        )
        # 令牌刷新后回写实例 Cookie
        self.cookies_str = result.get("cookies_str", self.cookies_str)

        if result.get("success"):
            detail = (result.get("res") or {}).get("data", {}) or {}
            seller = detail.get("sellerDO") or {}
            seller_user_id = seller.get("sellerId")
            seller_nick = seller.get("nick")
            return {
                "success": True,
                "account_invalid": False,
                "item_invalid": False,
                "seller_user_id": str(seller_user_id) if seller_user_id is not None else None,
                "seller_nick": str(seller_nick) if seller_nick is not None else None,
                "detail": detail,
                "error": "",
            }

        account_invalid = bool(result.get("account_invalid"))
        # 拿到了服务端业务失败响应且非账号问题 -> 商品级明确失败（下架/不存在/跨境等），停止重试；
        # 网络异常/重试耗尽（res 为 None）视为临时失败，可下次重试
        item_invalid = (not account_invalid) and (result.get("res") is not None)
        return {
            "success": False,
            "account_invalid": account_invalid,
            "item_invalid": item_invalid,
            "seller_user_id": None,
            "seller_nick": None,
            "detail": None,
            "error": result.get("error") or "详情获取失败",
        }

    async def fetch_comments(self, item_id: str, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """调用商品评论区接口（只读，Phase 0 探针 / 线索池扫描专用）。

        风控约定（线索池模块红线）：
        - 本方法只读，不产生任何写操作；触发风控时返回 risk_triggered=True，
          调用方应立即终止本轮扫描并冷却账号，不得重试、不得走远程过风控。
        - 调用频率由上层任务控制（商品间随机间隔、全局日上限），本方法不做内部限频。

        接口已确认：mtop.taobao.idle.item.comment.list v1.0（APP 端评论区接口，需登录态）。
        入参/响应结构待有效登录态下探针收敛，见模块头部 COMMENT_API 说明。

        Returns:
            {
              success: bool,
              account_invalid: bool,   # True 表示账号不可用（Session过期/验证/挤爆）
              item_invalid: bool,      # True 表示商品级明确失败（下架/不存在等），应停止重试
              risk_triggered: bool,    # True 表示触发验证/滑块等风控（带 punish_url）
              punish_url: str,         # 仅风控时有值（探针页据此提示人工处理）
              comments: list[dict],     # 解析后的评论列表（结构见 parse_comment_entry）
              total: int,              # 评论区总数（取不到时为 0，字段名待抓包确认）
              raw: dict|None,          # 接口原始返回 data（探针页排查用）
              error: str,
            }
        """
        # 入参按常见分页形式组装（itemId + currentPage/pageSize）；
        # 字段风格待有效登录态下探针确认，见模块头部 COMMENT_API 说明
        data = {
            "itemId": str(item_id),
            "currentPage": int(page),
            "pageSize": int(page_size),
        }
        result = await mtop_call(
            self.cookie_id, self.cookies_str, COMMENT_API, COMMENT_API_VERSION, data,
            owner_id=self.owner_id,
            proxy=self.proxy,
            # TODO: extra_params 待抓包确认（详情接口用 spm_cnt，评论接口可能不同）
        )
        # 令牌刷新后回写实例 Cookie
        self.cookies_str = result.get("cookies_str", self.cookies_str)

        # mtop_call 中风控（触发验证/滑块）表现为 account_invalid=True 且带 punish_url；
        # Session过期同为 account_invalid=True 但无 punish_url，据此区分
        punish_url = result.get("punish_url") or ""

        if result.get("success"):
            raw_data = (result.get("res") or {}).get("data", {}) or {}
            comment_list = extract_comment_list(raw_data)
            # TODO: 总数字段名待抓包确认（常见候选 totalCount / count / commentCount）
            total = 0
            for total_key in ("totalCount", "count", "commentCount"):
                value = raw_data.get(total_key)
                if value is not None:
                    try:
                        total = int(value)
                    except (TypeError, ValueError):
                        total = 0
                    break
            return {
                "success": True,
                "account_invalid": False,
                "item_invalid": False,
                "risk_triggered": False,
                "punish_url": "",
                "comments": [parse_comment_entry(entry) for entry in comment_list],
                "total": total,
                "raw": raw_data,
                "error": "",
            }

        account_invalid = bool(result.get("account_invalid"))
        # 评论接口需要登录态：FAIL_BIZ_COMMON_NEED_LOGIN 表示当前 Cookie 未登录
        # （区别于 Session 过期），同样应切换账号/重新登录而非视为商品失败
        ret_list = ((result.get("res") or {}).get("ret")) or []
        if any("NEED_LOGIN" in str(r) for r in ret_list):
            account_invalid = True
        item_invalid = (not account_invalid) and (result.get("res") is not None)
        return {
            "success": False,
            "account_invalid": account_invalid,
            "item_invalid": item_invalid,
            "risk_triggered": bool(punish_url),
            "punish_url": punish_url,
            "comments": [],
            "total": 0,
            "raw": None,
            "error": result.get("error") or "评论获取失败",
        }


__all__ = ["XianyuItemDetailClient"]
