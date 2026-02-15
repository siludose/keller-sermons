# Keller Sermons 内容生产规范 (SOP)

> **版本**: 2.0
> **更新日期**: 2026-02-15
> **标准案例**: `sermons/Entering_His_Rest/`

本文档是项目的**唯一权威标准**。所有新内容按此流程生产。

---

## 一、目录结构

```
keller-sermons/
├── sermons/{Sermon_Name}/        # 源文件（每篇讲道一个文件夹）
│   ├── metadata.json             # 元数据（必须）
│   ├── transcript.md             # 英文原文（必须）
│   ├── translation.md            # 中文翻译（必须）
│   └── outline.md                # 大纲（可选）
│
├── combined/{Sermon_Name}.md     # 发布文件：中英对照（必须）
│
├── bibles/CUNPS.json             # 和合本圣经数据库
├── scripts/                      # 处理脚本
├── docs/                         # 项目文档
├── config/                       # 配置文件
└── archive/                      # 归档旧文件
```

---

## 二、命名规范

| 项目 | 规则 | 示例 |
|------|------|------|
| 文件夹名 | 英文标题，首字母大写，下划线分隔 | `Entering_His_Rest` |
| 空格 | → `_` | `The_Glory_of_the_Incarnation` |
| 撇号 `'` | 移除 | `Jesus_Model_of_Spirituality` |
| 冒号 `:` | 移除 | `Wisdom_How_To_Get_It` |
| 问号 `?` | 移除 | `Why_Tell_Stories` |
| 括号 `()` | → `_` | `Anatomy_of_Sin_Part_1` |
| `&` | → `and` | `Work_and_Rest` |

---

## 三、生产流程（6 步）

```
获取转录 → 建立目录 → 翻译 → 经文替换 → 添加标题 → 合并发布
   1          2        3        4          5          6
```

### Step 1: 获取英文转录

**来源**（优先级排序）：
1. Gospel in Life 播客音频 → Whisper 转录
2. YouTube 字幕 → `youtube-transcript-api`
3. 已有文字稿

**输出**: 纯英文文本，保留完整内容

### Step 2: 建立目录结构

创建文件夹和初始文件：

```bash
mkdir -p sermons/Sermon_Name
```

**metadata.json**（当前标准格式）：
```json
{
  "title": "Entering His Rest",
  "speaker": "Tim Keller"
}
```

**transcript.md**：
```markdown
# Entering His Rest

## English Transcript

[完整英文内容...]
```

### Step 3: 中文翻译

**工具选择**（按优先级）：
```bash
# 方式 1：使用项目翻译脚本（自动选择后端）
python3 scripts/translate_sermons.py --file "Sermon_Name"

# 方式 2：强制使用 Claude（质量最高）
python3 scripts/translate_sermons.py --file "Sermon_Name" --backend claude

# 方式 3：强制使用 Ollama（本地免费）
python3 scripts/translate_sermons.py --file "Sermon_Name" --backend ollama
```

**翻译要求**：
- 100% 内容保留，不删减、不总结、不改写
- 保留原文结构和段落划分
- 神学术语使用中文基督教通用译法

**输出**: `sermons/{Sermon_Name}/translation.md`

### Step 4: 经文替换（CUV 和合本）

将 AI 翻译的圣经经文替换为**和合本 (CUV)** 原文。

**查询工具**：
```bash
# 单节经文
python3 scripts/cuv_bible_query.py --book 希伯来书 --chapter 4 --verse 1

# 整章
python3 scripts/cuv_bible_query.py --book 希伯来书 --chapter 4
```

**数据源**: `bibles/CUNPS.json`

**标准格式**：
```markdown
> "所以，我们既蒙留下有进入他安息的应许，就当畏惧，免得我们中间或有人似乎是赶不上了。"
> ——希伯来书 4:1
```

### Step 5: 添加内容型标题

将通用标题改为**基于内容的描述性标题**：

| 类型 | ❌ 通用标题 | ✅ 内容型标题 |
|------|-----------|-------------|
| 问题型 | `### 第一部分` | `### 你知道怎样躺下并睡着吗？` |
| 概念型 | `### 核心信息` | `### 安息日的安息：灵魂的深度睡眠` |
| 行动型 | `### 应用` | `### 安息的检验：你能坐着听批评吗？` |

**要求**：
- 标题直接反映该段落的核心内容
- 中文标题 ≤ 15 字
- 只加标题，不改动正文内容

### Step 6: 合并为中英对照

**输出**: `combined/{Sermon_Name}.md`

