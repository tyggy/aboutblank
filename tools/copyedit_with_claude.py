#!/usr/bin/env python3
"""
Copyedit Transcripts Using Claude API - WITH BATCHING

Uses Claude API (Claude Haiku 4.5 for cost-effectiveness) to:
- Fix grammar and punctuation
- Remove filler words (um, uh, you know, etc.)
- Improve readability
- Preserve meaning and content

Supports batching for long transcripts to avoid context window limits.
"""

import argparse
import os
import re
from pathlib import Path
from typing import List, Optional

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("Warning: anthropic package not installed")
    print("Install with: pip install anthropic")


class ClaudeCopyeditor:
    """Copyedit transcripts using Claude API with smart batching."""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-haiku-4-5-20251001"):
        """
        Initialize the copyeditor.

        Args:
            api_key: Anthropic API key (or set ANTHROPIC_API_KEY env var)
            model: Claude model to use (default: Claude Haiku 4.5 for cost-effectiveness)
        """
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("anthropic package is required. Install with: pip install anthropic")

        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError(
                "API key required. Set ANTHROPIC_API_KEY environment variable "
                "or pass api_key parameter"
            )

        self.client = Anthropic(api_key=self.api_key)
        self.model = model

        # Context window limits (conservative estimates to stay well under limits)
        # Claude 3.5 Haiku has 200k context, but we'll use 150k to be safe
        # and account for system prompt + output
        self.max_input_chars = 150000 * 4  # ~4 chars per token

    def split_into_batches(self, text: str, max_chars: int = None) -> List[str]:
        """
        Split text into batches that fit within context window.

        Splits on paragraph boundaries to maintain coherence.

        Args:
            text: Text to split
            max_chars: Maximum characters per batch (default: self.max_input_chars)

        Returns:
            List of text batches
        """
        if max_chars is None:
            max_chars = self.max_input_chars

        # If text fits in one batch, return it
        if len(text) <= max_chars:
            return [text]

        # Split on double newlines (paragraph boundaries)
        paragraphs = text.split('\n\n')

        batches = []
        current_batch = []
        current_length = 0

        for para in paragraphs:
            para_length = len(para) + 2  # +2 for the \n\n we'll add back

            # If adding this paragraph would exceed limit, start new batch
            if current_batch and current_length + para_length > max_chars:
                batches.append('\n\n'.join(current_batch))
                current_batch = [para]
                current_length = para_length
            else:
                current_batch.append(para)
                current_length += para_length

        # Add remaining batch
        if current_batch:
            batches.append('\n\n'.join(current_batch))

        return batches

    def copyedit_text(self, text: str, context: str = "", batch_info: str = "") -> str:
        """
        Copyedit text using Claude API.

        Args:
            text: Text to copyedit
            context: Optional context about the text (speaker, topic, etc.)
            batch_info: Info about which batch this is (for logging)

        Returns:
            Copyedited text
        """
        system_prompt = """You are a professional copyeditor specializing in cleaning up transcripts.

Your task:
1. Fix grammar and punctuation
2. Remove filler words (um, uh, you know, like, basically, actually when unnecessary)
3. Remove false starts and repetitions
4. Fix run-on sentences
5. Improve readability while preserving the speaker's voice
6. Keep technical terms and proper names as-is
7. Maintain paragraph structure

Important:
- DO NOT change the meaning or content
- DO NOT add new information
- DO NOT remove important content
- DO preserve the speaker's natural style and tone
- DO keep it conversational if the original was conversational
- If this is part of a longer transcript, maintain flow for smooth transitions

Output ONLY the edited text, no explanations or meta-commentary."""

        user_prompt = f"""Copyedit this transcript:

{f"Context: {context}" if context else ""}
{f"Batch: {batch_info}" if batch_info else ""}

Transcript:
{text}

Remember: Fix grammar, remove fillers, improve readability, but preserve meaning and voice."""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=8192,  # Allow longer output for Haiku
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )

            return message.content[0].text

        except Exception as e:
            print(f"Error calling Claude API: {e}")
            raise

    def copyedit_long_text(self, text: str, context: str = "") -> str:
        """
        Copyedit potentially long text using batching.

        Args:
            text: Text to copyedit (can be very long)
            context: Optional context

        Returns:
            Copyedited text
        """
        # Split into batches
        batches = self.split_into_batches(text)

        if len(batches) == 1:
            print(f"  Processing in 1 batch ({len(text)} chars)")
            return self.copyedit_text(text, context)

        print(f"  Splitting into {len(batches)} batches...")

        # Process each batch
        edited_batches = []
        for i, batch in enumerate(batches, 1):
            batch_info = f"Part {i} of {len(batches)}"
            print(f"  Processing batch {i}/{len(batches)} ({len(batch)} chars)...")

            edited = self.copyedit_text(batch, context, batch_info)
            edited_batches.append(edited)

        # Combine batches
        result = '\n\n'.join(edited_batches)
        print(f"  ✓ Combined {len(batches)} batches into {len(result)} chars")

        return result

    def process_markdown_file(
        self,
        input_file: Path,
        output_file: Optional[Path] = None,
        in_place: bool = False
    ) -> None:
        """
        Process a markdown file, copyediting only the transcript section.

        Args:
            input_file: Path to input markdown file
            output_file: Path to output file
            in_place: Overwrite the input file
        """
        if output_file is None and not in_place:
            # Default: add _edited suffix
            stem = input_file.stem
            suffix = input_file.suffix
            output_file = input_file.parent / f"{stem}_edited{suffix}"
        elif in_place:
            output_file = input_file

        content = input_file.read_text(encoding='utf-8')

        # Extract metadata for context
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        channel_match = re.search(r'\*\*Channel:\*\*\s+(.+)$', content, re.MULTILINE)

        title = title_match.group(1) if title_match else "Unknown"
        channel = channel_match.group(1) if channel_match else "Unknown"
        context = f"Title: {title}, Channel: {channel}"

        print(f"\nProcessing: {title}")
        print(f"Model: {self.model}")
        print(f"File size: {len(content):,} characters")

        # Find the transcript section
        pattern = r'(##\s+Transcript\s*\n)(.*?)(?=\n##|\Z)'

        def replace_transcript(match):
            header = match.group(1)
            transcript = match.group(2).strip()

            if not transcript:
                return match.group(0)

            print(f"  Transcript section: {len(transcript):,} characters")

            try:
                # Use batching for long transcripts
                edited = self.copyedit_long_text(transcript, context)
                print(f"  ✓ Edited to {len(edited):,} characters")
                return header + '\n' + edited + '\n'
            except Exception as e:
                print(f"  ✗ Error: {e}")
                return match.group(0)

        # Replace the transcript section
        new_content = re.sub(pattern, replace_transcript, content, flags=re.DOTALL | re.IGNORECASE)

        # Write output
        output_file.write_text(new_content, encoding='utf-8')
        print(f"✓ Saved to: {output_file}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Copyedit transcripts using Claude API (with batching for long transcripts)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Set API key (required)
  export ANTHROPIC_API_KEY=your-api-key-here

  # Copyedit a single file
  python copyedit_with_claude.py transcript.md

  # Copyedit to a specific output file
  python copyedit_with_claude.py transcript.md -o edited.md

  # Copyedit in-place (overwrite original)
  python copyedit_with_claude.py transcript.md --in-place

  # Copyedit multiple files
  python copyedit_with_claude.py knowledge_base/transcripts/raw/*.md

  # Use a different model (Sonnet for higher quality)
  python copyedit_with_claude.py transcript.md --model claude-3-5-sonnet-20241022

Models:
  - claude-haiku-4-5-20251001 (default - Claude Haiku 4.5, fastest & cheapest)
  - claude-3-5-haiku-20241022 (Claude 3.5 Haiku, previous version)
  - claude-3-5-sonnet-20241022 (Claude 3.5 Sonnet, higher quality, more expensive)

Cost estimate (Claude Haiku 4.5):
  - Input: $1 per million tokens (~4M characters)
  - Output: $5 per million tokens
  - A 20-minute transcript (~5000 words) costs ~$0.02-0.05
  - A 90-minute transcript (~20,000 words) costs ~$0.10-0.20

Batching:
  - Automatically splits long transcripts into batches
  - Each batch processes independently to stay within context limits
  - Batches are seamlessly recombined
  - Progress shown for multi-batch processing
        """
    )

    parser.add_argument(
        'files',
        nargs='*',
        help='Markdown files to copyedit'
    )

    parser.add_argument(
        '-o', '--output',
        help='Output file (only for single file input)'
    )

    parser.add_argument(
        '--in-place',
        action='store_true',
        help='Overwrite input files'
    )

    parser.add_argument(
        '--model',
        default='claude-haiku-4-5-20251001',
        choices=[
            'claude-haiku-4-5-20251001',
            'claude-3-5-haiku-20241022',
            'claude-3-5-sonnet-20241022',
            'claude-3-opus-20240229'
        ],
        help='Claude model to use (default: Claude Haiku 4.5 for cost-effectiveness)'
    )

    parser.add_argument(
        '--api-key',
        help='Anthropic API key (or set ANTHROPIC_API_KEY env var)'
    )

    args = parser.parse_args()

    if not ANTHROPIC_AVAILABLE:
        print("\nError: anthropic package not installed")
        print("Install with: pip install anthropic")
        return 1

    if not args.files:
        parser.print_help()
        return 0

    # Check for API key
    api_key = args.api_key or os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("\nError: ANTHROPIC_API_KEY not set")
        print("\nSet it with:")
        print("  export ANTHROPIC_API_KEY=your-api-key-here")
        print("\nOr pass it as an argument:")
        print("  python copyedit_with_claude.py --api-key your-key-here file.md")
        return 1

    # Initialize copyeditor
    try:
        copyeditor = ClaudeCopyeditor(api_key=api_key, model=args.model)
        print(f"\nUsing model: {args.model}")
        print(f"Max batch size: ~{copyeditor.max_input_chars:,} characters\n")
    except Exception as e:
        print(f"\nError initializing Claude API: {e}")
        return 1

    # Process files
    for file_path in args.files:
        input_file = Path(file_path)

        if not input_file.exists():
            print(f"✗ File not found: {input_file}")
            continue

        # Determine output file
        if args.output and len(args.files) == 1:
            output_file = Path(args.output)
        else:
            output_file = None

        try:
            copyeditor.process_markdown_file(
                input_file,
                output_file=output_file,
                in_place=args.in_place
            )
        except Exception as e:
            print(f"✗ Error processing {input_file}: {e}")
            import traceback
            traceback.print_exc()
            continue

    print("\n✓ All done!")
    return 0


if __name__ == '__main__':
    exit(main())
