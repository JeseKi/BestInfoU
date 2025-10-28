# -*- coding: utf-8 -*-
"""
示例业务模型（模板版）

公开接口：
- `Item`

规范注释：
- 本项目中，为了保持模型的简洁性和可维护性，禁止使用外键关系。
  所有跨表关联应通过服务层手动处理，以提高灵活性和降低耦合度。
"""

from __future__ import annotations

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.server.database import Base


class Item(Base):
    __tablename__ = "example_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
