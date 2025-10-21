# Makefile for Buddhism & AI Knowledge Base

.PHONY: help setup process analyze synthesize clean

help:
	@echo "Buddhism & AI Knowledge Base - Available commands:"
	@echo ""
	@echo "🚀 QUICK START:"
	@echo "  source activate                   - Activate Python environment"
	@echo "  make kb-build                     - Build complete knowledge base"
	@echo ""
	@echo "Setup:"
	@echo "  ./setup_env.sh                    - First time setup (run once)"
	@echo "  make env                          - Activate environment and open shell"
	@echo ""
	@echo "YouTube Transcripts:"
	@echo "  make youtube-status               - Check transcript download status"
	@echo "  make youtube-download             - Download all YouTube transcripts"
	@echo "  make youtube-test                 - Test download with one video"
	@echo ""
	@echo "Transcript Cleaning:"
	@echo "  make transcripts-clean            - Remove inline timestamps"
	@echo "  make transcripts-copyedit         - Copyedit with Claude API"
	@echo "  make transcripts-process          - Clean + copyedit (full pipeline)"
	@echo "  make transcripts-cleanup-duplicates - Remove accidentally duplicated files"
	@echo ""
	@echo "Research Papers:"
	@echo "  make papers-extract               - Extract text from PDFs"
	@echo "  make papers-copyedit              - Copyedit papers with Claude API"
	@echo "  make papers-process               - Extract + copyedit (full pipeline)"
	@echo ""
	@echo "Knowledge Extraction:"
	@echo "  make kb-fix-speakers              - Fix speaker name transcription errors"
	@echo "  make kb-scan-speakers             - Scan for potential speaker name errors"
	@echo "  make kb-extract                   - Extract entities (auto-skips processed files)"
	@echo "  make kb-extract-force             - Force re-extract all entities"
	@echo "  make kb-normalize                 - Normalize and deduplicate entities"
	@echo "  make kb-populate                  - Create entity pages in knowledge base"
	@echo "  make kb-link                      - Inject wiki links into transcripts"
	@echo "  make kb-enrich                    - Cross-enrich entities with bidirectional links"
	@echo "  make kb-build                     - Full pipeline: fix → extract → normalize → populate → link → enrich"
	@echo ""
	@echo "Analysis:"
	@echo "  make analyze                      - Run concept extraction and mapping"
	@echo "  make synthesize                   - Generate synthesis documents"
	@echo "  make report                       - Generate full project report"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean                        - Clean generated files"

setup:
	python -m venv venv
	. venv/bin/activate && pip install -r requirements.txt
	python setup_claude_env.py

env:
	@echo "🐍 Activating Python environment..."
	@echo "Run 'deactivate' when done"
	@bash -c "source venv/bin/activate && exec bash"

# YouTube transcript processing with yt-dlp
youtube-status:
	@echo "Checking YouTube transcript status..."
	python tools/ytdlp_processor.py --status

youtube-download:
	@echo "Downloading YouTube transcripts..."
	python tools/ytdlp_processor.py --verbose
	@echo "YouTube transcripts downloaded!"

youtube-test:
	@echo "Testing with one video (xaUknipwnpw - Michael Levin)..."
	python tools/ytdlp_processor.py --video xaUknipwnpw --verbose
	@echo "Test complete!"

youtube-force:
	@echo "Force re-downloading all transcripts..."
	python tools/ytdlp_processor.py --force --verbose
	@echo "Transcripts re-downloaded!"

