# DB_Practice

当前工作区已生成以下项目骨架：

- `backend/`：FastAPI + SQLAlchemy 2.0 后端骨架
- `frontend/`：Vue 3 + Vite 前端骨架
- `docs/`：需求、数据库、架构、计划与阶段执行文档
- `deploy/`：后续 Docker、Nginx 与部署配置目录
- `scripts/`：数据生成与导入脚本目录
- `data/`：数据文件目录

## 当前状态

阶段一“工程基线与开发环境收口”已完成以下基线能力：

- PostgreSQL 主表、索引、触发器和 Alembic 初始迁移已落地
- 独立 SQL 初始化脚本已提供：`scripts/sql/family_tree_init.sql`
- FastAPI 应用可启动，已接入基础 CORS、日志、统一错误响应和健康检查
- 前端可启动并成功构建
- 后端最小测试基座已建立，并包含健康检查与错误响应冒烟测试

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

前端默认 API 地址：

- `VITE_API_BASE_URL=http://localhost:8000/api/v1`

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

健康检查：

```bash
curl http://localhost:8000/api/v1/health/
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

若不走 Alembic，也可以直接执行初始化脚本：

```bash
psql -h localhost -U postgres -d family_tree_db -f /home/mochen/db_practice/scripts/sql/family_tree_init.sql
```

## 测试

后端基础冒烟测试：

```bash
pytest backend/tests -q
```

前端构建测试：

```bash
cd frontend
npm run build
```

## 目录说明

- `backend/tests/api/`：后端 API 冒烟测试
- `backend/tests/services/`：后续服务层测试
- `backend/tests/queries/`：后续查询层测试
- `scripts/sql/`：数据库初始化 SQL 脚本
- `deploy/`：当前为空目录，留待后续阶段补充 Docker Compose、Nginx 和部署文件
- `docs/寻根溯源族谱管理系统-总开发计划.md`：总开发计划
- `docs/阶段一-工程基线与开发环境收口-详细执行与测试验收文档.md`：阶段一详细计划

## 后续工作

- 阶段二：认证与权限闭环
- 阶段三：族谱与协作者模块
- 阶段四：成员与关系维护
- 阶段五及之后：复杂查询、统计、数据生成、性能优化、联调与部署
