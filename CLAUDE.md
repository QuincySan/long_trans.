# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Environment

All commands should be run in the `conda test` environment:
```bash
source ~/miniconda3/etc/profile.d/conda.sh && conda activate test
```

## Key Commands

### Installation
```bash
pip install -r requirements.txt
```

### Running the Translation System
```bash
# Batch translation (processes all files in to_translate/)
python main.py

# Single file translation
python main.py -f filename.md

# Quality levels
python main.py --quality basic      # Direct translation
python main.py --quality advanced   # Translation + detailed review + targeted polishing

# Custom chunk sizes
python main.py --large-chunk-size 20000 --small-chunk-size 2000

# Different models
python main.py --model claude-3-5-sonnet-20241022
python main.py --model deepseek-v3
python main.py --model gemini-2.0-pro-exp-02-05
```

### Testing
```bash
# Run individual test files
python -m pytest tests/test_chunker.py
python -m pytest tests/test_translator.py
python -m pytest tests/test_main_cli.py

# Run all tests
python -m pytest tests/
```

## Core Architecture

### Two-Level Chunking Strategy
The system implements a sophisticated chunking approach:
1. **Level 1 (Large chunks)**: Text is split into ~20,000 word segments for summary generation
2. **Level 2 (Small chunks)**: Each large chunk is further divided into ~2,000 word segments for translation
3. **Context preservation**: Generated summaries are passed as context when translating small chunks

### Translation Quality Pipeline
- **Basic**: Direct translation only
- **Advanced**: Translation → qualitative review with specific feedback → targeted polishing

### Key Components Integration
- **chunker.py**: Handles intelligent text segmentation that respects Markdown structure and natural boundaries
- **translator.py**: Orchestrates the entire translation workflow with quality control
- **summarizer.py**: Generates contextual summaries for large chunks (≤500 words)
- **advanced_reviewer.py**: Provides detailed qualitative feedback for advanced quality
- **llm_client.py**: Abstracts multiple LLM providers (supports Claude, DeepSeek, Gemini)

### File Structure Convention
- **Input**: Place files to translate in `to_translate/` folder
- **Output**: Translated files appear in `translated/` folder
- **Logs**: Translation logs and statistics stored in `logs/` folder

## Environment Configuration

Required environment variables (use .env file):
```
FIREWORKS_API_KEY=your_api_key_here
FIREWORKS_API_BASE=https://api.fireworks.ai/inference/v1
```

## Important Implementation Details

### Word Counting Logic
- English text: Standard word counting (including hyphenated words and numbers)
- Chinese text: Each character counts as one word
- Mixed text: Supports combined Chinese/English counting
- Code blocks are excluded from word counts to avoid affecting segmentation

### Markdown Structure Preservation
- Chunking prioritizes natural boundaries (headers, paragraphs, sentences)
- Code blocks remain intact during segmentation
- Original Markdown formatting is preserved in final output

### Context Management
For documents > 20K words, the system:
1. Splits into multiple 20K word sections
2. Generates individual summaries for each section
3. Uses appropriate summary as context when translating chunks from that section