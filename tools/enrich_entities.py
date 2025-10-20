#!/usr/bin/env python3
"""
Cross-enrich entity pages with bidirectional links.

Updates entity pages to reference each other based on the normalized entities database.
For example:
- Adds frameworks to creator's thinker page
- Adds concepts to framework pages
- Adds thinkers to concept pages
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict


class EntityCrossEnricher:
    """Cross-enrich entity pages with bidirectional references."""

    def __init__(self, knowledge_base_dir: Path, dry_run: bool = False):
        """
        Initialize enricher.

        Args:
            knowledge_base_dir: Root directory of knowledge base
            dry_run: If True, don't actually write files
        """
        self.kb_dir = knowledge_base_dir
        self.dry_run = dry_run
        self.stats = defaultdict(int)

    def enrich_from_normalized(self, normalized_path: Path, verbose: bool = False) -> None:
        """Enrich entity pages based on normalized entities."""
        if verbose:
            print(f"📖 Loading normalized entities from: {normalized_path}")

        data = json.loads(normalized_path.read_text(encoding='utf-8'))

        # Build relationship maps
        relationships = self._build_relationship_maps(data, verbose)

        # Enrich each entity type
        self._enrich_thinkers(relationships, verbose)
        self._enrich_concepts(relationships, verbose)
        self._enrich_frameworks(relationships, verbose)
        self._enrich_institutions(relationships, verbose)

    def _build_relationship_maps(self, data: Dict, verbose: bool) -> Dict:
        """Build maps of relationships between entities."""
        if verbose:
            print("🔗 Building relationship maps...")

        relationships = {
            'thinker_to_frameworks': defaultdict(list),
            'thinker_to_concepts': defaultdict(set),
            'framework_to_thinkers': defaultdict(list),
            'framework_to_concepts': defaultdict(set),
            'concept_to_thinkers': defaultdict(set),
            'concept_to_frameworks': defaultdict(set),
            'institution_to_thinkers': defaultdict(set),
        }

        # Map frameworks to their creators
        for framework in data.get('frameworks', []):
            name = framework['name']
            creators = framework.get('creator')

            # Handle None, string, or list
            if creators is None:
                creators = []
            elif isinstance(creators, str):
                creators = [c.strip() for c in creators.split(',')]
            elif not isinstance(creators, list):
                creators = [creators]

            for creator in creators:
                if creator:
                    relationships['thinker_to_frameworks'][creator].append(name)
                    relationships['framework_to_thinkers'][name].append(creator)

        # Map concepts mentioned in framework contexts
        for framework in data.get('frameworks', []):
            fname = framework['name']
            context = framework.get('context', '').lower()

            # Find concept mentions in framework context
            for concept in data.get('concepts', []):
                cname = concept['name']
                # Simple check: if concept name appears in framework context
                if cname.lower() in context:
                    relationships['framework_to_concepts'][fname].add(cname)
                    relationships['concept_to_frameworks'][cname].add(fname)

        # Map thinkers to concepts based on domains
        for thinker in data.get('thinkers', []):
            tname = thinker['name']
            domains = thinker.get('domains', [])
            context = thinker.get('context', '').lower()

            # Find concept mentions
            for concept in data.get('concepts', []):
                cname = concept['name']
                ccategory = concept.get('category', '')

                # Link if domain matches concept category or name appears in context
                if ccategory in [d.lower() for d in domains] or cname.lower() in context:
                    relationships['thinker_to_concepts'][tname].add(cname)
                    relationships['concept_to_thinkers'][cname].add(tname)

        if verbose:
            print(f"  ✓ Found {sum(len(v) for v in relationships['thinker_to_frameworks'].values())} framework→creator links")
            print(f"  ✓ Found {sum(len(v) for v in relationships['thinker_to_concepts'].values())} thinker→concept links")
            print()

        return relationships

    def _enrich_thinkers(self, relationships: Dict, verbose: bool) -> None:
        """Enrich thinker pages with frameworks they created and concepts they discuss."""
        if verbose:
            print("👤 Enriching thinker pages...")

        thinkers_dir = self.kb_dir / 'thinkers'
        if not thinkers_dir.exists():
            return

        for thinker_file in thinkers_dir.glob('*.md'):
            # Skip templates
            if '_templates' in str(thinker_file):
                continue

            content = thinker_file.read_text(encoding='utf-8')

            # Extract thinker name from title
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            if not title_match:
                continue

            thinker_name = title_match.group(1).strip()

            # Get related entities
            frameworks = relationships['thinker_to_frameworks'].get(thinker_name, [])
            concepts = relationships['thinker_to_concepts'].get(thinker_name, set())

            if not frameworks and not concepts:
                continue

            # Build enrichment sections
            enrichments = []

            if frameworks:
                framework_links = '\n'.join(f"- [[{f}]]" for f in frameworks)
                enrichments.append(f"""## Frameworks

