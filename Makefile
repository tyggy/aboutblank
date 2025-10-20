# Makefile for Buddhism & AI Knowledge Base

.PHONY: help setup process analyze synthesize clean

help:
	@echo "Buddhism & AI Knowledge Base - Available commands:"
	@echo "  make setup      - Set up Claude Code environment"
	@echo "  make download   - Download all transcripts"
	@echo "  make process    - Process all transcripts" 
	@echo "  make analyze    - Run concept extraction and mapping"
	@echo "  make synthesize - Generate synthesis documents"
	@echo "  make report     - Generate full project report"
	@echo "  make clean      - Clean generated files"

setup:
	python -m venv venv
	. venv/bin/activate && pip install -r requirements.txt
	python setup_claude_env.py

download:
	python tools/transcript_downloader.py Buddhism_&_AI.md -o knowledge_base/transcripts/raw

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
