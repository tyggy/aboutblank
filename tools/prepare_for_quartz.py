#!/usr/bin/env python3
"""
Prepare documents for Quartz by injecting links and using proper titles.

This creates linkified versions separate from clean edited files.
"""

import argparse
import re
import sys
from pathlib import Path
from datetime import datetime
from inject_links import LinkInjector


class QuartzPreparator:
    """Prepare documents for Quartz deployment."""

    def __init__(self, entities_path: Path, dry_run: bool = False):
        """Initialize with entity database."""
        self.injector = LinkInjector(entities_path, dry_run=dry_run)
        self.dry_run = dry_run
        self.stats = {
            'processed': 0,
            'skipped': 0,
            'errors': 0
        }

    def extract_title(self, content: str, fallback_name: str) -> str:
        """
        Extract a clean title from markdown content.

        Priority:
        1. First H1 heading (# Title)
        2. title: from frontmatter
        3. Fallback to cleaned filename
        """
        # Try to find first H1
        h1_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if h1_match:
            title = h1_match.group(1).strip()
            # Clean up any markdown formatting
            title = re.sub(r'\*\*(.+?)\*\*', r'\1', title)  # Remove bold
            title = re.sub(r'\*(.+?)\*', r'\1', title)  # Remove italic
            title = re.sub(r'`(.+?)`', r'\1', title)  # Remove code
            return title

        # Try frontmatter title
        fm_match = re.search(r'^---\s*\n.*?^title:\s*(.+)$.*?\n---',
                           content, re.MULTILINE | re.DOTALL)
        if fm_match:
            return fm_match.group(1).strip().strip('"\'')

        # Fallback: clean up filename
        # Remove _edited, _cleaned, etc.
        title = fallback_name
        title = re.sub(r'_edited|_cleaned|_linkified', '', title)
        # Convert video IDs and paper IDs to something nicer
        if re.match(r'^[a-zA-Z0-9_-]{11}$', title):
            # YouTube video ID - keep as is but label
            return f"Video: {title}"
        # Replace hyphens/underscores with spaces and title case
        title = title.replace('-', ' ').replace('_', ' ')
        return title.title()

    def create_quartz_frontmatter(self, title: str, doc_type: str,
                                  original_path: Path) -> str:
        """
        Create Quartz-friendly frontmatter.

        Args:
            title: Document title
            doc_type: 'transcript' or 'paper'
            original_path: Path to original file for metadata
        """
        today = datetime.now().strftime('%Y-%m-%d')

        # Get modification time of original
        mtime = datetime.fromtimestamp(original_path.stat().st_mtime)

        frontmatter = f"""---
title: "{title}"
type: {doc_type}
created: {mtime.strftime('%Y-%m-%d')}
updated: {today}
tags: [{doc_type}]
---
"""
        return frontmatter

    def prepare_document(self, source_path: Path, output_dir: Path,
                        doc_type: str, verbose: bool = False) -> None:
        """
        Prepare a single document for Quartz.

        Args:
            source_path: Path to clean edited markdown
            output_dir: Directory for linkified output
            doc_type: 'transcript' or 'paper'
            verbose: Print detailed info
        """
        if verbose:
            print(f"📖 Processing: {source_path.name}")

        try:
            # Read original content
            content = source_path.read_text(encoding='utf-8')

            # Extract title
            title = self.extract_title(content, source_path.stem)

            # Create clean filename from title
            # Keep it URL-friendly
            filename = title.lower()
            filename = re.sub(r'[^\w\s-]', '', filename)  # Remove special chars
            filename = re.sub(r'[-\s]+', '-', filename)  # Normalize spaces/hyphens
            filename = filename.strip('-')[:100]  # Limit length
            filename = f"{filename}.md"

            # Inject wiki links
            modified_content, links_added = self.injector._inject_links_in_text(content, verbose)

            # Remove old frontmatter if exists
            modified_content = re.sub(
                r'^---\s*\n.*?\n---\s*\n',
                '',
                modified_content,
                flags=re.DOTALL
            )

            # Add new Quartz frontmatter
            frontmatter = self.create_quartz_frontmatter(title, doc_type, source_path)
            final_content = frontmatter + "\n" + modified_content

            # Create output path
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / filename

            # Check if output exists and is identical
            if output_path.exists():
                existing = output_path.read_text(encoding='utf-8')
                if existing == final_content:
                    if verbose:
                        print(f"  ⊘ Skipped: {filename} (no changes)")
                    self.stats['skipped'] += 1
                    return

            # Write output
            if not self.dry_run:
                output_path.write_text(final_content, encoding='utf-8')
                if verbose:
                    print(f"  ✓ Created: {filename}")
                    if sum(links_added.values()) > 0:
                        print(f"    • Added {sum(links_added.values())} links")
            else:
                if verbose:
                    print(f"  [DRY RUN] Would create: {filename}")

            self.stats['processed'] += 1

        except Exception as e:
            print(f"❌ Error processing {source_path.name}: {e}", file=sys.stderr)
            self.stats['errors'] += 1

    def prepare_all(self, source_dir: Path, output_dir: Path,
                   doc_type: str, pattern: str = "*_edited.md",
                   verbose: bool = False) -> None:
        """
        Prepare all documents in a directory.

        Args:
            source_dir: Directory with clean edited files
            output_dir: Directory for linkified output
            doc_type: 'transcript' or 'paper'
            pattern: Glob pattern for source files
            verbose: Print detailed info
        """
        if not source_dir.exists():
            print(f"⚠️  Source directory not found: {source_dir}")
            return

        source_files = list(source_dir.glob(pattern))
        if not source_files:
            print(f"⚠️  No files matching {pattern} in {source_dir}")
            return

        if verbose:
            print(f"\n{'='*60}")
            print(f"Preparing {len(source_files)} {doc_type}s for Quartz")
            print(f"{'='*60}\n")

        for source_file in sorted(source_files):
            self.prepare_document(source_file, output_dir, doc_type, verbose)

    def print_summary(self):
        """Print processing summary."""
        print(f"\n{'='*60}")
        print("📊 Preparation Summary")
        print(f"{'='*60}")
        print(f"  ✓ Processed: {self.stats['processed']}")
        print(f"  ⊘ Skipped: {self.stats['skipped']} (no changes)")
        if self.stats['errors'] > 0:
            print(f"  ❌ Errors: {self.stats['errors']}")
        print(f"  📁 Total: {sum(self.stats.values())}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Prepare documents for Quartz with proper titles and wiki links"
    )
    parser.add_argument(
        '--transcripts',
        type=Path,
        default=Path('knowledge_base/transcripts/raw'),
        help='Directory with edited transcripts (default: knowledge_base/transcripts/raw)'
    )
    parser.add_argument(
        '--papers',
        type=Path,
        default=Path('knowledge_base/papers/edited'),
        help='Directory with edited papers (default: knowledge_base/papers/edited)'
    )
    parser.add_argument(
        '--output-transcripts',
        type=Path,
        default=Path('knowledge_base/transcripts/linkified'),
        help='Output directory for linkified transcripts'
    )
    parser.add_argument(
        '--output-papers',
        type=Path,
        default=Path('knowledge_base/papers/linkified'),
        help='Output directory for linkified papers'
    )
    parser.add_argument(
        '--entities',
        type=Path,
        default=Path('knowledge_base/entities'),
        help='Path to entities directory (default: knowledge_base/entities)'
    )
    parser.add_argument(
        '--skip-transcripts',
        action='store_true',
        help='Skip processing transcripts'
    )
    parser.add_argument(
        '--skip-papers',
        action='store_true',
        help='Skip processing papers'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Verbose output'
    )

    args = parser.parse_args()

    # Check entities directory
    if not args.entities.exists():
        print(f"❌ Entities directory not found: {args.entities}")
        print("Run 'make kb-normalize' first to create entity database")
        sys.exit(1)

    # Initialize preparator
    preparator = QuartzPreparator(args.entities, dry_run=args.dry_run)

    # Process transcripts
    if not args.skip_transcripts and args.transcripts.exists():
        preparator.prepare_all(
            args.transcripts,
            args.output_transcripts,
            'transcript',
            '*_edited.md',
            args.verbose
        )

    # Process papers
    if not args.skip_papers and args.papers.exists():
        preparator.prepare_all(
            args.papers,
            args.output_papers,
            'paper',
            '*_edited.md',
            args.verbose
        )

    # Print summary
    preparator.print_summary()

    if not args.dry_run:
        print("✅ Quartz preparation complete!")
        print()
        print("Next steps:")
        print("  1. Copy entity pages: cp -r knowledge_base/{thinkers,concepts,frameworks,institutions} quartz/content/")
        print("  2. Link documents: ln -s $(pwd)/knowledge_base/transcripts/linkified quartz/content/transcripts")
        print("  3. Link papers: ln -s $(pwd)/knowledge_base/papers/linkified quartz/content/papers")
        print("  4. Build Quartz: cd quartz && npx quartz build --serve")


if __name__ == '__main__':
    main()
