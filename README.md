# DB_Practice

当前工作区已生成以下项目骨架：

- `backend/`：FastAPI + SQLAlchemy 2.0 后端骨架
- `frontend/`：Vue 3 + Vite 前端骨架
- `docs/`：需求、数据库、架构、计划与阶段执行文档
- `deploy/`：预留的部署说明目录
- `scripts/`：数据生成与导入脚本目录
- `data/`：数据文件目录

## 当前状态

阶段一“工程基线与开发环境收口”已完成以下基线能力：

- PostgreSQL 主表、索引、触发器和 Alembic 初始迁移已落地
- 独立 SQL 初始化脚本已提供：`scripts/sql/family_tree_init.sql`
- FastAPI 应用可启动，已接入基础 CORS、日志、统一错误响应和健康检查
- 前端可启动并成功构建
- 后端最小测试基座已建立，并包含健康检查与错误响应冒烟测试
- 阶段二后端认证闭环已接入：注册、登录、刷新令牌、登出、当前用户与族谱权限依赖
- 前端已接入登录态持久化、令牌自动续期、路由守卫和最小登录/注册页面
- 阶段三族谱与协作者模块已完成最小闭环：族谱 CRUD、协作者管理、前端列表/详情/协作者管理页已可联调
- 当前阶段三权限规则已固定为：所有已登录用户默认可读取所有族谱；`creator` 可管理协作者和删除空族谱；`collaborator` 可编辑族谱但不可管理协作者；`reader` 与未显式授权用户只读

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

联调注意：

- 若前端使用 `http://127.0.0.1:5173` 或 `http://127.0.0.1:4173` 访问，而后端 CORS 只放行 `http://localhost:5173`，浏览器会在登录前的 `OPTIONS` 预检阶段直接失败。
- 手工联调时应保证前端访问地址与 `backend/.env` 中的 CORS 白名单一致。

前端阶段二默认使用：

- `localStorage` 持久化 `accessToken`、`refreshToken` 和当前用户信息
- Axios 响应拦截器在收到 `401` 时自动尝试 `POST /auth/refresh`
- 刷新失败后清空登录态，并由路由守卫带回登录页

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

### Docker Compose 一键启动

项目已提供完整 Docker Compose 编排：

```bash
docker compose up --build -d
```

默认入口：

```text
http://localhost:18080/
```

Compose 会启动 PostgreSQL、Redis、数据库初始化任务、FastAPI 后端、Vue 前端和 Nginx。首次启动时会导入根目录的 `family_tree_db_dump.sql`，并针对 `parent_child` 表上的慢触发器提供导入前禁用、导入后恢复的保护逻辑。详细说明见 `deploy/README.md`。

停止服务但保留数据库数据：

```bash
docker compose down
```

停止并删除数据库卷：

```bash
docker compose down -v
```

### 本机开发启动

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

阶段二前端认证主流程：

1. 访问受保护路由时，未登录会自动跳转到 `/auth/login?redirect=原目标路径`
2. 登录或注册成功后，前端自动保存会话并跳回原目标路径
3. 刷新页面时，前端会先恢复本地会话，再通过 `/api/v1/auth/me` 校验当前登录态
4. Access Token 失效时，前端会自动使用 Refresh Token 续期

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

阶段三补充验证：

```bash
python scripts/dev/seed_stage3_manual_test_data.py
bash /home/mochen/db_practice/scripts/dev/stage3_probe.sh
```

## 目录说明

- `backend/tests/api/`：后端 API 冒烟测试
- `backend/tests/services/`：后续服务层测试
- `backend/tests/queries/`：后续查询层测试
- `scripts/sql/`：数据库初始化 SQL 脚本
- `scripts/dev/seed_stage3_manual_test_data.py`：阶段三联调种子数据脚本
- `scripts/dev/stage3_probe.sh`：阶段三接口与权限快速探测脚本
- `deploy/`：当前保留为部署说明预留目录
- `docs/寻根溯源族谱管理系统-总开发计划.md`：总开发计划
- `docs/阶段一-工程基线与开发环境收口-详细执行与测试验收文档.md`：阶段一详细计划
- `docs/阶段三-族谱与协作者模块-详细执行与测试验收文档.md`：阶段三详细计划
- `docs/阶段三-工作包H-测试环境准备与手工联调说明.md`：阶段三联调与测试数据说明

## 后续工作

- 阶段三收尾：文档、联调说明与验收记录收口
- 阶段四：成员与关系维护
- 阶段五及之后：复杂查询、统计、数据生成、性能优化、联调与部署
