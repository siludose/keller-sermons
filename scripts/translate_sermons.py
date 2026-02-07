#!/usr/bin/env python3
"""
Generate Chinese translations for sermon files using Claude AI.

This script:
1. Reads English transcript from each sermon file
2. Uses Claude API to translate to Chinese
3. Replaces placeholder with actual translation
4. Preserves other file content

Usage:
  python3 scripts/translate_sermons.py --file sermon_name
  python3 scripts/translate_sermons.py --batch
"""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path
from typing import Optional, List

try:
    import anthropic
except ImportError:
    print("Error: anthropic package not installed. Run: pip install anthropic")
    exit(1)


ROOT = Path(__file__).resolve().parents[1]


def extract_english_transcript(content: str) -> Optional[str]:
    """Extract English transcript from sermon content."""
    # Look for English section
    match = re.search(
        r'### English\s*\n(.*?)(?:\n### 中文翻译|\n---|\Z)',
        content,
        re.DOTALL
    )
    if match:
        return match.group(1).strip()
    return None


def translate_with_claude(english_text: str, client: anthropic.Anthropic) -> Optional[str]:
    """Translate English text to Chinese using Claude API."""
    try:
        # Limit text to manageable size
        text_to_translate = english_text[:3000]
        
        message = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=4000,
            messages=[
                {
                    "role": "user",
                    "content": f"""请将以下讲道文本翻译成中文（使用简体中文），保持原有的格式和结构：

{text_to_translate}

要求：
1. 保持标题、小标题的格式（#### 等）
2. 保持引用块、列表等的格式
3. 如果有圣经经文引用，保持英文书卷名称（如 Matthew, Romans 等）
4. 翻译应该自然流畅，符合中文表达习惯
5. 不要添加额外的解释或注释
"""
                }
            ]
        )
        
        return message.content[0].text
    except Exception as e:
        print(f"Error: {e}")
        return None


def process_sermon(sermon_name: str, client: anthropic.Anthropic) -> bool:
    """Process a single sermon file for translation."""
    md_path = ROOT / f"{sermon_name}.md"
    if not md_path.exists():
        return False

    content = md_path.read_text(encoding="utf-8")
    
    # Check if already has Chinese translation (not placeholder)
    if "### 中文翻译" in content and "中文翻译待补充" not in content:
        return False
    
    # Extract English transcript
    english_text = extract_english_transcript(content)
    if not english_text:
        return False
    
    # Translate with Claude
    print(f"  Translating {sermon_name}...", end=" ", flush=True)
    chinese_text = translate_with_claude(english_text, client)
    
    if not chinese_text:
        print("FAILED")
        return False
    
    # Replace placeholder with translation
    new_content = re.sub(
        r'### 中文翻译\s*\n\n中文翻译待补充',
        f'### 中文翻译\n\n{chinese_text}',
        content
    )
    
    if new_content == content:
        print("SKIPPED")
        return False
    
    md_path.write_text(new_content, encoding="utf-8")
    print("DONE")
    return True


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Translate sermons to Chinese")
    ap.add_argument("--file", help="Process a single sermon file")
    ap.add_argument("--batch", action="store_true", help="Process all sermon files")

    args = ap.parse_args(argv)
    
    # Initialize API client
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        return 1
    
    client = anthropic.Anthropic(api_key=api_key)

    if args.file:
        if process_sermon(args.file, client):
            print(f"Translated {args.file}")
        else:
            print(f"No translation needed for {args.file}")
        return 0

    if args.batch:
        # Find all files that need translation
        sermon_files = sorted(ROOT.glob("*.md"))
        sermon_files = [
            f.stem for f in sermon_files 
            if not f.name.startswith(("README", "SERMON", "BIBLE"))
            and "中文翻译待补充" in f.read_text(encoding="utf-8", errors="ignore")
        ]

        print(f"\nFound {len(sermon_files)} files needing translation\n")
        translated = 0
        for i, sermon_name in enumerate(sermon_files, 1):
            if process_sermon(sermon_name, client):
                translated += 1
            if i % 5 == 0:
                print(f"  [{i}/{len(sermon_files)}] Progress: {translated} translated so far")

        print(f"\nTranslated {translated}/{len(sermon_files)} sermon files")
        return 0

    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
