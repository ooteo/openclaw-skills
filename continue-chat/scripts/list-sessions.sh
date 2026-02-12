#!/bin/bash
# List recent sessions with timestamps and sizes
# Usage: list-sessions.sh [count]

COUNT=${1:-10}
SESSION_DIR="$HOME/.openclaw/agents/main/sessions"

echo "Recent sessions (newest first):"
echo "─────────────────────────────────────────────────────────────"
printf "%-40s %20s %10s\n" "SESSION ID" "MODIFIED" "SIZE"
echo "─────────────────────────────────────────────────────────────"

ls -lt "$SESSION_DIR"/*.jsonl 2>/dev/null | head -$COUNT | while read line; do
    file=$(echo "$line" | awk '{print $NF}')
    size=$(echo "$line" | awk '{print $5}')
    date=$(echo "$line" | awk '{print $6, $7, $8}')
    basename=$(basename "$file" .jsonl)
    
    # Convert size to human readable
    if [ "$size" -gt 1048576 ]; then
        size_hr="$(echo "scale=1; $size/1048576" | bc)M"
    elif [ "$size" -gt 1024 ]; then
        size_hr="$(echo "scale=1; $size/1024" | bc)K"
    else
        size_hr="${size}B"
    fi
    
    printf "%-40s %20s %10s\n" "$basename" "$date" "$size_hr"
done

echo ""
echo "Current session is typically the most recent (top)."
echo "To summarize a session: summarize-session.sh <session-id>"
