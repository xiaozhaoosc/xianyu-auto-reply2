"""
消息断流看门狗

背景：自动回复 IM WebSocket 出现过"僵尸连接"——断线自动重连后心跳正常、
状态 connected，但闲鱼不再下发业务消息（2026-08-30 实测 5.5 小时零解密帧，
期间买家消息全部无人回复，心跳探测无法发现）。

原理：系统有两条 IM 通道共同收消息——
1. backend-web chat_new 推送通道（前端聊天页用），每条入站买家消息会写
   Redis `watchdog:push_ts:<account_id>`
2. websocket 自动回复连接（本进程），每条解密成功的业务帧会刷新
   `MessageHandler.last_decrypt_ts`
两条通道都活着时两者时间戳接近；若推送通道持续有消息而本连接长时间零解密，
即判定僵尸连接 → 触发实例重启 + 通知告警。

安全设计：全部 fail-open——Redis 读不到、无推送证据、冷却期内都只跳过不动作；
绝不会因为看门狗自身的故障导致重启。
"""
from __future__ import annotations

import asyncio
import time

from loguru import logger

# 判定阈值：本连接连续多少秒零业务帧且期间推送通道有消息 → 判定断流
STALE_THRESHOLD_S = 600        # 10 分钟
# 巡检间隔
CHECK_INTERVAL_S = 60          # 1 分钟
# 看门狗触发的实例重启冷却（同一账号两次自动重启的最小间隔）
RESTART_COOLDOWN_S = 1800      # 30 分钟


class MessageStreamWatchdog:
    """单账号消息断流看门狗（作为 XianyuLive 的后台任务运行）

    生命周期跟随账号任务：实例重启时随其他后台任务一起被取消，新实例重建。
    """

    def __init__(self, live):
        """
        Args:
            live: XianyuLive 实例（读取连接/消息处理器状态，触发重启与通知）
        """
        self.live = live
        self.cookie_id = live.cookie_id
        self._last_watchdog_restart = 0.0  # 本实例内的重启冷却计时

    async def run(self):
        """看门狗主循环（被作为后台任务 create_task 运行）"""
        logger.info(
            f"【{self.cookie_id}】消息断流看门狗已启动: "
            f"阈值={STALE_THRESHOLD_S}s, 巡检={CHECK_INTERVAL_S}s, 重启冷却={RESTART_COOLDOWN_S}s"
        )
        try:
            while True:
                await asyncio.sleep(CHECK_INTERVAL_S)
                try:
                    await self._check_once()
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    # 看门狗自身异常绝不影响主连接
                    logger.warning(f"【{self.cookie_id}】消息断流看门狗检查异常: {e}")
        except asyncio.CancelledError:
            logger.info(f"【{self.cookie_id}】消息断流看门狗已取消")

    async def _check_once(self):
        now = time.time()

        # 证据一：推送通道（backend-web chat_new）最近一次入站买家消息时间
        try:
            from common.db.redis_client import get_redis_client
            rc = await get_redis_client()
            raw = await rc.get(f"watchdog:push_ts:{self.cookie_id}")
        except Exception as e:
            # Redis 不可用时 fail-open 跳过
            logger.debug(f"【{self.cookie_id}】看门狗读取推送证据失败，跳过: {e}")
            return
        if not raw:
            return  # 没有推送证据（但凡是买家消息都没来过），无可比对
        try:
            push_ts = float(raw)
        except (TypeError, ValueError):
            return

        # 证据二：本连接最近一次成功解密的业务帧；MessageHandler 尚未创建时
        # 用连接建立时刻作为基线（重启后旧推送不会立刻误触发）
        handler = getattr(self.live, 'message_handler', None)
        decrypt_ts = getattr(handler, 'last_decrypt_ts', 0.0) if handler else 0.0
        conn_start = getattr(self.live, '_connection_start_time', 0.0) or 0.0
        decrypt_ts = max(decrypt_ts, conn_start)

        # 判定：推送比解密新（说明断流的窗口里确有买家消息进来）
        #       且推送发生在阈值窗口内（排除几小时前的旧消息造成的误触发）
        #       且本连接已超过阈值时长无业务帧
        if not (push_ts > decrypt_ts):
            return
        if (now - push_ts) > STALE_THRESHOLD_S:
            return
        if (now - decrypt_ts) < STALE_THRESHOLD_S:
            return

        logger.warning(
            f"【{self.cookie_id}】🐕 消息断流检测到僵尸连接: "
            f"本连接 {(now - decrypt_ts) / 60:.0f} 分钟零业务帧, "
            f"期间推送通道有入站消息(最近一次 {(now - push_ts) / 60:.1f} 分钟前)"
        )

        # 重启冷却：冷却期内只告警提示，不重复重启
        if now - self._last_watchdog_restart < RESTART_COOLDOWN_S:
            logger.warning(
                f"【{self.cookie_id}】看门狗重启冷却中(还需 "
                f"{(RESTART_COOLDOWN_S - (now - self._last_watchdog_restart)) / 60:.0f} 分钟)，本次不自动重启"
            )
            return
        self._last_watchdog_restart = now

        # 先告警再重启（重启后当前实例被 CookieManager 取消）
        alert_msg = (
            f"消息断流看门狗触发：自动回复消息连接已 "
            f"{(now - decrypt_ts) / 60:.0f} 分钟未收到任何买家消息，"
            f"但期间聊天页推送通道持续收到新消息(最近一次 {(now - push_ts) / 60:.1f} 分钟前)，"
            f"判定为僵尸连接，正在自动重启该账号的消息连接。"
        )
        try:
            await self.live.send_token_refresh_notification(
                alert_msg, notification_type="message_watchdog_restart"
            )
        except Exception as e:
            logger.warning(f"【{self.cookie_id}】看门狗告警发送失败(不影响重启): {e}")

        await self.live.restart_instance(reason=alert_msg)
