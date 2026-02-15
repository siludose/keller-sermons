# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Project Overview

**Tim Keller Sermons Collection** - A bilingual (English/Chinese) repository of 97 Tim Keller sermons with automated translation and formatting workflows.

## Repository Structure

```
keller-sermons/
├── sermons/{Sermon_Name}/        # Source files (one folder per sermon)
│   ├── metadata.json             # {"title": "...", "speaker": "Tim Keller"}
│   ├── transcript.md             # English transcript
│   ├── translation.md            # Chinese translation (with content-based titles)
│   └── outline.md                # Bilingual outline (optional)
├── combined/{Sermon_Name}.md     # Published bilingual files (EN/ZH interleaved)
├── bibles/CUNPS.json             # Chinese Union Version Bible database
├── scripts/                      # Python automation tools
├── config/translation.json       # Translation backend config
├── docs/                         # Documentation
│   └── CONTENT_SOP.md            # ← THE authoritative production standard
└── archive/                      # Archived legacy files
```

## Production Standard

**All new content follows `docs/CONTENT_SOP.md`**. Standard case: `sermons/Entering_His_Rest/`.

### 6-Step Pipeline

```
获取转录 → 建立目录 → 翻译 → 经文替换(CUV) → 添加内容型标题 → 合并发布
```

### Critical Rules

1. **100% content preservation** - Never summarize, abbreviate, or reduce content
2. **CUV Bible verses** - Always replace AI-translated scripture with 和合本 (CUV) from `bibles/CUNPS.json`
3. **Content-based titles** - Use descriptive titles like `### 安息的检验：你能坐着听批评吗？` not generic ones like `### 第一部分`
4. **Do NOT use `smart_beautifier.py`** - Known to cause 68% content loss

## Common Commands

```bash
# Translate a sermon
python3 scripts/translate_sermons.py --file "Sermon_Name"

# Query CUV Bible verse
python3 scripts/cuv_bible_query.py --book 希伯来书 --chapter 4 --verse 1

# Merge transcript + translation → combined bilingual file
python3 scripts/generate_combined.py Sermon_Name

# Safe paragraph merge (verified ±2% content preservation)
python3 scripts/safe_paragraph_merger.py --file "Sermon_Name"
```

## File Naming Convention

- English title, Title_Case, underscores: `Entering_His_Rest`
- Remove `'`, `:`, `?`; replace `()` with `_`; replace `&` with `and`

## Translation Backend

Priority order (configured in `config/translation.json`):
1. **Ollama** - Local model `qwen2.5:7b-instruct-q8_0`, free
2. **Claude** - Anthropic API fallback, requires `ANTHROPIC_API_KEY`

## Git Commit Style

```bash
# Chinese commit messages preferred
git commit -m "feat: 为 X 篇讲道添加中文翻译"
git commit -m "fix: 修复经文格式"
git commit -m "chore: 整理仓库结构"
```
