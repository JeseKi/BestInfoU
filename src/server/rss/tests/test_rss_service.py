# -*- coding: utf-8 -*-
"""
RSS 服务层测试
"""

from __future__ import annotations

from datetime import datetime, timezone
from fastapi import HTTPException

from pydantic import HttpUrl
from pydantic_core import Url
import pytest
from sqlalchemy.orm import Session

from src.server.rss.service import (
    list_sources,
    refresh_source,
    create_source,
    update_source,
    delete_source,
)
from src.server.rss.service.fetch_service import RSSFetchError
from src.server.rss.service.source_service import (
    DEFAULT_FEED_URL,
    DEFAULT_SOURCE_AVATAR,
)
from src.server.rss.models import RSSEntry, FetchLog, RSSSource
from src.server.rss.schemas import (
    CreateRSSSourcePayload,
    UpdateRSSSourcePayload,
)


SAMPLE_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>示例频道</title>
    <link>https://example.com</link>
    <description>示例内容</description>
    <item>
      <title>第一篇文章</title>
      <link>https://example.com/post-1</link>
      <guid>post-1</guid>
      <description>第一篇摘要</description>
      <pubDate>Tue, 01 Jan 2024 00:00:00 +0000</pubDate>
      <author>alice@example.com</author>
    </item>
    <item>
      <title>第二篇文章</title>
      <link>https://example.com/post-2</link>
      <guid>post-2</guid>
      <description>第二篇摘要</description>
      <pubDate>Wed, 02 Jan 2024 12:30:00 +0000</pubDate>
      <author>bob@example.com</author>
    </item>
  </channel>
