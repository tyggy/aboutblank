# Installation Guide

## Python Version Compatibility

This project supports multiple Python versions with different feature sets:

### Python 3.14 (Latest) - YouTube Transcripts Only

**What works:**
- ✓ YouTube transcript downloading (yt-dlp)
- ✓ VTT/SRT to markdown conversion
- ✓ All core transcript processing features

**What doesn't work yet:**
- ✗ spaCy and NLP analysis (thinc/srsly not compatible yet)
- ✗ Some advanced text processing features

**Installation:**
```bash
pip install yt-dlp
```

That's it! The YouTube transcript pipeline only needs yt-dlp.

### Python 3.11 or Earlier - Full Features

**What works:**
- ✓ Everything in Python 3.14, plus:
- ✓ spaCy for NLP analysis
- ✓ NLTK for text processing
- ✓ Full concept extraction pipeline

**Installation:**
```bash
pip install -r requirements-full.txt
```

## Quick Start

### Option 1: Minimal Install (Recommended for Python 3.14)

```bash
# Install just what you need for YouTube transcripts
pip install yt-dlp

# Test it works
python tools/ytdlp_processor.py --status
```

### Option 2: Full Install (Python 3.11 or earlier)

```bash
# Create virtual environment (recommended)
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install all dependencies
pip install -r requirements-full.txt

# Test it works
python tools/ytdlp_processor.py --status
```

### Option 3: Using pyenv (Recommended for Multiple Python Versions)

```bash
# Install Python 3.11 alongside 3.14
pyenv install 3.11.9
pyenv local 3.11.9

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install full requirements
pip install -r requirements-full.txt
```

## Checking Your Python Version

```bash
python --version
# or
python3 --version
```

## What You Can Do With Each Setup

### Minimal Setup (yt-dlp only)

```bash
# Download YouTube transcripts
make youtube-status
make youtube-download
make youtube-test

# Use the processor directly
python tools/ytdlp_processor.py --verbose

# Convert subtitles manually
python tools/vtt_to_markdown.py subtitle.vtt
```

### Full Setup (Python 3.11 + all packages)

```bash
# Everything above, plus:
python tools/concept_extractor.py
python tools/connection_mapper.py
make analyze
make synthesize
```

## Troubleshooting

### Error: "Failed building wheel for srsly/thinc"

**Cause:** You're using Python 3.14 and trying to install spaCy (which isn't compatible yet)

**Solution:**
1. Use minimal install (just yt-dlp) if you only need transcripts
2. Or switch to Python 3.11 for full features

```bash
# Option 1: Minimal
pip install yt-dlp

# Option 2: Switch Python version
pyenv install 3.11.9
pyenv local 3.11.9
pip install -r requirements-full.txt
```

### Error: "yt-dlp not found"

**Solution:**
```bash
pip install yt-dlp
```

### Error: "SSL Certificate Verify Failed"

**Solution:** Already handled in the code with `--no-check-certificate` flag. If you still have issues:
```bash
# macOS
/Applications/Python\ 3.14/Install\ Certificates.command

# Or bypass (less secure)
export PYTHONHTTPSVERIFY=0
```

### YouTube 403 Forbidden Errors

**Cause:** Network restrictions, rate limiting, or VPN issues

**Solutions:**
1. Wait a few minutes and try again
2. Try a different network
3. Use a VPN
4. Check if YouTube is accessible: `curl -I https://youtube.com`

## Dependency Overview

| Package | Required For | Python 3.14 Compatible? |
|---------|-------------|------------------------|
| yt-dlp | YouTube transcripts | ✓ Yes |
| pandas | Data analysis | ✓ Yes |
| numpy | Data processing | ✓ Yes |
| networkx | Connection mapping | ✓ Yes |
| matplotlib | Visualization | ✓ Yes |
| scikit-learn | ML features | ✓ Yes |
| spacy | NLP analysis | ✗ No (use 3.11) |
| nltk | Text processing | ⚠️  Partial |
| anthropic | Claude API | ⚠️  Check latest |

## Recommended Setup for Different Use Cases

### Just downloading YouTube transcripts
```bash
pip install yt-dlp
```

### Transcripts + basic analysis
```bash
pip install yt-dlp pandas networkx
```

### Full research workflow (concept extraction, NLP)
```bash
# Use Python 3.11
pip install -r requirements-full.txt
```

## Virtual Environment Best Practices

Always use a virtual environment to avoid conflicts:

```bash
# Create
python -m venv venv

# Activate
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Install
pip install yt-dlp
# or
pip install -r requirements-full.txt

# Deactivate when done
deactivate
```

## Getting Help

1. Check your Python version: `python --version`
2. Check what's installed: `pip list`
3. For YouTube transcript issues, see: `YOUTUBE_TRANSCRIPT_USAGE.md`
4. For general issues, see: `README_CLAUDE.md`

## Summary

**TL;DR:**
- **Python 3.14?** → Just use `pip install yt-dlp`
- **Python 3.11?** → Use `pip install -r requirements-full.txt`
- **Want both?** → Use pyenv to manage multiple Python versions

The YouTube transcript pipeline works perfectly on any Python version with just yt-dlp!
