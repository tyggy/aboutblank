# Quick Start - Never Forget Commands!

## First Time Setup (Do Once)

```bash
./setup_env.sh
```

This will:
- Create Python virtual environment
- Install all dependencies
- Activate the environment
- Keep you in an active shell

## Every Time You Come Back

### Option 1: Use the activate script (Recommended)
```bash
source activate
```

Then run your commands:
```bash
make kb-build
python tools/extract_entities.py --help
```

When done:
```bash
deactivate
```

### Option 2: Use make (Auto-activates)
```bash
make env
```

This activates and gives you a shell.

### Option 3: One-liner for common tasks
```bash
# The make commands auto-handle the environment for you!
make kb-build           # Builds entire knowledge base
make transcripts-clean  # Cleans transcripts
make kb-extract         # Extracts entities
```

## Common Commands Cheat Sheet

```bash
# === SETUP (once) ===
./setup_env.sh                    # First time setup

# === ACTIVATE (each session) ===
source activate                   # Activate environment

# === TRANSCRIPTS ===
make youtube-download             # Download from YouTube
make transcripts-clean            # Remove timestamps/fillers
make transcripts-copyedit         # Claude API copyedit

# === KNOWLEDGE BASE ===
make kb-build                     # Complete pipeline (everything!)
make kb-extract                   # Extract entities from transcripts
make kb-normalize                 # Deduplicate entities
make kb-populate                  # Create entity pages
make kb-link                      # Add wiki links to transcripts
make kb-enrich                    # Cross-link entity pages

# === HELPERS ===
make help                         # Show all commands
make kb-scan-speakers             # Find transcription errors

# === DEACTIVATE ===
deactivate                        # Exit virtual environment
```

## Environment Variables

Set these once in your shell config (~/.bashrc or ~/.zshrc):

```bash
# Add to ~/.bashrc or ~/.zshrc
export ANTHROPIC_API_KEY='your-key-here'
```

Then you never need to set it again!

## Troubleshooting

### "Command not found"
```bash
# Make sure environment is activated:
source activate

# Or run setup again:
./setup_env.sh
```

### "No module named 'anthropic'"
```bash
# Reinstall dependencies:
source activate
pip install -r requirements.txt
```

### "make: command not found"
```bash
# Install make (macOS):
xcode-select --install

# Install make (Ubuntu/Debian):
sudo apt-get install build-essential
```

## Pro Tips

### Auto-activate on cd

Add this to your ~/.bashrc or ~/.zshrc:

```bash
# Auto-activate venv when entering directory
cd() {
    builtin cd "$@"
    if [ -f "activate" ]; then
        source activate
    fi
}
```

### Use direnv (Advanced)

Install direnv and create `.envrc`:

```bash
# Install direnv
brew install direnv  # macOS
# or
sudo apt install direnv  # Linux

# Create .envrc in project root
echo "source activate" > .envrc
direnv allow

# Now auto-activates when you cd into the directory!
```

### Aliases

Add to ~/.bashrc or ~/.zshrc:

```bash
alias kb='cd ~/path/to/aboutblank && source activate'
alias kb-build='cd ~/path/to/aboutblank && source activate && make kb-build'
```

Then just type:
```bash
kb              # Go to project and activate
kb-build        # Build knowledge base from anywhere
```

## Quick Reference

| What you want to do | Command |
|---------------------|---------|
| First time setup | `./setup_env.sh` |
| Activate environment | `source activate` |
| Download transcripts | `make youtube-download` |
| Clean transcripts | `make transcripts-clean` |
| Copyedit transcripts | `make transcripts-copyedit` |
| Build knowledge base | `make kb-build` |
| Extract entities | `make kb-extract` |
| Add cross-links | `make kb-enrich` |
| See all commands | `make help` |
| Deactivate | `deactivate` |

## TL;DR - Simplest Workflow

```bash
# First time only:
./setup_env.sh

# Every time after:
source activate
make kb-build

# That's it!
```
