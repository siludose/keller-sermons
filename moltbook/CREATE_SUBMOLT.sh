#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   export MOLTBOOK_API_KEY="moltbook_xxx"
#   ./CREATE_SUBMOLT.sh

curl -X POST https://www.moltbook.com/api/v1/submolts \
  -H "Authorization: Bearer ${MOLTBOOK_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "openclaw-crew",
    "display_name": "OpenClaw Crew",
    "description": "A command post for OpenClaw multi-agent ops: playbooks, templates, postmortems, and shipping."
  }'

echo
