# -*- coding: utf-8 -*-
import os


def test_register_and_login_flow(test_client):
    # 注册
    resp = test_client.post(
        "/api/auth/register",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "Password123",
        },
    )
    assert resp.status_code == 201, resp.text

    # 登录
    resp = test_client.post(
        "/api/auth/login", json={"username": "alice", "password": "Password123"}
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "access_token" in data and "refresh_token" in data


def test_login_wrong_password(test_client, init_test_database):
    resp = test_client.post(
        "/api/auth/login", json={"username": "admin", "password": "wrong"}
    )
    assert resp.status_code == 401


def test_profile_with_test_token(test_client, init_test_database):
    os.environ.setdefault("APP_ENV", "test")
    # 使用 test_token 直接访问
    resp = test_client.get(
        "/api/auth/profile",
        headers={"Authorization": "Bearer KISPACE_TEST_TOKEN"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "admin"


def test_change_password_flow(test_client):
    # 注册
    test_client.post(
        "/api/auth/register",
        json={
            "username": "bob",
            "email": "bob@example.com",
            "password": "OldPassword123",
        },
    )
    # 登录
    login = test_client.post(
        "/api/auth/login", json={"username": "bob", "password": "OldPassword123"}
    ).json()
    headers = {"Authorization": f"Bearer {login['access_token']}"}

    # 修改密码：旧密码错误
    resp = test_client.put(
        "/api/auth/password",
        json={"old_password": "wrong", "new_password": "NewPassword123"},
        headers=headers,
    )
    assert resp.status_code == 400

    # 修改密码：成功
    resp = test_client.put(
        "/api/auth/password",
        json={"old_password": "OldPassword123", "new_password": "NewPassword123"},
        headers=headers,
    )
    assert resp.status_code == 200

    # 新密码登录
    resp = test_client.post(
        "/api/auth/login", json={"username": "bob", "password": "NewPassword123"}
    )
    assert resp.status_code == 200
