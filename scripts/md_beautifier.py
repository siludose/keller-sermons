#!/usr/bin/env python3
"""
Markdown Beautifier
Standardizes formatting for sermon outlines, transcripts, and translations.
"""

import re
from typing import List


def beautify_outline(text: str) -> str:
    """
    Format outline with consistent hierarchy:
    - Main points: 1., 2., 3.
    - Sub-points: -
    - Proper indentation
    """
    if not text.strip():
        return text

    lines = text.split('\n')
    formatted_lines = []
    current_number = 1

    for line in lines:
        stripped = line.strip()

        # Skip empty lines
        if not stripped:
            formatted_lines.append('')
            continue

        # Detect main points (various formats)
        # Formats: "I.", "1.", "A.", "First,", etc.
        is_main_point = bool(re.match(r'^([IVX]+\.|[0-9]+\.|[A-Z]\.|\*\*[IVX]+\.|First|Second|Third|Fourth|Fifth)', stripped))

        if is_main_point:
            # Normalize to numbered format
            # Remove existing numbering
            content = re.sub(r'^([IVX]+\.|[0-9]+\.|[A-Z]\.|\*\*[IVX]+\.?\*\*|First|Second|Third|Fourth|Fifth)[:\s]*', '', stripped)
            formatted_lines.append(f"{current_number}. {content}")
            current_number += 1
        else:
            # Sub-point or continued text
            if stripped.startswith('-') or stripped.startswith('*'):
                # Already a bullet, clean it up
                content = re.sub(r'^[-*]\s*', '', stripped)
                formatted_lines.append(f"   - {content}")
            elif re.match(r'^[a-z]\.|^\([a-z]\)', stripped):
                # Sub-numbering like "a.", "(a)"
                content = re.sub(r'^[a-z]\.|^\([a-z]\)\s*', '', stripped)
                formatted_lines.append(f"   - {content}")
            else:
                # Continuation of previous point
                # Check if previous line was a main point
                if formatted_lines and re.match(r'^[0-9]+\.', formatted_lines[-1]):
                    formatted_lines.append(f"   {stripped}")
                elif formatted_lines and formatted_lines[-1].strip().startswith('-'):
                    formatted_lines.append(f"     {stripped}")
                else:
                    formatted_lines.append(f"   {stripped}")

    # Clean up excessive blank lines (max 2 consecutive)
    result = '\n'.join(formatted_lines)
    result = re.sub(r'\n{3,}', '\n\n', result)

    return result.strip()


def beautify_transcript(text: str) -> str:
    """
    Format transcript for readability:
    - Paragraph breaks every 3-4 sentences
    - Proper spacing around quotes
    - Block quotes for Scripture
    """
    if not text.strip():
        return text

    # Normalize line breaks
    text = re.sub(r'\r\n', '\n', text)

    # Remove excessive whitespace
    text = re.sub(r' +', ' ', text)

    # Ensure proper spacing after punctuation
    text = re.sub(r'([.!?])([A-Z])', r'\1 \2', text)

    # Format block quotes (Scripture or extended quotes)
    # Pattern: Scripture references followed by colon
    text = re.sub(
        r'\n([A-Z][a-z]+ \d+:\d+(?:-\d+)?:)\s*',
        r'\n\n> **\1**\n> ',
        text
    )

    # Add paragraph breaks (every 3-4 sentences)
    paragraphs = []
    sentences = re.split(r'([.!?])\s+', text)

    current_para = ""
    sentence_count = 0

    for i in range(0, len(sentences) - 1, 2):
        sentence = sentences[i] + sentences[i + 1]
        current_para += sentence + " "
        sentence_count += 1

        # Break paragraph every 3-4 sentences or at natural breaks
        if sentence_count >= 3 or i + 2 >= len(sentences):
            paragraphs.append(current_para.strip())
            current_para = ""
            sentence_count = 0

    # Handle last sentence if any
    if current_para.strip():
        paragraphs.append(current_para.strip())

    result = '\n\n'.join(paragraphs)

    # Clean up excessive blank lines
    result = re.sub(r'\n{3,}', '\n\n', result)

    return result.strip()


