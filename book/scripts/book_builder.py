#!/usr/bin/env python3
"""
book_builder.py — Autonomous Book Generator v1
OpenClaw skill: generates publication-quality books end-to-end.

Architecture (from Grok 2026-03-05):
  Markdown + YAML → Smart Router → Typst / Quarto / WeasyPrint → PDF/EPUB
  Images: mflux (MLX + Flux.1, local, arm64-native, free)

Usage:
  python3 book_builder.py --yaml book.yaml --content manuscript.md
  python3 book_builder.py --subject "FRC Robotics" --audience high-school --depth thorough
"""

import os
import sys
import json
import yaml
import argparse
import subprocess
import tempfile
import textwrap
from pathlib import Path
from typing import Optional

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────

IMAGES_DIR   = Path("images")
OUTPUT_DIR   = Path("output")
SOURCES_DIR  = Path("sources")

SUPPORTED_ENGINES = {"typst", "quarto", "weasyprint"}

LENGTH_PAGES = {
    "brief":    (5, 10),
    "guide":    (15, 30),
    "textbook": (40, 60),
    "wiki":     (60, 100),
}

DEPTH_TO_RESEARCH = {
    "quick":     "Use your training knowledge only. No external sources required.",
    "standard":  "Supplement with common knowledge and well-known references.",
    "thorough":  "Research thoroughly. Cite key sources. Prefer primary literature where available.",
    "exhaustive":"Deep research with primary literature, citations, and cross-referenced sources.",
}


# ─────────────────────────────────────────────
# SMART ROUTER
# ─────────────────────────────────────────────

def decide_engine(meta: dict) -> str:
    """Choose render backend from YAML metadata signals."""
    book_type     = meta.get("book_type", "auto").lower()
    image_density = meta.get("image_density", "low").lower()
    has_math      = meta.get("has_math", False)
    has_code      = meta.get("has_code", False)
    has_citations = meta.get("has_citations", False)

    # Explicit override
    override = meta.get("render_engine", "auto").lower()
    if override in SUPPORTED_ENGINES:
        return override

    # Infer from signals
    if book_type in {"scientific", "technical", "academic", "textbook"} \
       or has_math or has_code or has_citations:
        return "quarto"
    elif book_type in {"kids", "kids-picture", "coffee_table"} \
         or image_density in {"high", "very_high"}:
        return "weasyprint"
    else:
        return "typst"  # default — fastest, best typography


# ─────────────────────────────────────────────
# IMAGE GENERATION (mflux / Flux.1 via MLX)
# ─────────────────────────────────────────────

