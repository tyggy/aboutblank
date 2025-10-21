#!/usr/bin/env python3
"""
Recategorize existing concept entities using improved categorization guidelines.

Reads concept JSON files, uses Claude to re-categorize them based on new
specific guidelines, and updates the category field.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, Optional
from collections import defaultdict
from anthropic import Anthropic


class ConceptRecategorizer:
    """Re-categorize concepts using improved guidelines."""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-haiku-4-5-20251001", dry_run: bool = False):
        """Initialize with API key and model."""
        self.client = Anthropic(api_key=api_key or os.environ.get('ANTHROPIC_API_KEY'))
        self.model = model
        self.dry_run = dry_run
        self.stats = defaultdict(int)

    def categorize_concept(self, concept_name: str, concept_context: str, current_category: str) -> str:
        """
        Use Claude to categorize a concept.

        Args:
            concept_name: Name of the concept
            concept_context: Context/description of the concept
            current_category: Current category (for reference)

        Returns:
            New category name
        """
        prompt = f"""You are categorizing a concept for a Buddhism & AI knowledge base.

Concept: {concept_name}
Context: {concept_context}
Current category: {current_category}

Choose the MOST SPECIFIC category from these options:

- **biology**: Cells, genes, bioelectricity, morphogenesis, regeneration, development, evolution, organisms
  Examples: gap junctions, action potentials, gene networks, xenobots, morphogenesis

- **cognitive**: Mind, perception, consciousness, memory, learning, neuroscience, psychology
  Examples: embodied cognition, predictive processing, self-model, attention

- **ai**: Machine learning, neural networks, algorithms, computational intelligence
  Examples: transformers, autoencoders, reinforcement learning, deep learning

- **buddhist**: Buddhist teachings, practices, concepts from Buddhist philosophy
  Examples: anatta, dukkha, emptiness, dependent arising, mindfulness

- **philosophy**: Metaphysics, epistemology, phenomenology, ontology, ethics (non-Buddhist)
  Examples: supervenience, panpsychism, hard problem, emergence

- **systems**: Cybernetics, complexity, systems theory, information theory
  Examples: autopoiesis, stigmergy, dissipative structures, feedback loops

- **interdisciplinary**: RARELY USE - only when concept genuinely cannot fit in single category above
  Examples: collective intelligence (biology+cognitive+systems), self (philosophy+cognitive+buddhist)

IMPORTANT: Default to specific categories. "interdisciplinary" should be used sparingly (<10%).