def beautify_translation(text: str) -> str:
    """
    Format Chinese translation:
    - Use Chinese punctuation (。，！？)
    - Proper spacing around quotes
    - Paragraph breaks similar to English
    """
    if not text.strip():
        return text

    # Normalize line breaks
    text = re.sub(r'\r\n', '\n', text)

    # Convert English punctuation to Chinese where appropriate
    # Only convert in Chinese context (surrounded by Chinese characters)
    def has_chinese(s):
        return bool(re.search(r'[\u4e00-\u9fff]', s))

    lines = text.split('\n')
    formatted_lines = []

    for line in lines:
        if has_chinese(line):
            # Convert punctuation
            line = line.replace('.', '。')
            line = line.replace(',', '，')
            line = line.replace('!', '！')
            line = line.replace('?', '？')
            line = line.replace(':', '：')
            line = line.replace(';', '；')

            # But preserve English punctuation in English words/phrases
            # Revert punctuation after English words
            line = re.sub(r'([a-zA-Z])。', r'\1.', line)
            line = re.sub(r'([a-zA-Z])，', r'\1,', line)

        formatted_lines.append(line)

    text = '\n'.join(formatted_lines)

    # Remove excessive whitespace
    text = re.sub(r' +', ' ', text)

    # Paragraph spacing (Chinese typically has slightly different rhythm)
    # Look for sentence-final punctuation followed by Chinese character
    text = re.sub(r'([。！？])\s*([^》\n])', r'\1\n\n\2', text)

    # Clean up excessive blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def format_scripture_refs(text: str) -> str:
    """
    Standardize Scripture reference formatting.

    Formats:
    - Book Chapter:Verse -> *Book Chapter:Verse*
    - Adds italics for clarity
    """
    # Common Bible book names (English)
    books = [
        'Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy',
        'Joshua', 'Judges', 'Ruth', '1 Samuel', '2 Samuel',
        '1 Kings', '2 Kings', '1 Chronicles', '2 Chronicles',
        'Ezra', 'Nehemiah', 'Esther', 'Job', 'Psalms', 'Proverbs',
        'Ecclesiastes', 'Song of Solomon', 'Isaiah', 'Jeremiah',
        'Lamentations', 'Ezekiel', 'Daniel', 'Hosea', 'Joel',
        'Amos', 'Obadiah', 'Jonah', 'Micah', 'Nahum', 'Habakkuk',
        'Zephaniah', 'Haggai', 'Zechariah', 'Malachi',
        'Matthew', 'Mark', 'Luke', 'John', 'Acts', 'Romans',
        '1 Corinthians', '2 Corinthians', 'Galatians', 'Ephesians',
        'Philippians', 'Colossians', '1 Thessalonians', '2 Thessalonians',
        '1 Timothy', '2 Timothy', 'Titus', 'Philemon', 'Hebrews',
        'James', '1 Peter', '2 Peter', '1 John', '2 John', '3 John',
        'Jude', 'Revelation'
    ]

    # Create pattern for all books
    books_pattern = '|'.join(re.escape(book) for book in books)

    # Pattern: BookName Chapter:Verse or BookName Chapter:Verse-Verse
    pattern = rf'\b({books_pattern})\s+(\d+):(\d+(?:-\d+)?)\b'

    # Replace with italicized version if not already formatted
    def replace_ref(match):
        ref = match.group(0)
        # Check if already in markdown (*, **, _, etc.)
        if match.start() > 0 and text[match.start() - 1] in ['*', '_']:
            return ref
        return f"*{ref}*"

    return re.sub(pattern, replace_ref, text)


def beautify_all(
    outline: str,
    transcript: str,
    translation: str
) -> tuple[str, str, str]:
    """
    Beautify all sermon components at once.
    Returns (beautified_outline, beautified_transcript, beautified_translation)
    """
    return (
        beautify_outline(outline),
        beautify_transcript(transcript),
        beautify_translation(translation)
    )


def main():
    """CLI for testing beautifier"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python md_beautifier.py <outline|transcript|translation> <input_file>")
        print("\nExample:")
        print("  python md_beautifier.py outline sample_outline.txt")
        sys.exit(1)

    mode = sys.argv[1]
    input_file = sys.argv[2]

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()

        if mode == 'outline':
            result = beautify_outline(content)
        elif mode == 'transcript':
            result = beautify_transcript(content)
        elif mode == 'translation':
            result = beautify_translation(content)
        else:
            print(f"Unknown mode: {mode}")
            sys.exit(1)

        print(result)

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
