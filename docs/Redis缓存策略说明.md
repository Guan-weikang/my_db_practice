# Redis 缓存策略说明

## 1. 目标

Redis 用于缓存大规模族谱下的只读查询结果，降低重复进入孔氏等大族谱时的数据库压力和页面等待时间。

当前实现采用“缓存失败不影响业务”的策略：Redis 不可用时接口自动回退到数据库查询。

## 2. 已缓存接口

### 族谱基础信息

- `GET /api/v1/family-trees`
- `GET /api/v1/family-trees/accessible`
- `GET /api/v1/family-trees/{tree_id}`

### 成员辅助信息

- `GET /api/v1/family-trees/{tree_id}/members/id-range`
- `GET /api/v1/family-trees/{tree_id}/members`

### Dashboard 统计

- `GET /api/v1/family-trees/{tree_id}/analytics/dashboard`
- `GET /api/v1/family-trees/{tree_id}/analytics/generation/max-average-lifespan`
- `GET /api/v1/family-trees/{tree_id}/analytics/members/older-than-50-unmarried-male`
- `GET /api/v1/family-trees/{tree_id}/analytics/members/before-generation-average-birth-year`

### 结构查询

- `GET /api/v1/family-trees/{tree_id}/search/branch-tree`
- `GET /api/v1/family-trees/{tree_id}/kinship/ancestors/{member_id}`
- `GET /api/v1/family-trees/{tree_id}/kinship/path`

## 3. TTL

- 族谱列表：`120` 秒
- 族谱详情、统计、结构查询：`300` 秒
- 成员 ID 范围：`600` 秒
- 成员列表分页：`180` 秒

这些 TTL 适合当前手工联调和演示场景。若进入生产场景，建议结合访问量和数据更新频率重新调整。

## 4. 失效策略

以下写操作完成后会按族谱维度清理缓存：

- 创建、修改、删除族谱
- 创建、修改、删除成员
- 创建、删除父子关系
- 创建、修改、删除婚姻关系
- 邀请、修改、撤销协作者

清理范围：

- `tree:{tree_id}:*`
- `family-trees:*`

## 5. 后续可扩展方向

- 缓存成员详情和搜索结果。
- 对高频结构查询加入“预热脚本”，在导入阶段七数据后提前写入缓存。
- 对超大图谱查询增加服务端结果压缩或只返回前 N 层图谱数据。
- 增加缓存命中率日志，用于判断哪些接口最值得继续优化。
