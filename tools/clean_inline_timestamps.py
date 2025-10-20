#!/usr/bin/env python3
"""
Clean Inline Timestamps from Transcripts

Handles transcripts with inline timestamps like:
and<00: 00: 01. 319> next<00: 00: 01. 880> we<00: 00: 02. 040>

Removes timestamps and deduplicates repeated text.
"""

import argparse
import re
from pathlib import Path
from typing import List, Set


class InlineTimestampCleaner:
    """Cleans transcripts with inline timestamps."""

    def __init__(self):
        # Pattern to match timestamps like <00: 00: 01. 319>
        self.timestamp_pattern = re.compile(r'<\d{2}:\s*\d{2}:\s*\d{2}\.\s*\d{3}>')

    def remove_timestamps(self, text: str) -> str:
        """Remove all inline timestamps from text."""
        return self.timestamp_pattern.sub('', text)

    def deduplicate_text(self, text: str) -> str:
        """
        Remove duplicated phrases that often appear in auto-transcripts.

        Example: "and next we are moving on our next and next we are moving on our next"
        Should become: "and next we are moving on our next"
        """
        # Split into words
        words = text.split()

        if len(words) <= 3:
            return text

        # Find repeating sequences
        cleaned_words = []
        i = 0

        while i < len(words):
            # Try different sequence lengths (from long to short)
            found_duplicate = False

            for seq_len in range(min(20, len(words) - i), 2, -1):
                if i + seq_len * 2 <= len(words):
                    # Check if next sequence matches
                    seq1 = words[i:i + seq_len]
                    seq2 = words[i + seq_len:i + seq_len * 2]

                    if seq1 == seq2:
                        # Found duplicate, add only once
                        cleaned_words.extend(seq1)
                        i += seq_len * 2
                        found_duplicate = True
                        break

            if not found_duplicate:
                cleaned_words.append(words[i])
                i += 1

        return ' '.join(cleaned_words)

    def clean_text(self, text: str) -> str:
        """Clean text by removing timestamps and deduplicating."""
        # Remove timestamps
        text = self.remove_timestamps(text)

        # Clean up extra spaces
        text = re.sub(r'\s+', ' ', text)

        # Deduplicate repeated phrases
        text = self.deduplicate_text(text)

        # Clean up spacing around punctuation
        text = re.sub(r'\s+([.,!?;:])', r'\1', text)
        text = re.sub(r'([.,!?;:])\s*', r'\1 ', text)

        # Remove extra spaces
        text = re.sub(r'\s+', ' ', text)

        return text.strip()

    def split_into_paragraphs(self, text: str, min_sentence_length: int = 100) -> List[str]:
        """
        Split cleaned text into readable paragraphs.

        Args:
            text: Cleaned text
            min_sentence_length: Minimum characters before starting new paragraph

        Returns:
            List of paragraphs
        """
        # Split on sentence boundaries
        sentences = re.split(r'([.!?]\s+)', text)

        paragraphs = []
        current_para = []
        current_length = 0

        for i in range(0, len(sentences), 2):
            sentence = sentences[i]
            punct = sentences[i + 1] if i + 1 < len(sentences) else ''

            full_sentence = sentence + punct
            current_para.append(full_sentence)
            current_length += len(full_sentence)

            # Start new paragraph if we have enough text and a sentence boundary
            if current_length >= min_sentence_length and punct.strip():
                para_text = ''.join(current_para).strip()
                if para_text:
                    paragraphs.append(para_text)
                current_para = []
                current_length = 0

        # Add any remaining text
        if current_para:
            para_text = ''.join(current_para).strip()
            if para_text:
                paragraphs.append(para_text)

        return paragraphs

    def clean_transcript_section(self, transcript_text: str) -> str:
        """
        Clean a full transcript section.

        Args:
            transcript_text: Raw transcript text with inline timestamps

        Returns:
            Cleaned, formatted transcript
        """
        # Clean the text
        cleaned = self.clean_text(transcript_text)

        # Split into paragraphs
        paragraphs = self.split_into_paragraphs(cleaned)

        # Join with double newlines
        return '\n\n'.join(paragraphs)

    def process_markdown_file(self, input_file: Path, output_file: Path = None) -> None:
        """
        Process a markdown file, cleaning only the transcript section.

        Args:
            input_file: Path to input markdown file
            output_file: Path to output file (default: overwrite input)
        """
        if output_file is None:
            output_file = input_file

        content = input_file.read_text(encoding='utf-8')

        # Find the transcript section
        # Looking for ## Transcript followed by content until ## or end of file
        pattern = r'(## Transcript\s*\n)(.*?)(?=\n##|\Z)'

        def replace_transcript(match):
            header = match.group(1)
            transcript = match.group(2)

            # Clean the transcript
            cleaned = self.clean_transcript_section(transcript)

            return header + '\n' + cleaned

        # Replace the transcript section
        new_content = re.sub(pattern, replace_transcript, content, flags=re.DOTALL)

        # Write output
        output_file.write_text(new_content, encoding='utf-8')

        print(f"✓ Cleaned: {input_file.name}")
        if output_file != input_file:
            print(f"  → Saved to: {output_file.name}")


def main():
    parser = argparse.ArgumentParser(
        description='Clean inline timestamps from transcripts',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Clean a single file (in-place)
  python clean_inline_timestamps.py transcript.md

  # Clean to a new file
  python clean_inline_timestamps.py transcript.md -o cleaned.md

  # Clean all markdown files in a directory
  python clean_inline_timestamps.py knowledge_base/transcripts/raw/*.md

  # Test on raw text
  echo "hello<00:00:01.000> world<00:00:02.000>" | python clean_inline_timestamps.py --test
        """
    )

    parser.add_argument(
        'files',
        nargs='*',
        help='Markdown files to clean'
    )

    parser.add_argument(
        '-o', '--output',
        help='Output file (only for single file input)'
    )

    parser.add_argument(
        '--test',
        action='store_true',
        help='Test mode: read from stdin and print to stdout'
    )

    parser.add_argument(
        '--suffix',
        default='_cleaned',
        help='Suffix to add to output files (default: _cleaned)'
    )

    parser.add_argument(
        '--in-place',
        action='store_true',
        help='Overwrite input files'
    )

    args = parser.parse_args()

    cleaner = InlineTimestampCleaner()

    # Test mode
    if args.test:
        import sys
        text = sys.stdin.read()
        cleaned = cleaner.clean_text(text)
        print(cleaned)
        return

    if not args.files:
        parser.print_help()
        return

    # Process files
    for file_path in args.files:
        input_file = Path(file_path)

        if not input_file.exists():
            print(f"✗ File not found: {input_file}")
            continue

        # Determine output file
        if args.output and len(args.files) == 1:
            output_file = Path(args.output)
        elif args.in_place:
            output_file = input_file
        else:
            # Add suffix before extension
            stem = input_file.stem
            suffix = input_file.suffix
            output_file = input_file.parent / f"{stem}{args.suffix}{suffix}"

        try:
            cleaner.process_markdown_file(input_file, output_file)
        except Exception as e:
            print(f"✗ Error processing {input_file}: {e}")


if __name__ == '__main__':
    main()
