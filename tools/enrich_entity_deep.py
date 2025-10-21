#!/usr/bin/env python3
"""
Deep enrichment of entity pages from source documents.

Takes entities from normalized_entities.json and enriches them with
comprehensive information extracted from all source documents.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
from anthropic import Anthropic
import re


class EntityEnricher:
    """Enrich entities with deep, comprehensive information."""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-5-sonnet-20241022"):
        """
        Initialize enricher.

        Note: Uses Sonnet for better quality and can draw on broader knowledge.
        """
        self.client = Anthropic(api_key=api_key or os.environ.get('ANTHROPIC_API_KEY'))
        self.model = model
        self.max_tokens = 8192  # Balanced for comprehensive but focused content

    def find_entity_mentions(self, entity_name: str, source_files: List[Path]) -> List[Dict]:
        """
        Find all mentions of entity across source files.

        Returns list of {file, section, text} dictionaries.
        """
        mentions = []

        for source_file in source_files:
            if not source_file.exists():
                continue

            try:
                content = source_file.read_text(encoding='utf-8')

                # Find paragraphs mentioning the entity (case-insensitive)
                pattern = re.compile(rf'\b{re.escape(entity_name)}\b', re.IGNORECASE)
                paragraphs = content.split('\n\n')

                for para in paragraphs:
                    if pattern.search(para):
                        mentions.append({
                            'file': source_file.name,
                            'text': para.strip()
                        })

            except Exception as e:
                print(f"⚠️  Error reading {source_file}: {e}", file=sys.stderr)
                continue

        return mentions

    def enrich_concept(self, concept: Dict, mentions: List[Dict], verbose: bool = False) -> Dict:
        """
        Create comprehensive enriched concept entry.

        Returns enriched concept with detailed sections.
        """
        if verbose:
            print(f"  🔍 Enriching: {concept['name']}")
            print(f"     Found {len(mentions)} mentions across sources")

        # Build context from all mentions
        mentions_text = ""
        for i, mention in enumerate(mentions[:20], 1):  # Limit to 20 most relevant
            mentions_text += f"\n{i}. From {mention['file']}:\n{mention['text']}\n"

        # Build adaptive enrichment prompt
        prompt = f"""You are creating a comprehensive knowledge base article about "{concept['name']}", a concept in the intersection of Buddhism, AI, and consciousness studies.

CURRENT BASIC DEFINITION:
{concept.get('context', 'No basic definition available.')}

ALL MENTIONS FROM SOURCE DOCUMENTS:
{mentions_text}

Create an enriched article that combines insights from the source documents with your broader knowledge of this concept.

GUIDELINES:
1. Start with a clear Definition section (2-4 sentences) that synthesizes both source material and your knowledge
2. Create additional sections where you have valuable information to share (from sources OR your training):
   - Historical Context & Origins (who proposed it, evolution of the concept)
   - How It Works (mechanisms, processes, technical details)
   - Examples & Applications (concrete instances, real-world use)
   - Relationships (connections to other concepts/frameworks mentioned in sources or relevant ones you know)
   - Open Questions (unresolved issues, research frontiers)
   - Key References (from sources)

IMPORTANT:
- Use clear, accessible language
- When citing source material, note it explicitly (e.g., "According to Levin..." or "As discussed in [source]...")
- You may draw on your general knowledge to provide richer context beyond what's in the sources
- For well-known concepts, provide comprehensive coverage even if sources are limited
- DO NOT create empty sections - only include sections where you have substantive content
- Aim for a middle ground between basic definition and full Wikipedia article
- Structure should be natural and flow from the content
- Length should be adaptive: richer for well-known concepts, more focused for niche ones (typically 3-10 paragraphs)

