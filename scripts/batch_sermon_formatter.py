#!/usr/bin/env python3
"""
Batch formatter for sermon markdown files.

This script helps process multiple sermon files, providing:
1. Detection of Bible verse references
2. Suggestions for formatting improvements
3. Progress tracking

Usage:
  python3 scripts/batch_sermon_formatter.py --action analyze [--dir .]
  python3 scripts/batch_sermon_formatter.py --action list-verses --file filename.md
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Optional, List, Dict, Tuple


ROOT = Path(__file__).resolve().parents[1]

# Bible book patterns - common Chinese names
BIBLE_BOOKS = [
    # OT
    "创世记", "出埃及记", "利未记", "民数记", "申命记",
    "约书亚记", "士师记", "路得记", "撒母耳记上", "撒母耳记下",
    "列王纪上", "列王纪下", "历代志上", "历代志下", "以斯拉记",
    "尼希米记", "以斯帖记", "约伯记", "诗篇", "箴言",
    "传道书", "以赛亚书", "耶利米书", "耶利米哀歌", "以西结书",
    "但以理书", "何西阿书", "约珥书", "阿摩司书", "俄巴底亚书",
    "约拿书", "弥迦书", "那鸿书", "哈巴谷书", "西番雅书",
    "哈该书", "撒迦利亚书", "玛拉基书",
    # NT
    "马太福音", "马可福音", "路加福音", "约翰福音",
    "使徒行传", "罗马书", "哥林多前书", "哥林多后书",
    "加拉太书", "以弗所书", "腓立比书", "歌罗西书",
    "帖撒罗尼迦前书", "帖撒罗尼迦后书", "提摩太前书", "提摩太后书",
    "提多书", "腓利门书", "希伯来书", "雅各书",
    "彼得前书", "彼得后书", "约翰一书", "约翰二书",
    "约翰三书", "犹大书", "启示录",
]

# Verse reference pattern: "书卷 chapter:verse" or "书卷chapter:verse"
VERSE_PATTERN = re.compile(
    r'(' + '|'.join(re.escape(book) for book in BIBLE_BOOKS) + r')\s*(\d+)[:\:：](\d+)'
)


def find_bible_references(content: str) -> List[Tuple[str, int, int]]:
    """Find all Bible verse references in the text."""
    matches = []
    for match in VERSE_PATTERN.finditer(content):
        book = match.group(1)
        chapter = int(match.group(2))
        verse = int(match.group(3))
        matches.append((book, chapter, verse))
    return matches


def analyze_file(filepath: Path) -> Dict:
    """Analyze a sermon file."""
    if not filepath.exists():
        return {"error": f"File not found: {filepath}"}

    with filepath.open("r", encoding="utf-8") as f:
        content = f.read()

    # Check file structure
    has_outline = "## Sermon Outline" in content or "## 讲道大纲" in content
    has_english = "### English" in content or "### 英文" in content
    has_chinese = "### 中文" in content or "### Chinese" in content

    # Find Bible references
    verses = find_bible_references(content)

    # Check for verse content (blockquotes)
    verse_blockquotes = len(re.findall(r'^> ', content, re.MULTILINE))

    # Estimate Chinese paragraph lengths
    chinese_section = None
    if has_chinese:
        # Try to extract Chinese section
        match = re.search(r'### 中文翻译\n+(.*?)(?=\n###|\Z)', content, re.DOTALL)
        if match:
            chinese_section = match.group(1)

    return {
        "file": filepath.name,
        "size_kb": filepath.stat().st_size / 1024,
        "has_outline": has_outline,
        "has_english": has_english,
        "has_chinese": has_chinese,
        "bible_references": verses,
        "verse_count": len(verses),
        "verse_blockquotes": verse_blockquotes,
        "needs_formatting": not (has_outline and has_english and has_chinese),
    }


def list_sermon_files(directory: Path = ROOT) -> List[Path]:
    """List all sermon markdown files."""
    files = sorted(
        [
            f
            for f in directory.glob("*.md")
            if f.name
            not in ["README.md", "BIBLE_QUERY.md", "SERMON_FORMATTING_WORKFLOW.md"]
        ]
    )
    return files


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        description="Batch sermon formatter and analyzer"
    )
    sub = ap.add_subparsers(dest="action", required=True)

    # analyze action
    ap_analyze = sub.add_parser("analyze", help="Analyze sermon files")
    ap_analyze.add_argument("--dir", default=str(ROOT))
    ap_analyze.add_argument("--output", help="Output JSON file")

    # list-verses action
    ap_list = sub.add_parser("list-verses", help="List Bible verses in a file")
    ap_list.add_argument("--file", required=True)

    # summary action
    ap_summary = sub.add_parser("summary", help="Print processing summary")
    ap_summary.add_argument("--dir", default=str(ROOT))

    args = ap.parse_args(argv)

    if args.action == "analyze":
        directory = Path(args.dir)
        files = list_sermon_files(directory)
        results = []

        for i, filepath in enumerate(files, 1):
            print(f"[{i}/{len(files)}] Analyzing {filepath.name}...", end=" ")
            analysis = analyze_file(filepath)
            results.append(analysis)
            status = "✓" if not analysis.get("needs_formatting") else "⚠"
            print(f"{status}")

        # Summary statistics
        total_files = len(results)
        needs_work = sum(1 for r in results if r.get("needs_formatting"))
        total_verses = sum(r.get("verse_count", 0) for r in results)

        print(f"\n=== Summary ===")
        print(f"Total files: {total_files}")
        print(f"Need formatting: {needs_work}")
        print(f"Total Bible verse references: {total_verses}")

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"Results saved to: {args.output}")

        return 0

    if args.action == "list-verses":
        filepath = Path(args.file)
        if not filepath.exists():
            print(f"File not found: {filepath}")
            return 1

        analysis = analyze_file(filepath)
        if "error" in analysis:
            print(f"Error: {analysis['error']}")
            return 1

        verses = analysis.get("bible_references", [])
        if not verses:
            print(f"No Bible verses found in {filepath.name}")
            return 0

        print(f"Bible verses in {filepath.name}:")
        for book, chapter, verse in sorted(set(verses)):
            print(f"  - {book} {chapter}:{verse}")

        return 0

    if args.action == "summary":
        directory = Path(args.dir)
        files = list_sermon_files(directory)
        results = []

        print("Analyzing all sermon files...")
        for filepath in files:
            analysis = analyze_file(filepath)
            results.append(analysis)

        # Detailed summary
        has_all_sections = sum(
            1
            for r in results
            if r.get("has_outline")
            and r.get("has_english")
            and r.get("has_chinese")
        )

        print(f"\n=== Sermon Files Summary ===")
        print(f"Total sermon files: {len(results)}")
        print(f"With complete structure: {has_all_sections}")
        print(f"Needing formatting: {sum(1 for r in results if r.get('needs_formatting'))}")
        print(f"\nTotal Bible verse references: {sum(r.get('verse_count', 0) for r in results)}")
        print(f"Total verse blockquotes: {sum(r.get('verse_blockquotes', 0) for r in results)}")

        # List files needing work
        needing_work = [r for r in results if r.get("needs_formatting")]
        if needing_work:
            print(f"\nFiles needing structure improvements ({len(needing_work)}):")
            for r in sorted(needing_work, key=lambda x: -x["size_kb"])[:10]:
                print(f"  - {r['file']} ({r['size_kb']:.1f}KB)")
                missing = []
                if not r.get("has_outline"):
                    missing.append("outline")
                if not r.get("has_english"):
                    missing.append("English section")
                if not r.get("has_chinese"):
                    missing.append("Chinese section")
                if missing:
                    print(f"    Missing: {', '.join(missing)}")

        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
