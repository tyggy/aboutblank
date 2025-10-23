#!/usr/bin/env python3
"""
Count how many times each entity is mentioned/linked across all documents.

Adds mention_count to entity frontmatter for Quartz sidebar sorting.
"""

import argparse
import re
import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, Set


def count_entity_mentions(entities_dir: Path, docs_dirs: list[Path]) -> Dict[str, int]:
    """
    Count mentions of each entity across all documents.

    Returns:
        Dict mapping entity_name -> mention_count
    """
    mention_counts = defaultdict(int)

    # Get all entity names and aliases
    entity_patterns = {}  # name/alias -> canonical_name

    for entity_type in ['thinkers', 'concepts', 'frameworks', 'institutions']:
        type_dir = entities_dir / entity_type
        if not type_dir.exists():
            continue

        for json_file in type_dir.glob('*.json'):
            try:
                entity = json.loads(json_file.read_text(encoding='utf-8'))
                name = entity.get('name')
                if not name:
                    continue

                # Add name
                entity_patterns[name.lower()] = name

                # Add aliases
                for alias in entity.get('aliases', []):
                    if alias:
                        entity_patterns[alias.lower()] = name

            except Exception as e:
                print(f"⚠️  Error loading {json_file}: {e}")

    # Count mentions in documents
    wiki_link_pattern = re.compile(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]')

    for docs_dir in docs_dirs:
        if not docs_dir.exists():
            continue

        for doc_file in docs_dir.glob('**/*.md'):
            try:
                content = doc_file.read_text(encoding='utf-8')

                # Find all wiki links
                for match in wiki_link_pattern.finditer(content):
                    linked_entity = match.group(1).strip()

                    # Normalize and look up canonical name
                    canonical = entity_patterns.get(linked_entity.lower(), linked_entity)
                    mention_counts[canonical] += 1

            except Exception as e:
                print(f"⚠️  Error reading {doc_file}: {e}")

    return dict(mention_counts)


def update_entity_frontmatter(entity_file: Path, mention_count: int) -> bool:
    """
    Update entity markdown file with mention count in frontmatter.

    Returns:
        True if file was modified
    """
    try:
        content = entity_file.read_text(encoding='utf-8')

        # Find frontmatter
        fm_match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
        if not fm_match:
            return False

        frontmatter = fm_match.group(1)
        body = fm_match.group(2)

        # Check if mention_count already exists
        if re.search(r'^mention_count:', frontmatter, re.MULTILINE):
            # Update existing
            frontmatter = re.sub(
                r'^mention_count:.*$',
                f'mention_count: {mention_count}',
                frontmatter,
                flags=re.MULTILINE
            )
        else:
            # Add new field after 'updated' or at end
            if 'updated:' in frontmatter:
                frontmatter = re.sub(
                    r'(updated:.*?)$',
                    r'\1\nmention_count: ' + str(mention_count),
                    frontmatter,
                    flags=re.MULTILINE
                )
            else:
                frontmatter += f"\nmention_count: {mention_count}"

        # Reconstruct file
        new_content = f"---\n{frontmatter}\n---\n{body}"

        if new_content != content:
            entity_file.write_text(new_content, encoding='utf-8')
            return True

        return False

    except Exception as e:
        print(f"❌ Error updating {entity_file}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Count entity mentions and update frontmatter for Quartz sorting"
    )
    parser.add_argument(
        '--entities',
        type=Path,
        default=Path('knowledge_base/entities'),
        help='Entities directory'
    )
    parser.add_argument(
        '--docs',
        type=Path,
        nargs='+',
        default=[
            Path('knowledge_base/transcripts/linkified'),
            Path('knowledge_base/papers/linkified')
        ],
        help='Document directories to scan'
    )
    parser.add_argument(
        '--output-entity-pages',
        type=Path,
        default=Path('knowledge_base'),
        help='Directory with generated entity markdown pages'
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Verbose output'
    )

    args = parser.parse_args()

    if not args.entities.exists():
        print(f"❌ Entities directory not found: {args.entities}")
        return 1

    print("🔍 Counting entity mentions...")

    # Count mentions
    mention_counts = count_entity_mentions(args.entities, args.docs)

    if args.verbose:
        # Show top 20 most mentioned
        print("\n📊 Top 20 Most Mentioned Entities:")
        sorted_entities = sorted(mention_counts.items(), key=lambda x: x[1], reverse=True)
        for name, count in sorted_entities[:20]:
            print(f"  {count:4d}  {name}")
        print()

    # Update entity markdown files
    print("📝 Updating entity frontmatter...")
    updated = 0
    skipped = 0

    for entity_type in ['thinkers', 'concepts', 'frameworks', 'institutions']:
        type_dir = args.output_entity_pages / entity_type
        if not type_dir.exists():
            continue

        for md_file in type_dir.glob('*.md'):
            # Extract name from file
            content = md_file.read_text(encoding='utf-8')
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            if not title_match:
                continue

            entity_name = title_match.group(1).strip()
            count = mention_counts.get(entity_name, 0)

            if update_entity_frontmatter(md_file, count):
                updated += 1
                if args.verbose:
                    print(f"  ✓ {entity_name}: {count} mentions")
            else:
                skipped += 1

    print(f"\n✅ Updated {updated} entity pages")
    if skipped > 0:
        print(f"  ⊘ Skipped {skipped} (no changes)")

    print("\nTo use in Quartz sidebar:")
    print("  1. Configure quartz.config.ts to sort by mention_count")
    print("  2. Limit displayed items to top N most mentioned")


if __name__ == '__main__':
    main()
