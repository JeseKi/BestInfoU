# -*- coding: utf-8 -*-
"""
认证模块 DAO（模板版）

公开接口：
- `UserDAO`

内部方法：
- 无

说明：
- 提供用户读取/写入的持久化封装，业务逻辑放在 service。
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from src.server.dao.dao_base import BaseDAO
from .models import User


class UserDAO(BaseDAO):
    def __init__(self, db_session: Session):
        super().__init__(db_session)

    def get_by_username(self, username: str) -> User | None:
        return self.db_session.query(User).filter(User.username == username).first()

    def create(self, username: str, email: str, password_hash: str) -> User:
        user = User(username=username, email=email, password_hash=password_hash)
        self.db_session.add(user)
        self.db_session.commit()
        self.db_session.refresh(user)
        return user

    def update(self, user: User, **fields) -> User:
        for k, v in fields.items():
            setattr(user, k, v)
        self.db_session.commit()
        self.db_session.refresh(user)
        return user