Frameworks this thinker created or contributed to:

{framework_links}""")

            if concepts:
                concept_links = '\n'.join(f"- [[{c}]]" for c in sorted(concepts))
                enrichments.append(f"""## Key Concepts

Concepts this thinker frequently discusses:

{concept_links}""")

            # Insert enrichments before the Notes section
            if enrichments:
                enrichment_text = '\n\n'.join(enrichments)

                # Find Notes section
                notes_pattern = r'(##\s+Notes\s*\n)'
                if re.search(notes_pattern, content):
                    new_content = re.sub(
                        notes_pattern,
                        f'{enrichment_text}\n\n\\1',
                        content
                    )
                else:
                    # Add before end
                    new_content = content.rstrip() + '\n\n' + enrichment_text + '\n'

                if new_content != content:
                    if self.dry_run:
                        if verbose:
                            print(f"  [DRY RUN] Would enrich: {thinker_file.name}")
                    else:
                        thinker_file.write_text(new_content, encoding='utf-8')
                        self.stats['thinkers_enriched'] += 1
                        if verbose:
                            print(f"  ✓ Enriched: {thinker_file.name} ({len(frameworks)} frameworks, {len(concepts)} concepts)")

    def _enrich_concepts(self, relationships: Dict, verbose: bool) -> None:
        """Enrich concept pages with related thinkers and frameworks."""
        if verbose:
            print()
            print("💡 Enriching concept pages...")

        concepts_dir = self.kb_dir / 'concepts'
        if not concepts_dir.exists():
            return

        for concept_file in concepts_dir.rglob('*.md'):
            # Skip templates
            if '_templates' in str(concept_file):
                continue

            content = concept_file.read_text(encoding='utf-8')

            # Extract concept name
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            if not title_match:
                continue

            concept_name = title_match.group(1).strip()

            # Get related entities
            thinkers = relationships['concept_to_thinkers'].get(concept_name, set())
            frameworks = relationships['concept_to_frameworks'].get(concept_name, set())

            if not thinkers and not frameworks:
                continue

            # Build enrichment sections
            enrichments = []

            if thinkers:
                thinker_links = '\n'.join(f"- [[{t}]]" for t in sorted(thinkers))
                enrichments.append(f"""## Key Thinkers

Thinkers who discuss or developed this concept:

{thinker_links}""")

            if frameworks:
                framework_links = '\n'.join(f"- [[{f}]]" for f in sorted(frameworks))
                enrichments.append(f"""## Related Frameworks

Frameworks that use this concept:

