#!/usr/bin/env python3
"""
P2 Phase 1: Add ### English section titles to transcript.md
based on matching sections from translation.md.

For sermons where translation.md has ### sections but transcript.md doesn't,
this script aligns paragraphs proportionally and inserts English ### titles.
"""

import os
import re
import sys

SERMONS_DIR = os.path.join(os.path.dirname(__file__), '..', 'sermons')

# Chinese → English title translations for multi-section sermons
TITLE_TRANSLATIONS = {
    # Admitting (19 sections)
    "引言：主祷文是一切问题的答案": "Introduction: The Lord's Prayer Contains All Answers",
    "祷告是让心灵回归正确轨道": "Prayer: Getting the Heart Back on Track",
    "全新生命的异象": "A Vision of a Whole New Life",
    "一切始于敬拜赞美": "It All Starts with Adoration",
    "悔改必须从敬拜赞美中流出": "Repentance Must Flow from Adoration",
    "为什么必须悔改？": "Why Must We Repent?",
    "罪疚感只能在神面前解决": "Guilt Can Only Be Resolved Before God",
    "卓别林与球和链：我们无法自我拯救": "Chaplin and the Ball and Chain: We Cannot Save Ourselves",
    "悔改的动力：爱而非惧怕": "The Motivation for Repentance: Love, Not Fear",
    "律法主义的悔改与福音的悔改": "Legalistic Repentance vs. Gospel Repentance",
    "十字架：同时显明罪的严重与神的接纳": "The Cross: Revealing Both Sin's Gravity and God's Acceptance",
    '耶稣为何"死得如此艰难"？': 'Why Did Jesus "Die So Poorly"?',
    "唯有在基督里才能真正悔改": "Only in Christ Can We Truly Repent",
    "老板与父亲：两种截然不同的悔改": "Boss vs. Father: Two Kinds of Sorrow",
    "饶恕人是真悔改的试金石": "Forgiving Others: The Acid Test of True Repentance",
    "三个实用的悔改方法": "Three Practical Ways to Repent",
    "悔改是苦尽甘来": "Repentance Is Bittersweet",
    "悔改进入生命：最伟大的恩赐": "Repentance unto Life: The Greatest Gift",
    "结束祷告": "Closing Prayer",

    # Radical_Generosity (17 sections)
    "为什么教会必须谈论金钱": "Why the Church Must Talk About Money",
    "全人医治的比喻": "The Parable of Whole-Person Healing",
    "激进慷慨：真基督徒的标志": "Radical Generosity: The Mark of a True Christian",
    "慷慨的双重影响": "The Twofold Impact of Generosity",
    "番茄的比喻：意义的重要性": "The Tomato Parable: The Importance of Meaning",
    "拉丁美洲的属灵复兴": "The Spiritual Revival in Latin America",
    "激进慷慨如何改变罗马帝国": "How Radical Generosity Transformed the Roman Empire",
    "早期基督徒改变世界的四种品质": "Four Qualities That Changed the World",
    "慷慨的动力：创造与救赎": "The Motivation for Generosity: Creation and Redemption",
    "父亲与孩子的比喻": "The Father and Child Parable",
    "救赎的动力：福音如何改变一切": "The Power of Redemption: How the Gospel Changes Everything",
    "司布真的比喻：无价的药": "Spurgeon's Parable: The Priceless Medicine",
    "慷慨的衡量标准：十一奉献": "The Measure of Generosity: Tithing",
    "爱的语言与慷慨": "The Language of Love and Generosity",
    "认识恩典的诊断方式": "Diagnosing Grace",
    "松开你紧握的拳头": "Unclench Your Fist",
    "结束祷告": "Closing Prayer",

    # Thy_Will_Be_Done (13 sections)
    "祷告的真正目的不是向神索取": "The True Purpose of Prayer Is Not to Get Things from God",
    "先接受再祈求的祷告次序": "Accept First, Then Ask: The Order of Prayer",
    "保罗的祷告：为内在生命祈求": "Paul's Prayers: Praying for the Inner Life",
    "认知疗法的属灵启示": "The Spiritual Insight of Cognitive Therapy",
    "六岁孩子与两千万遗产": "A Six-Year-Old and a Twenty-Million-Dollar Inheritance",
    "客西马尼园：耶稣的顺服": "Gethsemane: Jesus' Submission",
    "马思逊的诗歌：凡人的顺服": "George Matheson's Hymn: A Mortal's Submission",
    "苦难会改变你，却不会让你原地不动": "Suffering Will Change You, but It Won't Leave You Where You Are",
    "祷告不是被动，而是主动祈求": "Prayer Is Not Passive but Active Asking",
    "祷告的保险装置": "The Safety Mechanism of Prayer",
    "做最亲近父心的孩子": "Being the Child Closest to the Father's Heart",
    "雅各的摔跤：唯有降服方能得胜": "Jacob's Wrestling: Only in Surrender Can You Prevail",
    "结束祷告": "Closing Prayer",

    # The_Power_of_the_Incarnation (10 sections)
    "施洗约翰的自我认知": "John the Baptist's Self-Understanding",
    "耶稣论施洗约翰的伟大": "Jesus' Testimony About John's Greatness",
    "约翰对耶稣的极高认识": "John's Exalted View of Jesus",
    "解鞋带的比喻与基督的超越": "The Sandal-Strap Metaphor and Christ's Transcendence",
    "谦卑与刚勇并存的品格": "Humility and Boldness Combined",
    "超越表现主义的身份认同": "Beyond Performance-Based Identity",
    "道成肉身如何赐给我们新身份": "How the Incarnation Gives Us a New Identity",
    "身份认同的试金石": "The Litmus Test of Identity",
    "你是否敢于做一个声音": "Do You Dare to Be a Voice?",

    # Seeking_the_Kingdom (8 sections)
    "焦虑的本质：渴望掌控不可掌控之事": "The Nature of Anxiety: Craving Control over the Uncontrollable",
    "焦虑的根源：人类对权力的渴望": "The Root of Anxiety: The Human Desire for Power",
    "对症下药：纠正错误的思维": "The Cure: Correcting Wrong Thinking",
    "上帝的护理：万事互相效力": "God's Providence: All Things Work Together",
    "上帝的慈爱：天父知道你的需要": "God's Love: Your Father Knows Your Needs",
    "上帝的国度：先求他的国和他的义": "God's Kingdom: Seek First His Kingdom and Righteousness",
    "寻求神国的三重含义": "Three Meanings of Seeking God's Kingdom",
    "正确的优先次序：先求他的国": "Right Priorities: Seek First His Kingdom",
    "信靠基督：不仅信他存在，更要信他的话": "Trusting Christ: Not Just Belief, but Trust",
    "不要为明天忧虑": "Do Not Worry About Tomorrow",

    # Entering_His_Rest (7 sections)
    "引言：你知道怎样躺下并睡着吗？": "Introduction: Do You Know How to Lie Down and Fall Asleep?",
    "安息：圣经中最重要的主题之一": "Rest: One of the Bible's Most Important Themes",
    "安息日的安息：灵魂的深度睡眠": "Sabbath Rest: The Deep Sleep of the Soul",
    "卡夫卡的《审判》：我们内心的焦虑": "Kafka's The Trial: The Anxiety Within",
    "罗马书 2 章：那台看不见的录音机": "Romans 2: The Invisible Tape Recorder",
    "如何进入安息？福音的两部分": "How to Enter Rest: Two Parts of the Gospel",
    "安息的检验：你能坐着听批评吗？": "The Test of Rest: Can You Sit and Hear Criticism?",

    # The_Glory_of_the_Incarnation (6 sections)
    '"道成肉身"——人类思想的革命': "The Word Made Flesh: A Revolution in Human Thought",
    "苦难中的无限安慰": "Infinite Comfort in Suffering",
    "受苦的神能坚固受苦的人": "A Suffering God Can Strengthen Suffering People",
    "效法道成肉身：投入服事": "Imitating the Incarnation: Entering into Service",
    "既现实又确定的盼望": "A Hope Both Realistic and Certain",
    "结束祷告": "Closing Prayer",
}


