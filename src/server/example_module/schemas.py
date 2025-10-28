# -*- coding: utf-8 -*-
"""
示例模块 Pydantic 模型（模板版）

公开接口：
- `ItemCreate`、`ItemOut`
"""

from pydantic import BaseModel, Field, ConfigDict


class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class ItemOut(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)
