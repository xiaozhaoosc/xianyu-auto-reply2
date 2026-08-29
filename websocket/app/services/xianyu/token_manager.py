"""
Token管理模块

功能:
1. Token刷新循环
2. Cookie刷新循环
3. 浏览器Cookie刷新
4. Token验证
"""
import asyncio
import os
import time
from loguru import logger


class TokenManager:
    """Token管理器"""

    # 滑块/风控类失败状态：命中这些状态时按退避阶梯拉长重试间隔，避免高频触发风控
    _CAPTCHA_BACKOFF_STATUSES = frozenset({
        "failed_captcha",
        "failed_captcha_max_retries",
        "failed_captcha_exception",
        "skipped_risk_control_processing",
        "skipped_local_slider_disabled",
        "skipped_local_slider_config_unavailable",
    })

    @staticmethod
    def _load_cookie_refresh_interval() -> int:
        """读取Cookie刷新间隔（秒）。环境变量 COOKIE_REFRESH_INTERVAL 可覆盖，默认10800（3小时）"""
        try:
            return max(int(os.getenv("COOKIE_REFRESH_INTERVAL", "10800")), 300)
        except (TypeError, ValueError):
            return 10800

    def _effective_cookie_interval(self) -> int:
        """根据连续失败次数计算当前生效的等待间隔（退避阶梯：1h→2h→3h，按基础间隔的1/3、2/3、1倍）"""
        if self.cookie_consecutive_failures <= 0:
            return self.cookie_refresh_interval
        idx = min(self.cookie_consecutive_failures - 1, len(self.cookie_failure_backoff) - 1)
        return self.cookie_failure_backoff[idx]
    
    def __init__(self, xianyu_instance):
        """
        初始化Token管理器
        
        Args:
            xianyu_instance: XianyuAsync实例的引用
        """
        self.xianyu = xianyu_instance
        self.cookie_id = xianyu_instance.cookie_id
        
        # Token配置
        self.token_refresh_interval = xianyu_instance.token_refresh_interval
        self.token_retry_interval = xianyu_instance.token_retry_interval
        self.last_token_refresh_time = 0
        self.current_token = None
        
        # Cookie刷新配置
        # 间隔可通过环境变量 COOKIE_REFRESH_INTERVAL 覆盖（秒），默认 3 小时。
        # 原硬编码 180 秒（3分钟）导致滑块被高频触发：实测单日刷新2964次、滑块332次、人工验证不断。
        self.cookie_refresh_interval = self._load_cookie_refresh_interval()
        # 滑块/风控失败退避阶梯：失败后等待 = 基础间隔的 1/3 → 2/3 → 1 倍（默认即 1h→2h→3h 封顶）
        base = self.cookie_refresh_interval
        self.cookie_failure_backoff = (max(base // 3, 300), max(base * 2 // 3, 600), base)
        self.cookie_consecutive_failures = 0  # 连续滑块/风控失败次数（供退避计算）
        self.last_cookie_refresh_time = 0
        self.cookie_refresh_lock = asyncio.Lock()
        self.cookie_refresh_enabled = True
        
        # 消息接收标识 - 用于控制Cookie刷新
        self.last_message_received_time = 0
        self.message_cookie_refresh_cooldown = 300  # 收到消息后5分钟内不执行Cookie刷新
        
        # 扫码登录Cookie刷新标志
        self.last_qr_cookie_refresh_time = 0
        self.qr_cookie_refresh_cooldown = 600  # 扫码登录Cookie刷新后的冷却时间:10分钟
        
        # 浏览器Cookie刷新成功标志
        self.browser_cookie_refreshed = False
        self.restarted_in_browser_refresh = False
    
    async def token_refresh_loop(self):
        """Token刷新循环"""
        try:
            while True:
                try:
                    await self.xianyu._interruptible_sleep(self.token_refresh_interval)
                    
                    if time.time() - self.last_token_refresh_time >= self.token_refresh_interval:
                        await self.xianyu.refresh_token()
                        
                except asyncio.CancelledError:
                    logger.info(f"【{self.cookie_id}】Token刷新循环收到取消信号")
                    raise
                except Exception as e:
                    logger.error(f"【{self.cookie_id}】Token刷新循环异常: {str(e)}")
                    await self.xianyu._interruptible_sleep(self.token_retry_interval)
                    
        except asyncio.CancelledError:
            logger.info(f"【{self.cookie_id}】Token刷新循环已取消")
            raise
        finally:
            logger.info(f"【{self.cookie_id}】Token刷新循环已退出")
    
    async def cookie_refresh_loop(self):
        """Cookie刷新定时任务"""
        logger.info(
            f"【{self.cookie_id}】Cookie刷新循环已启动，刷新间隔: {self.cookie_refresh_interval}秒"
            f"（滑块失败后按退避阶梯 {[f'{x // 3600}h' for x in self.cookie_failure_backoff]} 拉长）"
        )
        check_count = 0
        try:
            while True:
                try:
                    check_count += 1
                    if not self.cookie_refresh_enabled:
                        logger.debug(f"【{self.cookie_id}】Cookie刷新功能已禁用,跳过执行")
                        await self.xianyu._interruptible_sleep(300)
                        continue

                    current_time = time.time()
                    effective_interval = self._effective_cookie_interval()
                    time_since_last_refresh = current_time - self.last_cookie_refresh_time

                    # 每10次检查输出一次状态日志（约10分钟）
                    if check_count % 10 == 0:
                        logger.info(f"【{self.cookie_id}】Cookie刷新状态: 距上次刷新 {int(time_since_last_refresh)}秒，当前生效间隔 {effective_interval}秒（连续失败{self.cookie_consecutive_failures}次）")

                    if time_since_last_refresh >= effective_interval:
                        time_since_last_message = current_time - self.last_message_received_time
                        if self.last_message_received_time > 0 and time_since_last_message < self.message_cookie_refresh_cooldown:
                            remaining_time = self.message_cookie_refresh_cooldown - time_since_last_message
                            logger.info(f"【{self.cookie_id}】收到消息后冷却中,还需等待 {int(remaining_time)}秒")
                        elif self.cookie_refresh_lock.locked():
                            logger.info(f"【{self.cookie_id}】Cookie刷新任务已在执行中,跳过本次触发")
                        else:
                            logger.info(f"【{self.cookie_id}】开始执行Cookie刷新任务...")
                            await self._execute_cookie_refresh(current_time)

                    await self.xianyu._interruptible_sleep(60)
                    
                except asyncio.CancelledError:
                    logger.info(f"【{self.cookie_id}】Cookie刷新循环收到取消信号,准备退出")
                    raise
                except Exception as e:
                    logger.error(f"【{self.cookie_id}】Cookie刷新循环失败: {str(e)}")
                    await self.xianyu._interruptible_sleep(60)
                    
        except asyncio.CancelledError:
            logger.info(f"【{self.cookie_id}】Cookie刷新循环已取消")
            raise
        finally:
            logger.info(f"【{self.cookie_id}】Cookie刷新循环已退出")
    
    async def _execute_cookie_refresh(self, current_time: float):
        """
        执行Cookie刷新任务
        
        Args:
            current_time: 当前时间戳
        """
        async with self.cookie_refresh_lock:
            try:
                logger.info(f"【{self.cookie_id}】开始Cookie刷新任务...")

                new_token = await self.xianyu.refresh_token()
                refresh_status = getattr(self.xianyu, "last_token_refresh_status", "") or ""

                if new_token:
                    self.last_cookie_refresh_time = current_time
                    if self.cookie_consecutive_failures > 0:
                        logger.info(f"【{self.cookie_id}】Token刷新成功，滑块失败退避计数清零（原{self.cookie_consecutive_failures}次）")
                    self.cookie_consecutive_failures = 0
                    logger.info(f"【{self.cookie_id}】Cookie刷新任务完成,Token已更新")
                elif refresh_status in (
                    "skipped_local_slider_disabled",
                    "skipped_local_slider_config_unavailable",
                    "skipped_risk_control_processing",
                    "skipped_risk_control_check_failed",
                    "skipped_startup_cache_lookup_failed",
                ):
                    self.last_cookie_refresh_time = time.time()
                    # 其中滑块/风控相关状态累计退避计数，下次按退避阶梯等待
                    if refresh_status in self._CAPTCHA_BACKOFF_STATUSES:
                        self.cookie_consecutive_failures += 1
                    effective_interval = self._effective_cookie_interval()
                    if refresh_status == "skipped_local_slider_disabled":
                        reason = "Token接口仍需滑块，但本机滑块不处理已开启"
                    elif refresh_status == "skipped_local_slider_config_unavailable":
                        reason = "本机滑块处理开关读取失败"
                    elif refresh_status == "skipped_risk_control_processing":
                        reason = "同账号已有处理中的风控任务"
                    elif refresh_status == "skipped_startup_cache_lookup_failed":
                        reason = "启动阶段读取Token缓存失败"
                    else:
                        reason = "处理中风控日志检查失败"
                    logger.warning(
                        f"【{self.cookie_id}】{reason}，"
                        f"等待下一个{int(effective_interval / 60)}分钟刷新周期"
                        f"（连续滑块/风控失败{self.cookie_consecutive_failures}次）"
                    )
                elif refresh_status in self._CAPTCHA_BACKOFF_STATUSES:
                    # 滑块验证失败（自动滑未过/人工超时/异常）：不5秒重试，直接按退避阶梯拉长
                    self.cookie_consecutive_failures += 1
                    self.last_cookie_refresh_time = time.time()
                    effective_interval = self._effective_cookie_interval()
                    logger.warning(
                        f"【{self.cookie_id}】滑块验证未通过（{refresh_status}），"
                        f"进入退避：连续失败{self.cookie_consecutive_failures}次，"
                        f"{int(effective_interval / 3600)}小时后再试"
                    )
                else:
                    logger.warning(f"【{self.cookie_id}】Cookie刷新任务失败,Token刷新未成功，5秒后立即重试")
                    # 失败后不更新 last_cookie_refresh_time，等待5秒后立即重试
                    await self.xianyu._interruptible_sleep(5)
                    logger.info(f"【{self.cookie_id}】开始重试Cookie刷新任务...")
                    retry_token = await self.xianyu.refresh_token()
                    if retry_token:
                        self.last_cookie_refresh_time = time.time()
                        logger.info(f"【{self.cookie_id}】Cookie刷新重试成功,Token已更新")
                    else:
                        logger.warning(f"【{self.cookie_id}】Cookie刷新重试仍失败,等待下一个刷新周期")
                        self.last_cookie_refresh_time = time.time()
                    
            except Exception as e:
                logger.error(f"【{self.cookie_id}】执行Cookie刷新任务异常: {str(e)}")
                self.last_cookie_refresh_time = time.time()
            finally:
                self.last_message_received_time = 0
