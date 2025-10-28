# -*- coding: utf-8 -*-
"""
RSS 抓取服务

功能：
- 抓取、解析 RSS 内容
- 刷新指定的订阅源

公开接口：
- `refresh_source`
- `_fetch_feed_content`
- `_parse_feed_entries`

内部方法：
- 无
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List

import httpx
import feedparser  # type: ignore
from fastapi import HTTPException, status
from loguru import logger
from sqlalchemy.orm import Session

from ..dao import RSSSourceDAO, RSSEntryDAO, FetchLogDAO
from ..schemas import (
    FetchLogSchema,
    RSSSourceSchema,
    SourceRefreshResponse,
)
from ..config import rss_config

HTTP_TIMEOUT = rss_config.rss_http_timeout


class RSSFetchError(RuntimeError):
    """RSS 抓取失败"""


def refresh_source(db: Session, source_id: int) -> SourceRefreshResponse:
    """刷新指定订阅源。"""
    from .source_service import ensure_default_source

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
        # 延迟导入以避免循环导入问题
        from .entry_service import _materialize_entries

        materialized = _materialize_entries(db, source, parsed_entries)
        entries_created = entry_dao.bulk_insert(materialized)
        source_dao.update_last_synced(source.id, datetime.now(timezone.utc))
        # 从 avatar_service 导入
        from .avatar_service import _ensure_source_avatar

        if (
            not source.feed_avatar
            or source.feed_avatar == "https://baoyu.io/favicon.ico"
        ):
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
            status=status_value,  # type: ignore
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
