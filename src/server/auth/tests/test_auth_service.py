# -*- coding: utf-8 -*-
"""
认证服务层测试
"""

from datetime import timedelta

from sqlalchemy.orm import Session

from src.server.auth.models import User
from src.server.auth.schemas import UserCreate, UserUpdate
from src.server.auth.service import (
    get_user_by_username,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    create_user,
    update_user,
    change_password,
    bootstrap_default_admin,
)


def test_get_user_by_username(test_db_session: Session):
    """测试根据用户名获取用户"""
    # 准备测试数据
    user = User(username="testuser", email="test@example.com")
    user.set_password("password123")
    test_db_session.add(user)
    test_db_session.commit()

    # 测试获取存在的用户
    result = get_user_by_username(test_db_session, "testuser")
    assert result is not None
    assert result.username == "testuser"
    assert result.email == "test@example.com"

    # 测试获取不存在的用户
    result = get_user_by_username(test_db_session, "nonexistent")
    assert result is None


def test_authenticate_user(test_db_session: Session):
    """测试用户认证"""
    # 准备测试数据
    user = User(username="testuser", email="test@example.com")
    user.set_password("password123")
    test_db_session.add(user)
    test_db_session.commit()

    # 测试正确凭据
    result = authenticate_user(test_db_session, "testuser", "password123")
    assert result is not None
    assert result.username == "testuser"

    # 测试错误密码
    result = authenticate_user(test_db_session, "testuser", "wrongpassword")
    assert result is None

    # 测试不存在的用户
    result = authenticate_user(test_db_session, "nonexistent", "password123")
    assert result is None


def test_create_access_token():
    """测试创建访问令牌"""
    data = {"sub": "testuser"}

    # 测试默认过期时间
    token = create_access_token(data)
    assert isinstance(token, str)
    assert len(token) > 0

    # 测试自定义过期时间
    token = create_access_token(data, timedelta(minutes=30))
    assert isinstance(token, str)
    assert len(token) > 0


def test_create_refresh_token():
    """测试创建刷新令牌"""
    data = {"sub": "testuser"}

    # 测试默认过期时间
    token = create_refresh_token(data)
    assert isinstance(token, str)
    assert len(token) > 0

    # 测试自定义过期时间
    token = create_refresh_token(data, timedelta(days=7))
    assert isinstance(token, str)
    assert len(token) > 0


def test_create_user(test_db_session: Session):
    """测试创建用户"""
    user_data = UserCreate(
        username="newuser", email="newuser@example.com", password="password123"
    )

    user = create_user(test_db_session, user_data)

    assert user is not None
    assert user.username == "newuser"
    assert user.email == "newuser@example.com"
    assert user.password_hash is not None
    assert len(user.password_hash) > 0


def test_update_user(test_db_session: Session):
    """测试更新用户"""
    # 准备测试数据
    user = User(username="testuser", email="test@example.com")
    user.set_password("password123")  # 设置密码哈希
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)

    # 更新用户信息
    update_data = UserUpdate(email="updated@example.com", name="Updated Name")
    updated_user = update_user(test_db_session, user, update_data)

    assert updated_user.email == "updated@example.com"
    assert updated_user.name == "Updated Name"


def test_change_password(test_db_session: Session):
    """测试修改密码"""
    # 准备测试数据
    user = User(username="testuser", email="test@example.com")
    user.set_password("oldpassword")
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)

    # 测试错误的旧密码
    result = change_password(test_db_session, user, "wrongpassword", "newpassword123")
    assert result is False

    # 测试正确的旧密码
    result = change_password(test_db_session, user, "oldpassword", "newpassword123")
    assert result is True

    # 验证新密码是否生效
    assert user.check_password("newpassword123") is True
    assert user.check_password("oldpassword") is False


def test_bootstrap_default_admin(test_db_session: Session):
    """测试引导默认管理员"""
    # 测试创建新的管理员
    bootstrap_default_admin(test_db_session)

    user = get_user_by_username(test_db_session, "admin")
    assert user is not None
    assert user.username == "admin"
    assert user.email == "admin@example.com"
    assert user.role == "admin"
    assert user.check_password("AdminPass123") is True

    # 测试重复调用不会创建重复用户
    bootstrap_default_admin(test_db_session)

    user_count = test_db_session.query(User).filter(User.username == "admin").count()
    assert user_count == 1
