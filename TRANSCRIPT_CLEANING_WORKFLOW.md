# Transcript Cleaning & Copyediting Workflow

Complete workflow for cleaning transcripts with inline timestamps and copyediting them using Claude API.

## Overview

The workflow has two stages:

1. **Clean** - Remove timestamps and basic deduplication
2. **Copyedit** - Use Claude API to fix grammar, remove fillers, improve readability

## Stage 1: Clean Inline Timestamps

### What it does:
- Removes inline timestamps like `<00:00:01.319>`
- Basic deduplication of exact repeated phrases
- Formats into readable paragraphs

### Usage:

```bash
# Clean a single file
python tools/clean_inline_timestamps.py transcript.md

# Output to new file
python tools/clean_inline_timestamps.py transcript.md -o transcript_cleaned.md

# Clean multiple files
python tools/clean_inline_timestamps.py knowledge_base/transcripts/raw/*.md

# In-place editing (overwrite originals)
python tools/clean_inline_timestamps.py transcript.md --in-place
```

### Example:

**Before:**
```
and<00: 00: 01. 319> next<00: 00: 01. 880> we<00: 00: 02. 040> are
```

**After:**
```
and next we are
```

## Stage 2: Copyedit with Claude API

### What it does:
- Fixes grammar and punctuation
- Removes filler words (um, uh, you know, like)
- Removes false starts and repetitions
- Improves sentence structure
- Preserves meaning and speaker's voice

### Setup:

1. **Install anthropic package:**
```bash
pip install anthropic
```

2. **Set API key:**
```bash
export ANTHROPIC_API_KEY=your-api-key-here
```

Get your API key from: https://console.anthropic.com/

### Usage:

```bash
# Copyedit a single file (creates file_edited.md)
python tools/copyedit_with_claude.py transcript_cleaned.md

# Specify output file
python tools/copyedit_with_claude.py transcript_cleaned.md -o transcript_final.md

# In-place editing (overwrite original)
python tools/copyedit_with_claude.py transcript_cleaned.md --in-place

# Copyedit multiple files
python tools/copyedit_with_claude.py knowledge_base/transcripts/raw/*_cleaned.md
```

### Model Options:

```bash
# Default: Haiku (recommended for copyediting - fast & cheap, ~$0.02-0.05 per 20-min transcript)
python tools/copyedit_with_claude.py transcript.md

# Sonnet (available but overkill for copyediting, ~$0.15-0.30 per 20-min transcript)
python tools/copyedit_with_claude.py transcript.md --model claude-sonnet-4-5-20250929
```

**Note:** Haiku 4.5 is perfectly capable for copyediting tasks. Save Sonnet for deep enrichment where higher reasoning is needed.

### Cost Estimates (Haiku):
- **Input:** $1 per million tokens (~4M characters)
- **Output:** $5 per million tokens
- **A 20-minute transcript (~5,000 words):** $0.02-0.05
- **Processing 10 transcripts:** $0.20-0.50

Very affordable for research projects!

## Complete Workflow

### Process a single transcript:

```bash
# 1. Clean timestamps
python tools/clean_inline_timestamps.py raw_transcript.md -o cleaned.md

# 2. Copyedit
python tools/copyedit_with_claude.py cleaned.md -o final.md

# Result: final.md is ready for analysis
```

### Batch process all transcripts:

```bash
#!/bin/bash
# save as: process_all_transcripts.sh

# Set your API key
export ANTHROPIC_API_KEY=your-api-key-here

# Step 1: Clean all raw transcripts
for file in knowledge_base/transcripts/raw/*[^_cleaned].md; do
    echo "Cleaning: $file"
    python tools/clean_inline_timestamps.py "$file"
done

# Step 2: Copyedit all cleaned transcripts
for file in knowledge_base/transcripts/raw/*_cleaned.md; do
    echo "Copyediting: $file"
    python tools/copyedit_with_claude.py "$file"
done

echo "All done! Check knowledge_base/transcripts/raw/ for *_edited.md files"
```

Run it:
```bash
chmod +x process_all_transcripts.sh
./process_all_transcripts.sh
```

## Directory Structure

Recommended organization:

