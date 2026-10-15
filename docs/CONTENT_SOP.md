# Keller Sermons 内容生产规范 (SOP)

> **版本**: 2.1
> **更新日期**: 2026-10-15
> **目录示例**: `sermons/Entering_His_Rest/`（不代表内容已完成逐段核验）

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

**当前流程：人工准备并逐段对照完整英文源稿核验。**

`python3 scripts/translate_sermons.py` 是已禁用的旧入口。旧实现只翻译前 3,000 个字符，并读写仓库根目录的 `{name}.md`，不适用于当前 `sermons/{Sermon_Name}/` 结构。现在所有参数（包括 `--help`、`--file`、`--batch`）都会明确报错并以非零状态退出，不加载模型 SDK、不调用 API、不写文件。

不要把其他现存翻译脚本视为已经验证安全的替代入口。使用任何模型辅助翻译前，需要单独验证完整输入覆盖、输出截断检测和失败时不覆盖已有译文；本规范不为这些脚本背书。

1. 保留完整 `transcript.md`，以其作为唯一翻译对照源。
2. 在临时草稿中翻译全部内容，逐段记录原文与译文对应关系，包括开头、结尾、经文、引文和列表。
3. 如需分批翻译，按明确的原文边界记录每批覆盖范围，检查无遗漏、无重复、无截断；不得以字符截取替代完整翻译。
4. 人工核验通过后，再保存为 `sermons/{Sermon_Name}/translation.md`；替换已有译文前保留可恢复版本。

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
python3 scripts/cuv_bible_query.py --bible bibles/CUNPS.json --book 希伯来书 --chapter 4 --verse 1

# 整章
python3 scripts/cuv_bible_query.py --bible bibles/CUNPS.json --book 希伯来书 --chapter 4
```

**数据源**: `bibles/CUNPS.json`。必须显式传入 `--bible`；查询脚本的旧默认路径不是当前数据目录。查询结果仍需核对书卷、章、节。

**标准格式**：
```markdown
> "所以，我们既蒙留下有进入他安息的应许，就当畏惧，免得我们中间或有人似乎是赶不上了。"
> ——希伯来书 4:1
```

### Step 5: 添加内容型标题

可为 **translation.md 和 transcript.md** 添加经人工核对的 `###` 章节标题。当前合并器完整保留两份文件，不依靠标题数量判断对齐；不要为满足机器计数而随意切分正文。

**translation.md** — 中文内容型标题：

| 类型 | ❌ 通用标题 | ✅ 内容型标题 |
|------|-----------|-------------|
| 问题型 | `### 第一部分` | `### 你知道怎样躺下并睡着吗？` |
| 概念型 | `### 核心信息` | `### 安息日的安息：灵魂的深度睡眠` |
| 行动型 | `### 应用` | `### 安息的检验：你能坐着听批评吗？` |

**transcript.md** — 对应的英文标题：

| translation.md | transcript.md |
|---------------|---------------|
| `### 引言：你知道怎样躺下并睡着吗？` | `### Introduction` |
| `### 安息日的安息：灵魂的深度睡眠` | `### Sabbath Rest: The REM of the Soul` |
| `### 安息的检验：你能坐着听批评吗？` | `### The Test of Rest` |

**要求**：
- 若采用分节对齐，两个文件的 `###` 标题数量与顺序必须一致，并人工确认每一节确实对应；数量一致本身不能证明语义对齐
- 中文标题反映核心内容，≤ 15 字
- 英文标题简洁描述性
- 只加标题，不改动正文内容

### Step 6: 合并为双语全文（未逐段对齐）

**工具**：
```bash
python3 scripts/generate_combined.py Sermon_Name
```

脚本读取 `sermons/{Sermon_Name}/transcript.md` 和 `translation.md`，生成 `combined/{Sermon_Name}.md`。合并只处理展示结构，不能验证译文忠实度或修复此前已经缺失的源稿。

