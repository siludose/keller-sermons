#!/usr/bin/env python3
"""
Sermon Data Model
Unified data structure for sermons, supporting conversion between legacy and new formats.
"""

import re
import json
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any
from pathlib import Path


@dataclass
class SermonMetadata:
    """Structured sermon metadata"""
    title: str
    speaker: str = "Tim Keller"
    date: str = ""
    scripture: str = ""
    series: str = ""
    apple_podcast_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {k: v for k, v in asdict(self).items() if v}


class Sermon:
    """
    Unified sermon representation supporting both legacy and new formats.

    Legacy format: Single MD file with sections
    New format: Folder with separate files
    """

    def __init__(
        self,
        metadata: SermonMetadata,
        outline: str = "",
        transcript: str = "",
        translation: str = ""
    ):
        self.metadata = metadata
        self.outline = outline.strip()
        self.transcript = transcript.strip()
        self.translation = translation.strip()

    @classmethod
    def from_legacy_md(cls, path: Path) -> 'Sermon':
        """
        Parse a legacy sermon MD file.

        Expected format:
        # Title

        ## Sermon Outline / 讲道大纲
        [outline content]

        ---

        ## English Transcript / 英文原文
        [transcript content]

        ---

        ## Chinese Translation / 中文翻译
        [translation content]
        """
        if not path.exists():
            raise FileNotFoundError(f"Sermon file not found: {path}")

        content = path.read_text(encoding='utf-8')

        # Extract title (first # heading)
        title_match = re.search(r'^#\s+(.+?)$', content, re.MULTILINE)
        if not title_match:
            # Fallback to filename
            title = path.stem.replace('_', ' ')
        else:
            title = title_match.group(1).strip()

        # Extract metadata if present (between title and first section)
        metadata_section = ""
        if title_match:
            after_title = content[title_match.end():]
            first_section = re.search(r'^##\s+', after_title, re.MULTILINE)
            if first_section:
                metadata_section = after_title[:first_section.start()].strip()

        # Parse metadata fields
        scripture = ""
        date = ""
        series = ""

        if metadata_section:
            scripture_match = re.search(r'\*\*Scripture[:\s]+\*\*\s*(.+?)(?:\n|$)', metadata_section, re.IGNORECASE)
            if scripture_match:
                scripture = scripture_match.group(1).strip()

            date_match = re.search(r'\*\*Date[:\s]+\*\*\s*(.+?)(?:\n|$)', metadata_section, re.IGNORECASE)
            if date_match:
                date = date_match.group(1).strip()

            series_match = re.search(r'\*\*Series[:\s]+\*\*\s*(.+?)(?:\n|$)', metadata_section, re.IGNORECASE)
            if series_match:
                series = series_match.group(1).strip()

        metadata = SermonMetadata(
            title=title,
            scripture=scripture,
            date=date,
            series=series
        )

        # Extract sections using regex
        outline = cls._extract_section(content, [
            r'##\s+Sermon Outline\s*/\s*讲道大纲',
            r'##\s+Sermon Outline',
            r'##\s+Outline'
        ])

        transcript = cls._extract_section(content, [
            r'##\s+English Transcript\s*/\s*英文原文',
            r'##\s+English Transcript',
            r'##\s+Transcript',
            r'###\s+English'  # Handle subsection format
        ])

        # Special handling for "Full Transcript" format with subsections
        if not transcript:
            full_transcript_match = re.search(r'##\s+Full Transcript\s*/\s*完整文本', content, re.IGNORECASE)
            if full_transcript_match:
                # Look for ### English subsection
                english_match = re.search(r'###\s+English\s*\n', content[full_transcript_match.end():])
                if english_match:
                    start = full_transcript_match.end() + english_match.end()
                    # Find next ### or ## or ---
                    next_section = re.search(r'\n(###\s+|##\s+|---)', content[start:])
                    if next_section:
                        end = start + next_section.start()
                    else:
                        end = len(content)
                    transcript = content[start:end].strip()

        translation = cls._extract_section(content, [
            r'##\s+Chinese Translation\s*/\s*中文翻译',
            r'##\s+Chinese Translation',
            r'##\s+Translation',
            r'###\s+中文翻译'  # Handle subsection format
        ])

        # Special handling for "Full Transcript" format with Chinese subsection
        if not translation:
            full_transcript_match = re.search(r'##\s+Full Transcript\s*/\s*完整文本', content, re.IGNORECASE)
            if full_transcript_match:
                # Look for ### 中文翻译 subsection
                chinese_match = re.search(r'###\s+中文翻译\s*\n', content[full_transcript_match.end():])
                if chinese_match:
                    start = full_transcript_match.end() + chinese_match.end()
                    # Find next ### or ## or ---
                    next_section = re.search(r'\n(###\s+|##\s+|---)', content[start:])
                    if next_section:
                        end = start + next_section.start()
                    else:
                        end = len(content)
                    translation = content[start:end].strip()

        # Fallback: if transcript is empty, look for any content after ---
        if not transcript and '---' in content:
            parts = re.split(r'\n---+\n', content)
            if len(parts) >= 2:
                # Usually: [header+outline, transcript, translation]
                if len(parts) >= 2:
                    transcript = parts[1].strip()
                if len(parts) >= 3:
                    translation = parts[2].strip()

        return cls(
            metadata=metadata,
            outline=outline,
            transcript=transcript,
            translation=translation
        )

    @staticmethod
    def _extract_section(content: str, patterns: List[str]) -> str:
        """
        Extract content between section header and next ## header or ---
        Tries multiple header patterns in order.
        """
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                # Find content from match end to next ## or ---
                start = match.end()
                # Look for next section marker
                next_section = re.search(r'\n(##\s+|---)', content[start:])
                if next_section:
                    end = start + next_section.start()
                else:
                    end = len(content)

                section_content = content[start:end].strip()
                # Remove leading/trailing separators
                section_content = re.sub(r'^---+\n', '', section_content)
                section_content = re.sub(r'\n---+$', '', section_content)
                return section_content.strip()

        return ""

    def to_new_structure(self, output_dir: Path) -> None:
        """
        Write sermon to new folder structure.

        Creates:
        - {output_dir}/metadata.json
        - {output_dir}/outline.md
        - {output_dir}/transcript.md
        - {output_dir}/translation.md
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        # Write metadata
        metadata_path = output_dir / "metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.metadata.to_dict(), f, indent=2, ensure_ascii=False)

        # Write outline
        if self.outline:
            outline_path = output_dir / "outline.md"
            outline_path.write_text(
                f"# {self.metadata.title}\n\n## Sermon Outline / 讲道大纲\n\n{self.outline}\n",
                encoding='utf-8'
            )

        # Write transcript
        if self.transcript:
            transcript_path = output_dir / "transcript.md"
            transcript_path.write_text(
                f"# {self.metadata.title}\n\n## English Transcript\n\n{self.transcript}\n",
                encoding='utf-8'
            )

        # Write translation
        if self.translation:
            translation_path = output_dir / "translation.md"
            translation_path.write_text(
                f"# {self.metadata.title}\n\n## Chinese Translation / 中文翻译\n\n{self.translation}\n",
                encoding='utf-8'
            )

    def validate(self) -> List[str]:
        """
        Validate sermon completeness and return list of issues.
        Empty list means no issues found.
        """
        issues = []

        if not self.metadata.title:
            issues.append("Missing title")

        if not self.transcript:
            issues.append("Missing English transcript")

        if not self.translation:
            issues.append("Missing Chinese translation")

        # Warn about missing outline (not critical)
        if not self.outline:
            issues.append("Warning: Missing outline (not critical)")

        # Check for suspiciously short content
        if self.transcript and len(self.transcript) < 500:
            issues.append(f"Transcript seems too short ({len(self.transcript)} chars)")

        if self.translation and len(self.translation) < 500:
            issues.append(f"Translation seems too short ({len(self.translation)} chars)")

        # Check for encoding issues (common problem markers)
        encoding_markers = ['�', '\x00', '\ufffd']
        for marker in encoding_markers:
            if marker in self.transcript:
                issues.append("Transcript contains encoding errors")
                break
            if marker in self.translation:
                issues.append("Translation contains encoding errors")
                break

        return issues

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the sermon content"""
        return {
            "title": self.metadata.title,
            "has_outline": bool(self.outline),
            "has_transcript": bool(self.transcript),
            "has_translation": bool(self.translation),
            "outline_length": len(self.outline),
            "transcript_length": len(self.transcript),
            "translation_length": len(self.translation),
            "transcript_words": len(self.transcript.split()) if self.transcript else 0,
        }


