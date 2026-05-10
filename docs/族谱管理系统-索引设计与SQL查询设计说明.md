# 族谱管理系统索引设计与 SQL 查询设计说明

## 1. 文档目的与适用范围

本文档用于补充《族谱管理系统数据库设计文档》，重点说明以下内容：

- 针对族谱系统主要查询场景的索引设计
- 课程要求中的核心 SQL 查询设计
- 面向实际应用界面的常用 SQL 查询设计
- 索引与查询之间的对应关系
- 性能验证与执行计划分析建议

本文档默认采用 PostgreSQL 作为目标数据库。

## 2. 命名约定与映射说明

为便于 PostgreSQL 实际落表和脚本编写，本文档统一采用小写下划线风格命名。

与现有数据库设计文档中的命名映射如下：

- `User` -> `user_account`
- `FamilyTree` -> `family_tree`
- `TreeCollaborator` -> `tree_collaborator`
- `Member` -> `member`
- `ParentChild` -> `parent_child`
- `Marriage` -> `marriage`

本文档中的 SQL、索引和字段命名均按以下表结构理解：

- `user_account(user_id, username, password_hash, display_name, email, created_at, status)`
- `family_tree(tree_id, tree_name, surname, compiled_at, creator_user_id, description, created_at, updated_at)`
- `tree_collaborator(tree_id, user_id, access_role, invited_by, invited_at, status)`
- `member(member_id, tree_id, name, gender, birth_date, death_date, generation_no, generation_name, biography, is_alive, created_at, updated_at)`
- `parent_child(tree_id, parent_member_id, child_member_id, parent_role)`
- `marriage(tree_id, member_id_1, member_id_2, married_at, ended_at, status)`

## 3. 查询场景分析

根据需求文档与数据库设计文档，本系统的查询需求主要分为四类：

1. 权限与列表类查询
   - 查询某用户创建的族谱
   - 查询某用户可参与的族谱

2. 成员检索类查询
   - 按姓名精确查找
   - 按姓名模糊查找
   - 同一族谱内重名成员筛选

3. 关系递归类查询
   - 查询某成员的父母
   - 查询某成员的子女
   - 查询某成员所有祖先
   - 树形预览
   - 查询两人是否存在亲缘关系路径

4. 统计与分析类查询
   - Dashboard 总人数与男女比例
   - 平均寿命最长的一代
   - 年龄大于 50 且无配偶的男性成员
   - 早于本代平均出生年份的成员
   - 某曾祖父的所有曾孙（四代查询）

因此，索引设计不能只围绕单表 CRUD，而必须围绕“族谱限定 + 成员关系连接 + 模糊搜索 + 递归查询”来做。

## 4. 索引设计说明

## 4.1 设计原则

本系统索引设计遵循以下原则：

1. 大多数成员关系查询都应带 `tree_id`，因此索引优先考虑复合索引而非单列索引。
2. 姓名查询分为精确/前缀查询与任意子串模糊查询，两类查询需要不同索引。
3. 父母子女关系与婚姻关系属于高频连接表，必须单独建索引支持双向访问。
4. 低选择性字段不单独建索引，除非和高频过滤字段组成复合索引。
5. 索引应服务于课程要求中的 SQL，而不是脱离实际查询场景机械堆砌。

## 4.2 基础索引

以下索引是本系统建议保留的基础索引。

### 4.2.1 族谱与协作查询索引

```sql
CREATE INDEX idx_family_tree_creator
ON family_tree(creator_user_id);

CREATE INDEX idx_tree_collaborator_user_status_tree
ON tree_collaborator(user_id, status, tree_id);

CREATE INDEX idx_tree_collaborator_tree_status_user
ON tree_collaborator(tree_id, status, user_id);
```

**用途说明**

- `idx_family_tree_creator` 用于查询某用户创建的族谱列表。
- `idx_tree_collaborator_user_status_tree` 用于查询某用户参与的族谱。
- `idx_tree_collaborator_tree_status_user` 用于查询某族谱下的协作者列表。

## 4.2.2 成员基础查询索引

