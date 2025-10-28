# -*- coding: utf-8 -*-
"""
认证依赖模块

文件功能：
    提供认证相关的依赖注入函数，用于验证用户身份和权限

公开接口：
    - get_current_user: 验证当前用户的身份并返回用户对象

内部方法：
    - 无内部方法

公开接口的 pydantic 模型：
    - 无需 pydantic 模型，直接返回 User 对象
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from src.server.database import get_db
from src.server.config import global_config
from .config import auth_config
from .models import User
from . import service

# OAuth2 密码持有者令牌方案
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """
    验证当前用户的身份并返回用户对象

    参数:
        token: JWT 访问令牌
        db: 数据库会话

    返回:
        User: 当前用户对象

    异常:
        HTTPException: 当令牌无效或用户不存在时抛出 401 未授权异常
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 开发和测试环境下的特殊处理
    if global_config.app_env in ["dev", "test"] and token == auth_config.test_token:
        user = db.query(User).filter(User.id == 1).first()
        if user:
            return user
        raise credentials_exception

    try:
        payload = jwt.decode(
            token, auth_config.jwt_secret_key, algorithms=[auth_config.jwt_algorithm]
        )
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = service.get_user_by_username(db, username=username)
    if user is None:
        raise credentials_exception
    return user
