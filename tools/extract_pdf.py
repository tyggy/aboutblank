#!/usr/bin/env python3
"""
Extract text from research papers (PDF format).

Converts PDFs to cleaned markdown text suitable for entity extraction.
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Optional

try:
    import fitz  # PyMuPDF
except ImportError:
    print("❌ Error: PyMuPDF not installed. Install with: pip install pymupdf", file=sys.stderr)
    sys.exit(1)


class PDFExtractor:
    """Extract and clean text from PDF files."""

    def __init__(self, papers_dir: Path):
        """
        Initialize PDF extractor.

        Args:
            papers_dir: Directory for processed papers (knowledge_base/papers)
        """
        self.papers_dir = papers_dir
        self.papers_dir.mkdir(parents=True, exist_ok=True)

    def extract_pdf(self, pdf_path: Path, output_path: Optional[Path] = None, verbose: bool = False) -> Path:
        """
        Extract text from PDF file.

        Args:
            pdf_path: Path to PDF file
            output_path: Optional output path (default: papers/cleaned/filename.md)
            verbose: Print progress information

        Returns:
            Path to output markdown file
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        if verbose:
            print(f"📄 Extracting: {pdf_path.name}")

        # Default output path
        if output_path is None:
            cleaned_dir = self.papers_dir / 'cleaned'
            cleaned_dir.mkdir(parents=True, exist_ok=True)
            output_path = cleaned_dir / f"{pdf_path.stem}.md"

        # Extract text from PDF
        try:
            doc = fitz.open(pdf_path)
            text_blocks = []

            for page_num, page in enumerate(doc, 1):
                if verbose and page_num % 10 == 0:
                    print(f"  Processing page {page_num}/{len(doc)}...")

                # Extract text from page
                text = page.get_text("text")
                text_blocks.append(text)

            doc.close()

            # Combine all text
            full_text = "\n\n".join(text_blocks)

        except Exception as e:
            raise RuntimeError(f"Failed to extract PDF: {e}")

        # Clean and format the text
        cleaned_text = self._clean_text(full_text)

        # Add metadata header
        title = self._extract_title(cleaned_text, pdf_path)
        formatted_text = self._format_output(title, cleaned_text, pdf_path)

        # Write output
        output_path.write_text(formatted_text, encoding='utf-8')

        if verbose:
            print(f"  ✓ Saved to: {output_path}")
            print(f"  📊 {len(full_text):,} chars → {len(cleaned_text):,} chars (cleaned)")

        return output_path

    def _clean_text(self, text: str) -> str:
        """Clean extracted PDF text."""
        # Remove excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' +', ' ', text)

        # Fix hyphenated words split across lines
        text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)

        # Remove page headers/footers (common patterns)
        # This is a heuristic - adjust as needed
        lines = text.split('\n')
        cleaned_lines = []

        for line in lines:
            # Skip lines that look like page numbers
            if re.match(r'^\s*\d+\s*$', line):
                continue
            # Skip very short lines at start/end of paragraphs (likely headers/footers)
            # But keep them if they're part of a list or heading
            cleaned_lines.append(line)

        text = '\n'.join(cleaned_lines)

        # Normalize quotes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")

        return text.strip()

    def _extract_title(self, text: str, pdf_path: Path) -> str:
        """Extract paper title from text or use filename."""
        # Try to extract title from first few lines
        lines = [l.strip() for l in text.split('\n') if l.strip()]

        if lines:
            # Assume first substantial line is the title
            # (more than 10 chars, not all caps, not a page number)
            for line in lines[:5]:
                if len(line) > 10 and not line.isupper() and not re.match(r'^\d+$', line):
                    return line

        # Fallback to filename
        return pdf_path.stem.replace('-', ' ').replace('_', ' ').title()

    def _format_output(self, title: str, text: str, pdf_path: Path) -> str:
        """Format output with metadata."""
        return f"""---
type: paper
source: {pdf_path.name}
format: pdf
processed: true
---

# {title}

{text}
"""

    def batch_extract(self, pdf_dir: Path, verbose: bool = False) -> list[Path]:
        """
        Extract all PDFs from a directory.

        Args:
            pdf_dir: Directory containing PDF files
            verbose: Print progress information

        Returns:
            List of output file paths
        """
        pdf_files = list(pdf_dir.glob('*.pdf'))

        if not pdf_files:
            print(f"⚠️  No PDF files found in: {pdf_dir}", file=sys.stderr)
            return []

        if verbose:
            print(f"📚 Found {len(pdf_files)} PDF(s) to process")
            print()

        output_paths = []

        for pdf_path in pdf_files:
            try:
                output_path = self.extract_pdf(pdf_path, verbose=verbose)
                output_paths.append(output_path)
            except Exception as e:
                print(f"❌ Error processing {pdf_path.name}: {e}", file=sys.stderr)

        if verbose:
            print()
            print(f"✅ Processed {len(output_paths)}/{len(pdf_files)} PDF(s)")

        return output_paths


def main():
    parser = argparse.ArgumentParser(
        description="Extract text from research papers (PDF format)"
    )
    parser.add_argument(
        'input',
        type=Path,
        help='PDF file or directory containing PDFs'
    )
    parser.add_argument(
        '--output',
        '-o',
        type=Path,
        help='Output file or directory (default: knowledge_base/papers/cleaned/)'
    )
    parser.add_argument(
        '--papers-dir',
        type=Path,
        default=Path('knowledge_base/papers'),
        help='Papers directory (default: knowledge_base/papers)'
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Verbose output'
    )

    args = parser.parse_args()

    # Initialize extractor
    extractor = PDFExtractor(args.papers_dir)

    print("📄 PDF Text Extraction")
    print(f"📁 Papers directory: {args.papers_dir}")
    print()

    # Process input
    if args.input.is_file():
        # Single file
        try:
            output_path = extractor.extract_pdf(args.input, args.output, verbose=args.verbose)
            print()
            print(f"✅ Extraction complete!")
            print(f"📄 Output: {output_path}")
        except Exception as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.input.is_dir():
        # Batch processing
        output_paths = extractor.batch_extract(args.input, verbose=args.verbose)

        if output_paths:
            print()
            print("✅ Batch extraction complete!")
            print(f"📁 Output directory: {output_paths[0].parent}")
        else:
            sys.exit(1)

    else:
        print(f"❌ Error: Path not found: {args.input}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
