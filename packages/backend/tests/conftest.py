import os

# Skip test files that require API keys at import time
collect_ignore = []

if not os.environ.get("GEMINI_API_KEY"):
    collect_ignore.append("test_extract_album_data.py")
