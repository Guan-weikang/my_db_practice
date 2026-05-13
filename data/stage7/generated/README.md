# Stage7 Generated CSV Output

本目录存放阶段七“全量规则生成”数据集的 CSV 产物。

当前规则约束：

- 所有成员都有生年
- 已死亡成员必须有卒年
- 2026 年存活成员年龄不大于 110
- 90 岁以上仍存活成员保持极低比例
- 高辈分成员大部分已死亡
- 族谱人数、代数和关系规模满足阶段七课程要求

默认生成命令：

```bash
python scripts/stage7/generate_dataset.py
```

默认输出文件包括：

- `user_account.csv`
- `family_tree.csv`
- `tree_collaborator.csv`
- `member.csv`
- `parent_child.csv`
- `marriage.csv`
- `member_provenance.csv`