Return the enriched article in markdown format with appropriate section headings."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            enriched_text = response.content[0].text.strip()

            if verbose:
                print(f"     ✓ Generated {len(enriched_text):,} character enrichment")

            # Add to concept
            concept['enriched_content'] = enriched_text
            concept['enrichment_model'] = self.model
            concept['enrichment_source_count'] = len(mentions)

            return concept

        except Exception as e:
            print(f"  ❌ Error enriching {concept['name']}: {e}", file=sys.stderr)
            return concept

    def should_enrich(
        self,
        entity: Dict,
        mentions: List[Dict],
        min_sources: int = 3,
        min_mentions: int = 5
    ) -> bool:
        """
        Determine if entity should be auto-enriched based on thresholds.

        Args:
            entity: Entity dictionary
            mentions: List of mention dictionaries
            min_sources: Minimum number of source files
            min_mentions: Minimum number of total mentions

        Returns:
            True if entity should be enriched
        """
        # Count unique source files
        unique_sources = len(set(m['file'] for m in mentions))

        # Check thresholds
        return unique_sources >= min_sources or len(mentions) >= min_mentions

    def enrich_auto(
        self,
        normalized_path: Path,
        source_dir: Path,
        min_sources: int = 3,
        min_mentions: int = 5,
        output_path: Optional[Path] = None,
        verbose: bool = False
    ) -> None:
        """
        Auto-enrich entities based on source material richness.

        Args:
            normalized_path: Path to normalized_entities.json
            source_dir: Directory containing source documents
            min_sources: Minimum number of sources to trigger enrichment
            min_mentions: Minimum number of mentions to trigger enrichment
            output_path: Output path (default: overwrite input)
            verbose: Print progress
        """
        if verbose:
            print(f"📖 Loading entities from: {normalized_path}")
            print(f"🎯 Auto-enrichment thresholds: {min_sources}+ sources OR {min_mentions}+ mentions")

        data = json.loads(normalized_path.read_text(encoding='utf-8'))

        # Find all source files
        source_files = []
        for pattern in ['*.md', '**/*.md']:
            source_files.extend(source_dir.glob(pattern))

        if verbose:
            print(f"📚 Found {len(source_files)} source documents")
            print()

        stats = {'enriched': 0, 'skipped_threshold': 0, 'skipped_existing': 0, 'not_found': 0}

        # Process concepts
        for concept in data.get('concepts', []):
            # Skip if already enriched
            if concept.get('enriched_content'):
                stats['skipped_existing'] += 1
                continue

            # Find mentions
            mentions = self.find_entity_mentions(concept['name'], source_files)

            if not mentions:
                stats['not_found'] += 1
                continue

            # Check if should enrich
            if not self.should_enrich(concept, mentions, min_sources, min_mentions):
                if verbose:
                    unique_sources = len(set(m['file'] for m in mentions))
                    print(f"  ⊘ Skipping {concept['name']}: {unique_sources} sources, {len(mentions)} mentions (below threshold)")
                stats['skipped_threshold'] += 1
                continue

            # Enrich
            self.enrich_concept(concept, mentions, verbose)
            stats['enriched'] += 1

        # TODO: Add thinkers, frameworks, institutions

        # Save
        if output_path is None:
            output_path = normalized_path

        output_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )

        # Summary
        print()
        print("=" * 60)
        print("📊 Auto-Enrichment Summary")
        print("=" * 60)
        print(f"  ✓ Enriched: {stats['enriched']}")
        print(f"  ⊘ Below threshold: {stats['skipped_threshold']}")
        print(f"  ✓ Already enriched: {stats['skipped_existing']}")
        print(f"  ⚠️  No mentions: {stats['not_found']}")
        print()
        print(f"✅ Saved to: {output_path}")
        print()
        print("Next step: run 'make kb-populate' to update entity pages")

    def enrich_selected_entities(
        self,
        normalized_path: Path,
        source_dir: Path,
        entity_names: List[str],
        output_path: Optional[Path] = None,
        verbose: bool = False
    ) -> None:
        """
        Enrich selected entities with comprehensive information.

        Args:
            normalized_path: Path to normalized_entities.json
            source_dir: Directory containing source documents
            entity_names: List of entity names to enrich
            output_path: Output path (default: overwrite input)
            verbose: Print progress
        """
        if verbose:
            print(f"📖 Loading entities from: {normalized_path}")

        data = json.loads(normalized_path.read_text(encoding='utf-8'))

        # Find all source files
        source_files = []
        for pattern in ['*.md', '**/*.md']:
            source_files.extend(source_dir.glob(pattern))

        if verbose:
            print(f"📚 Found {len(source_files)} source documents")
            print()

        stats = {'enriched': 0, 'skipped': 0, 'not_found': 0}

        # Process concepts
        for concept in data.get('concepts', []):
            if concept['name'] not in entity_names:
                stats['skipped'] += 1
                continue

            # Find mentions
            mentions = self.find_entity_mentions(concept['name'], source_files)

            if not mentions:
                print(f"  ⚠️  No mentions found for: {concept['name']}")
                stats['not_found'] += 1
                continue

            # Enrich
            self.enrich_concept(concept, mentions, verbose)
            stats['enriched'] += 1

        # TODO: Add thinkers, frameworks, institutions

        # Save
        if output_path is None:
            output_path = normalized_path

        output_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )

        # Summary
        print()
        print("=" * 60)
        print("📊 Enrichment Summary")
        print("=" * 60)
        print(f"  ✓ Enriched: {stats['enriched']}")
        print(f"  ⊘ Skipped: {stats['skipped']}")
        print(f"  ⚠️  No mentions: {stats['not_found']}")
        print()
        print(f"✅ Saved to: {output_path}")
        print()
        print("Next step: run 'make kb-populate' to update entity pages")


