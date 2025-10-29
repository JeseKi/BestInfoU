# -*- coding: utf-8 -*-
"""
RSS DAO

- 公开接口：
    - `RSSSourceDAO`
    - `RSSEntryDAO`
    - `FetchLogDAO`

内部方法：
- `_normalize_is_active`

文件功能：
- 为 RSS 模块提供面向数据库的访问层，封装订阅源、条目及抓取日志的常见 CRUD 操作。
"""

from __future__ import annotations

from datetime import datetime
from typing import Iterable, List, Sequence

from sqlalchemy import select, func, update
from sqlalchemy.orm import selectinload

from src.server.dao.dao_base import BaseDAO
from .models import RSSSource, RSSEntry, FetchLog


def _normalize_is_active(value: bool | int) -> bool:
    """标准化启用状态为布尔值。"""
    return bool(value)


class RSSSourceDAO(BaseDAO):
    """订阅源 DAO"""

    def list_all(self) -> List[RSSSource]:
        stmt = select(RSSSource).order_by(RSSSource.id.asc())
        return list(self.db_session.scalars(stmt))

    def list_active(self) -> List[RSSSource]:
        stmt = (
            select(RSSSource)
            .where(RSSSource.is_active.is_(True))
            .order_by(RSSSource.id.asc())
        )
        return list(self.db_session.scalars(stmt))

    def get_by_id(self, source_id: int) -> RSSSource | None:
        stmt = select(RSSSource).where(RSSSource.id == source_id)
        return self.db_session.scalars(stmt).first()

    def get_by_feed_url(self, feed_url: str) -> RSSSource | None:
        stmt = select(RSSSource).where(RSSSource.feed_url == feed_url)
        return self.db_session.scalars(stmt).first()

    def get_by_name(self, name: str) -> RSSSource | None:
        stmt = select(RSSSource).where(RSSSource.name == name)
        return self.db_session.scalars(stmt).first()

    def create_source(
        self,
        *,
        name: str,
        feed_url: str,
        homepage_url: str | None = None,
        feed_avatar: str | None = None,
        description: str | None = None,
        language: str | None = None,
        category: str | None = None,
        is_active: bool = True,
    ) -> RSSSource:
        source = RSSSource(
            name=name,
            feed_url=feed_url,
            homepage_url=homepage_url,
            feed_avatar=feed_avatar,
            description=description,
            language=language,
            category=category,
            is_active=_normalize_is_active(is_active),
        )
        self.db_session.add(source)
        self.db_session.commit()
        self.db_session.refresh(source)
        return source

    def update_source(
        self,
        source: RSSSource,
        *,
        name: str | None = None,
        feed_url: str | None = None,
        homepage_url: str | None = None,
        feed_avatar: str | None = None,
        description: str | None = None,
        language: str | None = None,
        category: str | None = None,
        is_active: bool | None = None,
    ) -> RSSSource:
        if name is not None:
            source.name = name
        if feed_url is not None:
            source.feed_url = feed_url
        if homepage_url is not None:
            source.homepage_url = homepage_url
        if feed_avatar is not None:
            source.feed_avatar = feed_avatar
        if description is not None:
            source.description = description
        if language is not None:
            source.language = language
        if category is not None:
            source.category = category
        if is_active is not None:
            source.is_active = bool(is_active)

        self.db_session.add(source)
        self.db_session.commit()
        self.db_session.refresh(source)
        return source

    def delete_source(self, source: RSSSource) -> None:
        self.db_session.delete(source)
        self.db_session.commit()

    def update_last_synced(self, source_id: int, timestamp: datetime) -> None:
        stmt = (
            update(RSSSource)
            .where(RSSSource.id == source_id)
            .values(last_synced_at=timestamp, updated_at=timestamp)
        )
        self.db_session.execute(stmt)
        self.db_session.commit()


class RSSEntryDAO(BaseDAO):
    """RSS 条目 DAO"""

    def list_latest_by_sources(
        self,
        source_ids: Sequence[int],
        limit: int,
    ) -> List[RSSEntry]:
        if not source_ids:
            return []
        stmt = (
            select(RSSEntry)
            .where(RSSEntry.source_id.in_(source_ids))
            .order_by(RSSEntry.published_at.desc().nullslast(), RSSEntry.id.desc())
            .limit(limit)
            .options(selectinload(RSSEntry.source))
        )
        return list(self.db_session.scalars(stmt))

    def exists_guid(self, guid: str) -> bool:
        stmt = select(func.count()).select_from(RSSEntry).where(RSSEntry.guid == guid)
        return bool(self.db_session.execute(stmt).scalar() or 0)

    def exists_signature(self, signature: str) -> bool:
        stmt = (
            select(func.count())
            .select_from(RSSEntry)
            .where(RSSEntry.hash_signature == signature)
        )
        return bool(self.db_session.execute(stmt).scalar() or 0)

    def bulk_insert(self, entries: Iterable[RSSEntry]) -> int:
        count = 0
        for entry in entries:
            self.db_session.add(entry)
            count += 1
        if count:
            self.db_session.commit()
        return count


class FetchLogDAO(BaseDAO):
    """抓取日志 DAO"""

    def create_log(
        self,
        *,
        source_id: int,
        status: str,
        started_at: datetime,
        finished_at: datetime | None,
        error_message: str | None,
        entries_fetched: int,
    ) -> FetchLog:
        log = FetchLog(
            source_id=source_id,
            status=status,
            started_at=started_at,
            finished_at=finished_at,
            error_message=error_message,
            entries_fetched=entries_fetched,
        )
        self.db_session.add(log)
        self.db_session.commit()
        self.db_session.refresh(log)
        return log