def main():
    """CLI for testing sermon model"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python sermon_model.py <sermon_file.md>")
        sys.exit(1)

    sermon_path = Path(sys.argv[1])

    try:
        sermon = Sermon.from_legacy_md(sermon_path)

        print(f"📖 Parsed: {sermon.metadata.title}")
        print(f"\nMetadata:")
        print(f"  Speaker: {sermon.metadata.speaker}")
        print(f"  Date: {sermon.metadata.date or 'N/A'}")
        print(f"  Scripture: {sermon.metadata.scripture or 'N/A'}")
        print(f"  Series: {sermon.metadata.series or 'N/A'}")

        print(f"\nContent:")
        print(f"  Outline: {'✓' if sermon.outline else '✗'} ({len(sermon.outline)} chars)")
        print(f"  Transcript: {'✓' if sermon.transcript else '✗'} ({len(sermon.transcript)} chars)")
        print(f"  Translation: {'✓' if sermon.translation else '✗'} ({len(sermon.translation)} chars)")

        issues = sermon.validate()
        if issues:
            print(f"\n⚠️  Issues found:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print(f"\n✅ No issues found")

        # Test writing to new structure
        if '--test-output' in sys.argv:
            test_output = Path("test_output") / sermon_path.stem
            sermon.to_new_structure(test_output)
            print(f"\n📁 Test output written to: {test_output}")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
