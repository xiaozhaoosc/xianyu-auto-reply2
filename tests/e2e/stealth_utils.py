import asyncio
import random
from playwright.async_api import Page, ElementHandle

# 移除 webdriver 痕迹的 JavaScript 代码 (Stealth 脚本)
STEALTH_JS = """
// 1. 覆盖 navigator.webdriver
Object.defineProperty(navigator, 'webdriver', {
  get: () => undefined
});

// 2. 伪造 chrome 属性
window.chrome = {
  runtime: {},
  loadTimes: function() {},
  csi: function() {},
  app: {}
};

// 3. 伪造插件列表 (避免空插件)
Object.defineProperty(navigator, 'plugins', {
  get: () => [
    { name: 'Chrome PDF Viewer', filename: 'internal-pdf-viewer' },
    { name: 'Chromium PDF Viewer', filename: 'internal-pdf-viewer' }
  ]
});

// 4. 伪造 languages
Object.defineProperty(navigator, 'languages', {
  get: () => ['zh-CN', 'zh', 'en']
});

// 5. 伪造 WebGL Vendor & Renderer
const getParameter = WebGLRenderingContext.prototype.getParameter;
WebGLRenderingContext.prototype.getParameter = function(parameter) {
  // UNMASKED_VENDOR_WEBGL
  if (parameter === 37445) {
    return 'Intel Inc.';
  }
  // UNMASKED_RENDERER_WEBGL
  if (parameter === 37446) {
    return 'Intel(R) Iris(TM) Plus Graphics 640';
  }
  return getParameter(parameter);
};
"""

async def apply_stealth(page: Page):
    """注入 Stealth 脚本以躲避反爬虫检测"""
    await page.add_init_script(STEALTH_JS)

async def human_delay(min_ms: int = 300, max_ms: int = 1500):
    """产生随机的物理延迟，模拟人类反应时间"""
    delay = random.randint(min_ms, max_ms) / 1000.0
    await asyncio.sleep(delay)

async def human_type(page: Page, selector: str, text: str):
    """模拟人类打字：带随机间隔地逐字输入，降低机器人特征"""
    element = await page.wait_for_selector(selector)
    await element.focus()
    await human_delay(200, 500)
    for char in text:
        await page.keyboard.type(char)
        # 字符输入间隔在 50ms - 250ms 之间抖动
        await asyncio.sleep(random.uniform(0.05, 0.25))
    await human_delay(300, 600)

async def human_click(page: Page, selector_or_element):
    """模拟人类点击：先移动（hover）到目标元素，稍作停顿，然后进行物理点击"""
    if isinstance(selector_or_element, str):
        element = await page.wait_for_selector(selector_or_element)
    else:
        element = selector_or_element
        
    # 模拟鼠标移动到元素上
    await element.hover()
    await human_delay(150, 450)
    
    # 执行点击
    await element.click()
    await human_delay(300, 1000)

async def human_scroll(page: Page, distance: int = 500):
    """模拟人类浏览时的平滑滚动"""
    steps = random.randint(5, 10)
    step_distance = distance // steps
    for _ in range(steps):
        # 每次滚动的位移带轻微扰动
        delta = step_distance + random.randint(-15, 15)
        await page.evaluate(f"window.scrollBy(0, {delta})")
        await human_delay(100, 300)
