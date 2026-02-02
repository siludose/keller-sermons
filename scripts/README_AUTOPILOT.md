# Keller Sermons Autopilot (helper script)

This repo has a lot of long transcripts. We translate them by splitting into chunks under `_chunks/<file>.md/*.en.txt` and producing matching `*.zh.txt`.

Because LLM translation runs via OpenClaw sub-agents (tooling), the **helper script is intentionally deterministic**: it does *not* call any model APIs.

## What it does

- **status**: show chunk completion + remaining `md` files with low Chinese ratio.
- **chunk-next**: create a new `_chunks/<file>/` directory for the next `*.md` needing work.
- **stitch-ready**: for chunk dirs where `zh == en`, stitch Chinese back into the `.md` and **commit+push** (only if `git diff` shows changes).
- **plan**: output JSON with `stitch_ready`, `translate_missing`, and `chunk_next`.

## Usage

From repo root:

```bash
python3 scripts/keller_autopilot.py status
python3 scripts/keller_autopilot.py chunk-next
python3 scripts/keller_autopilot.py stitch-ready
python3 scripts/keller_autopilot.py plan
```

## Notes

- The script commits **only root `*.md` files** (never commits `_chunks/`).
- Commit messages follow: `Add full Chinese translation: <Title>`.
- It is **idempotent**: rerunning should not spam commits.
