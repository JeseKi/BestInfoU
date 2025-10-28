# -*- coding: utf-8 -*-
"""
认证相关配置（模板版）

公开接口：
- `auth_config`
"""

from pydantic import Field
from pydantic_settings import BaseSettings


class AuthConfig(BaseSettings):
    """认证配置"""

    jwt_secret_key: str = Field(
        default="dev_secret_key_for_testing_only",
        title="JWT 密钥",
        description="生产务必通过环境变量覆盖",
    )
    jwt_algorithm: str = Field(default="HS256", title="JWT 算法")
    access_token_ttl_minutes: int = Field(default=15, title="Access Token 有效期(分钟)")
    refresh_token_ttl_days: int = Field(default=7, title="Refresh Token 有效期(天)")
    test_token: str = Field(
        default="KISPACE_TEST_TOKEN",
        title="测试 Token",
        description="dev/test 环境用于便捷鉴权",
    )


auth_config = AuthConfig()
