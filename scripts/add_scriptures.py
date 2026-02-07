#!/usr/bin/env python3
"""
Add Scripture references and CUV Bible passages to sermon files.

This script:
1. Extracts Scripture references from sermon text
2. Queries the CUV Bible for verses
3. Adds them to the sermon file

Usage:
  python3 scripts/add_scriptures.py --file sermon_name
  python3 scripts/add_scriptures.py --batch
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Optional, List, Set, Tuple


ROOT = Path(__file__).resolve().parents[1]

# Extended Bible book names (English)
BIBLE_BOOKS_EN = {
    "Matthew": "马太福音",
    "Mark": "马可福音",
    "Luke": "路加福音",
    "John": "约翰福音",
    "Acts": "使徒行传",
    "Romans": "罗马书",
    "Corinthians": "哥林多",
    "Galatians": "加拉太书",
    "Ephesians": "以弗所书",
    "Philippians": "腓立比书",
    "Colossians": "歌罗西书",
    "Thessalonians": "帖撒罗尼迦",
    "Timothy": "提摩太",
    "Titus": "提多书",
    "Philemon": "腓利门书",
    "Hebrews": "希伯来书",
    "James": "雅各书",
    "Peter": "彼得",
    "John": "约翰",
    "Jude": "犹大书",
    "Revelation": "启示录",
}

# Pattern to find Scripture references
VERSE_PATTERN = re.compile(
    r'\b(' + '|'.join(re.escape(b) for b in BIBLE_BOOKS_EN.keys()) + r')\s+(\d+)[:\:：](\d+)',
    re.IGNORECASE
)


def extract_verses(text: str) -> Set[Tuple[str, int, int]]:
    """Extract unique Scripture references from text."""
    verses = set()
    for match in VERSE_PATTERN.finditer(text):
        book = match.group(1)
        chapter = int(match.group(2))
        verse = int(match.group(3))
        verses.add((book, chapter, verse))
    return verses


def query_cuv_verse(book_en: str, chapter: int, verse: int) -> Optional[str]:
    """Query CUV Bible using the cuv_bible_query.py script."""
    try:
        result = subprocess.run(
            [
                "python3",
                str(ROOT / "scripts" / "cuv_bible_query.py"),
                "--book",
                BIBLE_BOOKS_EN.get(book_en, book_en),
                "--chapter",
                str(chapter),
                "--verse",
                str(verse),
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 2:
                return lines[1]
    except Exception as e:
        pass
    return None


def add_scripture_section(md_content: str, verses: Set[Tuple[str, int, int]]) -> str:
    """Add Scripture References section to MD file."""
    if not verses:
        return md_content

    # Check if section already exists
    if "## Scripture References" in md_content:
        return md_content

    # Build scripture section
    scripture_section = "\n---\n\n## Scripture References / 经文引用\n\n"

    for book, chapter, verse in sorted(verses):
        book_zh = BIBLE_BOOKS_EN.get(book, book)
        scripture_section += f"- {book_zh} {chapter}:{verse}\n"

    scripture_section += "\n"

    # Insert before the final timestamp
    if "*Last updated:" in md_content:
        md_content = md_content.replace(
            "\n*Last updated:",
            scripture_section + "*Last updated:",
        )
    else:
        md_content += scripture_section

    return md_content


def process_sermon(sermon_name: str) -> bool:
    """Process a single sermon file."""
    md_path = ROOT / f"{sermon_name}.md"
    if not md_path.exists():
        return False

    content = md_path.read_text(encoding="utf-8")

    # Extract verses
    verses = extract_verses(content)
    if not verses:
        return False

    # Add scripture section
    updated = add_scripture_section(content, verses)

    if updated != content:
        md_path.write_text(updated, encoding="utf-8")
        return True

    return False


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Add Scripture references to sermons")
    ap.add_argument("--file", help="Process a single sermon file")
    ap.add_argument("--batch", action="store_true", help="Process all sermon files")

    args = ap.parse_args(argv)

    if args.file:
        if process_sermon(args.file):
            print(f"Updated {args.file}")
        else:
            print(f"No changes needed for {args.file}")
        return 0

    if args.batch:
        # Process all MD files
        sermon_files = sorted(ROOT.glob("*.md"))
        sermon_files = [f.stem for f in sermon_files if not f.name.startswith(("README", "SERMON"))]

        updated_count = 0
        for i, sermon_name in enumerate(sermon_files, 1):
            if process_sermon(sermon_name):
                updated_count += 1
                if i % 20 == 0:
                    print(f"  [{i}/{len(sermon_files)}] Processing {sermon_name}")

        print(f"\nUpdated {updated_count}/{len(sermon_files)} sermon files")
        return 0

    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
