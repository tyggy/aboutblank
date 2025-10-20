#!/bin/bash

# ============================================
# Buddhism & AI Knowledge Base - Environment Setup
# Fixes Python 3.14 compatibility issues
# ============================================

echo "🔧 Buddhism & AI Knowledge Base - Environment Setup"
echo "=================================================="

# Check if pyenv is installed (recommended for Python version management)
if command -v pyenv &> /dev/null; then
    echo "✅ pyenv found. Installing Python 3.11.9..."
    pyenv install -s 3.11.9
    pyenv local 3.11.9
    PYTHON_CMD="python"
elif command -v python3.11 &> /dev/null; then
    echo "✅ Python 3.11 found"
    PYTHON_CMD="python3.11"
elif command -v python3.12 &> /dev/null; then
    echo "✅ Python 3.12 found"
    PYTHON_CMD="python3.12"
else
    echo "⚠️  Compatible Python version not found!"
    echo "Please install Python 3.11 or 3.12 first:"
    echo ""
    echo "On macOS with Homebrew:"
    echo "  brew install python@3.11"
    echo ""
    echo "Or install pyenv for better version management:"
    echo "  brew install pyenv"
    echo "  pyenv install 3.11.9"
    echo ""
    exit 1
fi

echo ""
echo "📦 Creating virtual environment..."

# Remove old venv if it exists
if [ -d "venv" ]; then
    echo "Removing old virtual environment..."
    rm -rf venv
fi

# Create new virtual environment with compatible Python
$PYTHON_CMD -m venv venv

# Activate virtual environment
source venv/bin/activate

echo "✅ Virtual environment created with $(python --version)"
echo ""
echo "📚 Installing compatible packages..."

# Upgrade pip first
pip install --upgrade pip setuptools wheel

# Create compatible requirements file
cat > requirements_compatible.txt << 'EOF'
# Core YouTube transcript tools
youtube-transcript-api>=0.6.0
pytube>=15.0.0
yt-dlp>=2023.7.6

# Data processing (compatible versions)
pandas>=1.5.0,<2.0.0
numpy>=1.24.0,<2.0.0
networkx>=3.0
matplotlib>=3.7.0

# NLP packages - using older stable versions for compatibility
# Note: spacy and advanced NLP features are optional
# If you need them, install separately with:
# pip install spacy==3.5.0
# python -m spacy download en_core_web_sm

# Text processing basics (no C dependencies)
beautifulsoup4>=4.12.0
markdown>=3.4.0
python-docx>=0.8.11

# Utilities
python-dotenv>=1.0.0
click>=8.1.0
rich>=13.0.0
tqdm>=4.65.0
requests>=2.31.0

# JSON/YAML handling
pyyaml>=6.0
jsonschema>=4.17.0

# Simple analysis tools
wordcloud>=1.9.0
textstat>=0.7.3

# Testing
pytest>=7.4.0
pytest-cov>=4.1.0

# Optional: Jupyter for interactive exploration
jupyter>=1.0.0
ipykernel>=6.25.0
EOF

# Install requirements
pip install -r requirements_compatible.txt

echo ""
echo "🔧 Setting up project structure..."

# Create directory structure
mkdir -p .claude/context
mkdir -p .claude/prompts
mkdir -p .claude/templates
mkdir -p knowledge_base/core_concepts
mkdir -p knowledge_base/thinkers/michael-levin
mkdir -p knowledge_base/thinkers/francisco-varela
mkdir -p knowledge_base/thinkers/gregory-bateson
mkdir -p knowledge_base/thinkers/iain-mcgilchrist
mkdir -p knowledge_base/transcripts/raw
mkdir -p knowledge_base/transcripts/edited
mkdir -p knowledge_base/synthesis
mkdir -p tools
mkdir -p outputs

echo "✅ Directory structure created"
echo ""

