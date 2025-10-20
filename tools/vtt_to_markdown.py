#!/usr/bin/env python3
"""
VTT/SRT to Markdown Converter
Converts subtitle files to clean, readable markdown format.
"""

import re
from pathlib import Path
from typing import List, Tuple


class SubtitleConverter:
    """Converts VTT and SRT subtitle files to clean markdown."""

    def __init__(self):
        self.vtt_timestamp_pattern = re.compile(r'^\d{2}:\d{2}:\d{2}\.\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}\.\d{3}')
        self.srt_timestamp_pattern = re.compile(r'^\d{2}:\d{2}:\d{2},\d{3}\s*-->\s*\d{2}:\d{2}:\d{2},\d{3}')
        self.srt_number_pattern = re.compile(r'^\d+$')
        self.speaker_pattern = re.compile(r'^<v\s+([^>]+)>')

    def parse_vtt(self, content: str) -> List[str]:
        """Parse VTT subtitle file and extract text chunks."""
        lines = content.split('\n')
        text_chunks = []
        current_text = []

        for line in lines:
            line = line.strip()

            # Skip VTT header, timestamps, and empty lines
            if (line.startswith('WEBVTT') or
                line.startswith('Kind:') or
                line.startswith('Language:') or
                self.vtt_timestamp_pattern.match(line) or
                not line):

                # Save accumulated text
                if current_text:
                    text_chunks.append(' '.join(current_text))
                    current_text = []
                continue

            # Extract speaker if present
            speaker_match = self.speaker_pattern.search(line)
            if speaker_match:
                line = self.speaker_pattern.sub('', line)

            # Remove VTT tags like <c>, </c>
            line = re.sub(r'</?c[^>]*>', '', line)
            line = re.sub(r'</?v[^>]*>', '', line)

            if line:
                current_text.append(line)

        # Save any remaining text
        if current_text:
            text_chunks.append(' '.join(current_text))

        return text_chunks

    def parse_srt(self, content: str) -> List[str]:
        """Parse SRT subtitle file and extract text chunks."""
        lines = content.split('\n')
        text_chunks = []
        current_text = []

        for line in lines:
            line = line.strip()

            # Skip subtitle numbers, timestamps, and empty lines
            if (self.srt_number_pattern.match(line) or
                self.srt_timestamp_pattern.match(line) or
                not line):

                # Save accumulated text
                if current_text:
                    text_chunks.append(' '.join(current_text))
                    current_text = []
                continue

            # Remove SRT tags
            line = re.sub(r'</?[^>]+>', '', line)

            if line:
                current_text.append(line)

        # Save any remaining text
        if current_text:
            text_chunks.append(' '.join(current_text))

        return text_chunks

    def merge_chunks(self, chunks: List[str], min_sentence_length: int = 50) -> List[str]:
        """
        Merge short subtitle chunks into proper sentences/paragraphs.

        Args:
            chunks: List of text chunks from subtitles
            min_sentence_length: Minimum length before considering a new paragraph

        Returns:
            List of merged paragraphs
        """
        if not chunks:
            return []

        paragraphs = []
        current_paragraph = []
        current_length = 0

        for chunk in chunks:
            # Clean up the chunk
            chunk = chunk.strip()
            if not chunk:
                continue

            # Remove duplicate words at boundaries (common in subtitles)
            if current_paragraph:
                last_words = current_paragraph[-1].split()[-3:]
                first_words = chunk.split()[:3]

                # Check for overlap
                for i in range(min(len(last_words), len(first_words)), 0, -1):
                    if last_words[-i:] == first_words[:i]:
                        # Remove duplicate from chunk
                        chunk_words = chunk.split()[i:]
                        chunk = ' '.join(chunk_words)
                        break

            current_paragraph.append(chunk)
            current_length += len(chunk)

            # Check if we should start a new paragraph
            # (sentence ends with period/question/exclamation and we have enough text)
            if (chunk.endswith(('.', '!', '?')) and
                current_length >= min_sentence_length):

                paragraphs.append(' '.join(current_paragraph))
                current_paragraph = []
                current_length = 0

        # Add any remaining text
        if current_paragraph:
            paragraphs.append(' '.join(current_paragraph))

        return paragraphs

    def clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)

        # Fix spacing around punctuation
        text = re.sub(r'\s+([.,!?;:])', r'\1', text)
        text = re.sub(r'([.,!?;:])\s*', r'\1 ', text)

        # Remove music notes and sound effects often in subtitles
        text = re.sub(r'[\u266A\u266B]', '', text)
        text = re.sub(r'\[.*?\]', '', text)
        text = re.sub(r'\(.*?\)', '', text)

        # Clean up multiple punctuation
        text = re.sub(r'\.{2,}', '...', text)
        text = re.sub(r'\s+', ' ', text)

        return text.strip()

    def convert_to_markdown(self, subtitle_file: Path) -> str:
        """
        Convert a subtitle file (VTT or SRT) to markdown format.

        Args:
            subtitle_file: Path to subtitle file

        Returns:
            Formatted markdown text
        """
        content = subtitle_file.read_text(encoding='utf-8')

        # Determine file type and parse
        if subtitle_file.suffix.lower() == '.vtt':
            chunks = self.parse_vtt(content)
        elif subtitle_file.suffix.lower() == '.srt':
            chunks = self.parse_srt(content)
        else:
            raise ValueError(f"Unsupported subtitle format: {subtitle_file.suffix}")

        # Merge chunks into paragraphs
        paragraphs = self.merge_chunks(chunks)

        # Clean each paragraph
        paragraphs = [self.clean_text(p) for p in paragraphs if p.strip()]

        # Join into markdown with double newlines between paragraphs
        markdown = '\n\n'.join(paragraphs)

        return markdown


def convert_subtitle_to_markdown(subtitle_file: Path) -> str:
    """
    Convenience function to convert a subtitle file to markdown.

    Args:
        subtitle_file: Path to VTT or SRT file

    Returns:
        Formatted markdown text
    """
    converter = SubtitleConverter()
    return converter.convert_to_markdown(subtitle_file)


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python vtt_to_markdown.py <subtitle_file>")
        sys.exit(1)

    subtitle_path = Path(sys.argv[1])
    if not subtitle_path.exists():
        print(f"Error: File not found: {subtitle_path}")
        sys.exit(1)

    try:
        markdown = convert_subtitle_to_markdown(subtitle_path)
        print(markdown)
    except Exception as e:
        print(f"Error converting subtitle: {e}")
        sys.exit(1)
