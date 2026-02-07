---
name: keller-cuv-rewrite
description: Rewrite Keller sermon Chinese chunks to 1:1 align with English and replace explicit scripture quotes with CUV (CUS) text from local bible/CUS. Use when updating Keller sermon translations or generating Chinese transcripts with strict sentence alignment and CUV scripture.
---

# Keller CUV Rewrite

Use this skill to rewrite Keller sermon Chinese chunks in `_chunks/<sermon>/NNN.zh.txt` so they align closely (sentence-by-sentence) with the English source, while replacing explicit scripture quotes with CUV (cus) text from `bible/CUS`.

## Workflow

1. **Open the target sermon**
   - English source: `_chunks/<sermon>/NNN.en.txt`
   - Chinese target: `_chunks/<sermon>/NNN.zh.txt`

2. **Rewrite rules**
   - **1:1 alignment**: keep sentence order; avoid merging multiple English sentences into one Chinese sentence.
   - **No omissions**: do not drop content unless it is a repeated sentence in the English.
   - **Scripture replacement**:
     - If the English explicitly cites a verse (e.g., “John 3:16”, “Romans 8:32”), replace the Chinese quote with the CUV (CUS) text from `bible/CUS/<Book>.md`.
     - If the English only paraphrases scripture without a clear reference, keep it as natural translation (do not force a CUV quote).
   - **Tone**: keep neutral, faithful, no embellishment.
   - **Paragraphs**: preserve paragraph boundaries and blank lines.

3. **Update the main sermon file**
   - Merge all `NNN.zh.txt` into `Jesus_Our_Gift.md` under a new section `## Chinese Transcript / 中文`.
   - Use the helper script: `python3 skills/public/keller-cuv-rewrite/scripts/merge_chunks.py --sermon <sermon>.md`.

4. **Commit & push**
   - `git add <sermon>.md`
   - `git commit -m "feat: add CUV-aligned Chinese transcript for <sermon>"`
   - `git push origin main`

## References

- **CUV text source**: `bible/CUS/*.md`
- **Rewrite standard**: `skills/public/keller-cuv-rewrite/references/standard.md`
