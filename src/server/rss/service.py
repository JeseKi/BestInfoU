# -*- coding: utf-8 -*-
"""
RSS 服务

公开接口：
- `ensure_default_source`
- `list_sources`
- `get_feed_snapshot`
- `refresh_source`

内部方法：
- `_fetch_feed_content`
- `_parse_feed_entries`
- `_resolve_guid`
- `_resolve_datetime`
- `_resolve_content`
- `_normalize_datetime_utc`
- `_build_entry_signature`
- `_materialize_entry`
- `_materialize_entries`
- `_to_entry_schema`
- `_ensure_source_avatar`
- `_update_source_avatar`
- `_fetch_site_avatar`
- `_rel_contains`
- `_normalize_candidate_url`

文件功能：
- 聚合 RSS 模块的业务逻辑：确保默认订阅源存在、抓取并解析 RSS 内容、写入条目、产出 API 所需的数据模型。
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Iterable, List
from urllib.parse import urljoin

import httpx
import feedparser  # type: ignore
from bs4 import BeautifulSoup  # type: ignore
try:  # feedparser 部分版本将工具函数暴露在 util 下
    from feedparser.util import mktime_tz as feedparser_mktime_tz  # type: ignore
except Exception:  # pragma: no cover - 仅在少数版本缺失时触发
    feedparser_mktime_tz = None
from fastapi import HTTPException, status
from loguru import logger
from sqlalchemy.orm import Session

from .dao import RSSSourceDAO, RSSEntryDAO, FetchLogDAO
from .models import RSSSource, RSSEntry
from .schemas import (
    FetchLogSchema,
    RSSFeedResponse,
    RSSSourceSchema,
    RSSEntrySchema,
    SourceRefreshResponse,
)

DEFAULT_FEED_URL = "https://s.baoyu.io/feed.xml"
DEFAULT_SOURCE_NAME = "宝玉 RSS"
DEFAULT_SOURCE_AVATAR = "https://baoyu.io/favicon.ico"
DEFAULT_SOURCE_HOMEPAGE = "https://baoyu.io/"
HTTP_TIMEOUT = 20.0
DEFAULT_ENTRY_LIMIT = 50


class RSSFetchError(RuntimeError):
    """RSS 抓取失败"""


def ensure_default_source(db: Session) -> RSSSource:
    """确保默认订阅源存在。"""
    source_dao = RSSSourceDAO(db)
    existing = source_dao.get_by_feed_url(DEFAULT_FEED_URL)
    if existing:
        if not existing.feed_avatar or existing.feed_avatar == DEFAULT_SOURCE_AVATAR:
            _ensure_source_avatar(db, existing)
            if (
                (not existing.feed_avatar or existing.feed_avatar == DEFAULT_SOURCE_AVATAR)
                and DEFAULT_SOURCE_AVATAR
            ):
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
        sync_interval_minutes=60,
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


def get_feed_snapshot(db: Session, limit: int = DEFAULT_ENTRY_LIMIT) -> RSSFeedResponse:
    """获取订阅源与最近条目。"""
    ensure_default_source(db)
    source_dao = RSSSourceDAO(db)
    entry_dao = RSSEntryDAO(db)

    sources = source_dao.list_active()
    source_ids = [source.id for source in sources]
    entries = entry_dao.list_latest_by_sources(source_ids, limit)

    source_models = [RSSSourceSchema.model_validate(item) for item in source_dao.list_all()]
    entry_models = [
        _to_entry_schema(entry)
        for entry in entries
    ]
    return RSSFeedResponse(sources=source_models, entries=entry_models)


def refresh_source(db: Session, source_id: int) -> SourceRefreshResponse:
    """刷新指定订阅源。"""
    ensure_default_source(db)
    source_dao = RSSSourceDAO(db)
    entry_dao = RSSEntryDAO(db)
    log_dao = FetchLogDAO(db)

    source = source_dao.get_by_id(source_id)
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订阅源不存在",
        )
    if not source.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="订阅源已停用，无法刷新",
        )

    started_at = datetime.now(timezone.utc)
    entries_created = 0
    error_message: str | None = None

    try:
        feed_text = _fetch_feed_content(source.feed_url)
        parsed_entries = _parse_feed_entries(feed_text)
        materialized = _materialize_entries(db, source, parsed_entries)
        entries_created = entry_dao.bulk_insert(materialized)
        source_dao.update_last_synced(source.id, datetime.now(timezone.utc))
        if not source.feed_avatar or source.feed_avatar == DEFAULT_SOURCE_AVATAR:
            _ensure_source_avatar(db, source)
        logger.info(
            "订阅源刷新成功：source_id={}, 新增条目={}",
            source.id,
            entries_created,
        )
        status_value = "success"
    except RSSFetchError as exc:
        logger.error("订阅源刷新失败：source_id={}, 错误={}", source.id, exc)
        error_message = str(exc)
        status_value = "error"
    except Exception:
        logger.exception("订阅源刷新出现未预期的异常：source_id={}", source.id)
        error_message = "内部错误，请稍后再试"
        status_value = "error"
    finally:
        finished_at = datetime.now(timezone.utc)
        log = log_dao.create_log(
            source_id=source.id,
            status=status_value, # type: ignore
            started_at=started_at,
            finished_at=finished_at,
            error_message=error_message,
            entries_fetched=entries_created,
        )

    refreshed_source = source_dao.get_by_id(source.id)
    if not refreshed_source:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="刷新后无法获取订阅源信息",
        )

    return SourceRefreshResponse(
        source=RSSSourceSchema.model_validate(refreshed_source),
        fetch_log=FetchLogSchema.model_validate(log),
    )


def _fetch_feed_content(feed_url: str) -> str:
    """抓取 RSS 内容。"""
    try:
        with httpx.Client(timeout=HTTP_TIMEOUT, follow_redirects=True) as client:
            response = client.get(feed_url, headers={"User-Agent": "BestInfoU/0.1"})
            response.raise_for_status()
            return response.text
    except httpx.HTTPError as exc:
        raise RSSFetchError(f"抓取 RSS 源失败：{exc}") from exc


def _parse_feed_entries(feed_text: str) -> List[feedparser.FeedParserDict]:
    """解析 RSS 文本，返回条目集合。"""
    parsed = feedparser.parse(feed_text)
    if parsed.bozo:
        raise RSSFetchError(f"RSS 解析失败：{parsed.bozo_exception}")
    if not parsed.entries:
        return []
    return list(parsed.entries)


def _materialize_entry(
    source_id: int,
    guid: str,
    signature: str,
    entry: feedparser.FeedParserDict,
) -> RSSEntry:
    """从解析条目构建数据库实体。"""
    published_at = _normalize_datetime_utc(_resolve_datetime(entry))
    summary = entry.get("summary") or entry.get("subtitle")
    content = _resolve_content(entry)
    author = entry.get("author")
    link = entry.get("link")

    return RSSEntry(
        source_id=source_id,
        guid=guid,
        title=entry.get("title") or "未命名条目",
        summary=summary,
        content=content or summary,
        link=link,
        author=author,
        published_at=published_at,
        fetched_at=datetime.now(timezone.utc),
        hash_signature=signature,
    )


def _build_entry_signature(
    source_id: int,
    guid: str,
    entry: feedparser.FeedParserDict,
) -> str:
    """根据条目内容构建哈希签名，用于去重。"""
    parts = [
        str(source_id),
        guid,
        entry.get("title") or "",
        entry.get("link") or "",
        entry.get("summary") or "",
    ]
    raw = "||".join(parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _resolve_guid(entry: feedparser.FeedParserDict) -> str:
    """提取条目唯一标识。"""
    candidates = [
        entry.get("id"),
        entry.get("guid"),
        entry.get("link"),
    ]
    for candidate in candidates:
        if candidate:
            return str(candidate)
    fallback = entry.get("title") or "unknown"
    return f"gen-{hashlib.sha1(fallback.encode('utf-8')).hexdigest()}" # type: ignore


def _resolve_datetime(entry: feedparser.FeedParserDict) -> datetime | None:
    """解析条目的发布时间，统一转换为 UTC。"""
    text_value = entry.get("published") or entry.get("updated") or entry.get("created")
    if text_value:
        try:
            parsed = parsedate_to_datetime(text_value) # type: ignore
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except (TypeError, ValueError, AttributeError):
            pass

    struct_time = (
        entry.get("published_parsed")
        or entry.get("updated_parsed")
        or entry.get("created_parsed")
    )
    if not struct_time:
        return None
    # feedparser 返回的 struct_time 是本地时间，通过 timestamp 转换为 UTC。
    if feedparser_mktime_tz is not None:
        try:
            timestamp = feedparser_mktime_tz(struct_time)
        except (TypeError, ValueError):
            timestamp = None
    else:
        timestamp = None

    if timestamp is None:
        from time import mktime

        timestamp = mktime(struct_time) # type: ignore
    return datetime.fromtimestamp(timestamp, tz=timezone.utc)


def _resolve_content(entry: feedparser.FeedParserDict) -> str | None:
    """解析条目正文内容。"""
    contents = entry.get("content")
    if isinstance(contents, list) and contents:
        for item in contents:
            value = item.get("value")
            if value:
                return value # type: ignore
    if isinstance(contents, dict):
        value = contents.get("value")
        if value:
            return value
    return entry.get("summary") # type: ignore


def _normalize_datetime_utc(value: datetime | None) -> datetime | None:
    """统一将时间转换为 UTC 时区。"""
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _materialize_entries(
    db: Session,
    source: RSSSource,
    feed_entries: Iterable[feedparser.FeedParserDict],
) -> List[RSSEntry]:
    """将解析结果转换为数据库实体并去重。"""
    entry_dao = RSSEntryDAO(db)
    materialized: List[RSSEntry] = []

    for entry in feed_entries:
        guid = _resolve_guid(entry)
        signature = _build_entry_signature(source.id, guid, entry)

        if entry_dao.exists_guid(guid) or entry_dao.exists_signature(signature):
            continue

        materialized.append(
            _materialize_entry(source.id, guid, signature, entry)
        )

    return materialized


def _to_entry_schema(entry: RSSEntry) -> RSSEntrySchema:
    """将 ORM 条目转换为 Pydantic 模型。"""
    source = entry.source
    source_name = source.name if source else "未知来源"
    avatar = source.feed_avatar if source else None
    return RSSEntrySchema(
        id=entry.id,
        source_id=entry.source_id,
        source_name=source_name,
        feed_avatar=avatar,
        title=entry.title,
        summary=entry.summary,
        content=entry.content,
        link=entry.link,
        author=entry.author,
        published_at=_normalize_datetime_utc(entry.published_at),
        fetched_at=_normalize_datetime_utc(entry.fetched_at) or datetime.now(timezone.utc),
    )


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
            normalized = _normalize_candidate_url(base_url, href) # type: ignore
            if normalized:
                return normalized

    for attr in ("property", "name"):
        for key in ("og:image", "twitter:image"):
            meta = soup.find("meta", attrs={attr: key})
            content = meta.get("content") if meta else None
            if content:
                normalized = _normalize_candidate_url(base_url, content) # type: ignore
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
