#!/usr/bin/env python3
"""
批量翻译新文件夹结构中的讲道

支持 sermons/{sermon_name}/translation.md 格式
使用 Ollama 或 Claude 进行翻译
"""

import sys
from pathlib import Path
from typing import Optional
import time

# 导入现有的翻译后端
try:
    from translate_sermons import get_translation_backend
    from openai import OpenAI
    import anthropic
except ImportError as e:
    print(f"❌ 错误：无法导入必需模块: {e}")
    print("确保已安装: pip install anthropic openai")
    sys.exit(1)


def translate_chunk_ollama(text: str, client: OpenAI, max_retries: int = 2) -> Optional[str]:
    """翻译单个文本块（带重试和超时）"""
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="qwen2.5:7b-instruct-q8_0",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a professional Chinese translator specializing in religious texts.
Translate sermon content to Simplified Chinese while preserving:
1. All markdown formatting
2. Bible book names in English
3. Natural flow and rhetorical power
4. Quoted material with >

Translate naturally and fluently."""
                    },
                    {
                        "role": "user",
                        "content": f"Translate this sermon excerpt to Simplified Chinese:\n\n{text[:2500]}"
                    }
                ],
                max_tokens=4000,
                temperature=0.3,
                timeout=60.0  # 60 秒超时
            )
            return response.choices[0].message.content
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"!", end="", flush=True)  # 重试标记
                time.sleep(2)
                continue
            else:
                print(f"\n  ❌ Ollama 错误: {e}", flush=True)
                return None
    return None


def translate_chunk_claude(text: str, client: anthropic.Anthropic) -> Optional[str]:
    """翻译单个文本块（Claude）"""
    try:
        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=4000,
            messages=[
                {
                    "role": "user",
                    "content": f"""Translate this sermon excerpt to Simplified Chinese. Preserve all markdown formatting and Bible book names in English. Be natural and fluent.

