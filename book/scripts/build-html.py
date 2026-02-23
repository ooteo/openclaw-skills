#!/usr/bin/env python3
"""
Convert DatologyAI wiki markdown files to HTML with navigation.
"""

import os
import re
from pathlib import Path
from datetime import datetime

# Paths
WIKI_DIR = Path(__file__).parent
CHAPTERS_DIR = WIKI_DIR / "chapters"
OUTPUT_DIR = WIKI_DIR / "html"

# Chapter metadata
CHAPTERS = [
    ("01-foundations", "Foundations"),
    ("02-scaling-problem", "The Scaling Problem"),
    ("03-data-science", "Data Science Essentials"),
    ("04-core-technology", "Core Technology"),
    ("05-business", "Business & Market Context"),
    ("06-reference", "Reference & Next Steps"),
]

CSS = """
:root {
    --bg: #1a1a2e;
    --bg-light: #16213e;
    --text: #edf2f4;
    --text-muted: #8d99ae;
    --accent: #e94560;
    --accent-light: #ff6b6b;
    --link: #4ecdc4;
    --border: #2d3748;
}

* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.7;
    display: flex;
    min-height: 100vh;
}

/* Sidebar */
.sidebar {
    width: 280px;
    background: var(--bg-light);
    padding: 2rem 1rem;
    position: fixed;
    height: 100vh;
    overflow-y: auto;
    border-right: 1px solid var(--border);
}

.sidebar h1 {
    font-size: 1.2rem;
    color: var(--accent);
    margin-bottom: 1.5rem;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid var(--accent);
}

.sidebar h2 {
    font-size: 0.85rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-top: 1.5rem;
    margin-bottom: 0.5rem;
}

.sidebar ul {
    list-style: none;
}

.sidebar li {
    margin: 0.3rem 0;
}

.sidebar a {
    color: var(--text);
    text-decoration: none;
    font-size: 0.9rem;
    display: block;
    padding: 0.3rem 0.5rem;
    border-radius: 4px;
    transition: all 0.2s;
}

.sidebar a:hover {
    background: rgba(78, 205, 196, 0.1);
    color: var(--link);
}

.sidebar a.active {
    background: rgba(233, 69, 96, 0.2);
    color: var(--accent-light);
}

/* Main content */
.main {
    margin-left: 280px;
    flex: 1;
    padding: 3rem 4rem;
    max-width: 900px;
}

.main h1 {
    font-size: 2.2rem;
    color: var(--accent-light);
    margin-bottom: 1rem;
    line-height: 1.3;
}

.main h2 {
    font-size: 1.5rem;
    color: var(--text);
    margin-top: 2.5rem;
    margin-bottom: 1rem;
    padding-bottom: 0.3rem;
    border-bottom: 1px solid var(--border);
}

.main h3 {
    font-size: 1.2rem;
    color: var(--text-muted);
    margin-top: 1.5rem;
    margin-bottom: 0.75rem;
}

.main p {
    margin-bottom: 1.2rem;
}

.main a {
    color: var(--link);
    text-decoration: none;
}

.main a:hover {
    text-decoration: underline;
}

/* TL;DR blockquote */
.main blockquote {
    background: rgba(78, 205, 196, 0.1);
    border-left: 4px solid var(--link);
    padding: 1rem 1.5rem;
    margin: 1.5rem 0;
    border-radius: 0 8px 8px 0;
}

.main blockquote strong {
    color: var(--link);
}

/* Lists */
.main ul, .main ol {
    margin: 1rem 0 1.5rem 1.5rem;
}

.main li {
    margin: 0.5rem 0;
}

/* Tables */
.main table {
    width: 100%;
    border-collapse: collapse;
    margin: 1.5rem 0;
}

.main th, .main td {
    padding: 0.75rem 1rem;
    text-align: left;
    border: 1px solid var(--border);
}

.main th {
    background: var(--bg-light);
    color: var(--accent-light);
}

.main tr:nth-child(even) {
    background: rgba(255, 255, 255, 0.02);
}

/* Code */
.main code {
    background: var(--bg-light);
    padding: 0.2rem 0.4rem;
    border-radius: 4px;
    font-size: 0.9em;
}

.main pre {
    background: var(--bg-light);
    padding: 1rem;
    border-radius: 8px;
    overflow-x: auto;
    margin: 1rem 0;
}

.main pre code {
    padding: 0;
    background: none;
}

/* Navigation */
.page-nav {
    display: flex;
    justify-content: space-between;
    margin-top: 3rem;
    padding-top: 2rem;
    border-top: 1px solid var(--border);
}

.page-nav a {
    color: var(--text-muted);
    text-decoration: none;
    padding: 0.5rem 1rem;
    border: 1px solid var(--border);
    border-radius: 4px;
    transition: all 0.2s;
}

.page-nav a:hover {
    border-color: var(--link);
    color: var(--link);
}

/* Responsive */
@media (max-width: 900px) {
    .sidebar {
        width: 100%;
        height: auto;
        position: relative;
    }
    .main {
        margin-left: 0;
        padding: 2rem;
    }
}
"""

