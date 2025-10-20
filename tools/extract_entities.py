#!/usr/bin/env python3
"""
Extract entities (thinkers, concepts, frameworks, institutions, questions) from transcripts.

Uses Claude API for intelligent entity extraction and categorization.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional
from anthropic import Anthropic
import os
import re


class EntityExtractor:
    """Extract structured entities from transcript text using Claude API."""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-haiku-4-5-20251001"):
        """Initialize with API key and model."""
        self.client = Anthropic(api_key=api_key or os.environ.get('ANTHROPIC_API_KEY'))
        self.model = model
        self.max_tokens = 4096

    def extract_from_transcript(self, transcript_path: Path, verbose: bool = False) -> Dict:
        """
        Extract entities from a single transcript.

        Returns:
            Dictionary with extracted entities by type
        """
        if verbose:
            print(f"📖 Reading transcript: {transcript_path.name}")

        content = transcript_path.read_text(encoding='utf-8')

        # Extract title from markdown
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        title = title_match.group(1) if title_match else transcript_path.stem

        # Extract just the transcript section (without metadata)
        transcript_match = re.search(
            r'##\s+Transcript\s*\n(.*?)(?=\n##|\Z)',
            content,
            flags=re.DOTALL | re.IGNORECASE
        )

        if transcript_match:
            transcript_text = transcript_match.group(1).strip()
        else:
            # Fallback: use everything after first heading
            parts = content.split('\n## ', 1)
            transcript_text = parts[1] if len(parts) > 1 else content

        # Limit length for API call (approx 100k chars = 25k tokens)
        if len(transcript_text) > 100000:
            if verbose:
                print(f"  ⚠️  Transcript is very long ({len(transcript_text):,} chars), truncating...")
            transcript_text = transcript_text[:100000]

        if verbose:
            print(f"  🤖 Extracting entities with Claude ({len(transcript_text):,} characters)...")

        # Call Claude to extract entities
        extraction_prompt = self._build_extraction_prompt(transcript_text, title)

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{
                    "role": "user",
                    "content": extraction_prompt
                }]
            )

            # Parse JSON response
            response_text = response.content[0].text

            # Extract JSON from potential markdown code blocks
            # Try to find JSON between triple backticks first
            json_match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(1)
            else:
                # Try to find JSON without code blocks
                # Look for content between first { and last }
                json_match = re.search(r'(\{.*\})', response_text, re.DOTALL)
                if json_match:
                    json_text = json_match.group(1)
                else:
                    json_text = response_text

            # Try to parse JSON
            try:
                entities = json.loads(json_text)
            except json.JSONDecodeError as json_err:
                # Save the problematic response for debugging
                debug_file = transcript_path.parent.parent / 'extractions' / f'{transcript_path.stem}_debug_response.txt'
                debug_file.parent.mkdir(parents=True, exist_ok=True)
                debug_file.write_text(
                    f"=== RAW RESPONSE ===\n{response_text}\n\n=== EXTRACTED JSON ===\n{json_text}",
                    encoding='utf-8'
                )
                print(f"  ⚠️  JSON parse error. Raw response saved to: {debug_file}", file=sys.stderr)
                print(f"  Error: {json_err}", file=sys.stderr)
                raise

            # Add metadata
            entities['_metadata'] = {
                'source_file': str(transcript_path),
                'title': title,
                'model': self.model,
                'extraction_date': self._get_timestamp()
            }

            if verbose:
                self._print_extraction_summary(entities)

            return entities

        except Exception as e:
            print(f"❌ Error extracting entities: {e}", file=sys.stderr)
            return {
                'thinkers': [],
                'concepts': [],
                'frameworks': [],
                'institutions': [],
                'questions': [],
                '_metadata': {
                    'source_file': str(transcript_path),
                    'title': title,
                    'error': str(e)
                }
            }

    def _build_extraction_prompt(self, transcript_text: str, title: str) -> str:
        """Build the extraction prompt for Claude."""
        return f"""Analyze this transcript and extract key entities for a knowledge base about Buddhism, AI, and consciousness.

Transcript title: {title}

Extract and categorize entities into these types:

1. **Thinkers** - People mentioned (full names, with context about their field)
2. **Concepts** - Important ideas, theories, or phenomena discussed
3. **Frameworks** - Named models, methodologies, or systematic approaches
4. **Institutions** - Organizations, research centers, universities, projects, monasteries
5. **Questions** - Significant open questions or research problems posed

