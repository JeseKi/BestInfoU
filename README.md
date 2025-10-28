# Fullstack Template (FastAPI + React/Vite)

一个极简但开箱即用的全栈模板：后端基于 FastAPI + SQLAlchemy（SQLite）+ Alembic，前端基于 React 19 + Vite 7 + Tailwind CSS 4 + Ant Design。内置认证模块与示例业务模块，并提供完善的中文注释与测试样例。

### 技术栈
- 后端：FastAPI、SQLAlchemy、Pydantic、python-jose[jwt]、bcrypt、pytest、pytest-asyncio、mypy、ruff、loguru、Alembic
- 前端：React 19、Vite 7、React Router 7、Tailwind CSS 4、Ant Design、Lucide React、axios、TypeScript 5

### 目录结构（关键项）
```
./
├── index.html                     # Vite 入口（挂载 src/client/main.tsx）
├── package.json                   # 前端脚本与依赖（pnpm 建议）
├── pnpm-lock.yaml
├── requirements.txt               # 后端依赖
├── requirements.in                # 后端依赖声明（uv 管理）
├── alembic.ini                    # 数据库迁移配置
├── .env.example                   # 环境变量示例
├── vite.config.ts                 # Vite 配置
├── tsconfig*.json                 # TS 配置
├── mypy.ini                       # mypy 类型检查配置
├── pytest.ini                     # pytest 测试配置
├── src/
│   ├── client/                    # 前端应用
│   │   ├── main.tsx               # React 入口
│   │   ├── App.tsx
│   │   ├── index.css              # Tailwind 入口样式
│   │   ├── tailwind.config.js
│   │   ├── postcss.config.js
│   │   ├── components/            # React 组件
│   │   ├── pages/                 # 页面组件
│   │   ├── hooks/                 # 自定义 hooks
│   │   ├── lib/                   # 工具库与 API 调用
│   │   └── providers/             # 上下文 Provider
│   └── server/                    # 后端应用
│       ├── main.py                # FastAPI 应用（挂载各模块）
│       ├── config.py              # 全局配置与 CORS 解析
│       ├── database.py            # SQLAlchemy 连接与初始化
│       ├── auth/                  # 认证模块
│       │   ├── models.py / schemas.py / router.py / service.py / dao.py
│       │   ├── README.md          # 模块接口文档
│       │   └── tests/             # 单元测试
│       └── example_module/        # 示例模块
│           ├── models.py / schemas.py / router.py / service.py / dao.py
│           ├── README.md          # 模块接口文档
│           └── tests/             # 单元测试
├── alembic/                       # Alembic 数据库迁移目录
│   ├── versions/                  # 迁移文件
│   └── env.py
└── scripts/
    └── init_db.py                 # 数据库 CLI（检查/重置）
```

### 环境要求
- Python 3.11+
- Node.js 18+（建议 20+）
- 包管理：pnpm（或 npm/yarn，本文以 pnpm 为例）

---

## 快速开始（开发环境）
1) 复制环境变量并按需调整
```bash
cp .env.example .env
```

2) 安装后端依赖（建议使用虚拟环境）
```bash
# 任选其一：
# python -m venv .venv && source .venv/bin/activate
# 或 conda create -n fullstack-template python=3.11 -y && conda activate fullstack-template

pip install -r requirements.txt
```

3) 安装前端依赖
```bash
pnpm install
```

4) 启动后端（终端 A）
```bash
# 推荐
python run.py
# 或
uvicorn src.server.main:app --reload --port 8000
```

5) 启动前端（终端 B）
```bash
pnpm dev
```

- 前端默认访问：http://localhost:5173
- 后端默认访问：http://localhost:8000


### 环境变量（.env）
`.env.example` 提供了可工作的默认值。常用项如下：
```ini
APP_ENV=dev
APP_SECRET_KEY=change-me
# 如果使用 Vite 默认端口：
ALLOWED_ORIGINS=["http://localhost:5173"]
# 如果你将 Vite 改成 3000：
# ALLOWED_ORIGINS=["http://localhost:3000"]
DATABASE_PATH=database.db
PORT=8000
LOG_LEVEL=info
```

- CORS 解析支持 JSON 数组、逗号分隔或单值，例如：
  - `ALLOWED_ORIGINS='["http://localhost:5173"]'`
  - `ALLOWED_ORIGINS="http://localhost:5173,http://localhost:3000"`
  - `ALLOWED_ORIGINS="*"`

---

## 数据库工具
使用内置脚本初始化/检查数据库：
```bash
# 仅初始化（幂等，若不存在则创建）
python scripts/init_db.py

# 检查当前表
python scripts/init_db.py --check

# 重置并初始化（删除现有文件后再创建）
python scripts/init_db.py --reset
```

---

## 模块与接口
- 认证模块文档见：`src/server/auth/README.md`
- 示例模块文档见：`src/server/example_module/README.md`

后端启动后可直接访问以下示例：
```bash
curl http://localhost:8000/api/example/ping
```

---

## 前端开发约定
- 入口：`index.html` -> `src/client/main.tsx` -> `src/client/App.tsx`
- UI：Tailwind CSS 4 + Ant Design，可无缝配合使用；样式入口 `src/client/index.css`
- 路由：已接入 React Router 7（按需扩展）
- UI 组件：推荐使用 Ant Design 组件库，也可使用 `lucide-react` 作为图标库
- API 调用：推荐使用 `axios`，已配置在 `src/client/lib/` 下

前端常用脚本：
```bash
pnpm dev       # 本地开发
pnpm build     # 生产构建（输出 dist/）
pnpm preview   # 本地预览生产构建
pnpm lint      # ESLint 代码检查
```

## 后端开发工具
```bash
# 类型检查
mypy src/server

# 代码格式检查
ruff check src/server

# 代码自动格式化
ruff format src/server
```

---

## 测试
- 后端测试：
```bash
python -m pytest . -q
```

- 前端目前未内置单测框架（可选接入 Vitest/RTL）。

---

## 设计要点与规范
- 路由层仅做参数校验与编排；业务放在 service 层；可复用的数据访问封装到 DAO 层
- ORM 同步调用通过 `asyncio.to_thread` 包裹，避免阻塞事件循环
- 全部日志与注释使用中文；测试覆盖公开接口与边界条件
- 新增模块流程：
  1. 在模块下创建 `models.py / schemas.py / router.py`（如需要再加 `dao.py / service.py`）
  2. 在 `database.init_database()` 中导入 `<module>.models` 以确保建表
  3. 在 `main.py` 中 `app.include_router(<module>.router)`

---

## 常见问题（FAQ）
- 前端请求被 CORS 拦截？
  - 确认 `.env` 中 `ALLOWED_ORIGINS` 与前端实际来源一致（5173/3000）。
- 数据库文件在哪？
  - 默认在项目根目录下的 `database.db`，可通过 `DATABASE_PATH` 修改。
- 生产如何部署？
  - 前端：`pnpm build` 产物在 `dist/`，由任意静态服务器/Nginx/对象存储托管
  - 后端：使用 `uvicorn`/`gunicorn + uvicorn workers` 启动；建议放到反向代理之后；如需后端直出静态资源可自行添加 `StaticFiles` 挂载。

---

感谢使用本模板，祝开发顺利！