Respond with ONLY the category name, nothing else. One word: biology, cognitive, ai, buddhist, philosophy, systems, or interdisciplinary."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=20,  # Just need one word
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            category = response.content[0].text.strip().lower()

            # Validate category
            valid_categories = {'biology', 'cognitive', 'ai', 'buddhist', 'philosophy', 'systems', 'interdisciplinary'}
            if category not in valid_categories:
                print(f"  ⚠️  Invalid category '{category}' for {concept_name}, keeping '{current_category}'", file=sys.stderr)
                return current_category

            return category

        except Exception as e:
            print(f"  ❌ Error categorizing {concept_name}: {e}", file=sys.stderr)
            return current_category

    def recategorize_concepts(self, entities_dir: Path, verbose: bool = False) -> None:
        """
        Recategorize all concept entities.

        Args:
            entities_dir: Path to knowledge_base/entities directory
            verbose: Show verbose output
        """
        concepts_dir = entities_dir / 'concepts'

        if not concepts_dir.exists():
            print(f"❌ Error: Concepts directory not found: {concepts_dir}", file=sys.stderr)
            sys.exit(1)

        # Find all concept JSON files
        concept_files = list(concepts_dir.glob('*.json'))

        if not concept_files:
            print("No concept JSON files found.", file=sys.stderr)
            return

        print(f"🔄 Recategorizing {len(concept_files)} concepts...")
        if self.dry_run:
            print("🔍 DRY RUN MODE - No files will be modified")
        print()

        for i, json_file in enumerate(concept_files, 1):
            try:
                # Load concept
                concept = json.loads(json_file.read_text(encoding='utf-8'))

                concept_name = concept.get('name', '')
                current_category = concept.get('category', 'interdisciplinary')

                # Get context for categorization
                context = concept.get('context', '')
                if not context:
                    # Try contexts array
                    contexts = concept.get('contexts', [])
                    if contexts:
                        context = contexts[0].get('text', '')

                if not context:
                    if verbose:
                        print(f"  [{i}/{len(concept_files)}] ⊘ Skipping {concept_name} (no context)")
                    self.stats['skipped_no_context'] += 1
                    continue

                # Categorize
                new_category = self.categorize_concept(concept_name, context, current_category)

                # Track changes
                if new_category != current_category:
                    self.stats['changed'] += 1
                    self.stats[f'{current_category}→{new_category}'] += 1

                    if verbose or not self.dry_run:
                        print(f"  [{i}/{len(concept_files)}] ✓ {concept_name}: {current_category} → {new_category}")

                    if not self.dry_run:
                        # Update concept
                        concept['category'] = new_category

                        # Save updated JSON
                        json_file.write_text(
                            json.dumps(concept, indent=2, ensure_ascii=False) + '\n',
                            encoding='utf-8'
                        )
                else:
                    self.stats['unchanged'] += 1
                    if verbose:
                        print(f"  [{i}/{len(concept_files)}] ⊘ {concept_name}: {current_category} (unchanged)")

            except Exception as e:
                print(f"  ❌ Error processing {json_file.name}: {e}", file=sys.stderr)
                self.stats['errors'] += 1

        self.print_summary()

    def print_summary(self) -> None:
        """Print categorization summary."""
        print()
        print("=" * 60)
        print("📊 Recategorization Summary")
        print("=" * 60)
        print(f"  ✓ Changed: {self.stats['changed']}")
        print(f"  ⊘ Unchanged: {self.stats['unchanged']}")
        if self.stats['skipped_no_context']:
            print(f"  ⊘ Skipped (no context): {self.stats['skipped_no_context']}")
        if self.stats['errors']:
            print(f"  ❌ Errors: {self.stats['errors']}")
        print()

        # Show category changes
        changes = [(k, v) for k, v in self.stats.items() if '→' in k]
        if changes:
            print("Category changes:")
            for change, count in sorted(changes, key=lambda x: -x[1]):
                print(f"  • {change}: {count}")
            print()

        print("Next steps:")
        if self.dry_run:
            print("  1. Review the changes above")
            print("  2. Run without --dry-run to apply changes")
            print("  3. Then run: make kb-populate-force")
        else:
            print("  Run: make kb-populate-force")
            print("  This will regenerate markdown files in the new category directories")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Recategorize concept entities with improved guidelines"
    )
    parser.add_argument(
        '--knowledge-base',
        type=Path,
        default=Path('knowledge_base'),
        help='Knowledge base directory (default: knowledge_base)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Don't actually modify files, just show what would change"
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Show all concepts, including unchanged ones'
    )
    parser.add_argument(
        '--model',
        default='claude-haiku-4-5-20251001',
        help='Model to use (default: claude-haiku-4-5-20251001)'
    )

    args = parser.parse_args()

    entities_dir = args.knowledge_base / 'entities'
    if not entities_dir.exists():
        print(f"❌ Error: Entities directory not found: {entities_dir}", file=sys.stderr)
        print(f"   Run 'make kb-normalize' first to create entity files.", file=sys.stderr)
        sys.exit(1)

    # Initialize recategorizer
    recategorizer = ConceptRecategorizer(
        model=args.model,
        dry_run=args.dry_run
    )

    # Recategorize
    recategorizer.recategorize_concepts(entities_dir, verbose=args.verbose)


if __name__ == '__main__':
    main()
