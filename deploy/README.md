# Deploy

本目录现在用于存放演示部署所需配置。

已落地内容：

- `../docker-compose.yml`：统一编排 `postgres`、`redis`、`backend`、`frontend`、`nginx`
- `nginx/default.conf`：统一入口与 `/api/` 反向代理配置
- `../scripts/stage7/reimport_generated.sh`：容器内一键重导入 Stage7 CSV

部署形态说明：

- `frontend` 容器只负责构建后的静态站点
- `nginx` 作为对外唯一入口
- `nginx` 将 `/api/` 转发给 `backend`
- `backend` 启动时自动执行 `alembic upgrade head`
- `stage7-import` 作为按需运行的一次性工具容器

更完整的启动与使用说明见根目录 [README.md](/home/mochen/db_practice/README.md:1)。
