# 快速开始指南

## ⚡ 30 秒快速开始

```bash
# 1. 安装依赖（仅需一次）
pip3 install -r scripts/requirements.txt

# 2. 确保 Ollama 运行
brew services start ollama

# 3. 翻译！
cd /Volumes/Macintosh\ Extra/Code/keller-sermons
python3 scripts/translate_sermons.py --batch
```

## 📚 常用命令

| 命令 | 说明 |
|------|------|
| `python3 scripts/translate_sermons.py --file Sermon_Name` | 翻译单个讲道 |
| `python3 scripts/translate_sermons.py --batch` | 翻译所有讲道 |
| `python3 scripts/translate_sermons.py --file Sermon_Name --backend ollama` | 强制使用 Ollama |
| `python3 scripts/translate_sermons.py --file Sermon_Name --backend claude` | 强制使用 Claude |
| `python3 scripts/translate_sermons.py --help` | 显示帮助 |

## 🎯 预期结果

```
Translation backend: ollama
  Translating Sermon_Name... DONE
Translated Sermon_Name
```

## ✅ 验证安装

```bash
# 检查 Ollama
ollama list | grep qwen2.5

# 检查 Python 依赖
python3 -c "import anthropic, openai, requests; print('✓ All OK')"

# 检查脚本
python3 -m py_compile scripts/translate_sermons.py && echo "✓ Syntax OK"
```

## 🚨 常见问题

### "Connection refused" 错误
```bash
brew services start ollama
```

### "Model not found" 错误
```bash
ollama pull qwen2.5:7b-instruct-q8_0
```

### 翻译很慢
- 检查系统资源使用：`top` 或 Activity Monitor
- 如果 CPU 使用率低，可能在使用 CPU 而非 GPU
- 考虑使用 `--backend claude` 作为快速备选

## 📖 完整文档

- **OLLAMA_INTEGRATION_GUIDE.md** - 详细指南
- **FORMATTING_PRESERVATION.md** - 格式保留说明
- **IMPLEMENTATION_SUMMARY.md** - 实施总结

## 💡 最佳实践

1. 首次运行前确保 Ollama 已启动
2. 对关键讲道使用 `--backend claude` 获得最优质量
3. 定期检查翻译质量，不满意的段落可手动调整
4. 保持 git 仓库更新，便于版本控制

---

**更多问题？** 查看 OLLAMA_INTEGRATION_GUIDE.md 的"常见问题"章节。
