#!/usr/bin/env python3
"""
Re-run entity extraction for files that failed.

Reads extraction results and re-processes any that have errors.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List


def find_failed_extractions(extractions_dir: Path) -> List[Path]:
    """Find extraction files that have errors."""
    failed_sources = []

    for json_file in extractions_dir.glob('*_entities.json'):
        try:
            data = json.loads(json_file.read_text(encoding='utf-8'))

            # Check for error in metadata
            if '_metadata' in data and 'error' in data['_metadata']:
                source_file = data['_metadata'].get('source_file')
                if source_file:
                    failed_sources.append(Path(source_file))
                    print(f"❌ Failed: {json_file.name}")
                    print(f"   Error: {data['_metadata']['error']}")
                    print(f"   Source: {source_file}")
                    print()
        except Exception as e:
            print(f"⚠️  Couldn't read {json_file}: {e}", file=sys.stderr)

    return failed_sources


def main():
    parser = argparse.ArgumentParser(
        description="Re-run entity extraction for failed files"
    )
    parser.add_argument(
        '--extractions-dir',
        type=Path,
        default=Path('knowledge_base/extractions'),
        help='Directory with extraction JSON files'
    )
    parser.add_argument(
        '--api-key',
        help='Anthropic API key (or set ANTHROPIC_API_KEY env var)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Just list failed extractions without re-running'
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Verbose output'
    )

    args = parser.parse_args()

    if not args.extractions_dir.exists():
        print(f"❌ Error: Extractions directory not found: {args.extractions_dir}", file=sys.stderr)
        sys.exit(1)

    print("🔍 Scanning for failed extractions...\n")

    failed_sources = find_failed_extractions(args.extractions_dir)

    if not failed_sources:
        print("✅ No failed extractions found!")
        sys.exit(0)

    print(f"Found {len(failed_sources)} failed extraction(s)")
    print()

    if args.dry_run:
        print("Dry run mode - would retry these files:")
        for source in failed_sources:
            print(f"  - {source}")
        sys.exit(0)

    # Re-run extraction
    print("Re-running extractions...")
    print()

    import subprocess
    import os

    # Build command
    cmd = ['python', 'tools/extract_entities.py']
    cmd.extend([str(f) for f in failed_sources])

    if args.verbose:
        cmd.append('--verbose')

    if args.api_key:
        cmd.extend(['--api-key', args.api_key])

    # Run
    env = os.environ.copy()
    result = subprocess.run(cmd, env=env)

    if result.returncode == 0:
        print()
        print("✅ Re-extraction complete!")
        print("Check knowledge_base/extractions/ for debug files if issues persist")
    else:
        print()
        print("❌ Re-extraction failed")
        sys.exit(1)


if __name__ == '__main__':
    main()
