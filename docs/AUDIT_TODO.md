# 存量内容审计 & 修复 TODO

> **审计日期**: 2026-02-15
> **审计基准**: `docs/CONTENT_SOP.md` v2.0

---

## 审计结果总览

| 检查项 | 合规 | 不合规 | 优先级 |
|--------|------|--------|--------|
| metadata.json 格式 | 97/97 (100%) | 0 | ✅ 无需修复 |
| transcript.md 有英文内容 | 91/97 | **6 空文件** | P0 |
| transcript.md 有 ### 标题 | 2/97 | **95 缺失** | P2 |
| translation.md 有 ### 内容型标题 | 97/98 | 1 损坏 | ✅ 基本通过 |
| translation.md 新格式（头部+元数据+页脚） | 2/98 | **96 旧格式** | P1 |
| combined/ 文件存在 | 97/97 | 0 | ✅ 全部存在 |

---

## P0: 6 篇缺少英文原文的 transcript.md

这 6 个文件只有中文大纲，没有英文转录内容。需要获取音频并转录。

| 讲道 | 文件大小 | 状态 |
|------|----------|------|
| Admitting | 341 bytes | ❌ 只有中文大纲 |
| The_Glory_of_the_Incarnation | 156 bytes | ❌ 只有中文大纲 |
| Radical_Generosity | 174 bytes | ❌ 只有中文大纲 |
| Seeking_the_Kingdom | 183 bytes | ❌ 只有中文大纲 |
| Thy_Will_Be_Done | 244 bytes | ❌ 只有中文大纲 |
| The_Power_of_the_Incarnation | 264 bytes | ❌ 只有中文大纲 |

**已确认**: `archive/backup/` 里有这 6 个文件，但也只有中文内容，从未有过英文原文。

**修复方案**: 拉音频 + Whisper 本地转录
- ✅ `whisper` CLI 已安装 (`faster-whisper 1.2.1`)
- ✅ `apple_podcasts_downloader.py` 已有（Gospel in Life RSS feed）
- ❌ `feedparser` 未安装 → `pip3 install feedparser`
- ⚠️ RSS feed 可能不包含老讲道，需手动找音频源

**流程**:
```bash
pip3 install feedparser
python3 scripts/apple_podcasts_downloader.py --list-episodes --limit 100
# 找到对应讲道 → 下载
whisper audio.mp3 --language en --output_format txt
```

**附加问题**: `Thy_Will_Be_Done/translation.md` 也疑似损坏（仅 925 bytes）

---

## P1: 96 篇 translation.md 旧格式

96/98 个文件仍使用旧格式 `## Chinese Translation / 中文翻译`，缺少：
- `# 中文标题` + `## English Title` 头部
- `**讲员**`、`**经文**`、`**系列**` 元数据行
- `## 核心经文` 段落
- `*翻译整理：小雷 ⚡*` 页脚

**已合规的 2 个文件**:
- `Entering_His_Rest` (标准案例)
- `The_Glory_of_the_Incarnation`

**修复方案**: 写迁移脚本，批量添加页脚 + 规范化头部格式。
注意：经文/系列元数据在 metadata.json 中不存在，需要逐篇补充或跳过。

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