def slugify(text):
    """Convert text to URL-friendly slug."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    return text.strip('-')

def convert_wikilinks(content, all_pages, base_path=""):
    """Convert [[WikiLinks]] to HTML links."""
    def replace_link(match):
        link_text = match.group(1)
        # Handle [[Page|Display Text]] format
        if '|' in link_text:
            target, display = link_text.split('|', 1)
        else:
            target = display = link_text
        
        # Find matching page
        slug = slugify(target)
        for page_slug, page_title, page_path in all_pages:
            if slug in page_slug or slugify(page_title) == slug:
                return f'<a href="{base_path}{page_path}">{display}</a>'
        
        # No match found, return as plain text
        return display
    
    return re.sub(r'\[\[([^\]]+)\]\]', replace_link, content)

def markdown_to_html(content):
    """Simple markdown to HTML conversion."""
    lines = content.split('\n')
    html_lines = []
    in_list = False
    in_code = False
    in_table = False
    
    for line in lines:
        # Code blocks
        if line.startswith('```'):
            if in_code:
                html_lines.append('</code></pre>')
                in_code = False
            else:
                html_lines.append('<pre><code>')
                in_code = True
            continue
        
        if in_code:
            html_lines.append(line)
            continue
        
        # Headers
        if line.startswith('# '):
            html_lines.append(f'<h1>{line[2:]}</h1>')
            continue
        elif line.startswith('## '):
            html_lines.append(f'<h2>{line[3:]}</h2>')
            continue
        elif line.startswith('### '):
            html_lines.append(f'<h3>{line[4:]}</h3>')
            continue
        
        # Blockquotes
        if line.startswith('> '):
            html_lines.append(f'<blockquote>{line[2:]}</blockquote>')
            continue
        
        # Tables
        if '|' in line and line.strip().startswith('|'):
            if not in_table:
                html_lines.append('<table>')
                in_table = True
            
            if line.strip().replace('|', '').replace('-', '').strip() == '':
                continue  # Skip separator line
            
            cells = [c.strip() for c in line.split('|')[1:-1]]
            tag = 'th' if not any('<tr>' in l for l in html_lines[-5:] if '<tr>' in l) else 'td'
            row = '<tr>' + ''.join(f'<{tag}>{c}</{tag}>' for c in cells) + '</tr>'
            html_lines.append(row)
            continue
        elif in_table:
            html_lines.append('</table>')
            in_table = False
        
        # Lists
        if line.strip().startswith('- ') or line.strip().startswith('* '):
            if not in_list:
                html_lines.append('<ul>')
                in_list = True
            html_lines.append(f'<li>{line.strip()[2:]}</li>')
            continue
        elif line.strip() and line[0].isdigit() and '. ' in line[:4]:
            if not in_list:
                html_lines.append('<ol>')
                in_list = 'ol'
            html_lines.append(f'<li>{line.split(". ", 1)[1]}</li>')
            continue
        elif in_list and line.strip() == '':
            html_lines.append('</ul>' if in_list == True else '</ol>')
            in_list = False
        
        # Bold and italic
        line = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', line)
        line = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', line)
        line = re.sub(r'`([^`]+)`', r'<code>\1</code>', line)
        
        # Paragraphs
        if line.strip():
            html_lines.append(f'<p>{line}</p>')
        else:
            html_lines.append('')
    
    if in_list:
        html_lines.append('</ul>' if in_list == True else '</ol>')
    if in_table:
        html_lines.append('</table>')
    
    return '\n'.join(html_lines)

def build_sidebar(chapters_data, current_page=None, base_path=""):
    """Build sidebar navigation HTML."""
    html = ['<nav class="sidebar">']
    html.append('<h1>DatologyAI Wiki</h1>')
    html.append(f'<ul><li><a href="{base_path}index.html">Home</a></li></ul>')
    
    for chapter_dir, chapter_name, pages in chapters_data:
        html.append(f'<h2>{chapter_name}</h2>')
        html.append('<ul>')
        for slug, title, path in pages:
            active = ' class="active"' if path == current_page else ''
            html.append(f'<li><a href="{base_path}{path}"{active}>{title}</a></li>')
        html.append('</ul>')
    
    html.append('</nav>')
    return '\n'.join(html)

def build_page(title, content, sidebar, prev_page=None, next_page=None, base_path=""):
    """Build complete HTML page."""
    nav = '<div class="page-nav">'
    if prev_page:
        nav += f'<a href="{base_path}{prev_page[1]}">← {prev_page[0]}</a>'
    else:
        nav += '<span></span>'
    if next_page:
        nav += f'<a href="{base_path}{next_page[1]}">{next_page[0]} →</a>'
    else:
        nav += '<span></span>'
    nav += '</div>'
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | DatologyAI Wiki</title>
    <style>{CSS}</style>
</head>
<body>
{sidebar}
<main class="main">
{content}
{nav}
</main>
</body>
</html>"""