Guidelines:
- Be selective: only extract entities that are clearly significant to the discussion
- Prefer full names over nicknames (e.g., "Michael Levin" not "Mike")
- For concepts, use standard terminology when possible
- Include brief context (1 sentence) for each entity
- Categorize concepts as: buddhist, cognitive, ai, or interdisciplinary
- If a category has no entities, return an empty array: []

IMPORTANT: Return ONLY valid JSON. Do not include any text before or after the JSON.
Return the JSON in this exact format:

```json
{{
  "thinkers": [
    {{
      "name": "Full Name",
      "aliases": ["Alternative Name"],
      "domains": ["Domain 1", "Domain 2"],
      "context": "Brief description of their relevance"
    }}
  ],
  "concepts": [
    {{
      "name": "Concept Name",
      "aliases": ["Alternative Term"],
      "category": "buddhist|cognitive|ai|interdisciplinary",
      "context": "Brief description"
    }}
  ],
  "frameworks": [
    {{
      "name": "Framework Name",
      "creator": "Creator Name or null",
      "context": "Brief description"
    }}
  ],
  "institutions": [
    {{
      "name": "Institution Name",
      "type": "research-center|monastery|university|project",
      "context": "Brief description"
    }}
  ],
  "questions": [
    {{
      "question": "The question text?",
      "category": "alignment|ethics|metaphysics|epistemology|other",
      "context": "Why this question matters"
    }}
  ]
}}
```

Transcript:

{transcript_text}

Return only the JSON, no additional commentary."""

    def _print_extraction_summary(self, entities: Dict) -> None:
        """Print a summary of extracted entities."""
        print(f"  ✓ Extracted:")
        print(f"    • {len(entities.get('thinkers', []))} thinkers")
        print(f"    • {len(entities.get('concepts', []))} concepts")
        print(f"    • {len(entities.get('frameworks', []))} frameworks")
        print(f"    • {len(entities.get('institutions', []))} institutions")
        print(f"    • {len(entities.get('questions', []))} questions")

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

    def save_extraction(self, entities: Dict, output_path: Path) -> None:
        """Save extracted entities to JSON file."""
        output_path.write_text(json.dumps(entities, indent=2, ensure_ascii=False), encoding='utf-8')
        print(f"💾 Saved extraction to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Extract entities from transcripts using Claude API"
    )
    parser.add_argument(
        'transcripts',
        nargs='+',
        type=Path,
        help='Transcript markdown files to process'
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('knowledge_base/extractions'),
        help='Directory for extraction JSON files (default: knowledge_base/extractions)'
    )
    parser.add_argument(
        '--api-key',
        help='Anthropic API key (or set ANTHROPIC_API_KEY env var)'
    )
    parser.add_argument(
        '--model',
        default='claude-haiku-4-5-20251001',
        help='Claude model to use (default: claude-haiku-4-5-20251001)'
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Verbose output'
    )

    args = parser.parse_args()

    # Check API key
    api_key = args.api_key or os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ Error: No API key provided.", file=sys.stderr)
        print("Set ANTHROPIC_API_KEY environment variable or use --api-key", file=sys.stderr)
        sys.exit(1)

    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize extractor
    extractor = EntityExtractor(api_key=api_key, model=args.model)

    print(f"🔍 Extracting entities from {len(args.transcripts)} transcript(s)...")
    print(f"📁 Output directory: {args.output_dir}")
    print()

    # Process each transcript
    for transcript_path in args.transcripts:
        if not transcript_path.exists():
            print(f"⚠️  File not found: {transcript_path}", file=sys.stderr)
            continue

        # Extract entities
        entities = extractor.extract_from_transcript(transcript_path, verbose=args.verbose)

        # Save to output directory
        output_filename = transcript_path.stem + '_entities.json'
        output_path = args.output_dir / output_filename
        extractor.save_extraction(entities, output_path)
        print()

    print("✅ Entity extraction complete!")
    print(f"\nNext steps:")
    print(f"  1. Review extractions in: {args.output_dir}")
    print(f"  2. Normalize names: python tools/normalize_entities.py")
    print(f"  3. Create entity pages: python tools/populate_entities.py")


if __name__ == '__main__':
    main()
