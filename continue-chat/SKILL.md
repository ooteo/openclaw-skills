---
name: continue-chat
description: Continue from a previous conversation. Use when user says "continue from last time", "pick up where we left off", "what were we talking about", "load previous context", or similar. Recovers context across session boundaries.
---

# Continue Chat

Recover context from previous sessions when OpenClaw creates a fresh session boundary.

## Quick Start

1. List recent sessions:
```bash
~/.openclaw/skills/continue-chat/scripts/list-sessions.sh
```

2. Get summary of a specific session:
```bash
~/.openclaw/skills/continue-chat/scripts/summarize-session.sh <session-id>
```

3. Load full history using `sessions_history` tool with the session key.

## Workflow

### "Continue from last time"

1. Run `list-sessions.sh` to see recent sessions with timestamps
2. Identify the session to continue from (usually the most recent before current)
3. Run `summarize-session.sh <session-id>` to get a quick summary
4. If more detail needed, use `sessions_history` tool:
   ```
   sessions_history(sessionKey="agent:main:main", limit=50, includeTools=false)
   ```
   Note: This fetches current session. For other sessions, read the transcript directly.

5. Present context to user: "Last time we discussed X, Y, Z. We left off at..."

### Finding the Right Session

Sessions are stored in: `~/.openclaw/agents/main/sessions/*.jsonl`

Each file is named by session UUID. Use `list-sessions.sh` which shows:
- Session ID
- Last modified time
- File size (proxy for conversation length)

### Manual Transcript Reading

For sessions other than current, read transcript directly:
```bash
# Get last N messages from a session
tail -100 ~/.openclaw/agents/main/sessions/<session-id>.jsonl | \
  jq -r 'select(.type=="message") | .message | select(.role=="user" or .role=="assistant") | "\(.role): \(.content[0].text // .content[0].type | .[0:200])"'
```

## Chat Summaries (Optional Enhancement)

Maintain `memory/chat-summaries.md` with session summaries for quick lookup:

```markdown
## 2026-02-11 23:57 — Learning How to Learn
Session: 3f1d8b87-2019-4734-8117-664149514fdd
Topics: Questioning as master skill, NotebookLM research, Einstein quote
Outcome: Sent off to research learning
Open threads: Learning research incomplete
```

Append to this file at end of significant sessions for faster future lookups.
