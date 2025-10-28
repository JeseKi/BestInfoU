# -*- coding: utf-8 -*-
"""
RSS 源管理服务

功能：
- 管理 RSS 订阅源：确保默认源存在、列出所有源

公开接口：
- `ensure_default_source`
- `list_sources`

内部方法：
- `_ensure_source_avatar`
- `_update_source_avatar`
"""

from __future__ import annotations

from typing import List

from loguru import logger
from sqlalchemy.orm import Session

from ..dao import RSSSourceDAO
from ..models import RSSSource
from ..schemas import RSSSourceSchema
from ..config import rss_config

DEFAULT_FEED_URL = rss_config.rss_default_feed_url
DEFAULT_SOURCE_NAME = rss_config.rss_default_source_name
DEFAULT_SOURCE_AVATAR = rss_config.rss_default_source_avatar
DEFAULT_SOURCE_HOMEPAGE = rss_config.rss_default_source_homepage


def ensure_default_source(db: Session) -> RSSSource:
    """确保默认订阅源存在。"""
    from .avatar_service import _ensure_source_avatar, _update_source_avatar

    source_dao = RSSSourceDAO(db)
    existing = source_dao.get_by_feed_url(DEFAULT_FEED_URL)
    if existing:
        if not existing.feed_avatar or existing.feed_avatar == DEFAULT_SOURCE_AVATAR:
            _ensure_source_avatar(db, existing)
            if (
                not existing.feed_avatar
                or existing.feed_avatar == DEFAULT_SOURCE_AVATAR
            ) and DEFAULT_SOURCE_AVATAR:
                _update_source_avatar(db, existing, DEFAULT_SOURCE_AVATAR)
        return existing
    logger.info("未找到默认订阅源，正在自动创建。")
    source = source_dao.create_source(
        name=DEFAULT_SOURCE_NAME,
        feed_url=DEFAULT_FEED_URL,
        homepage_url=DEFAULT_SOURCE_HOMEPAGE,
        feed_avatar=None,
        description="宝玉精选的优质中文内容。"
        "默认订阅源用于 MVP，后续可在后台管理页面维护。",
        category="technology",
        language="zh-CN",
        is_active=True,
        sync_interval_minutes=rss_config.rss_default_sync_interval_minutes,
    )
    _ensure_source_avatar(db, source)
    if not source.feed_avatar and DEFAULT_SOURCE_AVATAR:
        _update_source_avatar(db, source, DEFAULT_SOURCE_AVATAR)
    return source


def list_sources(db: Session) -> List[RSSSourceSchema]:
    """列出全部订阅源。"""
    ensure_default_source(db)
    sources = RSSSourceDAO(db).list_all()
    return [RSSSourceSchema.model_validate(source) for source in sources]
