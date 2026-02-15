#!/usr/bin/env python3
"""
智能美化器
使用 LLM 为讲道添加小标题、优化分段和段落聚合
"""

import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any

# 导入现有的翻译后端
try:
    from translate_sermons import get_translation_backend
except ImportError as e:
    print(f"❌ 错误：无法导入 translate_sermons 模块: {e}")
    print("确保 translate_sermons.py 在同一目录中")
    sys.exit(1)


class SmartBeautifier:
    """使用 LLM 智能美化讲道内容"""

    def __init__(self, backend_name: str, client):
        self.backend_name = backend_name
        self.client = client

    def _call_llm(self, prompt: str, max_tokens: int = 4000) -> Optional[str]:
        """调用 LLM 后端（针对美化任务优化）"""
        try:
            if self.backend_name == "ollama":
                response = self.client.chat.completions.create(
                    model="qwen2.5:7b-instruct-q8_0",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=0.3
                )
                return response.choices[0].message.content
            elif self.backend_name == "claude":
                message = self.client.messages.create(
                    model="claude-sonnet-4-5-20250929",
                    max_tokens=max_tokens,
                    messages=[{"role": "user", "content": prompt}]
                )
                return message.content[0].text
        except Exception as e:
            print(f"⚠️  LLM 调用失败: {e}")
            return None

    def beautify_transcript(self, text: str, title: str = "") -> str:
        """
        智能美化英文转录：
        1. 识别讲道结构（引言、要点1、2、3等）
        2. 添加描述性小标题
        3. 优化段落分隔
        """
        if not text.strip():
            return text

        print(f"✨ 使用 LLM 智能美化英文转录...")

        prompt = f"""You are a sermon formatter. Your task is to add structure to this sermon transcript.

TASK:
1. Identify the main sections of the sermon (introduction, main points, conclusion, etc.)
2. Add descriptive subheadings (###) for each major section
3. Break into well-organized paragraphs based on topic shifts
4. Preserve ALL original content - do not summarize or omit anything

GUIDELINES:
- Use ### for subheadings (e.g., "### Introduction", "### Main Point 1: The Human Problem")
- Make subheadings descriptive and meaningful
- Typical sermon structure: Introduction → 2-4 Main Points → Application → Conclusion
- Each paragraph should be 3-5 sentences on the same topic
- Preserve exact wording, just add formatting

SERMON TITLE: {title if title else "Untitled"}

TRANSCRIPT:
{text[:15000]}  # 限制输入长度

OUTPUT: Return the formatted transcript with ### subheadings and proper paragraphs."""

        try:
            result = self._call_llm(prompt)

            if result:
                print(f"✅ 智能美化完成")
                return result
            else:
                print(f"⚠️  LLM 美化失败，使用基础格式化")
                return self._basic_beautify(text)

        except Exception as e:
            print(f"⚠️  LLM 美化出错: {e}")
            print(f"   使用基础格式化")
            return self._basic_beautify(text)

    def beautify_translation(self, text: str, title: str = "") -> str:
        """
        智能美化中文翻译：
        1. 添加小标题（对应英文结构）
        2. 优化段落分隔
        3. 聚合相关内容
        """
        if not text.strip():
            return text

        print(f"✨ 使用 LLM 智能美化中文翻译...")

        prompt = f"""你是一位讲道格式化专家。你的任务是为这篇中文讲道添加结构和聚合段落。

任务：
1. 识别讲道的主要部分（引言、要点1、2、3等）
2. 为每个主要部分添加描述性小标题（使用 ###）
3. **将相关句子聚合成连贯段落** - 这是最重要的！
4. 保留所有原始内容 - 不要总结或省略任何内容

段落聚合规则（重要！）：
- **每段应包含 4-6 句话**，讨论同一个主题或观点
- **不要一句一段** - 必须将相关句子合并
- 相关的引用、解释、例证应该在同一段落中
- 只在主题明显转换时才开始新段落
- 段落之间用一个空行分隔

小标题规则：
- 使用 ### 作为小标题（例如："### 引言"、"### 要点一：人类的终极问题"）
- 小标题要有描述性和意义
- 典型讲道结构：引言 → 2-4个要点 → 应用 → 结论

讲道标题：{title if title else "未命名"}

中文翻译：
{text[:15000]}  # 限制输入长度

输出格式示例：
### 引言

欢迎来到《福音与生活》。当你认识的某个人在思考人生最深刻的问题时——我是谁？世界出了什么问题？什么真正能让我整全？耶稣不仅仅是给我们答案，他把他自己给了我们。在本月的播客中，提摩太·凯勒探讨我们如何能在基督里分享我们所拥有的盼望，作为一个人对意义和目的的追寻的答案。

如你所知，八月是《福音与生活》的"去并分享月"，我们精心策划了一系列免费资源来帮助你采取简单的步骤与神在你生活中所放置的某个人分享福音。你可以在 gospelandlife.com/share 访问这些资源。我们相信神使用小行为来做大事，我们邀请你在这个月做简单、小的行为去并分享福音，因为福音改变一切。

现在按照上述格式处理以下内容："""

        try:
            result = self._call_llm(prompt)

            if result:
                print(f"✅ 智能美化完成")
                return result
            else:
                print(f"⚠️  LLM 美化失败，使用基础格式化")
                return self._basic_beautify_chinese(text)

        except Exception as e:
            print(f"⚠️  LLM 美化出错: {e}")
            print(f"   使用基础格式化")
            return self._basic_beautify_chinese(text)

    def beautify_outline(self, outline: str, transcript: str = "") -> str:
        """
        智能优化大纲：
        1. 从转录中提取主要观点
        2. 创建清晰的层级结构
        3. 使用编号格式
        """
        if outline and len(outline) > 100:
            # 如果已有完整大纲，只做基础格式化
            return self._basic_beautify_outline(outline)

        if not transcript:
            return outline

        print(f"✨ 使用 LLM 生成大纲...")

        prompt = f"""Create a sermon outline based on this transcript.

TASK:
1. Identify 2-4 main points from the sermon
2. Create a hierarchical outline with sub-points
3. Use numbered format (1., 2., 3.) for main points
4. Use bullet points (   -) for sub-points

FORMAT:
1. Main Point One
   - Sub-point
   - Sub-point
2. Main Point Two
   - Sub-point

TRANSCRIPT:
{transcript[:8000]}  # 限制输入

OUTPUT: Return only the outline in the format above."""

        try:
            result = self._call_llm(prompt)

            if result:
                print(f"✅ 大纲生成完成")
                return result
            else:
                print(f"⚠️  大纲生成失败")
                return outline

        except Exception as e:
            print(f"⚠️  大纲生成出错: {e}")
            return outline

    def _basic_beautify(self, text: str) -> str:
        """基础英文格式化（后备方案）"""
        import re

        # 每3-4句分段
        sentences = re.split(r'([.!?])\s+', text)
        paragraphs = []
        current = ""
        count = 0

        for i in range(0, len(sentences) - 1, 2):
            if i + 1 < len(sentences):
                sentence = sentences[i] + sentences[i + 1]
                current += sentence + " "
                count += 1

                if count >= 3:
                    paragraphs.append(current.strip())
                    current = ""
                    count = 0

        if current.strip():
            paragraphs.append(current.strip())

        return "\n\n".join(paragraphs)

    def _basic_beautify_chinese(self, text: str) -> str:
        """基础中文格式化（后备方案）"""
        import re

        # 按中文句号分段
        text = re.sub(r'([。！？])\s*([^》\n])', r'\1\n\n\2', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def _basic_beautify_outline(self, outline: str) -> str:
        """基础大纲格式化"""
        # 导入基础美化器
        try:
            from md_beautifier import beautify_outline
            return beautify_outline(outline)
        except:
            return outline


class ChunkedSmartBeautifier(SmartBeautifier):
    """
    分块智能美化器
    处理长文本时分块处理，然后合并
    """

    def __init__(self, backend_name: str, client, chunk_size: int = 8000):
        super().__init__(backend_name, client)
        self.chunk_size = chunk_size

    def beautify_transcript(self, text: str, title: str = "") -> str:
        """分块美化长转录"""
        if len(text) < self.chunk_size:
            return super().beautify_transcript(text, title)

        print(f"📄 文本较长 ({len(text)} 字符)，将分块处理...")

        # 按段落分块
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = []
        current_size = 0

        for para in paragraphs:
            para_size = len(para)
            if current_size + para_size > self.chunk_size and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = [para]
                current_size = para_size
            else:
                current_chunk.append(para)
                current_size += para_size

        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))

        print(f"   分为 {len(chunks)} 块处理")

        # 处理每块
        beautified_chunks = []
        for i, chunk in enumerate(chunks):
            print(f"   处理第 {i+1}/{len(chunks)} 块...")
            result = super().beautify_transcript(chunk, title)
            beautified_chunks.append(result)

        # 合并
        return "\n\n---\n\n".join(beautified_chunks)

    def beautify_translation(self, text: str, title: str = "") -> str:
        """分块美化长翻译"""
        if len(text) < self.chunk_size:
            return super().beautify_translation(text, title)

        print(f"📄 文本较长 ({len(text)} 字符)，将分块处理...")

        # 按段落分块
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = []
        current_size = 0

        for para in paragraphs:
            para_size = len(para)
            if current_size + para_size > self.chunk_size and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = [para]
                current_size = para_size
            else:
                current_chunk.append(para)
                current_size += para_size

        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))

        print(f"   分为 {len(chunks)} 块处理")

        # 处理每块
        beautified_chunks = []
        for i, chunk in enumerate(chunks):
            print(f"   处理第 {i+1}/{len(chunks)} 块...")
            result = super().beautify_translation(chunk, title)
            beautified_chunks.append(result)

        # 合并
        return "\n\n---\n\n".join(beautified_chunks)


