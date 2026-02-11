#!/usr/bin/env python3
"""
Generate Chinese translations for sermon files using local Ollama or Claude AI.

This script:
1. Reads English transcript from each sermon file
2. Attempts to use local Ollama model (if available)
3. Falls back to Claude API if Ollama is unavailable
4. Replaces placeholder with actual translation
5. Preserves other file content

Usage:
  python3 scripts/translate_sermons.py --file sermon_name
  python3 scripts/translate_sermons.py --batch
  python3 scripts/translate_sermons.py --file sermon_name --backend ollama
  python3 scripts/translate_sermons.py --file sermon_name --backend claude
"""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path
from typing import Optional, List, Tuple

try:
    import anthropic
except ImportError:
    print("Error: anthropic package not installed. Run: pip install anthropic")
    exit(1)

try:
    from openai import OpenAI
except ImportError:
    print("Error: openai package not installed. Run: pip install openai")
    exit(1)

try:
    import requests
except ImportError:
    print("Error: requests package not installed. Run: pip install requests")
    exit(1)


ROOT = Path(__file__).resolve().parents[1]

# Global variable to cache the selected backend
_translation_backend = None
_translation_client = None


def check_ollama_available() -> bool:
    """Check if local Ollama service is available and has the qwen2.5 model."""
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=2)
        if resp.status_code != 200:
            return False
        data = resp.json()
        models = [m.get("name", "") for m in data.get("models", [])]
        # Check if any qwen2.5 model is available
        return any("qwen2.5" in m for m in models)
    except Exception:
        return False


def translate_with_ollama(text: str, client: OpenAI) -> Optional[str]:
    """Translate English text to Chinese using local Ollama model."""
    try:
        # Limit text to manageable size (Qwen2.5-7B context limit)
        text_to_translate = text[:3000]

        response = client.chat.completions.create(
            model="qwen2.5:7b-instruct-q8_0",
            messages=[
                {
                    "role": "system",
                    "content": """You are a professional Chinese translator specializing in religious texts.
Your task is to translate sermon content to Simplified Chinese while preserving:
1. All markdown formatting (headers, bold, lists, etc.)
2. Bible book names in English (e.g., Matthew, Romans, John)
3. The natural flow and rhetorical power of the original text
4. Any quoted material clearly marked with >

Translate naturally and fluently, as if written by a native Chinese speaker."""
                },
                {
                    "role": "user",
                    "content": f"Translate this sermon excerpt to Simplified Chinese:\n\n{text_to_translate}"
                }
            ],
            max_tokens=4000,
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Ollama error: {e}", flush=True)
        return None


def translate_with_claude(text: str, client: anthropic.Anthropic) -> Optional[str]:
    """Translate English text to Chinese using Claude API."""
    try:
        # Limit text to manageable size
        text_to_translate = text[:3000]

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
        print(f"Claude error: {e}", flush=True)
        return None


def get_translation_backend(force_backend: Optional[str] = None) -> Tuple[str, any]:
    """
    Select and initialize a translation backend.

    Priority:
    1. Forced backend (if specified)
    2. Ollama (if available)
    3. Claude (fallback)

    Returns:
        Tuple of (backend_name, client_object)
    """
    global _translation_backend, _translation_client

    # If already cached and no force, return cached
    if not force_backend and _translation_backend and _translation_client:
        return (_translation_backend, _translation_client)

    # If forced backend specified
    if force_backend:
        if force_backend == "ollama":
            if check_ollama_available():
                client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
                _translation_backend = "ollama"
                _translation_client = client
                return ("ollama", client)
            else:
                raise RuntimeError("Ollama is not available at http://localhost:11434")
        elif force_backend == "claude":
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if api_key:
                client = anthropic.Anthropic(api_key=api_key)
                _translation_backend = "claude"
                _translation_client = client
                return ("claude", client)
            else:
                raise RuntimeError("ANTHROPIC_API_KEY environment variable not set")

    # Try Ollama first (no force)
    if check_ollama_available():
        client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
        _translation_backend = "ollama"
        _translation_client = client
        return ("ollama", client)

    # Fallback to Claude
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        client = anthropic.Anthropic(api_key=api_key)
        _translation_backend = "claude"
        _translation_client = client
        return ("claude", client)

    raise RuntimeError(
        "No translation backend available:\n"
        "- Ollama not running at http://localhost:11434\n"
        "- ANTHROPIC_API_KEY environment variable not set"
    )


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


def process_sermon(sermon_name: str, backend: str, client: any) -> bool:
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

    # Translate with selected backend
    print(f"  Translating {sermon_name}...", end=" ", flush=True)
    if backend == "ollama":
        chinese_text = translate_with_ollama(english_text, client)
    elif backend == "claude":
        chinese_text = translate_with_claude(english_text, client)
    else:
        print(f"UNKNOWN BACKEND: {backend}")
        return False

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
    ap = argparse.ArgumentParser(description="Translate sermons to Chinese using Ollama or Claude")
    ap.add_argument("--file", help="Process a single sermon file")
    ap.add_argument("--batch", action="store_true", help="Process all sermon files")
    ap.add_argument(
        "--backend",
        choices=["auto", "ollama", "claude"],
        default="auto",
        help="Translation backend to use (default: auto - tries Ollama first, falls back to Claude)"
    )

    args = ap.parse_args(argv)

    # Get translation backend
    try:
        backend, client = get_translation_backend(force_backend=None if args.backend == "auto" else args.backend)
        print(f"Translation backend: {backend}")
    except RuntimeError as e:
        print(f"Error: {e}")
        return 1

    if args.file:
        if process_sermon(args.file, backend, client):
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
            if process_sermon(sermon_name, backend, client):
                translated += 1
            if i % 5 == 0:
                print(f"  [{i}/{len(sermon_files)}] Progress: {translated} translated so far")

        print(f"\nTranslated {translated}/{len(sermon_files)} sermon files")
        return 0

    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
