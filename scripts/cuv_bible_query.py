#!/usr/bin/env python3
"""
Query Chinese Union Version (CUV) Bible from CUNPS.json.

Data source: bibles_downloads/CUNPS.json
The file is a JSON list with structure:
  [
    {
      "pk": 3514482,
      "translation": "CUNPS",
      "book": 1,
      "chapter": 1,
      "verse": 1,
      "text": "起初，神创造天地。",
      ...
    },
    ...
  ]

Book mapping:
  1: 创世记, 2: 出埃及记, ..., 39: 玛拉基书,
  40: 马太福音, 41: 马可福音, ..., 66: 启示录
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional, List, Dict, Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CUNPS_PATH = ROOT / "bibles_downloads" / "CUNPS.json"

# Bible book number to name mapping (CUV standard)
BOOK_NUM_TO_NAME = {
    1: "创世记", 2: "出埃及记", 3: "利未记", 4: "民数记", 5: "申命记",
    6: "约书亚记", 7: "士师记", 8: "路得记", 9: "撒母耳记上", 10: "撒母耳记下",
    11: "列王纪上", 12: "列王纪下", 13: "历代志上", 14: "历代志下", 15: "以斯拉记",
    16: "尼希米记", 17: "以斯帖记", 18: "约伯记", 19: "诗篇", 20: "箴言",
    21: "传道书", 22: "以赛亚书", 23: "耶利米书", 24: "耶利米哀歌", 25: "以西结书",
    26: "但以理书", 27: "何西阿书", 28: "约珥书", 29: "阿摩司书", 30: "俄巴底亚书",
    31: "约拿书", 32: "弥迦书", 33: "那鸿书", 34: "哈巴谷书", 35: "西番雅书",
    36: "哈该书", 37: "撒迦利亚书", 38: "玛拉基书",
    40: "马太福音", 41: "马可福音", 42: "路加福音", 43: "约翰福音",
    44: "使徒行传", 45: "罗马书", 46: "哥林多前书", 47: "哥林多后书",
    48: "加拉太书", 49: "以弗所书", 50: "腓立比书", 51: "歌罗西书",
    52: "帖撒罗尼迦前书", 53: "帖撒罗尼迦后书", 54: "提摩太前书", 55: "提摩太后书",
    56: "提多书", 57: "腓利门书", 58: "希伯来书", 59: "雅各书",
    60: "彼得前书", 61: "彼得后书", 62: "约翰一书", 63: "约翰二书",
    64: "约翰三书", 65: "犹大书", 66: "启示录",
}

# Reverse mapping
NAME_TO_BOOK_NUM = {v: k for k, v in BOOK_NUM_TO_NAME.items()}


def load_bible_data(path: Path) -> List[Dict[str, Any]]:
    """Load the CUNPS JSON file."""
    if not path.exists():
        raise FileNotFoundError(f"Bible data not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def normalize_book_name(name: str) -> str:
    """Normalize book name for lookup."""
    return name.strip()


def query_verse(
    bible_data: List[Dict[str, Any]],
    book: str,
    chapter: int,
    verse: Optional[int] = None,
) -> Optional[str]:
    """
    Query a verse from the Bible data.

    Args:
        bible_data: The loaded Bible JSON list
        book: Book name (e.g., "创世记", "马太福音", "雅各书")
        chapter: Chapter number
        verse: Verse number (optional - if None, return all verses in chapter)

    Returns:
        The verse text, or None if not found
    """
    book_name = normalize_book_name(book)

    # Find book number
    book_num = NAME_TO_BOOK_NUM.get(book_name)
    if book_num is None:
        return None

    # Find matching verses
    results = []
    for entry in bible_data:
        if (
            entry.get("book") == book_num
            and entry.get("chapter") == chapter
            and (verse is None or entry.get("verse") == verse)
        ):
            results.append(entry)

    if not results:
        return None

    # If specific verse requested, return single result
    if verse is not None and results:
        return results[0].get("text")

    # Otherwise, concatenate all verses in the chapter
    if verse is None:
        texts = [entry.get("text", "") for entry in results]
        return " ".join(texts)


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        description="Query Chinese Union Version (CUV) Bible"
    )
    ap.add_argument(
        "--bible",
        default=str(DEFAULT_CUNPS_PATH),
        help="Path to CUNPS.json file",
    )
    ap.add_argument(
        "--book",
        required=True,
        help="Book name (e.g., 创世记, 马太福音, 雅各书)",
    )
    ap.add_argument(
        "--chapter",
        type=int,
        required=True,
        help="Chapter number",
    )
    ap.add_argument(
        "--verse",
        type=int,
        help="Verse number (optional)",
    )

    args = ap.parse_args(argv)

    try:
        bible_data = load_bible_data(Path(args.bible))
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        return 1

    result = query_verse(bible_data, args.book, args.chapter, args.verse)

    if result is None:
        print("NOT_FOUND")
        return 2

    # Format output
    ref = f"{args.book} {args.chapter}"
    if args.verse:
        ref += f":{args.verse}"

    print(f"{ref}")
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
