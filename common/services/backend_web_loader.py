"""
Backend-Web 共享加载器

功能：
1. 按文件路径动态加载 backend-web 中可复用的服务模块
2. 为 common 共享层提供统一的类加载能力
"""
from __future__ import annotations

import importlib.util
import re
import sys
from functools import lru_cache
from pathlib import Path
from types import ModuleType


@lru_cache
def _get_repo_root() -> Path:
    """返回仓库根目录。"""
    return Path(__file__).resolve().parents[2]


@lru_cache
def _load_backend_web_module(module_name: str, relative_path: str) -> ModuleType:
    """按相对路径加载 backend-web 模块。"""
    source_path = _get_repo_root() / relative_path
    if not source_path.exists():
        raise FileNotFoundError(f"未找到 backend-web 模块文件: {source_path}")

    repo_root = str(_get_repo_root())
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

    spec = importlib.util.spec_from_file_location(module_name, source_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"无法加载 backend-web 模块: {source_path}")

    module = sys.modules.get(module_name)
    if module is None:
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        # backend-web 内部模块间使用绝对导入 `app.services.xxx`；在 scheduler/websocket
        # 等外部进程中 `app` 会被解析到各进程自己的 app 包导致 ModuleNotFoundError。
        # 此时把缺失的兄弟文件从 backend-web 按同路径加载并注册到 sys.modules 的
        # `app.services.xxx` 键上（import 机制命中 sys.modules 即直接返回），随后重试。
        for _ in range(10):
            try:
                spec.loader.exec_module(module)
                break
            except ModuleNotFoundError as e:
                missing = e.name or ""
                m = re.fullmatch(r"app\.services\.([A-Za-z0-9_.]+)", missing)
                if not m:
                    raise
                dep_rel = "backend-web/app/services/" + m.group(1).replace(".", "/") + ".py"
                dep_path = _get_repo_root() / dep_rel
                if not dep_path.exists():
                    raise
                _load_backend_web_module(missing, dep_rel)
    return module


@lru_cache
def load_backend_web_class(module_name: str, relative_path: str, class_name: str):
    """加载 backend-web 模块中的指定类。"""
    module = _load_backend_web_module(module_name, relative_path)
    target_class = getattr(module, class_name, None)
    if target_class is None:
        raise ImportError(f"模块 {module_name} 中不存在类 {class_name}")
    return target_class