```sql
CREATE INDEX idx_member_tree_name
ON member(tree_id, name);

CREATE INDEX idx_member_tree_generation
ON member(tree_id, generation_no);

CREATE INDEX idx_member_tree_gender_birth
ON member(tree_id, gender, birth_date);
```

**用途说明**

- `idx_member_tree_name` 用于同一族谱内按姓名等值或前缀检索。
- `idx_member_tree_generation` 用于按族谱、按代统计。
- `idx_member_tree_gender_birth` 用于“男性 + 年龄范围”筛选。

## 4.2.3 父母子女关系索引

你给出的初步方案是：

```sql
CREATE INDEX idx_parent_child_parent
ON parent_child(parent_id);

CREATE INDEX idx_parent_child_child
ON parent_child(child_id);
```

这类思路是对的，但字段名需要与当前设计统一，而且在本系统中更推荐使用带 `tree_id` 的复合索引。

建议改为：

```sql
CREATE INDEX idx_parent_child_tree_parent
ON parent_child(tree_id, parent_member_id);

CREATE INDEX idx_parent_child_tree_child
ON parent_child(tree_id, child_member_id);
```

**原因**

- 绝大多数父子关系查询都会限定在某个族谱内部。
- 若只对 `parent_member_id` 或 `child_member_id` 建单列索引，优化器仍可能需要额外过滤 `tree_id`。
- 复合索引更贴合本系统的真实查询模式。

## 4.2.4 婚姻关系索引

你给出的初步方案是：

```sql
CREATE INDEX idx_marriages_member1
ON marriages(member1_id);

CREATE INDEX idx_marriages_member2
ON marriages(member2_id);
```

建议统一为：

```sql
CREATE INDEX idx_marriage_tree_member1
ON marriage(tree_id, member_id_1);

CREATE INDEX idx_marriage_tree_member2
ON marriage(tree_id, member_id_2);
```

**原因**

- 配偶查询通常需要先限定 `tree_id`。
- `marriage` 表的查找模式常为：
  - `member_id_1 = ?`
  - `member_id_2 = ?`
  - 或两者的并集
- 两个单独方向的复合索引有利于 PostgreSQL 通过 `BitmapOr` 或 `UNION ALL` 方式优化查询。

## 4.2.5 姓名模糊查询索引

PostgreSQL 下，优化姓名模糊查询建议启用 `pg_trgm`：

```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE INDEX idx_member_name_trgm
ON member USING gin (name gin_trgm_ops);
```

**说明**

- 该索引主要优化 `%关键字%` 形式的任意子串匹配。
- 该索引不能替代 `idx_member_tree_name`。
- 两者适用场景不同：
  - `tree_id + name` 组合索引：适合同族谱内等值、排序、前缀匹配
  - `GIN + pg_trgm`：适合模糊匹配

若后续高频模糊搜索始终限定在单个族谱内，可进一步考虑表达式方案或分层过滤，但本版先保留为通用设计。

## 4.3 推荐索引总表

```sql
CREATE INDEX idx_family_tree_creator
ON family_tree(creator_user_id);

CREATE INDEX idx_tree_collaborator_user_status_tree
ON tree_collaborator(user_id, status, tree_id);

CREATE INDEX idx_tree_collaborator_tree_status_user
ON tree_collaborator(tree_id, status, user_id);

CREATE INDEX idx_member_tree_name
ON member(tree_id, name);

CREATE INDEX idx_member_tree_generation
ON member(tree_id, generation_no);

CREATE INDEX idx_member_tree_gender_birth
ON member(tree_id, gender, birth_date);

CREATE INDEX idx_parent_child_tree_parent
ON parent_child(tree_id, parent_member_id);

CREATE INDEX idx_parent_child_tree_child
ON parent_child(tree_id, child_member_id);

CREATE INDEX idx_marriage_tree_member1
ON marriage(tree_id, member_id_1);

CREATE INDEX idx_marriage_tree_member2
ON marriage(tree_id, member_id_2);

CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE INDEX idx_member_name_trgm
ON member USING gin (name gin_trgm_ops);
```

