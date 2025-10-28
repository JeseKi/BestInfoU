# -*- coding: utf-8 -*-
"""
RSS 模块入口

公开接口：
- 无

内部方法：
- 无

文件功能：
- 暴露 RSS 模块，使其可被 FastAPI 应用加载。
"""

from .config import rss_config

__all__ = ["rss_config"]
