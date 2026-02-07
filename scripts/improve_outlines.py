#!/usr/bin/env python3
"""
Improve sermon outlines by extracting from existing versions.

This script:
1. Checks if sermon has a better outline in git history
2. Updates outlines to be more structured

Usage:
  python3 scripts/improve_outlines.py --batch
"""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path
from typing import Optional, List


ROOT = Path(__file__).resolve().parents[1]


def get_git_file_version(filename: str, commit: str = "HEAD~1") -> Optional[str]:
    """Get a previous version of a file from git."""
    try:
        result = subprocess.run(
            ["git", "show", f"{commit}:{filename}"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return result.stdout
    except Exception:
        pass
    return None


def extract_outline_from_content(content: str) -> Optional[str]:
    """Extract outline section from markdown content."""
    # Look for outline section
    match = re.search(
        r'## (?:Sermon )?Outline.*?\n(.*?)(?:\n---|\n##|\Z)',
        content,
        re.DOTALL | re.IGNORECASE
    )
    if match:
        return match.group(1).strip()
    return None


def has_good_outline(outline: str) -> bool:
    """Check if outline looks complete/good."""
    if not outline:
        return False
    # Good outline should have multiple lines with structure
    lines = outline.strip().split('\n')
    return len(lines) > 3 and any(c in outline for c in ['1.', '2.', '3.', '-', '*'])


def improve_sermon_outline(sermon_name: str) -> bool:
    """Try to improve sermon outline."""
    md_path = ROOT / f"{sermon_name}.md"
    if not md_path.exists():
        return False

    content = md_path.read_text(encoding="utf-8")
    current_outline = extract_outline_from_content(content)

    # If current outline is already good, skip
    if has_good_outline(current_outline):
        return False

    # Try to get outline from previous git version
    old_content = get_git_file_version(f"{sermon_name}.md", "HEAD~2")
    if old_content:
        old_outline = extract_outline_from_content(old_content)
        if has_good_outline(old_outline) and old_outline != current_outline:
            # Replace outline
            new_content = re.sub(
                r'## Sermon Outline.*?\n.*?(?=\n---)',
                f'## Sermon Outline / 讲道大纲\n\n{old_outline}',
                content,
                flags=re.DOTALL | re.IGNORECASE,
            )

            if new_content != content:
                md_path.write_text(new_content, encoding="utf-8")
                return True

    return False


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Improve sermon outlines")
    ap.add_argument("--batch", action="store_true", help="Process all sermon files")

    args = ap.parse_args(argv)

    if args.batch:
        # Process all MD files
        sermon_files = sorted(ROOT.glob("*.md"))
        sermon_files = [f.stem for f in sermon_files if not f.name.startswith(("README", "SERMON", "BIBLE"))]

        improved = 0
        for i, sermon_name in enumerate(sermon_files, 1):
            if improve_sermon_outline(sermon_name):
                improved += 1
                if i % 20 == 0:
                    print(f"  [{i}/{len(sermon_files)}] {sermon_name}")

        print(f"\nImproved {improved}/{len(sermon_files)} sermon outlines")
        return 0

    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
