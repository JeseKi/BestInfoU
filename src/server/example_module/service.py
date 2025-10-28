# -*- coding: utf-8 -*-
"""
示例模块服务层（模板版）

公开接口：
- create_item(db, name)
- get_item(db, item_id)

内部方法：
- 无

说明：
- 服务层承载业务逻辑，路由层只做参数校验与装配。
"""

from __future__ import annotations

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from .dao import ExampleItemDAO

from .models import Item


def create_item(db: Session, name: str) -> Item:
    dao = ExampleItemDAO(db)
    try:
        return dao.create(name)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="名称已存在"
        )


def get_item(db: Session, item_id: int) -> Item:
    dao = ExampleItemDAO(db)
    item = dao.get(item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到")
    return item
