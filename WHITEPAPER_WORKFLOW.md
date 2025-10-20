# Whitepaper & Research Paper Workflow

## Recommended Format: PDF

**Use PDF as your primary format** for these reasons:

1. **Most universal** - All papers have PDFs
2. **Best extraction tools** - PyMuPDF, pdfplumber work great
3. **Preserve structure** - Can extract text, headings, citations
4. **No duplication** - One authoritative version

## Why Not XML or ePub?

- **XML**: Usually generated from LaTeX/source, not always available, structure varies
- **ePub**: Good for books, but rare for academic papers, harder to process
- **PDF**: Universal standard, always available

## Setup

### 1. Install Dependencies

```bash
# Add to requirements.txt
pip install pymupdf  # Also known as fitz - best for academic PDFs
pip install anthropic  # For Claude API (already installed)
```

### 2. Folder Structure

```
knowledge_base/
├── sources/
│   ├── papers/                    ← Put PDF files here
│   │   ├── author-year-title.pdf
│   │   └── ...
│   ├── papers_extracted/          ← Extracted markdown
│   │   ├── author-year-title.md
│   │   └── ...
│   └── youtube_talks.md
```

## Workflow

### Step 1: Add PDFs

Put research papers in `knowledge_base/sources/papers/`:

```bash
cd knowledge_base/sources/papers/

# Good naming convention:
# author-year-short-title.pdf

# Examples:
# levin-2024-intelligence-embodied-systems.pdf
# friston-2010-free-energy-principle.pdf
# doctor-2024-bodhisattva-ai-model.pdf
```

### Step 2: Extract Text

```bash
# Extract all papers to markdown
make papers-extract

# Or manually:
python tools/extract_papers.py knowledge_base/sources/papers/*.pdf --verbose
```

### Step 3: Process Like Transcripts

Papers go through the same pipeline as transcripts:

```bash
# Fix entity names
make kb-fix-speakers  # Works on papers too!

# Extract entities from papers
python tools/extract_entities.py knowledge_base/sources/papers_extracted/*.md

# Continue with normal flow
make kb-normalize
make kb-populate
make kb-enrich
```

## Tool: extract_papers.py

Creates markdown from PDFs with:

- **Metadata**: Author, year, title, abstract, keywords
- **Full text**: Extracted and cleaned
- **Citations**: Preserved
- **Structure**: Headings maintained

**Output format:**

```markdown
---
type: paper
title: "Intelligence in Embodied Systems"
authors: [Michael Levin, ...]
year: 2024
journal: Nature
doi: 10.1234/...
tags: [intelligence, embodiment, cognition]
---

# Intelligence in Embodied Systems

## Abstract

[Abstract text...]

## Introduction

[Paper content...]

## References

[Citations...]
```

## Deduplication Strategy

**Q: What if I have the same paper in PDF, XML, and ePub?**

**A: Keep only PDF:**

1. PDFs are the standard
2. Extraction quality is best
3. One source = no duplication
4. If you need XML/ePub later, convert from PDF

**Convert if needed:**
```bash
# PDF → ePub (if you want to read on e-reader)
ebook-convert paper.pdf paper.epub

# Don't keep multiple formats in knowledge base
# Keep source PDFs, delete converted versions after reading
```

## Advanced: Citation Graph

Papers can link to each other via citations:

```markdown
## Related Work

This builds on [[Friston 2010 - Free Energy Principle]] and
[[Levin 2019 - Collective Intelligence]].

## References

- [[Friston, K. (2010)]] - Free Energy Principle
- [[Levin, M. (2019)]] - Intelligence in Development
```

The entity extraction will find these references and create links!

## Integration with Existing KB

Papers integrate seamlessly:

```
Thinker: Michael Levin
├── Frameworks:
│   ├── Cognitive Light Cone
│   └── Morphogenetic Fields
├── Concepts:
│   ├── Embodied Cognition
│   └── Bioelectricity
└── Sources:
    ├── Papers:
    │   ├── Levin 2024 - Intelligence in Embodied Systems  ← New!
    │   └── Levin 2019 - Collective Intelligence         ← New!
    └── Talks:
        ├── Selves, Wants, and Innumerable Beings
        └── Creating Intelligence Across Scales
```

## Cost Estimate

Like transcripts, papers use Claude API for entity extraction:

- **Average paper**: 5,000-10,000 words
- **Cost**: ~$0.02-0.05 per paper (Haiku 4.5)
- **10 papers**: ~$0.20-0.50

Very affordable!

## Next Steps

1. **Create tools/extract_papers.py** - PDF → Markdown converter
2. **Update Makefile** - Add `make papers-extract`
3. **Test with one paper** - Validate extraction quality
4. **Process papers** - Run through entity extraction pipeline
5. **Cross-link** - Papers, transcripts, and entities all connected

Want me to create the PDF extraction tool?