# Transcript cleaning and copyediting
transcripts-clean:
	@echo "Cleaning transcripts (removing timestamps)..."
	@echo "Note: Automatically skips files with _cleaned or _edited in name"
	python tools/clean_inline_timestamps.py knowledge_base/transcripts/raw/*.md
	@echo "Transcripts cleaned!"

transcripts-copyedit:
	@echo "Copyediting transcripts with Claude API..."
	@if [ -z "$$ANTHROPIC_API_KEY" ]; then \
		echo "Error: ANTHROPIC_API_KEY not set"; \
		echo "Set it with: export ANTHROPIC_API_KEY=your-key-here"; \
		exit 1; \
	fi
	python tools/copyedit_with_claude.py knowledge_base/transcripts/raw/*_cleaned.md
	@echo "Copyediting complete!"

transcripts-process: transcripts-clean transcripts-copyedit
	@echo "All transcripts processed!"

# Clean up accidentally duplicated files
transcripts-cleanup-duplicates:
	@echo "Removing accidentally duplicated files (*_cleaned_edited_cleaned.md, etc.)..."
	@find knowledge_base/transcripts/raw -name "*_cleaned_edited_cleaned.md" -delete 2>/dev/null || true
	@find knowledge_base/transcripts/raw -name "*_edited_cleaned.md" -delete 2>/dev/null || true
	@find knowledge_base/transcripts/raw -name "*_cleaned_cleaned.md" -delete 2>/dev/null || true
	@echo "Cleanup complete!"

# Research paper processing
papers-extract:
	@echo "Extracting text from PDF papers..."
	@if [ ! -d knowledge_base/sources/papers ] || [ -z "$$(ls -A knowledge_base/sources/papers/*.pdf 2>/dev/null)" ]; then \
		echo "⚠️  No PDF files found in knowledge_base/sources/papers/"; \
		echo "   Add PDF files to that directory first."; \
		exit 0; \
	fi
	@mkdir -p knowledge_base/papers/cleaned
	python tools/extract_pdf.py knowledge_base/sources/papers --verbose
	@echo "✓ PDF extraction complete!"

papers-copyedit:
	@echo "Copyediting papers with Claude API..."
	@if [ -z "$$ANTHROPIC_API_KEY" ]; then \
		echo "Error: ANTHROPIC_API_KEY not set"; \
		echo "Set it with: export ANTHROPIC_API_KEY=your-key-here"; \
		exit 1; \
	fi
	@if [ ! -d knowledge_base/papers/cleaned ] || [ -z "$$(ls -A knowledge_base/papers/cleaned/*.md 2>/dev/null)" ]; then \
		echo "Error: No extracted papers found. Run 'make papers-extract' first."; \
		exit 1; \
	fi
	@mkdir -p knowledge_base/papers/edited
	python tools/copyedit_with_claude.py knowledge_base/papers/cleaned/*.md --output-dir knowledge_base/papers/edited
	@echo "✓ Paper copyediting complete!"

papers-process: papers-extract papers-copyedit
	@echo "All papers processed!"

# Knowledge extraction and Obsidian knowledge base building
kb-fix-speakers:
	@echo "Fixing speaker name transcription errors..."
	python tools/fix_speaker_names.py knowledge_base/transcripts/raw/*_edited.md --verbose
	@echo "✓ Speaker names corrected!"

kb-scan-speakers:
	@echo "Scanning for potential speaker name errors..."
	python tools/fix_speaker_names.py knowledge_base/transcripts/raw/*_edited.md --scan-only --verbose

kb-extract:
	@echo "Extracting entities from transcripts and papers..."
	@if [ -z "$$ANTHROPIC_API_KEY" ]; then \
		echo "Error: ANTHROPIC_API_KEY not set"; \
		echo "Set it with: export ANTHROPIC_API_KEY=your-key-here"; \
		exit 1; \
	fi
	@mkdir -p knowledge_base/extractions
	@# Extract from transcripts
	@if [ -n "$$(ls knowledge_base/transcripts/raw/*_edited.md 2>/dev/null)" ]; then \
		echo "📝 Extracting from transcripts..."; \
		python tools/extract_entities.py knowledge_base/transcripts/raw/*_edited.md --verbose; \
	else \
		echo "⚠️  No edited transcripts found."; \
	fi
	@# Extract from papers
	@if [ -n "$$(ls knowledge_base/papers/edited/*.md 2>/dev/null)" ]; then \
		echo "📄 Extracting from papers..."; \
		python tools/extract_entities.py knowledge_base/papers/edited/*.md --verbose; \
	else \
		echo "⚠️  No edited papers found."; \
	fi
	@echo "✓ Entity extraction complete!"
	@echo "Review extractions in: knowledge_base/extractions/"

kb-extract-force:
	@echo "Force re-extracting entities from all sources..."
	@if [ -z "$$ANTHROPIC_API_KEY" ]; then \
		echo "Error: ANTHROPIC_API_KEY not set"; \
		echo "Set it with: export ANTHROPIC_API_KEY=your-key-here"; \
		exit 1; \
	fi
	@mkdir -p knowledge_base/extractions
	@# Extract from transcripts
	@if [ -n "$$(ls knowledge_base/transcripts/raw/*_edited.md 2>/dev/null)" ]; then \
		echo "📝 Re-extracting from transcripts..."; \
		python tools/extract_entities.py knowledge_base/transcripts/raw/*_edited.md --verbose --force; \
	else \
		echo "⚠️  No edited transcripts found."; \
	fi
	@# Extract from papers
	@if [ -n "$$(ls knowledge_base/papers/edited/*.md 2>/dev/null)" ]; then \
		echo "📄 Re-extracting from papers..."; \
		python tools/extract_entities.py knowledge_base/papers/edited/*.md --verbose --force; \
	else \
		echo "⚠️  No edited papers found."; \
	fi
	@echo "✓ Force extraction complete!"
	@echo "Review extractions in: knowledge_base/extractions/"

kb-normalize:
	@echo "Normalizing and deduplicating entities..."
	@if [ ! -d knowledge_base/extractions ] || [ -z "$$(ls -A knowledge_base/extractions/*.json 2>/dev/null)" ]; then \
		echo "Error: No extractions found. Run 'make kb-extract' first."; \
		exit 1; \
	fi
	python tools/normalize_entities.py knowledge_base/extractions/*_entities.json --verbose
	@echo "✓ Normalization complete!"
	@echo "Review: knowledge_base/normalized_entities.json"

kb-populate:
	@echo "Creating entity pages in knowledge base..."
	@if [ ! -f knowledge_base/normalized_entities.json ]; then \
		echo "Error: normalized_entities.json not found. Run 'make kb-normalize' first."; \
		exit 1; \
	fi
	python tools/populate_entities.py knowledge_base/normalized_entities.json --verbose
	@echo "✓ Entity pages created!"
	@echo "Open knowledge_base/ in Obsidian to explore"

kb-link:
	@echo "Injecting wiki links into transcripts and papers..."
	@if [ ! -f knowledge_base/normalized_entities.json ]; then \
		echo "Error: normalized_entities.json not found. Run 'make kb-normalize' first."; \
		exit 1; \
	fi
	@# Link transcripts
	@if [ -n "$$(ls knowledge_base/transcripts/raw/*_edited.md 2>/dev/null)" ]; then \
		echo "📝 Linking transcripts..."; \
		python tools/inject_links.py knowledge_base/transcripts/raw/*_edited.md --verbose; \
	fi
	@# Link papers
	@if [ -n "$$(ls knowledge_base/papers/edited/*.md 2>/dev/null)" ]; then \
		echo "📄 Linking papers..."; \
		python tools/inject_links.py knowledge_base/papers/edited/*.md --verbose; \
	fi
	@echo "✓ Wiki links injected!"
	@echo "Sources now linked to entities"

kb-enrich:
	@echo "Cross-enriching entity pages..."
	@if [ ! -f knowledge_base/normalized_entities.json ]; then \
		echo "Error: normalized_entities.json not found. Run 'make kb-normalize' first."; \
		exit 1; \
	fi
	python tools/enrich_entities.py knowledge_base/normalized_entities.json --verbose
	@echo "✓ Entity pages enriched with bidirectional links!"

kb-build: kb-fix-speakers kb-extract kb-normalize kb-populate kb-link kb-enrich
	@echo ""
	@echo "════════════════════════════════════════════════"
	@echo "✅ Knowledge Base Build Complete!"
	@echo "════════════════════════════════════════════════"
	@echo ""
	@echo "Your Obsidian knowledge base is ready:"
	@echo "  📁 Thinkers: knowledge_base/thinkers/"
	@echo "  💡 Concepts: knowledge_base/concepts/"
	@echo "  🔧 Frameworks: knowledge_base/frameworks/"
	@echo "  🏛️  Institutions: knowledge_base/institutions/"
	@echo "  ❓ Questions: knowledge_base/questions/"
	@echo ""
	@echo "Sources processed:"
	@echo "  📝 Transcripts: knowledge_base/transcripts/"
	@echo "  📄 Papers: knowledge_base/papers/"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Open knowledge_base/ in Obsidian"
	@echo "  2. View graph: Cmd/Ctrl + G"
	@echo "  3. Explore bidirectional links between entities"
	@echo "  4. Add more papers: copy PDFs to knowledge_base/sources/papers/"
	@echo "  5. Manually refine and expand entity pages"
	@echo ""

process:
	@echo "Processing transcripts..."
	python tools/transcript_processor.py knowledge_base/transcripts/raw
	@echo "Transcripts processed!"

analyze:
	@echo "Extracting concepts..."
	python tools/concept_extractor.py knowledge_base/
	@echo "Mapping connections..."
	python tools/connection_mapper.py knowledge_base/
	@echo "Analysis complete!"

synthesize:
	@echo "Generating synthesis..."
	python tools/synthesis_generator.py
	@echo "Synthesis complete!"

report:
	@echo "Generating project report..."
	@make analyze
	@make synthesize
	python tools/generate_report.py
	@echo "Report generated in outputs/report.md"

clean:
	rm -rf outputs/*
	rm -rf __pycache__
	rm -rf .pytest_cache
	find . -type f -name "*.pyc" -delete

# Claude Code specific commands
claude-context:
	@echo "Updating Claude Code context..."
	python tools/update_context.py
	@echo "Context updated!"

claude-prompt:
	@echo "Generating Claude Code prompt for current task..."
	python tools/generate_claude_prompt.py
	@echo "Prompt copied to clipboard!"

test:
	pytest tests/ -v

backup:
	tar -czf backup_$(shell date +%Y%m%d_%H%M%S).tar.gz knowledge_base/
	@echo "Backup created!"
