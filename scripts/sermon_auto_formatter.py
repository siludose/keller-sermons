#!/usr/bin/env python3
"""
Semi-automatic sermon formatter.
Processes sermon files with English transcripts to create standardized format.

Usage:
  python3 scripts/sermon_auto_formatter.py --file sermon_name
  python3 scripts/sermon_auto_formatter.py --batch --output output.md
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Optional, List, Dict, Tuple


ROOT = Path(__file__).resolve().parents[1]

# Bible book patterns - for extracting verse references
BIBLE_BOOKS = [
    "Matthew", "Mark", "Luke", "John",
    "Acts", "Romans", "Corinthians", "Galatians", "Ephesians", "Philippians",
    "Colossians", "Thessalonians", "Timothy", "Titus", "Philemon", "Hebrews",
    "James", "Peter", "John", "Jude", "Revelation",
]

VERSE_PATTERN = re.compile(
    r'(' + '|'.join(BIBLE_BOOKS) + r')\s+(\d+)[:\:：](\d+)(?:\s*-\s*(\d+))?',
    re.IGNORECASE
)


def extract_scripture_references(text: str) -> List[Tuple[str, int, int]]:
    """Extract Scripture book:chapter:verse references."""
    refs = set()
    for match in VERSE_PATTERN.finditer(text):
        book = match.group(1)
        chapter = int(match.group(2))
        verse = int(match.group(3))
        refs.add((book, chapter, verse))
    return sorted(list(refs))


def read_transcript(sermon_name: str) -> Optional[str]:
    """Read the English transcript."""
    transcript_path = ROOT / "transcripts" / f"{sermon_name}_transcript.txt"
    if not transcript_path.exists():
        return None
    return transcript_path.read_text(encoding="utf-8")


def read_sermon_md(sermon_name: str) -> Optional[str]:
    """Read the existing sermon MD file."""
    md_path = ROOT / f"{sermon_name}.md"
    if not md_path.exists():
        return None
    return md_path.read_text(encoding="utf-8")


def extract_outline(md_content: str) -> Optional[str]:
    """Extract outline from existing MD."""
    match = re.search(
        r'## Sermon Outline.*?\n(.*?)(?:\n---|\n##|\Z)',
        md_content,
        re.DOTALL | re.IGNORECASE
    )
    return match.group(1).strip() if match else None


def extract_english_transcript(md_content: str) -> Optional[str]:
    """Extract English section from existing MD."""
    match = re.search(
        r'### English.*?\n(.*?)(?:\n###|\n---|\Z)',
        md_content,
        re.DOTALL | re.IGNORECASE
    )
    return match.group(1).strip() if match else None


def extract_metadata(md_content: str) -> Dict[str, str]:
    """Extract metadata from existing MD."""
    metadata = {}
    patterns = {
        'date': r'\*\*Date.*?\*\*:\s*(.+)',
        'scripture': r'\*\*Scripture.*?\*\*:\s*(.+)',
        'series': r'\*\*Series.*?\*\*:\s*(.+)',
        'speaker': r'\*\*Speaker.*?\*\*:\s*(.+)',
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, md_content, re.IGNORECASE)
        if match:
            metadata[key] = match.group(1).strip()
    return metadata


def generate_outline_template(sermon_name: str) -> str:
    """Generate a basic outline template based on sermon name."""
    # Simple heuristic based on common patterns
    templates = {
        "virtue": "1. Definition\n2. Biblical Foundation\n3. Examples\n4. Application\n5. Conclusion",
        "jesus": "1. Introduction\n2. Who is Jesus?\n3. Jesus' Claims\n4. Jesus' Impact\n5. Conclusion",
        "gospel": "1. The Problem\n2. The Solution\n3. The Gospel Message\n4. Response\n5. Conclusion",
    }

    for key, template in templates.items():
        if key.lower() in sermon_name.lower():
            return template

    return "1. Introduction\n2. Main Point 1\n3. Main Point 2\n4. Main Point 3\n5. Conclusion"


def format_sermon(sermon_name: str, transcript: str, existing_md: Optional[str] = None) -> str:
    """Format sermon with standard template."""

    # Extract metadata from existing MD
    metadata = {}
    if existing_md:
        metadata = extract_metadata(existing_md)

    # Extract Scripture references
    scripture_refs = extract_scripture_references(transcript)

    # Build header
    header = f"# {sermon_name.replace('_', ' ')}\n"
    header += f"# {sermon_name.replace('_', ' ')} (中文待翻译)\n\n"

    # Add metadata
    speaker = metadata.get('speaker', '提摩太·凯勒 (Tim Keller)')
    date = metadata.get('date', '1990年代')
    scripture = metadata.get('scripture', 'Multiple passages')
    series = metadata.get('series', 'Gospel in Life')

    header += f"**Speaker / 讲者**: {speaker}\n"
    header += f"**Date / 日期**: {date}\n"
    header += f"**Scripture / 经文**: {scripture}\n"
    header += f"**Series / 系列**: {series}\n"
    header += "\n---\n\n"

    # Add outline
    if existing_md:
        outline = extract_outline(existing_md)
    else:
        outline = generate_outline_template(sermon_name)

    header += "## Sermon Outline / 讲道大纲\n\n"
    header += outline if outline else "Outline to be added\n"
    header += "\n\n---\n\n"

    # Add transcript section
    header += "## Full Transcript / 完整文本\n\n"
    header += "### English\n\n"

    # Break up transcript into paragraphs
    paragraphs = transcript.split('\n')
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    # Group into logical chunks (roughly 3-4 sentences per chunk)
    chunks = []
    current_chunk = []
    sentence_count = 0

    for para in paragraphs:
        current_chunk.append(para)
        sentence_count += para.count('.') + para.count('!') + para.count('?')

        if sentence_count >= 3 or len(current_chunk) >= 4:
            chunks.append(' '.join(current_chunk))
            current_chunk = []
            sentence_count = 0

    if current_chunk:
        chunks.append(' '.join(current_chunk))

    # Add formatted chunks
    for chunk in chunks:
        header += chunk + "\n\n"

    # Add Chinese section (placeholder)
    header += "\n---\n\n"
    header += "### 中文翻译\n\n"
    header += "（中文翻译待补充）\n\n"

    # Add Scripture references section
    if scripture_refs:
        header += "---\n\n"
        header += "## Scripture References / 经文引用\n\n"
        for book, chapter, verse in scripture_refs:
            header += f"- {book} {chapter}:{verse}\n"
        header += "\n"

    header += "\n---\n\n"
    header += f"*Last updated: 2026-02-07*\n"

    return header


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        description="Semi-automatic sermon formatter"
    )
    ap.add_argument("--file", help="Process a single sermon file")
    ap.add_argument("--output", help="Output file (default: overwrite original)")
    ap.add_argument("--list", action="store_true", help="List processable sermons")
    ap.add_argument("--batch", action="store_true", help="Process all available sermons")
    ap.add_argument("--dry-run", action="store_true", help="Show what would be done")

    args = ap.parse_args(argv)

    if args.list:
        # List sermons with transcripts
        transcripts_dir = ROOT / "transcripts"
        files = list(transcripts_dir.glob("*_transcript.txt"))
        print(f"Found {len(files)} sermon transcripts:")
        for f in sorted(files)[:20]:
            sermon_name = f.name.replace("_transcript.txt", "")
            size = f.stat().st_size / 1024
            md_exists = (ROOT / f"{sermon_name}.md").exists()
            status = "✓" if md_exists else "✗"
            print(f"  {status} {sermon_name} ({size:.1f}KB)")
        return 0

    if args.file:
        transcript = read_transcript(args.file)
        if not transcript:
            print(f"Error: No transcript found for {args.file}")
            return 1

        existing_md = read_sermon_md(args.file)
        formatted = format_sermon(args.file, transcript, existing_md)

        if args.dry_run:
            print(formatted[:500])
            print("\n... (truncated)")
            return 0

        output_path = Path(args.output) if args.output else ROOT / f"{args.file}.md"
        output_path.write_text(formatted, encoding="utf-8")
        print(f"Formatted sermon saved to: {output_path}")
        return 0

    if args.batch:
        # Process all available sermons
        transcripts_dir = ROOT / "transcripts"
        transcript_files = sorted(transcripts_dir.glob("*_transcript.txt"))

        print(f"Processing {len(transcript_files)} sermons...")

        processed = 0
        for i, transcript_file in enumerate(transcript_files, 1):
            sermon_name = transcript_file.name.replace("_transcript.txt", "")

            try:
                transcript = transcript_file.read_text(encoding="utf-8")
                existing_md = read_sermon_md(sermon_name)
                formatted = format_sermon(sermon_name, transcript, existing_md)

                output_path = ROOT / f"{sermon_name}.md"
                output_path.write_text(formatted, encoding="utf-8")
                processed += 1

                if i % 10 == 0:
                    print(f"  [{i}/{len(transcript_files)}] Processed {sermon_name}")
            except Exception as e:
                print(f"  Error processing {sermon_name}: {e}")

        print(f"\nCompleted: {processed}/{len(transcript_files)} sermons")
        return 0

    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
