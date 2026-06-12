import os
import shutil
import pytest
from pathlib import Path
from playwright.async_api import async_playwright, BrowserContext, Page
from tests.e2e.stealth_utils import apply_stealth

# 浏览器数据持久化目录路径，用来保存 Cookie、Session、LocalStorage 等，防止每次测试都处于“新设备”高危环境
USER_DATA_DIR = Path(__file__).parent / ".xianyu_browser_data"

@pytest.fixture(scope="session", autouse=True)
def prepare_dirs():
    """测试前准备工作目录，如不存在则创建"""
    USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
    yield
    # 如果需要在测试全部结束后彻底清理数据目录，可以取消下行注释
    # shutil.rmtree(USER_DATA_DIR, ignore_errors=True)

@pytest.fixture
async def stealth_context() -> BrowserContext:
    """提供经过反爬检测伪装的持久化浏览器上下文"""
    async with async_playwright() as p:
        # 使用持久化上下文启动 Chromium
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(USER_DATA_DIR),
            headless=False, # 防风控建议在 headed 模式下运行测试，无头模式极易被标记
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
            # 禁用自动化控制栏（不显示 "Chrome 正受到自动测试软件的控制" 栏），规避检测
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox"
            ]
        )
        yield context
        await context.close()

@pytest.fixture
async def stealth_page(stealth_context: BrowserContext) -> Page:
    """提供带有 Stealth 防御罩的测试 Page 实例"""
    page = await stealth_context.new_page()
    
    # 注入反检测 Stealth JS
    await apply_stealth(page)
    
    yield page
    await page.close()
