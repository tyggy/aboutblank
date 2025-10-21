#!/usr/bin/env python3
"""
Populate knowledge base with entity pages from normalized entities.

Creates new markdown files for entities that don't exist,
updates existing ones with new references.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List
from datetime import datetime


class EntityPopulator:
    """Create and update entity pages in knowledge base."""

    def __init__(self, knowledge_base_dir: Path, dry_run: bool = False, force: bool = False):
        """
        Initialize populator.

        Args:
            knowledge_base_dir: Root directory of knowledge base
            dry_run: If True, don't actually write files
            force: If True, overwrite existing files
        """
        self.kb_dir = knowledge_base_dir
        self.dry_run = dry_run
        self.force = force
        self.stats = {
            'created': 0,
            'updated': 0,
            'skipped': 0
        }

    def _ensure_filename(self, entity: Dict, entity_type: str) -> str:
        """
        Ensure entity has a filename, generating one from name if missing.

        Args:
            entity: Entity dict
            entity_type: Type of entity (for error messages)

        Returns:
            Filename (without .md extension)
        """
        if 'filename' in entity and entity['filename']:
            return entity['filename']

        # Generate filename from name
        name = entity.get('name', '')
        if not name:
            raise ValueError(f"Entity missing both 'filename' and 'name' fields: {entity}")

        # Simple slug generation: lowercase, spaces to hyphens, remove special chars
        filename = name.lower().replace(' ', '-')
        filename = re.sub(r'[^a-z0-9-]', '', filename)

        print(f"  ⚠️  Generated filename '{filename}' for {entity_type} '{name}' (missing filename field)", file=sys.stderr)
        return filename

    def populate_from_entities(self, entities_dir: Path, verbose: bool = False) -> None:
        """Populate knowledge base from individual entity JSON files."""
        if verbose:
            print(f"📖 Loading entities from: {entities_dir}")

        # Load all entity types
        data = {
            'thinkers': self._load_entity_type(entities_dir / 'thinkers', verbose),
            'concepts': self._load_entity_type(entities_dir / 'concepts', verbose),
            'frameworks': self._load_entity_type(entities_dir / 'frameworks', verbose),
            'institutions': self._load_entity_type(entities_dir / 'institutions', verbose),
            'questions': self._load_entity_type(entities_dir / 'questions', verbose)
        }

        # Process each entity type
        self._populate_thinkers(data.get('thinkers', []), verbose)
        self._populate_concepts(data.get('concepts', []), verbose)
        self._populate_frameworks(data.get('frameworks', []), verbose)
        self._populate_institutions(data.get('institutions', []), verbose)
        self._populate_questions(data.get('questions', []), verbose)

    def _load_entity_type(self, type_dir: Path, verbose: bool = False) -> List[Dict]:
        """Load all entities of a specific type from individual JSON files."""
        entities = []

        if not type_dir.exists():
            return entities

        for json_file in sorted(type_dir.glob('*.json')):
            try:
                entity = json.loads(json_file.read_text(encoding='utf-8'))
                entities.append(entity)
            except Exception as e:
                print(f"⚠️  Error loading {json_file}: {e}", file=sys.stderr)

        if verbose and entities:
            print(f"  📂 Loaded {len(entities)} from {type_dir.name}/")

        return entities

    def _populate_thinkers(self, thinkers: List[Dict], verbose: bool) -> None:
        """Create/update thinker pages."""
        if not thinkers:
            return

        if verbose:
            print()
            print(f"👤 Processing {len(thinkers)} thinkers...")

        thinkers_dir = self.kb_dir / 'thinkers'
        thinkers_dir.mkdir(parents=True, exist_ok=True)

        for thinker in thinkers:
            if not thinker.get('is_new', False) and not self.force:
                # Existing entity - could update references
                self.stats['skipped'] += 1
                if verbose:
                    print(f"  ⊘ Skipping existing: {thinker['name']}")
                continue

            filename = self._ensure_filename(thinker, 'thinker') + '.md'
            filepath = thinkers_dir / filename

            if filepath.exists() and not self.force:
                self.stats['skipped'] += 1
                if verbose:
                    print(f"  ⊘ Already exists: {filename}")
                continue

            # Create new thinker page
            content = self._create_thinker_page(thinker)

            if self.dry_run:
                if verbose:
                    print(f"  [DRY RUN] Would create: {filename}")
            else:
                filepath.write_text(content, encoding='utf-8')
                self.stats['created'] += 1
                if verbose:
                    print(f"  ✓ Created: {filename}")

    def _create_thinker_page(self, thinker: Dict) -> str:
        """Generate markdown content for thinker page."""
        today = datetime.now().strftime('%Y-%m-%d')

        # Format aliases
        aliases_str = json.dumps(thinker.get('aliases', []))

        # Format domains
        domains = thinker.get('domains', [])

        # Build sections conditionally
        sections = []

        # Overview - handle synthesized, aggregated, and single contexts
        synthesized = thinker.get('synthesized_overview')
        contexts = thinker.get('contexts')
        single_context = thinker.get('context', '')

        if synthesized:
            # Use synthesized overview (best option)
            sections.append(f"""## Overview

