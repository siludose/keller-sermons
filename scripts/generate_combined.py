#!/usr/bin/env python3
"""
generate_combined.py - 合并 transcript.md + translation.md → combined/{name}.md

合并逻辑:
  - 如果 transcript.md 和 translation.md 都有 ### 标题且数量一致 → 按标题对齐
  - 如果只有 translation.md 有 ### 标题 → 按段落比例拆分英文
  - 如果都没有 ### 标题 → 双语分块输出

用法:
    python3 scripts/generate_combined.py Sermon_Name
    python3 scripts/generate_combined.py --all
    python3 scripts/generate_combined.py --all --overwrite
"""
import os
import re
import sys
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERMONS_DIR = os.path.join(BASE_DIR, "sermons")
COMBINED_DIR = os.path.join(BASE_DIR, "combined")

FOOTER = "*翻译整理：小雷 ⚡*"


def has_chinese(text):
    return bool(re.search(r'[\u4e00-\u9fff]', text))


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def strip_footer(text):
    """Remove translator footer line from content."""
    return re.sub(r'\*翻译整理[：:].*?\*\s*$', '', text).strip()


def split_into_sections(content):
    """Split markdown by ### headers. Returns [(header, body), ...]."""
    sections = []
    current_header = None
    current_lines = []

    for line in content.split("\n"):
        if line.startswith("### "):
            if current_header is not None:
                body = "\n".join(current_lines).strip()
                sections.append((current_header, strip_footer(body)))
            current_header = line[4:].strip()
            current_lines = []
        elif current_header is not None:
            if line.strip() == "---":
                continue
            current_lines.append(line)

    if current_header is not None:
        body = "\n".join(current_lines).strip()
        sections.append((current_header, strip_footer(body)))

    return sections


def extract_body_text(content):
    """Extract body text after ## header (for flat transcripts without ### sections)."""
    lines = content.split("\n")
    body_start = 0

    for i, line in enumerate(lines):
        if line.startswith("## "):
            body_start = i + 1
            break

    body_lines = [l for l in lines[body_start:] if l.strip() != "---"]
    return "\n".join(body_lines).strip()


def extract_metadata(translation_content, transcript_content, metadata_path):
    """Extract title_zh, title_en, speaker, scripture, series."""
    title_zh = ""
    title_en = ""
    speaker = ""
    scripture = ""
    series = ""

    for line in translation_content.split("\n"):
        # First # header
        if line.startswith("# ") and not title_zh and not title_en:
            candidate = line[2:].strip()
            if has_chinese(candidate):
                title_zh = candidate
            else:
                title_en = candidate
            continue

        # First ## header (skip special ones)
        if line.startswith("## ") and not line.startswith("### "):
            candidate = line[3:].strip()
            skip_keywords = ["Translation", "翻译", "核心经文", "Key Scripture"]
            if any(kw in candidate for kw in skip_keywords):
                continue
            if not title_en and not has_chinese(candidate):
                title_en = candidate
            elif not title_zh and has_chinese(candidate):
                title_zh = candidate
            continue

        # Metadata fields
        if "**讲员**" in line:
            speaker = re.sub(r".*\*\*讲员\*\*\s*[:：]\s*", "", line).strip()
        elif "**经文**" in line:
            scripture = re.sub(r".*\*\*经文\*\*\s*[:：]\s*", "", line).strip()
        elif "**系列**" in line:
            series = re.sub(r".*\*\*系列\*\*\s*[:：]\s*", "", line).strip()

    # Get English title from transcript
    for line in transcript_content.split("\n"):
        if line.startswith("# "):
            t_title = line[2:].strip()
            if not title_en:
                title_en = t_title
            break

    # Fallback: try metadata.json
    if (not title_zh or not title_en) and os.path.exists(metadata_path):
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                mdata = json.load(f)
            if not title_en and "title" in mdata and not has_chinese(mdata["title"]):
                title_en = mdata["title"]
            if not title_zh and "title_zh" in mdata:
                title_zh = mdata["title_zh"]
            if not title_zh and "title" in mdata and has_chinese(mdata["title"]):
                title_zh = mdata["title"]
        except Exception:
            pass

    # Final fallbacks
    if not title_zh:
        title_zh = title_en
    if not title_en:
        title_en = title_zh
    if not speaker:
        speaker = "提摩太·凯勒 (Tim Keller)"

    return {
        "title_zh": title_zh,
        "title_en": title_en,
        "speaker": speaker,
        "scripture": scripture,
        "series": series,
    }


def split_proportionally(text, target_sizes):
    """Split text into chunks proportional to target_sizes (by character count)."""
    paragraphs = [p.strip() for p in re.split(r"\n\n+", text) if p.strip()]

    if not paragraphs or not target_sizes:
        return [text] if text.strip() else [""]

    total_target = sum(target_sizes)
    if total_target == 0:
        return [text]

    result = []
    para_idx = 0

    for i, size in enumerate(target_sizes):
        if i == len(target_sizes) - 1:
            # Last section gets all remaining paragraphs
            chunk = paragraphs[para_idx:]
        else:
            proportion = size / total_target
            n_paras = max(1, round(proportion * len(paragraphs)))
            chunk = paragraphs[para_idx : para_idx + n_paras]
            para_idx += n_paras

        result.append("\n\n".join(chunk) if chunk else "")

    return result


