# Buddhism & AI Knowledge Base - Claude Code Guide

## Quick Start with Claude Code

1. **Initial Setup**
   ```bash
   # Install Claude Code (if not already installed)
   pip install claude-code
   
   # Set up environment
   python setup_claude_env.py
   
   # Download transcripts
   make download
   ```

2. **Working with Claude Code**
   ```bash
   # Start Claude Code with project context
   claude-code --context .claude/context/
   
   # Or use the shorthand
   claude-code .
   ```

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
