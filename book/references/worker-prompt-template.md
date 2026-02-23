# Worker Prompt Template

Use this template when spawning content generation workers.

---

## Prompt Structure

```
You are writing pages for an educational wiki about [TOPIC].

TARGET AUDIENCE: [Description from style guide]

YOUR ASSIGNMENT:
- Chapter: [CHAPTER_NUMBER] - [CHAPTER_NAME]
- Pages to write: [COUNT] pages
- Page list:
  1. [Page Title 1]
  2. [Page Title 2]
  ...

REFERENCE FILES (read these first):
- _style-guide.md — Voice, tone, page structure, length guidelines
- _glossary.md — Canonical term definitions (use EXACT terms)
- _page-index.md — All page titles for [[wikilinks]]

CRITICAL RULES:
1. Follow the page structure template EXACTLY (TL;DR, Hook, Content, Takeaways, Links)
2. Use glossary terms as written — do NOT invent synonyms
3. Use [[Page Title]] for internal links (match _page-index.md exactly)
4. Each page: 800-1500 words depending on complexity
5. Start with analogy, then technical explanation
6. Lead with problem/pain, then solution

OUTPUT:
For each page, create a markdown file at:
  chapters/[CHAPTER_FOLDER]/[SLUG].md

Example: chapters/01-foundations/01-what-is-x.md

When complete, list all files created with word counts.
```

---

## Worker Assignment Guidelines

| Chapter Size | Workers | Pages/Worker |
|--------------|---------|--------------|
| 1-8 pages | 1 | All |
| 9-15 pages | 1-2 | 8-10 |
| 16-20 pages | 2 | 8-10 |
| 21+ pages | 3+ | 7-10 |

## Model Selection

- **Content generation:** haiku (cost efficient, good quality)
- **Complex/technical chapters:** sonnet (if haiku struggles)
- **Final review/assembly:** main context (opus)

## Parallel Execution

1. **Phase 1:** Foundations chapter (sequential — everything depends on it)
2. **Phase 2:** All other chapters (parallel)

```
# Example spawn pattern
sessions_spawn task:"[PROMPT]" label:"wiki-ch1-foundations" model:"haiku"
sessions_spawn task:"[PROMPT]" label:"wiki-ch2-concepts" model:"haiku"
sessions_spawn task:"[PROMPT]" label:"wiki-ch3-application" model:"haiku"
# ... etc
```

## Monitoring

Check worker progress:
```
sessions_list kinds:["isolated"] messageLimit:1
```

Check specific worker:
```
sessions_history sessionKey:"wiki-ch1-foundations" limit:5
```
