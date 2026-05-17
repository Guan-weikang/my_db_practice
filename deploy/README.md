# Deploy

本目录保存 Docker Compose 部署所需的反向代理配置和数据库初始化脚本。

## 一键启动

在项目根目录执行：

```bash
docker compose up --build -d
```

默认启动以下服务：

- `postgres`：PostgreSQL 17
- `redis`：Redis 7.4
- `db-init`：一次性数据库导入/迁移任务
- `backend`：FastAPI API 服务
- `frontend`：Vue 静态站点
- `nginx`：统一入口，默认监听宿主机 `18080` 端口

Docker 还会额外在宿主机暴露调试端口，默认是 PostgreSQL `15432` 和 Redis `16379`，避免和 WSL 里本机已有的 `5432/6379` 冲突。容器内服务仍通过 `postgres:5432` 和 `redis:6379` 互联。

启动后访问：

```text
http://localhost:18080/
```

后端健康检查：

```text
http://localhost:18080/api/v1/health/
```

## 数据库初始化

首次启动时，`db-init` 会在数据库还没有业务表时导入根目录的 `family_tree_db_dump.sql`。

这个 dump 文件已经包含表结构、索引、函数、触发器和数据。导入完成后，脚本会执行：

```bash
alembic stamp head
```

这样 Alembic 会把当前数据库标记为最新版本，避免对已经存在的表重复执行建表迁移。

如果没有 dump 文件，或设置 `IMPORT_DUMP_ON_EMPTY_DB=0`，则会执行：

```bash
alembic upgrade head
```

## 慢触发器处理

项目中较慢的触发器是：

```text
public.parent_child.trg_prevent_parent_child_cycle
```

Compose 默认设置：

```env
DISABLE_SLOW_TRIGGER_DURING_IMPORT=1
SLOW_TRIGGER_TABLE=public.parent_child
SLOW_TRIGGER_NAME=trg_prevent_parent_child_cycle
```

`db-init` 会在导入或迁移前尝试禁用该触发器，并在结束时恢复。对于当前 `family_tree_db_dump.sql`，触发器本身是在数据导入后创建的，因此这一步通常不会额外生效；它主要用于后续你用已有 schema 执行批量数据导入的场景。

## 常用命令

查看状态：

```bash
docker compose ps
```

查看初始化日志：

```bash
docker compose logs db-init
```

查看后端日志：

```bash
docker compose logs -f backend
```

需要从 PyCharm 或宿主机直连容器数据库时，使用：

- PostgreSQL: `localhost:15432`
- Redis: `localhost:16379`

停止服务但保留数据库卷：

```bash
docker compose down
```

删除容器和数据库卷：

```bash
docker compose down -v
```

## 磁盘占用提醒

PostgreSQL 数据保存在命名卷 `postgres_data`，Redis 数据保存在 `redis_data`。如果只是重启或更新代码，使用 `docker compose down` 即可；只有确认不需要保留数据库数据时，再使用 `docker compose down -v`。

可以定期查看 Docker 占用：

```bash
docker system df
```
