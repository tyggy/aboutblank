#!/usr/bin/env python3
"""
Normalize and deduplicate extracted entities.

Merges entities from multiple extraction files, performs fuzzy matching
against existing knowledge base, and creates a normalized entity database.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from difflib import SequenceMatcher
from collections import defaultdict


class EntityNormalizer:
    """Normalize entity names and merge duplicates."""

    def __init__(self, knowledge_base_dir: Path, similarity_threshold: float = 0.85):
        """
        Initialize normalizer.

        Args:
            knowledge_base_dir: Root directory of knowledge base
            similarity_threshold: Minimum similarity (0-1) to consider entities the same
        """
        self.kb_dir = knowledge_base_dir
        self.similarity_threshold = similarity_threshold

        # Load existing entities from knowledge base
        self.existing_thinkers = self._load_existing_entities('thinkers')
        self.existing_concepts = self._load_existing_entities('concepts')
        self.existing_frameworks = self._load_existing_entities('frameworks')
        self.existing_institutions = self._load_existing_entities('institutions')

    def _load_existing_entities(self, entity_type: str) -> Dict[str, Dict]:
        """Load existing entities of a type from knowledge base."""
        entities = {}
        entity_dir = self.kb_dir / entity_type

        if not entity_dir.exists():
            return entities

        # Search through all subdirectories
        for md_file in entity_dir.rglob('*.md'):
            # Skip templates
            if '_templates' in md_file.parts:
                continue

            try:
                content = md_file.read_text(encoding='utf-8')

                # Extract frontmatter and title
                frontmatter_match = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
                title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)

                if title_match:
                    name = title_match.group(1).strip()
                    aliases = []

                    # Parse aliases from frontmatter
                    if frontmatter_match:
                        fm_text = frontmatter_match.group(1)
                        aliases_match = re.search(r'aliases:\s*\[(.*?)\]', fm_text)
                        if aliases_match:
                            aliases_text = aliases_match.group(1)
                            aliases = [a.strip().strip('"\'') for a in aliases_text.split(',') if a.strip()]

                    entities[name] = {
                        'name': name,
                        'file_path': str(md_file.relative_to(self.kb_dir)),
                        'aliases': aliases
                    }

            except Exception as e:
                print(f"⚠️  Error loading {md_file}: {e}", file=sys.stderr)

        return entities

    def normalize_thinker_name(self, name: str) -> Tuple[str, str]:
        """
        Normalize a thinker's name.

        Returns:
            (display_name, filename)
        """
        # Clean up the name
        name = name.strip()
        name = re.sub(r'\s+', ' ', name)  # Normalize whitespace

        # Handle common patterns
        # "Last, First" -> "First Last"
        if ',' in name:
            parts = [p.strip() for p in name.split(',')]
            if len(parts) == 2:
                name = f"{parts[1]} {parts[0]}"

        # Display name keeps normal capitalization
        display_name = name

        # Filename: lowercase with hyphens
        filename = name.lower().replace(' ', '-')
        filename = re.sub(r'[^a-z0-9-]', '', filename)  # Remove special chars

        return display_name, filename

    def normalize_concept_name(self, name: str) -> Tuple[str, str]:
        """
        Normalize a concept name.

        Returns:
            (display_name, filename)
        """
        # Clean up
        name = name.strip()
        name = re.sub(r'\s+', ' ', name)

        # Display name: Title Case for multi-word, capitalize for single word
        display_name = name.title()

        # Filename: lowercase with hyphens
        filename = name.lower().replace(' ', '-')
        filename = re.sub(r'[^a-z0-9-]', '', filename)

        return display_name, filename

    def similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity ratio between two strings (0-1)."""
        # Normalize for comparison
        s1 = str1.lower().strip()
        s2 = str2.lower().strip()

        # Exact match
        if s1 == s2:
            return 1.0

        # Use SequenceMatcher for fuzzy matching
        return SequenceMatcher(None, s1, s2).ratio()

    def find_best_match(
        self,
        entity_name: str,
        existing_entities: Dict[str, Dict],
        aliases: List[str] = None
    ) -> Tuple[Optional[str], float]:
        """
        Find best match for entity in existing database.

        Returns:
            (matched_name, similarity_score) or (None, 0.0)
        """
        best_match = None
        best_score = 0.0

        # Check against all existing entities and their aliases
        for existing_name, entity_data in existing_entities.items():
            # Check main name
            score = self.similarity(entity_name, existing_name)
            if score > best_score:
                best_score = score
                best_match = existing_name

            # Check aliases
            for alias in entity_data.get('aliases', []):
                score = self.similarity(entity_name, alias)
                if score > best_score:
                    best_score = score
                    best_match = existing_name

        # Also check if any of the new entity's aliases match
        if aliases:
            for alias in aliases:
                for existing_name, entity_data in existing_entities.items():
                    score = self.similarity(alias, existing_name)
                    if score > best_score:
                        best_score = score
                        best_match = existing_name

        # Only return match if above threshold
        if best_score >= self.similarity_threshold:
            return best_match, best_score

        return None, 0.0

    def save_entities(self, normalized: Dict, entities_dir: Path, verbose: bool = False) -> Dict:
        """
        Save normalized entities as individual JSON files.

        Args:
            normalized: Dictionary with entity type keys and lists of entities
            entities_dir: Base directory for entities (e.g., knowledge_base/entities)
            verbose: Print progress

        Returns:
            Dictionary with counts of saved entities by type
        """
        import datetime

        stats = {}

        for entity_type, entities in normalized.items():
            type_dir = entities_dir / entity_type
            type_dir.mkdir(parents=True, exist_ok=True)

            if verbose:
                print(f"💾 Saving {entity_type}...")

            for entity in entities:
                # Get filename (already normalized)
                filename = entity.get('filename', '')
                if not filename:
                    # Fallback: create from name
                    name = entity.get('name', entity.get('question', 'unknown'))
                    filename = re.sub(r'[^a-z0-9\s]', '', name.lower())
                    filename = '-'.join(filename.split())

                # Add metadata
                entity_data = entity.copy()
                entity_data['_metadata'] = {
                    'entity_type': entity_type.rstrip('s'),  # singular form
                    'last_updated': datetime.datetime.now().isoformat(),
                    'sources_count': len(entity.get('sources', [])),
                    'contexts_count': len(entity.get('contexts', [])) if 'contexts' in entity else (1 if entity.get('context') else 0)
                }

                # Write individual JSON file
                json_path = type_dir / f"{filename}.json"
                json_path.write_text(
                    json.dumps(entity_data, indent=2, ensure_ascii=False),
                    encoding='utf-8'
                )

            stats[entity_type] = len(entities)

            if verbose:
                print(f"  ✓ {len(entities)} {entity_type} saved")

        return stats

    def merge_extractions(self, extraction_files: List[Path], verbose: bool = False) -> Dict:
        """
        Merge multiple extraction files into normalized database.

        Returns:
            Normalized entities dictionary
        """
        if verbose:
            print("🔄 Merging extraction files...")
            print()

        # Collect all entities by type
        all_thinkers = []
        all_concepts = []
        all_frameworks = []
        all_institutions = []
        all_questions = []

        for extraction_file in extraction_files:
            if not extraction_file.exists():
                print(f"⚠️  File not found: {extraction_file}", file=sys.stderr)
                continue

            if verbose:
                print(f"📖 Loading: {extraction_file.name}")

            try:
                data = json.loads(extraction_file.read_text(encoding='utf-8'))
                source_file = data.get('_metadata', {}).get('source_file', str(extraction_file))

                # Add source tracking to each entity
                for thinker in data.get('thinkers', []):
                    thinker['_source'] = source_file
                    all_thinkers.append(thinker)
                for concept in data.get('concepts', []):
                    concept['_source'] = source_file
                    all_concepts.append(concept)
                for framework in data.get('frameworks', []):
                    framework['_source'] = source_file
                    all_frameworks.append(framework)
                for institution in data.get('institutions', []):
                    institution['_source'] = source_file
                    all_institutions.append(institution)
                for question in data.get('questions', []):
                    question['_source'] = source_file
                    all_questions.append(question)
            except Exception as e:
                print(f"❌ Error loading {extraction_file}: {e}", file=sys.stderr)

        if verbose:
            print()
            print(f"📊 Total extracted:")
            print(f"   • {len(all_thinkers)} thinkers")
            print(f"   • {len(all_concepts)} concepts")
            print(f"   • {len(all_frameworks)} frameworks")
            print(f"   • {len(all_institutions)} institutions")
            print(f"   • {len(all_questions)} questions")
            print()

        # Normalize and deduplicate each type
        normalized = {
            'thinkers': self._normalize_thinkers(all_thinkers, verbose),
            'concepts': self._normalize_concepts(all_concepts, verbose),
            'frameworks': self._normalize_frameworks(all_frameworks, verbose),
            'institutions': self._normalize_institutions(all_institutions, verbose),
            'questions': self._normalize_questions(all_questions, verbose)
        }

        return normalized

    def _normalize_thinkers(self, thinkers: List[Dict], verbose: bool) -> List[Dict]:
        """Normalize and deduplicate thinkers."""
        if verbose:
            print("👤 Normalizing thinkers...")

        normalized = []
        seen = {}  # normalized_name -> entity

        for thinker in thinkers:
            name = thinker.get('name', '').strip()
            if not name:
                continue

            aliases = thinker.get('aliases', [])
            source = thinker.get('_source', '')

            # Normalize name
            display_name, filename = self.normalize_thinker_name(name)

            # Check for existing match
            existing_match, score = self.find_best_match(name, self.existing_thinkers, aliases)

            if existing_match:
                if verbose:
                    print(f"  🔗 Matched '{name}' → existing '{existing_match}' (score: {score:.2f})")
                # Use existing entity data
                entity = self.existing_thinkers[existing_match].copy()
                entity['extracted_as'] = name
                entity['match_score'] = score
                normalized_key = existing_match
            else:
                # Check for duplicate in current extraction
                if display_name in seen:
                    # Merge with existing - aggregate all information
                    if verbose:
                        print(f"  🔀 Merging duplicate: '{name}'")

                    # Merge aliases
                    seen[display_name]['aliases'].extend(aliases)
                    seen[display_name]['aliases'] = list(set(seen[display_name]['aliases']))

                    # Merge domains (unique)
                    existing_domains = set(seen[display_name].get('domains', []))
                    new_domains = set(thinker.get('domains', []))
                    seen[display_name]['domains'] = list(existing_domains | new_domains)

                    # Aggregate contexts with source attribution
                    new_context = thinker.get('context', '').strip()
                    if new_context:
                        if 'contexts' not in seen[display_name]:
                            # Convert single context to list format
                            old_context = seen[display_name].get('context', '').strip()
                            old_source = seen[display_name].get('sources', [None])[0]
                            seen[display_name]['contexts'] = []
                            if old_context:
                                seen[display_name]['contexts'].append({
                                    'source': old_source,
                                    'text': old_context
                                })

                        # Add new context if different
                        existing_texts = [c['text'] for c in seen[display_name]['contexts']]
                        if new_context not in existing_texts:
                            seen[display_name]['contexts'].append({
                                'source': source,
                                'text': new_context
                            })

                    # Track sources
                    if source and source not in seen[display_name].get('sources', []):
                        seen[display_name].setdefault('sources', []).append(source)

                    continue
                else:
                    # New entity
                    entity = {
                        'name': display_name,
                        'filename': filename,
                        'aliases': aliases,
                        'domains': thinker.get('domains', []),
                        'context': thinker.get('context', ''),
                        'sources': [source] if source else [],
                        'is_new': True
                    }
                    normalized_key = display_name

            # Add source to entity
            if source:
                if 'sources' not in entity:
                    entity['sources'] = []
                if source not in entity['sources']:
                    entity['sources'].append(source)

            seen[normalized_key] = entity

        normalized = list(seen.values())

        if verbose:
            new_count = sum(1 for e in normalized if e.get('is_new'))
            print(f"  ✓ {len(normalized)} unique thinkers ({new_count} new, {len(normalized) - new_count} existing)")
            print()

        return normalized

    def _normalize_concepts(self, concepts: List[Dict], verbose: bool) -> List[Dict]:
        """Normalize and deduplicate concepts."""
        if verbose:
            print("💡 Normalizing concepts...")

        normalized = []
        seen = {}

        for concept in concepts:
            name = concept.get('name', '').strip()
            if not name:
                continue

            aliases = concept.get('aliases', [])
            source = concept.get('_source', '')
            display_name, filename = self.normalize_concept_name(name)

            # First, check against existing KB entities
            existing_match, score = self.find_best_match(name, self.existing_concepts, aliases)

            if existing_match:
                if verbose:
                    print(f"  🔗 Matched '{name}' → existing '{existing_match}' (score: {score:.2f})")
                entity = self.existing_concepts[existing_match].copy()
                entity['extracted_as'] = name
                entity['match_score'] = score
                normalized_key = existing_match
            else:
                # Check for fuzzy match against new entities in current batch
                seen_match, seen_score = self.find_best_match(name, {
                    key: {'name': key, 'aliases': seen[key].get('aliases', [])} for key in seen.keys()
                }, aliases)

                if seen_match:
                    if verbose:
                        print(f"  🔀 Merging duplicate: '{name}' → '{seen_match}' (score: {seen_score:.2f})")

                    # Merge aliases
                    seen[seen_match]['aliases'].extend(aliases)
                    seen[seen_match]['aliases'] = list(set(seen[seen_match]['aliases']))

                    # Aggregate contexts with source attribution
                    new_context = concept.get('context', '').strip()
                    if new_context:
                        if 'contexts' not in seen[seen_match]:
                            # Convert single context to list format
                            old_context = seen[seen_match].get('context', '').strip()
                            old_source = seen[seen_match].get('sources', [None])[0]
                            seen[seen_match]['contexts'] = []
                            if old_context:
                                seen[seen_match]['contexts'].append({
                                    'source': old_source,
                                    'text': old_context
                                })

                        # Add new context if different
                        existing_texts = [c['text'] for c in seen[seen_match]['contexts']]
                        if new_context not in existing_texts:
                            seen[seen_match]['contexts'].append({
                                'source': source,
                                'text': new_context
                            })

                    # Track sources
                    if source and source not in seen[seen_match].get('sources', []):
                        seen[seen_match].setdefault('sources', []).append(source)

                    continue
                else:
                    entity = {
                        'name': display_name,
                        'filename': filename,
                        'aliases': aliases,
                        'category': concept.get('category', 'interdisciplinary'),
                        'context': concept.get('context', ''),
                        'sources': [source] if source else [],
                        'is_new': True
                    }
                    normalized_key = display_name

            # Add source to entity
            if source:
                if 'sources' not in entity:
                    entity['sources'] = []
                if source not in entity['sources']:
                    entity['sources'].append(source)

            seen[normalized_key] = entity

        normalized = list(seen.values())

        if verbose:
            new_count = sum(1 for e in normalized if e.get('is_new'))
            print(f"  ✓ {len(normalized)} unique concepts ({new_count} new, {len(normalized) - new_count} existing)")
            print()

        return normalized

    def _normalize_frameworks(self, frameworks: List[Dict], verbose: bool) -> List[Dict]:
        """Normalize and deduplicate frameworks."""
        if verbose:
            print("🔧 Normalizing frameworks...")

        normalized = []
        seen = {}

        for framework in frameworks:
            name = framework.get('name', '').strip()
            if not name:
                continue

            source = framework.get('_source', '')
            display_name, filename = self.normalize_concept_name(name)

            # First, check against existing KB entities
            existing_match, score = self.find_best_match(name, self.existing_frameworks)

            if existing_match:
                if verbose:
                    print(f"  🔗 Matched '{name}' → existing '{existing_match}' (score: {score:.2f})")
                entity = self.existing_frameworks[existing_match].copy()
                entity['extracted_as'] = name
                entity['match_score'] = score
                normalized_key = existing_match
            else:
                # Check for fuzzy match against new entities in current batch
                seen_match, seen_score = self.find_best_match(name, {
                    key: {'name': key, 'aliases': []} for key in seen.keys()
                })

                if seen_match:
                    if verbose:
                        print(f"  🔀 Merging duplicate: '{name}' → '{seen_match}' (score: {seen_score:.2f})")

                    # Aggregate contexts with source attribution
                    new_context = framework.get('context', '').strip()
                    if new_context:
                        if 'contexts' not in seen[seen_match]:
                            # Convert single context to list format
                            old_context = seen[seen_match].get('context', '').strip()
                            old_source = seen[seen_match].get('sources', [None])[0]
                            seen[seen_match]['contexts'] = []
                            if old_context:
                                seen[seen_match]['contexts'].append({
                                    'source': old_source,
                                    'text': old_context
                                })

                        # Add new context if different
                        existing_texts = [c['text'] for c in seen[seen_match]['contexts']]
                        if new_context not in existing_texts:
                            seen[seen_match]['contexts'].append({
                                'source': source,
                                'text': new_context
                            })

                    # Track sources
                    if source and source not in seen[seen_match].get('sources', []):
                        seen[seen_match].setdefault('sources', []).append(source)

                    continue
                else:
                    entity = {
                        'name': display_name,
                        'filename': filename,
                        'creator': framework.get('creator'),
                        'context': framework.get('context', ''),
                        'sources': [source] if source else [],
                        'is_new': True
                    }
                    normalized_key = display_name

            # Add source to entity
            if source:
                if 'sources' not in entity:
                    entity['sources'] = []
                if source not in entity['sources']:
                    entity['sources'].append(source)

            seen[normalized_key] = entity

        normalized = list(seen.values())

        if verbose:
            new_count = sum(1 for e in normalized if e.get('is_new'))
            print(f"  ✓ {len(normalized)} unique frameworks ({new_count} new, {len(normalized) - new_count} existing)")
            print()

        return normalized

    def _normalize_institutions(self, institutions: List[Dict], verbose: bool) -> List[Dict]:
        """Normalize and deduplicate institutions."""
        if verbose:
            print("🏛️  Normalizing institutions...")

        normalized = []
        seen = {}

        for institution in institutions:
            name = institution.get('name', '').strip()
            if not name:
                continue

            source = institution.get('_source', '')
            display_name, filename = self.normalize_concept_name(name)

            # First, check against existing KB entities
            existing_match, score = self.find_best_match(name, self.existing_institutions)

            if existing_match:
                if verbose:
                    print(f"  🔗 Matched '{name}' → existing '{existing_match}' (score: {score:.2f})")
                entity = self.existing_institutions[existing_match].copy()
                entity['extracted_as'] = name
                entity['match_score'] = score
                normalized_key = existing_match
            else:
                # Check for fuzzy match against new entities in current batch
                seen_match, seen_score = self.find_best_match(name, {
                    key: {'name': key, 'aliases': []} for key in seen.keys()
                })

                if seen_match:
                    if verbose:
                        print(f"  🔀 Merging duplicate: '{name}' → '{seen_match}' (score: {seen_score:.2f})")

                    # Aggregate contexts with source attribution
                    new_context = institution.get('context', '').strip()
                    if new_context:
                        if 'contexts' not in seen[seen_match]:
                            # Convert single context to list format
                            old_context = seen[seen_match].get('context', '').strip()
                            old_source = seen[seen_match].get('sources', [None])[0]
                            seen[seen_match]['contexts'] = []
                            if old_context:
                                seen[seen_match]['contexts'].append({
                                    'source': old_source,
                                    'text': old_context
                                })

                        # Add new context if different
                        existing_texts = [c['text'] for c in seen[seen_match]['contexts']]
                        if new_context not in existing_texts:
                            seen[seen_match]['contexts'].append({
                                'source': source,
                                'text': new_context
                            })

                    # Track sources
                    if source and source not in seen[seen_match].get('sources', []):
                        seen[seen_match].setdefault('sources', []).append(source)

                    continue
                else:
                    entity = {
                        'name': display_name,
                        'filename': filename,
                        'type': institution.get('type', 'organization'),
                        'context': institution.get('context', ''),
                        'sources': [source] if source else [],
                        'is_new': True
                    }
                    normalized_key = display_name

            # Add source to entity
            if source:
                if 'sources' not in entity:
                    entity['sources'] = []
                if source not in entity['sources']:
                    entity['sources'].append(source)

            seen[normalized_key] = entity

        normalized = list(seen.values())

        if verbose:
            new_count = sum(1 for e in normalized if e.get('is_new'))
            print(f"  ✓ {len(normalized)} unique institutions ({new_count} new, {len(normalized) - new_count} existing)")
            print()

        return normalized

    def _normalize_questions(self, questions: List[Dict], verbose: bool) -> List[Dict]:
        """Normalize and deduplicate questions."""
        if verbose:
            print("❓ Normalizing questions...")

        normalized = []
        seen = set()

        for question in questions:
            q_text = question.get('question', '').strip()
            if not q_text:
                continue

            # Use question text as key for deduplication
            q_normalized = q_text.lower().strip('?. ')

            # Check for very similar questions
            is_duplicate = False
            for seen_q in seen:
                if self.similarity(q_normalized, seen_q) > 0.9:
                    is_duplicate = True
                    break

            if not is_duplicate:
                # Create filename from question text
                filename = re.sub(r'[^a-z0-9\s]', '', q_normalized.lower())
                filename = '-'.join(filename.split()[:8])  # First 8 words

                entity = {
                    'question': q_text,
                    'filename': filename,
                    'category': question.get('category', 'other'),
                    'context': question.get('context', ''),
                    'is_new': True
                }
                normalized.append(entity)
                seen.add(q_normalized)

        if verbose:
            print(f"  ✓ {len(normalized)} unique questions")
            print()

        return normalized


