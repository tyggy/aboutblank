# Knowledge Extraction & Obsidian Knowledge Base Guide

## Overview

This system automatically extracts entities (thinkers, concepts, frameworks, institutions, questions) from transcripts and builds a rich, interconnected Obsidian knowledge base with bidirectional wiki links.

## Prerequisites

1. **Cleaned and copyedited transcripts** in `knowledge_base/transcripts/raw/`
2. **Anthropic API key** set as environment variable:
   ```bash
   export ANTHROPIC_API_KEY=your-key-here
   ```
3. **Obsidian** installed (for viewing the knowledge graph)

## Quick Start

### Complete Pipeline

Run the entire pipeline with a single command:

```bash
make kb-build
```

This will:
1. Extract entities from transcripts using Claude API
2. Normalize and deduplicate entity names
3. Create entity pages in the knowledge base
4. Inject wiki links into transcripts

### Step-by-Step Process

For more control, run each step individually:

```bash
# Step 1: Extract entities from transcripts
make kb-extract

# Step 2: Normalize and deduplicate entities
make kb-normalize

# Step 3: Create entity pages
make kb-populate

# Step 4: Inject wiki links into transcripts
make kb-link
```

## Detailed Workflow

### 1. Entity Extraction (`make kb-extract`)

**What it does:**
- Reads copyedited transcripts (`*_edited.md`)
- Uses Claude Haiku 4.5 to identify and categorize entities
- Extracts:
  - **Thinkers**: People mentioned (with context)
  - **Concepts**: Important ideas and theories
  - **Frameworks**: Named models or methodologies
  - **Institutions**: Organizations, centers, projects
  - **Questions**: Research questions and open problems
- Saves JSON files to `knowledge_base/extractions/`

**Manual alternative:**
```bash
python tools/extract_entities.py \
  knowledge_base/transcripts/raw/*_edited.md \
  --verbose
```

**Output:**
- `knowledge_base/extractions/{transcript}_entities.json` for each transcript

**Cost:**
- Approximately $0.03-0.08 per transcript (depending on length)
- Uses Claude Haiku 4.5 for cost-effectiveness

**Tips:**
- Review extraction files before proceeding
- Claude will be selective - only clearly significant entities are extracted
- Extractions are deterministic - you can re-run safely

### 2. Name Normalization (`make kb-normalize`)

**What it does:**
- Loads all extraction files
- Loads existing entities from knowledge base
- Performs fuzzy matching to deduplicate entities
- Matches against existing database with 85% similarity threshold
- Normalizes naming conventions:
  - Thinkers: "firstname-lastname" format
  - Concepts: Title Case with hyphens
  - Handles aliases and variations
- Merges duplicate extractions
- Creates `knowledge_base/normalized_entities.json`

**Manual alternative:**
```bash
python tools/normalize_entities.py \
  knowledge_base/extractions/*_entities.json \
  --verbose \
  --similarity-threshold 0.85
```

**Output:**
- `knowledge_base/normalized_entities.json` - single unified entity database

**Example matching:**
- "Michael Levin" ≈ "M. Levin" → merged
- "cognitive light cone" ≈ "Cognitive Light Cone" → normalized
- "Free Energy Principle" vs existing "free-energy-principle.md" → matched

**Tips:**
- Review `normalized_entities.json` before populating
- Adjust `--similarity-threshold` if you get too many/few matches
- Entities marked `is_new: true` will be created
- Entities without that flag matched existing entries

### 3. Entity Page Population (`make kb-populate`)

**What it does:**
- Reads `normalized_entities.json`
- Creates markdown files for new entities using templates
- Places them in appropriate directories:
  - `knowledge_base/thinkers/` - People
  - `knowledge_base/concepts/{category}/` - Categorized concepts
  - `knowledge_base/frameworks/` - Models and methodologies
  - `knowledge_base/institutions/` - Organizations
  - `knowledge_base/questions/` - Research questions
- Skips entities that already exist
- Uses YAML frontmatter for metadata

**Manual alternative:**
```bash
python tools/populate_entities.py \
  knowledge_base/normalized_entities.json \
  --verbose \
  --dry-run  # Test first
```

**Output:**
- Markdown files for each new entity
- Organized folder structure
- Templates with placeholders for manual refinement

**Entity page features:**
- YAML frontmatter with metadata
- Aliases for search and linking
- Structured sections (overview, related entities, sources, etc.)
- Ready for manual expansion

**Tips:**
- Use `--dry-run` first to preview what will be created
- Pages start as stubs - expand them manually over time
- Existing entities are never overwritten
- Add custom sections as needed

### 4. Wiki Link Injection (`make kb-link`)

