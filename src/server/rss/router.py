# -*- coding: utf-8 -*-
"""
RSS 路由

公开接口：
- GET /api/rss/sources
- GET /api/rss/feeds
- POST /api/rss/sources/{source_id}/refresh

内部方法：
- 无

文件功能：
- 暴露 RSS 模块的 REST API，使前端能够读取订阅源、条目并手动触发抓取。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.server.database import get_db
from .service import list_sources, get_feed_snapshot, refresh_source
from .schemas import RSSFeedResponse, RSSSourceSchema, SourceRefreshResponse

router = APIRouter(prefix="/api/rss", tags=["RSS"])


@router.get(
    "/sources",
    response_model=list[RSSSourceSchema],
    summary="列出订阅源",
    response_description="返回全部订阅源信息",
)
def list_sources_api(db: Session = Depends(get_db)) -> list[RSSSourceSchema]:
    """列出所有订阅源。"""
    return list_sources(db)


@router.get(
    "/feeds",
    response_model=RSSFeedResponse,
    summary="获取订阅源快照",
    response_description="返回订阅源与最新条目集合",
)
def get_feeds_api(
    limit: int = Query(default=50, ge=1, le=200, description="返回的最大条目数量"),
    db: Session = Depends(get_db),
) -> RSSFeedResponse:
    """返回订阅源与最新条目的组合。"""
    return get_feed_snapshot(db, limit)


@router.post(
    "/sources/{source_id}/refresh",
    response_model=SourceRefreshResponse,
    summary="刷新订阅源",
    response_description="抓取指定订阅源并返回结果",
)
def refresh_source_api(
    source_id: int,
    db: Session = Depends(get_db),
) -> SourceRefreshResponse:
    """手动触发订阅源抓取。"""
    return refresh_source(db, source_id)
