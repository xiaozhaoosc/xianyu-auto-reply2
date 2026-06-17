"""
通用 aiohttp 代理 connector 工具

解决：所有散落在各处的 aiohttp.ClientSession() 裸调用不走代理的问题。
统一从数据库读取系统级代理配置（xy_system_settings），
并自动构建 ProxyConnector / TCPConnector。

用法：
    from common.utils.proxy_connector import create_proxy_connector

    connector = await create_proxy_connector()
    async with aiohttp.ClientSession(connector=connector) as session:
        ...
"""

import asyncio
import logging
from typing import Optional, Tuple

import aiohttp

logger = logging.getLogger(__name__)

# 缓存：避免每次请求都查 DB / 调代理 API
_cached_connector: Optional[aiohttp.BaseConnector] = None
_cached_proxy_url: Optional[str] = None
_cache_timestamp: float = 0
_CACHE_TTL = 300  # 5 分钟刷新一次


def _parse_proxy_url(url: str) -> Optional[Tuple[str, str, int, Optional[str], Optional[str]]]:
    """解析代理 URL → (proxy_type, host, port, user, pass)"""
    if not url:
        return None
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        scheme = parsed.scheme.lower()
        if scheme not in ('http', 'https', 'socks5', 'socks4'):
            return None
        host = parsed.hostname
        port = parsed.port
        if not host or not port:
            return None
        user = parsed.username or None
        password = parsed.password or None
        return (scheme, host, port, user, password)
    except Exception as e:
        logger.warning(f"解析代理 URL 失败: {url} → {e}")
        return None


async def _load_system_proxy_url() -> Optional[str]:
    """从 DB 读系统级代理配置，若启用则调 API 获取代理 endpoint"""
    try:
        from sqlalchemy import select
        from common.db.session import async_session_maker
        from common.models.system_setting import SystemSetting

        async with async_session_maker() as session:
            stmt = select(SystemSetting.key, SystemSetting.value).where(
                SystemSetting.key.in_(['proxy.api_url', 'proxy.enabled'])
            )
            result = await session.execute(stmt)
            rows = {key: value for key, value in result.all()}

        enabled = str(rows.get('proxy.enabled') or 'false').strip().lower() in ('true', '1', 'yes', 'on')
        api_url = str(rows.get('proxy.api_url') or '').strip()

        if not enabled or not api_url:
            return None

        # 调代理 API 获取 endpoint（纯文本 IP:PORT）
        timeout = aiohttp.ClientTimeout(total=5)
        async with aiohttp.ClientSession(timeout=timeout) as tmp_session:
            async with tmp_session.get(api_url) as resp:
                if resp.status != 200:
                    logger.warning(f"代理 API 返回 {resp.status}")
                    return None
                text = (await resp.text()).strip()
                if not text:
                    return None
                # 取第一行
                first_line = text.split('\n')[0].strip()
                if ':' not in first_line:
                    logger.warning(f"代理 API 返回格式异常: {first_line}")
                    return None
                host, port_str = first_line.rsplit(':', 1)
                port = int(port_str)
                return f"http://{host}:{port}"

    except Exception as e:
        logger.debug(f"读取系统代理配置失败（降级为直连）: {e}")
        return None


async def create_proxy_connector() -> aiohttp.BaseConnector:
    """创建带代理的 aiohttp connector（带缓存）

    优先级：系统代理 API → 直连
    """
    global _cached_connector, _cached_proxy_url, _cache_timestamp

    import time
    now = time.time()

    # 缓存命中且未过期
    if _cached_connector is not None and (now - _cache_timestamp) < _CACHE_TTL:
        return _cached_connector

    # 关闭旧 connector
    if _cached_connector is not None and not _cached_connector.closed:
        await _cached_connector.close()

    proxy_url = await _load_system_proxy_url()

    if proxy_url:
        parsed = _parse_proxy_url(proxy_url)
        if parsed:
            scheme, host, port, user, password = parsed
            try:
                from aiohttp_socks import ProxyConnector, ProxyType
                proxy_type_map = {
                    'socks5': ProxyType.SOCKS5,
                    'socks4': ProxyType.SOCKS4,
                    'http': ProxyType.HTTP,
                    'https': ProxyType.HTTP,
                }
                socks_type = proxy_type_map.get(scheme, ProxyType.HTTP)
                connector = ProxyConnector(
                    proxy_type=socks_type,
                    host=host,
                    port=port,
                    username=user,
                    password=password,
                    rdns=True,
                )
                logger.info(f"aiohttp 通用 connector 走代理: {scheme}://{host}:{port}")
                _cached_connector = connector
                _cached_proxy_url = proxy_url
                _cache_timestamp = now
                return connector
            except ImportError:
                logger.error("aiohttp-socks 未安装，通用 connector 降级为直连")
            except Exception as e:
                logger.error(f"构造代理 connector 失败: {e}，降级为直连")

    # 直连
    connector = aiohttp.TCPConnector(limit=50, limit_per_host=10)
    _cached_connector = connector
    _cached_proxy_url = None
    _cache_timestamp = now
    return connector


async def get_httpx_proxy() -> Optional[str]:
    """获取 httpx 兼容的代理 URL（带缓存，复用同一缓存周期）

    返回值可直接传给 httpx.AsyncClient(proxy=...) 参数。
    无代理时返回 None。

    用法：
        from common.utils.proxy_connector import get_httpx_proxy

        proxy = await get_httpx_proxy()
        async with httpx.AsyncClient(proxy=proxy) as client:
            ...
    """
    global _cached_proxy_url, _cache_timestamp

    import time
    now = time.time()

    # 缓存命中且未过期 —— 直接返回上次的 proxy URL
    if (now - _cache_timestamp) < _CACHE_TTL and _cached_connector is not None:
        return _cached_proxy_url

    # 缓存过期，重新加载
    proxy_url = await _load_system_proxy_url()
    _cached_proxy_url = proxy_url
    _cache_timestamp = now
    return proxy_url


async def create_aiohttp_session(**kwargs) -> aiohttp.ClientSession:
    """创建带代理的 aiohttp ClientSession（便捷方法）

    用法：
        async with await create_aiohttp_session() as session:
            async with session.get(url) as resp:
                ...
    """
    connector = await create_proxy_connector()
    return aiohttp.ClientSession(connector=connector, **kwargs)


async def invalidate_proxy_cache():
    """强制刷新代理缓存（代理切换后调用）"""
    global _cached_connector, _cached_proxy_url, _cache_timestamp
    if _cached_connector is not None and not _cached_connector.closed:
        await _cached_connector.close()
    _cached_connector = None
    _cached_proxy_url = None
    _cache_timestamp = 0