**What it does:**
- Scans transcript text for entity mentions
- Adds `[[Entity Name]]` wiki-link syntax
- Handles:
  - Multi-word entities (longest matches first)
  - Aliases and name variations
  - Possessives ("Levin's" → "[[Michael Levin]]'s")
  - Word boundaries (won't link partial words)
- Avoids:
  - Double-linking already linked text
  - Linking in headings, code blocks, frontmatter
  - Creating overlapping links
- Updates transcripts in-place

**Manual alternative:**
```bash
python tools/inject_links.py \
  knowledge_base/transcripts/raw/*_edited.md \
  --verbose \
  --dry-run  # Test first
```

**Output:**
- Transcripts with embedded wiki links
- Bidirectional navigation in Obsidian

**Tips:**
- Always use `--dry-run` first to preview changes
- Run multiple times is safe (won't double-link)
- Links respect existing formatting
- Manual links you add will be preserved

## Knowledge Base Structure

```
knowledge_base/
├── thinkers/              # People
│   ├── _templates/        # Template files
│   ├── michael-levin.md
│   └── karl-friston.md
│
├── concepts/              # Ideas and theories
│   ├── _templates/
│   ├── buddhist/          # Buddhist concepts
│   ├── cognitive/         # Cognitive science
│   ├── ai/                # AI/ML concepts
│   └── interdisciplinary/ # Bridge concepts
│
├── frameworks/            # Models and methodologies
│   ├── _templates/
│   ├── sci-loop.md
│   └── free-energy-principle.md
│
├── institutions/          # Organizations
│   ├── _templates/
│   └── center-for-apparent-selves.md
│
├── questions/             # Research questions
│   ├── _templates/
│   └── what-is-the-nature-of-agency.md
│
├── transcripts/           # Video transcripts
│   ├── raw/               # Processed transcripts
│   │   ├── *_cleaned.md
│   │   └── *_edited.md   # With wiki links
│   └── edited/            # (optional separate location)
│
├── extractions/           # Intermediate files
│   └── *_entities.json
│
└── normalized_entities.json  # Unified entity database
```

## Using with Obsidian

### Opening the Knowledge Base

1. Open Obsidian
2. "Open folder as vault" → select `knowledge_base/`
3. Trust the vault if prompted

### Exploring the Knowledge Graph

1. Open any transcript or entity page
2. Press `Cmd/Ctrl + G` to view graph
3. Click nodes to navigate
4. Hover to see connections

### Navigation Tips

- **Backlinks**: See all pages linking to current page
- **Forward links**: All pages linked from current page
- **Graph view**: Visual network of all connections
- **Search**: Finds both content and link text
- **Tags**: Use frontmatter tags for filtering

### Recommended Obsidian Plugins

- **Graph Analysis**: Enhanced graph visualization
- **Dataview**: Query and display entity metadata
- **Tag Wrangler**: Manage tags across pages
- **Templater**: Enhanced template functionality
- **Admonitions**: Callout boxes for notes

## Workflow Integration

### Initial Knowledge Base Build

```bash
# 1. Download and process transcripts
make youtube-download
make transcripts-clean
export ANTHROPIC_API_KEY=your-key
make transcripts-copyedit

# 2. Build knowledge base
make kb-build

# 3. Open in Obsidian
open knowledge_base/  # or drag folder to Obsidian
```

### Adding New Transcripts

```bash
# 1. Add new YouTube URLs to knowledge_base/sources/youtube_talks.md

# 2. Download and process
make youtube-download
make transcripts-clean
make transcripts-copyedit

# 3. Extract and merge into knowledge base
make kb-extract      # Extract from new transcripts
make kb-normalize    # Merge with existing entities
make kb-populate     # Create any new entity pages
make kb-link         # Add links to new transcripts
```

The system will:
- Match entities against existing database
- Only create new pages for truly new entities
- Update links across all transcripts

### Iterative Refinement

After the initial build:

1. **Review entity pages** - Expand stubs, add details
2. **Merge duplicates** - If fuzzy matching missed some
3. **Add manual links** - For subtle connections
4. **Create synthesis notes** - In `syntheses/` folder
5. **Re-run extraction** - If you refine transcript copyediting

## Cost Estimates

### Entity Extraction
- **Per transcript**: $0.03-0.08
- **20-minute video**: ~$0.04
- **90-minute video**: ~$0.15
- **Model**: Claude Haiku 4.5 (very affordable)

### Total Pipeline (10 transcripts)
- **Transcript copyediting**: $0.20-0.50
- **Entity extraction**: $0.30-0.80
- **Total**: ~$0.50-1.30

Very reasonable for the value provided!

## Troubleshooting

### "No extractions found"
- Run `make kb-extract` first
- Check `knowledge_base/extractions/` has JSON files

### "normalized_entities.json not found"
- Run `make kb-normalize` after extraction
- Check the file exists in `knowledge_base/`

### "ANTHROPIC_API_KEY not set"
```bash
export ANTHROPIC_API_KEY=your-key-here
# Or add to ~/.bashrc or ~/.zshrc
```

### JSON parsing errors during extraction

If you see errors like "Expecting value: line 1 column 1 (char 0)" in extraction results:

**Symptoms:**
```json
{
  "thinkers": [],
  "concepts": [],
  "_metadata": {
    "error": "Expecting value: line 1 column 1 (char 0)"
  }
}
```

**What this means:**
Claude's API returned an empty or malformed response for that transcript.

**Solution:**

1. **Check debug files** (created automatically with improved script):
   ```bash
   ls knowledge_base/extractions/*_debug_response.txt
   ```
   These show exactly what Claude returned.

2. **Retry failed extractions**:
   ```bash
   python tools/retry_failed_extractions.py --verbose
   ```
   This will automatically re-run extraction for any files that failed.

3. **Manual retry for specific file**:
   ```bash
   python tools/extract_entities.py \
     knowledge_base/transcripts/raw/problem-file_edited.md \
     --verbose
   ```

**Common causes:**
- Transcript too long (>100k characters triggers truncation)
- Very dense content overwhelming the model
- Temporary API issue (retry usually works)
- Transcript format issue (malformed markdown)

**If retries keep failing:**
- Check the transcript file - is it properly formatted?
- Try with a smaller section of the transcript
- The transcript might be edge case - can extract manually

### Too many duplicate entities created
- Lower similarity threshold:
  ```bash
  python tools/normalize_entities.py ... --similarity-threshold 0.80
  ```
- Manually merge in Obsidian, then re-run

### Missing links in transcripts
- Entity might not be in normalized database
- Check case sensitivity in `normalized_entities.json`
- Add manual alias if needed

### Links in wrong places
- Review with `--dry-run` first
- Adjust entity names in `normalized_entities.json`
- Re-run link injection (it's idempotent)

## Advanced Usage

### Custom Entity Categories

Add new concept categories:

```bash
mkdir -p knowledge_base/concepts/neuroscience
```

Update `tools/normalize_entities.py` to recognize the category.

### Manual Entity Addition

Create a file directly:

```bash
# Copy template
cp knowledge_base/concepts/_templates/concept-template.md \
   knowledge_base/concepts/cognitive/new-concept.md

# Edit the file
# Add to normalized_entities.json for linking
```

### Batch Operations

Extract from specific transcripts:

```bash
python tools/extract_entities.py \
  knowledge_base/transcripts/raw/xaUknipwnpw*.md \
  knowledge_base/transcripts/raw/staFQw-_e6E*.md \
  --verbose
```

### Integration with Other Tools

Export to JSON for external processing:

```bash
# Entity database is already JSON
cat knowledge_base/normalized_entities.json | jq '.thinkers'

# Export graph structure
# (Could be extended with a custom script)
```

## Best Practices

### 1. Review Before Committing
- Always check extractions before normalization
- Use `--dry-run` flags to preview changes
- Review `normalized_entities.json` before population

### 2. Iterative Refinement
- Build knowledge base incrementally
- Manually expand key entity pages
- Add connections you notice

### 3. Consistent Naming
- Follow the established conventions
- Use full names for thinkers
- Keep concept names clear and concise

### 4. Use Templates
- Start with templates for new entities
- Maintain consistent structure
- Customize as needed

### 5. Regular Updates
- Re-run extraction when adding new transcripts
- Normalization will merge with existing database
- Links are safe to regenerate

## Next Steps

After building your knowledge base:

1. **Explore in Obsidian** - Navigate the graph, discover connections
2. **Expand entity pages** - Add details, quotes, examples
3. **Create synthesis notes** - In `syntheses/` folder
4. **Add manual connections** - Link related concepts you notice
5. **Build custom views** - Use Dataview plugin for queries
6. **Share insights** - Export notes or graph visualizations

## Reference

### Key Files

- `KNOWLEDGE_STRUCTURE.md` - Detailed structure documentation
- `tools/extract_entities.py` - Entity extraction script
- `tools/normalize_entities.py` - Name normalization script
- `tools/populate_entities.py` - Entity page creation script
- `tools/inject_links.py` - Wiki link injection script

### Make Commands

- `make kb-extract` - Extract entities
- `make kb-normalize` - Normalize names
- `make kb-populate` - Create pages
- `make kb-link` - Inject links
- `make kb-build` - Full pipeline

### Useful Obsidian Shortcuts

- `Cmd/Ctrl + G` - Open graph view
- `Cmd/Ctrl + O` - Quick switcher
- `Cmd/Ctrl + E` - Toggle edit/preview
- `Cmd/Ctrl + [` - Navigate back
- `Cmd/Ctrl + F` - Search in file
- `Cmd/Ctrl + Shift + F` - Search in all files

## Support

For issues or questions:
- Check `KNOWLEDGE_STRUCTURE.md` for structural details
- Review `README_CLAUDE.md` for overall workflow
- Examine example entity pages in `knowledge_base/`

## Summary

This system provides:
- ✅ **Automated extraction** of entities from transcripts
- ✅ **Intelligent deduplication** with fuzzy matching
- ✅ **Structured organization** in Obsidian-compatible format
- ✅ **Bidirectional linking** for rich navigation
- ✅ **Incremental growth** - easily add new transcripts
- ✅ **Cost-effective** - uses Claude Haiku 4.5
- ✅ **Manual refinement** - balance automation with curation

Build your knowledge base once, explore connections forever!
