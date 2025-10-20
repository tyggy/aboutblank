#!/usr/bin/env python3
"""
Claude Code Environment Setup and Helper Scripts
For Buddhism & AI Knowledge Base Project
"""

import os
import json
import yaml
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import hashlib

class ClaudeCodeEnvironment:
    """Setup and manage Claude Code environment for knowledge base work"""
    
    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
        self.config_path = self.base_path / ".claude"
        self.context_path = self.config_path / "context"
        
    def setup_environment(self):
        """Create full Claude Code environment structure"""
        
        # Create directory structure
        directories = [
            ".claude/context",
            ".claude/prompts", 
            ".claude/templates",
            ".claude/scripts",
            "knowledge_base/core_concepts",
            "knowledge_base/thinkers",
            "knowledge_base/transcripts",
            "knowledge_base/synthesis",
            "tools",
            "outputs"
        ]
        
        for dir_path in directories:
            (self.base_path / dir_path).mkdir(parents=True, exist_ok=True)
        
        # Create configuration files
        self._create_claude_config()
        self._create_context_files()
        self._create_helper_scripts()
        self._create_makefile()
        self._create_readme()
        
        print("✅ Claude Code environment setup complete!")
        
    def _create_claude_config(self):
        """Create main Claude Code configuration"""
        
        config = {
            "project_name": "Buddhism & AI Knowledge Base",
            "version": "1.0.0",
            "description": "Exploring consciousness, intelligence, and ethics through Buddhist and AI lenses",
            "main_themes": [
                "consciousness_and_intelligence",
                "ethical_navigation", 
                "truth_seeking",
                "artificial_selves",
                "systems_thinking"
            ],
            "key_thinkers": [
                "Michael Levin",
                "Francisco Varela",
                "Gregory Bateson",
                "Iain McGilchrist",
                "David Chapman",
                "Eugene Gendlin"
            ],
            "tools": {
                "transcript_processor": "tools/transcript_processor.py",
                "concept_extractor": "tools/concept_extractor.py",
                "connection_mapper": "tools/connection_mapper.py",
                "synthesis_generator": "tools/synthesis_generator.py"
            },
            "output_formats": ["markdown", "json", "graph"],
            "claude_code_version": "latest"
        }
        
        with open(self.config_path / "config.json", "w") as f:
            json.dump(config, f, indent=2)
    
    def _create_context_files(self):
        """Create context files for Claude Code"""
        
        # Project context
        project_context = """# Buddhism & AI Knowledge Base - Project Context

## Overview
This project explores the intersection of Buddhist philosophy, consciousness studies, and artificial intelligence. We're building a comprehensive knowledge base that maps connections between diverse thinkers and concepts.

## Core Research Questions
1. How do different scales and forms of intelligence relate to each other?
2. What is the relationship between understanding, experience, and consciousness?
3. How can we navigate truth and ethics in complex, emergent systems?
4. What forms of care and connection are possible between diverse intelligences?

## Theoretical Framework
- **Buddhist Philosophy**: Non-self, interdependence, mindfulness, compassion
- **Systems Theory**: Emergence, feedback loops, attractors, complexity
- **Consciousness Studies**: Qualia, binding problem, integrated information theory
- **AI/ML**: Alignment, agency, goal-directedness, value learning

## Key Thinkers & Their Contributions

### Michael Levin
- Bioelectric networks and morphogenesis
- Intelligence as navigation in problem spaces
- "Platonic spaces of patterns"
- Collective intelligence and goal-directedness

### Francisco Varela
- Enactivism and embodied cognition
- Ethical know-how vs ethical knowledge
- Autopoiesis and self-organization

### Iain McGilchrist
- Attention and hemispheric specialization
- Different modes of being and knowing
- Truth and value in "The Matter with Things"

### Gregory Bateson
- Ecology of mind
- Levels of learning and communication
- Pattern that connects

## Working Methods
1. **Transcript Analysis**: Extract and synthesize ideas from video content
2. **Concept Mapping**: Identify connections between ideas across thinkers
3. **Pattern Recognition**: Find recurring themes and principles
4. **Synthesis Writing**: Create integrated perspectives on key questions

## Technical Approach
- Use Claude Code for automated processing and analysis
- Maintain markdown-based knowledge base for portability
- Create visualizations of conceptual networks
- Build tools for exploring and navigating the knowledge space

## Current Focus Areas
1. Processing Michael Levin's video transcripts
2. Mapping connections to Buddhist concepts
3. Developing synthesis on intelligence and consciousness
4. Creating practical applications for AI alignment
"""
        
        with open(self.context_path / "project_context.md", "w") as f:
            f.write(project_context)
        
        # Technical context
        technical_context = """# Technical Context for Claude Code

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
"""
        
        with open(self.context_path / "technical_context.md", "w") as f:
            f.write(technical_context)
    
    def _create_helper_scripts(self):
        """Create helper scripts for Claude Code"""
        
        # Concept extractor script
        concept_extractor = '''#!/usr/bin/env python3
"""Extract concepts from transcripts and documents"""

import re
import json
from pathlib import Path
from typing import List, Dict, Set
from collections import Counter

class ConceptExtractor:
    def __init__(self):
        self.concepts = {}
        self.concept_patterns = [
            # Technical terms
            r'\\b(?:emergence|consciousness|intelligence|agency|alignment)\\b',
            # Buddhist terms  
            r'\\b(?:dharma|mindfulness|compassion|interdependence|non-self)\\b',
            # Systems terms
            r'\\b(?:feedback|attractor|complexity|self-organization)\\b',
        ]
        
    def extract_from_file(self, filepath: Path) -> Dict:
        """Extract concepts from a single file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().lower()
        
        found_concepts = {}
        for pattern in self.concept_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if match not in found_concepts:
                    found_concepts[match] = {
                        'count': 0,
                        'contexts': []
                    }
                found_concepts[match]['count'] += 1
                
                # Extract context around the term
                context = self._get_context(content, match)
                if context and len(found_concepts[match]['contexts']) < 3:
                    found_concepts[match]['contexts'].append(context)
        
        return found_concepts
    
    def _get_context(self, content: str, term: str, window: int = 100) -> str:
        """Get context around a term"""
        pos = content.find(term)
        if pos == -1:
            return ""
        
        start = max(0, pos - window)
        end = min(len(content), pos + len(term) + window)
        
        context = content[start:end]
        # Clean up to sentence boundaries
        if start > 0:
            first_period = context.find('. ')
            if first_period != -1:
                context = context[first_period + 2:]
        
        return context.strip()
    
    def extract_from_directory(self, directory: Path) -> Dict:
        """Extract concepts from all files in directory"""
        all_concepts = {}
        
        for filepath in directory.rglob("*.md"):
            file_concepts = self.extract_from_file(filepath)
            
            for concept, data in file_concepts.items():
                if concept not in all_concepts:
                    all_concepts[concept] = {
                        'count': 0,
                        'files': [],
                        'contexts': []
                    }
                
                all_concepts[concept]['count'] += data['count']
                all_concepts[concept]['files'].append(str(filepath))
                all_concepts[concept]['contexts'].extend(data['contexts'])
        
        return all_concepts
    
    def save_concept_map(self, concepts: Dict, output_path: Path):
        """Save concept map to JSON"""
        with open(output_path, 'w') as f:
            json.dump(concepts, f, indent=2)
        
        # Also create markdown summary
        md_path = output_path.with_suffix('.md')
        with open(md_path, 'w') as f:
            f.write("# Concept Map\\n\\n")
            
            # Sort by frequency
            sorted_concepts = sorted(concepts.items(), 
                                   key=lambda x: x[1]['count'], 
                                   reverse=True)
            
            for concept, data in sorted_concepts[:20]:
                f.write(f"## {concept.title()}\\n")
                f.write(f"- **Frequency**: {data['count']}\\n")
                f.write(f"- **Files**: {len(data['files'])}\\n")
                if data['contexts']:
                    f.write(f"- **Example Context**: {data['contexts'][0][:200]}...\\n")
                f.write("\\n")

if __name__ == "__main__":
    import sys
    
    extractor = ConceptExtractor()
    
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
        if path.is_file():
            concepts = extractor.extract_from_file(path)
        else:
            concepts = extractor.extract_from_directory(path)
        
        output_path = Path("outputs/concept_map.json")
        extractor.save_concept_map(concepts, output_path)
        print(f"Concept map saved to {output_path}")
    else:
        print("Usage: concept_extractor.py <file_or_directory>")
'''
        
        with open(self.base_path / "tools" / "concept_extractor.py", "w") as f:
            f.write(concept_extractor)
        
        # Connection mapper script  
        connection_mapper = '''#!/usr/bin/env python3
"""Map connections between concepts and thinkers"""

import json
import networkx as nx
from pathlib import Path
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt

class ConnectionMapper:
    def __init__(self):
        self.graph = nx.Graph()
        self.thinker_concepts = {}
        
    def load_knowledge_base(self, kb_path: Path):
        """Load knowledge base and build connection graph"""
        
        # Load thinker files
        thinkers_path = kb_path / "thinkers"
        if thinkers_path.exists():
            for thinker_dir in thinkers_path.iterdir():
                if thinker_dir.is_dir():
                    self._process_thinker(thinker_dir)
        
        # Load concept files
        concepts_path = kb_path / "core_concepts"
        if concepts_path.exists():
            for concept_file in concepts_path.glob("*.md"):
                self._process_concept(concept_file)
    
    def _process_thinker(self, thinker_dir: Path):
        """Process a thinker's directory"""
        thinker_name = thinker_dir.name.replace("-", " ").title()
        self.graph.add_node(thinker_name, node_type="thinker")
        
        # Look for concepts in their files
        for filepath in thinker_dir.rglob("*.md"):
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Extract concepts (simplified - you'd want more sophisticated extraction)
                concepts = self._extract_concepts_from_content(content)
                
                for concept in concepts:
                    self.graph.add_node(concept, node_type="concept")
                    self.graph.add_edge(thinker_name, concept)
    
    def _process_concept(self, concept_file: Path):
        """Process a concept file"""
        concept_name = concept_file.stem.replace("-", " ").title()
        self.graph.add_node(concept_name, node_type="concept")
        
        with open(concept_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Find related concepts and thinkers
            related = self._extract_related_items(content)
            
            for item in related:
                if item not in self.graph:
                    self.graph.add_node(item, node_type="unknown")
                self.graph.add_edge(concept_name, item)
    
    def _extract_concepts_from_content(self, content: str) -> List[str]:
        """Extract concepts from content (simplified)"""
        # This is a simplified version - you'd want NLP here
        concepts = []
        
        keywords = [
            "consciousness", "intelligence", "emergence", 
            "ethics", "mindfulness", "systems", "complexity"
        ]
        
        for keyword in keywords:
            if keyword.lower() in content.lower():
                concepts.append(keyword.title())
        
        return concepts
    
    def _extract_related_items(self, content: str) -> List[str]:
        """Extract related items from content"""
        related = []
        
        # Look for markdown links
        import re
        links = re.findall(r'\\[\\[([^\\]]+)\\]\\]', content)
        related.extend(links)
        
        return related
    
    def find_bridges(self) -> List[Tuple[str, str]]:
        """Find bridge concepts connecting different areas"""
        bridges = []
        
        # Find nodes with high betweenness centrality
        centrality = nx.betweenness_centrality(self.graph)
        
        # Get top bridge nodes
        sorted_nodes = sorted(centrality.items(), key=lambda x: x[1], reverse=True)
        
        for node, score in sorted_nodes[:10]:
            if score > 0:
                bridges.append((node, score))
        
        return bridges
    
    def find_clusters(self) -> Dict[int, List[str]]:
        """Find conceptual clusters"""
        from networkx.algorithms import community
        
        communities = community.greedy_modularity_communities(self.graph)
        
        clusters = {}
        for i, community_set in enumerate(communities):
            clusters[i] = list(community_set)
        
        return clusters
    
    def visualize(self, output_path: Path):
        """Create network visualization"""
        plt.figure(figsize=(15, 10))
        
        # Set up positions
        pos = nx.spring_layout(self.graph, k=2, iterations=50)
        
        # Draw nodes by type
        thinkers = [n for n, d in self.graph.nodes(data=True) 
                   if d.get('node_type') == 'thinker']
        concepts = [n for n, d in self.graph.nodes(data=True) 
                   if d.get('node_type') == 'concept']
        
        nx.draw_networkx_nodes(self.graph, pos, nodelist=thinkers, 
                             node_color='lightblue', node_size=500, label='Thinkers')
        nx.draw_networkx_nodes(self.graph, pos, nodelist=concepts,
                             node_color='lightgreen', node_size=300, label='Concepts')
        
        # Draw edges and labels
        nx.draw_networkx_edges(self.graph, pos, alpha=0.2)
        nx.draw_networkx_labels(self.graph, pos, font_size=8)
        
        plt.title("Knowledge Base Concept Network")
        plt.legend()
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    def save_analysis(self, output_dir: Path):
        """Save network analysis"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save graph data
        nx.write_gexf(self.graph, output_dir / "knowledge_graph.gexf")
        
        # Save bridges
        bridges = self.find_bridges()
        with open(output_dir / "bridge_concepts.md", "w") as f:
            f.write("# Bridge Concepts\\n\\n")
            f.write("Concepts that connect different areas of the knowledge base:\\n\\n")
            for concept, score in bridges:
                f.write(f"- **{concept}**: centrality score {score:.3f}\\n")
        
        # Save clusters
        clusters = self.find_clusters()
        with open(output_dir / "concept_clusters.json", "w") as f:
            json.dump(clusters, f, indent=2)
        
        # Create visualization
        self.visualize(output_dir / "concept_network.png")

if __name__ == "__main__":
    import sys
    
    mapper = ConnectionMapper()
    
    kb_path = Path(sys.argv[1] if len(sys.argv) > 1 else "knowledge_base")
    output_dir = Path("outputs/connections")
    
    mapper.load_knowledge_base(kb_path)
    mapper.save_analysis(output_dir)
    
    print(f"Connection analysis saved to {output_dir}")
'''
        
        with open(self.base_path / "tools" / "connection_mapper.py", "w") as f:
            f.write(connection_mapper)
    
    def _create_makefile(self):
        """Create Makefile for common tasks"""
        
        makefile = """# Makefile for Buddhism & AI Knowledge Base

.PHONY: help setup process analyze synthesize clean

help:
	@echo "Buddhism & AI Knowledge Base - Available commands:"
	@echo "  make setup      - Set up Claude Code environment"
	@echo "  make download   - Download all transcripts"
	@echo "  make process    - Process all transcripts" 
	@echo "  make analyze    - Run concept extraction and mapping"
	@echo "  make synthesize - Generate synthesis documents"
	@echo "  make report     - Generate full project report"
	@echo "  make clean      - Clean generated files"

setup:
	python -m venv venv
	. venv/bin/activate && pip install -r requirements.txt
	python setup_claude_env.py

download:
	python tools/transcript_downloader.py Buddhism_&_AI.md -o knowledge_base/transcripts/raw

process:
	@echo "Processing transcripts..."
	python tools/transcript_processor.py knowledge_base/transcripts/raw
	@echo "Transcripts processed!"

analyze:
	@echo "Extracting concepts..."
	python tools/concept_extractor.py knowledge_base/
	@echo "Mapping connections..."
	python tools/connection_mapper.py knowledge_base/
	@echo "Analysis complete!"

synthesize:
	@echo "Generating synthesis..."
	python tools/synthesis_generator.py
	@echo "Synthesis complete!"

report:
	@echo "Generating project report..."
	@make analyze
	@make synthesize
	python tools/generate_report.py
	@echo "Report generated in outputs/report.md"

clean:
	rm -rf outputs/*
	rm -rf __pycache__
	rm -rf .pytest_cache
	find . -type f -name "*.pyc" -delete

# Claude Code specific commands
claude-context:
	@echo "Updating Claude Code context..."
	python tools/update_context.py
	@echo "Context updated!"

claude-prompt:
	@echo "Generating Claude Code prompt for current task..."
	python tools/generate_claude_prompt.py
	@echo "Prompt copied to clipboard!"

test:
	pytest tests/ -v

backup:
	tar -czf backup_$(shell date +%Y%m%d_%H%M%S).tar.gz knowledge_base/
	@echo "Backup created!"
"""
        
        with open(self.base_path / "Makefile", "w") as f:
            f.write(makefile)
    
    def _create_readme(self):
        """Create README for Claude Code"""
        
        readme = """# Buddhism & AI Knowledge Base - Claude Code Guide

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
"""
        
        with open(self.base_path / "README_CLAUDE.md", "w") as f:
            f.write(readme)

