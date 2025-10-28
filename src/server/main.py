# -*- coding: utf-8 -*-
"""
FastAPI 应用主入口。

负责应用的生命周期管理、中间件配置、API路由挂载以及前端SPA的集成。
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import Scope

from src.server.config import global_config
from src.server.database import get_database_info, init_database

# 路由模块
from src.server.auth.router import router as auth_router
from src.server.example_module.router import router as example_router

# --- 配置与常量 ---
PROJECT_ROOT = Path(global_config.project_root)
DIST_DIR = PROJECT_ROOT / "dist"
INDEX_FILE = DIST_DIR / "index.html"
ASSETS_DIRNAME = "assets"  # Vite 默认的 hash 产物目录


# --- 应用生命周期 ---
@asynccontextmanager
async def lifespan(_: FastAPI):
    """
    应用生命周期管理：
    - 启动时检查并按需初始化数据库。
    """
    logger.info("应用启动中...")
    db_info = get_database_info()
    if not db_info.database_exists:
        logger.warning("数据库不存在，正在执行初始化...")
        init_database()
        logger.success("数据库初始化完成。")
    else:
        logger.info(f"数据库已存在，大小: {db_info.database_size} 字节。")

    logger.success("应用启动完成。")
    yield
    logger.info("应用已关闭。")


# --- 应用实例与中间件 ---
fastapi_kwargs = {
    "title": "Fullstack Template Backend",
    "description": "提供身份验证、数据库交互及示例模块的后端服务。",
    "lifespan": lifespan,
}

if global_config.app_env == "prod":
    fastapi_kwargs["docs_url"] = None
    fastapi_kwargs["redoc_url"] = None
    logger.info("生产环境：API 文档已禁用")

app = FastAPI(**fastapi_kwargs)  # type: ignore

app.add_middleware(
    CORSMiddleware,
    allow_origins=global_config.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CacheControlMiddleware(BaseHTTPMiddleware):
    """
    自定义中间件，为不同路径设置合适的 Cache-Control 响应头。
    """

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        path = request.url.path

        # 对 Vite 构建的带 hash 的静态资源进行长期缓存
        if path.startswith(f"/{ASSETS_DIRNAME}/"):
            response.headers.setdefault(
                "Cache-Control", "public, max-age=31536000, immutable"
            )
        # 对 SPA 的入口文件和其它 HTML 页面禁用缓存，确保用户总能获取最新版本
        elif path == "/" or path.endswith(".html"):
            response.headers["Cache-Control"] = "no-cache"
        return response


app.add_middleware(CacheControlMiddleware)


# --- API 路由 ---
# API 路由建议统一使用 /api 前缀，以避免与前端路由冲突
@app.get("/api/health", summary="健康检查", tags=["系统"])
def health():
    """提供一个简单的健康检查端点，用于监控服务状态。"""
    return {"status": "ok"}


app.include_router(auth_router)
app.include_router(example_router)


# --- 前端 SPA 静态文件服务 ---
class SPAStaticFiles(StaticFiles):
    """
    专为单页应用（SPA）设计的静态文件服务。
    当请求的路径在文件系统中不存在时，会回退到服务 index.html，
    从而支持前端路由。
    """

    async def get_response(self, path: str, scope: Scope) -> Response:
        try:
            # 尝试像常规静态文件一样提供文件
            return await super().get_response(path, scope)
        except Exception:
            # 如果找不到文件 (Starlette 会抛出 RuntimeError, FastAPI 转为 404)
            # 并且请求的不是 API 路径，则返回 SPA 的入口 index.html
            if scope["path"].startswith("/api"):
                return Response(status_code=404)  # API 的 404 应该由 FastAPI 框架处理

            if INDEX_FILE.exists():
                return FileResponse(INDEX_FILE)
            else:
                logger.error(f"SPA 入口文件未找到: {INDEX_FILE}")
                return Response(
                    "Frontend entrypoint (index.html) not found.", status_code=500
                )


# 将前端构建产物目录挂载到根路径
# 注意：这必须在所有 API 路由之后挂载，以作为路径匹配的回退
if DIST_DIR.exists():
    app.mount(
        "/",
        SPAStaticFiles(directory=str(DIST_DIR), html=True),
        name="spa-frontend",
    )
else:
    logger.warning(
        f"前端构建目录 '{DIST_DIR}' 不存在，将不会提供前端页面。"
        "请确认是否已执行前端构建步骤。"
    )
