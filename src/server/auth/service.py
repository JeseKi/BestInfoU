# -*- coding: utf-8 -*-
"""
认证与用户服务（模板版）

公开接口：
- get_user_by_username
- authenticate_user
- create_access_token / create_refresh_token
- create_user / update_user / change_password
- bootstrap_default_admin
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt
from loguru import logger
from sqlalchemy.orm import Session

from .config import auth_config
from .models import User
from .schemas import UserCreate, UserUpdate
from .dao import UserDAO


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return UserDAO(db).get_by_username(username)


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    user = get_user_by_username(db, username)
    if not user or not user.check_password(password):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=auth_config.access_token_ttl_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode, auth_config.jwt_secret_key, algorithm=auth_config.jwt_algorithm
    )


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(days=auth_config.refresh_token_ttl_days)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode, auth_config.jwt_secret_key, algorithm=auth_config.jwt_algorithm
    )


def create_user(db: Session, user_data: UserCreate) -> User:
    # 先构造密码哈希
    tmp_user = User(username=user_data.username, email=user_data.email)
    tmp_user.set_password(user_data.password)
    return UserDAO(db).create(tmp_user.username, tmp_user.email, tmp_user.password_hash)


def update_user(db: Session, user: User, user_data: UserUpdate) -> User:
    update_data = user_data.model_dump(exclude_unset=True)
    return UserDAO(db).update(user, **update_data)


def change_password(
    db: Session, user: User, old_password: str, new_password: str
) -> bool:
    if not user.check_password(old_password):
        return False
    user.set_password(new_password)
    db.commit()
    return True


def bootstrap_default_admin(session: Session) -> None:
    """引导默认管理员（幂等）。用户名取邮箱 @ 前缀。"""
    admin_email = "admin@example.com"
    admin_username = admin_email.split("@")[0]
    user = get_user_by_username(session, admin_username)
    password = "AdminPass123"
    if user:
        return
    try:
        admin_user_data = UserCreate(
            username=admin_username, email=admin_email, password=password
        )
        new_user = create_user(session, admin_user_data)
        new_user.role = "admin"
        session.commit()
        logger.info(f"已引导管理员用户：{admin_username}")
    except Exception as e:
        session.rollback()
        logger.warning(f"引导管理员异常（已忽略）：{e}")
