#!/usr/bin/env python3
"""
Build and query a local index for the gitbook-holy-bible-niv-chinese repo.

Data source (already downloaded locally in this workspace):
  bibles_downloads/gitbook-holy-bible-niv-chinese/src/*.md

Format assumptions (observed across multiple books):
  - Chapter heading: "## <BookName>第<Chapter>章"
  - Verse marker: "<Abbr><Chapter>:<Verse>" on its own line (e.g. "太1:1", "王上1:1")
  - Verse content: blockquotes, with an empty blockquote line separating EN and ZH:
      > English...
      >
      > 中文...
"""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Tuple


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SRC_DIR = ROOT / "bibles_downloads" / "gitbook-holy-bible-niv-chinese" / "src"
DEFAULT_INDEX_PATH = ROOT / "bibles_downloads" / "gitbook-holy-bible-niv-chinese" / "index.jsonl"


CHAPTER_RE = re.compile(r"^##\s+(?P<book>.+?)第(?P<chapter>\d+)章\s*$")
VERSE_MARK_RE = re.compile(r"^(?P<abbr>[\S]+?)(?P<chapter>\d+):(?P<verse>\d+)\s*$")
FILENAME_RE = re.compile(r"^(?P<num>\d+)-(?P<book>.+?)\.md$")


@dataclass(frozen=True)
class VerseRow:
    book: str
    abbr: str
    chapter: int
    verse: int
    en: str
    zh: str
    source_file: str

    def to_json(self) -> str:
        return json.dumps(
            {
                "book": self.book,
                "abbr": self.abbr,
                "chapter": self.chapter,
                "verse": self.verse,
                "en": self.en,
                "zh": self.zh,
                "source_file": self.source_file,
            },
            ensure_ascii=False,
        )


def _strip_blockquote(line: str) -> Optional[str]:
    s = line.rstrip("\n")
    if not s.startswith(">"):
        return None
    # "> text" or ">".
    s = s[1:]
    if s.startswith(" "):
        s = s[1:]
    return s


def _parse_book_name_from_filename(p: Path) -> str:
    m = FILENAME_RE.match(p.name)
    if not m:
        raise ValueError(f"Unexpected filename format: {p.name}")
    return m.group("book")


def parse_markdown_book(path: Path) -> Iterator[VerseRow]:
    book_name = _parse_book_name_from_filename(path)
    abbr: Optional[str] = None
    current_chapter: Optional[int] = None

    lines = path.read_text(encoding="utf-8").splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        m_ch = CHAPTER_RE.match(line)
        if m_ch:
            current_chapter = int(m_ch.group("chapter"))
            i += 1
            continue

        m_vm = VERSE_MARK_RE.match(line)
        if m_vm:
            if current_chapter is None:
                # Fall back to marker chapter if no heading encountered.
                current_chapter = int(m_vm.group("chapter"))
            abbr = m_vm.group("abbr")
            ch = int(m_vm.group("chapter"))
            vs = int(m_vm.group("verse"))

            # Collect following blockquote lines until next marker or chapter heading.
            i += 1
            bq: List[str] = []
            while i < len(lines):
                nxt = lines[i]
                nxt_s = nxt.strip()
                if CHAPTER_RE.match(nxt_s) or VERSE_MARK_RE.match(nxt_s):
                    break
                stripped = _strip_blockquote(nxt)
                if stripped is not None:
                    bq.append(stripped)
                i += 1

            # Split EN/ZH by first empty blockquote line.
            en_parts: List[str] = []
            zh_parts: List[str] = []
            target = en_parts
            for t in bq:
                if t.strip() == "":
                    # Only flip once, keep additional empties as paragraph breaks.
                    if target is en_parts and en_parts:
                        target = zh_parts
                    continue
                target.append(t.strip())

            en_text = " ".join(en_parts).strip()
            zh_text = " ".join(zh_parts).strip()
            yield VerseRow(
                book=book_name,
                abbr=abbr or "",
                chapter=ch,
                verse=vs,
                en=en_text,
                zh=zh_text,
                source_file=str(path),
            )
            continue

        i += 1


def iter_book_files(src_dir: Path) -> List[Path]:
    files: List[Path] = []
    for p in src_dir.glob("*.md"):
        if FILENAME_RE.match(p.name):
            files.append(p)
    files.sort(key=lambda p: int(FILENAME_RE.match(p.name).group("num")))  # type: ignore[union-attr]
    return files


def build_index(src_dir: Path, index_path: Path) -> Tuple[int, Dict[str, str]]:
    index_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    book_to_abbr: Dict[str, str] = {}

    with index_path.open("w", encoding="utf-8") as f:
        for book_file in iter_book_files(src_dir):
            for row in parse_markdown_book(book_file):
                if row.book and row.abbr and row.book not in book_to_abbr:
                    book_to_abbr[row.book] = row.abbr
                f.write(row.to_json())
                f.write("\n")
                count += 1

    return count, book_to_abbr


def _load_index(index_path: Path) -> Iterator[dict]:
    with index_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def query(index_path: Path, book_or_abbr: str, chapter: int, verse: int) -> Optional[dict]:
    key = book_or_abbr.strip()
    for row in _load_index(index_path):
        if row.get("chapter") != chapter or row.get("verse") != verse:
            continue
        if row.get("book") == key or row.get("abbr") == key:
            return row
    return None


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    ap_build = sub.add_parser("build", help="Build index.jsonl from markdown source files")
    ap_build.add_argument("--src-dir", default=str(DEFAULT_SRC_DIR))
    ap_build.add_argument("--index", default=str(DEFAULT_INDEX_PATH))

    ap_q = sub.add_parser("q", help="Query a verse by book/abbr + chapter + verse")
    ap_q.add_argument("--index", default=str(DEFAULT_INDEX_PATH))
    ap_q.add_argument("--book", required=True, help="Book name (e.g. 列王纪上) or abbreviation (e.g. 王上)")
    ap_q.add_argument("--chapter", type=int, required=True)
    ap_q.add_argument("--verse", type=int, required=True)
    ap_q.add_argument("--json", action="store_true", help="Output raw JSON")

    args = ap.parse_args(argv)

    if args.cmd == "build":
        src_dir = Path(args.src_dir)
        index_path = Path(args.index)
        if not src_dir.exists():
            raise SystemExit(f"Missing src dir: {src_dir}")
        n, book_to_abbr = build_index(src_dir, index_path)
        print(f"indexed_verses={n}")
        print(f"index_path={index_path}")
        # show a small mapping sample
        sample = list(book_to_abbr.items())[:10]
        if sample:
            print("book_abbr_sample=" + ", ".join([f"{b}:{a}" for b, a in sample]))
        return 0

    if args.cmd == "q":
        index_path = Path(args.index)
        if not index_path.exists():
            raise SystemExit(f"Missing index. Build it first: {index_path}")
        row = query(index_path, args.book, args.chapter, args.verse)
        if row is None:
            print("NOT_FOUND")
            return 2
        if args.json:
            print(json.dumps(row, ensure_ascii=False))
            return 0
        ref = f"{row.get('book')} {row.get('abbr')}{row.get('chapter')}:{row.get('verse')}"
        print(ref)
        if row.get("en"):
            print(row["en"])
        if row.get("zh"):
            print(row["zh"])
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())