def generate_combined(sermon_name, overwrite=False):
    """Generate combined/{sermon_name}.md from transcript + translation."""
    sermon_dir = os.path.join(SERMONS_DIR, sermon_name)
    translation_path = os.path.join(sermon_dir, "translation.md")
    transcript_path = os.path.join(sermon_dir, "transcript.md")
    metadata_path = os.path.join(sermon_dir, "metadata.json")
    output_path = os.path.join(COMBINED_DIR, f"{sermon_name}.md")

    if os.path.exists(output_path) and not overwrite:
        return "skip"

    if not os.path.exists(translation_path):
        print(f"  ⚠️  {sermon_name}: missing translation.md")
        return "error"
    if not os.path.exists(transcript_path):
        print(f"  ⚠️  {sermon_name}: missing transcript.md")
        return "error"

    translation_content = read_file(translation_path)
    transcript_content = read_file(transcript_path)

    meta = extract_metadata(translation_content, transcript_content, metadata_path)

    zh_sections = split_into_sections(translation_content)
    en_sections = split_into_sections(transcript_content)

    parts = []

    # ── Header ──
    parts.append(f"# {meta['title_zh']} / {meta['title_en']}")
    parts.append("")
    parts.append(f"**讲员**: {meta['speaker']}")
    if meta["scripture"]:
        parts.append(f"**经文**: {meta['scripture']}")
    if meta["series"]:
        parts.append(f"**系列**: {meta['series']}")
    parts.append("")
    parts.append("---")
    parts.append("")

    # ── Body ──
    mode = ""
    if zh_sections and en_sections and len(zh_sections) == len(en_sections):
        # Case 1: Both have matching ### sections → align
        mode = "aligned"
        for (en_h, en_body), (zh_h, zh_body) in zip(en_sections, zh_sections):
            parts.append(f"## {zh_h} / {en_h}")
            parts.append("")
            parts.append(en_body)
            parts.append("")
            parts.append("---")
            parts.append("")
            parts.append(zh_body)
            parts.append("")
            parts.append("---")
            parts.append("")

    elif zh_sections:
        # Case 2: Only translation has sections → split English proportionally
        mode = "proportional"
        en_body = extract_body_text(transcript_content)
        zh_sizes = [len(body) for _, body in zh_sections]
        en_chunks = split_proportionally(en_body, zh_sizes)

        for i, (zh_h, zh_body) in enumerate(zh_sections):
            en_chunk = en_chunks[i] if i < len(en_chunks) else ""
            parts.append(f"## {zh_h}")
            parts.append("")
            if en_chunk:
                parts.append(en_chunk)
                parts.append("")
            parts.append("---")
            parts.append("")
            parts.append(zh_body)
            parts.append("")
            parts.append("---")
            parts.append("")

    else:
        # Case 3: Neither has sections → two blocks
        mode = "blocks"
        en_body = extract_body_text(transcript_content)
        zh_body = strip_footer(extract_body_text(translation_content))

        parts.append(en_body)
        parts.append("")
        parts.append("---")
        parts.append("")
        parts.append(zh_body)
        parts.append("")
        parts.append("---")
        parts.append("")

    parts.append(FOOTER)

    output = "\n".join(parts)

    os.makedirs(COMBINED_DIR, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output)

    # Size check
    t_size = os.path.getsize(transcript_path)
    tr_size = os.path.getsize(translation_path)
    c_size = len(output.encode("utf-8"))

    ok = c_size >= (t_size + tr_size) * 0.8
    icon = "✅" if ok else "⚠️"
    print(f"  {icon} {sermon_name} ({mode}): {c_size:,} bytes")

    return "ok"


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="合并 transcript.md + translation.md → combined/{name}.md"
    )
    parser.add_argument("name", nargs="?", help="Sermon folder name")
    parser.add_argument("--all", action="store_true", help="Process all sermons")
    parser.add_argument(
        "--overwrite", action="store_true", help="Overwrite existing combined files"
    )
    args = parser.parse_args()

    if not args.name and not args.all:
        parser.print_help()
        sys.exit(1)

    if args.all:
        sermons = sorted(
            d
            for d in os.listdir(SERMONS_DIR)
            if os.path.isdir(os.path.join(SERMONS_DIR, d))
        )
        counts = {"ok": 0, "skip": 0, "error": 0}
        for name in sermons:
            result = generate_combined(name, args.overwrite)
            counts[result] += 1
        print(f"\nDone: {counts['ok']} generated, {counts['skip']} skipped, {counts['error']} errors")
    else:
        sermon_dir = os.path.join(SERMONS_DIR, args.name)
        if not os.path.isdir(sermon_dir):
            print(f"Error: sermons/{args.name}/ not found")
            sys.exit(1)
        result = generate_combined(args.name, args.overwrite)
        if result == "error":
            sys.exit(1)


if __name__ == "__main__":
    main()
