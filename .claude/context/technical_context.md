# Technical Context for Claude Code

## File Structure
- `.claude/` - Claude Code configuration and context
- `knowledge_base/` - Main content repository
- `tools/` - Python scripts for processing
- `outputs/` - Generated content and reports

## Key Scripts

### transcript_processor.py
Processes YouTube transcripts:
- Clean and format raw transcripts
- Extract key concepts and quotes
- Generate summaries and outlines

### concept_extractor.py
Identifies and extracts concepts:
- Technical terms and definitions
- Philosophical concepts
- Cross-references to other thinkers

### connection_mapper.py
Maps relationships between ideas:
- Creates concept graphs
- Identifies thematic clusters
- Finds bridge concepts

### synthesis_generator.py
Creates integrated content:
- Generates essays connecting ideas
- Creates study guides
- Produces research summaries

## Data Formats

### Transcript Format
```markdown
# [Title]
**Metadata**: speaker, date, url
**Tags**: #concept1 #concept2
**Summary**: Brief overview

## Content
[Processed transcript]

## Key Points
- Point 1
- Point 2

## Connections
- Links to other content
```

### Concept Format
```json
{
  "term": "emergence",
  "definitions": [...],
  "contexts": [...],
  "thinkers": [...],
  "related": [...]
}
```

## Processing Pipeline
1. Download transcript → 
2. Clean and format →
3. Extract concepts →
4. Map connections →
5. Generate synthesis →
6. Update knowledge base

## Best Practices
- Always preserve original meaning
- Flag uncertainties with [?]
- Cross-reference extensively
- Maintain bidirectional links
- Version control all changes
