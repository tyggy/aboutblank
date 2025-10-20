# Makefile for Buddhism & AI Knowledge Base

.PHONY: help setup process analyze synthesize clean

help:
	@echo "Buddhism & AI Knowledge Base - Available commands:"
	@echo "  make setup             - Set up Claude Code environment"
	@echo "  make youtube-status    - Check YouTube transcript processing status"
	@echo "  make youtube-download  - Download all YouTube transcripts"
	@echo "  make youtube-test      - Test download with one video"
	@echo "  make process           - Process all transcripts"
	@echo "  make analyze           - Run concept extraction and mapping"
	@echo "  make synthesize        - Generate synthesis documents"
	@echo "  make report            - Generate full project report"
	@echo "  make clean             - Clean generated files"

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
