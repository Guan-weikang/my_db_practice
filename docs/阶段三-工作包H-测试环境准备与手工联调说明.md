# 阶段三工作包 H：测试环境准备与手工联调说明

## 1. 目标

本文档用于固定阶段三的联调测试环境准备方式，确保后续前端手工联调、接口验证和权限演示都基于同一组稳定数据。

## 2. 当前阶段约定

- 所有族谱默认对所有已登录用户可读。
- `creator` 仍拥有最高权限。
- `collaborator` 仍可编辑族谱，但不可管理协作者。
- `reader` 与未被显式授权的普通已登录用户都具备只读能力。
- 协作者管理接口仍只允许 `creator` 调用。

说明：

- 默认可读仅影响“读取族谱列表与详情”。
- 默认可读不等于默认可编辑，也不等于默认可管理协作者。

## 3. 种子数据脚本

已提供可重复执行的种子数据脚本：

- [seed_stage3_manual_test_data.py](/home/mochen/db_practice/scripts/dev/seed_stage3_manual_test_data.py)

建议执行命令：

```bash
python scripts/dev/seed_stage3_manual_test_data.py
```

脚本作用：

- 创建 4 个稳定联调账号
- 创建 3 个联调用族谱
- 为其中 1 个族谱写入协作者与读者授权
- 为 2 个族谱写入最小成员数据，便于验证“非空族谱不可物理删除”

脚本设计：

- 幂等执行
- 已存在同名账号或同名族谱时不重复插入
- 可作为本地和演示环境的快速准备入口

## 4. 默认联调账号

- `stage3_creator / Password123`
- `stage3_collaborator / Password123`
- `stage3_reader / Password123`
- `stage3_viewer / Password123`

## 5. 默认联调数据

### 5.1 Stage3 Managed Tree

用途：

- 协作者列表查看
- 协作者改权
- 协作者撤销
- `collaborator` 编辑族谱
- `reader` 只读验证

授权关系：

- `stage3_creator`：创建者
- `stage3_collaborator`：协作者
- `stage3_reader`：读者
- `stage3_viewer`：未显式授权，但因默认可读仍可查看详情

### 5.2 Stage3 Empty Tree

用途：

- 验证空族谱允许物理删除

### 5.3 Stage3 Public Read Tree

用途：

- 验证未显式授权用户也能读取族谱列表与详情

## 6. 建议验证顺序

### 6.1 后端自动化验证

执行：

```bash
pytest backend/tests -q
python -m compileall backend/app backend/tests
```

预期：

- 所有阶段一到阶段三当前测试通过

### 6.2 数据准备验证

执行种子脚本后，用以下方式抽查：

- `stage3_creator` 登录后应看到自己创建的族谱，角色为 `creator`
- `stage3_collaborator` 登录后应看到：
  - `Stage3 Managed Tree`，角色为 `collaborator`
  - 其他族谱，角色为 `reader`
- `stage3_reader` 登录后应看到：
  - `Stage3 Managed Tree`，角色为 `reader`
- `stage3_viewer` 登录后应看到所有族谱，且默认至少有一部分角色为 `reader`

### 6.3 删除策略验证

- `Stage3 Empty Tree` 应允许创建者删除
- `Stage3 Managed Tree` 因已有成员，不允许物理删除

## 7. 前端手工联调前置条件

开始阶段三工作包 G 手工联调前，应先满足以下条件：

- 后端 API 可启动
- 前端工程可启动
- 种子数据脚本已执行
- 至少准备好 4 个联调账号
- 当前浏览器能完成登录流程

## 8. 当前已验证状态

- 后端族谱 CRUD 已完成
- 后端协作者管理已完成
- 默认“所有族谱对所有已登录用户可读”规则已收口到后端权限与列表逻辑
- 自动化测试已覆盖：
  - 族谱 CRUD
  - 协作者邀请、改权、撤销
  - 越权管理拒绝
  - 默认可读行为

## 9. 下一步

工作包 H 完成后，下一步进入工作包 G 的前端手工联调测试，重点验证：

- 登录后族谱列表展示
- 默认可读族谱详情访问
- 创建者进入协作者管理页
- 协作者与读者的页面可见性和行为提示
