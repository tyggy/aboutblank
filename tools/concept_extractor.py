#!/usr/bin/env python3
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
            r'\b(?:emergence|consciousness|intelligence|agency|alignment)\b',
            # Buddhist terms  
            r'\b(?:dharma|mindfulness|compassion|interdependence|non-self)\b',
            # Systems terms
            r'\b(?:feedback|attractor|complexity|self-organization)\b',
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
            f.write("# Concept Map\n\n")
            
            # Sort by frequency
            sorted_concepts = sorted(concepts.items(), 
                                   key=lambda x: x[1]['count'], 
                                   reverse=True)
            
            for concept, data in sorted_concepts[:20]:
                f.write(f"## {concept.title()}\n")
                f.write(f"- **Frequency**: {data['count']}\n")
                f.write(f"- **Files**: {len(data['files'])}\n")
                if data['contexts']:
                    f.write(f"- **Example Context**: {data['contexts'][0][:200]}...\n")
                f.write("\n")

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
