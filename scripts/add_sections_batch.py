#!/usr/bin/env python3
"""Add ### section titles to 18 remaining sermons that have no sections."""
import os

BASE = '/Volumes/Macintosh Extra/Code/keller-sermons/sermons'

# Sermon name -> list of (English title, Chinese title, position_fraction)
# position_fraction is where in the content (0.0=start, 1.0=end) to insert
SECTIONS = {
    'Knowing_Good': [
        ('Natural Moral Knowledge', '天然的道德认知', 0.20),
        ('The Subjectivity Objection', '主观性的反驳', 0.40),
        ('True and False Righteousness', '真假义行', 0.60),
        ('The Heart of the Matter', '问题的核心', 0.80),
    ],
    'Let_Nothing_Move_You_Easter': [
        ('What Resurrection Accomplishes', '复活成就了什么', 0.20),
        ('The Promise of New Creation', '新创造的应许', 0.40),
        ('Standing Firm in Hope', '在盼望中站稳', 0.65),
        ('First Fruits of Glory', '荣耀的初熟果子', 0.82),
    ],
    'Life_in_the_Spirit': [
        ('Filled with the Spirit', '被圣灵充满', 0.20),
        ('Spiritual Wisdom', '属灵的智慧', 0.40),
        ('Gratitude in Everything', '凡事感恩', 0.60),
        ('The Spirit and the Psalms', '圣灵与诗篇', 0.80),
    ],
    'Love_Beyond_Degree': [
        ('Jesus Weeps with Us', '耶稣与我们同哭', 0.20),
        ('Beyond Religious Performance', '超越宗教表现', 0.40),
        ('Bad Things Turn to Good', '坏事变为祝福', 0.60),
        ('The Depth of God\'s Love', '上帝之爱的深度', 0.80),
    ],
    'Love_in_the_Neighborhood': [
        ('Three Dimensions of Love', '爱的三个维度', 0.20),
        ('Loving Beyond Your Circle', '爱超越圈子', 0.40),
        ('Radical Inclusion', '彻底的接纳', 0.60),
        ('Love Demands Justice', '爱要求公义', 0.80),
    ],
    'Peace': [
        ('When Peace Is Shattered', '平安被打碎时', 0.18),
        ('The Practice of Trust', '信靠的操练', 0.38),
        ('Thinking on What Is True', '思想真实之事', 0.58),
        ('The Secret of Peace', '平安的秘诀', 0.78),
    ],
    'Perfect_Freedom': [
        ('The Paradox of Slavery', '奴役的悖论', 0.20),
        ('United with Christ', '与基督联合', 0.40),
        ('Freedom Beyond Imagination', '超越想象的自由', 0.60),
        ('True Liberation', '真正的释放', 0.80),
    ],
    'Pride_The_Case_of_Nebuchadnezzar': [
        ('The Dream and Its Warning', '异梦与警告', 0.20),
        ('Hidden Forms of Pride', '骄傲的隐藏形式', 0.40),
        ('Pride as Self-Justification', '骄傲即自我辩护', 0.60),
        ('Restoration Through Humility', '谦卑中的恢复', 0.80),
    ],
    'Real_Joy': [
        ('The Pursuit of Happiness', '追求幸福的困境', 0.18),
        ('Joy Beyond Circumstances', '超越环境的喜乐', 0.38),
        ('Foretastes of Glory', '荣耀的预尝', 0.58),
        ('The Gospel Brings Joy', '福音带来喜乐', 0.78),
    ],
    'The_Judgment_on_Sin': [
        ('The People\'s Rebellion', '百姓的悖逆', 0.20),
        ('Moses at the Rock', '摩西在磐石前', 0.40),
        ('Striking versus Speaking', '击打与说话', 0.60),
        ('Grace from the Stricken Rock', '从被击之磐石涌出恩典', 0.80),
    ],
    'The_Search_for_Achievement': [
        ('The Work-Based Life', '以工作为中心的人生', 0.18),
        ('The Hunger for Recognition', '对认可的渴求', 0.38),
        ('The Limits of Achievement', '成就的局限', 0.58),
        ('Rest Within Work', '工作中的安息', 0.80),
    ],
    'The_Search_for_God': [
        ('The Vision of Holiness', '圣洁的异象', 0.18),
        ('Encountering the Redeemer', '遇见救赎主', 0.38),
        ('The Path to More of God', '更多寻见上帝之路', 0.58),
        ('Refined by Fire', '在火中被炼净', 0.80),
    ],
    'The_Search_for_Justice': [
        ('The Preacher\'s Quest', '传道者的追寻', 0.25),
        ('Confronting Injustice', '面对不公', 0.50),
        ('Beyond Death and Vanity', '超越死亡与虚空', 0.75),
    ],
    'The_Word': [
        ('The Mystery of Christmas', '圣诞的奥秘', 0.20),
        ('Knowing God Through the Word', '藉话语认识上帝', 0.40),
        ('Beyond Ancient Paganism', '超越古代多神论', 0.60),
        ('The Word Made Flesh', '道成肉身', 0.80),
    ],
    'Work_Wholeheartedly': [
        ('Conversion and Vocation', '归信与呼召', 0.20),
        ('Connecting Work to God', '将工作与上帝连接', 0.40),
        ('Beyond Working for Money', '超越为钱工作', 0.60),
        ('Working as Stewardship', '工作即管家职分', 0.80),
    ],
    'Work_and_Grace_The_Spiritual_Music_of_John_Coltrane': [
        ('The Hand of God in Art', '上帝之手在艺术中', 0.20),
        ('Dedication and Idolatry', '专注与偶像崇拜', 0.40),
        ('Beyond Success', '超越成功', 0.60),
        ('Grace and Gratitude', '恩典与感恩', 0.80),
    ],
    'Work_and_Rest': [
        ('Our Work-Obsessed Culture', '工作至上的文化', 0.20),
        ('The Meaning of Conversion', '归信的意义', 0.40),
        ('The Finished Work of Christ', '基督已完成的工作', 0.60),
        ('The Discipline of Rest', '安息的操练', 0.80),
    ],
    'Wrath_The_Case_of_Esau': [
        ('A Story of Forgiveness', '一个饶恕的故事', 0.20),
        ('When Anger Goes Wrong', '愤怒何时出错', 0.40),
        ('The Prison of Bitterness', '苦毒的牢笼', 0.60),
        ('Grace Overcomes Bitterness', '恩典胜过苦毒', 0.80),
    ],
}


