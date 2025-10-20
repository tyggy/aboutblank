#!/bin/bash
# Quick setup script for Python environment

echo "🐍 Setting up Python environment..."
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
    echo ""
fi

# Activate venv
echo "Activating virtual environment..."
source venv/bin/activate

# Check if dependencies installed
if ! python -c "import anthropic" 2>/dev/null; then
    echo ""
    echo "Installing dependencies..."
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    echo "✓ Dependencies installed"
fi

echo ""
echo "✅ Python environment ready!"
echo ""
echo "Your environment is now activated."
echo "You can run commands like:"
echo "  make kb-build"
echo "  python tools/extract_entities.py --help"
echo ""
echo "To deactivate later: deactivate"
echo ""

# Keep shell open in activated environment
exec $SHELL
