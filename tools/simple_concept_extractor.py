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
