# 智能美化指南

## 概述

智能美化功能使用 LLM（大语言模型）为讲道内容添加结构化小标题、优化段落分隔和内容聚合。

## 功能特点

### 1. 添加小标题
自动识别讲道的主要部分并添加描述性小标题：
- 引言
- 要点一、要点二、要点三等
- 应用
- 结论

示例：
```markdown
### 引言：人类的终极问题

当我们思考人生意义时...

### 要点一：我们知道该做什么，却无力做到

圣经告诉我们...
```

### 2. 语义分段
根据内容主题转换进行智能分段，而不是机械地按句数分段：
- 识别主题变化点
- 将相关句子聚合成段落
- 保持段落长度适中（3-5 句）

### 3. 段落聚合
将讨论同一主题的句子组合成连贯的段落：
- 引用和解释放在一起
- 相关观点聚合
- 过渡自然流畅

## 使用方法

### 方式 1：迁移时使用智能美化

```bash
# 单个讲道迁移（使用智能美化）
python3 scripts/migrate_to_new_structure.py --file A_New_Heart --smart-beautify

# 批量迁移所有讲道（使用智能美化）
python3 scripts/migrate_to_new_structure.py --batch --smart-beautify

# 预览模式（查看但不执行）
python3 scripts/migrate_to_new_structure.py --dry-run --batch --smart-beautify
```

### 方式 2：单独美化已迁移的讲道

```bash
# 美化已迁移讲道的英文和中文
python3 scripts/smart_beautifier.py --file A_New_Heart

# 只美化英文转录
python3 scripts/smart_beautifier.py --file A_New_Heart --transcript-only

# 只美化中文翻译
python3 scripts/smart_beautifier.py --file A_New_Heart --translation-only

# 指定后端（ollama 或 claude）
python3 scripts/smart_beautifier.py --file A_New_Heart --backend ollama
```

## 后端选择

智能美化支持两种后端：

### 1. Ollama（本地，推荐）
- **优点**：免费、快速、隐私
- **要求**：需要运行 Ollama 服务
- **模型**：`qwen2.5:7b-instruct-q8_0`

```bash
# 启动 Ollama
brew services start ollama

# 或手动启动
ollama serve
```

### 2. Claude API
- **优点**：质量高、结果稳定
- **要求**：需要 `ANTHROPIC_API_KEY` 环境变量
- **费用**：按 API 使用计费

```bash
# 设置 API 密钥
export ANTHROPIC_API_KEY="your-key-here"
```

## 对比：基础美化 vs 智能美化

### 基础美化
```markdown
## English Transcript

Welcome to Gospel and Life. When someone you know is
contemplating life's deepest questions, who am I? What's
wrong with the world? What can truly make me whole?

Jesus doesn't just give us answers. He gives us Himself.
In this month's podcast, Tim Keller looks at how we can
share the hope we have in Christ.
```

### 智能美化
```markdown
## English Transcript

### Introduction: Life's Deepest Questions

Welcome to Gospel and Life. When someone you know is
contemplating life's deepest questions—who am I? What's
wrong with the world? What can truly make me whole?—
these are not just philosophical puzzles, but the cries
of the human heart.

### The Gospel Answer

Jesus doesn't just give us answers. He gives us Himself.
In this month's podcast, Tim Keller looks at how we can
share the hope we have in Christ as the answer to a
person's search for meaning and purpose.
```

## 性能考虑

### 处理时间
- **基础美化**：< 1 秒/讲道
- **智能美化**：2-5 分钟/讲道（取决于长度和后端）

### 文本长度处理
智能美化器会自动处理长文本：
- 短文本（< 8000 字符）：一次性处理
- 长文本（> 8000 字符）：分块处理后合并

### 批量处理建议
对于 99 个讲道的批量迁移：
- **基础美化**：约 5 分钟完成所有
- **智能美化**：约 3-6 小时完成所有

**建议策略：**
1. 先用基础美化批量迁移所有讲道
2. 选择重点讲道单独运行智能美化
3. 或在夜间运行智能美化批量处理

## 故障处理

### 问题：LLM 超时或失败
**解决**：自动回退到基础美化

### 问题：内容被截断
**解决**：使用分块处理（`ChunkedSmartBeautifier`）

### 问题：小标题不准确
**解决**：
```bash
# 手动编辑或重新运行
python3 scripts/smart_beautifier.py --file Sermon_Name
```

## 质量检查

美化后建议检查：

1. **小标题质量**
   - 是否准确反映内容
   - 是否有逻辑层次
   - 是否使用 ### 格式

2. **段落分隔**
   - 段落是否过长或过短
   - 主题转换是否清晰
   - 过渡是否自然

3. **内容完整性**
   - 所有原始内容是否保留
   - 没有遗漏或重复

## 示例输出

查看已美化的示例：
```bash
# 查看英文转录
cat sermons/A_New_Heart/transcript.md

# 查看中文翻译
cat sermons/A_New_Heart/translation.md
```

## 配置

智能美化使用与翻译相同的配置文件：
`config/translation.json`

相关设置：
```json
{
  "backends": {
    "ollama": {
      "priority": 1,
      "model": "qwen2.5:7b-instruct-q8_0"
    },
    "claude": {
      "priority": 2
    }
  },
  "translation_settings": {
    "temperature": 0.3,
    "max_output_tokens": 4000
  }
}
```

## 最佳实践

1. **先测试单个讲道**
   ```bash
   python3 scripts/smart_beautifier.py --file Test_Sermon
   ```

2. **检查质量后批量处理**
   如果单个测试满意，再批量处理

3. **保留备份**
   智能美化会覆盖文件，迁移时会自动备份

4. **选择性使用**
   不是所有讲道都需要智能美化，可以：
   - 重点讲道使用智能美化
   - 其他使用基础美化

5. **夜间运行批量任务**
   智能美化批量处理时间较长，适合夜间运行

## 技术细节

### Prompt 设计
智能美化使用精心设计的提示词：
- 明确指示保留所有原始内容
- 只添加格式不修改措辞
- 提供清晰的输出格式要求

### 分块策略
- 按段落边界分块（而非硬性字符数）
- 保持上下文连贯性
- 合并时使用分隔符

### 错误处理
- 自动回退到基础美化
- 详细的错误日志
- 不影响迁移流程

---

**提示**：首次使用建议先在单个讲道上测试，确认效果后再批量处理！
