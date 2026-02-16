#!/usr/bin/env python3
"""
transcribe_whisper.py - 使用 faster-whisper large-v3 转录讲道音频
"""
import sys
import os
from pathlib import Path

try:
    from faster_whisper import WhisperModel
except ImportError:
    print("❌ faster-whisper not installed: pip3 install faster-whisper")
    sys.exit(1)

BASE_DIR = Path(__file__).parent.parent
DOWNLOADS_DIR = BASE_DIR / "downloads"

# 6 个需要转录的讲道
SERMONS = [
    "Admitting",
    "The_Glory_of_the_Incarnation",
    "Radical_Generosity",
    "Seeking_the_Kingdom",
    "Thy_Will_Be_Done",
    "The_Power_of_the_Incarnation",
]


def transcribe_sermon(model, sermon_name: str) -> str:
    """Transcribe a single sermon, return full text."""
    mp3_path = DOWNLOADS_DIR / f"{sermon_name}.mp3"
    if not mp3_path.exists():
        print(f"  ❌ {mp3_path} not found")
        return ""

    print(f"  🎙️  Transcribing {sermon_name}...")
    segments, info = model.transcribe(
        str(mp3_path),
        language="en",
        beam_size=5,
        vad_filter=True,  # Filter out silence
    )

    text_parts = []
    for segment in segments:
        text_parts.append(segment.text.strip())

    full_text = " ".join(text_parts)
    print(f"  ✅ {sermon_name}: {len(full_text):,} chars")
    return full_text


def main():
    print("📥 Loading faster-whisper large-v3 model...")
    print("   (First run will download ~3GB model)")
    model = WhisperModel("large-v3", device="cpu", compute_type="int8")
    print("✅ Model loaded\n")

    for sermon_name in SERMONS:
        text = transcribe_sermon(model, sermon_name)
        if not text:
            continue

        # Write to output txt file
        out_path = DOWNLOADS_DIR / f"{sermon_name}.txt"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"  📝 Saved: {out_path}\n")

    print("🎉 All done!")


if __name__ == "__main__":
    main()
