# -*- coding: utf-8 -*-
"""
RSS Pydantic 模型

公开接口：
- `RSSSourceSchema`
- `RSSEntrySchema`
- `FetchLogSchema`
- `RSSFeedResponse`
- `SourceRefreshResponse`

内部方法：
- 无

文件功能：
- 提供 RSS 模块在 API 层返回所需的数据模型，保证序列化字段与业务语义一致。
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class RSSSourceSchema(BaseModel):
    """订阅源信息"""

    id: int
    name: str
    feed_url: str
    homepage_url: Optional[str] = None
    feed_avatar: Optional[str] = None
    description: Optional[str] = None
    language: Optional[str] = None
    category: Optional[str] = None
    is_active: bool = True
    last_synced_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class RSSEntrySchema(BaseModel):
    """RSS 条目信息"""

    id: int
    source_id: int
    source_name: str
    feed_avatar: Optional[str] = None
    title: str
    summary: Optional[str] = None
    content: Optional[str] = None
    link: Optional[str] = None
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    fetched_at: datetime

    model_config = {"from_attributes": True}


class FetchLogSchema(BaseModel):
    """抓取日志"""

    id: int
    source_id: int
    status: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    error_message: Optional[str] = None
    entries_fetched: int

    model_config = {"from_attributes": True}


class RSSFeedResponse(BaseModel):
    """RSS 源与条目聚合响应"""

    sources: List[RSSSourceSchema]
    entries: List[RSSEntrySchema]


class SourceRefreshResponse(BaseModel):
    """刷新指定订阅源后的结果"""

    source: RSSSourceSchema
    fetch_log: FetchLogSchema
