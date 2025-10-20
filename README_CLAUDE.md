# Buddhism & AI Knowledge Base - Claude Code Guide

## 🚀 Never Forget Commands!

**New here? Start with: [`QUICKSTART.md`](QUICKSTART.md)**

It has all the simple commands you need, including:
- How to activate your Python environment (never forget again!)
- Complete command cheat sheet
- One-liner workflows

### The Simplest Way

```bash
# First time setup (run once):
./setup_env.sh

# Every time after that:
source activate
make kb-build

# Done!
```

---

## Quick Start with Claude Code

1. **Initial Setup**
   ```bash
   # Install dependencies (includes yt-dlp)
   pip install -r requirements.txt

   # Check YouTube transcript status
   make youtube-status

   # Download all YouTube transcripts
   make youtube-download

   # Or test with just one video first
   make youtube-test
   ```

2. **Working with Claude Code**
   ```bash
   # Start Claude Code with project context
   claude-code --context .claude/context/
   
   # Or use the shorthand
   claude-code .
   ```

## YouTube Transcript Pipeline

### New yt-dlp Based System

The project now uses **yt-dlp** for reliable YouTube transcript downloading:

**Features:**
- Automatic detection of already-processed videos (idempotent)
- Downloads both manual and auto-generated subtitles
- Converts VTT/SRT to clean markdown
- Includes video metadata and formatting
- Smart error handling and retry logic
- Processing log tracking

**Commands:**
```bash
# Check what's been processed
make youtube-status

# Download all new transcripts
make youtube-download

# Test with one video
make youtube-test

# Force re-download everything
make youtube-force

# Or use the script directly
python tools/ytdlp_processor.py --help
python tools/ytdlp_processor.py --video xaUknipwnpw --verbose
```

**How it Works:**
1. Reads video URLs from `knowledge_base/sources/youtube_talks.md`
2. Checks `knowledge_base/transcripts/raw/` for existing files
3. Downloads only new videos using yt-dlp
4. Converts subtitles to markdown with metadata
5. Saves as `{video_id}_{title}.md`
6. Updates `processing_log.json`

**Output Format:**
Each transcript includes:
- Video title, URL, channel, published date
- Duration and download timestamp
- Video description and tags
- Clean, paragraph-formatted transcript
- JSON metadata for reference

### Adding New Videos

Simply add YouTube URLs to `knowledge_base/sources/youtube_talks.md`:
```
https://www.youtube.com/watch?v=xaUknipwnpw
https://www.youtube.com/watch?v=staFQw-_e6E
```

Then run `make youtube-download` - it will automatically process only new videos.

## Transcript Cleaning & Copyediting

After downloading transcripts, they need two-stage processing to remove timestamps, filler words, and improve readability:

### Stage 1: Clean (Free)
Removes inline timestamps, filler words (uh, um, you know), and YouTube metadata:

```bash
# Clean all transcripts (auto-skips already-cleaned files)
make transcripts-clean

# Or manually:
python tools/clean_inline_timestamps.py knowledge_base/transcripts/raw/*.md
```

**What it does:**
- Removes timestamps like `<00:00:01.319>`
- Removes filler words (uh, um, er, you know, I mean, etc.)
- Aggressive deduplication of repeated phrases
- Strips YouTube metadata (keeps only title + transcript)
- Creates readable paragraphs

**Output:** Creates `*_cleaned.md` files with clean, readable text.

### Stage 2: Copyedit with Claude API (Paid)
Uses Claude Haiku 4.5 for grammar fixes and improved readability:

```bash
# Set API key first
export ANTHROPIC_API_KEY=your-key-here

# Copyedit all cleaned transcripts
make transcripts-copyedit

# Or manually:
python tools/copyedit_with_claude.py knowledge_base/transcripts/raw/*_cleaned.md
```

**What it does:**
- Fixes grammar and punctuation
- Removes remaining fillers and false starts
- Improves sentence structure and flow
- Preserves meaning and speaker's voice
- Automatically batches long transcripts to avoid context limits

**Cost:** ~$0.02-0.05 per 20-minute transcript (very affordable!)

**Output:** Creates `*_edited.md` files ready for analysis.

### Complete Pipeline
```bash
# Full workflow: download → clean → copyedit
make youtube-download
make transcripts-clean
export ANTHROPIC_API_KEY=your-key-here
make transcripts-copyedit
```

### Re-cleaning Existing Files
If you have transcripts cleaned before the latest updates, re-clean them to apply filler word removal and metadata stripping:

```bash
./reclean_transcripts.sh
```

### Documentation
- Full workflow guide: `TRANSCRIPT_CLEANING_WORKFLOW.md`
- Installation guide: `INSTALLATION.md`

## Knowledge Extraction & Obsidian Integration

After transcripts are cleaned and copyedited, automatically extract entities and build a rich Obsidian knowledge base with bidirectional wiki links.

### Quick Start

```bash
# Complete pipeline: extract → normalize → populate → link
export ANTHROPIC_API_KEY=your-key-here
make kb-build
```

### What Gets Extracted

The system uses Claude API to intelligently extract:
- **Thinkers**: People mentioned (e.g., Michael Levin, Karl Friston)
- **Concepts**: Key ideas (e.g., Cognitive Light Cone, Free Energy Principle)
- **Frameworks**: Models and methodologies (e.g., SCI Loop)
- **Institutions**: Organizations and research centers
- **Questions**: Research questions and open problems

### Features

