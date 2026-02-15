#!/bin/bash
set -e

SERMONS_DIR="/home/node/clawd/keller_sermons"
cd "$SERMONS_DIR"

# Episode data (title|date|url)
EPISODES=(
  "Overflowing Joy|2026-Jan-26|https://mcdn.podbean.com/mf/web/vaccbqjy98fzw6nm/260126_OverflowingJoy.mp3"
  "Sex and the End of Loneliness|2026-Jan-23|https://mcdn.podbean.com/mf/web/tbbxqkgkc2fgsq89/260123_SexAndTheEndOfLoneliness.mp3"
  "Love Your Enemies|2026-Jan-21|https://mcdn.podbean.com/mf/web/n9ycjfr8hhp3hrdb/260121_LoveYourEnemies.mp3"
  "Aggressive Compassion|2026-Jan-19|https://mcdn.podbean.com/mf/web/6ewzmmn7cxik64h4/260119_AggressiveCompassion.mp3"
  "Secret Treason|2026-Jan-16|https://mcdn.podbean.com/mf/web/cfj8gn8iyyfy9h5a/260116_SecretTreason.mp3"
  "Orphans or Children|2026-Jan-14|https://mcdn.podbean.com/mf/web/5ghxwdc2mqm4xj6z/260114_OrphansOrChildren.mp3"
  "Entering His Rest|2026-Jan-12|https://mcdn.podbean.com/mf/web/69mjmxf4nvig3uis/260112_EnteringHisRest.mp3"
  "First of All|2026-Jan-09|https://mcdn.podbean.com/mf/web/t47gk45hw25vgxdn/260109_FirstOfAll.mp3"
  "Gods Law|2026-Jan-07|https://mcdn.podbean.com/mf/web/t43wn6mj2zmd5cg8/260107_GodsLaw.mp3"
)

process_episode() {
  local title="$1"
  local date="$2"
  local url="$3"
  
  local safe_title=$(echo "$title" | tr ' ' '_' | tr -cd '[:alnum:]_-')
  local audio_file="${safe_title}.mp3"
  local compressed_file="${safe_title}_compressed.mp3"
  local transcript_file="${safe_title}_transcript.txt"
  local md_file="${safe_title}.md"
  
  # Skip if already done
  if [ -f "$md_file" ]; then
    echo "⏭️  Already processed: $title"
    return 0
  fi
  
  echo "========================================"
  echo "Processing: $title"
  echo "========================================"
  
  # Step 1: Download
  if [ ! -f "$audio_file" ]; then
    echo "📥 Downloading..."
    curl -sL "$url" -o "$audio_file"
  fi
  
  # Step 2: Compress for Whisper (< 25MB)
  if [ ! -f "$compressed_file" ]; then
    echo "🔄 Compressing audio..."
    ffmpeg -i "$audio_file" -ac 1 -ar 16000 -b:a 32k "$compressed_file" -y 2>/dev/null
  fi
  
  # Step 3: Transcribe
  if [ ! -f "$transcript_file" ]; then
    echo "🎙️  Transcribing..."
    curl -s https://api.openai.com/v1/audio/transcriptions \
      -H "Authorization: Bearer $OPENAI_API_KEY" \
      -F "file=@$compressed_file" \
      -F "model=whisper-1" \
      -F "language=en" \
      -F "response_format=text" \
      -o "$transcript_file"
  fi
  
  # Step 4: Translate
  echo "🌏 Translating..."
  local transcript=$(cat "$transcript_file")
  
  cat "$transcript_file" | jq -Rs "{
    \"model\": \"gpt-4o\",
    \"messages\": [{\"role\": \"user\", \"content\": (\"You are translating a Tim Keller sermon.\\n\\nTitle: $title\\nDate: $date\\n\\nHere is the full English transcript:\\n\" + . + \"\\n\\nPlease provide:\\n1. Chinese translation of the title\\n2. Scripture references mentioned (if any)\\n3. A sermon outline with 5-7 main points (in both English and Chinese)\\n4. Full Chinese translation of the transcript\\n\\nRespond in JSON format:\\n{\\n    \\\"title_cn\\\": \\\"中文标题\\\",\\n    \\\"scripture_refs\\\": [\\\"经文引用\\\"],\\n    \\\"outline\\\": [\\n        {\\\"en\\\": \\\"Point in English\\\", \\\"cn\\\": \\\"要点中文\\\"}\\n    ],\\n    \\\"transcript_cn\\\": \\\"完整中文翻译...\\\"\\n}\")}],
    \"temperature\": 0.3,
    \"response_format\": {\"type\": \"json_object\"}
  }" > /tmp/gpt_request.json
  
  curl -s https://api.openai.com/v1/chat/completions \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $OPENAI_API_KEY" \
    -d @/tmp/gpt_request.json > "${safe_title}_response.json"
  
  jq -r '.choices[0].message.content' "${safe_title}_response.json" > "${safe_title}_analysis.json"
  
  # Step 5: Generate Markdown
  echo "📝 Generating Markdown..."
  
  local title_cn=$(jq -r '.title_cn // ""' "${safe_title}_analysis.json")
  local scripture=$(jq -r '.scripture_refs | if . then join(", ") else "Not specified" end' "${safe_title}_analysis.json")
  local transcript_cn=$(jq -r '.transcript_cn // ""' "${safe_title}_analysis.json")
  
  # Build outline
  local outline=""
  local count=$(jq '.outline | length' "${safe_title}_analysis.json")
  for ((i=0; i<count; i++)); do
    local en=$(jq -r ".outline[$i].en // \"\"" "${safe_title}_analysis.json")
    local cn=$(jq -r ".outline[$i].cn // \"\"" "${safe_title}_analysis.json")
    outline+="$((i+1)). $en
   $cn

"
  done
  
  cat > "$md_file" << MARKDOWN
# $title
# $title_cn

**Date / 日期:** $date

**Scripture References / 经文引用:** $scripture

---

## Sermon Outline / 讲道大纲

$outline

---

## Full Transcript / 完整文本

### English

$(cat "$transcript_file")

---

### 中文翻译

$transcript_cn
MARKDOWN

  echo "✅ Saved: $md_file"
  
  # Cleanup
  rm -f "${safe_title}_response.json" /tmp/gpt_request.json
}

# Process all episodes
for episode in "${EPISODES[@]}"; do
  IFS='|' read -r title date url <<< "$episode"
  process_episode "$title" "$date" "$url"
done

echo ""
echo "========================================"
echo "All episodes processed!"
echo "========================================"
