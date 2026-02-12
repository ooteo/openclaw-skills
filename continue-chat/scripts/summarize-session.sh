#!/bin/bash
# Summarize a session by extracting key messages
# Usage: summarize-session.sh <session-id> [message-count]

SESSION_ID=$1
MSG_COUNT=${2:-20}

if [ -z "$SESSION_ID" ]; then
    echo "Usage: summarize-session.sh <session-id> [message-count]"
    echo "Get session IDs from: list-sessions.sh"
    exit 1
fi

SESSION_FILE="$HOME/.openclaw/agents/main/sessions/${SESSION_ID}.jsonl"

if [ ! -f "$SESSION_FILE" ]; then
    echo "Session not found: $SESSION_FILE"
    exit 1
fi

echo "Session: $SESSION_ID"
echo "File: $SESSION_FILE"
echo "─────────────────────────────────────────────────────────────"

# Extract session start time
START_TIME=$(head -1 "$SESSION_FILE" | jq -r '.timestamp // "unknown"')
echo "Started: $START_TIME"
echo ""

echo "Last $MSG_COUNT messages (truncated):"
echo "─────────────────────────────────────────────────────────────"

# Extract recent messages, showing role and truncated content
# Filter for text content (skip thinking blocks)
tail -200 "$SESSION_FILE" | \
    jq -r 'select(.type=="message") | .message | select(.role=="user" or .role=="assistant") | 
    . as $msg | 
    ($msg.content | map(select(.type=="text")) | .[0].text // "...") as $text |
    "\($msg.role | ascii_upcase): \($text | .[0:150] | gsub("\n"; " "))"' 2>/dev/null | \
    grep -v "^\(USER\|ASSISTANT\): \.\.\.$" | \
    tail -$MSG_COUNT

echo ""
echo "─────────────────────────────────────────────────────────────"
echo "For full context, read the transcript directly or use sessions_history tool."
