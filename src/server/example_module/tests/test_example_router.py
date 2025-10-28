# -*- coding: utf-8 -*-
from http import HTTPStatus


def test_ping(test_client):
    resp = test_client.get("/api/example/ping")
    assert resp.status_code == HTTPStatus.OK
    assert resp.json()["message"] == "pong"


def test_create_and_get_item(test_client):
    # 创建
    resp = test_client.post("/api/example/items", json={"name": "hello"})
    assert resp.status_code == HTTPStatus.CREATED, resp.text
    item = resp.json()

    # 重复名称
    resp2 = test_client.post("/api/example/items", json={"name": "hello"})
    assert resp2.status_code == HTTPStatus.BAD_REQUEST

    # 查询
    resp3 = test_client.get(f"/api/example/items/{item['id']}")
    assert resp3.status_code == HTTPStatus.OK
    assert resp3.json()["name"] == "hello"

    # 查询不存在
    resp4 = test_client.get("/api/example/items/999999")
    assert resp4.status_code == HTTPStatus.NOT_FOUND