## 4.4 是否还需要保留单列索引

在当前设计下，不建议再额外保留以下单列索引：

- `parent_child(parent_member_id)`
- `parent_child(child_member_id)`
- `marriage(member_id_1)`
- `marriage(member_id_2)`

原因是这些单列索引与复合索引 `(tree_id, ...)` 存在明显功能重叠，而系统中的查询通常都会携带 `tree_id`。若后续测试发现存在大量“不带 tree_id 的全局关系分析查询”，再单独补充单列索引更合理。

## 5. SQL 查询设计说明

## 5.1 SQL 设计原则

本系统的 SQL 设计遵循以下约定：

1. 所有成员关系查询默认带 `tree_id` 条件，避免跨族谱错误连接。
2. 祖先、后代、分支等层级查询统一优先采用 `WITH RECURSIVE`。
3. 配偶查询统一通过 `marriage` 两侧合并实现。
4. 年龄计算统一以 `birth_date` 与 `CURRENT_DATE` 为基础。
5. “没有配偶”统一采用 `NOT EXISTS` 写法。
6. 统计查询默认过滤必要空值。
7. 对于需要性能验证的 SQL，应额外提供 `EXPLAIN ANALYZE` 版本。

## 5.2 课程要求核心 SQL

### 5.2.1 给定成员 ID，查询其配偶及所有子女

```sql
WITH spouse_info AS (
    SELECT m2.member_id, m2.name, 'spouse' AS relation_type
    FROM marriage mg
    JOIN member m2
      ON m2.tree_id = mg.tree_id
     AND (
            (mg.member_id_1 = :member_id AND m2.member_id = mg.member_id_2)
         OR (mg.member_id_2 = :member_id AND m2.member_id = mg.member_id_1)
        )
    WHERE mg.tree_id = :tree_id
),
child_info AS (
    SELECT c.member_id, c.name, 'child' AS relation_type
    FROM parent_child pc
    JOIN member c
      ON c.tree_id = pc.tree_id
     AND c.member_id = pc.child_member_id
    WHERE pc.tree_id = :tree_id
      AND pc.parent_member_id = :member_id
)
SELECT * FROM spouse_info
UNION ALL
SELECT * FROM child_info;
```

**主要依赖索引**

- `idx_marriage_tree_member1`
- `idx_marriage_tree_member2`
- `idx_parent_child_tree_parent`

### 5.2.2 递归查询某成员的所有祖先

```sql
WITH RECURSIVE ancestor_cte AS (
    SELECT
        pc.tree_id,
        pc.child_member_id AS start_member_id,
        pc.parent_member_id AS ancestor_member_id,
        pc.parent_role,
        1 AS level
    FROM parent_child pc
    WHERE pc.tree_id = :tree_id
      AND pc.child_member_id = :member_id

    UNION ALL

    SELECT
        pc.tree_id,
        a.start_member_id,
        pc.parent_member_id AS ancestor_member_id,
        pc.parent_role,
        a.level + 1
    FROM ancestor_cte a
    JOIN parent_child pc
      ON pc.tree_id = a.tree_id
     AND pc.child_member_id = a.ancestor_member_id
)
SELECT
    a.level,
    a.parent_role,
    m.member_id,
    m.name,
    m.gender,
    m.birth_date,
    m.death_date
FROM ancestor_cte a
JOIN member m
  ON m.tree_id = a.tree_id
 AND m.member_id = a.ancestor_member_id
ORDER BY a.level, m.member_id;
```

**主要依赖索引**

- `idx_parent_child_tree_child`

### 5.2.3 统计某家族平均寿命最长的一代

```sql
WITH generation_life AS (
    SELECT
        tree_id,
        generation_no,
        AVG(EXTRACT(YEAR FROM age(COALESCE(death_date, CURRENT_DATE), birth_date))) AS avg_lifespan
    FROM member
    WHERE tree_id = :tree_id
      AND generation_no IS NOT NULL
      AND birth_date IS NOT NULL
    GROUP BY tree_id, generation_no
)
SELECT tree_id, generation_no, avg_lifespan
FROM generation_life
ORDER BY avg_lifespan DESC
LIMIT 1;
```

