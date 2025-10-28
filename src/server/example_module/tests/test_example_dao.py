# -*- coding: utf-8 -*-
"""
示例模块DAO层测试
"""

import pytest
from sqlalchemy.orm import Session

from src.server.example_module.dao import ExampleItemDAO
from src.server.example_module.models import Item


def test_example_item_dao_create(test_db_session: Session):
    """测试创建项目"""
    dao = ExampleItemDAO(test_db_session)

    # 正常创建
    item = dao.create("test_item")

    assert item is not None
    assert item.name == "test_item"

    # 测试重复名称
    with pytest.raises(ValueError) as exc_info:
        dao.create("test_item")

    assert str(exc_info.value) == "名称已存在"


def test_example_item_dao_get(test_db_session: Session):
    """测试获取项目"""
    # 准备测试数据
    item = Item(name="test_item")
    test_db_session.add(item)
    test_db_session.commit()
    test_db_session.refresh(item)

    dao = ExampleItemDAO(test_db_session)

    # 获取存在的项目
    retrieved_item = dao.get(item.id)
    assert retrieved_item is not None
    assert retrieved_item.id == item.id
    assert retrieved_item.name == "test_item"

    # 获取不存在的项目
    retrieved_item = dao.get(999999)
    assert retrieved_item is None
