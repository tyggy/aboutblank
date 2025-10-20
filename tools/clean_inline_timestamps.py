#!/usr/bin/env python3
"""
Clean Inline Timestamps from Transcripts - IMPROVED VERSION

Handles transcripts with inline timestamps like:
and<00: 00: 01. 319> next<00: 00: 01. 880> we<00: 00: 02. 040>

Removes timestamps, deduplicates repeated text, and creates readable paragraphs.
"""

import argparse
import re
from pathlib import Path
from typing import List


class InlineTimestampCleaner:
    """Cleans transcripts with inline timestamps."""

    def __init__(self):
        # Pattern to match timestamps like <00: 00: 01. 319>
        self.timestamp_pattern = re.compile(r'<\d{2}:\s*\d{2}:\s*\d{2}\.\s*\d{3}>')

    def remove_timestamps(self, text: str) -> str:
        """Remove all inline timestamps from text."""
        return self.timestamp_pattern.sub(' ', text)

    def aggressive_deduplicate(self, text: str) -> str:
        """
        Aggressively remove duplicated phrases.

        The auto-generated subtitles often duplicate phrases multiple times:
        "hello world hello world hello world" ->  "hello world"
        """
        words = text.split()

        if len(words) <= 5:
            return text

        # Use a more aggressive approach: sliding window to detect any repetition
        result = []
        i = 0

        while i < len(words):
            # Try to find the longest non-repeating sequence from this position
            best_seq_len = 1

            # Check from current position to end
            # Look for patterns where the same sequence repeats
            for check_len in range(1, min(50, (len(words) - i) // 2 + 1)):
                # Check if this sequence repeats immediately after
                seq = words[i:i + check_len]
                next_seq = words[i + check_len:i + 2 * check_len] if i + 2 * check_len <= len(words) else []

                if seq and seq == next_seq:
                    # Found a repetition, skip all copies
                    repeat_count = 1
                    pos = i + check_len

                    while pos + check_len <= len(words):
                        test_seq = words[pos:pos + check_len]
                        if test_seq == seq:
                            repeat_count += 1
                            pos += check_len
                        else:
                            break

                    # Add the sequence once and skip past all repetitions
                    result.extend(seq)
                    i = pos
                    best_seq_len = 0  # Signal that we handled this
                    break

            if best_seq_len > 0:
                # No repetition found, add this word
                result.append(words[i])
                i += 1

        return ' '.join(result)

    def clean_text(self, text: str) -> str:
        """Clean text by removing timestamps and deduplicating."""
        # Remove timestamps first
        text = self.remove_timestamps(text)

        # Clean up extra spaces
        text = re.sub(r'\s+', ' ', text)

        # Aggressive deduplication
        text = self.aggressive_deduplicate(text)

        # Clean up spacing around punctuation
        text = re.sub(r'\s+([.,!?;:])', r'\1', text)
        text = re.sub(r'([.,!?;:])\s*', r'\1 ', text)

        # Remove extra spaces again
        text = re.sub(r'\s+', ' ', text)

        # Remove common artifacts
        text = re.sub(r'\[.*?\]', '', text)  # Remove [music], [applause], etc.

        return text.strip()

    def split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Split on sentence boundaries but keep the punctuation
        sentences = re.split(r'([.!?])\s+', text)

        # Recombine sentences with their punctuation
        result = []
        for i in range(0, len(sentences) - 1, 2):
            sentence = sentences[i]
            punct = sentences[i + 1] if i + 1 < len(sentences) else ''
            if sentence.strip():
                result.append(sentence.strip() + punct)

        # Handle last sentence if no punctuation
        if len(sentences) % 2 == 1 and sentences[-1].strip():
            result.append(sentences[-1].strip())

        return result

    def create_paragraphs(self, sentences: List[str], target_length: int = 400) -> List[str]:
        """
        Group sentences into paragraphs of roughly target_length characters.

        Args:
            sentences: List of sentences
            target_length: Target paragraph length in characters

        Returns:
            List of paragraphs
        """
        paragraphs = []
        current_para = []
        current_length = 0

        for sentence in sentences:
            sentence_length = len(sentence)

            # Start new paragraph if adding this would make it too long
            # (unless current paragraph is empty)
            if current_para and current_length + sentence_length > target_length * 1.5:
                paragraphs.append(' '.join(current_para))
                current_para = [sentence]
                current_length = sentence_length
            else:
                current_para.append(sentence)
                current_length += sentence_length

        # Add remaining paragraph
        if current_para:
            paragraphs.append(' '.join(current_para))

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

        # Split into sentences
        sentences = self.split_into_sentences(cleaned)

        # Group into paragraphs
        paragraphs = self.create_paragraphs(sentences)

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
        pattern = r'(##\s+Transcript\s*\n)(.*?)(?=\n##|\Z)'

        def replace_transcript(match):
            header = match.group(1)
            transcript = match.group(2)

            # Clean the transcript
            cleaned = self.clean_transcript_section(transcript)

            return header + '\n' + cleaned + '\n'

        # Replace the transcript section
        new_content = re.sub(pattern, replace_transcript, content, flags=re.DOTALL | re.IGNORECASE)

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
  echo "hello<00:00:01.000> world<00:00:02.000> hello world" | python clean_inline_timestamps.py --test
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

        # Skip files that are already cleaned or edited (unless in-place or specific output)
        if not args.in_place and not args.output:
            if '_cleaned' in input_file.stem or '_edited' in input_file.stem:
                print(f"⊘ Skipping already processed file: {input_file.name}")
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
            output_file = input_file.parent / f"{stem}_cleaned{suffix}"

        try:
            cleaner.process_markdown_file(input_file, output_file)
        except Exception as e:
            print(f"✗ Error processing {input_file}: {e}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    main()
