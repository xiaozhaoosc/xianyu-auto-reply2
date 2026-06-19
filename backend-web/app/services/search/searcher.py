"""
商品搜索服务

基于Playwright实现闲鱼商品搜索
复刻原始 utils/item_search.py 的逻辑
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.models.xy_account import XYAccount
from app.services.search.browser import BrowserManager, PLAYWRIGHT_AVAILABLE
from app.services.search.parser import ItemParser
from app.services.search.slider_handler import SliderHandler


class ItemSearchService:
    """商品搜索服务"""

    # 搜索相关选择器
    SEARCH_INPUT_SELECTORS = [
        'input[class*="search-input"]',
        'input[placeholder*="搜索"]',
        'input[type="text"]',
        '.search-input',
        '#search-input'
    ]

    NEXT_PAGE_SELECTORS = [
        '.search-page-tiny-arrow-right--oXVFaRao',
        '[class*="search-page-tiny-arrow-right"]',
        'button[aria-label="下一页"]',
        'button:has-text("下一页")',
        'a:has-text("下一页")',
        '.ant-pagination-next',
        'li.ant-pagination-next a',
        'a[aria-label="下一页"]'
    ]

    def __init__(self, db_session: Optional[AsyncSession] = None, user_id: str = "default"):
        """
        初始化搜索服务
        
        Args:
            db_session: 异步数据库会话（可选，用于获取Cookie）
            user_id: 用户ID，用于滑块验证会话
        """
        self.db_session = db_session
        self.user_id = user_id
        self.browser = BrowserManager()
        self.parser = ItemParser()
        self.slider_handler = SliderHandler(user_id)
        self.api_responses: List[Dict] = []
        self.data_list: List[Dict] = []
        self.cookie_value: str = ""
        self._search_error: Optional[str] = None
        self._verification_url: Optional[str] = None

    async def get_first_valid_cookie(self) -> Optional[Dict[str, str]]:
        """获取第一个有效的cookie"""
        if not self.db_session:
            logger.error("数据库会话未初始化")
            return None

        try:
            conditions = [XYAccount.status == "active"]
            # 尽量只使用当前登录用户自己的账号 Cookie（避免跨用户取到别人的 Cookie）
            if isinstance(self.user_id, str) and self.user_id.isdigit():
                conditions.append(XYAccount.owner_id == int(self.user_id))

            stmt = select(XYAccount).where(*conditions).limit(1)
            result = await self.db_session.execute(stmt)
            account = result.scalars().first()

            if account and account.cookie and len(account.cookie) > 50:
                logger.info(f"找到有效cookie: {account.account_id}")
                self.cookie_value = account.cookie
                return {
                    'id': account.account_id,
                    'value': account.cookie
                }

            return None

        except Exception as e:
            logger.error(f"获取cookie失败: {str(e)}")
            return None

    async def _on_response(self, response):
        """处理API响应"""
        if "h5api.m.goofish.com/h5/mtop.taobao.idlemtopsearch.pc.search" in response.url:
            try:
                if response.status != 200:
                    logger.warning(f"API响应状态异常: {response.status}")
                    return

                try:
                    result_json = await response.json()
                except Exception:
                    logger.warning("无法解析响应JSON")
                    return

                self.api_responses.append(result_json)
                logger.info(f"捕获到API响应")

                ret = (result_json or {}).get("ret")
                is_blocked = False
                if isinstance(ret, list) and ret:
                    non_success = [str(x) for x in ret if x and not str(x).startswith("SUCCESS")]
                    if non_success:
                        self._search_error = "; ".join(non_success[:3])
                        if any("FAIL_SYS_USER_VALIDATE" in x for x in non_success):
                            is_blocked = True

                data = (result_json or {}).get("data") or {}
                if isinstance(data, dict):
                    data_error = data.get("errorMsg") or data.get("error_message") or data.get("message")
                    if data_error and not self._search_error:
                        self._search_error = str(data_error)
                    if data_error and "FAIL_SYS_USER_VALIDATE" in str(data_error):
                        is_blocked = True

                if is_blocked or (self._search_error and "FAIL_SYS_USER_VALIDATE" in str(self._search_error)):
                    v_url = data.get("url") or (result_json or {}).get("data", {}).get("url")
                    if v_url:
                        self._verification_url = v_url
                        logger.warning(f"📌 _on_response 捕获到 API 拦截，验证 URL: {self._verification_url}")

                items = result_json.get("data", {}).get("resultList", [])
                logger.info(f"从API获取到 {len(items)} 条原始数据")

                parsed_items = await self.parser.parse_items_batch(items)
                self.data_list.extend(parsed_items)

            except Exception as e:
                logger.warning(f"响应处理异常: {str(e)}")

    async def _handle_verification_and_sync_cookies(
        self,
        max_retries: int = 5,
        page: Optional[Page] = None
    ) -> bool:
        """
        通用滑块及拦截验证处理，自动从 Playwright 导出 cookies 并同步数据库。
        """
        target_page = page or self.browser.page
        if not target_page:
            return True

        v_url = getattr(self, "_verification_url", None)
        has_slider = False
        detected_selector = None

        # 如果检测到确实被拦截了，但当前页面上还没检测到滑块，我们轮询等最多 5 秒钟让淘宝 JS 注入滑块
        is_blocked_by_api = False
        search_err_str = str(getattr(self, "_search_error", "") or "")
        if "FAIL_SYS_USER_VALIDATE" in search_err_str or "舆情/验证码拦截" in search_err_str:
            is_blocked_by_api = True

        if not v_url:
            # 轮询等滑块出现
            for _ in range(10):  # 10 * 0.5s = 5s
                has_slider, detected_selector = await self.slider_handler.detect_slider(target_page)
                if has_slider:
                    break
                await asyncio.sleep(0.5)

            if not has_slider:
                if not is_blocked_by_api:
                    return True
                else:
                    logger.warning("⚠️ API 被验证码拦截，但页面上等了 5 秒也没有渲染出滑块组件。")
        else:
            detected_selector = "FAIL_SYS_USER_VALIDATE (API URL)"
            has_slider = True

        logger.warning(f"⚠️ 搜索流检测到安全拦截或滑块验证（{detected_selector}），开始处理...")

        captcha_ok = False
        new_cookies_dict = None

        # 优先通过验证 URL 调用统一 fallback 滑块引擎
        if v_url:
            logger.warning(f"🚀 发现拦截验证 URL，优先调用 token 流 run_slider_verification_with_fallback. URL: {v_url}")
            try:
                from common.services.captcha.orchestrator import run_slider_verification_with_fallback
                from app.core.config import get_settings
                env_headless = get_settings().browser_headless
                success, cookies, captcha_engine = await asyncio.to_thread(
                    run_slider_verification_with_fallback,
                    user_id=f"{self.user_id}",
                    url=v_url,
                    enable_learning=True,
                    headless=env_headless,
                    browser_timeout=25,
                    existing_cookies_str=self.cookie_value,
                )
                if success and cookies:
                    captcha_ok = True
                    new_cookies_dict = cookies
                    logger.success(f"✅ 通过 run_slider_verification_with_fallback 验证成功（引擎: {captcha_engine}）")
            except Exception as e:
                logger.error(f"❌ 调用 run_slider_verification_with_fallback 发生异常: {e}")

        # 如果没有 URL 验证，或者 URL 验证没成功，但在当前页面显示了滑块，在当前页面滑动
        if not captcha_ok:
            page_slider, _ = await self.slider_handler.detect_slider(target_page)
            if page_slider:
                logger.info("⏳ 尝试在当前 Playwright 页面进行滑块验证...")
                captcha_ok = await self.slider_handler.handle_verification(
                    page=target_page,
                    context=self.browser.context,
                    max_retries=max_retries,
                    allow_manual=True,
                )
                if captcha_ok and self.browser.context:
                    try:
                        page_cookies = await self.browser.context.cookies()
                        new_cookies_dict = {c["name"]: c["value"] for c in page_cookies}
                    except Exception as e:
                        logger.error(f"❌ 从当前页面 context 提取 cookies 异常: {e}")

        if not captcha_ok:
            logger.error("❌ 验证码处理失败，无法继续")
            return False

        # 提取 x5sec 并更新浏览器及数据库
        if new_cookies_dict:
            x5sec_cookies = {}
            for k, v in new_cookies_dict.items():
                if k.lower().startswith('x5') or 'x5sec' in k.lower():
                    x5sec_cookies[k] = v

            if x5sec_cookies:
                logger.info(f"🔮 导出成功，检测到 x5sec cookies: {list(x5sec_cookies.keys())}")
                
                # 写入浏览器 context
                try:
                    new_cookies_list = []
                    for k, v in x5sec_cookies.items():
                        new_cookies_list.append({
                            'name': k,
                            'value': v,
                            'domain': '.goofish.com',
                            'path': '/'
                        })
                    if self.browser.context:
                        await self.browser.context.add_cookies(new_cookies_list)
                        logger.info("已将最新 x5sec cookies 覆盖写入当前浏览器 context")
                except Exception as e:
                    logger.error(f"❌ 写入最新 x5sec cookies 到浏览器 context 失败: {e}")

                # 写入数据库并更新内存变量
                if self.db_session:
                    from app.services.compass.goofish_compass import update_xy_account_cookie
                    updated = await update_xy_account_cookie(
                        db_session=self.db_session,
                        user_id=self.user_id,
                        old_cookie=self.cookie_value,
                        new_x5sec_cookies=x5sec_cookies
                    )
                    if updated:
                        old_cookies_dict = {}
                        if self.cookie_value:
                            for pair in self.cookie_value.split(";"):
                                pair = pair.strip()
                                if "=" in pair:
                                    k, v = pair.split("=", 1)
                                    old_cookies_dict[k.strip()] = v.strip()
                        for k, v in x5sec_cookies.items():
                            old_cookies_dict[k] = v
                        self.cookie_value = "; ".join([f"{k}={v}" for k, v in old_cookies_dict.items()])
            else:
                logger.warning("⚠️ 验证通过，但提取的 cookies 中没有发现 x5sec 相关的 cookie")

        if hasattr(self, "_verification_url"):
            self._verification_url = None

        return True

    async def search_items(
        self,
        keyword: str,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        搜索闲鱼商品
        
        Args:
            keyword: 搜索关键词
            page: 页码，从1开始
            page_size: 每页数量
            
        Returns:
            搜索结果字典
        """
        if not PLAYWRIGHT_AVAILABLE:
            logger.error("Playwright 不可用")
            return {'items': [], 'total': 0, 'error': 'Playwright 不可用'}

        logger.info(f"搜索闲鱼商品: 关键词='{keyword}', 页码={page}")

        try:
            await self.browser.init_browser()
            self.api_responses = []
            self.data_list = []

            # 获取并设置cookies
            cookie_data = await self.get_first_valid_cookie()
            if not cookie_data:
                raise Exception("未找到有效的cookies账户")

            logger.info(f"使用账户: {cookie_data.get('id', 'unknown')}")

            # 访问闲鱼首页
            await self.browser.navigate_to("https://www.goofish.com")
            await self.browser.set_cookies(cookie_data.get('value', ''))

            # 刷新页面应用cookies
            if self.browser.page:
                await self.browser.page.reload()
                await asyncio.sleep(2)

            await self.browser.wait_for_network_idle(timeout=10000)

            # 搜索
            logger.info(f"正在搜索关键词: {keyword}")
            search_input = await self._find_search_input()
            if not search_input:
                logger.warning("⚠️ 未能直接找到搜索框元素，检查当前页面是否被验证码/滑块拦截...")
                captcha_ok = await self._handle_verification_and_sync_cookies(max_retries=5)
                if captcha_ok:
                    logger.info("验证通过后，重新加载页面再次尝试寻找搜索框...")
                    if self.browser.page:
                        await self.browser.page.reload()
                        await asyncio.sleep(2)
                    search_input = await self._find_search_input()

            if not search_input:
                raise Exception("未找到搜索框元素")

            await search_input.fill(keyword)

            # 注册响应监听
            self.browser.on_response(self._on_response)

            # 增加重试机制，应对拦截
            max_search_retries = 3
            for attempt in range(max_search_retries):
                self._search_error = None
                self._verification_url = None
                self.data_list.clear()

                logger.info(f"发送搜索请求 (尝试 {attempt + 1}/{max_search_retries})...")
                await self.browser.click('button[type="submit"]')
                await self.browser.wait_for_network_idle(timeout=15000)
                await asyncio.sleep(2)

                # 处理弹窗
                try:
                    await self.browser.press_key('Escape')
                    await asyncio.sleep(0.5)
                except Exception:
                    pass

                # 处理滑块并同步 Cookie 到数据库与浏览器
                captcha_ok = await self._handle_verification_and_sync_cookies(max_retries=5)
                if not captcha_ok:
                    logger.error("❌ 滑块验证失败")
                    return {'items': [], 'total': 0, 'error': '滑块验证失败'}

                # 如果没有拦截错误，或者数据获取成功，则跳出重试
                if not self._search_error or "FAIL_SYS_USER_VALIDATE" not in str(self._search_error):
                    logger.success(f"🎉 搜索成功，获取数据成功（尝试次数: {attempt + 1}）")
                    break
                else:
                    logger.warning(f"⚠️ 搜索仍被拦截，准备下一次重试 (尝试 {attempt + 1} 失败: {self._search_error})")
                    await asyncio.sleep(1)

            await asyncio.sleep(3)

            # 如果需要翻页
            if page > 1:
                self.data_list.clear()
                await self._navigate_to_page(page)

            # 排序
            sorted_items = self.parser.sort_by_want_count(self.data_list)

            logger.info(f"搜索完成，获取到 {len(sorted_items)} 条数据")

            return {
                'items': sorted_items,
                'total': len(sorted_items),
                'is_real_data': True,
                'source': 'playwright'
            }

        except Exception as e:
            error_msg = self._format_error_message(str(e))
            logger.error(f"搜索失败: {error_msg}")
            return {'items': [], 'total': 0, 'error': f'搜索失败: {error_msg}'}

        finally:
            await self.browser.close_browser()

    async def search_multiple_pages(
        self,
        keyword: str,
        total_pages: int = 1
    ) -> Dict[str, Any]:
        """
        搜索多页闲鱼商品
        
        Args:
            keyword: 搜索关键词
            total_pages: 总页数
            
        Returns:
            搜索结果字典
        """
        if not PLAYWRIGHT_AVAILABLE:
            return {'items': [], 'total': 0, 'error': 'Playwright 不可用'}

        logger.info(f"多页搜索: 关键词='{keyword}', 总页数={total_pages}")

        try:
            await self.browser.init_browser()
            self.api_responses = []
            self.data_list = []

            # 获取并设置cookies
            cookie_data = await self.get_first_valid_cookie()
            if not cookie_data:
                raise Exception("未找到有效的cookies账户")

            # 访问闲鱼首页
            await self.browser.navigate_to("https://www.goofish.com")
            await self.browser.set_cookies(cookie_data.get('value', ''))

            if self.browser.page:
                await self.browser.page.reload()
                await asyncio.sleep(2)

            await self.browser.wait_for_network_idle(timeout=15000)

            # 搜索
            search_input = await self._find_search_input()
            if not search_input:
                logger.warning("⚠️ 未能直接找到搜索框元素，检查当前页面是否被验证码/滑块拦截...")
                captcha_ok = await self._handle_verification_and_sync_cookies(max_retries=5)
                if captcha_ok:
                    logger.info("验证通过后，重新加载页面再次尝试寻找搜索框...")
                    if self.browser.page:
                        await self.browser.page.reload()
                        await asyncio.sleep(2)
                    search_input = await self._find_search_input()

            if not search_input:
                raise Exception("未找到搜索框元素")

            await search_input.fill(keyword)
            self.browser.on_response(self._on_response)

            # 增加重试机制，应对拦截
            max_search_retries = 3
            for attempt in range(max_search_retries):
                self._search_error = None
                self._verification_url = None
                self.data_list.clear()

                logger.info(f"发送搜索请求 (尝试 {attempt + 1}/{max_search_retries})...")
                await self.browser.click('button[type="submit"]')
                await self.browser.wait_for_network_idle(timeout=15000)
                await asyncio.sleep(2)

                # 处理弹窗
                try:
                    await self.browser.press_key('Escape')
                except Exception:
                    pass

                # 处理滑块并同步 Cookie
                captcha_ok = await self._handle_verification_and_sync_cookies(max_retries=5)
                if not captcha_ok:
                    return {'items': [], 'total': 0, 'error': '滑块验证失败'}

                # 如果没有拦截错误，或者获取数据成功，则跳出重试
                if not self._search_error or "FAIL_SYS_USER_VALIDATE" not in str(self._search_error):
                    logger.success(f"🎉 搜索成功，获取数据成功（尝试次数: {attempt + 1}）")
                    break
                else:
                    logger.warning(f"⚠️ 搜索仍被拦截，准备下一次重试 (尝试 {attempt + 1} 失败: {self._search_error})")
                    await asyncio.sleep(1)

            await asyncio.sleep(3)

            first_page_count = len(self.data_list)
            logger.info(f"第1页完成，获取到 {first_page_count} 条数据")

            # 获取更多页
            if total_pages > 1:
                for page_num in range(2, total_pages + 1):
                    success = await self._click_next_page(page_num)
                    if not success:
                        logger.warning(f"无法获取第 {page_num} 页，停止翻页")
                        break

            # 排序
            sorted_items = self.parser.sort_by_want_count(self.data_list)

            logger.info(f"多页搜索完成，共获取 {len(sorted_items)} 条数据")

            return {
                'items': sorted_items,
                'total': len(sorted_items),
                'is_real_data': True,
                'source': 'playwright'
            }

        except Exception as e:
            error_msg = self._format_error_message(str(e))
            logger.error(f"多页搜索失败: {error_msg}")
            return {'items': [], 'total': 0, 'error': f'搜索失败: {error_msg}'}

        finally:
            await self.browser.close_browser()

    async def _find_search_input(self):
        """查找搜索输入框"""
        if not self.browser.page:
            return None

        for selector in self.SEARCH_INPUT_SELECTORS:
            try:
                element = await self.browser.page.wait_for_selector(selector, timeout=5000)
                if element:
                    logger.info(f"✅ 找到搜索框: {selector}")
                    return element
            except Exception:
                continue

        return None

    async def _navigate_to_page(self, target_page: int):
        """导航到指定页面"""
        try:
            logger.info(f"正在导航到第 {target_page} 页...")
            await asyncio.sleep(2)

            for current_page in range(2, target_page + 1):
                success = await self._click_next_page(current_page)
                if not success:
                    break

        except Exception as e:
            logger.error(f"导航失败: {str(e)}")

    async def _click_next_page(self, page_num: int) -> bool:
        """点击下一页"""
        if not self.browser.page:
            return False

        logger.info(f"正在获取第 {page_num} 页...")
        await asyncio.sleep(2)

        before_count = len(self.data_list)

        for selector in self.NEXT_PAGE_SELECTORS:
            try:
                next_button = self.browser.page.locator(selector).first

                if await next_button.is_visible(timeout=3000):
                    is_disabled = await next_button.get_attribute("disabled")
                    has_disabled_class = await next_button.evaluate(
                        "el => el.classList.contains('ant-pagination-disabled') || el.classList.contains('disabled')"
                    )

                    if not is_disabled and not has_disabled_class:
                        await next_button.scroll_into_view_if_needed()
                        await asyncio.sleep(1)
                        await next_button.click()
                        await self.browser.wait_for_network_idle(timeout=15000)
                        await asyncio.sleep(5)

                        after_count = len(self.data_list)
                        new_items = after_count - before_count

                        if new_items > 0:
                            logger.info(f"第 {page_num} 页成功，新增 {new_items} 条数据")
                            return True
                        else:
                            logger.warning(f"第 {page_num} 页没有新数据")
                            return False

            except Exception:
                continue

        logger.warning(f"无法找到下一页按钮")
        return False

    def _format_error_message(self, error_msg: str) -> str:
        """格式化错误信息"""
        if "Executable doesn't exist" in error_msg or "playwright install" in error_msg:
            return "浏览器未安装。请运行: playwright install chromium"
        elif "BrowserType.launch" in error_msg:
            return "浏览器启动失败"
        elif "Target page, context or browser has been closed" in error_msg:
            return "浏览器页面被意外关闭"
        elif "Timeout" in error_msg:
            return "页面加载超时"
        return error_msg