# Main setup function
def setup_claude_code_environment():
    """Run the complete setup"""
    env = ClaudeCodeEnvironment()
    env.setup_environment()
    
    # Create requirements.txt
    requirements = """# Requirements for Buddhism & AI Knowledge Base

# Core dependencies
youtube-transcript-api>=0.6.0
pytube>=15.0.0
yt-dlp>=2023.7.6

# Processing and analysis
pandas>=2.0.0
numpy>=1.24.0
networkx>=3.0
matplotlib>=3.7.0
scikit-learn>=1.3.0

# NLP and text processing
spacy>=3.5.0
nltk>=3.8.0
textblob>=0.17.0

# Claude Code and API
anthropic>=0.3.0
claude-code>=0.1.0

# Utilities
python-dotenv>=1.0.0
click>=8.1.0
rich>=13.0.0
tqdm>=4.65.0

# Documentation
mkdocs>=1.5.0
mkdocs-material>=9.0.0

# Testing
pytest>=7.4.0
pytest-cov>=4.1.0

# Optional but recommended
jupyter>=1.0.0
ipykernel>=6.25.0
"""
    
    with open("requirements.txt", "w") as f:
        f.write(requirements)
    
    print("\n🎉 Setup complete! Next steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Download transcripts: make download")  
    print("3. Start Claude Code: claude-code .")
    print("\nCheck README_CLAUDE.md for detailed instructions!")

if __name__ == "__main__":
    setup_claude_code_environment()
