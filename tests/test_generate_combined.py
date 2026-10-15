"""Offline regression tests: python -m unittest discover -s tests -v."""
import contextlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('generate_combined', ROOT / 'scripts/generate_combined.py')
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)


class CombinedTests(unittest.TestCase):
    def assert_sources(self, en, zh):
        output = generator.render_combined({'title_zh': '标题', 'title_en': 'Title'}, en, zh)
        prefix, body = output.split('## 英文原文 / English source\n\n', 1)
        actual_en, actual_zh = body.split('\n\n---\n\n## 中文译文 / Chinese source\n\n', 1)
        self.assertEqual(actual_en, en)
        self.assertEqual(actual_zh, zh + '\n\n<!-- End of Chinese source -->\n')
        self.assertIn('alignment has not been verified', prefix)
        return output

    def test_preamble_before_first_heading_preserved(self):
        self.assert_sources('# Title\n\nScripture and roadmap.\n### First\nBody',
                            '# 标题\n\n经文与引言。\n### 第一\n内容')

    def test_equal_heading_counts_are_not_assumed_aligned(self):
        self.assert_sources('### Alpha\nFirst\n### Beta\nSecond',
                            '### 乙\n第二\n### 甲\n第一')

    def test_one_sided_and_mismatched_headings(self):
        for en in ('Plain text\n\nLast paragraph', '### A\nOne\n### B\nTwo'):
            with self.subTest(en=en):
                self.assert_sources(en, '### 一\n甲\n### 二\n乙\n### 三\n丙')

    def test_flat_text_empty_and_markdown_preserved(self):
        for en, zh in [('', ''), ('Before\n## Arbitrary\nAfter\n---\nEnd', '全文'),
                       ('```md\n### Not a heading\n```\n> quotation\n', '末尾\n\n'),
                       ('Windows\r\n\r\n### Header\r\nBody', '汉字\r\n')]:
            with self.subTest(en=en):
                self.assert_sources(en, zh)

    def test_credits_are_preserved_not_invented(self):
        output = self.assert_sources('Original transcript', '译文\n*翻译整理：原作者*')
        self.assertEqual(output.count('*翻译整理：原作者*'), 1)
        self.assertNotIn('小雷', output)

    def test_generation_skip_overwrite_and_missing_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sermon = root / 'sermons' / 'Example'
            sermon.mkdir(parents=True)
            en = '# Example\r\n\r\nBefore\r\n### Section\r\nBody'
            zh = '# 示例\n全文\n'
            (sermon / 'transcript.md').write_bytes(en.encode())
            (sermon / 'translation.md').write_bytes(zh.encode())
            with patch.object(generator, 'SERMONS_DIR', str(root / 'sermons')), patch.object(generator, 'COMBINED_DIR', str(root / 'combined')), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(generator.generate_combined('Example'), 'ok')
                output = root / 'combined' / 'Example.md'
                self.assertIn(en.encode(), output.read_bytes())
                self.assertIn(zh.encode(), output.read_bytes())
                first = output.read_bytes()
                self.assertEqual(generator.generate_combined('Example'), 'skip')
                self.assertEqual(generator.generate_combined('Example', True), 'ok')
                self.assertEqual(output.read_bytes(), first)
                (sermon / 'translation.md').unlink()
                self.assertEqual(generator.generate_combined('Example', True), 'error')
                self.assertEqual(output.read_bytes(), first)

    def test_real_sermon_sources_are_complete(self):
        for name in ('Peace', 'Kindness', 'Patience'):
            with self.subTest(name=name):
                folder = ROOT / 'sermons' / name
                self.assert_sources((folder / 'transcript.md').read_text(),
                                    (folder / 'translation.md').read_text())

    def test_committed_combined_files_match_generator(self):
        for name in ('Peace', 'Kindness', 'Patience'):
            with self.subTest(name=name):
                folder = ROOT / 'sermons' / name
                en = generator.read_file(folder / 'transcript.md')
                zh = generator.read_file(folder / 'translation.md')
                meta = generator.extract_metadata(zh, en, folder / 'metadata.json')
                expected = generator.render_combined(meta, en, zh)
                self.assertEqual((ROOT / 'combined' / (name + '.md')).read_bytes(),
                                 expected.encode('utf-8'))


if __name__ == '__main__':
    unittest.main()
