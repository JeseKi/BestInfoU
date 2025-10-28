# -*- coding: utf-8 -*-
"""
RSS 模块配置

公开接口：
- `rss_config`
"""

from pydantic import Field
from pydantic_settings import BaseSettings


class RSSConfig(BaseSettings):
    """RSS 模块配置"""

    # 默认订阅源配置
    rss_default_feed_url: str = Field(
        default="https://s.baoyu.io/feed.xml",
        title="默认 RSS 源地址",
        description="自动创建的默认 RSS 订阅源地址",
    )

    rss_default_source_name: str = Field(
        default="宝玉 RSS",
        title="默认订阅源名称",
        description="自动创建的默认 RSS 订阅源名称",
    )

    rss_default_source_avatar: str = Field(
        default="https://baoyu.io/favicon.ico",
        title="默认订阅源头像",
        description="默认订阅源的头像 URL",
    )

    rss_default_source_homepage: str = Field(
        default="https://baoyu.io/",
        title="默认订阅源主页",
        description="默认订阅源的主页 URL",
    )

    # HTTP 请求配置
    rss_http_timeout: float = Field(
        default=20.0,
        title="HTTP 请求超时时间",
        description="RSS 抓取请求的超时时间（秒）",
    )

    # 业务逻辑配置
    rss_default_entry_limit: int = Field(
        default=50,
        title="默认条目限制",
        description="获取 RSS 条目时的默认数量限制",
    )

    rss_default_sync_interval_minutes: int = Field(
        default=60,
        title="默认同步间隔",
        description="RSS 源同步更新的默认间隔（分钟）",
    )


rss_config = RSSConfig()
