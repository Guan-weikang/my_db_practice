# Stage7 Tree Profiles

本目录不再保存任何真实历史人物 seed 数据。

阶段七现已切换为“全量规则生成”模式：

- 族谱名称与规模配置仍保留
- 所有成员均由生成器按统一规则产生
- 不使用真实历史人物姓名、关系、生卒年
- `manifest_index.json` 只保存树配置索引，不保存人物清单

构建索引命令：

```bash
python scripts/stage7/build_seed_manifests.py
```
