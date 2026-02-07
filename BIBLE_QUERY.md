# Bible Query (gitbook-holy-bible-niv-chinese)

This repo includes a small local index + query tool for the downloaded GitBook Bible content.

## Data Source

The tool expects the GitBook markdown files to exist at:

`/Volumes/Macintosh Extra/Code/keller-sermons/bibles_downloads/gitbook-holy-bible-niv-chinese/src/*.md`

Those files come from the GitHub repo:

`zergtant/gitbook-holy-bible-niv-chinese`

## Build The Index (One Time)

Build a local JSONL index:

```bash
python3 /Volumes/Macintosh Extra/Code/keller-sermons/scripts/bible_index.py build
```

Output file:

`/Volumes/Macintosh Extra/Code/keller-sermons/bibles_downloads/gitbook-holy-bible-niv-chinese/index.jsonl`

## Query A Verse

Query by full book name:

```bash
python3 /Volumes/Macintosh Extra/Code/keller-sermons/scripts/bible_index.py q --book 列王纪上 --chapter 1 --verse 1
```

Query by the book abbreviation used in this dataset:

```bash
python3 /Volumes/Macintosh Extra/Code/keller-sermons/scripts/bible_index.py q --book 王上 --chapter 1 --verse 2
```

Return raw JSON:

```bash
python3 /Volumes/Macintosh Extra/Code/keller-sermons/scripts/bible_index.py q --book 王上 --chapter 1 --verse 2 --json
```

## Notes

- Output includes both English and Chinese lines as stored in the GitBook markdown.
- The generated `index.jsonl` is intentionally not committed (see `.gitignore`).

