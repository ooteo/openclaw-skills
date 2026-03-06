# Book Generator Skill

Generate comprehensive, publication-quality educational content (wikis, textbooks, guides, kids books, scientific papers) from research — fully autonomic, end-to-end.

## When to use this skill

Use when creating:
- Textbooks, guides, wikis for any subject/audience
- Children's books or illustrated books
- Scientific/technical/academic documents
- Coffee table / image-heavy books
- Any "book-like" content requiring research synthesis + professional output

## Tools Required

Install once:
```bash
brew install typst quarto
pip install weasyprint pillow cairosvg mflux
```

## Quick Invocation

Gather parameters from the user (all optional except subject), then run:

```bash
python3 ~/.openclaw/skills/book/scripts/book_builder.py \
  --subject "SUBJECT" \
  --audience "AUDIENCE" \
  --depth "quick|standard|thorough|exhaustive" \
  --format "pdf|epub|html-wiki|print-book" \
  --book-type "auto|textbook|fiction|kids|scientific|coffee_table" \
  --output ~/Desktop/my_book/
```

Or build from existing YAML + manuscript:
```bash
python3 ~/.openclaw/skills/book/scripts/book_builder.py \
  --yaml book.yaml --content manuscript.md
```

## Parameters

### Subject / Content
| Parameter | Values | Description |
|-----------|--------|-------------|
| `subject` | any string | Topic or composite ("calculus for musicians") |
| `perspective` | first-principles \| chronological \| comparative \| practitioner \| Socratic \| narrative | Framing lens |
| `audience` | K-8 \| high-school \| undergrad \| grad \| professional \| general | Target audience |
| `voice` | academic \| conversational \| field-guide \| reference \| story-driven | Tone |

### Research
| Parameter | Values | Default | Description |
|-----------|--------|---------|-------------|
| `depth` | quick \| standard \| thorough \| exhaustive | standard | Research depth |
| `sources` | provided \| auto-discover \| none | none | Source strategy |
| `save-sources` | bool | false | Archive reviewed materials |
| `references` | none \| inline \| bibliography \| full-citation | none | Citation format |
| `citation-style` | APA \| MLA \| Chicago \| IEEE | APA | Only when references enabled |

### Output Format
| Parameter | Values | Default | Description |
|-----------|--------|---------|-------------|
| `format` | html-wiki \| static-site \| pdf \| epub \| print-book | pdf | Output format |
| `book-type` | auto \| textbook \| fiction \| kids \| scientific \| coffee_table | auto | Router hint |
| `length` | brief \| guide \| textbook \| wiki \| N (pages) | standard | Length target |
| `theme` | classic \| modern \| playful \| minimal | classic | Visual style |
| `trim-size` | 8.5x11 \| 6x9 \| square \| letter | 6x9 | Page dimensions |

### Features
| Parameter | Values | Default | Description |
|-----------|--------|---------|-------------|
| `glossary` | bool | false | Auto-generate glossary |
| `exercises` | bool | false | End-of-chapter questions |
| `pedagogy` | explanatory \| Socratic \| project-based \| case-study | explanatory | Teaching style |
| `publication-ready` | bool | false | Enables references+bibliography+citation |

## Smart Router

Auto-selects render backend from YAML signals:
- `scientific` / `technical` / `academic` / `has_math` / `has_code` → **Quarto** (Typst backend)
- `kids` / `coffee_table` / `image_density: high|very_high` → **WeasyPrint** (HTML/CSS)
- everything else → **Typst** (default — fastest, best typography)

Override with `render_engine: typst|quarto|weasyprint` in YAML.

## Render Backends (v1, all free)

| Backend | Best For | Output |
|---------|----------|--------|
| Typst | Fiction, nonfiction, guides, wikis | PDF + EPUB |
| Quarto | Scientific, technical, academic, math | PDF + EPUB |
| WeasyPrint | Kids books, coffee table, image-heavy | PDF |

## Image Generation (local, free)

Uses **mflux** (MLX + Flux.1, arm64-native):
- `schnell` model: ~10s/image, great for kids books
- `dev` model: ~60s/image, publication quality

```bash
# Install
uv pip install mflux
# Test
mflux-generate --model schnell -q 4 --prompt "test" --output test.png
```

## v2 Roadmap (requires paid tools)
- PrinceXML: superior print quality for image-heavy books
- Adobe CC / InDesign: professional layout for coffee table books  
- Adobe Express SDK (client: 3e39c400cfc2481eb4b942d07baabca0): browser-based image editing

## Output Structure

```
output/
├── book.yaml          # Metadata
├── manuscript.md      # Raw content
├── images/            # Generated images
├── book.pdf           # Final PDF
├── book.epub          # EPUB (when requested)
└── sources/           # Archived sources (when save-sources=true)
```

## Workflow

1. **Gather params** from user conversation
2. **Research** (if depth ≥ standard): web search → NotebookLM → sources list
3. **Generate YAML** front-matter from params
4. **Generate manuscript** (Markdown, structured) using LLM with subject/audience/voice
5. **Route** to render backend via smart router
6. **Generate images** via mflux (extract prompts from manuscript)
7. **Compile** to PDF/EPUB
8. **Add references** if publication-ready
9. **Deliver** output path to user
