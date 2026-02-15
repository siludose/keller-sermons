#!/bin/bash
set -e

SERMONS_DIR="/home/node/clawd/keller_sermons"
cd "$SERMONS_DIR"

# 读取前 10 期的 URL 和标题
EPISODES=$(python3 -c "
import json
with open('/tmp/keller_episodes.json') as f:
    eps = json.load(f)[:10]
for i, ep in enumerate(eps):
    safe_title = ''.join(c if c.isalnum() or c in ' -_' else '' for c in ep['title']).replace(' ', '_')
    print(f\"{i}|{safe_title}|{ep['audio_url']}|{ep['date']}\")
")

echo "=== 并发下载 10 个音频文件 ==="
echo "$EPISODES" | while IFS='|' read idx title url date; do
    if [ ! -f "${title}.mp3" ]; then
        echo "下载: $title"
        curl -sL "$url" -o "${title}.mp3" &
    else
        echo "已存在: $title"
    fi
done

# 等待所有下载完成
wait
echo "✅ 所有下载完成"
ls -lh *.mp3 | head -15

echo ""
echo "=== 并发转录 (最多 5 个同时) ==="
# 使用 GNU parallel 或简单的后台任务控制
transcribe() {
    local title="$1"
    local mp3="${title}.mp3"
    local txt="${title}_transcript.txt"
    
    if [ -f "$txt" ] && [ -s "$txt" ]; then
        echo "已转录: $title"
        return 0
    fi
    
    echo "转录中: $title"
    curl -s https://api.openai.com/v1/audio/transcriptions \
        -H "Authorization: Bearer $OPENAI_API_KEY" \
        -F "file=@$mp3" \
        -F "model=whisper-1" \
        -F "language=en" \
        -o "${title}_response.json"
    
    # 提取文本
    python3 -c "import json; print(json.load(open('${title}_response.json'))['text'])" > "$txt" 2>/dev/null || echo "转录失败: $title"
}

export -f transcribe
export OPENAI_API_KEY

# 并发转录（5个同时）
echo "$EPISODES" | while IFS='|' read idx title url date; do
    echo "$title"
done | xargs -P 5 -I {} bash -c 'transcribe "$@"' _ {}

echo "✅ 所有转录完成"
ls -lh *_transcript.txt 2>/dev/null | head -15
