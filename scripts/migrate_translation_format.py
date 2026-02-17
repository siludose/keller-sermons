#!/usr/bin/env python3
"""
P1 Migration: Convert translation.md files from old format to new format.

Old format:
    # English Title
    ## Chinese Translation / 中文翻译
    [content...]

New format:
    # 中文标题
    ## English Title
    **讲员**: 提摩太·凯勒 (Tim Keller)
    ---
    [content...]
    ---
    *翻译整理：小雷 ⚡*
"""

import json
import os
import re
import sys

SERMONS_DIR = os.path.join(os.path.dirname(__file__), '..', 'sermons')

# Chinese title mapping for all old-format sermons
TITLE_MAP = {
    "A_Covenant_Relationship": "盟约关系",
    "A_New_Heart": "一颗新心",
    "Aggressive_Compassion": "积极的怜悯",
    "Anatomy_of_Sin_Part_1": "罪的解剖（上）",
    "Anatomy_of_Sin_Part_2": "罪的解剖（下）",
    "Born_Again": "重生",
    "Choose_Life": "拣选生命",
    "Discovering_the_Gospel": "发现福音",
    "Does_God_Control_Everything": "神掌管万事吗",
    "Duplicity_The_Case_of_Peter": "虚伪：彼得的案例",
    "Educators_Forum_The_Gospel_Changes_Everything": "教育者论坛：福音改变一切",
    "Envy_The_Case_of_Israel": "嫉妒：以色列的案例",
    "Facing_Doubt": "面对怀疑",
    "Finding_God": "寻找神",
    "Finding_Jesus": "寻见耶稣",
    "First_of_All": "首先",
    "Gluttony_The_Case_of_Achan": "贪食：亚干的案例",
    "Gods_Law": "神的律法",
    "Greed_The_Case_of_the_Rich_Young_Ruler": "贪财：少年财主的案例",
    "Groaning_in_the_Spirit": "在圣灵中叹息",
    "How_Do_I_Know_the_Bible_Is_True_Open_Forum": "我怎么知道圣经是真的",
    "How_Sin_Makes_Us_Addicts": "罪如何使我们上瘾",
    "How_Sin_Makes_Us_Convicts": "罪如何使我们成为囚犯",
    "How_Sin_Makes_Us_Homeless": "罪如何使我们无家可归",
    "How_Sin_Makes_Us_Vandals": "罪如何使我们成为破坏者",
    "How_To_Pray": "如何祷告",
    "Humility": "谦卑",
    "Indestructible_Love": "不可摧毁的爱",
    "Indestructible_Truth": "不可摧毁的真理",
    "Integrity": "正直",
    "Jesus_Our_Gift": "耶稣：我们的礼物",
    "Jesus_Our_God": "耶稣：我们的神",
    "Jesus_Our_King": "耶稣：我们的君王",
    "Jesus_Our_Servant": "耶稣：我们的仆人",
    "Jesus_as_King_Gods_Ultimate_Plan": "耶稣为王：神的终极计划",
    "Jesus_as_King_The_King_of_Hearts": "耶稣为王：心灵之王",
    "Jesus_as_Prophet_Part_1": "耶稣为先知（上）",
    "Jesus_as_Prophet_Part_2": "耶稣为先知（下）",
    "Jesus\u2019_Model_of_Spirituality": "耶稣的灵性模范",
    "Kindness": "恩慈",
    "Knowing_God": "认识神",
    "Knowing_Good": "认识善",
    "Let_Nothing_Move_You_Easter": "不要动摇",
    "Life_in_the_Spirit": "在圣灵中的生命",
    "Love_Beyond_Degree": "超越限度的爱",
    "Love_Lust_and_Liberation": "爱、情欲与释放",
    "Love_Your_Enemies": "爱你的仇敌",
    "Love_and_the_Fruit_of_the_Spirit": "爱与圣灵的果子",
    "Love_in_the_Neighborhood": "邻舍之爱",
    "Lust_The_Case_of_Joseph": "情欲：约瑟的案例",
    "Money_and_the_Logic_of_Grace": "金钱与恩典的逻辑",
    "Mortification_Through_Joy": "以喜乐治死罪",
    "Orphans_or_Children": "孤儿还是儿女",
    "Overflowing_Joy": "满溢的喜乐",
    "Patience": "忍耐",
    "Peace": "平安",
    "Perfect_Freedom": "完全的自由",
    "Pride_The_Case_of_Nebuchadnezzar": "骄傲：尼布甲尼撒的案例",
    "Real_Joy": "真正的喜乐",
    "Rich_in_Faith": "信心的富足",
    "Secret_Treason": "暗中的叛逆",
    "Self-Control": "节制",
    "Sex_and_the_End_of_Loneliness": "性与孤独的终结",
    "Splitness": "分裂",
    "Thanksgiving_Message_from_Kathy_Keller": "凯西·凯勒的感恩节信息",
    "The_Cosmic_Spirit": "宇宙性的圣灵",
    "The_Gifts_of_the_Spirit": "圣灵的恩赐",
    "The_Inside_Out_Kingdom": "由内而外的国度",
    "The_Judgment_on_Sin": "对罪的审判",
    "The_New_Community": "新群体",
    "The_Search_for_Achievement": "追寻成就",
    "The_Search_for_God": "追寻神",
    "The_Search_for_Justice": "追求公义",
    "The_Search_for_Pleasure": "追求享乐",
    "The_Sickness_Unto_Death": "致死的疾病",
    "The_Upside_Down_Kingdom": "颠倒的国度",
    "The_Word": "道",
    "Treasure_vs._Money": "财宝与金钱",
    "True_Spirituality": "真正的灵性",
    "Who_Is_the_Spirit": "圣灵是谁",
    "Who_is_this_Jesus_Open_Forum": "这位耶稣是谁",
    "Why_Tell_Stories": "为什么要讲故事",
    "Why_a_Public_Faith": "为何要公开信仰",
    "Wisdom_How_To_Get_It": "智慧：如何获得",
    "Wisdom_How_To_Live_It": "智慧：如何活出",
    "Wisdom_What_is_it": "智慧：何为智慧",
    "Work_Wholeheartedly": "全心工作",
    "Work_and_Grace_The_Spiritual_Music_of_John_Coltrane": "工作与恩典：柯川的属灵音乐",
    "Work_and_Rest": "工作与安息",
    "Wrath_The_Case_of_Esau": "愤怒：以扫的案例",
}

