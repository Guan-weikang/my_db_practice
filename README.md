# DB_Practice

当前工作区已生成以下项目骨架：

- `backend/`：FastAPI + SQLAlchemy 2.0 后端骨架
- `frontend/`：Vue 3 + Vite 前端骨架
- `scripts/`：数据生成与导入脚本目录
- `data/`：数据文件目录

## 环境要求

- Python 3.12
- Node.js 20+
- PostgreSQL 16+
- Redis 7+

## 环境配置

后端使用 `backend/.env`，前端开发环境可基于 `frontend/.env.example` 或 `frontend/.env.development`。

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.development
```

当前后端模板默认连接：

- PostgreSQL：`postgresql+asyncpg://postgres:123456@localhost:5432/family_tree_db`
- Redis：`redis://localhost:6379/0`

## 安装依赖

后端建议在 `common_use` conda 环境中安装：

```bash
conda activate common_use
python -m pip install -r backend/requirements/base.txt
```

前端安装：

```bash
cd frontend
npm install
```

## 启动项目

后端需要在 `backend/` 目录下运行，这样 `app.*` 导入和 `.env` 读取路径才是正确的：

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

前端开发：

```bash
cd frontend
npm run dev -- --host 0.0.0.0 --port 5173
```

## Alembic

已保留 Alembic 基础目录，迁移文件放在 `backend/alembic/versions/`。

常用命令：

```bash
cd backend
alembic revision --autogenerate -m "init schema"
alembic upgrade head
```

Alembic 会读取 `backend/.env` 中的 `DATABASE_URL`，并自动将 `asyncpg` 连接转换为迁移使用的 `psycopg` 连接。

## 后续工作

- PostgreSQL 建表与初始迁移
- 认证与权限实现
- 族谱、成员、关系的完整业务逻辑
- Vue 页面与接口联调
