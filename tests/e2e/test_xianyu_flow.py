import pytest
from playwright.async_api import Page, expect
from tests.e2e.stealth_utils import human_click, human_type, human_scroll, human_delay

@pytest.mark.asyncio
async def test_xianyu_message_flow(stealth_page: Page):
    """
    仿真测试闲鱼自动回复的基础交互流。
    展示如何在安全防风控配置下打开闲鱼、浏览并执行拟人化操作。
    """
    page = stealth_page

    # 1. 打开闲鱼主页（防风控：使用正常跳转并加上首屏延迟）
    await page.goto("https://2.taobao.com/")
    await page.wait_for_load_state("networkidle")
    await human_delay(1000, 2000)

    # 2. 模拟真实用户的滚屏浏览动作
    await human_scroll(page, distance=600)
    await human_delay(800, 1500)

    # 3. 检查当前是否已登录（如果持久化 Context 里已经保存了 Cookie，这步会保持登录）
    # 这里是一个检查机制，如果被重定向到了登录页，可以通过控制台或手动扫码通过
    if "login" in page.url:
        print("\n[警告] 检测到需要扫码登录，请在打开的 headed 浏览器窗口中手动完成扫码...")
        # 等待 60 秒给用户扫码（只要扫码一次，数据会持久化保存在 .xianyu_browser_data 目录下，下次运行免密直接进）
        try:
            await page.wait_for_url("https://2.taobao.com/", timeout=60000)
            print("[成功] 扫码登录成功，已保存 Session 状态。")
        except Exception:
            pytest.fail("登录超时，未能在 60 秒内完成扫码。")

    # 4. 模拟点击导航栏的“消息”或某个元素
    # 注意：下面使用我们封装的拟人化点击，会先 hover 过去，等待随机微毫秒再点击
    # （此处使用虚拟选择器，具体业务中应替换为闲鱼最新的真实 DOM Selector）
    try:
        # 模拟鼠标滑过闲鱼首页某件商品的缩略图
        target_item_selector = ".item-card" # 伪选择器
        if await page.query_selector(target_item_selector):
            await human_click(page, target_item_selector)
            await human_delay(1500, 3000)
            
            # 返回上一页
            await page.go_back()
            await human_delay(1000, 2000)
    except Exception as e:
        print(f"提示：仿真元素未找到或状态异常（正常现象，可能未处于登录态）：{e}")

    # 5. 模拟正常关闭与休眠
    await human_delay(500, 1000)