{synthesized}""")

        elif contexts and len(contexts) > 1:
            # Multiple contexts - show as clean paragraphs
            overview_parts = []
            for ctx in contexts:
                overview_parts.append(f"{ctx['text']}")

            sections.append(f"""## Overview

{chr(10).join(overview_parts)}""")
        elif contexts and len(contexts) == 1:
            # Single context in new format
            sections.append(f"""## Overview

{contexts[0]['text']}""")
        elif single_context:
            # Old format: single context string
            sections.append(f"""## Overview

{single_context}""")

        # Primary Domains (if we have any)
        if domains:
            domains_md = '\n'.join(f"- [[{d}]]" for d in domains)
            sections.append(f"""## Primary Domains

{domains_md}""")

        # Join sections
        content_sections = '\n\n'.join(sections) if sections else ''

        # Add note for non-enriched pages only
        if content_sections and not thinker.get('enriched_content'):
            content_sections += '\n\n' + """## Notes

*Extracted from source material (transcripts and papers). Consider enriching with affiliated institutions, key works, and biographical details.*"""

        return f"""---
type: thinker
aliases: {aliases_str}
domains: {json.dumps(domains)}
institutions: []
tags: []
created: {today}
updated: {today}
---

# {thinker['name']}

{content_sections}
"""

    def _populate_concepts(self, concepts: List[Dict], verbose: bool) -> None:
        """Create/update concept pages."""
        if not concepts:
            return

        if verbose:
            print()
            print(f"💡 Processing {len(concepts)} concepts...")

        for concept in concepts:
            if not concept.get('is_new', False) and not self.force:
                self.stats['skipped'] += 1
                if verbose:
                    print(f"  ⊘ Skipping existing: {concept['name']}")
                continue

            # Determine category subdirectory
            category = concept.get('category', 'interdisciplinary')
            concepts_dir = self.kb_dir / 'concepts' / category
            concepts_dir.mkdir(parents=True, exist_ok=True)

            filename = self._ensure_filename(concept, 'concept') + '.md'
            filepath = concepts_dir / filename

            if filepath.exists():
                self.stats['skipped'] += 1
                if verbose:
                    print(f"  ⊘ Already exists: {category}/{filename}")
                continue

            # Create new concept page
            content = self._create_concept_page(concept)

            if self.dry_run:
                if verbose:
                    print(f"  [DRY RUN] Would create: {category}/{filename}")
            else:
                filepath.write_text(content, encoding='utf-8')
                self.stats['created'] += 1
                if verbose:
                    print(f"  ✓ Created: {category}/{filename}")

    def _create_concept_page(self, concept: Dict) -> str:
        """Generate markdown content for concept page."""
        today = datetime.now().strftime('%Y-%m-%d')
        aliases_str = json.dumps(concept.get('aliases', []))
        category = concept.get('category', 'interdisciplinary')

        # Build sections conditionally
        sections = []

        # Check for deep enrichment first
        enriched = concept.get('enriched_content')

        if enriched:
            # Use comprehensive enriched content
            sections.append(enriched)

        else:
            # Use standard extraction
            # Definition - handle synthesized, aggregated, and single contexts
            synthesized = concept.get('synthesized_overview')
            contexts = concept.get('contexts')
            single_context = concept.get('context', '')

            if synthesized:
                # Use synthesized definition (best option)
                sections.append(f"""## Definition

