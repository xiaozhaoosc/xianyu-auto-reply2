"""
浏览器管理器

管理Playwright浏览器的初始化和关闭
"""
from __future__ import annotations

import asyncio
import os
import sys
import tempfile
from typing import Any, Dict, List, Optional

from loguru import logger
from common.utils.browser_utils import ensure_playwright_browser_path, get_chromium_executable_path

# 修复Docker环境中的asyncio事件循环策略问题
if sys.platform.startswith('linux') or os.getenv('DOCKER_ENV'):
    try:
        asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
    except Exception as e:
        logger.warning(f"设置事件循环策略失败: {e}")

if os.getenv('DOCKER_ENV'):
    try:
        if hasattr(asyncio, 'SelectorEventLoop'):
            loop = asyncio.SelectorEventLoop()
            asyncio.set_event_loop(loop)
    except Exception as e:
        logger.warning(f"设置SelectorEventLoop失败: {e}")

try:
    from playwright.async_api import async_playwright, Page, BrowserContext, Browser
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    Page = Any
    BrowserContext = Any
    Browser = Any
    logger.warning("Playwright 未安装，将无法使用真实搜索功能")


class BrowserManager:
    """浏览器管理器"""

    # 浏览器启动参数
    DEFAULT_BROWSER_ARGS = [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--no-first-run',
        '--disable-extensions',
        '--disable-default-apps',
        '--no-default-browser-check',
        '--lang=zh-CN',
        '--accept-lang=zh-CN,zh,en-US,en'
    ]

    DOCKER_BROWSER_ARGS = [
        '--disable-gpu',
    ]

    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self._user_data_dir: Optional[str] = None

    @property
    def is_available(self) -> bool:
        """检查Playwright是否可用"""
        return PLAYWRIGHT_AVAILABLE

    async def init_browser(self, headless: Optional[bool] = None) -> bool:
        """初始化浏览器（使用持久化上下文）"""
        if not PLAYWRIGHT_AVAILABLE:
            raise Exception("Playwright 未安装，无法使用真实搜索功能")

        if self.browser:
            return True

        # 动态读取配置，默认为 True
        from app.core.config import get_settings
        env_headless = get_settings().browser_headless
        if headless is None:
            headless = env_headless

        # Docker环境或显式设置强制无头模式（容器内无显示器，有头模式会报错）
        if os.environ.get("DOCKER_ENV") == "true" or os.environ.get("BROWSER_HEADLESS_FORCE", "").lower() == "true":
            logger.info("强制使用无头模式")
            headless = True

        try:
            ensure_playwright_browser_path()
            self.playwright = await async_playwright().start()

            # 设置持久化数据目录
            self._user_data_dir = os.path.join(
                tempfile.gettempdir(), 'xianyu_browser_cache'
            )
            os.makedirs(self._user_data_dir, exist_ok=True)
            logger.info(f"使用持久化数据目录: {self._user_data_dir}")

            # 引入防反爬脚本与随机特征配置
            from common.services.captcha.browser_features import get_random_browser_features, get_stealth_script
            browser_features = get_random_browser_features()

            # 构建浏览器参数
            browser_args = self.DEFAULT_BROWSER_ARGS.copy()
            browser_args.append('--disable-blink-features=AutomationControlled')
            browser_args.append(f"--window-size={browser_features['window_size']}")
            browser_args.append(f"--lang={browser_features['lang']}")
            browser_args.append(f"--accept-lang={browser_features['accept_lang']}")

            if os.getenv('DOCKER_ENV') == 'true':
                browser_args.extend(self.DOCKER_BROWSER_ARGS)

            logger.info("正在启动浏览器（中文模式，持久化缓存）...")
            chromium_path = get_chromium_executable_path()

            # 使用持久化上下文
            launch_kwargs = dict(
                headless=headless,
                args=browser_args,
                ignore_default_args=["--enable-automation"],
                user_agent=browser_features['user_agent'],
                viewport={'width': browser_features['viewport_width'], 'height': browser_features['viewport_height']},
                locale=browser_features['locale'],
                ignore_https_errors=True,
                extra_http_headers={
                    'Accept-Language': browser_features['accept_lang']
                }
            )
            if chromium_path:
                launch_kwargs["executable_path"] = chromium_path

            # 【防锁死与防并发冲突设计】
            # 如果 SingletonLock 残留或者有并发请求占用同一个 profile 目录，
            # 捕获异常并切换到全新的隔离临时目录重试，最多重试 3 次不同的目录。
            import uuid
            current_user_data_dir = self._user_data_dir
            max_launch_attempts = 3
            
            for attempt in range(1, max_launch_attempts + 1):
                try:
                    # 尝试清理旧锁文件（SingletonLock 在 Linux 下是软链接，Windows 下是文件）
                    lock_file = os.path.join(current_user_data_dir, "SingletonLock")
                    if os.path.exists(lock_file):
                        try:
                            if os.path.islink(lock_file):
                                os.unlink(lock_file)
                            else:
                                os.remove(lock_file)
                            logger.info(f"清理了已存在的 SingletonLock: {lock_file}")
                        except Exception as lock_e:
                            logger.debug(f"无法清理 SingletonLock (可能被占用中): {lock_e}")

                    self.context = await self.playwright.chromium.launch_persistent_context(
                        current_user_data_dir,
                        **launch_kwargs,
                    )
                    # 启动成功，更新实际使用的数据目录并跳出循环
                    self._user_data_dir = current_user_data_dir
                    break
                except Exception as launch_e:
                    err_msg = str(launch_e)
                    is_lock_conflict = "Opening in existing browser session" in err_msg or "profile is already in use" in err_msg
                    
                    if is_lock_conflict and attempt < max_launch_attempts:
                        logger.warning(
                            f"⚠️ 浏览器目录 {current_user_data_dir} 被占用或存在锁冲突，"
                            f"第 {attempt}/{max_launch_attempts} 次尝试切换到临时随机隔离目录..."
                        )
                        # 产生一个带 UUID 后缀的新目录
                        current_user_data_dir = os.path.join(
                            tempfile.gettempdir(), 
                            f'xianyu_browser_cache_{uuid.uuid4().hex[:8]}'
                        )
                        os.makedirs(current_user_data_dir, exist_ok=True)
                    else:
                        # 检查有头模式不支持的降级逻辑（原有逻辑）
                        if not launch_kwargs.get("headless") and (
                            "XServer" in err_msg or 
                            "DISPLAY" in err_msg or 
                            "failed to initialize" in err_msg or 
                            "closed" in err_msg
                        ):
                            logger.warning(f"有头模式启动浏览器失败（可能由于无 GUI 环境/缺少 XServer），自动降级为无头模式重试: {launch_e}")
                            launch_kwargs["headless"] = True
                            continue
                        raise

            # 在 Context 级别全局注入防检测（Stealth）脚本，防止 iframe 与新页面特征分裂
            await self.context.add_init_script(get_stealth_script(browser_features))
            logger.info("已在 Context 注入防检测（Stealth）脚本")

            self.browser = self.context.browser
            logger.info("浏览器启动成功（持久化上下文已创建）...")

            self.page = await self.context.new_page()
            logger.info("浏览器初始化完成")

            return True

        except Exception as e:
            logger.error(f"浏览器初始化失败: {e}")
            await self.close_browser()
            raise

    async def close_browser(self):
        """关闭浏览器"""
        try:
            if self.page:
                await self.page.close()
                self.page = None

            if self.context:
                await self.context.close()
                self.context = None

            self.browser = None

            if self.playwright:
                await self.playwright.stop()
                self.playwright = None

            logger.debug("浏览器已关闭（缓存已保存）")

            # 【清理随机临时目录】
            # 如果当前使用的是临时隔离目录（即带有 uuid 后缀的目录），在关闭时将其彻底删除，防止临时文件泄露。
            # 原有的 /tmp/xianyu_browser_cache 目录则保留以作复用。
            if self._user_data_dir and self._user_data_dir != os.path.join(tempfile.gettempdir(), 'xianyu_browser_cache'):
                try:
                    import shutil
                    if os.path.exists(self._user_data_dir):
                        # 延迟一小会儿，确保浏览器进程已经完全退出、释放了所有文件句柄
                        await asyncio.sleep(0.5)
                        shutil.rmtree(self._user_data_dir, ignore_errors=True)
                        logger.info(f"清理了临时隔离浏览器目录: {self._user_data_dir}")
                except Exception as clean_e:
                    logger.debug(f"清理临时目录失败: {clean_e}")

        except Exception as e:
            logger.warning(f"关闭浏览器时出错: {e}")

    async def set_cookies(self, cookie_value: str) -> bool:
        """设置浏览器cookies"""
        try:
            if not cookie_value or not self.context:
                return False

            cookies = []
            for cookie_pair in cookie_value.split(';'):
                cookie_pair = cookie_pair.strip()
                if '=' in cookie_pair:
                    name, value = cookie_pair.split('=', 1)
                    cookies.append({
                        'name': name.strip(),
                        'value': value.strip(),
                        'domain': '.goofish.com',
                        'path': '/'
                    })

            await self.context.add_cookies(cookies)
            logger.info(f"成功设置 {len(cookies)} 个cookies到浏览器")
            return True

        except Exception as e:
            logger.error(f"设置浏览器cookies失败: {str(e)}")
            return False

    async def navigate_to(self, url: str, timeout: int = 30000) -> bool:
        """导航到指定URL"""
        try:
            if not self.page:
                return False

            await self.page.goto(url, timeout=timeout)
            return True

        except Exception as e:
            logger.error(f"导航失败: {e}")
            return False

    async def wait_for_network_idle(self, timeout: int = 15000):
        """等待网络空闲"""
        if self.page:
            await self.page.wait_for_load_state("networkidle", timeout=timeout)

    async def fill_input(self, selector: str, value: str) -> bool:
        """填充输入框"""
        try:
            if not self.page:
                return False

            await self.page.fill(selector, value)
            return True

        except Exception as e:
            logger.error(f"填充输入框失败: {e}")
            return False

    async def click(self, selector: str) -> bool:
        """点击元素"""
        try:
            if not self.page:
                return False

            await self.page.click(selector)
            return True

        except Exception as e:
            logger.error(f"点击元素失败: {e}")
            return False

    async def press_key(self, key: str):
        """按下键盘按键"""
        if self.page:
            await self.page.keyboard.press(key)

    def on_response(self, callback):
        """注册响应监听器"""
        if self.page:
            self.page.on("response", callback)
