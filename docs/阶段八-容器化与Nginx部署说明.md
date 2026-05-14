# 阶段八 容器化与 Nginx 部署说明

## 1. 目标

当前项目补齐一套适合课程演示和手工联调的部署方案：

- 使用 `Docker Compose` 编排核心服务
- 使用 `nginx` 作为统一对外入口
- 前端静态资源与后端 API 统一走一个地址访问
- 保持部署结构简单，不引入生产级编排复杂度

## 2. 已落地文件

- 根目录 `docker-compose.yml`
- 根目录 `.env.compose.example`
- `backend/Dockerfile`
- `backend/.dockerignore`
- `frontend/Dockerfile`
- `frontend/.dockerignore`
- `deploy/nginx/default.conf`
- `scripts/stage7/reimport_generated.sh`

## 3. 部署拓扑

```text
浏览器
  |
  v
nginx:80
  |-- /        -> frontend:80
  |-- /api/    -> backend:8000

backend -> postgres:5432
backend -> redis:6379
```

## 4. 服务职责

### `postgres`

- 存储业务主数据
- 使用命名卷 `postgres_data`

### `redis`

- 承载当前已接入的热点缓存
- 使用命名卷 `redis_data`

### `backend`

- 基于 `python:3.12-slim`
- 启动命令中先执行 `alembic upgrade head`
- 然后启动 `uvicorn app.main:app`

### `frontend`

- 基于 `node:24-alpine` 构建
- 产物输出到 `dist/`
- 运行态由轻量 `nginx` 容器承载静态文件

### `nginx`

- 作为唯一对外入口
- `/api/` 转发到 `backend`
- `/` 转发到 `frontend`

### `stage7-import`

- 一次性工具服务，不常驻运行
- 用于把 `data/stage7/generated` 下的 CSV 快速导入容器内数据库
- 导入完成后自动清理 Redis 业务缓存

## 5. 环境变量

首次使用建议：

```bash
cp .env.compose.example .env
```

重点变量：

- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `JWT_SECRET_KEY`
- `JWT_REFRESH_SECRET_KEY`
- `NGINX_PORT`
- `VITE_API_BASE_URL`

当前默认前端 API 地址为：

```text
/api/v1
```

这意味着浏览器端不会直接访问 `backend:8000`，而是统一通过 `nginx` 代理。

## 6. 启动方式

```bash
docker compose up --build -d
```

访问地址：

- 页面入口：`http://localhost`
- 健康检查：`http://localhost/api/v1/health/`

导入 Stage7 演示数据：

```bash
docker compose --profile tools run --rm stage7-import
```

该命令会执行：

- 等待 `postgres` 可连接
- 调用 `scripts/stage7/reimport_generated.py`
- 导入 `user_account`、`family_tree`、`tree_collaborator`、`member`、`parent_child`、`marriage`
- 对可信的 Stage7 离线 CSV 临时启用 `session_replication_role=replica`，跳过触发器校验以缩短导入时间
- 清理 `cache:v1:*`

停止：

```bash
docker compose down
```

连同卷一起清理：

```bash
docker compose down -v
```

## 7. 设计取舍

当前方案刻意保持克制：

- 不拆开发版和生产版两套 Compose
- 不接入 `gunicorn`
- 不引入 `prometheus`、`grafana`
- 不做复杂证书、域名、HTTPS 配置

原因是本项目目标是课程交付与联调演示，不需要生产级部署体系。

## 8. 当前限制

我在当前 WSL 环境内无法直接执行 `docker compose config` 或镜像构建，因为该环境没有接通 Docker Desktop 的 WSL 集成。

如果你本机已经启用 Docker Desktop 的 WSL 集成，直接在项目根目录执行：

```bash
docker compose up --build -d
```

即可验证整套部署文件。