{framework_links}""")

            # Insert enrichments
            if enrichments:
                enrichment_text = '\n\n'.join(enrichments)

                notes_pattern = r'(##\s+Notes\s*\n)'
                if re.search(notes_pattern, content):
                    new_content = re.sub(notes_pattern, f'{enrichment_text}\n\n\\1', content)
                else:
                    new_content = content.rstrip() + '\n\n' + enrichment_text + '\n'

                if new_content != content:
                    if self.dry_run:
                        if verbose:
                            print(f"  [DRY RUN] Would enrich: {concept_file.name}")
                    else:
                        concept_file.write_text(new_content, encoding='utf-8')
                        self.stats['concepts_enriched'] += 1
                        if verbose:
                            print(f"  ✓ Enriched: {concept_file.name} ({len(thinkers)} thinkers, {len(frameworks)} frameworks)")

    def _enrich_frameworks(self, relationships: Dict, verbose: bool) -> None:
        """Enrich framework pages with related concepts."""
        if verbose:
            print()
            print("🔧 Enriching framework pages...")

        frameworks_dir = self.kb_dir / 'frameworks'
        if not frameworks_dir.exists():
            return

        for framework_file in frameworks_dir.glob('*.md'):
            if '_templates' in str(framework_file):
                continue

            content = framework_file.read_text(encoding='utf-8')

            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            if not title_match:
                continue

            framework_name = title_match.group(1).strip()

            # Get related concepts
            concepts = relationships['framework_to_concepts'].get(framework_name, set())

            if not concepts:
                continue

            # Build enrichment
            concept_links = '\n'.join(f"- [[{c}]]" for c in sorted(concepts))
            enrichment = f"""## Key Concepts

Concepts central to this framework:

{concept_links}"""

            # Insert enrichment
            notes_pattern = r'(##\s+Notes\s*\n)'
            if re.search(notes_pattern, content):
                new_content = re.sub(notes_pattern, f'{enrichment}\n\n\\1', content)
            else:
                new_content = content.rstrip() + '\n\n' + enrichment + '\n'

            if new_content != content:
                if self.dry_run:
                    if verbose:
                        print(f"  [DRY RUN] Would enrich: {framework_file.name}")
                else:
                    framework_file.write_text(new_content, encoding='utf-8')
                    self.stats['frameworks_enriched'] += 1
                    if verbose:
                        print(f"  ✓ Enriched: {framework_file.name} ({len(concepts)} concepts)")

    def _enrich_institutions(self, relationships: Dict, verbose: bool) -> None:
        """Enrich institution pages with key people."""
        if verbose:
            print()
            print("🏛️  Enriching institution pages...")

        # This would need more data to implement properly
        # Placeholder for now

    def print_summary(self) -> None:
        """Print summary of enrichment."""
        print()
        print("=" * 50)
        print("📊 Summary")
        print("=" * 50)
        print(f"  ✓ Thinkers enriched: {self.stats['thinkers_enriched']}")
        print(f"  ✓ Concepts enriched: {self.stats['concepts_enriched']}")
        print(f"  ✓ Frameworks enriched: {self.stats['frameworks_enriched']}")
        print(f"  ✓ Total: {sum(self.stats.values())} pages enriched")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Cross-enrich entity pages with bidirectional links"
    )
    parser.add_argument(
        'normalized_entities',
        type=Path,
        help='Normalized entities JSON file'
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
        help="Don't actually write files"
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Verbose output'
    )

    args = parser.parse_args()

    if not args.normalized_entities.exists():
        print(f"❌ Error: File not found: {args.normalized_entities}", file=sys.stderr)
        sys.exit(1)

    # Initialize enricher
    enricher = EntityCrossEnricher(args.knowledge_base, dry_run=args.dry_run)

    print("🔗 Cross-Enriching Entity Pages")
    print(f"📁 Knowledge base: {args.knowledge_base}")
    print(f"📖 Source: {args.normalized_entities}")
    if args.dry_run:
        print("🔍 DRY RUN MODE")
    print()

    # Enrich
    enricher.enrich_from_normalized(args.normalized_entities, verbose=args.verbose)

    # Print summary
    enricher.print_summary()

    if not args.dry_run:
        print("✅ Cross-enrichment complete!")
        print()
        print("Pages now have bidirectional links:")
        print("  - Thinkers link to their frameworks and concepts")
        print("  - Concepts link to thinkers and frameworks")
        print("  - Frameworks link to concepts and creators")


if __name__ == '__main__':
    main()