def main():
    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Collect all pages
    chapters_data = []
    all_pages = []
    
    for chapter_dir, chapter_name in CHAPTERS:
        chapter_path = CHAPTERS_DIR / chapter_dir
        if not chapter_path.exists():
            continue
        
        pages = []
        for md_file in sorted(chapter_path.glob("*.md")):
            with open(md_file) as f:
                content = f.read()
            
            # Extract title from first H1
            title_match = re.search(r'^# (.+)$', content, re.MULTILINE)
            title = title_match.group(1) if title_match else md_file.stem
            
            slug = md_file.stem
            html_path = f"{chapter_dir}/{slug}.html"
            pages.append((slug, title, html_path))
            all_pages.append((slug, title, html_path))
        
        chapters_data.append((chapter_dir, chapter_name, pages))
    
    # Convert all pages
    for i, (chapter_dir, chapter_name, pages) in enumerate(chapters_data):
        chapter_path = CHAPTERS_DIR / chapter_dir
        output_chapter = OUTPUT_DIR / chapter_dir
        output_chapter.mkdir(exist_ok=True)
        
        for j, (slug, title, html_path) in enumerate(pages):
            md_file = chapter_path / f"{slug}.md"
            with open(md_file) as f:
                content = f.read()
            
            # Convert wikilinks and markdown (chapter pages need ../ prefix)
            content = convert_wikilinks(content, all_pages, base_path="../")
            html_content = markdown_to_html(content)
            
            # Build navigation
            flat_idx = sum(len(c[2]) for c in chapters_data[:i]) + j
            prev_page = all_pages[flat_idx - 1][1:] if flat_idx > 0 else None
            next_page = all_pages[flat_idx + 1][1:] if flat_idx < len(all_pages) - 1 else None
            
            # Build sidebar (chapter pages need ../ prefix for links)
            sidebar = build_sidebar(chapters_data, html_path, base_path="../")
            
            # Build complete page
            page_html = build_page(title, html_content, sidebar, prev_page, next_page, base_path="../")
            
            # Write file
            output_file = OUTPUT_DIR / html_path
            with open(output_file, 'w') as f:
                f.write(page_html)
            
            print(f"✓ {html_path}")
    
    # Create index page
    index_content = f"""<h1>DatologyAI Educational Wiki</h1>
<blockquote><strong>From "What is AI?" to exponential scaling mastery.</strong></blockquote>
<p>This wiki teaches DatologyAI's breakthrough technology for automated data curation. 
Whether you're a marketing professional, product manager, data scientist, or investor, 
you'll find content tailored to your needs.</p>

<h2>Quick Start</h2>
<ul>
<li><strong>New to AI?</strong> Start with <a href="01-foundations/01-what-is-artificial-intelligence.html">What is Artificial Intelligence</a></li>
<li><strong>Know the basics?</strong> Jump to <a href="02-scaling-problem/01-neural-scaling-laws-explained.html">Neural Scaling Laws Explained</a></li>
<li><strong>Ready for the core insight?</strong> Read <a href="04-core-technology/03-prototypicality-the-core-concept.html">Prototypicality: The Core Concept</a></li>
<li><strong>Just want the summary?</strong> See <a href="06-reference/02-key-concepts-summary.html">Key Concepts Summary</a></li>
</ul>

<h2>What You'll Learn</h2>
<p>This wiki covers:</p>
<ul>
<li><strong>The Scaling Problem</strong> — Why training AI is hitting a wall</li>
<li><strong>Data Curation</strong> — Why the right data beats more data</li>
<li><strong>Prototypicality</strong> — The core concept behind DatologyAI's approach</li>
<li><strong>Exponential Scaling</strong> — How to beat diminishing returns</li>
<li><strong>Business Context</strong> — Team, funding, market, and competitive landscape</li>
</ul>

<h2>By Audience</h2>
<ul>
<li><a href="06-reference/03-for-product-managers.html">For Product Managers</a></li>
<li><a href="06-reference/04-for-data-scientists.html">For Data Scientists</a></li>
<li><a href="06-reference/05-for-investors.html">For Investors</a></li>
</ul>

<p style="margin-top: 2rem; color: var(--text-muted); font-size: 0.9rem;">
Generated {datetime.now().strftime('%Y-%m-%d')} • 64 pages • ~87,000 words
</p>
"""
    
    sidebar = build_sidebar(chapters_data)
    index_html = build_page("Home", index_content, sidebar, 
                           next_page=all_pages[0][1:] if all_pages else None)
    
    with open(OUTPUT_DIR / "index.html", 'w') as f:
        f.write(index_html)
    
    print(f"\n✅ Wiki built: {len(all_pages)} pages in {OUTPUT_DIR}")
    print(f"   Open {OUTPUT_DIR}/index.html to view")

if __name__ == "__main__":
    main()
