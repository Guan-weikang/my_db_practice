# 阶段六：Dashboard 与统计分析详细执行与测试验收文档

## 1. 文档目的

本文档用于细化《[寻根溯源族谱管理系统-总开发计划](/home/mochen/db_practice/docs/寻根溯源族谱管理系统-总开发计划.md)》中的“阶段六：Dashboard 与统计分析”，作为阶段六实施、联调与验收的直接依据。

本文档默认承接以下前提：

- 阶段一已固定统一错误结构、分页结构和测试基座。
- 阶段二已完成登录鉴权与族谱访问权限基线。
- 阶段三已完成族谱列表、详情与协作者访问闭环。
- 阶段四已完成成员、父母子女、婚姻关系维护能力。
- 阶段五已完成搜索、分支树、祖先查询、亲缘路径以及稳定查询测试数据基线。

## 2. 阶段目标

本阶段的目标是让“看统计、验结果、支撑课程分析题”成为正式可用的只读能力，并为后续阶段的数据生成、性能测试和最终演示提供稳定统计入口，具体包括：

- 完成 Dashboard 基础统计接口。
- 完成课程要求的三类统计分析接口。
- 统一统计结果结构和只读权限边界。
- 完成 Dashboard 页面最小展示闭环。
- 建立阶段六自动化测试、手工联调和复用数据说明。

## 3. 范围与边界

### 3.1 本阶段范围

- `analytics` 模块接口与响应模型
- 原生 SQL 聚合查询实现
- 统计查询参数、结果整形和权限复用
- Dashboard 页面基础展示与族谱切换
- 阶段六测试数据补充与自动化测试

### 3.2 本阶段不做

- 不实现阶段七的大规模性能专项
- 不引入 Redis、物化视图或异步离线预聚合
- 不实现导出报表、图表下载或打印能力
- 不新增统计模块的全局 Pinia store
- 不改动阶段四、五已落地的成员、关系和查询表结构
- 不把 Dashboard 扩展成复杂 BI 页面

## 4. 阶段六固定业务规则

- 延续当前系统基线：所有已登录用户默认可读取族谱，因此也默认可读取该族谱下的统计结果。
- 本阶段所有接口均为只读接口，统一接入 `require_tree_reader`。
- 所有统计接口必须显式限定 `tree_id`，不做跨族谱聚合。
- Dashboard 统计结果服务于单个族谱视角，不做用户全局统计首页。
- “男女比例”仅对 `male` 与 `female` 统计出比率；`unknown` 计入总人数，但不参与男女比率分子。
- “平均寿命最长的一代”只统计 `generation_no` 与 `birth_date` 均非空的成员；寿命按 `age(COALESCE(death_date, CURRENT_DATE), birth_date)` 计算。
- “年龄超过 50 岁且没有配偶的男性成员”按需求文档口径实现：年龄基于 `CURRENT_DATE` 计算；只要在 `marriage` 表中存在婚姻记录，无论 `active` 还是 `ended`，都不属于“没有配偶”。
- “出生年份早于该辈分平均出生年份的成员”按出生年份比较，不按完整出生日期比较。
- 列表型统计接口本阶段不分页，优先保证课程题结果可直接核对与展示。
- 本阶段默认不启用缓存；若后续需要缓存，只允许作为服务层可插拔优化，不改变接口契约。

## 5. 交付物

本阶段完成后，至少应产出以下成果：

1. 可用的 Dashboard 统计接口
2. 可用的平均寿命最长一代接口
3. 可用的超过 50 岁且无配偶男性成员接口
4. 可用的出生年份早于本代平均出生年份成员接口
5. 已落地的统计响应模型
6. 已落地的 Dashboard 页面与族谱切换入口
7. 阶段六测试数据补充说明与自动化测试
8. 更新后的阶段六执行文档与验收说明

## 6. 详细执行任务

## 6.1 工作包 A：统计接口契约与结果模型收口

目标：

- 在编码前固定阶段六的接口、返回结构、权限边界和空结果语义，避免前后端联调时重复改口径。

具体任务：

- 固定 `analytics` 模块接口：
  - `GET /api/v1/family-trees/{tree_id}/analytics/dashboard`
  - `GET /api/v1/family-trees/{tree_id}/analytics/generation/max-average-lifespan`
  - `GET /api/v1/family-trees/{tree_id}/analytics/members/older-than-50-unmarried-male`
  - `GET /api/v1/family-trees/{tree_id}/analytics/members/before-generation-average-birth-year`
