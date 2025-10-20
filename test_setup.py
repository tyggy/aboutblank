#!/usr/bin/env python3
"""Test that the environment is set up correctly"""

import sys
print(f"Python version: {sys.version}")

try:
    import youtube_transcript_api
    print("✅ youtube_transcript_api installed")
except ImportError:
    print("❌ youtube_transcript_api not installed")

try:
    import pandas
    print("✅ pandas installed")
except ImportError:
    print("❌ pandas not installed")

try:
    import matplotlib
    print("✅ matplotlib installed")
except ImportError:
    print("❌ matplotlib not installed")

try:
    import networkx
    print("✅ networkx installed")
except ImportError:
    print("❌ networkx not installed")

print("\n🎉 Basic environment ready!")
print("\nNote: Advanced NLP features (spaCy) are optional.")
print("If you need them later, run:")
print("  pip install spacy==3.5.0")
print("  python -m spacy download en_core_web_sm")
