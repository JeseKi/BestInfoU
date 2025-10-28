# -*- coding: utf-8 -*-
"""
认证DAO层测试
"""

from sqlalchemy.orm import Session

from src.server.auth.dao import UserDAO
from src.server.auth.models import User


def test_user_dao_get_by_username(test_db_session: Session):
    """测试根据用户名获取用户"""
    # 准备测试数据
    user = User(username="testuser", email="test@example.com")
    user.set_password("password123")
    test_db_session.add(user)
    test_db_session.commit()

    dao = UserDAO(test_db_session)

    # 测试获取存在的用户
    result = dao.get_by_username("testuser")
    assert result is not None
    assert result.username == "testuser"
    assert result.email == "test@example.com"

    # 测试获取不存在的用户
    result = dao.get_by_username("nonexistent")
    assert result is None


def test_user_dao_create(test_db_session: Session):
    """测试创建用户"""
    dao = UserDAO(test_db_session)

    user = dao.create("newuser", "newuser@example.com", "hashed_password")

    assert user is not None
    assert user.username == "newuser"
    assert user.email == "newuser@example.com"
    assert user.password_hash == "hashed_password"


def test_user_dao_update(test_db_session: Session):
    """测试更新用户"""
    # 准备测试数据
    user = User(username="testuser", email="test@example.com")
    user.set_password("password123")  # 设置密码哈希
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)

    dao = UserDAO(test_db_session)

    # 更新用户信息
    updated_user = dao.update(user, email="updated@example.com", name="Updated Name")

    assert updated_user.email == "updated@example.com"
    assert updated_user.name == "Updated Name"
