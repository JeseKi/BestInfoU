# -*- coding: utf-8 -*-
"""
RSS 数据模型

公开接口：
- `RSSSource`
- `RSSEntry`
- `FetchLog`

内部方法：
- 无

文件功能：
- 定义 RSS 模块使用的 SQLAlchemy ORM 模型，描述订阅源、条目以及抓取日志结构。

说明：
- 所有时间字段统一使用 UTC。
- 条目通过 `guid` 与 `hash_signature` 双重约束避免重复写入。
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import (
    String,
    Integer,
    DateTime,
    Text,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.server.database import Base


class RSSSource(Base):
    __tablename__ = "rss_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    feed_url: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    homepage_url: Mapped[Optional[str]] = mapped_column(String(512), default=None)
    feed_avatar: Mapped[Optional[str]] = mapped_column(String(512), default=None)
    description: Mapped[Optional[str]] = mapped_column(Text, default=None)
    language: Mapped[Optional[str]] = mapped_column(String(32), default=None)
    category: Mapped[Optional[str]] = mapped_column(String(64), default=None)
    is_active: Mapped[bool] = mapped_column(Integer, nullable=False, default=1)
    sync_interval_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=60
    )
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=None
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    entries: Mapped[List["RSSEntry"]] = relationship(
        "RSSEntry",
        back_populates="source",
        cascade="all, delete-orphan",
    )
    fetch_logs: Mapped[List["FetchLog"]] = relationship(
        "FetchLog",
        back_populates="source",
        cascade="all, delete-orphan",
    )


class RSSEntry(Base):
    __tablename__ = "rss_entries"
    __table_args__ = (
        UniqueConstraint("guid", name="uq_rss_entries_guid"),
        UniqueConstraint("hash_signature", name="uq_rss_entries_hash_signature"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("rss_sources.id", ondelete="CASCADE"),
        nullable=False,
    )
    guid: Mapped[str] = mapped_column(String(512), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, default=None)
    content: Mapped[Optional[str]] = mapped_column(Text, default=None)
    link: Mapped[Optional[str]] = mapped_column(String(512), default=None)
    author: Mapped[Optional[str]] = mapped_column(String(128), default=None)
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=None
    )
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    hash_signature: Mapped[str] = mapped_column(String(128), nullable=False)

    source: Mapped["RSSSource"] = relationship("RSSSource", back_populates="entries")


class FetchLog(Base):
    __tablename__ = "rss_fetch_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("rss_sources.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="success")
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=None
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, default=None)
    entries_fetched: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    source: Mapped["RSSSource"] = relationship("RSSSource", back_populates="fetch_logs")
