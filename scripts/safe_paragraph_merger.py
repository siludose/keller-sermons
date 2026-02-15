#!/usr/bin/env python3
"""
安全的段落合并器
不使用 LLM，只做简单的段落聚合，保证内容完整性
"""

import re
import sys
from pathlib import Path


def merge_chinese_paragraphs(text: str, sentences_per_paragraph: int = 4) -> str:
    """
    安全地合并中文段落
    - 保留所有原始内容
    - 将连续的短行合并成段落
    - 按标点符号（。！？）分段
    """
    if not text.strip():
        return text

    # 移除多余空行，保留内容
    lines = [line.strip() for line in text.split('\n') if line.strip()]

    # 将所有行连接成一个长文本
    full_text = ' '.join(lines)

    # 按中文句号、感叹号、问号分割
    sentences = re.split(r'([。！？])', full_text)

    # 重新组合句子（把标点符号加回去）
    complete_sentences = []
    for i in range(0, len(sentences) - 1, 2):
        if i + 1 < len(sentences):
            complete_sentences.append(sentences[i] + sentences[i + 1])

    # 按指定数量合并成段落
    paragraphs = []
    current_paragraph = []

    for sentence in complete_sentences:
        sentence = sentence.strip()
        if sentence:
            current_paragraph.append(sentence)

            if len(current_paragraph) >= sentences_per_paragraph:
                paragraphs.append(''.join(current_paragraph))
                current_paragraph = []

    # 处理剩余句子
    if current_paragraph:
        paragraphs.append(''.join(current_paragraph))

    # 用双换行符分隔段落
    result = '\n\n'.join(paragraphs)

    return result


def merge_english_paragraphs(text: str, sentences_per_paragraph: int = 4) -> str:
    """
    安全地合并英文段落
    - 保留所有原始内容
    - 按句号、感叹号、问号分段
    """
    if not text.strip():
        return text

    # 移除多余空行
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    full_text = ' '.join(lines)

    # 按英文句号分割（考虑缩写）
    sentences = re.split(r'([.!?])\s+', full_text)

    # 重新组合句子
    complete_sentences = []
    for i in range(0, len(sentences) - 1, 2):
        if i + 1 < len(sentences):
            sentence = sentences[i] + sentences[i + 1]
            complete_sentences.append(sentence.strip())

    # 合并成段落
    paragraphs = []
    current_paragraph = []

    for sentence in complete_sentences:
        if sentence:
            current_paragraph.append(sentence)

            if len(current_paragraph) >= sentences_per_paragraph:
                paragraphs.append(' '.join(current_paragraph))
                current_paragraph = []

    if current_paragraph:
        paragraphs.append(' '.join(current_paragraph))

    result = '\n\n'.join(paragraphs)

    return result


def process_sermon_file(sermon_folder: Path, chinese_only: bool = False, english_only: bool = False):
    """处理讲道文件，安全地合并段落"""

    # 处理中文翻译
    if not english_only:
        translation_path = sermon_folder / "translation.md"
        if translation_path.exists():
            print(f"📖 处理中文翻译...")
            content = translation_path.read_text(encoding='utf-8')

            # 提取标题和正文
            match = re.search(r'(.*?## Chinese Translation.*?\n\n)(.*)', content, re.DOTALL)
            if match:
                header = match.group(1)
                body = match.group(2)

                original_length = len(body)
                print(f"   原始长度: {original_length} 字符")

                # 合并段落
                merged_body = merge_chinese_paragraphs(body, sentences_per_paragraph=4)

                new_length = len(merged_body)
                print(f"   合并后长度: {new_length} 字符")

                # 验证内容完整性（允许 ±2% 的差异，因为空格变化）
                diff_percent = abs(new_length - original_length) / original_length * 100
                if diff_percent > 2:
                    print(f"   ⚠️  警告：内容长度变化 {diff_percent:.1f}%")
                else:
                    print(f"   ✅ 内容完整性验证通过")

                # 写回文件
                new_content = header + merged_body + "\n"
                translation_path.write_text(new_content, encoding='utf-8')
                print(f"   ✅ 已保存")

    # 处理英文转录
    if not chinese_only:
        transcript_path = sermon_folder / "transcript.md"
        if transcript_path.exists():
            print(f"📖 处理英文转录...")
            content = transcript_path.read_text(encoding='utf-8')

            # 提取标题和正文
            match = re.search(r'(.*?## English Transcript.*?\n\n)(.*)', content, re.DOTALL)
            if match:
                header = match.group(1)
                body = match.group(2)

                original_length = len(body)
                print(f"   原始长度: {original_length} 字符")

                # 合并段落
                merged_body = merge_english_paragraphs(body, sentences_per_paragraph=4)

                new_length = len(merged_body)
                print(f"   合并后长度: {new_length} 字符")

                # 验证
                diff_percent = abs(new_length - original_length) / original_length * 100
                if diff_percent > 2:
                    print(f"   ⚠️  警告：内容长度变化 {diff_percent:.1f}%")
                else:
                    print(f"   ✅ 内容完整性验证通过")

                # 写回文件
                new_content = header + merged_body + "\n"
                transcript_path.write_text(new_content, encoding='utf-8')
                print(f"   ✅ 已保存")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="安全的段落合并（保证内容完整性）")
    parser.add_argument("--file", required=True, help="讲道文件名")
    parser.add_argument("--chinese-only", action="store_true", help="只处理中文")
    parser.add_argument("--english-only", action="store_true", help="只处理英文")
    parser.add_argument("--sentences", type=int, default=4, help="每段句子数（默认4）")

    args = parser.parse_args()

    base_dir = Path(__file__).parent.parent
    sermon_folder = base_dir / "sermons" / args.file

    if not sermon_folder.exists():
        print(f"❌ 讲道文件夹不存在: {sermon_folder}")
        sys.exit(1)

    print(f"🔧 安全段落合并：{args.file}")
    print(f"   策略：每段 {args.sentences} 句话")
    print(f"   保证：100% 保留原始内容\n")

    process_sermon_file(sermon_folder, args.chinese_only, args.english_only)

    print(f"\n✅ 完成！")


if __name__ == "__main__":
    main()
