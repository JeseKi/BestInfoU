# -*- coding: utf-8 -*-
"""
pytest 公共 fixtures（模板版）

功能：
- 统一测试环境变量
- 提供内存 SQLite 的数据库引擎、会话与 TestClient
- 引导默认管理员

公开接口：
- `test_db_engine`
- `test_db_session`
- `test_client`
- `init_test_database`
"""

from __future__ import annotations

import os
from typing import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.engine import Connection

# 测试环境配置
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("ALLOWED_ORIGINS", '["http://localhost:3000"]')


@pytest.fixture(scope="function")
def test_db_engine() -> Iterator[Connection]:
    """提供共享内存 SQLite 连接（保持连接存活，保证多线程一致）。"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    keep_conn = engine.connect()

    from src.server.database import Base
    import src.server.auth.models  # noqa: F401

    Base.metadata.create_all(bind=keep_conn)

    try:
        yield keep_conn
    finally:
        try:
            keep_conn.close()
        finally:
            engine.dispose()


@pytest.fixture(scope="function")
def test_db_session(test_db_engine) -> Iterator[Session]:
    """提供内存数据库会话。"""
    TestingSessionLocal = sessionmaker(
        bind=test_db_engine, autocommit=False, autoflush=False
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def test_client(test_db_session: Session) -> Iterator[TestClient]:
    """提供一个配置了测试数据库的 FastAPI TestClient。"""
    from src.server.main import app
    from src.server.database import get_db

    def override_get_db() -> Iterator[Session]:
        yield test_db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="function")
def init_test_database(test_db_engine) -> None:
    """初始化默认管理员等必要基础数据。"""
    TestingSessionLocal = sessionmaker(
        bind=test_db_engine, autocommit=False, autoflush=False
    )
    session = TestingSessionLocal()
    try:
        from src.server.auth.models import User

        exists = session.query(User).order_by(User.id.asc()).first()
        if not exists:
            admin = User(
                username="admin",
                email="admin@example.com",
                name="默认管理员",
                role="admin",
            )
            admin.set_password("admin123")
            session.add(admin)
            session.commit()
    finally:
        session.close()
