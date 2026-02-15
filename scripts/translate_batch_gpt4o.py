#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量翻译讲道文件 - 使用 GPT-4o-mini
完整翻译英文原文到中文，并替换经文引用
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime
import time

try:
    from openai import OpenAI
except ImportError:
    print("Error: openai package not installed. Run: pip install openai")
    exit(1)

# 初始化 OpenAI 客户端
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    print("Error: OPENAI_API_KEY environment variable not set")
    print("Please run: export OPENAI_API_KEY='your-key-here'")
    exit(1)

client = OpenAI(api_key=API_KEY)

# 配置
SERMON_DIR = Path(".")
MODEL = "gpt-4o-mini"
BATCH_SIZE = 5  # 处理多少个文件后暂停（控制成本）
RATE_LIMIT_DELAY = 2  # API调用间隔（秒）

# 加载已翻译的文件列表（用于恢复）
PROGRESS_FILE = SERMON_DIR / ".translation_progress.json"


def load_progress():
    """加载已翻译的文件列表"""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"completed": [], "failed": [], "total": 0}


def save_progress(progress):
    """保存进度"""
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


def get_sermon_files():
    """获取所有需要翻译的讲道文件"""
    files = []
    for f in sorted(SERMON_DIR.glob("*.md")):
        if f.name.startswith(("README", "SERMON", "BIBLE")):
            continue
        files.append(f)
    return files


def extract_english_section(content):
    """从文件中提取英文原文"""
    match = re.search(r'### English\s*\n(.*?)(?:\n### 中文翻译|\n---)', content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


def translate_with_gpt4o(english_text):
    """使用 GPT-4o-mini 翻译"""
    prompt = f"""请将以下英文讲道文本翻译成中文。要求：
1. 保留原意，传达讲者的语气和深度
2. 中文表达自然流畅，符合中文阅读习惯
3. 保留段落结构和逻辑关系
4. 对于圣经经文引用，保留原格式如"Romans 3:23"等

英文文本：
{english_text}

请提供完整的中文翻译："""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "你是一位专业的宗教文本翻译者，精通中英文，特别是圣经和基督教术语。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=4000
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"  ❌ 翻译错误: {str(e)}")
        return None


def update_file_with_translation(filepath, chinese_translation):
    """更新文件，将翻译后的中文放入中文翻译部分"""
    content = filepath.read_text(encoding="utf-8")

    new_content = re.sub(
        r'### 中文翻译\s*\n\n.*?(?=\n---)',
        f'### 中文翻译\n\n{chinese_translation}',
        content,
        flags=re.DOTALL
    )

    filepath.write_text(new_content, encoding="utf-8")
    return True


def main():
    """主程序"""
    print("=" * 70)
    print("讲道文件批量翻译 - GPT-4o-mini")
    print("=" * 70)
    print()

    print(f"✓ OpenAI API Key: 已设置")
    print(f"✓ 使用模型: {MODEL}")
    print()

    progress = load_progress()
    all_files = get_sermon_files()

    print(f"📊 统计:")
    print(f"  总讲道文件: {len(all_files)}")
    print(f"  已完成: {len(progress['completed'])}")
    print(f"  失败: {len(progress['failed'])}")
    print(f"  待处理: {len(all_files) - len(progress['completed']) - len(progress['failed'])}")
    print()

    completed_set = set(progress['completed'])
    failed_set = set(progress['failed'])
    remaining_files = [f for f in all_files if f.name not in completed_set and f.name not in failed_set]

    if not remaining_files:
        print("✓ 所有文件都已处理！")
        return

    print(f"开始处理 {len(remaining_files)} 个文件...")
    print()

    processed_count = 0
    for idx, filepath in enumerate(remaining_files, 1):
        print(f"[{idx}/{len(remaining_files)}] 处理: {filepath.name}")

        try:
            content = filepath.read_text(encoding="utf-8")
            english_text = extract_english_section(content)

            if not english_text:
                print(f"  ⚠ 找不到英文部分，跳过")
                progress['failed'].append(filepath.name)
                save_progress(progress)
                continue

            print(f"  📝 英文长度: {len(english_text)} 字符")
            print(f"  🤖 调用 GPT-4o-mini...")
            
            chinese_translation = translate_with_gpt4o(english_text)

            if not chinese_translation:
                print(f"  ❌ 翻译失败")
                progress['failed'].append(filepath.name)
                save_progress(progress)
                continue

            print(f"  ✓ 翻译完成: {len(chinese_translation)} 字符")
            update_file_with_translation(filepath, chinese_translation)
            print(f"  ✓ 文件已更新")

            progress['completed'].append(filepath.name)
            save_progress(progress)

            processed_count += 1

            if processed_count % BATCH_SIZE == 0:
                print()
                print(f"⏸ 已处理 {processed_count} 个文件，暂停 30 秒...")
                print(f"✓ 进度已保存，可随时中断")
                time.sleep(30)
                print(f"▶ 继续处理...")
                print()
            else:
                time.sleep(RATE_LIMIT_DELAY)

        except Exception as e:
            print(f"  ❌ 错误: {str(e)}")
            progress['failed'].append(filepath.name)
            save_progress(progress)

    print()
    print("=" * 70)
    print("✓ 批量翻译完成！")
    print(f"  本次处理: {processed_count} 个文件")
    print(f"  总完成: {len(progress['completed'])} 个文件")
    print(f"  失败: {len(progress['failed'])} 个文件")
    print("=" * 70)


if __name__ == "__main__":
    main()
