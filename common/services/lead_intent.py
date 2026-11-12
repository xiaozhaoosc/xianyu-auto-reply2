"""
线索评论意图分层

功能：
1. 对采集到的评论文本做两层筛选：关键词层 + 意图分层
2. strong-明确求购/求链接/问库存；medium-价格/规格咨询；weak-闲聊砍价无效互动
3. 提供 dedupe_hash 生成（防同一评论重复入库）

只读分析用途，不含任何触达动作。
"""
from __future__ import annotations

import hashlib
import re
from typing import List, Tuple

# 强意向词：明确求购 / 求链接 / 问库存
STRONG_KEYWORDS = [
    "还有吗",
    "还有没有",
    "还有货吗",
    "求同款",
    "求类似",
    "类似的还有吗",
    "有链接吗",
    "出吗",
    "能出吗",
    "怎么出",
    "想要",
    "蹲一个",
    "蹲",
    "私我",
]

# 中意向词：价格 / 规格咨询
MEDIUM_KEYWORDS = [
    "多少钱",
    "价格",
    "包邮吗",
    "颜色",
    "型号",
    "尺寸",
    "什么版",
    "有货吗",
    "全新吗",
    "可以刀",
    "便宜点",
    "能便宜",
]

# 弱意向模式：闲聊 / 无效互动（仅 include_weak=True 时入库）
WEAK_PATTERNS = [
    "哈哈",
    "不错",
    "好看",
    "666",
    "+1",
    "顶",
]

INTENT_STRONG = "strong"
INTENT_MEDIUM = "medium"
INTENT_WEAK = "weak"

# 意图层级权重（demand_score 计算）
INTENT_WEIGHTS = {INTENT_STRONG: 3, INTENT_MEDIUM: 1, INTENT_WEAK: 0}

# 归一化：去空白 + 全角转半角（只处理常见全角问号感叹号等，保持简单）
_FULLWIDTH_MAP = str.maketrans("？！，。：；（）", "?!,.:;()")


def normalize_content(content: str) -> str:
    """评论内容归一化：去首尾空白、压缩连续空白、全角标点转半角、统一小写英文。"""
    if not content:
        return ""
    text = content.strip().translate(_FULLWIDTH_MAP)
    text = re.sub(r"\s+", " ", text)
    return text.lower()


def classify_intent(content: str) -> Tuple[str, List[str]]:
    """对单条评论做意图分层。

    Returns:
        (intent_level, 命中关键词列表)。多次命中取最高档（strong > medium > weak）。
    """
    text = normalize_content(content)
    if not text:
        return INTENT_WEAK, []

    hits = [kw for kw in STRONG_KEYWORDS if kw in text]
    if hits:
        return INTENT_STRONG, hits

    hits = [kw for kw in MEDIUM_KEYWORDS if kw in text]
    if hits:
        return INTENT_MEDIUM, hits

    return INTENT_WEAK, []


def build_dedupe_hash(item_id: str, commenter_user_id: str | None, content: str) -> str:
    """生成评论去重哈希：md5(item_id + commenter_user_id + 归一化content)。

    commenter_user_id 取不到时用空串（同商品同内容视为同一条）。
    """
    raw = f"{item_id}|{commenter_user_id or ''}|{normalize_content(content)}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def build_suggestions(item_title: str | None, item_price: str | None) -> List[str]:
    """根据线索商品生成 2~3 条人工可选话术（纯本地模板拼接，不调 AI、不联网）。

    仅作为人工跟进的参考文案，由操作者自行判断、修改后使用；
    系统不提供任何自动发送通道。
    """
    title = (item_title or "这款商品").strip()
    if len(title) > 40:
        title = title[:40] + "…"
    price_part = f"，价格 {item_price.strip()}" if item_price and item_price.strip() else ""
    return [
        f"您好，看到您在「{title}」下求同款，我这边也有类似款，可以看看我的商品列表",
        f"亲，同款我们店里有现货{price_part}，有需要的话点头像进店看看",
        "您好，这款我这边正好有，可以点击我头像进店看下同款，有问题随时问我",
    ]


__all__ = [
    "STRONG_KEYWORDS",
    "MEDIUM_KEYWORDS",
    "WEAK_PATTERNS",
    "INTENT_STRONG",
    "INTENT_MEDIUM",
    "INTENT_WEAK",
    "INTENT_WEIGHTS",
    "normalize_content",
    "classify_intent",
    "build_dedupe_hash",
    "build_suggestions",
]
