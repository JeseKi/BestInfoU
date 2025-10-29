# -*- coding: utf-8 -*-
"""
RSS 模块入口

公开接口：
- `rss_config`
- `router`
- `list_sources`
- `create_source`
- `update_source`
- `delete_source`
- `get_feed_snapshot`
- `refresh_source`

内部方法：
- 无

文件功能：
- 暴露 RSS 模块的主要能力，供 FastAPI 应用加载并在其他模块复用服务层接口。
"""

from typing import Any

from .config import rss_config

__all__ = [
    "rss_config",
    "router",
    "list_sources",
    "create_source",
    "update_source",
    "delete_source",
    "get_feed_snapshot",
    "refresh_source",
]


def __getattr__(name: str) -> Any:
    """按需加载子模块，避免导入时出现循环依赖。"""
    if name == "router":
        from .router import router as value
    elif name in {
        "list_sources",
        "create_source",
        "update_source",
        "delete_source",
        "get_feed_snapshot",
        "refresh_source",
    }:
        from . import service as service_module

        value = getattr(service_module, name)
    else:
        raise AttributeError(f"module 'src.server.rss' has no attribute '{name}'")
    return value


def __dir__() -> list[str]:
    return sorted(__all__)