# 便捷函数
async def search_xianyu_items(
    keyword: str,
    page: int = 1,
    page_size: int = 20,
    db_session: Optional[AsyncSession] = None
) -> Dict[str, Any]:
    """搜索闲鱼商品的便捷函数"""
    max_retries = 2
    retry_delay = 5

    for attempt in range(max_retries + 1):
        try:
            service = ItemSearchService(db_session)
            logger.info(f"搜索尝试: {attempt + 1}/{max_retries + 1}")
            result = await service.search_items(keyword, page, page_size)

            if result.get('items') or not result.get('error'):
                return result

        except Exception as e:
            logger.error(f"搜索失败 (尝试 {attempt + 1}): {str(e)}")

            if attempt == max_retries:
                return {'items': [], 'total': 0, 'error': f"搜索失败: {str(e)}"}

            await asyncio.sleep(retry_delay)

    return {'items': [], 'total': 0, 'error': "未知错误"}


async def search_multiple_pages_xianyu(
    keyword: str,
    total_pages: int = 1,
    db_session: Optional[AsyncSession] = None
) -> Dict[str, Any]:
    """搜索多页闲鱼商品的便捷函数"""
    try:
        service = ItemSearchService(db_session)
        return await service.search_multiple_pages(keyword, total_pages)
    except Exception as e:
        logger.error(f"多页搜索失败: {str(e)}")
        return {'items': [], 'total': 0, 'error': f"搜索失败: {str(e)}"}
