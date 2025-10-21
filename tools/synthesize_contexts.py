#!/usr/bin/env python3
"""
Synthesize unified entity descriptions from multiple source contexts.

When entities appear in multiple papers/talks with different contexts,
this tool uses Claude to create comprehensive synthesized overviews.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
from anthropic import Anthropic


class ContextSynthesizer:
    """Synthesize unified descriptions from multiple contexts."""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-haiku-4-5-20251001"):
        """Initialize synthesizer with API key and model."""
        self.client = Anthropic(api_key=api_key or os.environ.get('ANTHROPIC_API_KEY'))
        self.model = model
        self.max_tokens = 2048  # Enough for comprehensive synthesis

    def synthesize_contexts(self, contexts: List[Dict], entity_name: str, entity_type: str) -> str:
        """
        Synthesize multiple contexts into one comprehensive description.

        Args:
            contexts: List of {"source": path, "text": context} dicts
            entity_name: Name of the entity
            entity_type: Type (thinker, concept, framework, institution)

        Returns:
            Synthesized description
        """
        if not contexts:
            return ""

        if len(contexts) == 1:
            # Single context, no synthesis needed
            return contexts[0]['text']

        # Build synthesis prompt
        contexts_text = ""
        for i, ctx in enumerate(contexts, 1):
            source_name = Path(ctx['source']).stem if ctx['source'] else f"Source {i}"
            contexts_text += f"\n{i}. From {source_name}:\n{ctx['text']}\n"

        prompt = f"""You are synthesizing information about "{entity_name}", a {entity_type} in a knowledge base about Buddhism, AI, and consciousness.

Multiple sources provide different perspectives:
{contexts_text}

Task: Create a single, comprehensive description that:
- Integrates insights from all sources
- Highlights complementary information
- Resolves any contradictions or differences in emphasis
- Maintains accuracy to the source material
- Is concise but complete (2-4 sentences)
- Uses clear, accessible language

Return ONLY the synthesized description, no preamble or explanation."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            return response.content[0].text.strip()

        except Exception as e:
            print(f"⚠️  Error synthesizing contexts for {entity_name}: {e}", file=sys.stderr)
            # Fallback: concatenate contexts
            return " ".join(ctx['text'] for ctx in contexts)

    def synthesize_entity_file(self, entity: Dict, entity_type: str, verbose: bool = False) -> Dict:
        """
        Add synthesized overview to entity with multiple contexts.

        Args:
            entity: Entity dictionary
            entity_type: Type of entity
            verbose: Print progress

        Returns:
            Updated entity dictionary
        """
        contexts = entity.get('contexts')
        if not contexts or len(contexts) <= 1:
            # No synthesis needed
            return entity

        if verbose:
            source_names = [Path(c['source']).stem for c in contexts if c['source']]
            print(f"  🔄 Synthesizing {len(contexts)} contexts from: {', '.join(source_names[:3])}{' ...' if len(source_names) > 3 else ''}")

        # Synthesize
        synthesized = self.synthesize_contexts(contexts, entity['name'], entity_type)

        # Add to entity
        entity['synthesized_overview'] = synthesized

        if verbose:
            print(f"  ✓ Created {len(synthesized)} char synthesis")

        return entity

    def process_normalized_file(self, normalized_path: Path, output_path: Optional[Path] = None, verbose: bool = False) -> None:
        """
        Process normalized entities file, adding synthesized overviews.

        Args:
            normalized_path: Path to normalized_entities.json
            output_path: Output path (default: overwrite input)
            verbose: Print progress
        """
        if verbose:
            print(f"📖 Loading: {normalized_path}")

        data = json.loads(normalized_path.read_text(encoding='utf-8'))

        stats = {
            'thinkers': 0,
            'concepts': 0,
            'frameworks': 0,
            'institutions': 0
        }

        # Process each entity type
        for entity_type in ['thinkers', 'concepts', 'frameworks', 'institutions']:
            entities = data.get(entity_type, [])

            if verbose and entities:
                print(f"\n{entity_type.title()}:")

            for entity in entities:
                if entity.get('contexts') and len(entity['contexts']) > 1:
                    self.synthesize_entity_file(entity, entity_type.rstrip('s'), verbose)
                    stats[entity_type] += 1

        # Save output
        if output_path is None:
            output_path = normalized_path

        output_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )

        # Print summary
        print()
        print("=" * 60)
        print("📊 Synthesis Summary")
        print("=" * 60)
        for entity_type, count in stats.items():
            if count > 0:
                print(f"  {entity_type.title()}: {count} synthesized")
        print()
        print(f"✅ Saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Synthesize unified entity descriptions from multiple contexts"
    )
    parser.add_argument(
        'normalized_entities',
        type=Path,
        help='Path to normalized_entities.json'
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
        default='claude-haiku-4-5-20251001',
        help='Claude model to use (default: claude-haiku-4-5-20251001)'
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

    # Initialize synthesizer
    synthesizer = ContextSynthesizer(api_key=api_key, model=args.model)

    print("🔄 Synthesizing Entity Contexts")
    print(f"📁 Source: {args.normalized_entities}")
    print()

    # Process file
    try:
        synthesizer.process_normalized_file(
            args.normalized_entities,
            output_path=args.output,
            verbose=args.verbose
        )
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