{text[:2500]}"""
                }
            ]
        )
        return message.content[0].text
    except Exception as e:
        print(f"\n  ❌ Claude 错误: {e}", flush=True)
        return None


def translate_sermon_folder(sermon_folder: Path, backend: str, client) -> bool:
    """翻译单个讲道文件夹"""

    transcript_path = sermon_folder / "transcript.md"
    translation_path = sermon_folder / "translation.md"

    # 检查文件是否存在
    if not transcript_path.exists():
        print(f"  ⚠️  跳过：缺少转录文件")
        return False

    if not translation_path.exists():
        print(f"  ⚠️  跳过：缺少翻译文件")
        return False

    # 读取现有翻译
    translation_content = translation_path.read_text(encoding='utf-8')

    # 检查是否已有完整翻译（> 1000 字符）
    # 提取正文（去掉标题）
    import re
    content_match = re.search(r'## Chinese Translation.*?\n+(.*)', translation_content, re.DOTALL)
    if content_match:
        existing_translation = content_match.group(1).strip()
        if len(existing_translation) > 1000:
            print(f"  ✅ 跳过：已有完整翻译 ({len(existing_translation)} 字符)")
            return False

    # 读取英文转录
    transcript_content = transcript_path.read_text(encoding='utf-8')

    # 提取英文内容
    english_match = re.search(r'## English Transcript.*?\n+(.*)', transcript_content, re.DOTALL)
    if not english_match:
        print(f"  ⚠️  跳过：无法提取英文转录")
        return False

    english_text = english_match.group(1).strip()

    if len(english_text) < 100:
        print(f"  ⚠️  跳过：转录太短 ({len(english_text)} 字符)")
        return False

    # 分块翻译（每块 2200 字符）
    chunk_size = 2200
    chunks = []

    if len(english_text) <= chunk_size:
        chunks = [english_text]
    else:
        # 按段落分块
        paragraphs = english_text.split('\n\n')
        current_chunk = []
        current_size = 0

        for para in paragraphs:
            para_size = len(para)
            if current_size + para_size > chunk_size and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = [para]
                current_size = para_size
            else:
                current_chunk.append(para)
                current_size += para_size

        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))

    print(f"  📄 翻译中... ({len(chunks)} 块)", end=" ", flush=True)

    # 翻译每块
    translated_chunks = []
    for i, chunk in enumerate(chunks):
        print(f".", end="", flush=True)  # 显示进度点

        try:
            if backend == "ollama":
                result = translate_chunk_ollama(chunk, client)
            elif backend == "claude":
                result = translate_chunk_claude(chunk, client)
            else:
                print(f"\n  ❌ 未知后端: {backend}", flush=True)
                return False

            if not result:
                print(f"\n  ❌ 翻译失败（块 {i+1}/{len(chunks)}）", flush=True)
                return False

            translated_chunks.append(result)
        except Exception as e:
            print(f"\n  ❌ 错误（块 {i+1}/{len(chunks)}）: {e}", flush=True)
            return False

    # 合并翻译
    chinese_text = '\n\n'.join(translated_chunks)

    # 读取元数据获取标题
    metadata_path = sermon_folder / "metadata.json"
    title = sermon_folder.name
    if metadata_path.exists():
        import json
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
            title = metadata.get("title", title)

    # 写回翻译文件
    new_content = f"# {title}\n\n## Chinese Translation / 中文翻译\n\n{chinese_text}\n"
    translation_path.write_text(new_content, encoding='utf-8')

    print(f"✅ ({len(chinese_text)} 字符)")
    return True


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="批量翻译新文件夹结构中的讲道"
    )
    parser.add_argument(
        "--file",
        help="处理单个讲道文件夹"
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="批量处理所有讲道"
    )
    parser.add_argument(
        "--backend",
        choices=["auto", "ollama", "claude"],
        default="auto",
        help="指定后端（默认：自动选择）"
    )

    args = parser.parse_args()

    # 获取后端
    try:
        backend_name, client = get_translation_backend(
            force_backend=None if args.backend == "auto" else args.backend
        )
        print(f"✅ 使用后端: {backend_name}\n")
    except Exception as e:
        print(f"❌ 后端初始化失败: {e}")
        sys.exit(1)

    # 获取仓库根目录
    base_dir = Path(__file__).parent.parent
    sermons_dir = base_dir / "sermons"

    if not sermons_dir.exists():
        print(f"❌ sermons/ 目录不存在: {sermons_dir}")
        sys.exit(1)

    # 处理单个讲道
    if args.file:
        sermon_folder = sermons_dir / args.file
        if not sermon_folder.exists():
            print(f"❌ 讲道文件夹不存在: {sermon_folder}")
            sys.exit(1)

        print(f"📖 处理: {args.file}")
        if translate_sermon_folder(sermon_folder, backend_name, client):
            print(f"\n✅ 翻译完成！")
        else:
            print(f"\n⚠️  无需翻译")
        return

    # 批量处理
    if args.batch:
        # 查找所有讲道文件夹
        sermon_folders = sorted([d for d in sermons_dir.iterdir() if d.is_dir()])

        print(f"📦 找到 {len(sermon_folders)} 个讲道文件夹\n")

        # 筛选需要翻译的
        need_translation = []
        for folder in sermon_folders:
            translation_path = folder / "translation.md"
            if translation_path.exists():
                content = translation_path.read_text(encoding='utf-8')
                import re
                content_match = re.search(r'## Chinese Translation.*?\n+(.*)', content, re.DOTALL)
                if content_match:
                    existing = content_match.group(1).strip()
                    if len(existing) < 1000:
                        need_translation.append(folder)
                else:
                    need_translation.append(folder)

        print(f"📋 需要翻译: {len(need_translation)} 个讲道\n")

        if len(need_translation) == 0:
            print("✅ 所有讲道已翻译完成！")
            return

        # 逐个翻译
        translated = 0
        failed = 0

        for i, folder in enumerate(need_translation, 1):
            print(f"\n[{i}/{len(need_translation)}] 📖 {folder.name}")

            try:
                if translate_sermon_folder(folder, backend_name, client):
                    translated += 1
                else:
                    print(f"  ⚠️  跳过")
            except Exception as e:
                print(f"  ❌ 错误: {e}")
                failed += 1

            # 每 5 个讲道报告一次进度
            if i % 5 == 0:
                print(f"\n📊 进度: {translated} 个已翻译, {failed} 个失败")

        # 最终报告
        print(f"\n{'='*60}")
        print(f"🎉 批量翻译完成！")
        print(f"{'='*60}")
        print(f"  ✅ 成功翻译: {translated}/{len(need_translation)}")
        if failed > 0:
            print(f"  ❌ 失败: {failed}")
        print(f"{'='*60}")

    else:
        print("❌ 请使用 --file 或 --batch 参数")
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
