# Targeted content corrections

Reviewed on 2026-10-15. This is a bounded correction record, not a claim that either sermon has been fully proofread or verified against audio. Formatting and bilingual generation are separate from these editorial changes.

## Peace

- In `sermons/Peace/transcript.md`, corrected `piece` to `peace` where the surrounding discussion clearly means God's peace, developing peace, or the contrast between “stupid” and “smart” peace. Corrected `Stupid pieces.` to `Stupid peace.` without adding conjectural connective words. Corrected `the reason we don't have pieces, we're` to `the reason we don't have peace is, we're`.
- Preserved the genuine phrase `torn into pieces`, which describes debilitating worry tearing a person apart.
- In `sermons/Peace/translation.md`, changed `愚蠢的部分`, `聪明的部分`, and the corresponding `基督徒的部分` to `愚蠢的平安`, `聪明的平安`, and `基督徒的平安`. These follow the surrounding English argument, rather than a fresh audio transcription.
- Added metadata: sermon date `2010-04-25`, Scripture `Philippians 4:4-12`, and series `The Real Signs of the Spirit`. The date is the sermon date, not the podcast publication date.

Sources:

- [Official Peace sermon page](https://gospelinlife.com/sermon/peace-4/): date, Scripture, series, speaker, and outline.
- [Official Peace podcast episode](https://podcast.gospelinlife.com/e/peace/): independently identifies the sermon date and Scripture. Its publication date is November 10, 2025.
- [MP3 linked in the official episode HTML](https://mcdn.podbean.com/mf/web/yu5qse6iv29qsbb8/251110_Peace.mp3): availability checked with HTTP HEAD (200, `audio/mpeg`, 38,628,096 bytes). Availability does not mean the recording has been listened to or the transcript verified.

### Remaining uncertainty

No audio listening/transcription capability was available in this review. Unclear phrases such as `an equal living`, `Barnes and Noble Reborder's bookstore`, `here's what the woman never do`, `myron mud`, and `peace and fallible` remain unchanged and require listening against the official recording. The `couple` / `一对夫妇` passage and the transition from thinking to thanking (including repeated thinking in Chinese and `you think` in the request/thanksgiving passage) also remain unresolved. Do not infer exact spoken wording from these suspected recognition errors. These repairs do not certify the rest of the English transcript or Chinese translation, including other Scripture quotations.

## Patience

- Replaced only the corrupt opening Chinese reading of Romans 12:10–21 in `sermons/Patience/translation.md`. It previously included unrelated material and omitted substantial portions of the announced passage.
- The replacement uses repository file `bibles/CUNPS.json`: book `45`, chapter `12`, verses `10` through `21`, in verse order. It is explicitly labeled 和合本新标点版 (CUNPS). HTML styling tags were stripped while retaining their text, including variant-reading notes. This is a sourced Chinese Bible quotation, not a claim to reproduce every word of the English reading's translation.
- Preserved the introduction before the passage and all commentary beginning with `这是神的话语。` after it.
- Added metadata: sermon date `2010-05-02`, catalog Scripture `Romans 12:9-21`, and series `The Real Signs of the Spirit`.
- Kept the distinction between catalog Scripture (`scripture`) and the reading announced in the existing English transcript (`scripture_reading`: `Romans 12:10-21`). The latter has not been independently confirmed by listening.

Sources:

- [Official Patience sermon page](https://gospelinlife.com/sermon/patience-3/): date, catalog Scripture, series, and speaker.
- `sermons/Patience/transcript.md`, “Introduction and Scripture Reading”: announcement of Romans 12:10–21 and the corresponding English reading.
- `bibles/CUNPS.json`: existing local Chinese Bible text, as identified above. The Bible dataset is unchanged.

## Validation scope

`tests/test_sermon_corrections.py` checks the twelve sourced Patience verses in order, targeted Peace homophones and retained `torn into pieces`, and the metadata distinction. These are bounded regression tests, not a whole-sermon quality assessment. Derived bilingual output was regenerated for Peace, Kindness, and Patience only. All 12 offline regression tests pass; a non-mutating source-inclusion smoke check covers all 97 sermon pairs. This checks preservation, not translation accuracy.


## Combined-generation repair

The old generator discarded text before the first `###` heading. The existing Peace output omitted 1,099 English words in 33 preamble paragraphs; Kindness omitted 271 English words in 7 preamble paragraphs. The repaired generator embeds both complete source files verbatim, preserving headings, Scripture, introductory roadmaps, dividers, and existing credits.

No verified alignment map exists in the repository. Matching heading counts and proportional paragraph splitting cannot establish semantic correspondence, so the generated files explicitly present unaligned full English and Chinese texts. This favors complete, honest presentation over guessed alternating sections. Only the three named combined files were regenerated; other existing publications have not been re-audited or regenerated.

The obsolete `scripts/translate_sermons.py` entry point is disabled before dependencies, network calls, or writes because its former implementation silently truncated input to 3,000 characters and used the old root-file layout. Other translation engines are not certified by these repairs. The current workflow and test command are documented in `CONTENT_SOP.md`.
