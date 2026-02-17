# 存量内容审计 & 修复 TODO

> **审计日期**: 2026-02-15
> **审计基准**: `docs/CONTENT_SOP.md` v2.0

---

## 审计结果总览

| 检查项 | 合规 | 不合规 | 优先级 |
|--------|------|--------|--------|
| metadata.json 格式 | 97/97 (100%) | 0 | ✅ 无需修复 |
| transcript.md 有英文内容 | 97/97 (100%) | 0 | ✅ 已修复 |
| transcript.md 有 ### 标题 | 2/97 | **95 缺失** | P2 |
| translation.md 有 ### 内容型标题 | 97/98 | 1 损坏 | ✅ 基本通过 |
| translation.md 新格式（头部+元数据+页脚） | 97/97 (100%) | 0 | ✅ 已修复 |
| combined/ 文件存在 | 97/97 | 0 | ✅ 全部存在 |

---

## ~~P0: 6 篇缺少英文原文的 transcript.md~~ ✅ 已修复 (2026-02-16)

已通过 Whisper large-v3 本地转录完成，并全部翻译为中文。

| 讲道 | transcript.md | translation.md | 状态 |
|------|----------|----------|------|
| Admitting | 273 行 | 390 行 | ✅ 完成 |
| The_Glory_of_the_Incarnation | 187 行 | 243 行 | ✅ 完成 |
| Radical_Generosity | 269 行 | 333 行 | ✅ 完成 |
| Seeking_the_Kingdom | 229 行 | 267 行 | ✅ 完成 |
| Thy_Will_Be_Done | 301 行 | 353 行 | ✅ 完成 |
| The_Power_of_the_Incarnation | 269 行 | 301 行 | ✅ 完成 |

**工具链**: `apple_podcasts_downloader.py` → `transcribe_whisper.py` → `clean_transcripts.py` → Claude 翻译

---

## ~~P1: 96 篇 translation.md 旧格式~~ ✅ 已修复 (2026-02-17)

已通过 `migrate_translation_format.py` 批量迁移 90 个文件到新格式：
- ✅ `# 中文标题` + `## English Title` 头部（90 篇中文标题翻译）
- ✅ `**讲员**` 元数据行
- ✅ `*翻译整理：小雷 ⚡*` 页脚
- ⚠️ `**经文**`、`**系列**` 待逐篇补充（metadata.json 中无此数据）
- ⚠️ `## 核心经文` 段落待逐篇添加

已同步重新生成全部 97 个 combined/ 文件，均为 `# 中文标题 / English Title` 格式。

---

## P2: 95 篇 transcript.md 缺少 ### 标题

仅 2 个文件有 ### 章节标题（Born_Again, How_To_Pray），其余 95 个为纯文本。
SOP Step 5 要求 transcript.md 和 translation.md 都有对应的 ### 标题以便合并对齐。

**已合规的 2 个文件**:
- `Born_Again`
- `How_To_Pray`

**修复方案**: 需逐篇阅读内容理解讲道结构后手动添加，无法批量自动化。
建议：按需渐进式处理，优先处理重要讲道。

---

## 修复优先级

```
P0 → 获取 6 篇缺失的英文转录（拉音频 + Whisper 转录）
P1 → 批量迁移 96 篇 translation.md 到新格式
P2 → 逐篇为 transcript.md 添加 ### 标题（渐进式）
```

---

*审计人：小雷 ⚡*
