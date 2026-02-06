# Shared Skill Repository

All agents in your ecosystem can contribute to a shared skill repository. When one agent learns something new or improves an existing skill, it becomes available to all.

## Why Share Skills?

- **Collective learning** — Improvements compound across all agents
- **Redundancy** — Your own fork protects against upstream removal/compromise
- **Consistency** — All agents have the same capabilities
- **Auditability** — Git history tracks all changes

## Setup Options

### Option A: Fork an existing repo

Fork from a known source, then all agents contribute to your fork:

```bash
# 1. Fork github.com/openclaw/skills (or another source) via GitHub UI

# 2. Clone your fork
git clone https://github.com/yourorg/openclaw-skills.git ~/.openclaw/workspace/openclaw-skills

# 3. Add upstream for updates (optional)
cd ~/.openclaw/workspace/openclaw-skills
git remote add upstream https://github.com/openclaw/skills.git
```

### Option B: Start fresh

Create your own skill repo from scratch:

```bash
# 1. Create repo on GitHub (yourorg/openclaw-skills)

# 2. Initialize locally
mkdir -p ~/.openclaw/workspace/openclaw-skills
cd ~/.openclaw/workspace/openclaw-skills
git init
echo "# OpenClaw Skills" > README.md
git add README.md
git commit -m "Initial commit"
git remote add origin https://github.com/yourorg/openclaw-skills.git
git push -u origin main
```

## Push Scripts

Create these in `~/.openclaw/workspace/scripts/`:

### push-skill.sh

```bash
#!/usr/bin/env bash
set -euo pipefail

SKILL_NAME="$1"
SKILL_SRC="$HOME/.openclaw/skills/$SKILL_NAME"
REPO_DIR="$HOME/.openclaw/workspace/openclaw-skills"

if [[ ! -d "$SKILL_SRC" ]]; then
    echo "Skill not found: $SKILL_SRC" >&2
    exit 1
fi

echo "Copying $SKILL_NAME to repo..."
rm -rf "$REPO_DIR/$SKILL_NAME"
cp -r "$SKILL_SRC" "$REPO_DIR/$SKILL_NAME"

cd "$REPO_DIR"
git add "$SKILL_NAME"
git commit -m "Update skill: $SKILL_NAME" || echo "No changes to commit"
git push

echo "✓ Pushed $SKILL_NAME to GitHub"
```

### push-all-skills.sh

```bash
#!/usr/bin/env bash
set -euo pipefail

SKILLS_DIR="$HOME/.openclaw/skills"
REPO_DIR="$HOME/.openclaw/workspace/openclaw-skills"

cd "$REPO_DIR"

for skill_dir in "$SKILLS_DIR"/*/; do
    skill_name=$(basename "$skill_dir")
    
    # Skip if not a valid skill (no SKILL.md)
    [[ -f "$skill_dir/SKILL.md" ]] || continue
    
    echo "Syncing: $skill_name"
    rm -rf "$REPO_DIR/$skill_name"
    cp -r "$skill_dir" "$REPO_DIR/$skill_name"
done

git add -A
git commit -m "Sync all skills: $(date +%Y-%m-%d)" || echo "No changes"
git push

echo "✓ All skills pushed"
```

Make executable:
```bash
chmod +x ~/.openclaw/workspace/scripts/push-skill.sh
chmod +x ~/.openclaw/workspace/scripts/push-all-skills.sh
```

## AGENTS.md Integration

Add this to your workspace's AGENTS.md so all agents know how to contribute:

```markdown
## Skills — Creating & Sharing

Skills live in `~/.openclaw/skills/`. When you create a new skill, **push it to GitHub**.

**Repository:** https://github.com/yourorg/openclaw-skills

**Workflow:**
1. Create skill in `~/.openclaw/skills/<skill-name>/`
2. Follow the skill-creator format (SKILL.md + optional scripts/references/assets)
3. Push to GitHub using the automation scripts

**Scripts:**
\`\`\`bash
# Push single skill
~/.openclaw/workspace/scripts/push-skill.sh <skill-name>

# Push all skills
~/.openclaw/workspace/scripts/push-all-skills.sh
\`\`\`

**Local repo clone:** `~/.openclaw/workspace/openclaw-skills/`
```

## Pulling Updates

### From your own repo (other agents' contributions)

```bash
cd ~/.openclaw/workspace/openclaw-skills
git pull

# Optionally sync to skills dir
for skill in */; do
    [[ -f "$skill/SKILL.md" ]] || continue
    cp -r "$skill" ~/.openclaw/skills/
done
```

### From upstream (if forked)

```bash
cd ~/.openclaw/workspace/openclaw-skills
git fetch upstream
git merge upstream/main
git push
```

## Multi-Agent Deployment

When deploying new agents via `openclaw-deploy`:

```bash
./scripts/deploy.sh docker-remote \
  --host deploy@newserver.com \
  --skill-repo "github.com/yourorg/openclaw-skills" \
  ...
```

This automatically:
1. Clones the skill repo
2. Sets up push scripts
3. Configures AGENTS.md

## Security Considerations

### Your own repo
- You control what gets merged
- Review PRs if accepting external contributions
- Use branch protection for main

### Upstream repos
- Fork rather than direct clone
- Review before merging upstream changes
- Pin to specific commits/tags for stability

### Compromised upstream
If an upstream repo is compromised:
1. Your fork is unaffected (until you pull)
2. Don't merge upstream until verified
3. You can diverge permanently if needed

## Automation Ideas

### Auto-push on skill creation
Add to skill-creator workflow:
```bash
# After creating skill
~/.openclaw/workspace/scripts/push-skill.sh "$SKILL_NAME"
```

### Periodic sync
Add cron job to pull updates:
```json5
{
  schedule: { kind: "cron", expr: "0 6 * * *" },  // Daily 6am
  payload: { 
    kind: "systemEvent", 
    text: "Pull latest skills from shared repo and report any new ones." 
  }
}
```

### Webhook on push
GitHub webhook → trigger skill reload on all agents
