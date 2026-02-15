# Keller Sermons 内容生产规范 (SOP)

> **版本**: 1.0  
> **更新日期**: 2026-02-15  
> **标准案例**: `Entering_His_Rest`

---

## 一、目录结构

```
keller-sermons/
├── sermons/{Sermon_Name}/      # 源文件（分离存储）
│   ├── metadata.json           # 元数据
│   ├── transcript.md           # 英文原文
│   └── translation.md          # 中文翻译（带内容型标题）
│
├── combined/{Sermon_Name}.md   # 发布文件（中英对照）
│
├── bibles/                     # 圣经引用数据 (CUV)
├── scripts/                    # 处理脚本
├── docs/                       # 项目文档
└── archive/                    # 归档旧文件
```

---

## 二、内容生产流程

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  1. 获取    │ ──▶ │  2. 翻译    │ ──▶ │  3. 经文    │ ──▶ │  4. 美化    │ ──▶ │  5. 合并    │
│  英文转录   │     │  中文翻译   │     │  替换CUV    │     │  添加标题   │     │  中英对照   │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

### Step 1: 获取英文转录

- **来源**: Gospel in Life 播客、YouTube、音频转录
- **工具**: Whisper、youtube-transcript-api
- **输出**: `sermons/{Sermon_Name}/transcript.md`

### Step 2: 中文翻译

- **工具**: GPT-4、Claude、或其他翻译模型
- **要求**: 保留原文结构，不删减内容
- **输出**: `sermons/{Sermon_Name}/translation.md`

### Step 3: 经文替换 (CUV)

将 AI 翻译的经文替换为**和合本 (CUV)** 原文：

| 替换前 | 替换后 |
|-------|--------|
| AI 翻译的经文 | 和合本 CUV 原文 |
| 经文出处不规范 | `> "经文内容"\n> ——书卷名 章:节` |

**数据源**: `bibles/CUS/` 目录

**标准格式**:
```markdown
> "所以，我们既蒙留下有进入他安息的应许，就当畏惧，免得我们中间或有人似乎是赶不上了。"
> ——希伯来书 4:1
```

### Step 4: 添加内容型标题

将通用标题改为内容型标题：

| ❌ 通用标题 | ✅ 内容型标题 |
|-----------|-------------|
| `### 第一部分` | `### 你知道怎样躺下并睡着吗？` |
| `### 核心信息` | `### 安息日的安息：灵魂的深度睡眠` |
| `### 应用` | `### 安息的检验：你能坐着听批评吗？` |

**标题类型**:
- **问题型**: `### 为什么最好的人也必须重生？`
- **概念型**: `### 有机成长与新身份：重生意味着什么？`
- **行动型**: `### 空手而来：如何重生？`

### Step 5: 合并为中英对照

**输出**: `combined/{Sermon_Name}.md`

**格式**:
```markdown
# 中文标题 / English Title

**讲员**: 提摩太·凯勒 (Tim Keller)  
**经文**: 书卷名 章:节 / Book Chapter:Verse

---

## 小标题 / Section Title

English paragraph...

---

中文段落...

---
```

---

## 三、文件格式规范

### metadata.json

```json
{
  "title": "Entering His Rest",
  "title_zh": "进入他的安息",
  "speaker": "Tim Keller",
  "date": "2016",
  "scripture": "Hebrews 4:1-12",
  "scripture_zh": "希伯来书 4:1-12",
  "series": "Ten Commandments",
  "series_zh": "十诫系列"
}
```

### translation.md 结构

```markdown
# 中文标题
## English Title

**讲员**: 提摩太·凯勒 (Tim Keller)  
**经文**: 书卷名 章:节  
**系列**: 系列名

---

## 核心经文

> "经文内容"
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

### combined/ 格式

```markdown
# 中文标题 / English Title

## 小标题 / Section Title

English paragraph...

---

中文段落...
```

---

## 四、命名规范

| 项目 | 规范 | 示例 |
|-----|------|------|
| 文件夹名 | 英文标题，下划线分隔 | `Entering_His_Rest` |
| 空格 | 用下划线 `_` | `The_Glory_of_the_Incarnation` |
| 括号 | 用下划线替代 | `Anatomy_of_Sin_Part_1` |
| 大小写 | 首字母大写 | `Why_Tell_Stories` |
| 特殊字符 | 移除 `'`、`:`、`?` 等 | `Wisdom_How_To_Get_It` |

---

## 五、质量检查清单

- [ ] `metadata.json` 完整（title, speaker, scripture）
- [ ] `transcript.md` 英文原文无删减
- [ ] `translation.md` 中文翻译无删减
- [ ] 经文已替换为 CUV 原文
- [ ] 经文格式规范 (`> "..." \n > ——书卷名`)
- [ ] 标题为内容型（非通用型）
- [ ] `combined/` 文件格式正确（中英对照）
- [ ] 字节数验证：`combined/` ≥ `transcript.md` + `translation.md`
- [ ] Git commit + push

---

## 六、标准案例

**参考文件**: `Entering_His_Rest`

```
sermons/Entering_His_Rest/
├── metadata.json
├── transcript.md
└── translation.md

combined/Entering_His_Rest.md
```

查看这些文件了解正确的格式和结构。

---

*文档维护：小雷 ⚡*