**主要依赖索引**

- `idx_member_tree_generation`

### 5.2.4 查询年龄超过 50 岁且没有配偶的男性成员

```sql
SELECT m.member_id, m.name, m.birth_date
FROM member m
WHERE m.tree_id = :tree_id
  AND m.gender = 'male'
  AND m.birth_date IS NOT NULL
  AND EXTRACT(YEAR FROM age(CURRENT_DATE, m.birth_date)) > 50
  AND NOT EXISTS (
      SELECT 1
      FROM marriage mg
      WHERE mg.tree_id = m.tree_id
        AND (mg.member_id_1 = m.member_id OR mg.member_id_2 = m.member_id)
  )
ORDER BY m.birth_date;
```

**主要依赖索引**

- `idx_member_tree_gender_birth`
- `idx_marriage_tree_member1`
- `idx_marriage_tree_member2`

### 5.2.5 找出出生年份早于本代平均出生年份的成员

```sql
WITH generation_birth_avg AS (
    SELECT
        tree_id,
        generation_no,
        AVG(EXTRACT(YEAR FROM birth_date)) AS avg_birth_year
    FROM member
    WHERE tree_id = :tree_id
      AND generation_no IS NOT NULL
      AND birth_date IS NOT NULL
    GROUP BY tree_id, generation_no
)
SELECT
    m.member_id,
    m.name,
    m.generation_no,
    EXTRACT(YEAR FROM m.birth_date) AS birth_year,
    g.avg_birth_year
FROM member m
JOIN generation_birth_avg g
  ON g.tree_id = m.tree_id
 AND g.generation_no = m.generation_no
WHERE m.tree_id = :tree_id
  AND m.birth_date IS NOT NULL
  AND EXTRACT(YEAR FROM m.birth_date) < g.avg_birth_year
ORDER BY m.generation_no, m.birth_date;
```

**主要依赖索引**

- `idx_member_tree_generation`

### 5.2.6 查询某曾祖父的所有曾孙（四代查询）

该查询用于课程要求中的性能对比测试。

```sql
WITH RECURSIVE descendants AS (
    SELECT
        pc.tree_id,
        pc.parent_member_id,
        pc.child_member_id,
        1 AS depth
    FROM parent_child pc
    WHERE pc.tree_id = :tree_id
      AND pc.parent_member_id = :ancestor_member_id

    UNION ALL

    SELECT
        pc.tree_id,
        pc.parent_member_id,
        pc.child_member_id,
        d.depth + 1
    FROM descendants d
    JOIN parent_child pc
      ON pc.tree_id = d.tree_id
     AND pc.parent_member_id = d.child_member_id
    WHERE d.depth < 4
)
SELECT
    m.member_id,
    m.name,
    d.depth
FROM descendants d
JOIN member m
  ON m.tree_id = d.tree_id
 AND m.member_id = d.child_member_id
WHERE d.depth = 4
ORDER BY m.member_id;
```

**主要依赖索引**

- `idx_parent_child_tree_parent`

## 5.3 常用应用查询

### 5.3.1 查询某用户创建的族谱

```sql
SELECT tree_id, tree_name, surname, compiled_at, created_at
FROM family_tree
WHERE creator_user_id = :user_id
ORDER BY created_at DESC;
```

### 5.3.2 查询某用户可访问的全部族谱

```sql
SELECT DISTINCT
    ft.tree_id,
    ft.tree_name,
    ft.surname,
    ft.creator_user_id
FROM family_tree ft
LEFT JOIN tree_collaborator tc
  ON tc.tree_id = ft.tree_id
 AND tc.user_id = :user_id
 AND tc.status = 'active'
WHERE ft.creator_user_id = :user_id
   OR tc.user_id IS NOT NULL
ORDER BY ft.created_at DESC;
```

### 5.3.3 查询某族谱下的协作者