- 固定所有统计接口统一接入 `require_tree_reader`
- 固定 Dashboard 返回结构：
  - `tree_id`
  - `summary`
- `summary` 固定字段：
  - `total_members`
  - `male_count`
  - `female_count`
  - `unknown_count`
  - `male_ratio`
  - `female_ratio`
- 固定“平均寿命最长的一代”返回结构：
  - `tree_id`
  - `item`
- `item` 为空时返回 `null`，非空时固定字段：
  - `generation_no`
  - `avg_lifespan_years`
- 固定“超过 50 岁且没有配偶的男性成员”返回结构：
  - `tree_id`
  - `items`
- `items` 每项固定字段：
  - `member_id`
  - `name`
  - `birth_date`
  - `age_years`
  - `generation_no`
  - `generation_name`
- 固定“出生年份早于本代平均出生年份的成员”返回结构：
  - `tree_id`
  - `items`
- `items` 每项固定字段：
  - `member_id`
  - `name`
  - `generation_no`
  - `generation_name`
  - `birth_year`
  - `avg_birth_year`
- 固定错误行为：
  - 族谱不存在返回 `404`
  - 未登录访问返回 `401`
  - 无该族谱读取权限返回 `403`

输出物：

- 阶段六接口清单
- 响应模型清单
- 统计口径清单
- 阶段六读取权限矩阵

完成定义：

- 前后端对阶段六接口名、字段名、空结果语义和只读权限边界无歧义。

## 6.2 工作包 B：Dashboard 汇总统计闭环

目标：

- 让单个族谱的总人数、男女数量和男女比例成为正式接口能力，并能直接支撑 Dashboard 顶部统计卡片。

具体任务：

- 在 `backend/app/queries/analytics_queries.py` 中落地 Dashboard 原生 SQL
- 查询固定限定 `tree_id`
- 固定统计：
  - 总人数 `total_members`
  - 男性人数 `male_count`
  - 女性人数 `female_count`
  - 未知性别人数 `unknown_count`
  - 男性比例 `male_ratio`
  - 女性比例 `female_ratio`
- 比率固定保留 4 位小数
- 总人数为 0 时：
  - `total_members = 0`
  - 其他人数为 `0`
  - `male_ratio = null`
  - `female_ratio = null`

实现分层固定为：

- `queries` 负责原生 SQL
- `services/analytics_service.py` 负责结果归一化和响应拼装
- `api/routers/analytics.py` 只负责收参、鉴权和调服务

完成定义：

- Dashboard 汇总接口返回结果与数据库真实数据一致，可直接用于统计卡片展示。

## 6.3 工作包 C：课程统计分析一闭环

目标：

- 提供“统计某个家族中平均寿命最长的一代人”的正式查询能力。

具体任务：

- 在 `backend/app/queries/analytics_queries.py` 中实现平均寿命最长一代 SQL
- 固定只纳入：
  - `generation_no IS NOT NULL`
  - `birth_date IS NOT NULL`
- 寿命计算固定为：
  - 已故成员：`age(death_date, birth_date)`
  - 在世成员：`age(CURRENT_DATE, birth_date)`
- 平均寿命结果字段固定命名为 `avg_lifespan_years`
- 若存在多代平均寿命并列最高：
  - 按 `generation_no ASC` 选第一条，保证结果稳定
- 若无可统计成员：
  - 返回 `item = null`

完成定义：

- 输入族谱后，系统可稳定返回平均寿命最长的一代，且 SQL 可独立执行复核。

## 6.4 工作包 D：课程统计分析二闭环

目标：

- 提供“查询所有年龄超过 50 岁、且没有配偶的男性成员”的正式查询能力。

具体任务：

- 在 `backend/app/queries/analytics_queries.py` 中实现未婚高龄男性查询 SQL
- 固定筛选条件：
  - `gender = 'male'`
  - `birth_date IS NOT NULL`
  - `EXTRACT(YEAR FROM age(CURRENT_DATE, birth_date)) > 50`
  - 在 `marriage` 表中不存在该成员任一婚姻记录
- 查询结果固定返回：
  - `member_id`
  - `name`
  - `birth_date`
  - `age_years`
  - `generation_no`
  - `generation_name`
- 固定排序：
  - `birth_date ASC`
  - `member_id ASC`

完成定义：

- 系统可稳定返回符合条件的成员列表，且“无配偶”语义在 `active` / `ended` 婚姻场景下无歧义。

## 6.5 工作包 E：课程统计分析三闭环

