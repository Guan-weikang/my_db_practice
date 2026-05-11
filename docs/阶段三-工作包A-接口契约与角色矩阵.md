# 阶段三工作包 A：接口契约与角色矩阵

## 1. 文档目的

本文档用于固化阶段三“族谱与协作者模块”的接口契约、请求响应结构和角色能力矩阵，作为后续工作包 B 及之后实现的直接依据。

本文档默认承接以下前提：

- 阶段一已固定统一错误结构与分页结构
- 阶段二已完成登录鉴权与 `creator` / `collaborator` / `reader` 权限依赖

## 2. 接口清单

### 2.1 族谱模块

- `GET /api/v1/family-trees/`
- `POST /api/v1/family-trees/`
- `GET /api/v1/family-trees/accessible`
- `GET /api/v1/family-trees/{tree_id}`
- `PATCH /api/v1/family-trees/{tree_id}`
- `DELETE /api/v1/family-trees/{tree_id}`

说明：

- `GET /api/v1/family-trees/` 作为标准可访问族谱列表接口。
- `GET /api/v1/family-trees/accessible` 作为兼容保留接口，响应结构与标准列表接口保持一致。

### 2.2 协作者模块

- `GET /api/v1/family-trees/{tree_id}/collaborators/`
- `POST /api/v1/family-trees/{tree_id}/collaborators/`
- `PATCH /api/v1/family-trees/{tree_id}/collaborators/{user_id}`
- `DELETE /api/v1/family-trees/{tree_id}/collaborators/{user_id}`

## 3. 请求响应模型

### 3.1 族谱请求模型

`FamilyTreeCreateRequest`

- `tree_name: str`
- `surname: str`
- `compiled_at: date | null`
- `description: str | null`

`FamilyTreeUpdateRequest`

- `tree_name: str | null`
- `surname: str | null`
- `compiled_at: date | null`
- `description: str | null`

### 3.2 族谱响应模型

`FamilyTreeResponse`

- `tree_id: int`
- `tree_name: str`
- `surname: str`
- `compiled_at: date | null`
- `description: str | null`

`FamilyTreeDetailResponse`

- 继承 `FamilyTreeResponse`
- 增加 `access_role: "creator" | "collaborator" | "reader"`

`PaginatedFamilyTreeResponse`

- `items: AccessibleFamilyTreeListItem[]`
- `total: int`
- `page: int`
- `page_size: int`

### 3.3 协作者请求模型

`CollaboratorCreateRequest`

- `user_id: int`
- `access_role: "collaborator" | "reader"`

`CollaboratorUpdateRequest`

- `access_role: "collaborator" | "reader"`

### 3.4 协作者响应模型

`CollaboratorResponse`

- `user_id: int`
- `username: str`
- `display_name: str | null`
- `access_role: "collaborator" | "reader"`
- `status: "active" | "revoked" | "pending"`
- `invited_by: int`
- `invited_at: datetime`

`PaginatedCollaboratorResponse`

- `items: CollaboratorResponse[]`
- `total: int`
- `page: int`
- `page_size: int`

## 4. 权限矩阵

### 4.1 族谱角色能力

- 默认规则：所有已登录用户都可读取族谱列表与族谱详情；未显式授权的登录用户在读取时视为 `reader`
- `creator`：可读、可改、可删族谱，可查看和管理协作者
- `collaborator`：可读、可改族谱，不可删族谱，不可管理协作者
- `reader`：仅可读族谱，不可修改族谱，不可管理协作者
- 未登录用户：不可读取详情，不可管理协作者

### 4.2 接口与角色对应

- `GET /api/v1/family-trees/`：登录即可
- `POST /api/v1/family-trees/`：登录即可
- `GET /api/v1/family-trees/{tree_id}`：`creator` / `collaborator` / `reader`
- `PATCH /api/v1/family-trees/{tree_id}`：`creator` / `collaborator`
- `DELETE /api/v1/family-trees/{tree_id}`：仅 `creator`
- `GET /api/v1/family-trees/{tree_id}/collaborators/`：仅 `creator`
- `POST /api/v1/family-trees/{tree_id}/collaborators/`：仅 `creator`
- `PATCH /api/v1/family-trees/{tree_id}/collaborators/{user_id}`：仅 `creator`
- `DELETE /api/v1/family-trees/{tree_id}/collaborators/{user_id}`：仅 `creator`

## 5. 数据约束取舍

- `creator` 身份以 `family_tree.creator_user_id` 为准。
- 协作者表只承载显式 `collaborator` 与显式 `reader` 两类授权关系。
- 阶段三“邀请协作者”定义为创建者直接授权，不引入邮件邀请和确认流。
- 协作者记录推荐保留历史状态，撤销优先使用 `revoked`，而不是物理删除。
- 撤销显式授权后，目标用户仍保留系统默认只读能力，但不再作为该族谱的显式协作者出现在管理列表中。

## 6. 后续实现边界

- 工作包 A 只固定契约，不在本包内完成完整 CRUD 业务实现。
- 工作包 B 开始进入 schema、repository、service 的正式落地。
- 工作包 C 之后再完成列表、详情、创建、更新、删除和协作者管理的真实业务闭环。
