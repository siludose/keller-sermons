# 备份信息

## 备份总览

**备份时间**：2026-02-11
**备份类型**：讲道文件生产备份
**备份位置**：`/backup/` 目录

## 备份统计

| 项目 | 数值 |
|------|------|
| 备份文件数量 | 105 个 .md 文件 |
| 备份总大小 | 4.2 MB |
| 原文件位置 | `/` （根目录） |
| 备份文件位置 | `/backup/` |

## 备份内容

所有讲道的 Markdown 文件，包括：

- ✅ 英文讲道内容
- ✅ 中文翻译
- ✅ Markdown 格式
- ✅ 圣经经文引用

### 文件列表示例

```
A_Covenant_Relationship.md
A_New_Heart.md
Admitting.md
Aggressive_Compassion.md
Anatomy_of_Sin_(Part_1).md
Anatomy_of_Sin_(Part_2).md
BIBLE_QUERY.md
Born_Again.md
... （共 105 个）
```

## 备份状态

| 检查项 | 状态 |
|--------|------|
| 文件夹创建 | ✅ 完成 |
| 文件复制 | ✅ 完成（105 个） |
| 数据完整性 | ✅ 完整 |
| 原文件保留 | ✅ 是 |

## 恢复方法

### 方法 1：查看备份文件
```bash
# 查看备份的讲道文件
ls -lh backup/

# 查看特定讲道备份
cat backup/Admitting.md
```

### 方法 2：恢复单个文件
```bash
# 如果原文件被意外修改或删除，可以从备份恢复
cp backup/Sermon_Name.md ./Sermon_Name.md
```

### 方法 3：批量恢复
```bash
# 如果需要恢复所有文件
cp backup/*.md ./
```

## 文件验证

### 原文件 vs 备份文件

两个位置的文件内容完全相同，可通过以下方式验证：

```bash
# 比较文件内容
diff Admitting.md backup/Admitting.md
# 如果没有输出，说明文件相同

# 或使用 MD5 校验
md5sum *.md > /tmp/original_md5.txt
md5sum backup/*.md > /tmp/backup_md5.txt
diff /tmp/original_md5.txt /tmp/backup_md5.txt
```

## 备份注意事项

1. **独立备份**
   - 备份文件与原文件完全独立
   - 修改原文件不会影响备份
   - 修改备份文件不会影响原文件

2. **自动更新**
   - 当前备份是静态快照
   - 原文件的后续修改不会自动同步到备份
   - 如需更新备份，需要手动重新复制

3. **文件安全**
   - 原文件和备份文件都已保存
   - 可以安全地进行修改和实验
   - 遇到问题可从备份恢复

## 未来维护

### 定期备份
```bash
# 创建带时间戳的备份
cp -r backup backup_2026-02-11
```

### 增量备份
```bash
# 只备份修改的文件
rsync -av --delete . backup/
```

## 相关文档

- [README.md](README.md) - 项目总体说明
- [QUICK_START.md](QUICK_START.md) - 快速开始指南
- [OLLAMA_INTEGRATION_GUIDE.md](OLLAMA_INTEGRATION_GUIDE.md) - Ollama 集成指南

## 联系和支持

如有备份相关问题，请参考：

1. 检查文件是否存在：`ls -la backup/`
2. 验证文件大小：`du -sh backup/`
3. 对比原文件：`diff Sermon_Name.md backup/Sermon_Name.md`

---

**备份文件夹创建时间**：2026-02-11
**备份类型**：讲道生产文件快照
**状态**：✅ 完成
