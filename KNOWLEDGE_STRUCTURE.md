# Knowledge Base Structure

## Philosophy

This structure is designed for Obsidian with bidirectional wiki links (`[[Entity Name]]`). It balances richness with practicality - simple enough to maintain, complex enough to capture meaningful relationships.

## Folder Structure

```
knowledge_base/
├── thinkers/              # People and their ideas
│   ├── _templates/        # Templates for consistency
│   └── [person-name].md   # e.g., michael-levin.md, dalai-lama.md
│
├── concepts/              # Core ideas and theories
│   ├── _templates/
│   ├── buddhist/          # Buddhist concepts
│   ├── cognitive/         # Cognitive science concepts
│   ├── ai/                # AI/ML concepts
│   └── interdisciplinary/ # Bridge concepts
│
├── frameworks/            # Models, methodologies, systems
│   └── [framework-name].md  # e.g., sci-loop.md, four-seals.md
│
├── institutions/          # Organizations, centers, projects
│   └── [institution-name].md
│
├── sources/               # Reference materials
│   ├── books.md
│   ├── papers.md
│   ├── youtube_talks.md   # Existing
│   └── conferences.md
│
├── transcripts/           # Video/audio transcripts
│   ├── raw/               # Original downloads
│   ├── cleaned/           # After timestamp removal
│   └── edited/            # After copyediting
│
├── questions/             # Open problems and research questions
│   └── [question-slug].md
│
└── syntheses/             # Generated insights and connections
    ├── daily/             # Daily capture notes
    ├── themes/            # Thematic syntheses
    └── maps/              # Relationship maps
```

## Entity Types and Templates

### 1. Thinker (Person)

**Filename:** `thinkers/[firstname-lastname].md`

**Template fields:**
- Full name
- Aliases (for fuzzy matching)
- Primary domains (Buddhism, AI, Cognitive Science, etc.)
- Affiliated institutions
- Key concepts they discuss
- Notable works/sources
- Related thinkers
- Tags

### 2. Concept

**Filename:** `concepts/[category]/[concept-name].md`

**Template fields:**
- Concept name
- Aliases/related terms
- Category (Buddhist, Cognitive, AI, Interdisciplinary)
- Definition
- Key thinkers who discuss it
- Related concepts
- Sources where mentioned
- Tags

### 3. Framework

**Filename:** `frameworks/[framework-name].md`

**Template fields:**
- Framework name
- Creator/originator
- Description
- Components
- Applications
- Related concepts
- Sources
- Tags

### 4. Institution

**Filename:** `institutions/[institution-name].md`

**Template fields:**
- Institution name
- Type (Research center, monastery, university, project)
- Key people
- Focus areas
- Related work
- Tags

### 5. Question

**Filename:** `questions/[question-slug].md`

**Template fields:**
- Question text
- Category (alignment, ethics, metaphysics, etc.)
- Relevant thinkers
- Relevant concepts
- Current approaches
- Sources discussing it
- Tags

## Bidirectional Links

All entities link to each other using `[[Entity Name]]` syntax:

**Example from a thinker page:**
```markdown
# Michael Levin

Primary domains: [[Cognitive Science]], [[Bioelectricity]], [[Collective Intelligence]]

Key concepts:
- [[Cognitive Light Cone]]
- [[Morphogenetic Fields]]
- [[Embodied Cognition]]

Collaborates with: [[Joscha Bach]], [[Karl Friston]]

Related questions:
- [[What is the nature of agency?]]
- [[Can collective intelligence emerge from simple rules?]]
```

**Example from a concept page:**
```markdown
# Cognitive Light Cone

Category: [[Cognitive Science]] | [[Interdisciplinary]]

Key thinkers: [[Michael Levin]], [[Karl Friston]]

Related concepts: [[Free Energy Principle]], [[Active Inference]]

Mentioned in:
- [[michael-levin-intelligence-transcript]]
- [[levin-bach-consciousness-dialog]]
```

## Name Normalization Rules

To ensure consistent linking:

1. **Thinkers:** `firstname-lastname` (lowercase, hyphenated)
   - "Michael Levin" → `[[Michael Levin]]` → links to `thinkers/michael-levin.md`
   - Aliases captured in frontmatter: "Mike Levin", "M. Levin"

2. **Concepts:** Natural capitalization
   - "Cognitive Light Cone" → `[[Cognitive Light Cone]]`
   - Links to `concepts/cognitive/cognitive-light-cone.md`

3. **Multi-word entities:** Use natural spacing in links
   - Good: `[[Four Seals of Buddhism]]`
   - Filename: `concepts/buddhist/four-seals-of-buddhism.md`

## Frontmatter Standard

All entities use YAML frontmatter for metadata:

```yaml
---
type: thinker|concept|framework|institution|question
aliases: [alternative names, abbreviations]
tags: [domain1, domain2, topic1]
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
```

## Extraction Workflow

1. **During copyediting:** Extract entities and create initial database
2. **Name normalization:** Match against existing entities, create new ones
3. **Link injection:** Add wiki links to transcripts in appropriate places
4. **Bidirectional updates:** Update entity pages with transcript references
5. **Review and refinement:** Human review of auto-extracted entities

## Growth Strategy

Start minimal:
- Create only entities that appear in multiple sources or are clearly significant
- Let the database grow organically as more transcripts are processed
- Merge duplicates as they're discovered
- Refine entity definitions based on usage patterns

## Tools Needed

1. `extract_entities.py` - Extract thinkers, concepts, etc. from transcripts
2. `normalize_names.py` - Fuzzy match and normalize entity names
3. `inject_links.py` - Add wiki links to transcripts
4. `update_entity_pages.py` - Keep entity pages in sync with mentions
5. `validate_links.py` - Check for broken or inconsistent links
