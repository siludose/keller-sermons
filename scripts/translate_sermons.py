#!/usr/bin/env python3
"""Disabled legacy root-Markdown translator; see docs/CONTENT_SOP.md.

The former implementation translated only the first 3,000 characters and wrote
root-level Markdown, not the current sermons/<name>/translation.md layout.
Keep this entry point as a dependency-free failure for old commands and jobs.
It deliberately performs no source reads, network requests, or file writes.
"""

import sys


DEPRECATION_MESSAGE = (
    "ERROR: scripts/translate_sermons.py is deprecated and disabled.\n"
    "The legacy root-Markdown translator truncated source text to 3,000 "
    "characters and is unsafe for complete sermons.\n"
    "Manually prepare and source-check the complete translation in "
    "sermons/<name>/translation.md against sermons/<name>/transcript.md; "
    "see docs/CONTENT_SOP.md.\n"
    "Other translation scripts have not been verified as safe replacements. "
    "No API calls or file writes were performed."
)


def main(argv=None):
    """Reject every legacy invocation, including --help, without side effects."""
    print(DEPRECATION_MESSAGE, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
