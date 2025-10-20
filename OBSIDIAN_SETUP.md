# Obsidian Setup Guide

## Fixing "Link Creates New File" Issue

If clicking links in Obsidian creates new files instead of opening existing ones, here's how to fix it:

### Problem

When entity pages link to transcripts, the link might not match the exact filename.

### Solution 1: Configure Obsidian Settings

1. Open Obsidian Settings (Cmd/Ctrl + ,)
2. Go to **Files & Links**
3. Set **"New link format"** to: **Shortest path when possible**
4. Enable **"Use [[Wikilinks]]"**
5. Enable **"Automatically update internal links"**

### Solution 2: Ensure All Files Are in the Vault

Make sure you opened the **root `knowledge_base/` folder** as your vault, not a subfolder:

```
✅ CORRECT: Open knowledge_base/ as vault
❌ WRONG: Open knowledge_base/thinkers/ as vault
```

### Solution 3: Move Transcripts to Standard Location

Obsidian works best when all markdown files are in the vault root or standard folders.

**Current structure:**
```
knowledge_base/
├── transcripts/
│   └── raw/                  ← Transcripts are here (deep)
│       └── video-id_title_cleaned_edited.md
├── thinkers/
├── concepts/
└── frameworks/
```

**Better structure for Obsidian:**
```
knowledge_base/
├── transcripts/              ← Move transcripts here
│   └── video-title.md
├── thinkers/
├── concepts/
└── frameworks/
```

**To reorganize:**

```bash
# Move transcripts up one level
mv knowledge_base/transcripts/raw/*.md knowledge_base/transcripts/

# Or create a flatter structure
mkdir -p knowledge_base/_sources
mv knowledge_base/transcripts/raw/*.md knowledge_base/_sources/
```

### Solution 4: Simplify Transcript Filenames

Long filenames with IDs and tags can cause linking issues.

**Current:**
```
BRJ48AU5gP4_[Speaker_Prof._Dr._Thomas_H._Doctor]_Buddhism_and_AI_Collaboration_and_a_New_Model_of_Intelligence_cleaned_edited.md
```

**Better:**
```
Buddhism and AI Collaboration - Thomas Doctor.md
```

Rename for Obsidian-friendly names:

```bash
cd knowledge_base/transcripts/raw/

# Example: Rename to remove IDs and cleanup
mv "BRJ48AU5gP4_*_cleaned_edited.md" "Buddhism and AI Collaboration - Thomas Doctor.md"
```

## Recommended Vault Structure

```
knowledge_base/                    ← Open this as your Obsidian vault
├── 📁 _sources/                   ← All source materials
│   ├── transcripts/
│   ├── papers/
│   └── books/
├── 📁 thinkers/                   ← Entity pages
├── 📁 concepts/
│   ├── buddhist/
│   ├── cognitive/
│   ├── ai/
│   └── interdisciplinary/
├── 📁 frameworks/
├── 📁 institutions/
├── 📁 questions/
└── 📁 syntheses/                  ← Your notes and synthesis
    ├── daily/
    └── themes/
```

## Obsidian Plugins to Install

These enhance the knowledge base experience:

1. **Graph Analysis** - Better graph visualization
2. **Dataview** - Query entities by metadata
3. **Tag Wrangler** - Manage tags
4. **Excalidraw** - Draw concept maps
5. **Local Graph** - See connections for current note

## Testing Links

After setup, test a link:

1. Open a thinker page (e.g., `michael-levin.md`)
2. Click on a framework link (e.g., `[[Cognitive Light Cone]]`)
3. Should open the concept page, not create new file

If it still creates a new file:
- Check the exact filename in `concepts/cognitive/`
- Ensure capitalization matches
- Try using the full path: `[[concepts/cognitive/cognitive-light-cone]]`

## Wiki Link Format

Obsidian supports these link formats:

```markdown
[[Page Name]]                          # Basic link
[[Page Name|Display Text]]             # Custom display
[[folder/subfolder/Page Name]]         # With path
[[Page Name#Heading]]                  # Link to heading
```

For this knowledge base, use basic format:
```markdown
[[Michael Levin]]
[[Cognitive Light Cone]]
[[SCI Loop]]
```

Obsidian will find them regardless of which folder they're in (as long as names are unique).