def get_content_paragraphs(lines):
    """Find content start (after ---) and return list of (line_index, text) for non-empty lines."""
    start = 0
    for i, line in enumerate(lines):
        if line.strip() == '---':
            start = i + 1
            break

    paras = []
    for i in range(start, len(lines)):
        if lines[i].strip() and not lines[i].startswith('*翻译整理'):
            paras.append(i)
    return paras, start


def insert_sections(filepath, sections, is_chinese=False):
    """Insert ### section titles at proportional positions."""
    with open(filepath) as f:
        lines = f.readlines()

    para_indices, content_start = get_content_paragraphs(lines)
    n_paras = len(para_indices)

    if n_paras == 0:
        print(f"  WARNING: No paragraphs found in {filepath}")
        return False

    # Calculate insertion points
    insertions = []  # (line_index, title)
    for eng_title, cn_title, frac in sections:
        title = cn_title if is_chinese else eng_title
        target_para = int(n_paras * frac)
        target_para = max(1, min(target_para, n_paras - 1))

        # Find the line index for this paragraph
        line_idx = para_indices[target_para]

        # Find the previous blank line to insert before this paragraph
        insert_at = line_idx
        while insert_at > 0 and lines[insert_at - 1].strip() == '':
            insert_at -= 1

        insertions.append((insert_at, f'### {title}'))

    # Insert in reverse order to preserve line numbers
    insertions.sort(key=lambda x: x[0], reverse=True)

    for insert_at, title in insertions:
        lines.insert(insert_at, f'\n{title}\n\n')

    with open(filepath, 'w') as f:
        f.writelines(lines)

    return True


def count_sections(filepath):
    with open(filepath) as f:
        return sum(1 for line in f if line.startswith('### '))


def main():
    processed = 0
    errors = 0

    for name, sections in SECTIONS.items():
        transcript = os.path.join(BASE, name, 'transcript.md')
        translation = os.path.join(BASE, name, 'translation.md')

        if not os.path.exists(transcript) or not os.path.exists(translation):
            print(f"SKIP {name}: files not found")
            errors += 1
            continue

        # Check if already has sections
        if count_sections(transcript) > 0 or count_sections(translation) > 0:
            print(f"SKIP {name}: already has sections")
            continue

        print(f"Processing {name}...")
        ok1 = insert_sections(transcript, sections, is_chinese=False)
        ok2 = insert_sections(translation, sections, is_chinese=True)

        if ok1 and ok2:
            tc = count_sections(transcript)
            trc = count_sections(translation)
            if tc == trc:
                print(f"  OK: {tc} sections in both files")
                processed += 1
            else:
                print(f"  MISMATCH: transcript={tc}, translation={trc}")
                errors += 1
        else:
            print(f"  ERROR processing {name}")
            errors += 1

    print(f"\nDone: {processed} processed, {errors} errors")


if __name__ == '__main__':
    main()
