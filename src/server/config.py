# -*- coding: utf-8 -*-
"""
全局配置（极简）

公开接口：
- `global_config`: 全局配置实例

内部方法：
- 无

说明：
- 支持 .env 与 .env.{APP_ENV} 加载
- 提供 CORS 允许源解析
"""

import os
import json
from typing import List
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# 先加载 .env 和 .env.{APP_ENV}
load_dotenv(".env")
app_env = os.getenv("APP_ENV", "dev")
load_dotenv(f".env.{app_env}", override=True)


class GlobalConfig(BaseSettings):
    """全局配置"""

    app_env: str = Field(default="dev", title="应用环境")

    database_protocol: str = Field(default="sqlite", title="数据库协议")

    database_path: Path = Field(
        default=Path("data") / "database.db",
        title="数据库路径",
        description="相对项目根目录的相对路径",
    )

    app_secret_key: str = Field(
        default="dev_secret_key_for_testing_only",
        title="应用密钥",
        description="用于会话/签名等场景（可选）",
    )

    project_root: Path = Field(
        default=Path.cwd(),
        title="项目根目录",
        description="相对项目根目录的相对路径",
    )

    @property
    def allowed_origins(self) -> List[str]:
        """允许的跨域来源

        支持格式：
        1. JSON：ALLOWED_ORIGINS='["http://localhost:5173"]'
        2. 逗号分隔：ALLOWED_ORIGINS="http://localhost:5173,https://example.com"
        3. 单个值：ALLOWED_ORIGINS="*"
        4. 未设置：默认为 ["*"]
        """
        env_value = os.getenv("ALLOWED_ORIGINS")
        if not env_value:
            return ["*"]
        try:
            parsed = json.loads(env_value)
            if isinstance(parsed, list):
                return [str(item) for item in parsed]
        except json.JSONDecodeError:
            pass
        if "," in env_value:
            return [origin.strip() for origin in env_value.split(",") if origin.strip()]
        return [env_value.strip()] if env_value.strip() else ["*"]

    model_config = SettingsConfigDict(
        env_file=None, env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )


global_config = GlobalConfig()
