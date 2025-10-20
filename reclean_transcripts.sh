#!/bin/bash
# Re-clean existing transcripts with updated cleaner
# Includes: filler word removal + metadata stripping

echo "Re-cleaning transcripts (filler word removal + metadata stripping)..."
echo ""

# Find all _cleaned.md files and re-process them in-place
for file in knowledge_base/transcripts/raw/*_cleaned.md; do
    if [ -f "$file" ]; then
        echo "Re-cleaning: $(basename "$file")"
        python tools/clean_inline_timestamps.py "$file" --in-place
    fi
done

echo ""
echo "✓ All cleaned transcripts updated!"
echo "  - Filler words removed (uh, um, you know, etc.)"
echo "  - YouTube metadata stripped (kept only title + transcript)"
echo ""
echo "Next step: make transcripts-copyedit"
