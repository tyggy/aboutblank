#!/usr/bin/env python3
"""
Inject wiki links into transcripts based on extracted entities.

Adds [[Entity Name]] links when entities are mentioned in transcripts.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict


class LinkInjector:
    """Inject wiki-style links into markdown transcripts."""

    def __init__(self, entities_dir: Path, dry_run: bool = False):
        """
        Initialize link injector.

        Args:
            entities_dir: Path to knowledge_base/entities directory
            dry_run: If True, don't actually write files
        """
        self.dry_run = dry_run

        # Load entities from individual JSON files
        data = self._load_all_entities(entities_dir)

        # Build lookup tables for each entity type
        self.entity_lookup = self._build_entity_lookup(data)

        # Statistics
        self.stats = defaultdict(int)

    def _load_all_entities(self, entities_dir: Path) -> Dict:
        """Load all entities from individual JSON files."""
        data = {
            'thinkers': [],
            'concepts': [],
            'frameworks': [],
            'institutions': [],
            'questions': []
        }

        for entity_type in data.keys():
            type_dir = entities_dir / entity_type
            if not type_dir.exists():
                continue

            for json_file in type_dir.glob('*.json'):
                try:
                    entity = json.loads(json_file.read_text(encoding='utf-8'))
                    data[entity_type].append(entity)
                except Exception as e:
                    print(f"⚠️  Error loading {json_file}: {e}", file=sys.stderr)

        return data

    def _build_entity_lookup(self, data: Dict) -> Dict[str, Dict]:
        """
        Build lookup table mapping text patterns to entity names.

        Returns:
            Dict mapping lowercase text -> (display_name, entity_type)
        """
        lookup = {}

        # Process thinkers
        for thinker in data.get('thinkers', []):
            name = thinker['name']
            # Add main name
            lookup[name.lower()] = {'name': name, 'type': 'thinker'}
            # Add aliases
            for alias in thinker.get('aliases', []):
                if alias:
                    lookup[alias.lower()] = {'name': name, 'type': 'thinker'}

        # Process concepts
        for concept in data.get('concepts', []):
            name = concept['name']
            lookup[name.lower()] = {'name': name, 'type': 'concept'}
            for alias in concept.get('aliases', []):
                if alias:
                    lookup[alias.lower()] = {'name': name, 'type': 'concept'}

        # Process frameworks
        for framework in data.get('frameworks', []):
            name = framework['name']
            lookup[name.lower()] = {'name': name, 'type': 'framework'}

        # Process institutions
        for institution in data.get('institutions', []):
            name = institution['name']
            lookup[name.lower()] = {'name': name, 'type': 'institution'}

        return lookup

    def inject_links_in_file(self, transcript_path: Path, output_path: Path = None, verbose: bool = False) -> None:
        """
        Inject wiki links into a transcript file.

        Args:
            transcript_path: Path to transcript markdown file
            output_path: Where to save (default: overwrite original)
            verbose: Print detailed information
        """
        if verbose:
            print(f"📖 Processing: {transcript_path.name}")

        content = transcript_path.read_text(encoding='utf-8')

        # Track what we've linked in this file
        links_added = defaultdict(int)

        # Inject links
        modified_content, links_added = self._inject_links_in_text(content, verbose)

        # Only write if changes were made
        if modified_content != content:
            if output_path is None:
                output_path = transcript_path

            if self.dry_run:
                if verbose:
                    print(f"  [DRY RUN] Would add {sum(links_added.values())} links")
            else:
                output_path.write_text(modified_content, encoding='utf-8')
                if verbose:
                    print(f"  ✓ Added {sum(links_added.values())} links")
                    for entity_type, count in sorted(links_added.items()):
                        print(f"    • {count} {entity_type} links")

            # Update stats
            for entity_type, count in links_added.items():
                self.stats[entity_type] += count
        else:
            if verbose:
                print(f"  ⊘ No new links to add")

    def _inject_links_in_text(self, text: str, verbose: bool = False) -> Tuple[str, Dict]:
        """
        Inject wiki links into text.

        Returns:
            (modified_text, links_added_by_type)
        """
        links_added = defaultdict(int)

        # Sort entities by length (longest first) to match multi-word entities first
        sorted_patterns = sorted(self.entity_lookup.keys(), key=len, reverse=True)

        # Build regex pattern for all entities
        # We'll process each paragraph separately to avoid cross-paragraph issues
        paragraphs = text.split('\n\n')
        modified_paragraphs = []

        for paragraph in paragraphs:
            modified_para = paragraph

            # Skip if this paragraph is already heavily linked or is metadata
            if modified_para.count('[[') > 10 or modified_para.startswith('---'):
                modified_paragraphs.append(modified_para)
                continue

            # Track positions we've already linked (to avoid overlapping links)
            linked_ranges = set()

            for pattern_text in sorted_patterns:
                entity_info = self.entity_lookup[pattern_text]
                entity_name = entity_info['name']
                entity_type = entity_info['type']

                # Build regex pattern with word boundaries
                # Handle possessives (e.g., "Levin's")
                pattern = re.escape(pattern_text)
                regex = re.compile(
                    r'\b' + pattern + r"(?:'s)?" + r'\b',
                    re.IGNORECASE
                )

                # Find all matches
                matches = list(regex.finditer(modified_para))

                for match in matches:
                    start, end = match.span()

                    # Skip if already inside a link
                    if self._is_inside_link(modified_para, start):
                        continue

                    # Skip if overlaps with existing link
                    if any(start < linked_end and end > linked_start
                           for linked_start, linked_end in linked_ranges):
                        continue

                    # Skip if inside code blocks or headings
                    if self._is_inside_special_block(modified_para, start):
                        continue

                    # Extract matched text (preserving case and possessive)
                    matched_text = match.group(0)

                    # Create wiki link
                    wiki_link = f"[[{entity_name}]]"

                    # If possessive, keep the 's outside the link
                    if matched_text.endswith("'s"):
                        wiki_link = f"[[{entity_name}]]'s"
                        matched_text = matched_text[:-2]  # Remove 's for replacement

                    # Replace
                    modified_para = (
                        modified_para[:start] +
                        wiki_link +
                        modified_para[end:]
                    )

                    # Track this range as linked
                    new_end = start + len(wiki_link)
                    linked_ranges.add((start, new_end))

                    # Update stats
                    links_added[entity_type] += 1

                    # Adjust remaining positions after insertion
                    len_diff = len(wiki_link) - (end - start)
                    linked_ranges = {
                        (s + len_diff if s > start else s,
                         e + len_diff if e > start else e)
                        for s, e in linked_ranges
                    }

                    # Need to recompile matches since text changed
                    break  # Will continue with next pattern

            modified_paragraphs.append(modified_para)

        modified_text = '\n\n'.join(modified_paragraphs)
        return modified_text, links_added

    def _is_inside_link(self, text: str, position: int) -> bool:
        """Check if position is inside an existing wiki link."""
        # Find the last [[ before position
        last_open = text.rfind('[[', 0, position)
        if last_open == -1:
            return False

        # Check if there's a closing ]] between the [[ and position
        close_after_open = text.find(']]', last_open, position)
        if close_after_open == -1:
            # We're inside an unclosed [[
            return True

        return False

    def _is_inside_special_block(self, text: str, position: int) -> bool:
        """Check if position is inside a code block, heading, or other special block."""
        # Check if we're in a heading (line starts with #)
        line_start = text.rfind('\n', 0, position) + 1
        line = text[line_start:text.find('\n', position) if text.find('\n', position) != -1 else len(text)]

        if line.lstrip().startswith('#'):
            return True

        # Check for inline code (between backticks)
        before = text[:position]
        backtick_count = before.count('`') - before.count('\\`')
        if backtick_count % 2 == 1:
            return True

        # Check for frontmatter (between ---)
        if text.startswith('---'):
            second_marker = text.find('\n---', 1)
            if second_marker != -1 and position < second_marker:
                return True

        return False

    def print_summary(self) -> None:
        """Print summary of link injection."""
        print()
        print("=" * 50)
        print("📊 Summary")
        print("=" * 50)
        total_links = sum(self.stats.values())
        print(f"  ✓ Total links added: {total_links}")
        for entity_type, count in sorted(self.stats.items()):
            print(f"    • {count} {entity_type} links")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Inject wiki links into transcripts"
    )
    parser.add_argument(
        'transcripts',
        nargs='+',
        type=Path,
        help='Transcript files to process'
    )
    parser.add_argument(
        '--knowledge-base',
        type=Path,
        default=Path('knowledge_base'),
        help='Knowledge base directory (default: knowledge_base)'
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        help='Output directory (default: overwrite originals)'
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

    entities_dir = args.knowledge_base / 'entities'
    if not entities_dir.exists():
        print(f"❌ Error: Entities directory not found: {entities_dir}", file=sys.stderr)
        print("   Run 'make kb-normalize' first to create entity files.", file=sys.stderr)
        sys.exit(1)

    # Initialize injector
    injector = LinkInjector(entities_dir, dry_run=args.dry_run)

    print("🔗 Injecting Wiki Links")
    print(f"📂 Entities: {entities_dir}")
    print(f"📁 Transcripts: {len(args.transcripts)} file(s)")
    if args.dry_run:
        print("🔍 DRY RUN MODE")
    print()

    # Process each transcript
    for transcript_path in args.transcripts:
        if not transcript_path.exists():
            print(f"⚠️  File not found: {transcript_path}", file=sys.stderr)
            continue

        # Determine output path
        if args.output_dir:
            args.output_dir.mkdir(parents=True, exist_ok=True)
            output_path = args.output_dir / transcript_path.name
        else:
            output_path = transcript_path

        # Inject links
        injector.inject_links_in_file(transcript_path, output_path, verbose=args.verbose)

    # Print summary
    injector.print_summary()

    if not args.dry_run:
        print("✅ Link injection complete!")
        print()
        print("Next steps:")
        print("  1. Open knowledge base in Obsidian")
        print("  2. View the graph (Cmd/Ctrl+G)")
        print("  3. Manually review and refine entity pages")


if __name__ == '__main__':
    main()
