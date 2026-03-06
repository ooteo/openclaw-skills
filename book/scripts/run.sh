#!/bin/bash
# Wrapper: activates skill venv and runs book_builder.py
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
source "$SKILL_DIR/venv/bin/activate"
python3 "$SKILL_DIR/scripts/book_builder.py" "$@"
