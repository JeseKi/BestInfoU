# -*- coding: utf-8 -*-
"""
示例模块路由（模板版）

公开接口：
- GET /api/example/ping
- POST /api/example/items
- GET /api/example/items/{item_id}
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.server.database import get_db
from .schemas import ItemCreate, ItemOut
from . import service
from src.server.dao.dao_base import run_in_thread

router = APIRouter(prefix="/api/example", tags=["示例"])


@router.get(
    "/ping",
    summary="健康检查",
    description="检查服务是否正常运行",
    response_description="返回服务状态信息",
    responses={
        200: {"description": "服务正常运行"},
    },
)
async def ping() -> dict[str, str]:
    return {"message": "pong"}


@router.post(
    "/items",
    response_model=ItemOut,
    status_code=status.HTTP_201_CREATED,
    summary="创建项目",
    description="创建一个新的项目，需要提供项目名称等基本信息",
    response_description="返回新创建的项目信息",
    responses={
        201: {"description": "项目创建成功"},
        400: {"description": "请求参数错误"},
    },
)
async def create_item(payload: ItemCreate, db: Session = Depends(get_db)):
    def _create():
        return service.create_item(db, payload.name)

    return await run_in_thread(_create)


@router.get(
    "/items/{item_id}",
    response_model=ItemOut,
    summary="获取项目详情",
    description="根据项目ID获取指定项目的详细信息",
    response_description="返回指定项目的详细信息",
    responses={
        200: {"description": "获取项目成功"},
        404: {"description": "项目不存在"},
    },
)
async def get_item(item_id: int, db: Session = Depends(get_db)):
    def _get():
        return service.get_item(db, item_id)

    return await run_in_thread(_get)
