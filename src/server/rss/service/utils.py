# -*- coding: utf-8 -*-
"""
RSS 服务工具模块

功能：
- 提供 RSS 服务中共享的底层工具函数

公开接口：
- 无（仅内部使用）

内部方法：
- `_resolve_guid`
- `_resolve_datetime`
- `_resolve_content`
- `_normalize_datetime_utc`
- `_build_entry_signature`
- `_materialize_entry`
- `_to_entry_schema`
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import feedparser  # type: ignore

try:  # feedparser 部分版本将工具函数暴露在 util 下
    from feedparser.util import mktime_tz as feedparser_mktime_tz  # type: ignore
except Exception:  # pragma: no cover - 仅在少数版本缺失时触发
    feedparser_mktime_tz = None

from ..models import RSSEntry
from ..schemas import RSSEntrySchema


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
    return f"gen-{hashlib.sha1(fallback.encode('utf-8')).hexdigest()}"  # type: ignore


def _resolve_datetime(entry: feedparser.FeedParserDict) -> datetime | None:
    """解析条目的发布时间，统一转换为 UTC。"""
    text_value = entry.get("published") or entry.get("updated") or entry.get("created")
    if text_value:
        try:
            parsed = parsedate_to_datetime(text_value)  # type: ignore
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

        timestamp = mktime(struct_time)  # type: ignore
    return datetime.fromtimestamp(timestamp, tz=timezone.utc)


def _resolve_content(entry: feedparser.FeedParserDict) -> str | None:
    """解析条目正文内容。"""
    contents = entry.get("content")
    if isinstance(contents, list) and contents:
        for item in contents:
            value = item.get("value")
            if value:
                return value  # type: ignore
    if isinstance(contents, dict):
        value = contents.get("value")
        if value:
            return value
    return entry.get("summary")  # type: ignore


def _normalize_datetime_utc(value: datetime | None) -> datetime | None:
    """统一将时间转换为 UTC 时区。"""
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


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
        fetched_at=_normalize_datetime_utc(entry.fetched_at)
        or datetime.now(timezone.utc),
    )