目标：

- 提供“找出家族中出生年份早于该辈分平均出生年份的所有成员”的正式查询能力。

具体任务：

- 在 `backend/app/queries/analytics_queries.py` 中实现按代平均出生年份统计 SQL
- 固定只纳入：
  - `generation_no IS NOT NULL`
  - `birth_date IS NOT NULL`
- 先按 `tree_id + generation_no` 计算 `avg_birth_year`
- 再筛出：
  - `EXTRACT(YEAR FROM birth_date) < avg_birth_year`
- 查询结果固定返回：
  - `member_id`
  - `name`
  - `generation_no`
  - `generation_name`
  - `birth_year`
  - `avg_birth_year`
- 固定排序：
  - `generation_no ASC`
  - `birth_year ASC`
  - `member_id ASC`

完成定义：

- 系统可稳定返回所有“出生年份早于本代平均出生年份”的成员，且结果可直接对照 SQL 验证。

## 6.6 工作包 F：后端服务层、路由层与 Schema 收口

目标：

- 让阶段六不仅有 SQL，还形成稳定的服务层封装、API 输出和类型约束。

具体任务：

- 新增 `backend/app/services/analytics_service.py`
- 扩展 `backend/app/schemas/analytics.py`
- 替换当前 `backend/app/api/routers/analytics.py` 的占位实现
- 路由实现风格与阶段五保持一致：
  - 路由负责参数与权限
  - 服务负责查库与整形
  - Query 负责原生 SQL
- 固定所有响应都使用 `response_model`
- 固定空结果语义：
  - Dashboard 始终返回 `summary`
  - 单条统计接口可返回 `item = null`
  - 列表统计接口空命中时返回 `items = []`

完成定义：

- 阶段六所有接口具备正式 schema、正式服务实现和正式权限接入，不再保留占位返回。

## 6.7 工作包 G：Dashboard 页面与前端联调闭环

目标：

- 让阶段六不只有后端统计接口，也有最小可演示的前端 Dashboard 页面。

具体任务：

- 补齐 `frontend/src/api/analytics.ts`
- 改造 `frontend/src/views/dashboard/DashboardView.vue`
- 页面固定职责：
  - 加载当前用户可访问的族谱列表
  - 允许切换目标族谱
  - 展示 Dashboard 汇总卡片
  - 展示三类课程统计结果
- Dashboard 页面固定使用局部状态管理，不新增全局 Pinia store
- 页面默认行为固定为：
  - 若 URL 中带 `treeId`，优先加载该族谱
  - 否则默认加载可访问族谱列表中的第一个
- 页面展示固定分为四块：
  - 汇总统计卡片
  - 平均寿命最长一代
  - 超过 50 岁且没有配偶的男性成员列表
  - 出生年份早于本代平均出生年份成员列表
- 每块结果都需覆盖：
  - `loading`
  - `error`
  - `empty`
  - `success`

完成定义：

- 登录后进入 Dashboard，可切换族谱并看到完整统计结果展示闭环。

## 6.8 工作包 H：测试数据、自动化测试与手工验收说明

目标：

- 为阶段六建立稳定、可复用、可解释的统计验证数据基线。

具体任务：

- 在阶段五种子数据基础上补充以下确定性样例：
  - 至少 1 个空成员族谱
  - 至少 1 个仅包含 `unknown` 性别成员的样例
  - 至少 2 个不同代际且寿命差异明显的样例
  - 至少 1 个超过 50 岁且无婚姻记录的男性成员
  - 至少 1 个超过 50 岁但存在 `ended` 婚姻的男性成员
  - 至少 1 组可验证“早于本代平均出生年份”的同代成员样例
- 后端测试按三层补齐：
  - `tests/queries/`：验证 SQL 聚合结果
  - `tests/services/`：验证结果整形和空结果语义
  - `tests/api/`：验证接口行为、权限与响应结构
- 固定关键测试用例：
  - Dashboard：空树、混合性别、仅 unknown 性别、比例精度
  - 平均寿命最长一代：正常命中、并列场景、空结果
  - 超过 50 岁无配偶男性：正常命中、已结束婚姻排除、空结果
  - 早于本代平均出生年份：正常命中、同代多人比较、空结果
  - 权限：创建者、reader、默认可读用户可访问；未登录拒绝
- 固定验证命令：
  - `pytest backend/tests -q`
  - `python -m compileall backend/app backend/tests scripts/dev`
  - `npm run build`

完成定义：