```sql
SELECT
    u.user_id,
    u.username,
    u.display_name,
    tc.access_role,
    tc.status,
    tc.invited_at
FROM tree_collaborator tc
JOIN user_account u
  ON u.user_id = tc.user_id
WHERE tc.tree_id = :tree_id
ORDER BY tc.invited_at DESC;
```

### 5.3.4 Dashboard：统计家族总人数与男女比例

```sql
SELECT
    tree_id,
    COUNT(*) AS total_members,
    COUNT(*) FILTER (WHERE gender = 'male') AS male_count,
    COUNT(*) FILTER (WHERE gender = 'female') AS female_count,
    ROUND(
        COUNT(*) FILTER (WHERE gender = 'male')::numeric
        / NULLIF(COUNT(*), 0),
        4
    ) AS male_ratio,
    ROUND(
        COUNT(*) FILTER (WHERE gender = 'female')::numeric
        / NULLIF(COUNT(*), 0),
        4
    ) AS female_ratio
FROM member
WHERE tree_id = :tree_id
GROUP BY tree_id;
```

### 5.3.5 同一族谱内按姓名模糊查找成员

```sql
SELECT
    member_id,
    name,
    gender,
    generation_no,
    birth_date,
    death_date
FROM member
WHERE tree_id = :tree_id
  AND name ILIKE '%' || :keyword || '%'
ORDER BY generation_no NULLS LAST, name, member_id
LIMIT 50;
```

**主要依赖索引**

- `idx_member_name_trgm`
- `idx_member_tree_name`

### 5.3.6 查询某成员的父母

```sql
SELECT
    p.member_id,
    p.name,
    p.gender,
    pc.parent_role
FROM parent_child pc
JOIN member p
  ON p.tree_id = pc.tree_id
 AND p.member_id = pc.parent_member_id
WHERE pc.tree_id = :tree_id
  AND pc.child_member_id = :member_id
ORDER BY pc.parent_role;
```

### 5.3.7 查询某成员的直系子女

```sql
SELECT
    c.member_id,
    c.name,
    c.gender,
    c.birth_date
FROM parent_child pc
JOIN member c
  ON c.tree_id = pc.tree_id
 AND c.member_id = pc.child_member_id
WHERE pc.tree_id = :tree_id
  AND pc.parent_member_id = :member_id
ORDER BY c.birth_date NULLS LAST, c.member_id;
```

### 5.3.8 查询某分支的树形预览

```sql
WITH RECURSIVE tree_branch AS (
    SELECT
        m.tree_id,
        m.member_id,
        m.name,
        0 AS level,
        CAST(m.name AS TEXT) AS path_text
    FROM member m
    WHERE m.tree_id = :tree_id
      AND m.member_id = :root_member_id

    UNION ALL

    SELECT
        c.tree_id,
        c.member_id,
        c.name,
        tb.level + 1,
        tb.path_text || ' -> ' || c.name
    FROM tree_branch tb
    JOIN parent_child pc
      ON pc.tree_id = tb.tree_id
     AND pc.parent_member_id = tb.member_id
    JOIN member c
      ON c.tree_id = pc.tree_id
     AND c.member_id = pc.child_member_id
)
SELECT *
FROM tree_branch
ORDER BY path_text;
```

### 5.3.9 查询两个人是否存在亲缘关系路径

该查询本质上是图遍历问题。可将 `parent_child` 与 `marriage` 两类关系统一展开为边，再用递归 CTE 搜索路径。

```sql
WITH RECURSIVE relation_edges AS (
    SELECT tree_id, parent_member_id AS from_member, child_member_id AS to_member
    FROM parent_child
    WHERE tree_id = :tree_id

    UNION

    SELECT tree_id, child_member_id AS from_member, parent_member_id AS to_member
    FROM parent_child
    WHERE tree_id = :tree_id

    UNION

    SELECT tree_id, member_id_1 AS from_member, member_id_2 AS to_member
    FROM marriage
    WHERE tree_id = :tree_id

    UNION

    SELECT tree_id, member_id_2 AS from_member, member_id_1 AS to_member
    FROM marriage
    WHERE tree_id = :tree_id
),
path_search AS (
    SELECT
        :tree_id AS tree_id,
        :member_a AS current_member,
        ARRAY[:member_a] AS path_members

    UNION ALL

    SELECT
        e.tree_id,
        e.to_member,
        ps.path_members || e.to_member
    FROM path_search ps
    JOIN relation_edges e
      ON e.tree_id = ps.tree_id
     AND e.from_member = ps.current_member
    WHERE NOT e.to_member = ANY(ps.path_members)
)
SELECT path_members
FROM path_search
WHERE current_member = :member_b
ORDER BY array_length(path_members, 1)
LIMIT 1;
```

