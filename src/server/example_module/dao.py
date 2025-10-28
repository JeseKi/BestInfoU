# -*- coding: utf-8 -*-
"""
示例模块 DAO（可选示范）

公开接口：
- `ExampleItemDAO`
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from src.server.dao.dao_base import BaseDAO
from .models import Item


class ExampleItemDAO(BaseDAO):
    def __init__(self, db_session: Session):
        super().__init__(db_session)

    def create(self, name: str) -> Item:
        exists = self.db_session.query(Item).filter(Item.name == name).first()
        if exists:
            raise ValueError("名称已存在")
        item = Item(name=name)
        self.db_session.add(item)
        self.db_session.commit()
        self.db_session.refresh(item)
        return item

    def get(self, item_id: int) -> Item | None:
        return self.db_session.query(Item).filter(Item.id == item_id).first()