✅ **Smart deduplication** - Fuzzy matching finds duplicates (e.g., "M. Levin" = "Michael Levin")
✅ **Name normalization** - Fixes transcription errors automatically
✅ **Bidirectional links** - Creates `[[Entity Name]]` wiki links in Obsidian
✅ **Structured pages** - Generates organized markdown files for each entity
✅ **Incremental growth** - Easily add new transcripts without duplicating work
✅ **Cost-effective** - Uses Claude Haiku 4.5 (~$0.04 per transcript)

### Step-by-Step

```bash
# Extract entities from transcripts
make kb-extract

# Normalize names and deduplicate
make kb-normalize

# Create entity pages in knowledge base
make kb-populate

# Inject wiki links into transcripts
make kb-link
```

### Knowledge Base Structure

```
knowledge_base/
├── thinkers/              # People and their ideas
├── concepts/              # Organized by category
│   ├── buddhist/
│   ├── cognitive/
│   ├── ai/
│   └── interdisciplinary/
├── frameworks/            # Models and methodologies
├── institutions/          # Organizations and centers
├── questions/             # Research questions
└── transcripts/raw/       # Linked transcripts
```

### Using with Obsidian

1. Open `knowledge_base/` in Obsidian
2. Press `Cmd/Ctrl + G` to view the knowledge graph
3. Click any entity to see connections
4. Navigate bidirectionally through wiki links

### Documentation

- Complete guide: `KNOWLEDGE_EXTRACTION_GUIDE.md`
- Structure reference: `KNOWLEDGE_STRUCTURE.md`

## Common Claude Code Commands

### Processing Transcripts
```
Claude, process all transcripts in knowledge_base/transcripts/raw and:
1. Clean and format them
2. Extract key concepts
3. Create summaries
4. Identify connections to Buddhist concepts
```

### Analyzing Connections
```
Claude, analyze the knowledge base and:
1. Map connections between Michael Levin's ideas and Buddhist concepts
2. Find bridge concepts between different thinkers
3. Create a visual network of relationships
```

### Generating Synthesis
```
Claude, create a synthesis essay on:
"How does Michael Levin's concept of intelligence as navigation in problem spaces 
relate to Buddhist ideas of skillful means and the path?"
```

## Project Structure for Claude Code

```
.claude/
├── config.json         # Project configuration
├── context/           # Context files for Claude
│   ├── project_context.md
│   └── technical_context.md
├── prompts/           # Reusable prompts
└── templates/         # Document templates

knowledge_base/
├── core_concepts/     # Fundamental concepts
├── thinkers/         # Individual thinker directories
├── transcripts/      # Video transcripts
└── synthesis/        # Generated synthesis

tools/
├── concept_extractor.py
├── connection_mapper.py
└── synthesis_generator.py
```

## Key Features for Claude Code

### 1. Context Awareness
Claude Code has access to:
- Project overview and research questions
- Technical implementation details
- File structure and naming conventions
- Key concepts and terminology

### 2. Tool Integration
Claude Code can use:
- `transcript_processor.py` - Clean and analyze transcripts
- `concept_extractor.py` - Extract and categorize concepts
- `connection_mapper.py` - Find relationships
- `synthesis_generator.py` - Create integrated content

### 3. Intelligent Processing
Claude Code understands:
- Buddhist terminology (dharma, mindfulness, non-self)
- Systems theory (emergence, complexity, feedback)
- Consciousness studies (qualia, binding problem)
- AI/ML concepts (alignment, agency)

## Example Workflows

### Workflow 1: Process New Video
```bash
# Download transcript
python tools/transcript_downloader.py "https://youtube.com/watch?v=..."

# Use Claude Code to process
claude-code
> Process the new transcript in transcripts/raw/, extract key insights about consciousness

# Generate connections
> Map how this relates to existing content on emergence and intelligence
```

### Workflow 2: Create Synthesis
```bash
# Use Claude Code for synthesis
claude-code
> Review all content on "collective intelligence" across thinkers
> Create a synthesis document comparing approaches
> Identify gaps and future research directions
```

### Workflow 3: Answer Research Question
```bash
claude-code
> Using the knowledge base, explore: 
> "What would a Buddhist-informed approach to AI alignment look like?"
> Draw from Levin, Varela, and McGilchrist's work
```

## Tips for Claude Code

1. **Be Specific**: Reference specific files or directories
2. **Use Context**: Mention relevant thinkers or concepts
3. **Iterate**: Build on previous responses
4. **Cross-Reference**: Ask Claude to connect ideas across sources
5. **Validate**: Have Claude check its work against source material

## Advanced Features

### Custom Prompts
Create reusable prompts in `.claude/prompts/`:
```markdown
# transcript_analysis.md
Analyze this transcript for:
1. Key concepts related to {topic}
2. Connections to {thinker}
3. Novel insights
4. Questions raised
```

### Templates
Use templates in `.claude/templates/` for consistent output:
```markdown
# concept_note.md
# {Concept Name}

## Definition
{definition}

## Context in Buddhism
{buddhist_context}

## Context in AI/Systems
{ai_context}

## Key Thinkers
{thinkers}

## Open Questions
{questions}
```

## Troubleshooting

- **Claude Code can't find files**: Check working directory
- **Context too large**: Use specific subdirectories
- **Unclear responses**: Provide more specific context
- **Technical errors**: Check Python environment

## Getting Help

- Check `.claude/context/` for project details
- Run `make help` for available commands
- Review example prompts in `.claude/prompts/`

Happy exploring! 🧘‍♂️🤖