- 阶段六拥有稳定测试数据、自动化校验和可复述的手工验收口径。

## 7. 推荐执行顺序

建议按以下顺序推进：

1. 工作包 A：统计接口契约与结果模型收口
2. 工作包 B：Dashboard 汇总统计闭环
3. 工作包 C：课程统计分析一闭环
4. 工作包 D：课程统计分析二闭环
5. 工作包 E：课程统计分析三闭环
6. 工作包 F：后端服务层、路由层与 Schema 收口
7. 工作包 G：Dashboard 页面与前端联调闭环
8. 工作包 H：测试数据、自动化测试与手工验收说明

原因：

- 先固定接口和返回结构，再落地 SQL，可减少前后端返工。
- Dashboard 汇总最简单，先闭环可提供页面骨架的首批数据源。
- 三类课程统计都依赖成员与婚姻数据，适合在同一阶段连续实现和测试。
- 服务层和 schema 统一收口后，前端联调更稳定。
- 测试数据和自动化测试应在接口稳定后统一补齐，避免多次重写断言。

## 8. 阶段六验收标准

### 8.1 Dashboard 汇总接口验收

- `GET /analytics/dashboard` 可返回总人数、男女数量和男女比例。
- 统计结果与数据库真实数据一致。
- 空族谱和仅 unknown 性别场景返回结构稳定。

### 8.2 三类课程统计接口验收

- `GET /analytics/generation/max-average-lifespan` 可返回平均寿命最长的一代。
- `GET /analytics/members/older-than-50-unmarried-male` 可返回超过 50 岁且没有配偶的男性成员。
- `GET /analytics/members/before-generation-average-birth-year` 可返回出生年份早于本代平均出生年份的成员。
- 所有课程要求 SQL 都可单条执行并可复用到接口。

### 8.3 权限与边界验收

- 所有已登录用户都可读取阶段六统计结果。
- 未登录用户不可访问统计接口。
- 非法或不存在的族谱访问被明确拒绝。
- 阶段六边界明确，不混入性能专项、导入导出和缓存系统落地实现。

### 8.4 Dashboard 页面验收

- 登录后可进入 Dashboard 页面。
- 页面可切换当前展示的族谱。
- 页面可稳定展示 4 组统计结果和对应空状态、错误状态。
- 接口返回结果可直接支撑 Dashboard 页面。

### 8.5 文档与测试验收

- 阶段六接口、字段、统计口径、空结果语义和测试命令有文档说明。
- 自动化测试覆盖成功路径、空结果路径和关键异常路径。
- 查询层、服务层、接口层三层测试都有落地。

## 9. 测试计划与用例

### 9.1 Dashboard 汇总测试

- 验证空树统计返回 0 与空比例。
- 验证混合性别统计结果正确。
- 验证仅 unknown 性别时男女比率为空。
- 验证比例精度与数量字段一致。

### 9.2 平均寿命最长一代测试

- 验证正常数据下可返回平均寿命最长的一代。
- 验证并列场景按 `generation_no ASC` 稳定取值。
- 验证缺少 `birth_date` 或 `generation_no` 的成员不会污染统计。
- 验证无可统计成员时返回 `item = null`。

### 9.3 超过 50 岁无配偶男性测试

- 验证符合条件成员被正确返回。
- 验证存在 `active` 婚姻成员被排除。
- 验证存在 `ended` 婚姻成员也被排除。
- 验证空结果返回空列表而非报错。

### 9.4 出生年份早于本代平均出生年份测试

- 验证同代平均出生年份计算正确。
- 验证仅返回出生年份严格早于平均值的成员。
- 验证无可比较成员时返回空列表。

### 9.5 前端手工联调测试

- 验证 Dashboard 初次进入可自动加载默认族谱统计。
- 验证切换族谱后四块统计结果同步刷新。
- 验证各块的 loading、error、empty、success 状态展示。
- 验证页面在空树与无命中统计场景下仍可稳定展示。

## 10. 后续衔接

阶段六完成后，下一阶段应直接进入“阶段七：模拟数据、导入导出与性能优化”，重点复用本阶段形成的：

- 稳定的 `analytics` 接口骨架
- 稳定的统计 SQL 实现
- 稳定的 Dashboard 页面入口
- 稳定的统计测试数据集

同时，阶段七的性能验证也应复用本阶段落地的：

- Dashboard 汇总统计 SQL
- 平均寿命最长一代 SQL
- 超过 50 岁无配偶男性 SQL
- 早于本代平均出生年份成员 SQL
