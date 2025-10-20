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

    def __init__(self, knowledge_base_dir: Path, dry_run: bool = False):
        """
        Initialize populator.

        Args:
            knowledge_base_dir: Root directory of knowledge base
            dry_run: If True, don't actually write files
        """
        self.kb_dir = knowledge_base_dir
        self.dry_run = dry_run
        self.stats = {
            'created': 0,
            'updated': 0,
            'skipped': 0
        }

    def populate_from_normalized(self, normalized_path: Path, verbose: bool = False) -> None:
        """Populate knowledge base from normalized entities JSON."""
        if verbose:
            print(f"📖 Loading normalized entities from: {normalized_path}")

        data = json.loads(normalized_path.read_text(encoding='utf-8'))

        # Process each entity type
        self._populate_thinkers(data.get('thinkers', []), verbose)
        self._populate_concepts(data.get('concepts', []), verbose)
        self._populate_frameworks(data.get('frameworks', []), verbose)
        self._populate_institutions(data.get('institutions', []), verbose)
        self._populate_questions(data.get('questions', []), verbose)

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
            if not thinker.get('is_new', False):
                # Existing entity - could update references
                self.stats['skipped'] += 1
                if verbose:
                    print(f"  ⊘ Skipping existing: {thinker['name']}")
                continue

            filename = thinker['filename'] + '.md'
            filepath = thinkers_dir / filename

            if filepath.exists():
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

        # Format domains as list
        domains = thinker.get('domains', [])
        domains_md = '\n'.join(f"- [[{d}]]" for d in domains) if domains else "- (To be categorized)"

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

## Overview

{thinker.get('context', '(Context to be added)')}

## Primary Domains

{domains_md}

## Affiliated Institutions

- (To be added)

## Key Concepts

Concepts this thinker frequently discusses or developed:

- (To be added from transcript analysis)

## Notable Works

### Books

- (To be added)

### Papers

- (To be added)

### Talks & Interviews

- (To be added)

## Related Thinkers

Collaborators, influences, or related researchers:

- (To be added)

## Quotes & Insights

(Notable quotes to be added)

## Questions They Address

- (To be added)

## References

Links to sources where this thinker appears in our knowledge base.

**Mentioned in:**
- (Transcripts to be linked)
"""

    def _populate_concepts(self, concepts: List[Dict], verbose: bool) -> None:
        """Create/update concept pages."""
        if not concepts:
            return

        if verbose:
            print()
            print(f"💡 Processing {len(concepts)} concepts...")

        for concept in concepts:
            if not concept.get('is_new', False):
                self.stats['skipped'] += 1
                if verbose:
                    print(f"  ⊘ Skipping existing: {concept['name']}")
                continue

            # Determine category subdirectory
            category = concept.get('category', 'interdisciplinary')
            concepts_dir = self.kb_dir / 'concepts' / category
            concepts_dir.mkdir(parents=True, exist_ok=True)

            filename = concept['filename'] + '.md'
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

        return f"""---
type: concept
aliases: {aliases_str}
category: {category}
tags: []
created: {today}
updated: {today}
---

# {concept['name']}

## Definition

{concept.get('context', '(Definition to be refined)')}

## Category

- Primary: [[{category.title()}]]

## Key Characteristics

- (To be added from analysis)

## Key Thinkers

Who discusses or developed this concept:

- (To be linked)

## Related Concepts

How this concept connects to others:

- (To be added)

## Related Frameworks

- (To be added)

## Applications

How this concept is applied or manifests:

1. (To be added)

## Questions & Debates

- (To be added)

## Examples

Concrete examples illustrating the concept.

## Sources

Where this concept appears in our knowledge base:

**Discussed in:**
- (Transcripts to be linked)

## Notes

(Additional observations, connections, or insights)
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
            if not framework.get('is_new', False):
                self.stats['skipped'] += 1
                if verbose:
                    print(f"  ⊘ Skipping existing: {framework['name']}")
                continue

            filename = framework['filename'] + '.md'
            filepath = frameworks_dir / filename

            if filepath.exists():
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
        creator_md = f"- [[{creator}]]" if creator else "- (Creator to be determined)"

        return f"""---
type: framework
aliases: []
creator: {json.dumps([creator] if creator else [])}
tags: []
created: {today}
updated: {today}
---

# {framework['name']}

## Overview

{framework.get('context', '(Description to be expanded)')}

## Creator/Originator

{creator_md}

## Description

(Detailed explanation to be added)

## Components

Key elements that make up this framework:

1. **Component 1**
   - (Description)

2. **Component 2**
   - (Description)

## Key Concepts

Concepts central to this framework:

- (To be added)

## Applications

How this framework is used:

- (To be added)

## Related Frameworks

- (To be added)

## Strengths

(What this framework does well)

## Limitations

(Known limitations or criticisms)

## Sources

Where this framework is discussed:

**Detailed in:**
- (Transcripts to be linked)

## Examples

(Concrete examples of the framework in action)
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
            if not institution.get('is_new', False):
                self.stats['skipped'] += 1
                if verbose:
                    print(f"  ⊘ Skipping existing: {institution['name']}")
                continue

            filename = institution['filename'] + '.md'
            filepath = institutions_dir / filename

            if filepath.exists():
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

        return f"""---
type: institution
institution_type: {inst_type}
tags: []
created: {today}
updated: {today}
---

# {institution['name']}

## Type

{inst_type.replace('-', ' ').title()}

## Overview

{institution.get('context', '(Overview to be expanded)')}

## Key People

- (To be added)

## Focus Areas

Main areas of research or practice:

- (To be added)

## Related Concepts

- (To be added)

## Related Work

Projects, publications, or initiatives:

- (To be added)

## Collaborations

Other institutions or people they work with:

- (To be added)

## Sources

Where this institution is mentioned:

**Mentioned in:**
- (Transcripts to be linked)

## Links

- Website: (To be added)
- Location: (To be added)

## Notes

(Additional information)
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
            filename = question['filename'] + '.md'
            filepath = questions_dir / filename

            if filepath.exists():
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

        return f"""---
type: question
category: {category}
status: open
tags: []
created: {today}
updated: {today}
---

# {question['question']}

## Category

- [[{category.title()}]]

## Status

Open

## Description

{question.get('context', '(Extended description to be added)')}

## Relevant Thinkers

Who addresses this question:

- (To be added)

## Relevant Concepts

Concepts that inform this question:

- (To be added)

## Current Approaches

How different traditions or fields approach this question:

### Approach 1
(To be added)

### Approach 2
(To be added)

## Related Questions

- (To be added)

## Sources

Where this question is discussed:

**Discussed in:**
- (Transcripts to be linked)

## Personal Notes

(Insights, connections, or observations)
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
        help="Don't actually write files, just show what would be done"
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

    # Initialize populator
    populator = EntityPopulator(args.knowledge_base, dry_run=args.dry_run)

    print("🏗️  Populating Knowledge Base")
    print(f"📁 Knowledge base: {args.knowledge_base}")
    print(f"📖 Source: {args.normalized_entities}")
    if args.dry_run:
        print("🔍 DRY RUN MODE - No files will be modified")
    print()

    # Populate
    populator.populate_from_normalized(args.normalized_entities, verbose=args.verbose)

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
