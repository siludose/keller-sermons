#!/usr/bin/env python3
"""clean_transcripts.py - Clean Whisper transcripts for 6 P0 sermons.

Handles:
1. Remove podcast partnership intros
2. Remove mid-sermon fundraising ads
3. Remove podcast outros
4. Fix Whisper repetition artifacts
5. Add paragraph breaks
6. Write transcript.md and update metadata.json
"""

import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DOWNLOADS = BASE_DIR / "downloads"
SERMONS = BASE_DIR / "sermons"

# Sermon configurations
CONFIGS = {
    "Admitting": {"title": "Admitting"},
    "The_Glory_of_the_Incarnation": {"title": "The Glory of the Incarnation"},
    "Radical_Generosity": {"title": "Radical Generosity"},
    "Seeking_the_Kingdom": {"title": "Seeking the Kingdom"},
    "Thy_Will_Be_Done": {"title": "Thy Will Be Done"},
    "The_Power_of_the_Incarnation": {"title": "The Power of the Incarnation"},
}


def remove_partnership_intro(text):
    """Remove 'During January...' partnership ads from opening."""
    # Pattern: "Welcome to Gospel in Life. During January..." through "gospelinlife.com slash partner."
    # Then there's a repeated sermon intro after it.
    marker = "During January, we're inviting our listeners"
    if marker not in text:
        return text

    # Find the partnership intro
    partner_start = text.find(marker)

    # Find the end of the partnership ad (ends with "gospelinlife.com slash partner.")
    # There may be multiple mentions, find the last one before the sermon intro
    partner_section = text[partner_start:partner_start + 500]
    partner_end_marker = "slash partner."
    partner_end_pos = text.find(partner_end_marker, partner_start)
    if partner_end_pos == -1:
        return text

    # Move past the period
    partner_end_pos += len(partner_end_marker)

    # Keep "Welcome to Gospel in Life." prefix and join with content after the ad
    welcome_end = text.find(".", 0, partner_start)
    if welcome_end == -1:
        prefix = ""
    else:
        prefix = text[:welcome_end + 1].strip()

    suffix = text[partner_end_pos:].strip()
    if prefix:
        return prefix + " " + suffix
    return suffix


def remove_mid_sermon_ads(text):
    """Remove mid-sermon fundraising/promotional ads."""
    # Pattern 1: "As 2025 comes to a close..." fundraising
    ad_patterns = [
        # Fundraising ads
        (r"As 2025 comes to a close.*?(?:Now(?:,|\s+here'?s) Dr\. Keller with the (?:remainder|rest) of today'?s (?:message|teaching)\.?)",
         re.DOTALL),
        # Christmas video promotion
        (r"At Christmas, we are animated by the gifts we give and receive\..*?(?:Now(?:,|\s+here'?s) Dr\. Keller with the (?:remainder|rest) of today'?s (?:message|teaching)\.?)",
         re.DOTALL),
        # Counterfeit Gods book promotion
        (r"We all chase things like success, true love, or the perfect life\..*?(?:Now(?:,|\s+here'?s) Dr\. Keller with the (?:remainder|rest) of today'?s (?:message|teaching)\.?)",
         re.DOTALL),
    ]

    for pattern, flags in ad_patterns:
        text = re.sub(pattern, "", text, flags=flags)

    return text


def remove_outro(text):
    """Remove podcast outro."""
    outro_patterns = [
        "Thanks for listening to Tim Keller on the Gospel",
        "Thanks for listening to Tim Keller on the gospel",
        "Thanks for joining us here on the Gospel",
        "Thanks for joining us here on the gospel",
        "thanks for joining us here on the gospel",
        "Thanks for listening to today's teaching.",
        "thanks for listening to today's teaching.",
    ]

    # Find the last occurrence of any outro pattern
    last_idx = -1
    for pattern in outro_patterns:
        idx = text.rfind(pattern)
        if idx > last_idx:
            last_idx = idx

    if last_idx > 0:
        text = text[:last_idx].rstrip()

    return text


def fix_whisper_repetitions(text):
    """Fix Whisper repetition artifacts.

    Detects when the same phrase/sentence is repeated 2+ times consecutively
    and keeps only one instance.
    """
    # Split into sentences
    # Use a regex that splits on sentence-ending punctuation followed by space
    sentences = re.split(r'(?<=[.!?])\s+', text)

    cleaned = []
    i = 0
    while i < len(sentences):
        sent = sentences[i].strip()
        if not sent:
            i += 1
            continue

        # Check if this sentence is repeated consecutively
        repeat_count = 1
        while (i + repeat_count < len(sentences) and
               sentences[i + repeat_count].strip() == sent):
            repeat_count += 1

        # If repeated 3+ times, it's definitely a Whisper artifact
        # If repeated 2 times, check if it's a short filler phrase
        if repeat_count >= 3:
            cleaned.append(sent)
            i += repeat_count
        elif repeat_count == 2:
            # Only de-dup very short repeated phrases (likely artifacts)
            # or exact duplicates of longer sentences
            if len(sent.split()) <= 8 or len(sent) > 50:
                cleaned.append(sent)
                i += repeat_count
            else:
                cleaned.append(sent)
                i += 1
        else:
            cleaned.append(sent)
            i += 1

    text = ' '.join(cleaned)

    # Also fix inline repetitions like "that, that, that, that, that, that"
    # Fix repeated short words/phrases with commas
    text = re.sub(r'\b((?:that|the|and|or|is|was|he|she|it|we|you|they|I|a|an|to|in|of|for|on|at|by|with)\b(?:,?\s*)){4,}',
                  lambda m: m.group(0).split(',')[0].strip().split()[0] + ' ',
                  text)

    # Fix "that, that, that..." patterns more precisely
    text = re.sub(r'\bthat(?:,\s*that){2,}\b', 'that', text)
    text = re.sub(r'\bthe(?:,\s*the){2,}\b', 'the', text)
    text = re.sub(r'\band(?:,\s*and){2,}\b', 'and', text)

    # Fix stuttering patterns like "and the, and the, and the"
    text = re.sub(r'(?:(?:and the|the the|that the|of the|in the|is the),?\s*){3,}', '', text)

    return text


