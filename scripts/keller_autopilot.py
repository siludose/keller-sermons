#!/usr/bin/env python3
"""keller_autopilot.py

A small, *idempotent* helper for the keller-sermons repo.

What it does (safe, deterministic):
- Scan repo for unfinished chunk directories under _chunks/
- For COMPLETE chunk dirs: stitch *.zh.txt into the target *.md Chinese section
- For INCOMPLETE chunk dirs: report missing chunk numbers
- For eligible *.md without a chunk dir: create chunks (000.en.txt + 001..NNN.en.txt)

What it does NOT do:
- Call LLM APIs. (Translation is done by OpenClaw subagents.)

This design keeps the script reliable and easy to run from OpenClaw cron/exec.

Usage:
  python3 scripts/keller_autopilot.py status
  python3 scripts/keller_autopilot.py chunk-next
  python3 scripts/keller_autopilot.py stitch-ready
  python3 scripts/keller_autopilot.py plan  # prints JSON plan

Exit codes:
  0 = ok
  2 = nothing to do
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
CHUNKS_ROOT = REPO_ROOT / "_chunks"

CJK_RE = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]")

EN_SECTION_PATTERNS = [
    # common format
    re.compile(r"### English Transcript \(for reference\)\n\n(.*?)\n\n### 中文翻译\n", re.S),
    # some files use bilingual header
    re.compile(r"## English Transcript / 英文原文\n\n(.*)\Z", re.S),
    re.compile(r"## English Transcript / 英文原文\n\n(.*?)\n\n## ", re.S),
]

CN_SECTION_PATTERNS = [
    (re.compile(r"(### 中文翻译\n\n)(.*)\Z", re.S), "### 中文翻译"),
    (re.compile(r"(## Chinese Translation / 中文翻译\n\n)(.*)\Z", re.S), "## Chinese Translation / 中文翻译"),
]


def run(cmd: list[str], cwd: Optional[Path] = None) -> str:
    return subprocess.check_output(cmd, cwd=str(cwd or REPO_ROOT), text=True).strip()


def chinese_ratio(text: str) -> float:
    cn = len(CJK_RE.findall(text))
    total = len(re.findall(r"\S", text))
    return (cn / total) if total else 0.0


def split_text(text: str, maxlen: int = 2200) -> list[str]:
    text = text.strip()
    parts: list[str] = []
    i = 0
    while i < len(text):
        end = min(len(text), i + maxlen)
        if end < len(text):
            back = end
            while back > i and not text[back - 1].isspace():
                back -= 1
            if back == i:
                back = end
            end = back
        parts.append(text[i:end].strip())
        i = end
    return [p for p in parts if p]


def num_from_filename(name: str) -> Optional[int]:
    m = re.match(r"^(\d{3})\.(?:en|zh)\.txt$", name)
    return int(m.group(1)) if m else None


@dataclass
class ChunkDirStatus:
    name: str
    path: Path
    en_count: int
    zh_count: int
    missing: list[int]

    @property
    def complete(self) -> bool:
        return self.en_count > 0 and self.zh_count == self.en_count and not self.missing


def scan_chunk_dirs() -> list[ChunkDirStatus]:
    out: list[ChunkDirStatus] = []
    if not CHUNKS_ROOT.exists():
        return out

    for d in sorted([p for p in CHUNKS_ROOT.iterdir() if p.is_dir()], key=lambda p: p.name):
        en_files = sorted(d.glob("*.en.txt"))
        zh_files = sorted(d.glob("*.zh.txt"))
        en_nums = {n for n in (num_from_filename(p.name) for p in en_files) if n is not None}
        zh_nums = {n for n in (num_from_filename(p.name) for p in zh_files) if n is not None}
        missing = sorted(list(en_nums - zh_nums))
        out.append(
            ChunkDirStatus(
                name=d.name,
                path=d,
                en_count=len(en_nums),
                zh_count=len(zh_nums),
                missing=missing,
            )
        )
    return out


def extract_english(md_path: Path) -> Optional[str]:
    text = md_path.read_text(encoding="utf-8", errors="ignore")
    for pat in EN_SECTION_PATTERNS:
        m = pat.search(text)
        if m:
            return m.group(1).strip()
    return None


def ensure_chunk_dir(md_path: Path) -> tuple[Path, int]:
    """Create _chunks/<mdfilename>/000.en.txt + 001..NNN.en.txt; return (dir, NNN)."""
    english = extract_english(md_path)
    if not english:
        raise RuntimeError(f"No English transcript section found in {md_path.name}")

    d = CHUNKS_ROOT / md_path.name
    d.mkdir(parents=True, exist_ok=True)

    (d / "000.en.txt").write_text(english.strip() + "\n", encoding="utf-8")
    parts = split_text(english, maxlen=2200)
    for idx, part in enumerate(parts, 1):
        (d / f"{idx:03d}.en.txt").write_text(part + "\n", encoding="utf-8")

    return d, len(parts)


def stitch_into_md(md_path: Path, chunk_dir: Path) -> int:
    """Stitch all zh chunks into md Chinese section. Returns stitched length."""
    zh_files = sorted(chunk_dir.glob("*.zh.txt"), key=lambda p: int(p.stem.split(".")[0]))
    pieces: list[str] = []
    for p in zh_files:
        t = p.read_text(encoding="utf-8", errors="ignore").strip()
        if t:
            pieces.append(t)
    full = "\n\n".join(pieces).strip() + "\n"

    src = md_path.read_text(encoding="utf-8", errors="ignore")

    replaced = False
    for pat, _hdr in CN_SECTION_PATTERNS:
        if pat.search(src):
            src = pat.sub(lambda m: m.group(1) + full, src)
            replaced = True
            break

    if not replaced:
        # If the file uses the common format, append a Chinese section.
        src = src.rstrip() + "\n\n### 中文翻译\n\n" + full

    md_path.write_text(src, encoding="utf-8")
    return len(full)


def find_next_md_without_chunks(low_ratio_only: bool = True) -> Optional[Path]:
    mds = sorted(REPO_ROOT.glob("*.md"))
    for p in mds:
        if low_ratio_only:
            try:
                ratio = chinese_ratio(p.read_text(encoding="utf-8", errors="ignore"))
            except Exception:
                continue
            if ratio >= 0.10:
                continue
        if (CHUNKS_ROOT / p.name).exists():
            continue
        # Only process if we can find English transcript
        if extract_english(p):
            return p
    return None


def git_has_changes(paths: list[Path]) -> bool:
    if not paths:
        return False
    args = ["git", "diff", "--name-only", "--"] + [str(p) for p in paths]
    out = run(args)
    return bool(out.strip())


def git_commit_push(md_path: Path, message: str) -> None:
    # Idempotent: only commit if there is an actual diff.
    if not git_has_changes([md_path]):
        return
    run(["git", "add", str(md_path)])
    # commit may fail if identical staged content; ignore.
    try:
        run(["git", "commit", "-m", message])
    except subprocess.CalledProcessError:
        return
    run(["git", "push"])


def cmd_status(_args: argparse.Namespace) -> int:
    dirs = scan_chunk_dirs()
    incomplete = [d for d in dirs if d.en_count and not d.complete]
    complete = [d for d in dirs if d.complete]

    low = []
    for p in sorted(REPO_ROOT.glob("*.md")):
        ratio = chinese_ratio(p.read_text(encoding="utf-8", errors="ignore"))
        if ratio < 0.10:
            low.append((ratio, p.name))

    print(f"chunks: {len(dirs)} (complete {len(complete)}, incomplete {len(incomplete)})")
    if incomplete:
        for d in incomplete[:20]:
            print(f"- {d.name}: {d.zh_count}/{d.en_count} missing={d.missing[:10]}")
    print(f"md<10%: {len(low)}")
    if low:
        for r, name in sorted(low)[:10]:
            print(f"- {name} {r:.2%}")
    return 0


def cmd_chunk_next(_args: argparse.Namespace) -> int:
    md = find_next_md_without_chunks(low_ratio_only=True)
    if not md:
        print("nothing")
        return 2
    d, n = ensure_chunk_dir(md)
    print(f"created {d} with {n} chunks")
    return 0


def cmd_stitch_ready(_args: argparse.Namespace) -> int:
    dirs = scan_chunk_dirs()
    ready = [d for d in dirs if d.complete]
    if not ready:
        print("nothing")
        return 2

    stitched_any = False
    for d in ready:
        md_path = REPO_ROOT / d.name
        if not md_path.exists():
            continue
        before = md_path.read_text(encoding="utf-8", errors="ignore")
        stitch_into_md(md_path, d.path)
        after = md_path.read_text(encoding="utf-8", errors="ignore")
        if before != after:
            stitched_any = True
            # Commit message uses basename without extension for readability.
            title = md_path.stem.replace("_", " ")
            git_commit_push(md_path, f"Add full Chinese translation: {title}")

    if not stitched_any:
        print("nothing")
        return 2
    print("ok")
    return 0


def cmd_plan(_args: argparse.Namespace) -> int:
    dirs = scan_chunk_dirs()

    to_stitch = [d.name for d in dirs if d.complete]
    to_translate = []
    for d in dirs:
        if d.en_count and not d.complete:
            for n in d.missing:
                to_translate.append({"file": d.name, "chunk": f"{n:03d}"})

    next_md = find_next_md_without_chunks(low_ratio_only=True)
    plan = {
        "stitch_ready": to_stitch,
        "translate_missing": to_translate,
        "chunk_next": next_md.name if next_md else None,
    }
    print(json.dumps(plan, ensure_ascii=False, indent=2))
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status")
    sub.add_parser("chunk-next")
    sub.add_parser("stitch-ready")
    sub.add_parser("plan")

    args = parser.parse_args(argv)

    os.chdir(REPO_ROOT)

    if args.cmd == "status":
        return cmd_status(args)
    if args.cmd == "chunk-next":
        return cmd_chunk_next(args)
    if args.cmd == "stitch-ready":
        return cmd_stitch_ready(args)
    if args.cmd == "plan":
        return cmd_plan(args)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
