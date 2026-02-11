# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Tim Keller Sermons Collection** - A bilingual (English/Chinese) repository of Tim Keller's sermons with automated translation and formatting workflows.

### Repository Structure

```
keller-sermons/
├── *.md                           # 77+ formatted sermon files (main content)
├── scripts/                       # Python automation tools
├── config/                        # Configuration (translation.json)
├── bibles_downloads/              # Local Bible data for verse lookups
├── transcripts/                   # Raw English transcripts (if available)
└── _chunks/                       # Temporary working directories for large translations
```

## Common Development Tasks

### Installation & Setup

```bash
# Install Python dependencies (first time only)
pip3 install -r scripts/requirements.txt

# Ensure Ollama is running (for local translations)
brew services start ollama

# Verify installations
python3 -c "import anthropic, openai, requests; print('✓ All OK')"
```

### Translation Workflow

The primary workflow involves translating sermon English transcripts to Chinese using either local Ollama or Claude API.

```bash
# Translate a single sermon
python3 scripts/translate_sermons.py --file "Sermon_Name"

# Translate all sermons in batch
python3 scripts/translate_sermons.py --batch

# Force a specific backend
python3 scripts/translate_sermons.py --file "Sermon_Name" --backend ollama
python3 scripts/translate_sermons.py --file "Sermon_Name" --backend claude

# Show available options
python3 scripts/translate_sermons.py --help
```

**Note:** The script automatically selects Ollama if available (faster, free), otherwise falls back to Claude API. Backend priority is configured in `config/translation.json`.

### Bible Verse Lookups

Query the internal Bible database (和合本 Chinese Union Version) for sermon formatting:

```bash
# Query a single verse
python3 scripts/cuv_bible_query.py --book 马太福音 --chapter 5 --verse 3

# Query a whole chapter
python3 scripts/cuv_bible_query.py --book 以弗所书 --chapter 4

# Example books: 创世记, 马太福音, 罗马书, 启示录, etc.
```

### Formatting & Restructuring

Sermons follow a standardized three-part format:

1. **Sermon Outline** - Bilingual outline
2. **English Transcript** - Full English text
3. **Chinese Translation** - Full Chinese text

```bash
# Auto-format a sermon file
python3 scripts/sermon_auto_formatter.py --file "Sermon_Name"

# Batch process multiple sermons
python3 scripts/sermon_auto_formatter.py --batch --output output.md
```

For detailed formatting guidelines, see `SERMON_FORMATTING_WORKFLOW.md`.

### Progress Tracking

Translation progress is tracked in `.translation_progress.json`. The file contains:
- `completed`: Sermons with full translations
- `failed`: Sermons attempted but incomplete

## Architecture & Design Patterns

### Translation System

- **Multi-Backend Architecture**: Supports local Ollama (preferred) and Claude API (fallback)
- **Configuration**: Backend settings and translation parameters in `config/translation.json`
- **Chunking Strategy**: Large texts split into ~2200-char chunks for efficient processing
- **Formatting Preservation**: Markdown structure and Bible book names in English are preserved during translation

### Sermon File Format

Standard sermon structure with bilingual headers:

```markdown
# [Sermon Title]

## Sermon Outline / 讲道大纲
[Bilingual outline here]

---

## English Transcript / 英文原文
[Full English transcript]

---

## Chinese Translation / 中文翻译
[Full Chinese translation]
```

### Helper Scripts

- **translate_sermons.py** - Main translation orchestrator (Ollama + Claude fallback)
- **sermon_auto_formatter.py** - Standardizes sermon structure and formatting
- **cuv_bible_query.py** - Queries Chinese Union Version Bible data
- **keller_autopilot.py** - Idempotent helper for chunking and stitching large translations
- **improve_outlines.py** - Enhances sermon outlines
- **add_scriptures.py** - Inserts Bible verses into sermons

### Large Translation Handling

For long sermons, the `keller_autopilot.py` script breaks work into chunks:

```bash
# Check status of chunked translations
python3 scripts/keller_autopilot.py status

# Create chunks for the next sermon
python3 scripts/keller_autopilot.py chunk-next

# Stitch completed chunks back into sermon file
python3 scripts/keller_autopilot.py stitch-ready

# See full JSON plan of work
python3 scripts/keller_autopilot.py plan
```

## Git Workflow

Keep commits focused and descriptive:

```bash
# Typical commit for translated sermon
git add [sermon_name].md
git commit -m "chore: add Chinese translations for [Sermon Name]"

# Typical commit for multiple sermons
git commit -m "chore: add Chinese translations for series name (X/Y)"

# Format-only changes
git commit -m "chore: restructure [sermon_name] with improved formatting"
```

## Configuration

### Translation Backend Priority (`config/translation.json`)

Backends are tried in priority order (lower number = higher priority):

1. **Ollama** (priority 1) - Local model `qwen2.5:7b-instruct-q8_0`, free, faster
2. **Claude** (priority 2) - Anthropic API, requires `ANTHROPIC_API_KEY` env var

**Translation Settings:**
- `chunk_size`: 2200 characters (optimal for Qwen 2.5)
- `max_output_tokens`: 4000
- `temperature`: 0.3 (consistency)
- `preserve_formatting`: true (keeps markdown intact)

## Key Files & Their Purpose

| File | Purpose |
|------|---------|
| `README.md` | Project overview and sermon index |
| `SERMON_FORMATTING_WORKFLOW.md` | Detailed formatting guidelines and examples |
| `QUICK_START.md` | Fast setup and troubleshooting |
| `config/translation.json` | Backend configuration and translation settings |
| `scripts/requirements.txt` | Python dependencies (anthropic, openai, requests) |
| `.translation_progress.json` | Tracks which sermons are completed/failed |

## Dependencies

- **Python 3.7+**
- **anthropic** (>=0.18.0) - Claude API client
- **openai** (>=1.0.0) - Ollama/OpenAI-compatible endpoint client
- **requests** - HTTP library for Ollama health checks

Optional: **Ollama** (local inference) with `qwen2.5:7b-instruct-q8_0` model

## Notes for Future Work

1. **Chunking Workflow**: Use `keller_autopilot.py` for sermons over ~15KB to avoid API timeouts
2. **Formatting First**: Always format/structure sermons before translating for consistency
3. **Bible Verses**: Use `cuv_bible_query.py` to insert accurate Chinese Bible citations
4. **Testing Translations**: Spot-check output for theological terminology consistency
5. **Progress Tracking**: `.translation_progress.json` helps avoid duplicate work