**说明**

- 该查询满足“单个 SQL”实现路径搜索的要求。
- 在大规模数据下，路径搜索性能需要结合测试数据分布进一步验证。
- 若后续需要展示更友好的亲缘链路，可在结果基础上再关联 `member` 表取姓名。

## 6. 性能验证建议

## 6.1 姓名模糊查询性能对比

建议比较以下两种情况：

1. 仅有普通索引 `idx_member_tree_name`
2. 增加 `idx_member_name_trgm`

测试 SQL：

```sql
EXPLAIN ANALYZE
SELECT member_id, name
FROM member
WHERE tree_id = :tree_id
  AND name ILIKE '%' || :keyword || '%';
```

观察重点：

- 是否由顺序扫描变为 GIN 索引相关扫描
- 总执行时间是否明显下降
- 在大族谱成员量下是否仍可接受

## 6.2 四代查询性能对比

建议比较以下两种情况：

1. 不创建 `idx_parent_child_tree_parent`
2. 创建 `idx_parent_child_tree_parent`

测试 SQL：

```sql
EXPLAIN ANALYZE
WITH RECURSIVE descendants AS (
    SELECT tree_id, parent_member_id, child_member_id, 1 AS depth
    FROM parent_child
    WHERE tree_id = :tree_id
      AND parent_member_id = :ancestor_member_id

    UNION ALL

    SELECT pc.tree_id, pc.parent_member_id, pc.child_member_id, d.depth + 1
    FROM descendants d
    JOIN parent_child pc
      ON pc.tree_id = d.tree_id
     AND pc.parent_member_id = d.child_member_id
    WHERE d.depth < 4
)
SELECT *
FROM descendants
WHERE depth = 4;
```

观察重点：

- 递归阶段是否能够稳定走 `parent_child(tree_id, parent_member_id)` 索引
- 是否减少顺序扫描或重复回表开销
- 执行时间是否随数据规模增长仍保持可接受

## 6.3 报告建议提交内容

实验报告中的性能分析部分建议至少包括：

- 索引定义 SQL
- 被测试的查询 SQL
- `EXPLAIN` 或 `EXPLAIN ANALYZE` 输出
- 建索引前后执行时间对比
- 对执行计划变化的简要解释

## 7. 设计取舍与注意事项

1. 本文档采用的小写下划线命名是后续实际建库的推荐命名，与前一份数据库设计文档中的大写实体名属于同一逻辑模型的不同表示方式。
2. 姓名模糊搜索的 trigram 索引是 PostgreSQL 特性，若未来切换数据库，该部分设计需要调整。
3. `generation_no` 是统计分析的重要支撑字段，因此相关索引具有合理性。
4. 对于“亲缘路径查询”这类图遍历问题，SQL 可以完成，但性能高度依赖数据规模和路径深度，必要时可在应用层做缓存或限制搜索深度。
5. 本文档优先保证课程要求和后续实现衔接，不追求一次性覆盖所有潜在分析型查询。

## 8. 总结

本方案在你给出的初始索引思路基础上做了以下完善：

- 将单列关系索引调整为更适合本系统的复合索引
- 补充了协作者查询、辈分统计、年龄筛选等场景索引
- 区分了普通姓名索引与 `pg_trgm` 模糊索引的适用范围
- 完整补充了课程要求 SQL 与常用应用 SQL
- 明确了每类查询的主要依赖索引和性能验证方法

这份文档可以直接作为后续索引脚本、查询脚本和实验报告“SQL 与性能优化”章节的设计依据。