{synthesized}""")

            elif contexts and len(contexts) > 1:
                # Multiple contexts - show as clean paragraphs
                definition_parts = []
                for ctx in contexts:
                    definition_parts.append(f"{ctx['text']}")

                sections.append(f"""## Definition

{chr(10).join(definition_parts)}""")
            elif contexts and len(contexts) == 1:
                # Single context in new format
                sections.append(f"""## Definition

{contexts[0]['text']}""")
            elif single_context:
                # Old format: single context string
                sections.append(f"""## Definition

{single_context}""")

            # Category - always include (only for non-enriched)
            sections.append(f"""## Category

- Primary: [[{category.title()}]]""")

        # Aliases (if any beyond what's in frontmatter)
        aliases = concept.get('aliases', [])
        if aliases:
            alias_list = ', '.join(f'"{a}"' for a in aliases)
            sections.append(f"""## Alternative Names

Also known as: {alias_list}""")

        # Join sections
        content_sections = '\n\n'.join(sections)

        # Add note for non-enriched pages only
        if not enriched:
            content_sections += '\n\n' + """## Notes

*Extracted from source material. Run `make kb-enrich-auto` to enrich this and other concepts with comprehensive details from Claude's broader knowledge.*"""

        return f"""---
type: concept
aliases: {aliases_str}
category: {category}
tags: []
created: {today}
updated: {today}
---

# {concept['name']}

{content_sections}
"""

    def _populate_frameworks(self, frameworks: List[Dict], verbose: bool) -> None:
        """Create/update framework pages."""
        if not frameworks:
            return

        if verbose:
            print()
            print(f"🔧 Processing {len(frameworks)} frameworks...")

        frameworks_dir = self.kb_dir / 'frameworks'
        frameworks_dir.mkdir(parents=True, exist_ok=True)

        for framework in frameworks:
            if not framework.get('is_new', False) and not self.force:
                self.stats['skipped'] += 1
                if verbose:
                    print(f"  ⊘ Skipping existing: {framework['name']}")
                continue

            filename = self._ensure_filename(framework, 'framework') + '.md'
            filepath = frameworks_dir / filename

            if filepath.exists() and not self.force:
                self.stats['skipped'] += 1
                if verbose:
                    print(f"  ⊘ Already exists: {filename}")
                continue

            content = self._create_framework_page(framework)

            if self.dry_run:
                if verbose:
                    print(f"  [DRY RUN] Would create: {filename}")
            else:
                filepath.write_text(content, encoding='utf-8')
                self.stats['created'] += 1
                if verbose:
                    print(f"  ✓ Created: {filename}")

    def _create_framework_page(self, framework: Dict) -> str:
        """Generate markdown content for framework page."""
        today = datetime.now().strftime('%Y-%m-%d')
        creator = framework.get('creator')

        # Build sections conditionally
        sections = []

        # Overview - handle synthesized, aggregated, and single contexts
        synthesized = framework.get('synthesized_overview')
        contexts = framework.get('contexts')
        single_context = framework.get('context', '')

        if synthesized:
            # Use synthesized overview (best option)
            sections.append(f"""## Overview

{synthesized}""")

        elif contexts and len(contexts) > 1:
            # Multiple contexts - show as clean paragraphs
            overview_parts = []
            for ctx in contexts:
                overview_parts.append(f"{ctx['text']}")

            sections.append(f"""## Overview

{chr(10).join(overview_parts)}""")
        elif contexts and len(contexts) == 1:
            # Single context in new format
            sections.append(f"""## Overview

{contexts[0]['text']}""")
        elif single_context:
            # Old format: single context string
            sections.append(f"""## Overview

{single_context}""")

        # Creator (if we have one)
        if creator:
            # Handle creator as either string or list
            if isinstance(creator, list):
                creators = creator
            else:
                # Parse multiple creators if comma-separated string
                creators = [c.strip() for c in creator.split(',')]

            creator_links = '\n'.join(f"- [[{c}]]" for c in creators)
            sections.append(f"""## Creator/Originator

{creator_links}""")

        # Join sections with blank lines
        content_sections = '\n\n'.join(sections) if sections else ''

        # Add note for non-enriched pages only
        if content_sections and not framework.get('enriched_content'):
            content_sections += '\n\n' + """## Notes

*Extracted from source material. Expand with theoretical foundations, key principles, and applications as needed.*"""

        # Build frontmatter - ensure creator_list is always a list
        if not creator:
            creator_list = []
        elif isinstance(creator, list):
            creator_list = creator
        else:
            creator_list = [c.strip() for c in creator.split(',')]

        return f"""---
type: framework
aliases: []
creator: {json.dumps(creator_list)}
tags: []
created: {today}
updated: {today}
---

# {framework['name']}

{content_sections}
"""

    def _populate_institutions(self, institutions: List[Dict], verbose: bool) -> None:
        """Create/update institution pages."""
        if not institutions:
            return

        if verbose:
            print()
            print(f"🏛️  Processing {len(institutions)} institutions...")

        institutions_dir = self.kb_dir / 'institutions'
        institutions_dir.mkdir(parents=True, exist_ok=True)

        for institution in institutions:
            if not institution.get('is_new', False) and not self.force:
                self.stats['skipped'] += 1
                if verbose:
                    print(f"  ⊘ Skipping existing: {institution['name']}")
                continue

            filename = self._ensure_filename(institution, 'institution') + '.md'
            filepath = institutions_dir / filename

            if filepath.exists() and not self.force:
                self.stats['skipped'] += 1
                if verbose:
                    print(f"  ⊘ Already exists: {filename}")
                continue

            content = self._create_institution_page(institution)

            if self.dry_run:
                if verbose:
                    print(f"  [DRY RUN] Would create: {filename}")
            else:
                filepath.write_text(content, encoding='utf-8')
                self.stats['created'] += 1
                if verbose:
                    print(f"  ✓ Created: {filename}")

    def _create_institution_page(self, institution: Dict) -> str:
        """Generate markdown content for institution page."""
        today = datetime.now().strftime('%Y-%m-%d')
        inst_type = institution.get('type', 'organization')

        # Build sections conditionally
        sections = []

        # Type - always include
        sections.append(f"""## Type

{inst_type.replace('-', ' ').title()}""")

        # Overview - handle synthesized, aggregated, and single contexts
        synthesized = institution.get('synthesized_overview')
        contexts = institution.get('contexts')
        single_context = institution.get('context', '')

        if synthesized:
            # Use synthesized overview (best option)
            sections.append(f"""## Overview

{synthesized}""")

        elif contexts and len(contexts) > 1:
            # Multiple contexts - show as clean paragraphs
            overview_parts = []
            for ctx in contexts:
                overview_parts.append(f"{ctx['text']}")

            sections.append(f"""## Overview

{chr(10).join(overview_parts)}""")
        elif contexts and len(contexts) == 1:
            # Single context in new format
            sections.append(f"""## Overview

{contexts[0]['text']}""")
        elif single_context:
            # Old format: single context string
            sections.append(f"""## Overview

{single_context}""")

        # Join sections
        content_sections = '\n\n'.join(sections)

        # Add note for non-enriched pages only
        if not institution.get('enriched_content'):
            content_sections += '\n\n' + """## Notes

*Extracted from source material. Expand with key people, research focus areas, and related work as needed.*"""

        return f"""---
type: institution
institution_type: {inst_type}
tags: []
created: {today}
updated: {today}
---

# {institution['name']}

{content_sections}
"""

    def _populate_questions(self, questions: List[Dict], verbose: bool) -> None:
        """Create/update question pages."""
        if not questions:
            return

        if verbose:
            print()
            print(f"❓ Processing {len(questions)} questions...")

        questions_dir = self.kb_dir / 'questions'
        questions_dir.mkdir(parents=True, exist_ok=True)

        for question in questions:
            filename = self._ensure_filename(question, 'question') + '.md'
            filepath = questions_dir / filename

            if filepath.exists() and not self.force:
                self.stats['skipped'] += 1
                if verbose:
                    print(f"  ⊘ Already exists: {filename}")
                continue

            content = self._create_question_page(question)

            if self.dry_run:
                if verbose:
                    print(f"  [DRY RUN] Would create: {filename}")
            else:
                filepath.write_text(content, encoding='utf-8')
                self.stats['created'] += 1
                if verbose:
                    print(f"  ✓ Created: {filename}")

    def _create_question_page(self, question: Dict) -> str:
        """Generate markdown content for question page."""
        today = datetime.now().strftime('%Y-%m-%d')
        category = question.get('category', 'other')
        context = question.get('context', '')

        # Build sections conditionally
        sections = []

        # Category - always include
        sections.append(f"""## Category

- [[{category.title()}]]""")

        # Status - always include
        sections.append("""## Status

Open""")

        # Description (if we have context)
        if context:
            sections.append(f"""## Description

{context}""")

        # Join sections
        content_sections = '\n\n'.join(sections)

        # Add note for non-enriched pages only
        if not question.get('enriched_content'):
            content_sections += '\n\n' + """## Notes

*Extracted from source material. Expand with relevant thinkers, concepts, approaches, and related questions as needed.*"""

        return f"""---
type: question
category: {category}
status: open
tags: []
created: {today}
updated: {today}
---

# {question['question']}

{content_sections}
"""

    def print_summary(self) -> None:
        """Print summary of population results."""
        print()
        print("=" * 50)
        print("📊 Summary")
        print("=" * 50)
        print(f"  ✓ Created: {self.stats['created']} files")
        print(f"  ⊘ Skipped: {self.stats['skipped']} files (already exist or existing entities)")
        print(f"  📁 Total: {self.stats['created'] + self.stats['skipped']} entities processed")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Populate knowledge base with entity pages"
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
        help="Don't actually write files, just show what would be done"
    )
    parser.add_argument(
        '--force',
        '-f',
        action='store_true',
        help='Force overwrite of existing files'
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Verbose output'
    )

    args = parser.parse_args()

    entities_dir = args.knowledge_base / 'entities'
    if not entities_dir.exists():
        print(f"❌ Error: Entities directory not found: {entities_dir}", file=sys.stderr)
        print(f"   Run 'make kb-normalize' first to create entity files.", file=sys.stderr)
        sys.exit(1)

    # Initialize populator
    populator = EntityPopulator(args.knowledge_base, dry_run=args.dry_run, force=args.force)

    print("🏗️  Populating Knowledge Base")
    print(f"📁 Knowledge base: {args.knowledge_base}")
    print(f"📖 Source: {entities_dir}")
    if args.dry_run:
        print("🔍 DRY RUN MODE - No files will be modified")
    if args.force:
        print("⚡ FORCE MODE - Will overwrite existing files")
    print()

    # Populate
    populator.populate_from_entities(entities_dir, verbose=args.verbose)

    # Print summary
    populator.print_summary()

    if not args.dry_run:
        print("✅ Knowledge base population complete!")
        print()
        print("Next steps:")
        print("  1. Review created files in knowledge_base/")
        print("  2. Inject wiki links: python tools/inject_links.py")
        print("  3. Open in Obsidian to see the knowledge graph!")


if __name__ == '__main__':
    main()
