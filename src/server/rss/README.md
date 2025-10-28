# RSS 模块说明

## 公开接口
- `GET /api/rss/sources`：列出全部订阅源。
- `GET /api/rss/feeds`：返回订阅源与最新条目集合。
- `POST /api/rss/sources/{source_id}/refresh`：手动刷新指定订阅源。
- 服务层公开函数：`list_sources`、`get_feed_snapshot`、`refresh_source`。

## 业务逻辑定位
该模块负责从手动配置的 RSS 源抓取内容，并向前端提供标题与正文数据：
1. 启动时自动确保默认订阅源（宝玉 RSS）存在，后续可扩展后台管理接口维护更多来源。
2. 刷新接口通过线程池执行同步 HTTP 抓取与 feedparser 解析，解析成功后写入 `rss_entries` 并生成抓取日志。
3. 在首次创建或刷新时，服务会抓取订阅源主页的 favicon / og:image 自动补齐头像地址，便于前端展示来源识别。
4. 列表接口从最新条目中组装「订阅源 + 条目」快照供前端展示，默认每次返回 50 条。
5. 启动时自动启动 RSS 同步调度器，根据全局配置的时间间隔自动拉取过期的 RSS 源。

## 数据流
1. 前端调用 `/api/rss/feeds`。
2. 路由转发到 `service.get_feed_snapshot`，读取订阅源与条目。
3. 数据访问层通过 `RSSSourceDAO`、`RSSEntryDAO` 查询 SQLite。
4. 若用户点击刷新，则 `/api/rss/sources/{id}/refresh` 调用 `service.refresh_source`，抓取 RSS 文本、解析并写回数据库，同时写入 `FetchLog`。
5. 后台调度器定期检查各个源的 `last_synced_at` 时间戳，若超过配置的全局同步间隔，则自动触发拉取。
6. 服务返回 Pydantic 序列化后的结果。

## 用法示例
```python
from sqlalchemy.orm import Session
from src.server.rss import service

def show_latest_entries(db: Session) -> None:
    snapshot = service.get_feed_snapshot(db, limit=10)
    for entry in snapshot.entries:
        print(entry.title, entry.link)
```

## 设计说明
- 订阅源、条目、抓取日志分别建表，条目通过 `guid` 与内容哈希双重唯一约束去重。
- 所有耗时操作放在服务层同步实现，FastAPI 使用线程池调度，避免阻塞事件循环。
- 返回模型统一使用 Pydantic，保证前后端对于字段的一致认知。
