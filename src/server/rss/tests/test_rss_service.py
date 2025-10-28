# -*- coding: utf-8 -*-
"""
RSS 服务层测试
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy.orm import Session

from src.server.rss import service
from src.server.rss.models import RSSEntry, FetchLog, RSSSource


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
    sources = service.list_sources(db)
    assert sources, "默认订阅源未创建"
    return db.query(RSSSource).filter(RSSSource.feed_url == service.DEFAULT_FEED_URL).one()


def test_list_sources_contains_default(test_db_session: Session) -> None:
    """列出订阅源时应包含默认来源。"""
    sources = service.list_sources(test_db_session)
    assert any(source.feed_url == service.DEFAULT_FEED_URL for source in sources)


def test_refresh_source_success_inserts_entries(monkeypatch: pytest.MonkeyPatch, test_db_session: Session) -> None:
    """刷新订阅源成功时写入条目和日志。"""

    def fake_fetch(_: str) -> str:
        return SAMPLE_FEED

    monkeypatch.setattr(service, "_fetch_feed_content", fake_fetch)

    source = _setup_default_source(test_db_session)

    result = service.refresh_source(test_db_session, source.id)

    assert result.fetch_log.status == "success"
    assert result.fetch_log.entries_fetched == 2
    assert result.source.id == source.id

    entries = test_db_session.query(RSSEntry).filter(RSSEntry.source_id == source.id).all()
    assert len(entries) == 2

    first = next(entry for entry in entries if entry.guid == "post-1")
    assert first.title == "第一篇文章"
    assert first.author == "alice@example.com"
    first_published = first.published_at
    if first_published:
        if first_published.tzinfo is None:
            first_published = first_published.replace(tzinfo=timezone.utc)
        assert first_published == datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)

    logs = test_db_session.query(FetchLog).filter(FetchLog.source_id == source.id).all()
    assert len(logs) == 1
    assert logs[0].status == "success"


def test_refresh_source_is_idempotent(monkeypatch: pytest.MonkeyPatch, test_db_session: Session) -> None:
    """重复刷新不应写入重复条目。"""

    def fake_fetch(_: str) -> str:
        return SAMPLE_FEED

    monkeypatch.setattr(service, "_fetch_feed_content", fake_fetch)

    source = _setup_default_source(test_db_session)

    first = service.refresh_source(test_db_session, source.id)
    assert first.fetch_log.entries_fetched == 2

    second = service.refresh_source(test_db_session, source.id)
    assert second.fetch_log.entries_fetched == 0

    total_entries = test_db_session.query(RSSEntry).filter(RSSEntry.source_id == source.id).count()
    assert total_entries == 2


def test_refresh_source_records_error(monkeypatch: pytest.MonkeyPatch, test_db_session: Session) -> None:
    """抓取失败时应记录错误日志并返回错误状态。"""

    class DummyError(service.RSSFetchError):
        pass

    def fake_fetch(_: str) -> str:
        raise DummyError("模拟抓取失败")

    monkeypatch.setattr(service, "_fetch_feed_content", fake_fetch)

    source = _setup_default_source(test_db_session)

    result = service.refresh_source(test_db_session, source.id)

    assert result.fetch_log.status == "error"
    assert result.fetch_log.entries_fetched == 0
    assert result.fetch_log.error_message == "模拟抓取失败"

    logs = test_db_session.query(FetchLog).filter(FetchLog.source_id == source.id).all()
    assert len(logs) == 1
    assert logs[0].status == "error"
