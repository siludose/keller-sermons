#!/bin/bash
# Translate sermon using OpenAI API via curl

INPUT_FILE="$1"
OUTPUT_FILE="$2"
TITLE="$3"
CHINESE_TITLE="$4"
DATE="$5"

if [ -z "$INPUT_FILE" ] || [ -z "$OUTPUT_FILE" ]; then
    echo "Usage: $0 <input_file> <output_file> <title> <chinese_title> <date>"
    exit 1
fi

echo "Processing: $TITLE"

# Read transcript
TRANSCRIPT=$(cat "$INPUT_FILE")

# Create temp files for API calls
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

# Function to call OpenAI API
call_openai() {
    local system_prompt="$1"
    local user_prompt="$2"
    local response_format="${3:-text}"
    
    local json_payload
    if [ "$response_format" = "json" ]; then
        json_payload=$(jq -n \
            --arg model "gpt-4o" \
            --arg system "$system_prompt" \
            --arg user "$user_prompt" \
            '{
                model: $model,
                messages: [
                    {role: "system", content: $system},
                    {role: "user", content: $user}
                ],
                response_format: {type: "json_object"}
            }')
    else
        json_payload=$(jq -n \
            --arg model "gpt-4o" \
            --arg system "$system_prompt" \
            --arg user "$user_prompt" \
            '{
                model: $model,
                messages: [
                    {role: "system", content: $system},
                    {role: "user", content: $user}
                ]
            }')
    fi
    
    curl -s https://api.openai.com/v1/chat/completions \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $OPENAI_API_KEY" \
        -d "$json_payload" | jq -r '.choices[0].message.content'
}

echo "  Extracting outline and scriptures..."

# Extract first 15000 chars for analysis
ANALYSIS_TEXT="${TRANSCRIPT:0:15000}"

ANALYSIS=$(call_openai \
    "You are an expert in analyzing Christian sermons. Extract:
1. A sermon outline with 6-8 main points (in English)
2. All scripture references mentioned in the sermon

Return JSON format:
{
  \"outline\": [\"Point 1\", \"Point 2\", ...],
  \"scriptures\": [\"Book Chapter:Verse\", ...]
}" \
    "Analyze this Tim Keller sermon transcript:

$ANALYSIS_TEXT" \
    "json")

echo "  Analysis result received"

# Parse outline and scriptures
OUTLINE=$(echo "$ANALYSIS" | jq -r '.outline[]' 2>/dev/null || echo "")
SCRIPTURES=$(echo "$ANALYSIS" | jq -r '.scriptures | join(", ")' 2>/dev/null || echo "")

echo "  Translating outline..."

OUTLINE_CN=$(call_openai \
    "Translate the following sermon outline points to Chinese. Return JSON with format: {\"translations\": [\"翻译1\", \"翻译2\", ...]}" \
    "$(echo "$ANALYSIS" | jq -r '.outline | tojson')" \
    "json")

echo "  Translating full transcript..."

# Split transcript into chunks and translate
CHUNK_SIZE=7000
TRANSCRIPT_LENGTH=${#TRANSCRIPT}
CHUNK_NUM=0
TOTAL_CHUNKS=$(( (TRANSCRIPT_LENGTH + CHUNK_SIZE - 1) / CHUNK_SIZE ))

TRANSLATED=""
for ((i=0; i<TRANSCRIPT_LENGTH; i+=CHUNK_SIZE)); do
    CHUNK_NUM=$((CHUNK_NUM + 1))
    CHUNK="${TRANSCRIPT:$i:$CHUNK_SIZE}"
    echo "    Translating chunk $CHUNK_NUM/$TOTAL_CHUNKS..."
    
    CHUNK_TRANSLATION=$(call_openai \
        "You are translating a Tim Keller sermon transcript to Chinese.
- Maintain the spiritual and theological depth
- Use appropriate Christian terminology in Chinese
- Keep the conversational tone of the sermon
- Translate naturally, not word-for-word" \
        "Translate this sermon transcript section ($CHUNK_NUM/$TOTAL_CHUNKS) to Chinese:

$CHUNK")
    
    TRANSLATED="$TRANSLATED

$CHUNK_TRANSLATION"
done

echo "  Generating markdown..."

# Build markdown output
cat > "$OUTPUT_FILE" << MARKDOWN_END
# $TITLE
# $CHINESE_TITLE

**Date / 日期:** $DATE

**Scripture References / 经文引用:** $SCRIPTURES

---

## Sermon Outline / 讲道大纲

MARKDOWN_END

# Add outline points
OUTLINE_ARRAY=$(echo "$ANALYSIS" | jq -r '.outline')
OUTLINE_CN_ARRAY=$(echo "$OUTLINE_CN" | jq -r '.translations // .outline // []')

COUNT=$(echo "$OUTLINE_ARRAY" | jq -r 'length')
for ((i=0; i<COUNT; i++)); do
    EN=$(echo "$OUTLINE_ARRAY" | jq -r ".[$i]")
    CN=$(echo "$OUTLINE_CN_ARRAY" | jq -r ".[$i]" 2>/dev/null || echo "")
    echo "$((i+1)). $EN" >> "$OUTPUT_FILE"
    echo "   $CN" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
done

cat >> "$OUTPUT_FILE" << MARKDOWN_END
---

## Full Transcript / 完整文本

### English

$TRANSCRIPT

---

### 中文翻译

$TRANSLATED
MARKDOWN_END

FILE_SIZE=$(stat -f%z "$OUTPUT_FILE" 2>/dev/null || stat -c%s "$OUTPUT_FILE")
echo "  Done! Output: $OUTPUT_FILE ($(echo "scale=1; $FILE_SIZE/1024" | bc)KB)"
