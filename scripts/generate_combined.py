#!/usr/bin/env python3
"""
generate_combined.py - 合并 transcript.md + translation.md → combined/{name}.md

合并逻辑:
  - 完整保留两个源文件（包括首个标题前的内容、标题、分隔线和署名）。
  - 没有人工核验的对齐映射时，明确输出未逐段对齐的双语全文。
  - 不按标题数量或段落长度猜测对应关系，不添加译者署名。

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

ALIGNMENT_NOTICE = (
    "本文件保留英文原文与中文译文的完整内容，尚未逐段对齐。"
    " / Full source texts are preserved below; paragraph alignment has not been verified."
)


def has_chinese(text):
    return bool(re.search(r'[\u4e00-\u9fff]', text))


def read_file(path):
    with open(path, "r", encoding="utf-8", newline="") as f:
        return f.read()


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


def render_combined(meta, transcript_content, translation_content):
    """Embed each complete source once, without guessing cross-language alignment.

    Keep source strings verbatim: even content before a heading or inside a
    fenced code block is content, not disposable wrapper metadata. Existing
    source credits are retained; generation itself confers no authorship.
    """
    return (
        f"# {meta['title_zh']} / {meta['title_en']}\n\n"
        f"{ALIGNMENT_NOTICE}\n\n"
        "---\n\n## 英文原文 / English source\n\n"
        + transcript_content
        + "\n\n---\n\n## 中文译文 / Chinese source\n\n"
        + translation_content
        + "\n\n<!-- End of Chinese source -->\n"
    )


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

    output = render_combined(meta, transcript_content, translation_content)

    os.makedirs(COMBINED_DIR, exist_ok=True)
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        f.write(output)

    # Completeness is guaranteed by verbatim source inclusion, not a size ratio.
    print(f"  ✅ {sermon_name} (unaligned full texts): {len(output.encode('utf-8')):,} bytes")

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
        if counts["error"]:
            sys.exit(1)
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
