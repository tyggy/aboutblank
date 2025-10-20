# Makefile for Buddhism & AI Knowledge Base

.PHONY: help setup process analyze synthesize clean

help:
	@echo "Buddhism & AI Knowledge Base - Available commands:"
	@echo ""
	@echo "Setup:"
	@echo "  make setup                        - Set up Claude Code environment"
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
