# [PROJECT NAME] — Style Guide

## Audience

**Primary reader:** [Role/background description]
**Goal:** [What they should be able to do after reading]

## Voice & Tone

- **Clear over clever** — Explain concepts plainly before adding nuance
- **Confident but not arrogant** — State facts directly, acknowledge limitations
- **Conversational but substantive** — Not academic, not dumbed-down
- **[Domain]-aware** — Connect technical concepts to [relevant outcomes]

## Page Structure

Every page follows this structure:

```markdown
# Page Title

> **TL;DR:** One-sentence summary of the key takeaway.

## Opening Hook (100-150 words)
Why should the reader care? Lead with value or a compelling problem.

## Main Content (600-1000 words)
The core explanation. Use the Analogy Ladder:
1. Start with familiar concept
2. Build to technical reality
3. Show application

## Key Takeaways
- Bullet point 1
- Bullet point 2
- Bullet point 3

## Related Pages
- [[Link to related concept]]
- [[Link to prerequisite]]
- [[Link to deeper dive]]
```

## Linking Conventions

- Use double brackets for internal wiki links: `[[Page Title]]`
- Link to glossary terms on first use: `[[Glossary#term-name|term name]]`
- Every page should link to 2-4 related pages

## Length Guidelines

- **Foundation pages:** 800-1000 words
- **Core concept pages:** 1000-1500 words
- **Deep dive pages:** 1500-2000 words
- **Reference pages:** Variable (glossary entries ~100 words each)

## Pedagogical Patterns

### The Analogy Ladder
1. "It's like..." (familiar concept)
2. "More precisely..." (refined analogy)
3. "Technically..." (actual definition)

### The Problem-First Narrative
Never lead with the solution. Lead with pain:
- "Here's the problem..."
- "This is why it matters..."
- "And here's what changes that..."

## Terminology Rules

- Use terms exactly as defined in `_glossary.md`
- On first use of a technical term, link to glossary
- Avoid synonyms for key concepts (consistency > variety)

## Formatting

- Use **bold** for key terms on first introduction
- Use `code formatting` for specific names, metrics, technical values
- Use > blockquotes for important callouts or definitions
- Use tables for comparisons
- Use bullet lists for 3+ related items

## What to Avoid

- Jargon without explanation
- Passive voice (keep under 15%)
- "It is interesting to note that..." (just state it)
- Hedging when facts are clear
- Marketing fluff without substance

## Quality Checklist

Before submitting any page:
- [ ] TL;DR is genuinely one sentence
- [ ] Opening hook connects to value
- [ ] Analogy precedes technical explanation
- [ ] All technical terms linked to glossary
- [ ] 2-4 internal links to related pages
- [ ] Key takeaways are actionable/memorable
- [ ] Length within guidelines