**格式模板**：
```markdown
# 中文标题 / English Title

**讲员**: 提摩太·凯勒 (Tim Keller)
**经文**: 书卷名 章:节 / Book Chapter:Verse
**系列**: 系列名 / Series Name

---

## 核心经文 / Key Scripture

> **Hebrews 4:1-12:**
> "English scripture text..."

---

> **希伯来书 4:1-12：**
> "中文和合本经文..."

---

## 小标题 / Section Title

English paragraph...

---

中文段落...

---

*翻译整理：小雷 ⚡*
```

**合并规则**：
- 每个 section：先英文 → `---` → 中文
- section 之间用 `---` 分隔
- 标题双语：`## 中文标题 / English Title`

---

## 四、文件格式规范

### translation.md（标准案例见 `Entering_His_Rest`）

```markdown
# 中文标题
## English Title

**讲员**: 提摩太·凯勒 (Tim Keller)
**经文**: 书卷名 章:节
**系列**: 系列名

---

## 核心经文

> "和合本经文内容"
> ——书卷名 章:节

---

### 内容型标题一

段落内容...

---

### 内容型标题二

段落内容...

---

*翻译整理：小雷 ⚡*
```

### transcript.md

```markdown
# English Title

## English Transcript

Full English content...
```

### metadata.json

```json
{
  "title": "Entering His Rest",
  "speaker": "Tim Keller"
}
```

### outline.md（可选）

```markdown
# Sermon Title

## Sermon Outline / 讲道大纲

1. Introduction / 引言
2. Point One / 要点一
3. Point Two / 要点二
...
```

---

## 五、质量检查清单

### 必须通过 ✅

- [ ] 文件夹命名符合规范（英文、下划线、首字母大写）
- [ ] `metadata.json` 存在且格式正确
- [ ] `transcript.md` 英文原文完整无删减
- [ ] `translation.md` 中文翻译完整无删减
- [ ] 圣经经文已替换为 CUV 和合本
- [ ] 经文格式正确：`> "..." \n> ——书卷名 章:节`
- [ ] 标题为内容型（非通用型如"第一部分"）
- [ ] `combined/{Sermon_Name}.md` 已生成，格式正确
- [ ] combined 文件大小 ≥ transcript + translation

### 内容完整性验证

```
处理后长度变化必须在 ±2% 以内（仅允许格式变化）
```

**严禁**：
- LLM 自动聚合段落（已验证导致 68% 内容丢失）
- 任何形式的总结、改写、缩减
- 使用 `smart_beautifier.py`（已知问题工具）

---

## 六、工具速查

### 安全工具 ✅

| 工具 | 用途 | 命令 |
|------|------|------|
| `translate_sermons.py` | 翻译 | `python3 scripts/translate_sermons.py --file Name` |
| `cuv_bible_query.py` | 查经文 | `python3 scripts/cuv_bible_query.py --book 书卷 --chapter N --verse N` |
| `safe_paragraph_merger.py` | 段落合并 | `python3 scripts/safe_paragraph_merger.py --file Name` |
| `file_normalizer.py` | 文件名规范化 | `python3 scripts/file_normalizer.py` |

### 危险工具 ❌ 禁用

| 工具 | 问题 |
|------|------|
| `smart_beautifier.py` | 68% 内容丢失 |
| LLM 段落聚合 | 自动总结导致内容丢失 |

---

## 七、完整示例

**标准案例**: `Entering_His_Rest`

```
sermons/Entering_His_Rest/
├── metadata.json          → {"title": "Entering His Rest", "speaker": "Tim Keller"}
├── transcript.md          → 英文原文 (~5KB)
└── translation.md         → 中文翻译，7个内容型标题 (~5.5KB)

combined/Entering_His_Rest.md → 中英对照发布版 (~9.5KB)
```

**translation.md 标题示例**：
```
### 引言：你知道怎样躺下并睡着吗？
### 安息：圣经中最重要的主题之一
### 安息日的安息：灵魂的深度睡眠
### 卡夫卡的《审判》：我们内心的焦虑
### 罗马书 2 章：那台看不见的录音机
### 如何进入安息？福音的两部分
### 安息的检验：你能坐着听批评吗？
```

---

## 八、新讲道生产 Checklist

收到一篇新讲道后，按顺序执行：

```
□ 1. 获取英文转录文本
□ 2. 创建 sermons/Sermon_Name/ 目录
□ 3. 写入 metadata.json + transcript.md
□ 4. 执行翻译 → translation.md
□ 5. 查询并替换经文为 CUV 和合本
□ 6. 为 translation.md 添加内容型标题
□ 7. 合并生成 combined/Sermon_Name.md
□ 8. 运行质量检查（文件大小、格式）
□ 9. git add + commit + push
```

---

*文档维护：小雷 ⚡*
