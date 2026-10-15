"""Bounded regressions for sourced editorial repairs, not overall sermon accuracy."""
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


def read_sermon(name, filename):
    return (ROOT / 'sermons' / name / filename).read_text(encoding='utf-8')


class SermonCorrectionTests(unittest.TestCase):
    def test_patience_opening_matches_local_cunps_verses_in_order(self):
        bible = json.loads((ROOT / 'bibles/CUNPS.json').read_text(encoding='utf-8'))
        verses = [v for v in bible if v['book'] == 45 and v['chapter'] == 12
                  and 10 <= v['verse'] <= 21]
        self.assertEqual([v['verse'] for v in verses], list(range(10, 22)))
        expected = '\n\n'.join(re.sub(r'<[^>]+>', '', v['text']) for v in verses)
        translation = read_sermon('Patience', 'translation.md')
        marker = '圣经经文来自罗马书第12章第10节至第21节（以下经文采用和合本新标点版，CUNPS）：\n\n'
        reading = translation.split(marker, 1)[1].split('\n\n这是神的话语。', 1)[0]
        self.assertEqual(reading, expected)

    def test_peace_targeted_homophones(self):
        transcript = read_sermon('Peace', 'transcript.md')
        for phrase in ('this peace of God', 'character of this peace.',
                       'develop this peace', 'a stupid peace', 'a smart peace',
                       'Stupid peace.', "Christian's peace",
                       "the reason we don't have peace is, we're"):
            self.assertIn(phrase, transcript)
        self.assertIn('torn into pieces', transcript)
        self.assertNotIn('this piece of God', transcript)
        self.assertNotIn('stupid piece', transcript)
        self.assertNotIn('smart piece', transcript)
        self.assertNotIn("don't have pieces", transcript)
        translation = read_sermon('Peace', 'translation.md')
        for adjective in ('愚蠢', '聪明', '基督徒'):
            self.assertIn(adjective + '的平安', translation)
            self.assertNotIn(adjective + '的部分', translation)

    def test_official_metadata_and_announced_reading_are_distinct(self):
        peace = json.loads(read_sermon('Peace', 'metadata.json'))
        patience = json.loads(read_sermon('Patience', 'metadata.json'))
        self.assertEqual(peace['date'], '2010-04-25')
        self.assertEqual(peace['scripture'], 'Philippians 4:4-12')
        self.assertEqual(peace['scripture_reading'], 'Philippians 4:4-12')
        self.assertEqual(peace['source_url'], 'https://gospelinlife.com/sermon/peace-4/')
        self.assertEqual(patience['date'], '2010-05-02')
        self.assertEqual(patience['scripture'], 'Romans 12:9-21')
        self.assertEqual(patience['scripture_reading'], 'Romans 12:10-21')
        self.assertEqual(patience['source_url'], 'https://gospelinlife.com/sermon/patience-3/')
        self.assertIn('Romans chapter 12 verses 10 through 21',
                      read_sermon('Patience', 'transcript.md'))
        for metadata in (peace, patience):
            self.assertEqual(metadata['series'], 'The Real Signs of the Spirit')


if __name__ == '__main__':
    unittest.main()
