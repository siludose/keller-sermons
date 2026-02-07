#!/usr/bin/env python3
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sermon", required=True, help="Sermon filename, e.g. Jesus_Our_Gift.md")
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[3]  # .../skills/public/keller-cuv-rewrite/scripts -> repo root
    chunks_dir = repo / "_chunks" / args.sermon
    if not chunks_dir.exists():
        raise SystemExit(f"Missing chunks dir: {chunks_dir}")

    zh_files = sorted(chunks_dir.glob("*.zh.txt"), key=lambda p: int(p.stem.split(".")[0]))
    if not zh_files:
        raise SystemExit("No zh chunks found")

    zh_text = "\n\n".join([p.read_text(encoding="utf-8").rstrip() for p in zh_files]).strip() + "\n"

    sermon_path = repo / args.sermon
    content = sermon_path.read_text(encoding="utf-8")

    header = "\n\n---\n\n## Chinese Transcript / 中文\n\n"
    if "## Chinese Transcript / 中文" in content:
        before = content.split("## Chinese Transcript / 中文", 1)[0]
        content = before.rstrip() + header + zh_text
    else:
        content = content.rstrip() + header + zh_text

    sermon_path.write_text(content, encoding="utf-8")
    print(f"Updated {sermon_path} with {len(zh_files)} zh chunks")

if __name__ == "__main__":
    main()
