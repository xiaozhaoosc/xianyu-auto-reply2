"""
浏览器特征和反检测脚本

提供随机浏览器特征生成和反检测JavaScript脚本
复刻原始 utils/xianyu_slider_stealth.py 中的浏览器特征相关逻辑
"""
from __future__ import annotations

import random
from typing import Any, Dict


def get_random_browser_features() -> Dict[str, Any]:
    """获取随机浏览器特征"""
    # 随机选择窗口大小（使用更大的尺寸以适应最大化）
    window_sizes = [
        "1920,1080", "1920,1200", "2560,1440", "1680,1050", "1600,900"
    ]

    # 随机选择语言
    languages = [
        ("zh-CN", "zh-CN,zh;q=0.9,en;q=0.8"),
        ("zh-CN", "zh-CN,zh;q=0.9"),
        ("zh-CN", "zh-CN,zh;q=0.8,en;q=0.6")
    ]

    # 随机选择用户代理
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    ]

    window_size = random.choice(window_sizes)
    lang, accept_lang = random.choice(languages)
    user_agent = random.choice(user_agents)

    # 解析窗口大小
    width, height = map(int, window_size.split(','))

    return {
        'window_size': window_size,
        'lang': lang,
        'accept_lang': accept_lang,
        'user_agent': user_agent,
        'locale': lang,
        'viewport_width': width,
        'viewport_height': height,
        'device_scale_factor': random.choice([1.0, 1.25, 1.5]),
        'is_mobile': False,
        'has_touch': False,
        'timezone_id': 'Asia/Shanghai'
    }


def get_stealth_script(browser_features: Dict[str, Any]) -> str:
    """获取增强反检测脚本"""
    return """
        try {
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
                configurable: true
            });
        } catch (e) {}
    """