def split_paragraphs(text):
    """Split text into paragraphs (non-empty blocks separated by blank lines)."""
    paras = []
    current = []
    for line in text.split('\n'):
        if line.strip() == '' or line.strip() == '---':
            if current:
                paras.append('\n'.join(current))
                current = []
        else:
            current.append(line)
    if current:
        paras.append('\n'.join(current))
    return paras


def extract_translation_sections(filepath):
    """Extract ### sections from translation.md.
    Returns [(title, paragraph_count), ...]
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    sections = []
    current_title = None
    current_paras = []

    # Skip header (everything before first ###)
    in_content = False

    for line in content.split('\n'):
        if line.startswith('### '):
            if current_title is not None:
                sections.append((current_title, len(split_paragraphs('\n'.join(current_paras)))))
            current_title = line[4:].strip()
            current_paras = []
            in_content = True
        elif in_content:
            current_paras.append(line)

    if current_title is not None:
        sections.append((current_title, len(split_paragraphs('\n'.join(current_paras)))))

    return sections


def get_transcript_body(filepath):
    """Read transcript.md and return (header_lines, body_paragraphs)."""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Find where body starts (after ## English Transcript or after first blank line after headers)
    body_start = 0
    for i, line in enumerate(lines):
        if line.strip().startswith('## '):
            body_start = i + 1
            break

    # Skip blank lines after header
    while body_start < len(lines) and lines[body_start].strip() == '':
        body_start += 1

    header = ''.join(lines[:body_start])
    body = ''.join(lines[body_start:])
    body_paras = split_paragraphs(body)

    return header, body_paras


def translate_title(zh_title):
    """Translate Chinese section title to English."""
    # Clean up the title (remove any inline content)
    zh_clean = zh_title.split('\n')[0].strip()

    if zh_clean in TITLE_TRANSLATIONS:
        return TITLE_TRANSLATIONS[zh_clean]

    # Fallback: return Chinese title with note
    return f"[{zh_clean}]"


def process_sermon(sermon_name, dry_run=False):
    """Add ### English titles to transcript.md based on translation.md sections."""
    trans_path = os.path.join(SERMONS_DIR, sermon_name, 'translation.md')
    script_path = os.path.join(SERMONS_DIR, sermon_name, 'transcript.md')

    if not os.path.isfile(trans_path) or not os.path.isfile(script_path):
        return 'error', 'missing files'

    # Check if transcript already has ### titles
    with open(script_path, 'r', encoding='utf-8') as f:
        if '### ' in f.read():
            return 'skip', 'already has sections'

    # Get translation sections (require at least 3 clean sections)
    sections = extract_translation_sections(trans_path)
    if not sections:
        return 'skip', 'no sections in translation'
    if len(sections) < 3:
        return 'skip', f'only {len(sections)} sections (need ≥3 for meaningful alignment)'

    # Get transcript body
    header, body_paras = get_transcript_body(script_path)
    total_paras = len(body_paras)

    if total_paras == 0:
        return 'error', 'empty transcript body'

    # Check for untranslated titles
    untranslated = [t for t, _ in sections if translate_title(t).startswith('[')]
    if untranslated and not dry_run:
        return 'error', f'untranslated titles: {untranslated}'

    # Map section breaks to paragraph indices
    total_section_paras = sum(count for _, count in sections)
    if total_section_paras == 0:
        total_section_paras = len(sections)

    # Calculate paragraph index for each section start
    section_starts = []
    cumulative = 0
    for i, (title, count) in enumerate(sections):
        if i == 0:
            para_idx = 0
        else:
            # Proportional mapping
            ratio = cumulative / total_section_paras
            para_idx = min(int(ratio * total_paras), total_paras - 1)
        section_starts.append((para_idx, translate_title(title)))
        cumulative += count

    if dry_run:
        info = f'{len(sections)} sections, {total_paras} paras'
        for idx, title in section_starts:
            info += f'\n    [{idx}] ### {title}'
        return 'ok', info

    # Build new transcript
    output_lines = [header]
    para_to_title = {idx: title for idx, title in section_starts}

    for i, para in enumerate(body_paras):
        if i in para_to_title:
            output_lines.append(f'### {para_to_title[i]}\n\n')
        output_lines.append(para + '\n\n')

    new_content = ''.join(output_lines).rstrip('\n') + '\n'

    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    return 'ok', f'{len(sections)} sections added, {len(new_content.splitlines())} lines'


def main():
    dry_run = '--dry-run' in sys.argv
    target = [a for a in sys.argv[1:] if not a.startswith('--')]

    if dry_run:
        print("=== DRY RUN ===\n")

    if not target:
        # Process all sermons that need it
        target = sorted(os.listdir(SERMONS_DIR))

    ok = skip = err = 0
    for name in target:
        if not os.path.isdir(os.path.join(SERMONS_DIR, name)):
            continue
        status, msg = process_sermon(name, dry_run=dry_run)
        icon = {'ok': '✅', 'skip': '⏭️', 'error': '❌'}[status]
        print(f"  {icon} {name}: {msg}")
        if status == 'ok':
            ok += 1
        elif status == 'skip':
            skip += 1
        else:
            err += 1

    print(f"\nDone: {ok} processed, {skip} skipped, {err} errors")


if __name__ == '__main__':
    main()