def main():
    parser = argparse.ArgumentParser(
        description="Normalize and deduplicate extracted entities"
    )
    parser.add_argument(
        'extractions',
        nargs='+',
        type=Path,
        help='Extraction JSON files to merge'
    )
    parser.add_argument(
        '--knowledge-base',
        type=Path,
        default=Path('knowledge_base'),
        help='Knowledge base directory (default: knowledge_base)'
    )
    parser.add_argument(
        '--similarity-threshold',
        type=float,
        default=0.85,
        help='Similarity threshold for matching (0-1, default: 0.85)'
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Verbose output'
    )

    args = parser.parse_args()

    # Initialize normalizer
    normalizer = EntityNormalizer(
        args.knowledge_base,
        similarity_threshold=args.similarity_threshold
    )

    print("🔄 Entity Normalization")
    print(f"📁 Knowledge base: {args.knowledge_base}")
    print(f"📊 Loaded {len(normalizer.existing_thinkers)} existing thinkers")
    print(f"📊 Loaded {len(normalizer.existing_concepts)} existing concepts")
    print()

    # Merge and normalize
    normalized = normalizer.merge_extractions(args.extractions, verbose=args.verbose)

    # Save result - write individual JSON files per entity
    entities_dir = args.knowledge_base / 'entities'
    stats = normalizer.save_entities(normalized, entities_dir, verbose=args.verbose)

    print()
    print("💾 Saved normalized entities:")
    print(f"   • {stats['thinkers']} thinkers → entities/thinkers/")
    print(f"   • {stats['concepts']} concepts → entities/concepts/")
    print(f"   • {stats['frameworks']} frameworks → entities/frameworks/")
    print(f"   • {stats['institutions']} institutions → entities/institutions/")
    print(f"   • {stats['questions']} questions → entities/questions/")
    print()
    print("✅ Normalization complete!")
    print()
    print("Next steps:")
    print(f"  1. Review individual entities: {entities_dir}/")
    print(f"  2. Populate entity pages: make kb-populate")
    print(f"  3. Inject links into transcripts: make kb-link")


if __name__ == '__main__':
    main()
