# -*- coding: utf-8 -*-
"""
RSS 条目服务

功能：
- 获取 RSS 条目快照

公开接口：
- `get_feed_snapshot`

内部方法：
- `_materialize_entries`
"""

from __future__ import annotations

from typing import Iterable, List

import feedparser  # type: ignore
from sqlalchemy.orm import Session

from ..dao import RSSSourceDAO, RSSEntryDAO
from ..models import RSSSource, RSSEntry
from ..schemas import RSSFeedResponse, RSSSourceSchema

DEFAULT_ENTRY_LIMIT = 50


def get_feed_snapshot(db: Session, limit: int = DEFAULT_ENTRY_LIMIT) -> RSSFeedResponse:
    """获取订阅源与最近条目。"""
    from .source_service import ensure_default_source
    from .utils import _to_entry_schema

    ensure_default_source(db)
    source_dao = RSSSourceDAO(db)
    entry_dao = RSSEntryDAO(db)

    sources = source_dao.list_active()
    source_ids = [source.id for source in sources]
    entries = entry_dao.list_latest_by_sources(source_ids, limit)

    source_models = [
        RSSSourceSchema.model_validate(item) for item in source_dao.list_all()
    ]
    entry_models = [_to_entry_schema(entry) for entry in entries]
    return RSSFeedResponse(sources=source_models, entries=entry_models)


def _materialize_entries(
    db: Session,
    source: RSSSource,
    feed_entries: Iterable[feedparser.FeedParserDict],
) -> List[RSSEntry]:
    """将解析结果转换为数据库实体并去重。"""
    from .utils import _resolve_guid, _build_entry_signature, _materialize_entry

    entry_dao = RSSEntryDAO(db)
    materialized: List[RSSEntry] = []

    for entry in feed_entries:
        guid = _resolve_guid(entry)
        signature = _build_entry_signature(source.id, guid, entry)

        if entry_dao.exists_guid(guid) or entry_dao.exists_signature(signature):
            continue

        materialized.append(_materialize_entry(source.id, guid, signature, entry))

    return materialized
