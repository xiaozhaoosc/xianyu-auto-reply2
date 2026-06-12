import sys
from pathlib import Path

# 将当前服务目录和项目根目录添加到系统路径以支持直接导入
current_dir = Path(__file__).parent.parent
project_root = current_dir.parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(project_root))

# 显式加载 _bootstrap
_bootstrap_file = current_dir / "_bootstrap.py"
if _bootstrap_file.exists():
    import importlib.util
    _spec = importlib.util.spec_from_file_location("_bootstrap", str(_bootstrap_file))
    _mod = importlib.util.module_from_spec(_spec)
    sys.modules['_bootstrap'] = _mod
    _spec.loader.exec_module(_mod)

import pytest
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from httpx import AsyncClient

from _bootstrap import app
from app.api.deps import get_db_session
# 导入公共数据库 Base 模块，以便可以在测试 SQLite 内存库中自动生成表结构
from common.models import Base

# 使用 SQLite 内存库作为测试隔离库
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

@pytest.fixture(scope="session", autouse=True)
async def initialize_test_db():
    """在测试会话开始前初始化 SQLite 内存表，结束后清理"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """每个测试函数专用的隔离数据库会话"""
    async with TestingSessionLocal() as session:
        yield session

@pytest.fixture
async def client(db_session) -> AsyncGenerator[AsyncClient, None]:
    """FastAPI 的测试客户端，自动重写数据库依赖注入"""
    async def override_get_db_session():
        yield db_session
        
    app.dependency_overrides[get_db_session] = override_get_db_session
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