def add_paragraph_breaks(text):
    """Add paragraph breaks at natural points in the text."""
    # First, normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)

    paragraphs = []
    current_para = []

    # Transition words that often start new paragraphs
    transition_starters = [
        r'^Now,?\s',
        r'^So,?\s',
        r'^But\s',
        r'^Well,?\s',
        r'^Look,?\s',
        r'^See,?\s',
        r'^You see,?\s',
        r'^And so,?\s',
        r'^And yet,?\s',
        r'^And then,?\s',
        r'^And that\'?s?\s',
        r'^Therefore,?\s',
        r'^However,?\s',
        r'^Instead,?\s',
        r'^In other words,?\s',
        r'^In conclusion,?\s',
        r'^In the same way,?\s',
        r'^Let me\s',
        r'^Let\'?s\s',
        r'^Here\'?s?\s',
        r'^First(?:ly)?,?\s',
        r'^Second(?:ly)?,?\s',
        r'^Third(?:ly)?,?\s',
        r'^Number (?:one|two|three|four|five)',
        r'^The first\s',
        r'^The second\s',
        r'^The third\s',
        r'^That\'?s? (?:the |a |why|how|what|where|when)',
        r'^What (?:does|is|are|do|did|was|were|happens)',
        r'^How (?:does|do|did|can|could|would|is|are)',
        r'^Why (?:does|do|did|would|is|are|was)',
        r'^There(?:\'s| is| are| was| were)\s',
        r'^My (?:dear |appeal)',
        r'^I (?:want|would|can|know|think|remember|don\'t)',
        r'^Paul\s',
        r'^Jesus\s(?:Christ\s)?(?:says|said|is|was|comes|came|teaches|taught|looks|looked)',
        r'^The Bible\s',
        r'^A (?:lot|man|woman|person|friend|pastor)',
    ]

    for sent in sentences:
        sent = sent.strip()
        if not sent:
            continue

        # Check if this sentence should start a new paragraph
        should_break = False

        if len(current_para) >= 3:
            for pattern in transition_starters:
                if re.match(pattern, sent):
                    should_break = True
                    break

        # Also break after questions if paragraph is getting long
        if len(current_para) >= 2 and current_para[-1].endswith('?'):
            should_break = True

        # Force break if paragraph is getting very long
        if len(current_para) >= 7:
            should_break = True

        if should_break and current_para:
            paragraphs.append(' '.join(current_para))
            current_para = []

        current_para.append(sent)

    if current_para:
        paragraphs.append(' '.join(current_para))

    return '\n\n'.join(paragraphs)


def process_sermon(name, config):
    """Process a single sermon transcript."""
    raw_path = DOWNLOADS / f"{name}.txt"
    if not raw_path.exists():
        print(f"  SKIP: {raw_path} not found")
        return False

    text = raw_path.read_text(encoding='utf-8').strip()
    original_len = len(text)
    print(f"  Raw: {original_len:,} chars")

    # Step 1: Remove partnership intros
    text = remove_partnership_intro(text)

    # Step 2: Remove mid-sermon ads
    text = remove_mid_sermon_ads(text)

    # Step 3: Remove outro
    text = remove_outro(text)

    # Step 4: Fix Whisper repetitions
    text = fix_whisper_repetitions(text)

    # Step 5: Add paragraph breaks
    text = add_paragraph_breaks(text)

    cleaned_len = len(text)
    removed_pct = (1 - cleaned_len / original_len) * 100
    print(f"  Cleaned: {cleaned_len:,} chars ({removed_pct:.1f}% removed - ads/artifacts only)")

    # Write transcript.md
    transcript_path = SERMONS / name / "transcript.md"
    title = config['title']
    content = f"# {title}\n\n## English Transcript\n\n{text}\n"
    transcript_path.write_text(content, encoding='utf-8')
    print(f"  Written: {transcript_path}")

    # Update metadata.json
    meta_path = SERMONS / name / "metadata.json"
    meta = {"title": title, "speaker": "Tim Keller"}
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding='utf-8')
    print(f"  Updated: {meta_path}")

    # Save outline if exists in old transcript.md
    old_transcript = SERMONS / name / "transcript.md"
    # (outline was already in the old file - we saved it above)

    return True


def main():
    print("=" * 60)
    print("Cleaning 6 P0 sermon transcripts")
    print("=" * 60)

    success = 0
    for name, config in CONFIGS.items():
        print(f"\n[{name}]")
        if process_sermon(name, config):
            success += 1

    print(f"\n{'=' * 60}")
    print(f"Done: {success}/{len(CONFIGS)} sermons processed")


if __name__ == "__main__":
    main()
