---
name: book
description: Generate comprehensive educational content (wikis, textbooks, guides) from research. Use when creating multi-chapter educational materials, onboarding documentation, knowledge bases, or any "book-like" content that requires research synthesis, structured curriculum, and parallel content generation.
---

# Book Generation Skill

Generate comprehensive educational content from research materials. Produces static HTML wikis, textbooks, or guides.

## Workflow Overview

```
Research → Scope → Architecture → Scaffolding → Generate → Assemble → Package
```

| Phase | Tool | Cost |
|-------|------|------|
| Research | NotebookLM | Free |
| Scope/Architecture | Main context | Normal |
| Scaffolding | Main context | Normal |
| Content Generation | Parallel workers (haiku) | Low |
| Assembly | Python script | Zero |

## Phase 1: Research (NotebookLM)

Use NotebookLM (free Gemini tier) for deep research:

1. Create notebook with source materials (PDFs, URLs, docs)
2. Query for key concepts, relationships, terminology
3. Extract: glossary terms, chapter structure, key insights
4. Save research outputs to `project-name/research/`

**Output:** Research notes, glossary draft, concept map

## Phase 2: Scope Calibration

Determine depth based on audience and purpose:

| Level | Pages | Words | Use Case |
|-------|-------|-------|----------|
| Brief | 5-10 | 3-5K | Executive summary |
| Guide | 15-30 | 10-20K | Quick reference |
| Textbook | 40-60 | 30-50K | Comprehensive intro |
| Wiki | 60-100 | 50-100K | Deep mastery |

**Learning:** Start with explicit scope agreement. Initial estimates often too shallow—verify with user before proceeding.

## Phase 3: Architecture

Create chapter structure with page counts:

```markdown
## Chapter 1: Foundations (10 pages)
1. What is X?
2. Why X matters
...

## Chapter 2: Core Concepts (12 pages)
...
```

**Parallelization rules:**
- Foundations chapter: Sequential (everything depends on it)
- Later chapters: Can parallelize after foundations complete
- Split large chapters (15+ pages) into parts for separate workers

## Phase 4: Scaffolding

Create these files BEFORE spawning workers:

### `_style-guide.md`
- Audience definition
- Voice/tone rules
- Page structure template (TL;DR, hook, content, takeaways, links)
- Length guidelines by page type
- Terminology rules

### `_glossary.md`
- Canonical term definitions
- Workers MUST use exact terms
- Link format: `[[Glossary#term|display text]]`

### `_page-index.md`
- Complete list of all page titles
- Canonical names for `[[wikilinks]]`
- Chapter groupings

### `chapters/` structure
```
chapters/
├── 01-foundations/
├── 02-concepts/
├── 03-application/
└── ...
```

## Phase 5: Parallel Content Generation

Spawn workers with this prompt pattern:

```
You are writing pages for an educational wiki about [TOPIC].

CONTEXT:
- Read: _style-guide.md, _glossary.md, _page-index.md
- Your chapter: [CHAPTER_NAME]
- Your pages: [LIST]

INSTRUCTIONS:
1. Follow style guide exactly
2. Use glossary terms consistently
3. Use [[wikilinks]] for cross-references
4. Write each page to chapters/[CHAPTER]/[SLUG].md

Output format: One markdown file per page, saved to correct location.
```

**Worker assignment:**
- Use haiku for content generation (cost efficient)
- 8-12 pages per worker
- Split chapters >15 pages across multiple workers

## Phase 6: Assembly

Use `scripts/build-html.py` to convert markdown to HTML:

```bash
python3 scripts/build-html.py
```

The script:
1. Reads all `chapters/**/*.md` files
2. Converts `[[wikilinks]]` to HTML links
3. Generates navigation sidebar
4. Adds prev/next navigation
5. Applies CSS styling
6. Outputs to `html/` folder

### Critical Fix: Relative Paths

**Bug encountered:** Links broken in nested chapter pages.

**Root cause:** Pages in `html/01-chapter/page.html` need `../` prefix to reach `html/index.html` and sibling chapters.

**Solution:** Pass `base_path` parameter to link generators:
- Index page: `base_path=""`
- Chapter pages: `base_path="../"`

See `scripts/build-html.py` for implementation.

## Phase 7: Package

```bash
zip -r output.zip html/
```

Deliver as self-contained static site that opens in any browser.

## Quality Checklist

Before delivery:
- [ ] All internal links work
- [ ] Glossary terms used consistently
- [ ] Navigation sidebar complete
- [ ] Prev/next links functional
- [ ] Mobile-responsive CSS
- [ ] TL;DR on every page

## Learnings Log

| Issue | Root Cause | Fix |
|-------|-----------|-----|
| Scope too shallow | Didn't verify depth expectations | Explicit scope agreement upfront |
| Broken links in chapters | Relative paths need `../` for nested pages | `base_path` parameter in link generation |
| Worker output inconsistent | Style guide not explicit enough | Detailed page structure template |
| Glossary drift | Workers invented synonyms | "Use exact terms" rule in worker prompt |

## File References

- `scripts/build-html.py` — HTML conversion with wikilink processing
- `assets/style.css` — Default wiki styling (dark theme)
- `references/style-guide-template.md` — Template for _style-guide.md
- `references/worker-prompt-template.md` — Template for worker prompts