FOOTER = "\n---\n\n*翻译整理：小雷 ⚡*\n"
OLD_MARKER = "## Chinese Translation / 中文翻译"


def get_english_title(sermon_name):
    """Get the English title from metadata.json."""
    meta_path = os.path.join(SERMONS_DIR, sermon_name, 'metadata.json')
    try:
        with open(meta_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('title', sermon_name.replace('_', ' '))
    except (FileNotFoundError, json.JSONDecodeError):
        return sermon_name.replace('_', ' ')


def extract_content_after_marker(text):
    """Extract content after the '## Chinese Translation / 中文翻译' marker."""
    idx = text.find(OLD_MARKER)
    if idx == -1:
        return None
    # Skip the marker line itself
    after = text[idx + len(OLD_MARKER):]
    # Strip leading blank lines
    after = after.lstrip('\n')
    return after


def has_footer(text):
    """Check if the file already has the footer."""
    return '翻译整理：小雷' in text


def migrate_file(sermon_name, dry_run=False):
    """Migrate a single translation.md file to the new format."""
    filepath = os.path.join(SERMONS_DIR, sermon_name, 'translation.md')

    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()

    # Check if it has the old marker
    if OLD_MARKER not in text:
        return 'skip', 'already new format'

    # Get titles
    chinese_title = TITLE_MAP.get(sermon_name)
    if not chinese_title:
        return 'error', f'no Chinese title mapping for {sermon_name}'

    english_title = get_english_title(sermon_name)

    # Extract content after the old marker
    content = extract_content_after_marker(text)
    if content is None:
        return 'error', 'could not find old marker'

    # Build new file
    header = f"# {chinese_title}\n## {english_title}\n\n**讲员**: 提摩太·凯勒 (Tim Keller)\n\n---\n\n"

    # Ensure content ends with newline
    content = content.rstrip('\n') + '\n'

    new_text = header + content

    # Add footer if not present
    if not has_footer(new_text):
        new_text = new_text.rstrip('\n') + '\n' + FOOTER

    if dry_run:
        lines_old = len(text.splitlines())
        lines_new = len(new_text.splitlines())
        return 'ok', f'{lines_old} -> {lines_new} lines'

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_text)

    lines_new = len(new_text.splitlines())
    return 'ok', f'{lines_new} lines'


def main():
    dry_run = '--dry-run' in sys.argv
    if dry_run:
        print("=== DRY RUN (no files will be modified) ===\n")

    sermons = sorted(os.listdir(SERMONS_DIR))
    ok_count = 0
    skip_count = 0
    error_count = 0

    for sermon in sermons:
        trans_path = os.path.join(SERMONS_DIR, sermon, 'translation.md')
        if not os.path.isfile(trans_path):
            continue

        status, msg = migrate_file(sermon, dry_run=dry_run)

        if status == 'ok':
            print(f"  ✅ {sermon}: {msg}")
            ok_count += 1
        elif status == 'skip':
            print(f"  ⏭️  {sermon}: {msg}")
            skip_count += 1
        else:
            print(f"  ❌ {sermon}: {msg}")
            error_count += 1

    print(f"\nDone: {ok_count} migrated, {skip_count} skipped, {error_count} errors")


if __name__ == '__main__':
    main()