</rss>
"""


def _setup_default_source(db: Session) -> RSSSource:
    """确保测试使用的默认订阅源存在。"""
    sources = list_sources(db)
    assert sources, "默认订阅源未创建"
    return db.query(RSSSource).filter(RSSSource.feed_url == DEFAULT_FEED_URL).one()


def test_list_sources_contains_default(test_db_session: Session) -> None:
    """列出订阅源时应包含默认来源。"""
    sources = list_sources(test_db_session)
    assert any(source.feed_url == DEFAULT_FEED_URL for source in sources)
    assert any(source.feed_avatar == DEFAULT_SOURCE_AVATAR for source in sources)


def test_refresh_source_success_inserts_entries(
    monkeypatch: pytest.MonkeyPatch, test_db_session: Session
) -> None:
    """刷新订阅源成功时写入条目和日志。"""

    def fake_fetch(_: str) -> str:
        return SAMPLE_FEED

    monkeypatch.setattr(
        "src.server.rss.service.fetch_service._fetch_feed_content", fake_fetch
    )

    source = _setup_default_source(test_db_session)

    result = refresh_source(test_db_session, source.id)

    assert result.fetch_log.status == "success"
    assert result.fetch_log.entries_fetched == 2
    assert result.source.id == source.id
    assert result.source.feed_avatar == DEFAULT_SOURCE_AVATAR

    entries = (
        test_db_session.query(RSSEntry).filter(RSSEntry.source_id == source.id).all()
    )
    assert len(entries) == 2

    first = next(entry for entry in entries if entry.guid == "post-1")
    assert first.title == "第一篇文章"
    assert first.author == "alice@example.com"
    assert first.source.feed_avatar == DEFAULT_SOURCE_AVATAR
    first_published = first.published_at
    if first_published:
        if first_published.tzinfo is None:
            first_published = first_published.replace(tzinfo=timezone.utc)
        assert first_published == datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)

    logs = test_db_session.query(FetchLog).filter(FetchLog.source_id == source.id).all()
    assert len(logs) == 1
    assert logs[0].status == "success"


def test_refresh_source_is_idempotent(
    monkeypatch: pytest.MonkeyPatch, test_db_session: Session
) -> None:
    """重复刷新不应写入重复条目。"""

    def fake_fetch(_: str) -> str:
        return SAMPLE_FEED

    monkeypatch.setattr(
        "src.server.rss.service.fetch_service._fetch_feed_content", fake_fetch
    )

    source = _setup_default_source(test_db_session)

    first = refresh_source(test_db_session, source.id)
    assert first.fetch_log.entries_fetched == 2

    second = refresh_source(test_db_session, source.id)
    assert second.fetch_log.entries_fetched == 0

    total_entries = (
        test_db_session.query(RSSEntry).filter(RSSEntry.source_id == source.id).count()
    )
    assert total_entries == 2


def test_refresh_source_records_error(
    monkeypatch: pytest.MonkeyPatch, test_db_session: Session
) -> None:
    """抓取失败时应记录错误日志并返回错误状态。"""

    class DummyError(RSSFetchError):
        pass

    def fake_fetch(_: str) -> str:
        raise DummyError("模拟抓取失败")

    monkeypatch.setattr(
        "src.server.rss.service.fetch_service._fetch_feed_content", fake_fetch
    )

    source = _setup_default_source(test_db_session)

    result = refresh_source(test_db_session, source.id)

    assert result.fetch_log.status == "error"
    assert result.fetch_log.entries_fetched == 0
    assert result.fetch_log.error_message == "模拟抓取失败"

    logs = test_db_session.query(FetchLog).filter(FetchLog.source_id == source.id).all()
    assert len(logs) == 1
    assert logs[0].status == "error"


def _create_sample_source(
    db: Session,
    *,
    name: str = "示例订阅源",
    feed_url: HttpUrl = Url("https://example.com/feed.xml"),
) -> RSSSource:
    """创建测试用订阅源。"""
    payload = CreateRSSSourcePayload(
        name=name,
        feed_url=feed_url,
        homepage_url=Url("https://example.com"),
        description="用于测试的订阅源",
        category="technology",
        language="zh-CN",
        is_active=True,
    )
    created = create_source(db, payload)
    return db.query(RSSSource).filter(RSSSource.id == created.id).one()


def test_create_source_success(
    test_db_session: Session,
) -> None:
    """能够成功创建新的订阅源。"""
    source = _create_sample_source(test_db_session)
    assert source.name == "示例订阅源"
    assert source.feed_url == "https://example.com/feed.xml"
    assert source.is_active is True


def test_create_source_duplicate_feed_url(
    test_db_session: Session,
) -> None:
    """重复的订阅链接应触发冲突错误。"""
    _create_sample_source(test_db_session)
    with pytest.raises(HTTPException) as excinfo:
        create_source(
            test_db_session,
            CreateRSSSourcePayload(
                name="重复链接",
                feed_url=Url("https://example.com/feed.xml"),
            ),
        )
    assert excinfo.value.status_code == 400


def test_update_source_partial_fields_and_toggle_status(
    test_db_session: Session,
) -> None:
    """部分字段更新与启停切换后应正确落库。"""
    source = _create_sample_source(test_db_session)

    updated = update_source(
        test_db_session,
        source.id,
        UpdateRSSSourcePayload(
            name="更新后的名称",
            category="news",
            is_active=False,
        ),
    )
    assert updated.name == "更新后的名称"
    assert updated.category == "news"
    assert updated.is_active is False

    refreshed = test_db_session.query(RSSSource).filter(RSSSource.id == source.id).one()
    assert refreshed.name == "更新后的名称"
    assert refreshed.is_active is False


def test_delete_source_success(
    test_db_session: Session,
) -> None:
    """删除非默认订阅源成功后应从数据库移除。"""
    source = _create_sample_source(
        test_db_session,
        name="可删除的订阅源",
        feed_url=Url("https://example.com/delete-me.xml"),
    )
    delete_source(test_db_session, source.id)
    exists = (
        test_db_session.query(RSSSource)
        .filter(RSSSource.feed_url == "https://example.com/delete-me.xml")
        .first()
    )
    assert exists is None


def test_delete_source_protect_default(
    test_db_session: Session,
) -> None:
    """默认订阅源不允许被删除。"""
    default = _setup_default_source(test_db_session)
    with pytest.raises(HTTPException) as excinfo:
        delete_source(test_db_session, default.id)
    assert excinfo.value.status_code == 400


def test_refresh_source_not_found(
    test_db_session: Session,
) -> None:
    """刷新不存在的订阅源应返回 404。"""
    with pytest.raises(HTTPException) as excinfo:
        refresh_source(test_db_session, 999999)
    assert excinfo.value.status_code == 404


def test_refresh_source_inactive(
    test_db_session: Session,
) -> None:
    """刷新已停用的订阅源应返回 400。"""
    source = _create_sample_source(
        test_db_session,
        name="停用刷新校验",
        feed_url=Url("https://example.com/inactive.xml"),
    )
    update_source(
        test_db_session,
        source.id,
        UpdateRSSSourcePayload(is_active=False),
    )
    with pytest.raises(HTTPException) as excinfo:
        refresh_source(test_db_session, source.id)
    assert excinfo.value.status_code == 400
