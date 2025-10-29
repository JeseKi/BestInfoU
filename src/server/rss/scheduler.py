# -*- coding: utf-8 -*-
"""
RSS 自动拉取调度器

功能：
- 定时自动拉取 RSS 源
- 根据全局间隔配置和最后同步时间判断是否需要拉取

公开接口：
- `start_rss_scheduler`
- `stop_rss_scheduler`

内部方法：
- `_should_refresh_source`
- `_run_scheduler`
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import List
from concurrent.futures import ThreadPoolExecutor

from loguru import logger
from sqlalchemy.orm import Session

from .dao import RSSSourceDAO
from .service import refresh_source
from .config import rss_config


class RSSScheduler:
    """RSS 调度器类"""

    def __init__(self) -> None:
        self.is_running = False
        self.scheduler_task: asyncio.Task | None = None
        self.executor = ThreadPoolExecutor(
            max_workers=rss_config.rss_max_concurrent_fetches
        )

    async def start(self, db_session: Session) -> None:
        """启动调度器"""
        if self.is_running:
            logger.warning("RSS 调度器已在运行中")
            return

        self.is_running = True
        logger.info(
            f"启动 RSS 自动拉取调度器，间隔: {rss_config.rss_sync_interval_minutes} 分钟，"
            f"最大并发: {rss_config.rss_max_concurrent_fetches}"
        )
        self.scheduler_task = asyncio.create_task(self._run_scheduler(db_session))

    async def stop(self) -> None:
        """停止调度器"""
        if not self.is_running:
            return

        self.is_running = False
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                logger.info("RSS 调度器已停止")

        self.executor.shutdown(wait=True)

    async def _run_scheduler(self, db_session: Session) -> None:
        """调度器主循环"""
        while self.is_running:
            try:
                # 获取需要刷新的源列表
                sources_to_refresh = await self._get_sources_to_refresh(db_session)

                if sources_to_refresh:
                    logger.info(f"发现 {len(sources_to_refresh)} 个源需要刷新")
                    # 并发刷新这些源
                    await self._refresh_sources_concurrent(
                        db_session, sources_to_refresh
                    )
                else:
                    logger.debug("当前没有需要刷新的 RSS 源")

                # 等待下一个同步周期
                await asyncio.sleep(rss_config.rss_sync_interval_minutes * 60)

            except asyncio.CancelledError:
                logger.info("RSS 调度器任务被取消")
                break
            except Exception as e:
                logger.error(f"RSS 调度器运行出错: {e}")
                # 出错后等待一段时间再继续
                await asyncio.sleep(60)

    async def _get_sources_to_refresh(self, db_session: Session) -> List[int]:
        """获取需要刷新的源 ID 列表"""
        source_dao = RSSSourceDAO(db_session)
        active_sources = source_dao.list_active()

        sources_to_refresh = []
        now = datetime.now(timezone.utc)
        time_threshold = now - timedelta(minutes=rss_config.rss_sync_interval_minutes)

        for source in active_sources:
            # 如果从未同步过或者上次同步时间超过了配置的间隔，则需要刷新
            # 处理可能存在的 offset-naive datetime（假设为 UTC）
            last_synced = source.last_synced_at
            if last_synced and last_synced.tzinfo is None:
                last_synced = last_synced.replace(tzinfo=timezone.utc)
            if not last_synced or last_synced < time_threshold:
                sources_to_refresh.append(source.id)

        return sources_to_refresh

    async def _refresh_sources_concurrent(
        self, db_session: Session, source_ids: List[int]
    ) -> None:
        """并发刷新多个源"""
        try:
            # 创建新的会话副本用于每个任务，避免会话冲突
            tasks = []
            for source_id in source_ids:
                # 使用 run_in_executor 来处理每个刷新任务，避免阻塞事件循环
                task = asyncio.get_event_loop().run_in_executor(
                    self.executor,
                    self._refresh_single_source,
                    db_session.bind,  # 传递引擎而不是会话
                    source_id,
                )
                tasks.append(task)

            # 等待所有任务完成
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 检查结果中的异常
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"刷新源 {source_ids[i]} 时出错: {result}")

        except Exception as e:
            logger.error(f"并发刷新源时出错: {e}")

    def _refresh_single_source(self, engine, source_id: int) -> None:
        """刷新单个源的同步函数"""
        # 为每个线程创建新的会话
        from sqlalchemy.orm import sessionmaker

        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()

        try:
            logger.info(f"开始刷新源 ID: {source_id}")
            refresh_result = refresh_source(db, source_id)
            logger.info(
                f"源 ID {source_id} 刷新完成，新增条目: {refresh_result.fetch_log.entries_fetched}"
            )
        except Exception as e:
            logger.error(f"刷新源 ID {source_id} 失败: {e}")
        finally:
            db.close()


# 全局调度器实例
_scheduler = RSSScheduler()


async def start_rss_scheduler(db_session: Session) -> None:
    """启动 RSS 自动拉取调度器"""
    await _scheduler.start(db_session)


async def stop_rss_scheduler() -> None:
    """停止 RSS 自动拉取调度器"""
    await _scheduler.stop()
