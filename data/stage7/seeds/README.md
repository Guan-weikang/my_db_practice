# Stage7 Seed Manifests

本目录存放阶段七“真实种子谱系”清单。

设计原则：

- 只收录少量高知名度、可人工核验的真实人物
- 只固定种子层，不追求完整还原真实家谱
- 大规模成员由 `scripts/stage7/generate_dataset.py` 合成扩展
- `birth_year` / `death_year` 可保留 BCE 或模糊年份；若超出数据库 `DATE` 友好范围，生成 CSV 时会自动留空，并把真实年份保留在 manifest 与 provenance 中
- `source_system` / `source_url` 用于人工可追溯；当前仓库先提供 curated manifest，后续可扩展为自动抽取器

主要字段：

- `tree_code`：树编码
- `members[].member_code`：种子成员编码
- `members[].historical_real`：是否真实历史人物
- `members[].confidence`：`high` / `medium` / `reference_only`
- `parent_child[]`：父母关系
- `marriages[]`：婚姻关系
