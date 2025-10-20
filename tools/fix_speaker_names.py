#!/usr/bin/env python3
"""
Fix entity name transcription errors in transcripts.

Reads speaker_corrections.yaml (which handles all entity types: people,
institutions, concepts, frameworks) and corrects common transcription
errors before entity extraction.
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import yaml


class SpeakerNameFixer:
    """Fix speaker name transcription errors."""

    def __init__(self, corrections_file: Path):
        """
        Initialize with corrections file.

        Args:
            corrections_file: Path to speaker_corrections.yaml
        """
        self.corrections = self._load_corrections(corrections_file)
        self.stats = {'files_processed': 0, 'corrections_made': 0}

    def _load_corrections(self, corrections_file: Path) -> Dict[str, str]:
        """
        Load speaker corrections from YAML file.

        Returns:
            Dict mapping lowercase incorrect name -> correct name
        """
        if not corrections_file.exists():
            print(f"⚠️  Corrections file not found: {corrections_file}", file=sys.stderr)
            return {}

        try:
            data = yaml.safe_load(corrections_file.read_text(encoding='utf-8'))

            corrections = {}
            for incorrect, correction_data in data.items():
                # Skip comments and metadata
                if not isinstance(correction_data, dict):
                    continue

                correct_name = correction_data.get('correct')
                if correct_name:
                    # Store lowercase key for case-insensitive matching
                    corrections[incorrect.lower()] = correct_name

                    # Also add aliases as corrections
                    for alias in correction_data.get('aliases', []):
                        if alias.lower() != correct_name.lower():
                            corrections[alias.lower()] = correct_name

            return corrections

        except Exception as e:
            print(f"❌ Error loading corrections file: {e}", file=sys.stderr)
            return {}

    def fix_transcript(self, transcript_path: Path, output_path: Path = None, verbose: bool = False) -> int:
        """
        Fix speaker names in a transcript file.

        Args:
            transcript_path: Path to transcript markdown file
            output_path: Where to save (default: overwrite original)
            verbose: Print detailed information

        Returns:
            Number of corrections made
        """
        if verbose:
            print(f"📖 Processing: {transcript_path.name}")

        content = transcript_path.read_text(encoding='utf-8')
        original_content = content
        corrections_in_file = 0

        # Apply corrections
        for incorrect, correct in self.corrections.items():
            # Build pattern with word boundaries
            # Handle both regular mentions and possessives
            pattern = re.compile(
                r'\b' + re.escape(incorrect) + r"(?:'s)?\b",
                re.IGNORECASE
            )

            def replacement(match):
                matched_text = match.group(0)
                # Preserve possessive if present
                if matched_text.lower().endswith("'s"):
                    return correct + "'s"
                # Try to preserve original capitalization pattern
                if matched_text.isupper():
                    return correct.upper()
                elif matched_text[0].isupper():
                    return correct
                else:
                    return correct

            # Count matches before replacing
            matches = list(pattern.finditer(content))
            if matches:
                content = pattern.sub(replacement, content)
                corrections_in_file += len(matches)

                if verbose:
                    print(f"  ✓ Fixed '{incorrect}' → '{correct}' ({len(matches)} occurrence(s))")

        # Only write if changes were made
        if content != original_content:
            if output_path is None:
                output_path = transcript_path

            output_path.write_text(content, encoding='utf-8')

            if verbose:
                print(f"  ✓ Made {corrections_in_file} correction(s)")
        else:
            if verbose:
                print(f"  ⊘ No corrections needed")

        self.stats['files_processed'] += 1
        self.stats['corrections_made'] += corrections_in_file

        return corrections_in_file

    def print_summary(self):
        """Print summary of corrections."""
        print()
        print("=" * 50)
        print("📊 Summary")
        print("=" * 50)
        print(f"  Files processed: {self.stats['files_processed']}")
        print(f"  Corrections made: {self.stats['corrections_made']}")
        print()


def scan_for_potential_errors(transcript_paths: List[Path], corrections_file: Path, verbose: bool = False) -> None:
    """
    Scan transcripts for potential name errors not in corrections file.

    This helps discover new transcription errors to add to corrections.
    """
    print("🔍 Scanning for potential speaker name errors...")
    print()

    # Common patterns that might indicate speaker attribution
    speaker_patterns = [
        r'\[Speaker:?\s*([^\]]+)\]',  # [Speaker: Name]
        r'\[([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\]:',  # [Name]:
        r'Speaker:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # Speaker: Name
    ]

    all_speakers = set()

    for transcript_path in transcript_paths:
        content = transcript_path.read_text(encoding='utf-8')

        for pattern in speaker_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                speaker = match.group(1).strip()
                all_speakers.add(speaker)

    if all_speakers:
        print(f"Found {len(all_speakers)} unique speaker attribution(s):")
        print()

        # Load existing corrections
        existing_corrections = set()
        if corrections_file.exists():
            data = yaml.safe_load(corrections_file.read_text(encoding='utf-8'))
            for incorrect, correction_data in data.items():
                if isinstance(correction_data, dict):
                    existing_corrections.add(correction_data.get('correct', '').lower())
                    existing_corrections.update(
                        alias.lower() for alias in correction_data.get('aliases', [])
                    )

        for speaker in sorted(all_speakers):
            if speaker.lower() in existing_corrections:
                print(f"  ✓ {speaker} (already in corrections)")
            else:
                print(f"  ⚠️  {speaker} (not in corrections - potential error?)")

        print()
        print("Review the list above and add any transcription errors to:")
        print(f"  {corrections_file}")
    else:
        print("No speaker attributions found in transcripts.")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Fix speaker name transcription errors in transcripts"
    )
    parser.add_argument(
        'transcripts',
        nargs='*',
        type=Path,
        help='Transcript files to fix (or use --scan-only)'
    )
    parser.add_argument(
        '--corrections',
        type=Path,
        default=Path('knowledge_base/speaker_corrections.yaml'),
        help='Speaker corrections YAML file (default: knowledge_base/speaker_corrections.yaml)'
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        help='Output directory (default: overwrite originals)'
    )
    parser.add_argument(
        '--scan-only',
        action='store_true',
        help='Just scan for potential errors without fixing'
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Verbose output'
    )

    args = parser.parse_args()

    if not args.corrections.exists():
        print(f"❌ Corrections file not found: {args.corrections}", file=sys.stderr)
        print(f"Create it with speaker name corrections.", file=sys.stderr)
        print(f"See knowledge_base/speaker_corrections.yaml for format.", file=sys.stderr)
        sys.exit(1)

    # Scan mode
    if args.scan_only:
        if not args.transcripts:
            print("❌ Error: Provide transcript files to scan", file=sys.stderr)
            sys.exit(1)

        scan_for_potential_errors(args.transcripts, args.corrections, verbose=args.verbose)
        sys.exit(0)

    # Fix mode
    if not args.transcripts:
        print("❌ Error: Provide transcript files to fix", file=sys.stderr)
        parser.print_help()
        sys.exit(1)

    # Initialize fixer
    fixer = SpeakerNameFixer(args.corrections)

    if not fixer.corrections:
        print("⚠️  No corrections loaded. Nothing to fix.", file=sys.stderr)
        sys.exit(1)

    print("🔧 Fixing Speaker Names")
    print(f"📖 Corrections: {args.corrections}")
    print(f"   Loaded {len(fixer.corrections)} correction(s)")
    print(f"📁 Transcripts: {len(args.transcripts)} file(s)")
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

        # Fix speaker names
        fixer.fix_transcript(transcript_path, output_path, verbose=args.verbose)

    # Print summary
    fixer.print_summary()

    print("✅ Speaker name correction complete!")
    print()
    print("Next steps:")
    print("  1. Review corrected transcripts")
    print("  2. Run entity extraction: make kb-extract")
    print("  3. Names will now be correctly normalized")


if __name__ == '__main__':
    main()