先生成单篇并检查差异，再考虑批量处理。已有发布文件默认跳过；只有确认要替换并保留可恢复版本后才使用 `--overwrite`。禁止以字符数或段落比例猜测中英对应关系。

**输出**: `combined/{Sermon_Name}.md`

**生成的格式**（方括号表示完整源文件内容，不是摘要）：
```markdown
# 中文标题 / English Title

本文件保留英文原文与中文译文的完整内容，尚未逐段对齐。 / Full source texts are preserved below; paragraph alignment has not been verified.

---

## 英文原文 / English source

[transcript.md 完整原文，包括标题、引言、分隔线和原有署名]

---

## 中文译文 / Chinese source

[translation.md 完整原文，包括标题、经文、分隔线和原有署名]
```

**合并规则**：
- 先完整英文文件，再完整中文文件；源文本原样保留。
- 明确标注“尚未逐段对齐”，不按标题数量或长度推测对应关系。
- 不添加新的译者署名；源文件已有署名原样保留。
- 若需逐段交替的发布版，必须另行人工核验对应关系，当前生成命令不提供此功能。
- `--all` 可批量处理；发生错误时返回非零退出状态，不能仅以有文件生成判断全部成功。

---

## 四、文件格式规范

### translation.md（结构示例）

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

[如需署名，仅填写真实、已确认的译者与整理者]
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
- [ ] 分节发布时，英文与中文的 `###` 标题数量、顺序及实际内容对应均已核验
- [ ] `combined/{Sermon_Name}.md` 已生成，格式正确
- [ ] 合并保留两份源稿的全部正文、开头引言、经文、引文、列表及结尾；无静默丢弃、重复或猜测对齐
- [ ] 检查命令退出状态及输出差异，确认源文件未被修改

### 内容完整性验证

逐段对照原文与译文，再逐段核对合并输出。字节数、文件大小或字符数阈值只能提示异常，不能证明内容完整，也不能用于验证跨语言翻译是否忠实。标题和元数据可改变展示，但正文不得丢失。

结构回归测试（不访问网络、不调用模型）：
```bash
python3 -m unittest discover -s tests -v
```

**严禁**：
- LLM 自动聚合段落（已验证导致 68% 内容丢失）
- 任何形式的总结、改写、缩减
- 使用 `smart_beautifier.py`（已知问题工具）

---

## 六、工具速查

### 当前流程使用的入口

| 工具 | 用途 | 注意事项 |
|------|------|----------|
| `generate_combined.py` | 生成中英对照发布文件 | 仅负责合并；仍需人工检查内容和对应关系 |
| `cuv_bible_query.py` | 查询经文 | 显式指定 `--bible bibles/CUNPS.json`，核对书卷章节 |

### 禁用或未验证工具

| 工具 | 状态 |
|------|------|
| `translate_sermons.py` | 已禁用：旧实现截断至前 3,000 字符且使用根目录 Markdown |
| 其他翻译、段落合并、自动格式化及规范化脚本 | 未在本次修复中验证，不得称为安全替代工具；使用前逐项审查并备份 |
| `smart_beautifier.py`、LLM 段落聚合 | 不用于生产流程：存在总结、改写或丢失正文的风险 |

---

## 七、完整示例

**目录与标题示例**: `Entering_His_Rest`（示例不证明源稿完整或译文正确）

```
sermons/Entering_His_Rest/
├── metadata.json          → {"title": "Entering His Rest", "speaker": "Tim Keller"}
├── transcript.md          → 英文原文
└── translation.md         → 中文翻译

combined/Entering_His_Rest.md → 中英对照发布版
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
□ 4. 人工准备完整译文并逐段对照源稿核验 → translation.md
□ 5. 查询并替换经文为 CUV 和合本
□ 6. 如需章节标题，按真实内容边界添加并人工核对，不改写正文
□ 7. python3 scripts/generate_combined.py Sermon_Name
□ 8. 运行回归测试，并检查逐段完整性、对应关系及生成差异
□ 9. 经审阅后，按当前授权决定是否提交及推送
```

---

*文档维护：小雷 ⚡*
