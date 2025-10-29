# -*- coding: utf-8 -*-
"""
RSS 路由

公开接口：
- GET /api/rss/sources
- GET /api/rss/feeds
- POST /api/rss/sources
- PATCH /api/rss/sources/{source_id}
- DELETE /api/rss/sources/{source_id}
- POST /api/rss/sources/{source_id}/refresh

内部方法：
- `_require_admin`

文件功能：
- 暴露 RSS 模块的 REST API，使前端能够读取订阅源、条目并手动触发抓取。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, HTTPException, status, Response
from sqlalchemy.orm import Session

from src.server.auth.dependencies import get_current_user
from src.server.auth.models import User
from src.server.database import get_db
from .service import (
    list_sources,
    get_feed_snapshot,
    refresh_source,
    create_source,
    update_source,
    delete_source,
)
from .schemas import (
    RSSFeedResponse,
    RSSSourceSchema,
    SourceRefreshResponse,
    CreateRSSSourcePayload,
    UpdateRSSSourcePayload,
)

router = APIRouter(prefix="/api/rss", tags=["RSS"])


def _require_admin(current_user: User = Depends(get_current_user)) -> User:
    """校验当前用户是否为管理员。"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限。",
        )
    return current_user


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
    "/sources",
    response_model=RSSSourceSchema,
    status_code=status.HTTP_201_CREATED,
    summary="创建订阅源",
    response_description="返回新建的订阅源信息",
)
def create_source_api(
    payload: CreateRSSSourcePayload,
    db: Session = Depends(get_db),
    _: User = Depends(_require_admin),
) -> RSSSourceSchema:
    """创建新的订阅源。"""
    return create_source(db, payload)


@router.patch(
    "/sources/{source_id}",
    response_model=RSSSourceSchema,
    summary="更新订阅源",
    response_description="返回更新后的订阅源信息",
)
def update_source_api(
    source_id: int,
    payload: UpdateRSSSourcePayload,
    db: Session = Depends(get_db),
    _: User = Depends(_require_admin),
) -> RSSSourceSchema:
    """更新订阅源信息。"""
    return update_source(db, source_id, payload)


@router.delete(
    "/sources/{source_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除订阅源",
    response_description="成功删除订阅源后不返回内容",
)
def delete_source_api(
    source_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(_require_admin),
) -> Response:
    """删除指定订阅源。"""
    delete_source(db, source_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


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
