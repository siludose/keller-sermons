#!/usr/bin/env python3
"""
Translate Tim Keller sermon transcripts to Chinese using OpenAI GPT-4o
"""

import os
import sys
import json
from openai import OpenAI

client = OpenAI()

def extract_outline_and_scriptures(text: str) -> dict:
    """Extract sermon outline and scripture references"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": """You are an expert in analyzing Christian sermons. Extract:
1. A sermon outline with 6-8 main points (in English)
2. All scripture references mentioned in the sermon

Return JSON format:
{
  "outline": ["Point 1", "Point 2", ...],
  "scriptures": ["Book Chapter:Verse", ...]
}"""
            },
            {
                "role": "user", 
                "content": f"Analyze this Tim Keller sermon transcript:\n\n{text[:15000]}"
            }
        ],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)

def translate_outline(outline: list) -> list:
    """Translate outline points to Chinese"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "Translate the following sermon outline points to Chinese. Return JSON array with translations."
            },
            {
                "role": "user",
                "content": json.dumps(outline)
            }
        ],
        response_format={"type": "json_object"}
    )
    result = json.loads(response.choices[0].message.content)
    return result.get("translations", result.get("outline", list(result.values())[0] if result else []))

def translate_chunk(text: str, chunk_num: int, total_chunks: int) -> str:
    """Translate a chunk of text to Chinese"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": """You are translating a Tim Keller sermon transcript to Chinese.
- Maintain the spiritual and theological depth
- Use appropriate Christian terminology in Chinese
- Keep the conversational tone of the sermon
- Translate naturally, not word-for-word"""
            },
            {
                "role": "user",
                "content": f"Translate this sermon transcript section ({chunk_num}/{total_chunks}) to Chinese:\n\n{text}"
            }
        ]
    )
    return response.choices[0].message.content

def process_sermon(input_file: str, output_file: str, title: str, chinese_title: str, date: str):
    """Process a single sermon file"""
    print(f"Processing: {title}")
    
    # Read transcript
    with open(input_file, 'r', encoding='utf-8') as f:
        transcript = f.read()
    
    # Clean transcript - remove podcast intro/outro
    lines = transcript.split('\n')
    clean_lines = []
    for line in lines:
        if 'gospelandlife.com' in line.lower():
            continue
        if 'monthly partner' in line.lower() and len(line) < 200:
            continue
        clean_lines.append(line)
    transcript = '\n'.join(clean_lines)
    
    print("  Extracting outline and scriptures...")
    analysis = extract_outline_and_scriptures(transcript)
    outline = analysis.get("outline", [])
    scriptures = analysis.get("scriptures", [])
    
    print("  Translating outline...")
    outline_cn = translate_outline(outline)
    
    # Split transcript into chunks for translation (roughly 8000 chars each)
    chunk_size = 8000
    chunks = []
    current = ""
    for para in transcript.split('\n\n'):
        if len(current) + len(para) > chunk_size:
            if current:
                chunks.append(current)
            current = para
        else:
            current = current + '\n\n' + para if current else para
    if current:
        chunks.append(current)
    
    print(f"  Translating {len(chunks)} chunks...")
    translated_chunks = []
    for i, chunk in enumerate(chunks):
        print(f"    Chunk {i+1}/{len(chunks)}...")
        translated = translate_chunk(chunk, i+1, len(chunks))
        translated_chunks.append(translated)
    
    chinese_translation = '\n\n'.join(translated_chunks)
    
    # Build markdown
    md = f"""# {title}
# {chinese_title}

**Date / 日期:** {date}

**Scripture References / 经文引用:** {', '.join(scriptures)}

---

## Sermon Outline / 讲道大纲

"""
    
    for i, (en, cn) in enumerate(zip(outline, outline_cn), 1):
        md += f"{i}. {en}\n   {cn}\n\n"
    
    md += """---

## Full Transcript / 完整文本

### English

"""
    md += transcript
    
    md += """

---

### 中文翻译

"""
    md += chinese_translation
    
    # Write output
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(md)
    
    file_size = os.path.getsize(output_file)
    print(f"  Done! Output: {output_file} ({file_size / 1024:.1f}KB)")
    return file_size

if __name__ == "__main__":
    if len(sys.argv) != 6:
        print("Usage: python translate_sermon.py <input> <output> <title> <chinese_title> <date>")
        sys.exit(1)
    
    input_file, output_file, title, chinese_title, date = sys.argv[1:6]
    process_sermon(input_file, output_file, title, chinese_title, date)
