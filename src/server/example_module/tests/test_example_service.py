# -*- coding: utf-8 -*-
"""
示例模块服务层测试
"""

import pytest
from sqlalchemy.orm import Session
from fastapi import HTTPException

from src.server.example_module.models import Item
from src.server.example_module.service import create_item, get_item


def test_create_item(test_db_session: Session):
    """测试创建项目"""
    # 正常创建
    item = create_item(test_db_session, "test_item")

    assert item is not None
    assert item.name == "test_item"

    # 测试重复名称
    with pytest.raises(HTTPException) as exc_info:
        create_item(test_db_session, "test_item")

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "名称已存在"


def test_get_item(test_db_session: Session):
    """测试获取项目"""
    # 准备测试数据
    item = Item(name="test_item")
    test_db_session.add(item)
    test_db_session.commit()
    test_db_session.refresh(item)

    # 获取存在的项目
    retrieved_item = get_item(test_db_session, item.id)
    assert retrieved_item is not None
    assert retrieved_item.id == item.id
    assert retrieved_item.name == "test_item"

    # 获取不存在的项目
    with pytest.raises(HTTPException) as exc_info:
        get_item(test_db_session, 999999)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "未找到"
