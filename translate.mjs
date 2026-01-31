#!/usr/bin/env node
/**
 * Translate Tim Keller sermon transcripts to Chinese using OpenAI GPT-4o
 */

import fs from 'fs';
import path from 'path';

const OPENAI_API_KEY = process.env.OPENAI_API_KEY;

async function callOpenAI(systemPrompt, userPrompt, jsonMode = false) {
    const body = {
        model: "gpt-4o",
        messages: [
            { role: "system", content: systemPrompt },
            { role: "user", content: userPrompt }
        ]
    };
    
    if (jsonMode) {
        body.response_format = { type: "json_object" };
    }
    
    const response = await fetch('https://api.openai.com/v1/chat/completions', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${OPENAI_API_KEY}`
        },
        body: JSON.stringify(body)
    });
    
    const data = await response.json();
    if (data.error) {
        throw new Error(data.error.message);
    }
    return data.choices[0].message.content;
}

async function extractOutlineAndScriptures(text) {
    const result = await callOpenAI(
        `You are an expert in analyzing Christian sermons. Extract:
1. A sermon outline with 6-8 main points (in English)
2. All scripture references mentioned in the sermon

Return JSON format:
{
  "outline": ["Point 1", "Point 2", ...],
  "scriptures": ["Book Chapter:Verse", ...]
}`,
        `Analyze this Tim Keller sermon transcript:\n\n${text.slice(0, 15000)}`,
        true
    );
    return JSON.parse(result);
}

async function translateOutline(outline) {
    const result = await callOpenAI(
        "Translate the following sermon outline points to Chinese. Return JSON with format: {\"translations\": [\"翻译1\", \"翻译2\", ...]}",
        JSON.stringify(outline),
        true
    );
    const parsed = JSON.parse(result);
    return parsed.translations || parsed.outline || Object.values(parsed)[0] || [];
}

async function translateChunk(text, chunkNum, totalChunks) {
    return await callOpenAI(
        `You are translating a Tim Keller sermon transcript to Chinese.
- Maintain the spiritual and theological depth
- Use appropriate Christian terminology in Chinese  
- Keep the conversational tone of the sermon
- Translate naturally, not word-for-word`,
        `Translate this sermon transcript section (${chunkNum}/${totalChunks}) to Chinese:\n\n${text}`
    );
}

async function processSermon(inputFile, outputFile, title, chineseTitle, date) {
    console.log(`Processing: ${title}`);
    
    // Read transcript
    let transcript = fs.readFileSync(inputFile, 'utf-8');
    
    // Clean transcript - remove podcast intro/outro lines
    transcript = transcript.split('\n')
        .filter(line => !line.toLowerCase().includes('gospelandlife.com/partner'))
        .join('\n');
    
    console.log('  Extracting outline and scriptures...');
    const analysis = await extractOutlineAndScriptures(transcript);
    const outline = analysis.outline || [];
    const scriptures = analysis.scriptures || [];
    
    console.log('  Translating outline...');
    const outlineCn = await translateOutline(outline);
    
    // Split transcript into chunks for translation
    const chunkSize = 7000;
    const chunks = [];
    for (let i = 0; i < transcript.length; i += chunkSize) {
        chunks.push(transcript.slice(i, i + chunkSize));
    }
    
    console.log(`  Translating ${chunks.length} chunks...`);
    const translatedChunks = [];
    for (let i = 0; i < chunks.length; i++) {
        console.log(`    Chunk ${i + 1}/${chunks.length}...`);
        const translated = await translateChunk(chunks[i], i + 1, chunks.length);
        translatedChunks.push(translated);
    }
    
    const chineseTranslation = translatedChunks.join('\n\n');
    
    // Build markdown
    let md = `# ${title}
# ${chineseTitle}

**Date / 日期:** ${date}

**Scripture References / 经文引用:** ${scriptures.join(', ')}

---

## Sermon Outline / 讲道大纲

`;
    
    for (let i = 0; i < outline.length; i++) {
        md += `${i + 1}. ${outline[i]}\n   ${outlineCn[i] || ''}\n\n`;
    }
    
    md += `---

## Full Transcript / 完整文本

### English

${transcript}

---

### 中文翻译

${chineseTranslation}
`;
    
    // Write output
    fs.writeFileSync(outputFile, md);
    
    const fileSize = fs.statSync(outputFile).size;
    console.log(`  Done! Output: ${outputFile} (${(fileSize / 1024).toFixed(1)}KB)`);
    return fileSize;
}

// Main
const [,, inputFile, outputFile, title, chineseTitle, date] = process.argv;

if (!inputFile || !outputFile) {
    console.log('Usage: node translate.mjs <input> <output> <title> <chinese_title> <date>');
    process.exit(1);
}

processSermon(inputFile, outputFile, title, chineseTitle, date)
    .catch(err => {
        console.error('Error:', err.message);
        process.exit(1);
    });
