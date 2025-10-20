#!/bin/bash
# Re-clean existing transcripts with updated cleaner (includes filler word removal)

echo "Re-cleaning transcripts with filler word removal..."
echo ""

# Find all _cleaned.md files and re-process them in-place
for file in knowledge_base/transcripts/raw/*_cleaned.md; do
    if [ -f "$file" ]; then
        echo "Re-cleaning: $(basename "$file")"
        python tools/clean_inline_timestamps.py "$file" --in-place
    fi
done

echo ""
echo "✓ All cleaned transcripts updated with filler word removal!"
echo "Now you can run copyediting: make transcripts-copyedit"
