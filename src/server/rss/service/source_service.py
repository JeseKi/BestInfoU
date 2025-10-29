# -*- coding: utf-8 -*-
"""
RSS 源管理服务

功能：
- 管理 RSS 订阅源：确保默认源存在、提供增删改查能力

公开接口：
- `ensure_default_source`
- `list_sources`
- `create_source`
- `update_source`
- `delete_source`

内部方法：
- `_ensure_source_avatar`
- `_update_source_avatar`
"""

from __future__ import annotations

from typing import List

from fastapi import HTTPException, status
from loguru import logger
from sqlalchemy.orm import Session

from ..dao import RSSSourceDAO
from ..models import RSSSource
from ..schemas import (
    RSSSourceSchema,
    CreateRSSSourcePayload,
    UpdateRSSSourcePayload,
)
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


def create_source(
    db: Session,
    payload: CreateRSSSourcePayload,
) -> RSSSourceSchema:
    """创建新的订阅源。"""
    from .avatar_service import _ensure_source_avatar

    ensure_default_source(db)
    source_dao = RSSSourceDAO(db)

    normalized_feed_url = str(payload.feed_url)
    homepage_url = str(payload.homepage_url) if payload.homepage_url else None
    avatar_url = str(payload.feed_avatar) if payload.feed_avatar else None

    if source_dao.get_by_feed_url(normalized_feed_url):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="订阅链接已存在，请勿重复添加。",
        )
    if source_dao.get_by_name(payload.name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="订阅源名称已存在，请更换名称。",
        )

    source = source_dao.create_source(
        name=payload.name,
        feed_url=normalized_feed_url,
        homepage_url=homepage_url,
        feed_avatar=avatar_url,
        description=payload.description,
        language=payload.language,
        category=payload.category,
        is_active=payload.is_active,
    )
    if not source.feed_avatar:
        _ensure_source_avatar(db, source)

    return RSSSourceSchema.model_validate(source)


def update_source(
    db: Session,
    source_id: int,
    payload: UpdateRSSSourcePayload,
) -> RSSSourceSchema:
    """更新订阅源配置。"""
    from .avatar_service import _ensure_source_avatar

    ensure_default_source(db)
    source_dao = RSSSourceDAO(db)

    source = source_dao.get_by_id(source_id)
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订阅源不存在。",
        )

    next_feed_url = str(payload.feed_url) if payload.feed_url else None
    homepage_url = str(payload.homepage_url) if payload.homepage_url else None
    avatar_url = str(payload.feed_avatar) if payload.feed_avatar else None

    if next_feed_url and next_feed_url != source.feed_url:
        exists = source_dao.get_by_feed_url(next_feed_url)
        if exists and exists.id != source.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="订阅链接已存在，请勿重复添加。",
            )
    if payload.name and payload.name != source.name:
        exists = source_dao.get_by_name(payload.name)
        if exists and exists.id != source.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="订阅源名称已存在，请更换名称。",
            )

    updated = source_dao.update_source(
        source,
        name=payload.name,
        feed_url=next_feed_url,
        homepage_url=homepage_url,
        feed_avatar=avatar_url,
        description=payload.description,
        language=payload.language,
        category=payload.category,
        is_active=payload.is_active,
    )

    # 若启用或更新后缺少头像，尝试自动补全
    if not updated.feed_avatar:
        _ensure_source_avatar(db, updated)

    return RSSSourceSchema.model_validate(updated)


def delete_source(db: Session, source_id: int) -> None:
    """删除指定订阅源。"""
    ensure_default_source(db)
    source_dao = RSSSourceDAO(db)

    source = source_dao.get_by_id(source_id)
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订阅源不存在。",
        )
    if source.feed_url == DEFAULT_FEED_URL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="默认订阅源不允许删除。",
        )

    source_dao.delete_source(source)