def generate_image(
    prompt: str,
    filename: str,
    model: str = "schnell",
    quant: int = 4,
    steps: Optional[int] = None,
    width: int = 1024,
    height: int = 1024,
    seed: Optional[int] = None,
) -> Path:
    """Generate one image with mflux (local Flux.1, arm64-native). Returns PNG path."""
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    out = IMAGES_DIR / f"{filename}.png"

    cmd = [
        "mflux-generate",
        "--model", model,
        "-q", str(quant),
        "--prompt", prompt,
        "--width", str(width),
        "--height", str(height),
        "--output", str(out),
    ]
    if steps:
        cmd.extend(["--steps", str(steps)])
    if seed is not None:
        cmd.extend(["--seed", str(seed)])

    print(f"  🖼  Generating: {filename} ({model}, q{quant}) ...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"mflux-generate failed:\n{result.stderr}")
    if not out.exists():
        raise FileNotFoundError(f"Image not created: {out}")
    print(f"      ✓ {out}")
    return out


def batch_generate_images(image_list: list[dict], book_type: str = "text_heavy") -> list[Path]:
    """
    Generate all images for a book.
    image_list: [{"filename": "cover", "prompt": "..."}, ...]
    """
    # Pick model based on book type: schnell (fast) for kids, dev (quality) for coffee_table/scientific
    model = "dev" if book_type in {"coffee_table", "scientific", "academic"} else "schnell"
    steps = 30 if model == "dev" else None

    paths = []
    for item in image_list:
        path = generate_image(
            prompt=item["prompt"],
            filename=item["filename"],
            model=model,
            steps=steps,
        )
        paths.append(path)
    return paths


# ─────────────────────────────────────────────
# LLM CALL (pluggable)
# ─────────────────────────────────────────────

def call_llm(prompt: str, model: str = "claude-opus-4-5-20251001") -> str:
    """
    Call Anthropic Claude API.
    Default: Opus for book generation quality.
    Swap model arg for haiku/sonnet on simpler tasks.
    """
    import anthropic
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
    message = client.messages.create(
        model=model,
        max_tokens=8096,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()


def parse_code_blocks(text: str) -> dict[str, str]:
    """
    Extract named code blocks from LLM output.
    Pattern: ```filename\n...\n```
    Returns: {"filename": "content", ...}
    """
    import re
    pattern = r"```([^\n`]*)\n(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    blocks = {}
    for label, content in matches:
        label = label.strip()
        if label:
            blocks[label] = content
    return blocks


def parse_image_list(text: str) -> list[dict]:
    """
    Extract image generation list from LLM output.
    Looks for JSON block labeled 'images' or a list of [IMAGE: prompt → filename] lines.
    """
    import re
    # Try JSON block first
    blocks = parse_code_blocks(text)
    if "images" in blocks:
        try:
            return json.loads(blocks["images"])
        except json.JSONDecodeError:
            pass

    # Fallback: parse [IMAGE: prompt → filename] pattern
    images = []
    for match in re.finditer(r'\[IMAGE:\s*(.+?)\s*→\s*(\S+)\]', text):
        images.append({"prompt": match.group(1), "filename": match.group(2)})
    return images


# ─────────────────────────────────────────────
# MANUSCRIPT GENERATION
# ─────────────────────────────────────────────

MANUSCRIPT_PROMPT = """You are an expert educational content creator and book author.

BOOK METADATA:
{yaml_str}

RESEARCH GUIDANCE:
{research_guidance}

TASK:
Write a complete, structured manuscript for this book in Markdown format.

Requirements:
- Use proper Markdown headings (# for chapters, ## for sections, ### for subsections)
- Write for the specified audience: {audience}
- Voice/tone: {voice}
- Perspective/framing: {perspective}
- Target length: {length_guidance}
- Pedagogy style: {pedagogy}
{glossary_req}
{exercises_req}
{references_req}

For each image needed, insert a marker: [IMAGE: detailed visual description → filename_no_ext]

Output ONLY the Markdown manuscript. No preamble, no explanation.
"""

def generate_manuscript(meta: dict) -> str:
    """Generate full manuscript via LLM."""
    length_hint = meta.get("length", "standard")
    if length_hint in LENGTH_PAGES:
        lo, hi = LENGTH_PAGES[length_hint]
        length_guidance = f"approximately {lo}-{hi} pages"
    else:
        try:
            n = int(length_hint)
            length_guidance = f"approximately {n} pages"
        except (ValueError, TypeError):
            length_guidance = "standard length"

    prompt = MANUSCRIPT_PROMPT.format(
        yaml_str=yaml.dump(meta, allow_unicode=True),
        research_guidance=DEPTH_TO_RESEARCH.get(meta.get("depth", "standard"), ""),
        audience=meta.get("audience", "general public"),
        voice=meta.get("voice", "conversational"),
        perspective=meta.get("perspective", "explanatory"),
        length_guidance=length_guidance,
        pedagogy=meta.get("pedagogy", "explanatory"),
        glossary_req="- Include a Glossary section at the end." if meta.get("glossary") else "",
        exercises_req="- Include end-of-chapter exercises/questions." if meta.get("exercises") else "",
        references_req=f"- Include {meta.get('references', 'no')} references in {meta.get('citation_style', 'APA')} style."
                       if meta.get("publication_ready") or meta.get("references", "none") != "none"
                       else "- No references required.",
    )
    print("  📝 Generating manuscript via LLM...")
    return call_llm(prompt)


# ─────────────────────────────────────────────
# FORMAT PROMPTS
# ─────────────────────────────────────────────

TYPST_FORMAT_PROMPT = """You are an expert Typst book production engineer for autonomous generation.

YAML METADATA:
{yaml_str}

MANUSCRIPT (Markdown):
{content}

RULES (follow exactly):
1. Output a complete, compilable Typst file (main.typ).
2. Use #import "@preview/ilm:2.0.0": * for nonfiction/textbook, or minimal template for fiction.
3. Convert all Markdown headings → Typst headings (#heading[...]).
4. Convert lists, tables, quotes, code blocks to proper Typst syntax.
5. Add running headers: chapter title left, author right.
6. Place images via: #figure(image("images/FILENAME.png", width: 100%), caption: [Caption])
7. Use #pagebreak() at natural chapter breaks.
8. At end, output a JSON code block labeled 'images' with all required images:
   ```images
   [{{"filename": "cover", "prompt": "detailed description..."}}]
   ```
9. Output ONLY the .typ file content + the images JSON block. No explanation.
"""

QUARTO_FORMAT_PROMPT = """You are an expert Quarto + Typst book production engineer.

YAML METADATA:
{yaml_str}

MANUSCRIPT (Markdown):
{content}

RULES:
1. Output a complete Quarto book project. Use Typst PDF backend for quality.
2. Structure: _quarto.yml + index.qmd + one .qmd per chapter.
3. Enable cross-references, citations, math (if present), code highlighting.
4. For figures: use standard Quarto figure syntax with images/ paths.
5. Output each file as a labeled code block: ```_quarto.yml ... ``` ```01-intro.qmd ... ```
6. At end, JSON images block:
   ```images
   [{{"filename": "fig1", "prompt": "..."}}]
   ```
7. Output ONLY the file code blocks + images JSON. No explanation.
"""

WEASYPRINT_FORMAT_PROMPT = """You are an expert print-ready HTML/CSS book formatter for WeasyPrint.

YAML METADATA:
{yaml_str}

MANUSCRIPT (Markdown with [IMAGE: prompt → filename] markers):
{content}

TRIM SIZE: {trim_size}

RULES:
1. Output book.html + style.css as two labeled code blocks.
2. Use @page CSS rules for the specified trim size, bleed 0.125in, crop marks.
3. For kids books: full-bleed spreads, large text, colorful layout.
4. Replace [IMAGE: prompt → filename] with: <img src="images/filename.png" alt="prompt">
5. Use CSS grid/flex for page layouts. Proper page breaks between chapters/spreads.
6. At end, JSON images block:
   ```images
   [{{"filename": "spread1", "prompt": "..."}}]
   ```
7. Output ONLY book.html code block + style.css code block + images JSON.
"""


def format_for_typst(meta: dict, content: str) -> tuple[str, list[dict]]:
    prompt = TYPST_FORMAT_PROMPT.format(yaml_str=yaml.dump(meta), content=content)
    print("  🔧 Formatting for Typst...")
    raw = call_llm(prompt)
    blocks = parse_code_blocks(raw)
    typst_content = blocks.get("typst", raw)  # fallback to full output
    images = parse_image_list(raw)
    return typst_content, images


def format_for_quarto(meta: dict, content: str) -> tuple[dict[str, str], list[dict]]:
    prompt = QUARTO_FORMAT_PROMPT.format(yaml_str=yaml.dump(meta), content=content)
    print("  🔧 Formatting for Quarto...")
    raw = call_llm(prompt)
    blocks = parse_code_blocks(raw)
    images = parse_image_list(raw)
    return blocks, images


def format_for_weasyprint(meta: dict, content: str) -> tuple[str, str, list[dict]]:
    prompt = WEASYPRINT_FORMAT_PROMPT.format(
        yaml_str=yaml.dump(meta),
        content=content,
        trim_size=meta.get("trim_size", "8.5x11"),
    )
    print("  🔧 Formatting for WeasyPrint...")
    raw = call_llm(prompt)
    blocks = parse_code_blocks(raw)
    html    = blocks.get("html", blocks.get("book.html", ""))
    css     = blocks.get("css",  blocks.get("style.css", ""))
    images  = parse_image_list(raw)
    return html, css, images


# ─────────────────────────────────────────────
# COMPILERS
# ─────────────────────────────────────────────

def compile_typst(typst_content: str, out_pdf: Path):
    """Write .typ file and compile to PDF."""
    with tempfile.NamedTemporaryFile(suffix=".typ", delete=False, mode="w", encoding="utf-8") as f:
        f.write(typst_content)
        tmp = Path(f.name)
    try:
        subprocess.run(["typst", "compile", str(tmp), str(out_pdf)], check=True)
    finally:
        tmp.unlink(missing_ok=True)
    print(f"  ✓ PDF: {out_pdf}")


def compile_quarto(file_blocks: dict[str, str], out_dir: Path):
    """Write Quarto project files and render."""
    out_dir.mkdir(parents=True, exist_ok=True)
    for filename, content in file_blocks.items():
        (out_dir / filename).write_text(content, encoding="utf-8")
    orig = os.getcwd()
    try:
        os.chdir(out_dir)
        subprocess.run(["quarto", "render"], check=True)
    finally:
        os.chdir(orig)
    print(f"  ✓ Quarto output: {out_dir}")


def compile_weasyprint(html: str, css: str, out_pdf: Path):
    """Write HTML/CSS and render to PDF with WeasyPrint."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        # Copy images symlink
        if IMAGES_DIR.exists():
            img_link = tmp_dir / "images"
            img_link.symlink_to(IMAGES_DIR.resolve())
        (tmp_dir / "book.html").write_text(html, encoding="utf-8")
        (tmp_dir / "style.css").write_text(css, encoding="utf-8")
        subprocess.run([
            "weasyprint",
            str(tmp_dir / "book.html"),
            str(out_pdf),
            "--pdf-bleed", "0.125in",
        ], check=True)
    print(f"  ✓ PDF: {out_pdf}")


# ─────────────────────────────────────────────
# EPUB EXPORT (via Pandoc)
# ─────────────────────────────────────────────

def export_epub(manuscript_md: str, meta: dict, out_epub: Path):
    """Convert Markdown manuscript to EPUB via Pandoc."""
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False, mode="w") as f:
        f.write(manuscript_md)
        tmp = Path(f.name)
    try:
        cmd = [
            "pandoc", str(tmp),
            "-o", str(out_epub),
            "--metadata", f"title={meta.get('title', 'Book')}",
            "--metadata", f"author={meta.get('author', 'Unknown')}",
            "--toc",
        ]
        subprocess.run(cmd, check=True)
        print(f"  ✓ EPUB: {out_epub}")
    finally:
        tmp.unlink(missing_ok=True)


# ─────────────────────────────────────────────
# MAIN BUILD ORCHESTRATOR
# ─────────────────────────────────────────────

def build_book(
    meta: dict,
    manuscript: str,
    output_dir: Path = OUTPUT_DIR,
    override_engine: Optional[str] = None,
    save_sources: bool = False,
):
    """Full pipeline: format → generate images → compile → EPUB."""
    output_dir.mkdir(parents=True, exist_ok=True)
    title_slug = meta.get("title", "book").replace(" ", "_").lower()[:40]

    engine = override_engine or decide_engine(meta)
    print(f"\n📚 Building: {meta.get('title', 'Untitled')}")
    print(f"   Engine: {engine} | Book type: {meta.get('book_type', 'auto')}")

    image_list = []
    out_pdf    = output_dir / f"{title_slug}.pdf"
    out_epub   = output_dir / f"{title_slug}.epub"

    if engine == "typst":
        typst_src, image_list = format_for_typst(meta, manuscript)
        if image_list:
            batch_generate_images(image_list, meta.get("book_type", "text_heavy"))
        compile_typst(typst_src, out_pdf)

    elif engine == "quarto":
        quarto_dir = output_dir / "quarto_project"
        file_blocks, image_list = format_for_quarto(meta, manuscript)
        if image_list:
            batch_generate_images(image_list, meta.get("book_type", "scientific"))
        # Copy images into project
        if IMAGES_DIR.exists():
            (quarto_dir / "images").mkdir(parents=True, exist_ok=True)
            for img in IMAGES_DIR.glob("*.png"):
                import shutil
                shutil.copy(img, quarto_dir / "images" / img.name)
        compile_quarto(file_blocks, quarto_dir)

    elif engine == "weasyprint":
        html, css, image_list = format_for_weasyprint(meta, manuscript)
        if image_list:
            batch_generate_images(image_list, meta.get("book_type", "kids"))
        compile_weasyprint(html, css, out_pdf)

    # EPUB export (via Pandoc, works for all engines from Markdown)
    formats = meta.get("output_formats", ["pdf"])
    if "epub" in formats:
        export_epub(manuscript, meta, out_epub)

    print(f"\n✅ Done! Output: {output_dir}")
    return output_dir


# ─────────────────────────────────────────────
# YAML BUILDER (from CLI args)
# ─────────────────────────────────────────────

def build_meta_from_args(args) -> dict:
    """Build YAML metadata dict from CLI arguments."""
    meta = {
        "title":          args.title or f"A Guide to {args.subject}",
        "subtitle":       args.subtitle or "",
        "author":         args.author or "OpenClaw Press",
        "subject":        args.subject,
        "book_type":      args.book_type or "auto",
        "audience":       args.audience or "general",
        "voice":          args.voice or "conversational",
        "perspective":    args.perspective or "explanatory",
        "depth":          args.depth or "standard",
        "length":         args.length or "guide",
        "pedagogy":       args.pedagogy or "explanatory",
        "image_density":  "medium",
        "has_math":       False,
        "has_code":       False,
        "has_citations":  args.publication_ready or False,
        "trim_size":      args.trim_size or "6x9",
        "output_formats": ["pdf"],
        "theme":          args.theme or "classic",
        "render_engine":  args.engine or "auto",
        "references":     "bibliography" if args.publication_ready else (args.references or "none"),
        "citation_style": args.citation_style or "APA",
        "glossary":       args.glossary,
        "exercises":      args.exercises,
        "publication_ready": args.publication_ready or False,
    }
    if args.epub:
        meta["output_formats"].append("epub")
    if args.book_type in {"kids", "coffee_table"}:
        meta["image_density"] = "high"
    return meta


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="Autonomous Book Generator v1")

    # From YAML + manuscript (pre-existing)
    p.add_argument("--yaml",    help="Path to book.yaml metadata file")
    p.add_argument("--content", help="Path to existing Markdown manuscript")

    # Generate from scratch
    p.add_argument("--subject",       help="Book subject / topic")
    p.add_argument("--title",         help="Book title (default: auto)")
    p.add_argument("--subtitle",      help="Subtitle")
    p.add_argument("--author",        help="Author name")
    p.add_argument("--book-type",     default="auto",
                   choices=["auto","textbook","fiction","kids","scientific","coffee_table","guide","wiki"])
    p.add_argument("--audience",      default="general",
                   help="K-8 | high-school | undergrad | grad | professional | general")
    p.add_argument("--voice",         default="conversational",
                   choices=["academic","conversational","field-guide","reference","story-driven"])
    p.add_argument("--perspective",   default="explanatory",
                   choices=["first-principles","chronological","comparative","practitioner","Socratic","narrative","explanatory"])
    p.add_argument("--depth",         default="standard",
                   choices=["quick","standard","thorough","exhaustive"])
    p.add_argument("--length",        default="guide",
                   help="brief | guide | textbook | wiki | N (pages)")
    p.add_argument("--pedagogy",      default="explanatory",
                   choices=["explanatory","Socratic","project-based","case-study"])
    p.add_argument("--theme",         default="classic",
                   choices=["classic","modern","playful","minimal"])
    p.add_argument("--trim-size",     default="6x9",
                   choices=["6x9","8.5x11","square","letter"])
    p.add_argument("--references",    default="none",
                   choices=["none","inline","bibliography","full-citation"])
    p.add_argument("--citation-style",default="APA",
                   choices=["APA","MLA","Chicago","IEEE"])
    p.add_argument("--engine",        default="auto",
                   choices=["auto","typst","quarto","weasyprint"])
    p.add_argument("--glossary",      action="store_true")
    p.add_argument("--exercises",     action="store_true")
    p.add_argument("--epub",          action="store_true")
    p.add_argument("--publication-ready", action="store_true",
                   help="Enable references, bibliography, proper citations")
    p.add_argument("--save-sources",  action="store_true",
                   help="Archive source materials reviewed during generation")
    p.add_argument("--output",        default="output", help="Output directory")
    p.add_argument("--llm-model",     default="qwen2.5:7b",
                   help="Ollama model for content generation (default: qwen2.5:7b)")

    args = p.parse_args()
    output_dir = Path(args.output)

    # Path 1: pre-existing YAML + manuscript
    if args.yaml and args.content:
        meta       = yaml.safe_load(Path(args.yaml).read_text())
        manuscript = Path(args.content).read_text()

    # Path 2: generate from subject
    elif args.subject:
        meta       = build_meta_from_args(args)
        # Save YAML
        output_dir.mkdir(parents=True, exist_ok=True)
        yaml_out = output_dir / "book.yaml"
        yaml_out.write_text(yaml.dump(meta, allow_unicode=True))
        print(f"📋 YAML saved: {yaml_out}")

        # Generate manuscript
        manuscript = generate_manuscript(meta)
        md_out = output_dir / "manuscript.md"
        md_out.write_text(manuscript, encoding="utf-8")
        print(f"📝 Manuscript saved: {md_out}")

    else:
        p.print_help()
        print("\nError: provide either --yaml + --content, or --subject")
        sys.exit(1)

    # Build
    build_book(
        meta=meta,
        manuscript=manuscript,
        output_dir=output_dir,
        override_engine=args.engine if args.engine != "auto" else None,
        save_sources=args.save_sources,
    )


if __name__ == "__main__":
    main()
