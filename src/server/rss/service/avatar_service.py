# -*- coding: utf-8 -*-
"""
RSS 头像服务

功能：
- 获取和更新 RSS 源的头像

公开接口：
- 无（仅内部使用）

内部方法：
- `_ensure_source_avatar`
- `_update_source_avatar`
- `_fetch_site_avatar`
- `_rel_contains`
- `_normalize_candidate_url`
"""

from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup  # type: ignore
from loguru import logger
from sqlalchemy.orm import Session

from ..models import RSSSource
from ..config import rss_config

HTTP_TIMEOUT = rss_config.rss_http_timeout
DEFAULT_SOURCE_AVATAR = rss_config.rss_default_source_avatar


def _ensure_source_avatar(db: Session, source: RSSSource) -> None:
    """为订阅源补齐头像（仅在缺失或仍为默认占位时触发）。"""
    if source.feed_avatar and source.feed_avatar != DEFAULT_SOURCE_AVATAR:
        return
    homepage_url = source.homepage_url
    if not homepage_url:
        return
    try:
        avatar_url = _fetch_site_avatar(homepage_url)
    except Exception as exc:  # pragma: no cover - 网络异常
        logger.warning("解析站点头像失败：source_id=%s, error=%s", source.id, exc)
        return
    if not avatar_url:
        return
    _update_source_avatar(db, source, avatar_url)


def _update_source_avatar(db: Session, source: RSSSource, avatar_url: str) -> None:
    """将头像地址写回数据库。"""
    if not avatar_url:
        return
    if source.feed_avatar == avatar_url:
        return
    try:
        source.feed_avatar = avatar_url
        source.updated_at = datetime.now(timezone.utc)
        db.add(source)
        db.commit()
        db.refresh(source)
        logger.info("订阅源头像已更新：source_id=%s", source.id)
    except Exception as exc:  # pragma: no cover - 极端数据库错误
        db.rollback()
        logger.warning("订阅源头像写入失败：source_id=%s, error=%s", source.id, exc)


def _fetch_site_avatar(website_url: str) -> str | None:
    """尝试从站点主页解析 favicon / og:image 作为头像。"""
    try:
        response = httpx.get(
            website_url,
            timeout=HTTP_TIMEOUT,
            follow_redirects=True,
            headers={"User-Agent": "BestInfoU/0.1"},
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.warning("站点头像请求失败：url=%s, error=%s", website_url, exc)
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    base_url = str(response.url)

    rel_priority = [
        "apple-touch-icon",
        "apple-touch-icon-precomposed",
        "mask-icon",
        "shortcut icon",
        "icon",
    ]

    for rel_keyword in rel_priority:
        link = soup.find("link", rel=lambda value: _rel_contains(value, rel_keyword))
        href = link.get("href") if link else None
        if href:
            normalized = _normalize_candidate_url(base_url, href)  # type: ignore
            if normalized:
                return normalized

    for attr in ("property", "name"):
        for key in ("og:image", "twitter:image"):
            meta = soup.find("meta", attrs={attr: key})
            content = meta.get("content") if meta else None
            if content:
                normalized = _normalize_candidate_url(base_url, content)  # type: ignore
                if normalized:
                    return normalized

    return None


def _rel_contains(value: object, keyword: str) -> bool:
    """判断 rel 属性是否包含指定关键字。"""
    if not value:
        return False
    keyword_lower = keyword.lower()
    if isinstance(value, (list, tuple, set)):
        return any(keyword_lower in str(item).lower() for item in value)
    raw = str(value).lower()
    return keyword_lower in raw


def _normalize_candidate_url(base: str, candidate: str) -> str | None:
    """将相对路径归一化为绝对地址。"""
    if not candidate:
        return None
    candidate = candidate.strip()
    if not candidate:
        return None
    normalized = urljoin(base, candidate)
    return normalized or None
