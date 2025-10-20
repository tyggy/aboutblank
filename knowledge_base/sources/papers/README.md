# Research Papers

Add PDF research papers to this directory for processing.

## Quick Start

1. **Add PDFs to this directory:**
   ```bash
   cp path/to/your/paper.pdf knowledge_base/sources/papers/
   ```

2. **Process papers:**
   ```bash
   make papers-process
   ```

   This will:
   - Extract text from PDFs → `knowledge_base/papers/cleaned/`
   - Copyedit with Claude API → `knowledge_base/papers/edited/`

3. **Extract entities and build knowledge base:**
   ```bash
   make kb-build
   ```

   Entities from papers will be extracted and integrated with transcript entities.

## Supported Format

- **PDF only** (recommended in WHITEPAPER_WORKFLOW.md)
- Text will be extracted using PyMuPDF
- Works best with text-based PDFs (not scanned images)

## File Organization

```
knowledge_base/sources/papers/     # Place PDFs here
knowledge_base/papers/cleaned/     # Extracted text
knowledge_base/papers/edited/      # Copyedited versions
knowledge_base/extractions/        # Entity extractions
```

## Tips

- Use descriptive filenames (e.g., `levin-2023-collective-intelligence.pdf`)
- Papers will be processed alongside transcripts in the knowledge base
- Entity pages will show which papers mention each concept/thinker
- Papers will be linked to entities with [[wiki links]]

## See Also

- `WHITEPAPER_WORKFLOW.md` - Complete paper processing guide
- `make papers-extract` - Extract text only (no copyedit)
- `make papers-copyedit` - Copyedit only (requires extracted text)
