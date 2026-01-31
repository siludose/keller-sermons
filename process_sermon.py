#!/usr/bin/env python3
"""Process Tim Keller sermons: download, transcribe, translate, and generate markdown."""

import os
import json
import sys
import requests
from pathlib import Path

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
SERMONS_DIR = Path("/home/node/clawd/keller_sermons")

def download_audio(url: str, filename: str) -> Path:
    """Download audio file."""
    filepath = SERMONS_DIR / filename
    if filepath.exists():
        print(f"Audio already exists: {filename}")
        return filepath
    
    print(f"Downloading: {url}")
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    with open(filepath, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    print(f"Downloaded: {filename}")
    return filepath

def transcribe_audio(filepath: Path) -> str:
    """Transcribe audio using OpenAI Whisper API."""
    print(f"Transcribing: {filepath.name}")
    
    with open(filepath, 'rb') as audio_file:
        response = requests.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            files={"file": audio_file},
            data={"model": "whisper-1", "language": "en"}
        )
    
    response.raise_for_status()
    transcript = response.json()["text"]
    print(f"Transcription complete: {len(transcript)} characters")
    return transcript

def translate_and_analyze(title: str, date: str, transcript: str) -> dict:
    """Translate and analyze sermon using GPT-4."""
    print(f"Translating and analyzing: {title}")
    
    prompt = f"""You are translating a Tim Keller sermon. 

Title: {title}
Date: {date}

Here is the full English transcript:
{transcript}

Please provide:
1. Chinese translation of the title
2. Scripture references mentioned (if any)
3. A sermon outline with main points (in both English and Chinese)
4. Full Chinese translation of the transcript

Respond in JSON format:
{{
    "title_cn": "中文标题",
    "scripture_refs": ["经文引用1", "经文引用2"],
    "outline": [
        {{"en": "Point 1 in English", "cn": "要点1中文"}},
        {{"en": "Point 2 in English", "cn": "要点2中文"}}
    ],
    "transcript_cn": "完整中文翻译..."
}}"""

    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "response_format": {"type": "json_object"}
        }
    )
    
    response.raise_for_status()
    result = response.json()["choices"][0]["message"]["content"]
    print("Translation complete")
    return json.loads(result)

def generate_markdown(title: str, date: str, transcript_en: str, analysis: dict) -> str:
    """Generate markdown file content."""
    
    outline_md = ""
    for i, point in enumerate(analysis.get("outline", []), 1):
        outline_md += f"{i}. {point.get('en', '')}\n   {point.get('cn', '')}\n"
    
    scripture = ", ".join(analysis.get("scripture_refs", [])) or "Not specified"
    
    md = f"""# {title}
# {analysis.get('title_cn', title)}

**Date / 日期:** {date}

**Scripture References / 经文引用:** {scripture}

---

## Sermon Outline / 讲道大纲

{outline_md}

---

## Full Transcript / 完整文本

### English

{transcript_en}

---

### 中文翻译

{analysis.get('transcript_cn', '翻译处理中...')}
"""
    return md

def process_episode(episode: dict) -> bool:
    """Process a single episode."""
    title = episode["title"]
    date = episode["date"]
    audio_url = episode["audio_url"]
    
    # Generate safe filename
    safe_title = "".join(c if c.isalnum() or c in " -_" else "" for c in title)
    safe_title = safe_title.replace(" ", "_")
    
    audio_filename = f"{safe_title}.mp3"
    if audio_url.endswith(".m4a"):
        audio_filename = f"{safe_title}.m4a"
    
    md_filename = f"{safe_title}.md"
    md_path = SERMONS_DIR / md_filename
    
    # Skip if already processed
    if md_path.exists():
        print(f"Already processed: {title}")
        return True
    
    try:
        # Step 1: Download
        audio_path = download_audio(audio_url, audio_filename)
        
        # Step 2: Transcribe
        transcript_en = transcribe_audio(audio_path)
        
        # Step 3: Translate and analyze
        analysis = translate_and_analyze(title, date, transcript_en)
        
        # Step 4: Generate and save markdown
        markdown = generate_markdown(title, date, transcript_en, analysis)
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(markdown)
        
        print(f"✅ Saved: {md_filename}")
        
        # Optional: remove audio to save space
        # audio_path.unlink()
        
        return True
        
    except Exception as e:
        print(f"❌ Error processing {title}: {e}")
        return False

def main():
    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY not set")
        sys.exit(1)
    
    # Read episodes
    with open("/tmp/keller_episodes.json", "r") as f:
        episodes = json.load(f)
    
    # Process first 10
    episodes = episodes[:10]
    
    success = 0
    failed = 0
    
    for i, episode in enumerate(episodes, 1):
        print(f"\n{'='*60}")
        print(f"Processing {i}/10: {episode['title']}")
        print(f"{'='*60}")
        
        if process_episode(episode):
            success += 1
        else:
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"Complete! Success: {success}, Failed: {failed}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