# Create simplified concept extractor without spaCy
cat > tools/simple_concept_extractor.py << 'PYTHON'
#!/usr/bin/env python3
"""
Simple Concept Extractor for Buddhism & AI Knowledge Base
Works without spaCy or other complex NLP libraries
"""

import re
import json
from pathlib import Path
from collections import Counter
from typing import Dict, List, Set

class SimpleConceptExtractor:
    def __init__(self):
        # Define concept patterns manually
        self.buddhist_concepts = [
            'dharma', 'mindfulness', 'compassion', 'interdependence', 
            'non-self', 'emptiness', 'suffering', 'enlightenment',
            'meditation', 'awareness', 'impermanence', 'karma',
            'skillful means', 'middle way', 'noble truths'
        ]
        
        self.ai_concepts = [
            'intelligence', 'consciousness', 'emergence', 'agency',
            'alignment', 'goal-directed', 'optimization', 'learning',
            'neural network', 'artificial', 'machine learning',
            'cognition', 'computation', 'information processing'
        ]
        
        self.systems_concepts = [
            'complexity', 'feedback', 'attractor', 'self-organization',
            'autopoiesis', 'morphogenesis', 'collective', 'network',
            'dynamics', 'pattern', 'hierarchy', 'holarchy',
            'synergy', 'resilience', 'adaptation'
        ]
        
        self.thinker_concepts = {
            'levin': ['bioelectric', 'morphogenetic', 'xenobots', 'collective intelligence'],
            'varela': ['enactivism', 'embodied', 'autopoiesis', 'ethical know-how'],
            'mcgilchrist': ['hemisphere', 'attention', 'master', 'emissary'],
            'bateson': ['ecology of mind', 'deutero-learning', 'schismogenesis']
        }
        
    def extract_concepts(self, text: str) -> Dict[str, List[str]]:
        """Extract concepts from text"""
        text_lower = text.lower()
        found_concepts = {
            'buddhist': [],
            'ai': [],
            'systems': [],
            'thinkers': []
        }
        
        # Find Buddhist concepts
        for concept in self.buddhist_concepts:
            if concept in text_lower:
                count = text_lower.count(concept)
                found_concepts['buddhist'].append({
                    'term': concept,
                    'count': count
                })
        
        # Find AI concepts
        for concept in self.ai_concepts:
            if concept in text_lower:
                count = text_lower.count(concept)
                found_concepts['ai'].append({
                    'term': concept,
                    'count': count
                })
        
        # Find Systems concepts
        for concept in self.systems_concepts:
            if concept in text_lower:
                count = text_lower.count(concept)
                found_concepts['systems'].append({
                    'term': concept,
                    'count': count
                })
        
        # Find thinker-specific concepts
        for thinker, concepts in self.thinker_concepts.items():
            for concept in concepts:
                if concept in text_lower:
                    count = text_lower.count(concept)
                    found_concepts['thinkers'].append({
                        'thinker': thinker,
                        'term': concept,
                        'count': count
                    })
        
        return found_concepts
    
    def extract_quotes(self, text: str) -> List[str]:
        """Extract potential important quotes"""
        sentences = text.split('.')
        important_sentences = []
        
        keywords = ['intelligence', 'consciousness', 'buddhist', 'meaning',
                   'understand', 'emergence', 'collective', 'navigation']
        
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in keywords):
                if 50 < len(sentence) < 300:  # Reasonable quote length
                    important_sentences.append(sentence.strip())
        
        return important_sentences[:10]  # Top 10 quotes
    
    def process_file(self, filepath: Path) -> Dict:
        """Process a single file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
        
        return {
            'file': str(filepath),
            'concepts': self.extract_concepts(text),
            'key_quotes': self.extract_quotes(text),
            'word_count': len(text.split())
        }
    
    def process_directory(self, directory: Path) -> List[Dict]:
        """Process all markdown files in a directory"""
        results = []
        
        for filepath in directory.rglob("*.md"):
            print(f"Processing: {filepath}")
            results.append(self.process_file(filepath))
        
        return results
    
    def generate_report(self, results: List[Dict], output_path: Path):
        """Generate analysis report"""
        all_buddhist = Counter()
        all_ai = Counter()
        all_systems = Counter()
        
        for result in results:
            for concept in result['concepts']['buddhist']:
                all_buddhist[concept['term']] += concept['count']
            for concept in result['concepts']['ai']:
                all_ai[concept['term']] += concept['count']
            for concept in result['concepts']['systems']:
                all_systems[concept['term']] += concept['count']
        
        report = {
            'total_files': len(results),
            'top_buddhist_concepts': dict(all_buddhist.most_common(10)),
            'top_ai_concepts': dict(all_ai.most_common(10)),
            'top_systems_concepts': dict(all_systems.most_common(10)),
            'file_analyses': results
        }
        
        # Save JSON report
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Create markdown summary
        md_path = output_path.with_suffix('.md')
        with open(md_path, 'w') as f:
            f.write("# Concept Extraction Report\n\n")
            f.write(f"**Files Analyzed**: {len(results)}\n\n")
            
            f.write("## Top Buddhist Concepts\n")
            for concept, count in all_buddhist.most_common(5):
                f.write(f"- **{concept}**: {count} occurrences\n")
            
            f.write("\n## Top AI Concepts\n")
            for concept, count in all_ai.most_common(5):
                f.write(f"- **{concept}**: {count} occurrences\n")
            
            f.write("\n## Top Systems Concepts\n")
            for concept, count in all_systems.most_common(5):
                f.write(f"- **{concept}**: {count} occurrences\n")
        
        print(f"Report saved to {output_path}")
        print(f"Summary saved to {md_path}")

if __name__ == "__main__":
    import sys
    
    extractor = SimpleConceptExtractor()
    
    # Default to knowledge_base directory
    directory = Path(sys.argv[1] if len(sys.argv) > 1 else "knowledge_base")
    
    if directory.exists():
        results = extractor.process_directory(directory)
        output_path = Path("outputs/concept_analysis.json")
        output_path.parent.mkdir(exist_ok=True)
        extractor.generate_report(results, output_path)
    else:
        print(f"Directory {directory} not found")
PYTHON

chmod +x tools/simple_concept_extractor.py

echo ""
echo "✅ Created simplified concept extractor"

# Create a test script
cat > test_setup.py << 'PYTHON'
#!/usr/bin/env python3
"""Test that the environment is set up correctly"""

import sys
print(f"Python version: {sys.version}")

try:
    import youtube_transcript_api
    print("✅ youtube_transcript_api installed")
except ImportError:
    print("❌ youtube_transcript_api not installed")

try:
    import pandas
    print("✅ pandas installed")
except ImportError:
    print("❌ pandas not installed")

try:
    import matplotlib
    print("✅ matplotlib installed")
except ImportError:
    print("❌ matplotlib not installed")

try:
    import networkx
    print("✅ networkx installed")
except ImportError:
    print("❌ networkx not installed")

print("\n🎉 Basic environment ready!")
print("\nNote: Advanced NLP features (spaCy) are optional.")
print("If you need them later, run:")
print("  pip install spacy==3.5.0")
print("  python -m spacy download en_core_web_sm")
PYTHON

echo ""
echo "🧪 Testing setup..."
python test_setup.py

echo ""
echo "=================================================="
echo "✅ Environment setup complete!"
echo ""
echo "Next steps:"
echo "1. Activate the environment: source venv/bin/activate"
echo "2. Test transcript download: python tools/transcript_downloader.py <youtube-url>"
echo "3. Extract concepts: python tools/simple_concept_extractor.py"
echo ""
echo "The environment uses Python 3.11/3.12 for compatibility."
echo "Advanced NLP features are optional and can be added later if needed."
echo "=================================================="