```
knowledge_base/transcripts/
├── raw/                          # Original downloads
│   ├── video1.md                # Original with timestamps
│   └── video2.md
├── cleaned/                      # After timestamp removal
│   ├── video1_cleaned.md
│   └── video2_cleaned.md
└── edited/                       # Final copyedited versions
    ├── video1_final.md
    └── video2_final.md
```

Or, simpler workflow with in-place editing:

```
knowledge_base/transcripts/
├── raw/                          # Keep originals untouched
│   ├── video1_original.md
│   └── video2_original.md
└── processed/                    # Work here
    ├── video1.md                # Copy, then clean, then copyedit in-place
    └── video2.md
```

## Troubleshooting

### Claude API Errors

**"API key not found"**
```bash
# Check if set
echo $ANTHROPIC_API_KEY

# Set it
export ANTHROPIC_API_KEY=your-key-here
```

**"Rate limit exceeded"**
- Wait a few minutes
- Process files one at a time
- Add delays between files in batch script

**"anthropic package not installed"**
```bash
pip install anthropic
```

### Cleaning Issues

**"Cleaned transcript still has repetitions"**
- This is normal - the cleaner only removes exact duplicates
- The Claude copyeditor will handle this in Stage 2

**"Timestamps not removed"**
- Check timestamp format (should be `<00:00:00.000>`)
- If different format, let me know and I'll update the regex

**"Output missing paragraphs"**
- The cleaner formats based on sentence length
- Adjust `min_sentence_length` parameter if needed

## Quality Checking

After copyediting, spot-check a few transcripts:

```bash
# Compare original and edited
diff -u cleaned.md edited.md | less

# View just the edited version
cat video1_edited.md
```

Look for:
- Proper grammar and punctuation
- Filler words removed (um, uh, etc.)
- Preserved meaning and context
- Natural, readable flow

## Integration with Analysis Tools

The final edited transcripts work with your existing tools:

```bash
# Extract concepts from edited transcripts
python tools/concept_extractor.py knowledge_base/transcripts/edited/

# Map connections
python tools/connection_mapper.py knowledge_base/
```

## Tips for Best Results

1. **Always keep originals** - Don't overwrite source files
2. **Batch processing** - Process multiple files to save time
3. **Spot check quality** - Review a few transcripts to ensure quality
4. **Use Haiku first** - Test with cheap model, upgrade to Sonnet if needed
5. **Version control** - Commit after each stage (raw → cleaned → edited)

## Example: Full Process for One Video

```bash
# Assuming you have: video1_with_timestamps.md

# Step 1: Clean timestamps
python tools/clean_inline_timestamps.py \
    video1_with_timestamps.md \
    -o video1_cleaned.md

# Step 2: Copyedit (make sure API key is set)
export ANTHROPIC_API_KEY=your-key-here

python tools/copyedit_with_claude.py \
    video1_cleaned.md \
    -o video1_final.md

# Step 3: Review
cat video1_final.md

# Step 4: Move to final location
mv video1_final.md knowledge_base/transcripts/edited/

# Step 5: Archive original
mv video1_with_timestamps.md knowledge_base/transcripts/raw/archives/
```

## Makefile Integration

Add to your `Makefile`:

```makefile
# Clean transcripts (remove timestamps)
transcripts-clean:
	@echo "Cleaning transcripts..."
	python tools/clean_inline_timestamps.py knowledge_base/transcripts/raw/*.md
	@echo "Done!"

# Copyedit with Claude API
transcripts-copyedit:
	@echo "Copyediting transcripts..."
	@if [ -z "$$ANTHROPIC_API_KEY" ]; then \
		echo "Error: ANTHROPIC_API_KEY not set"; \
		exit 1; \
	fi
	python tools/copyedit_with_claude.py knowledge_base/transcripts/raw/*_cleaned.md
	@echo "Done!"

# Complete workflow
transcripts-process: transcripts-clean transcripts-copyedit
	@echo "All transcripts processed!"
```

Then use:
```bash
make transcripts-process
```

## Summary

| Stage | Tool | What it does | Cost |
|-------|------|-------------|------|
| 1 | `clean_inline_timestamps.py` | Remove timestamps, basic cleanup | Free |
| 2 | `copyedit_with_claude.py` | Grammar, fillers, readability | ~$0.02-0.05/transcript |

**Total cost for 10 transcripts: ~$0.20-0.50** ✓

The cleaned and edited transcripts are ready for your Buddhism & AI knowledge base analysis!