def main():
    parser = argparse.ArgumentParser(
        description="Deep enrichment of entity pages from source documents"
    )
    parser.add_argument(
        'normalized_entities',
        type=Path,
        help='Path to normalized_entities.json'
    )
    parser.add_argument(
        '--source-dir',
        type=Path,
        default=Path('knowledge_base'),
        help='Directory containing source documents (default: knowledge_base)'
    )

    # Mode selection
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        '--auto',
        action='store_true',
        help='Auto-enrich entities based on source material richness'
    )
    mode_group.add_argument(
        '--entities',
        nargs='+',
        help='Entity names to enrich (e.g., "Morphogenesis" "Cognitive Light Cone")'
    )

    # Auto-enrichment thresholds
    parser.add_argument(
        '--min-sources',
        type=int,
        default=3,
        help='Minimum number of source files for auto-enrichment (default: 3)'
    )
    parser.add_argument(
        '--min-mentions',
        type=int,
        default=5,
        help='Minimum number of mentions for auto-enrichment (default: 5)'
    )

    parser.add_argument(
        '--output',
        '-o',
        type=Path,
        help='Output path (default: overwrite input file)'
    )
    parser.add_argument(
        '--api-key',
        help='Anthropic API key (or set ANTHROPIC_API_KEY env var)'
    )
    parser.add_argument(
        '--model',
        default='claude-3-5-sonnet-20241022',
        help='Claude model (default: Sonnet for quality)'
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Verbose output'
    )

    args = parser.parse_args()

    # Check API key
    api_key = args.api_key or os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ Error: No API key provided.", file=sys.stderr)
        print("Set ANTHROPIC_API_KEY environment variable or use --api-key", file=sys.stderr)
        sys.exit(1)

    if not args.normalized_entities.exists():
        print(f"❌ Error: File not found: {args.normalized_entities}", file=sys.stderr)
        sys.exit(1)

    # Initialize enricher
    enricher = EntityEnricher(api_key=api_key, model=args.model)

    print("🔍 Deep Entity Enrichment")
    print(f"📁 Source: {args.normalized_entities}")
    print(f"📚 Sources: {args.source_dir}")

    if args.auto:
        print(f"🎯 Mode: Auto-enrich (≥{args.min_sources} sources OR ≥{args.min_mentions} mentions)")
    else:
        print(f"🎯 Entities: {', '.join(args.entities[:3])}{' ...' if len(args.entities) > 3 else ''}")
    print()

    # Enrich
    try:
        if args.auto:
            enricher.enrich_auto(
                args.normalized_entities,
                args.source_dir,
                min_sources=args.min_sources,
                min_mentions=args.min_mentions,
                output_path=args.output,
                verbose=args.verbose
            )
        else:
            enricher.enrich_selected_entities(
                args.normalized_entities,
                args.source_dir,
                args.entities,
                output_path=args.output,
                verbose=args.verbose
            )
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
