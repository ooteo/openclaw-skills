# Book Skill — Learnings Log

Lessons learned from the DatologyAI wiki project (Feb 2026).

## Project Evolution

The DatologyAI project went through multiple iterations:

| Version | Format | Pages | Outcome |
|---------|--------|-------|---------|
| v1 | Onboarding doc | 2 | Too shallow for "credible conversations" |
| v2 | Executive brief | 5 | Good summary, not enough depth |
| v3 | Technical deep dive | 10 | Technical audience only |
| v4 | Textbook | 20 | Getting closer, still incomplete |
| v5 | Full wiki | 64 | ✓ Comprehensive, navigable |

**Lesson:** Start with explicit scope agreement. "Credible conversations" depth requires 60-100 pages for complex technical topics.

---

## Bug: Broken Links in Nested Pages

### Symptom
Links in chapter pages (e.g., `html/01-foundations/page.html`) returned 404 errors.

### Root Cause
Link generation used paths like `href="index.html"` which are correct from the root but broken from nested chapter folders.

### Fix
Added `base_path` parameter to all link-generating functions:

```python
def build_sidebar(chapters_data, current_page=None, base_path=""):
    # ...
    html.append(f'<ul><li><a href="{base_path}index.html">Home</a></li></ul>')
    # ...
    html.append(f'<li><a href="{base_path}{path}"{active}>{title}</a></li>')
```

Call with `base_path="../"` for chapter pages, `base_path=""` for index.

### Prevention
Test navigation from BOTH root and nested pages before delivery.

---

## Issue: Worker Output Inconsistency

### Symptom
Different workers used different terms for the same concept (e.g., "data pruning" vs "data filtering" vs "data selection").

### Root Cause
Style guide mentioned "use consistent terminology" but didn't emphasize it strongly enough.

### Fix
1. Added explicit rule to worker prompt: "Use glossary terms as written — do NOT invent synonyms"
2. Bolded critical terms in glossary with "USE THIS TERM" notes
3. Added terminology section to style guide with specific examples

---

## Issue: Scope Creep Prevention

### What Worked
- Explicit page count in execution plan
- Chapter-by-chapter tracking
- Quality gates between phases

### What to Improve
- Get sign-off on scope BEFORE spawning workers
- Include word count estimates (not just page counts)
- Define "done" criteria upfront

---

## Cost Optimization Insights

| Component | Model | Cost Impact |
|-----------|-------|-------------|
| Research | NotebookLM | Free |
| Architecture | Main (opus) | Normal |
| Scaffolding | Main (opus) | Normal |
| Content (64 pages) | Haiku workers | ~$2-5 |
| Assembly | Python script | Zero |

**Key insight:** NotebookLM for research + haiku for content generation keeps costs very low even for large projects.

---

## Parallelization Patterns

### What Worked
- 8 workers for 64 pages (8 pages each)
- Split large chapters across multiple workers
- Shared scaffolding (style guide, glossary, page index)

### What to Improve
- Could have started foundations sequential, then parallelized rest
- Some chapters had dependencies that weren't tracked
- Consider dependency graph for complex curricula

---

## Quality Assurance

### Pre-Delivery Checklist Used
- [ ] All links work (both from root and nested pages)
- [ ] Glossary terms consistent
- [ ] Navigation complete
- [ ] Mobile-responsive
- [ ] Word count within targets

### Suggested Additions
- [ ] Spell check
- [ ] Link to external resources verified
- [ ] Images/diagrams render correctly
- [ ] Print CSS for PDF export
