#!/usr/bin/env python3
"""
Directly translate sermon files by reading and processing locally.
This script coordinates with Claude to handle translations in batches.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional, List


ROOT = Path(__file__).resolve().parents[1]


def extract_english_transcript(content: str) -> Optional[str]:
    """Extract English transcript from sermon content."""
    match = re.search(
        r'### English\s*\n(.*?)(?:\n### 中文翻译|\n---|\Z)',
        content,
        re.DOTALL
    )
    if match:
        return match.group(1).strip()
    return None


def needs_translation(content: str) -> bool:
    """Check if file needs translation."""
    return "### 中文翻译" in content and "中文翻译待补充" in content


def list_files_needing_translation() -> List[str]:
    """List all files that need translation."""
    sermon_files = sorted(ROOT.glob("*.md"))
    result = []
    for f in sermon_files:
        if f.name.startswith(("README", "SERMON", "BIBLE")):
            continue
        try:
            content = f.read_text(encoding="utf-8")
            if needs_translation(content):
                result.append(f.stem)
        except:
            pass
    return result


def main():
    files = list_files_needing_translation()
    print(f"Found {len(files)} files needing translation:")
    for i, filename in enumerate(files[:20], 1):
        print(f"  {i}. {filename}")
    if len(files) > 20:
        print(f"  ... and {len(files) - 20} more")


if __name__ == "__main__":
    main()
