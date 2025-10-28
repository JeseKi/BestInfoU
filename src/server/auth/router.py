# -*- coding: utf-8 -*-
"""
认证路由（模板版）

公开接口：
- POST /api/auth/login
- POST /api/auth/register
- POST /api/auth/refresh
- GET /api/auth/profile
- PUT /api/auth/profile
- PUT /api/auth/password
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.server.database import get_db
from .dependencies import get_current_user
from .models import User
from . import service
from .schemas import (
    PasswordChange,
    TokenResponse,
    UserCreate,
    UserProfile,
    UserUpdate,
    UserLogin,
)

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="用户登录",
    description="用户通过用户名和密码进行身份验证，获取访问令牌和刷新令牌",
    response_description="返回访问令牌和刷新令牌",
    responses={
        200: {"description": "登录成功"},
        401: {"description": "用户名或密码错误"},
    },
)
async def login_for_access_token(login_data: UserLogin, db: Session = Depends(get_db)):
    user = service.authenticate_user(db, login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="不正确的用户名或密码",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = service.create_access_token(data={"sub": user.username})
    refresh_token = service.create_refresh_token(data={"sub": user.username})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post(
    "/register",
    response_model=UserProfile,
    status_code=status.HTTP_201_CREATED,
    summary="用户注册",
    description="创建新用户账户，需要提供用户名、邮箱和密码等基本信息",
    response_description="返回新创建的用户信息",
    responses={
        201: {"description": "用户创建成功"},
        400: {"description": "用户名已被注册"},
    },
)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    db_user = service.get_user_by_username(db, username=user_data.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已被注册"
        )
    new_user = service.create_user(db=db, user_data=user_data)
    return new_user


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="刷新访问令牌",
    description="使用刷新令牌获取新的访问令牌和刷新令牌对",
    response_description="返回新的访问令牌和刷新令牌",
    responses={
        200: {"description": "令牌刷新成功"},
        401: {"description": "无效的刷新令牌"},
    },
)
async def refresh_access_token(current_user: User = Depends(get_current_user)):
    new_access_token = service.create_access_token(data={"sub": current_user.username})
    new_refresh_token = service.create_refresh_token(
        data={"sub": current_user.username}
    )
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@router.get(
    "/profile",
    response_model=UserProfile,
    summary="获取用户资料",
    description="获取当前登录用户的详细信息",
    response_description="返回当前用户的完整资料信息",
    responses={
        200: {"description": "获取用户资料成功"},
        401: {"description": "未认证或令牌无效"},
    },
)
async def get_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.put(
    "/profile",
    response_model=UserProfile,
    summary="更新用户资料",
    description="更新当前登录用户的个人信息，包括用户名、邮箱等基本信息",
    response_description="返回更新后的用户资料信息",
    responses={
        200: {"description": "用户资料更新成功"},
        400: {"description": "邮箱已被使用"},
        401: {"description": "未认证或令牌无效"},
    },
)
async def update_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user_data.email:
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="邮箱已被使用"
            )
    updated_user = service.update_user(db=db, user=current_user, user_data=user_data)
    return updated_user


@router.put(
    "/password",
    summary="修改用户密码",
    description="修改当前登录用户的密码，需要提供旧密码和新密码进行验证",
    response_description="返回密码修改结果信息",
    responses={
        200: {"description": "密码修改成功"},
        400: {"description": "旧密码不正确"},
        401: {"description": "未认证或令牌无效"},
    },
)
async def change_current_user_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    success = service.change_password(
        db=db,
        user=current_user,
        old_password=password_data.old_password,
        new_password=password_data.new_password,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="旧密码不正确"
        )
    return {"message": "密码修改成功"}