def main():
    """命令行接口"""
    import argparse

    parser = argparse.ArgumentParser(
        description="智能美化讲道内容"
    )
    parser.add_argument(
        "--file",
        required=True,
        help="讲道文件名（不含.md）"
    )
    parser.add_argument(
        "--backend",
        choices=["ollama", "claude"],
        help="指定后端（默认：自动选择）"
    )
    parser.add_argument(
        "--transcript-only",
        action="store_true",
        help="只美化英文转录"
    )
    parser.add_argument(
        "--translation-only",
        action="store_true",
        help="只美化中文翻译"
    )

    args = parser.parse_args()

    # 获取后端
    try:
        backend_name, client = get_translation_backend(args.backend)
        print(f"✅ 使用后端: {backend_name}")
    except Exception as e:
        print(f"❌ 后端初始化失败: {e}")
        sys.exit(1)

    # 创建美化器
    beautifier = ChunkedSmartBeautifier(backend_name, client)

    # 读取讲道文件
    base_dir = Path(__file__).parent.parent
    sermon_folder = base_dir / "sermons" / args.file

    if not sermon_folder.exists():
        print(f"❌ 讲道文件夹不存在: {sermon_folder}")
        sys.exit(1)

    # 读取元数据
    metadata_path = sermon_folder / "metadata.json"
    title = ""
    if metadata_path.exists():
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
            title = metadata.get("title", "")

    # 美化转录
    if not args.translation_only:
        transcript_path = sermon_folder / "transcript.md"
        if transcript_path.exists():
            print(f"\n📖 读取英文转录...")
            transcript = transcript_path.read_text(encoding='utf-8')

            # 提取内容（去掉标题）
            import re
            content_match = re.search(r'## English Transcript\s*\n+(.*)', transcript, re.DOTALL)
            if content_match:
                content = content_match.group(1).strip()
            else:
                content = transcript

            print(f"   原始长度: {len(content)} 字符")

            # 美化
            beautified = beautifier.beautify_transcript(content, title)

            # 写回文件
            output = f"# {title}\n\n## English Transcript\n\n{beautified}\n"
            transcript_path.write_text(output, encoding='utf-8')
            print(f"✅ 已保存美化后的转录")

    # 美化翻译
    if not args.transcript_only:
        translation_path = sermon_folder / "translation.md"
        if translation_path.exists():
            print(f"\n📖 读取中文翻译...")
            translation = translation_path.read_text(encoding='utf-8')

            # 提取内容（去掉标题）
            import re
            content_match = re.search(r'## Chinese Translation.*?\n+(.*)', translation, re.DOTALL)
            if content_match:
                content = content_match.group(1).strip()
            else:
                content = translation

            print(f"   原始长度: {len(content)} 字符")

            # 美化
            beautified = beautifier.beautify_translation(content, title)

            # 写回文件
            output = f"# {title}\n\n## Chinese Translation / 中文翻译\n\n{beautified}\n"
            translation_path.write_text(output, encoding='utf-8')
            print(f"✅ 已保存美化后的翻译")

    print(f"\n🎉 美化完成！")


if __name__ == "__main__":
    main()
