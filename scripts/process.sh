#!/bin/bash
# Process Tim Keller sermons

SERMONS_DIR="/home/node/clawd/keller_sermons"
cd "$SERMONS_DIR"

process_episode() {
    local title="$1"
    local date="$2"
    local url="$3"
    local safe_title=$(echo "$title" | tr ' ' '_' | tr -cd '[:alnum:]_-')
    
    local audio_file="${safe_title}.mp3"
    local md_file="${safe_title}.md"
    local transcript_file="${safe_title}_transcript.txt"
    local analysis_file="${safe_title}_analysis.json"
    
    # Skip if already done
    if [ -f "$md_file" ]; then
        echo "✅ Already processed: $title"
        return 0
    fi
    
    echo "📥 Downloading: $title"
    if [ ! -f "$audio_file" ]; then
        curl -sL "$url" -o "$audio_file"
    fi
    
    echo "🎙️ Transcribing: $title"
    if [ ! -f "$transcript_file" ]; then
        curl -s https://api.openai.com/v1/audio/transcriptions \
            -H "Authorization: Bearer $OPENAI_API_KEY" \
            -F "file=@$audio_file" \
            -F "model=whisper-1" \
            -F "language=en" \
            -F "response_format=text" \
            -o "$transcript_file"
    fi
    
    local transcript=$(cat "$transcript_file")
    
    echo "🌏 Translating: $title"
    
    # Create the prompt
    local prompt="You are translating a Tim Keller sermon.

Title: $title
Date: $date

Here is the full English transcript:
$transcript

Please provide:
1. Chinese translation of the title
2. Scripture references mentioned (if any)
3. A sermon outline with main points (in both English and Chinese)
4. Full Chinese translation of the transcript

Respond in JSON format:
{
    \"title_cn\": \"中文标题\",
    \"scripture_refs\": [\"经文引用\"],
    \"outline\": [
        {\"en\": \"Point in English\", \"cn\": \"要点中文\"}
    ],
    \"transcript_cn\": \"完整中文翻译...\"
}"

    # Escape for JSON
    local escaped_prompt=$(printf '%s' "$prompt" | jq -Rs .)
    
    curl -s https://api.openai.com/v1/chat/completions \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $OPENAI_API_KEY" \
        -d "{
            \"model\": \"gpt-4o\",
            \"messages\": [{\"role\": \"user\", \"content\": $escaped_prompt}],
            \"temperature\": 0.3,
            \"response_format\": {\"type\": \"json_object\"}
        }" > "${safe_title}_response.json"
    
    # Extract the content
    jq -r '.choices[0].message.content' "${safe_title}_response.json" > "$analysis_file"
    
    # Generate markdown
    generate_markdown "$title" "$date" "$safe_title"
    
    echo "✅ Saved: $md_file"
    
    # Cleanup temp files
    rm -f "${safe_title}_response.json"
}

generate_markdown() {
    local title="$1"
    local date="$2"
    local safe_title="$3"
    
    local transcript_file="${safe_title}_transcript.txt"
    local analysis_file="${safe_title}_analysis.json"
    local md_file="${safe_title}.md"
    
    local title_cn=$(jq -r '.title_cn // ""' "$analysis_file")
    local scripture=$(jq -r '.scripture_refs | if . then join(", ") else "Not specified" end' "$analysis_file")
    local transcript_en=$(cat "$transcript_file")
    local transcript_cn=$(jq -r '.transcript_cn // ""' "$analysis_file")
    
    # Build outline
    local outline=""
    local count=$(jq '.outline | length' "$analysis_file")
    for ((i=0; i<count; i++)); do
        local en=$(jq -r ".outline[$i].en // \"\"" "$analysis_file")
        local cn=$(jq -r ".outline[$i].cn // \"\"" "$analysis_file")
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

$transcript_en

---

### 中文翻译

$transcript_cn
MARKDOWN
}

# Main
echo "Processing Tim Keller Sermons..."
echo "================================"
