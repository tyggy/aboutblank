#!/usr/bin/env python3
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
        links = re.findall(r'\[\[([^\]]+)\]\]', content)
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
            f.write("# Bridge Concepts\n\n")
            f.write("Concepts that connect different areas of the knowledge base:\n\n")
            for concept, score in bridges:
                f.write(f"- **{concept}**: centrality score {score:.3f}\n")
        
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
