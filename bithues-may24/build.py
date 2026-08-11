import json
#!/usr/bin/env python3
"""
build.py — Bithues Site Generator

Parses Markdown story files and generates:
  - index.html              (homepage with featured stories, articles, reviews)
  - stories.html           (paginated story listing)
  - <slug>.html            (individual story pages, with page-turn for long stories)
  - articles.html          (article listing page)
  - reviews.html          (review listing page)
  - articles/<slug>.html   (individual article pages)
  - reviews/<slug>.html    (individual review pages)
  - about.html, contact.html, privacy.html, terms.html

Run: python3 build.py
"""

import codecs
import os
import re
import shutil
import string
from datetime import datetime, date
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
STORIES_DIR     = Path(__file__).parent.parent / "content" / "stories"
ARTICLES_DIR    = Path(__file__).parent.parent / "content" / "articles"
REVIEWS_DIR     = Path(__file__).parent.parent / "content" / "reviews"
NEWSLETTERS_DIR = Path(__file__).parent.parent / "content" / "newsletters"
OUTPUT_DIR      = Path(__file__).parent
TEMPLATE_DIR    = Path(__file__).parent

PAGINATE       = 9999  # all on one page — pagination removed 2026-06-01
REVIEWS_PAGINATE = 50   # reviews per listing page — keep high so genre filter sees all
BASE_URL       = "https://bithues.com"
PAGE_THRESHOLD = 2000  # word count → split into pages
CHUNK_SIZE     = 1500  # target words per page

# ── Front Matter Parser ─────────────────────────────────────────────────────────
def parse_front_matter(content: str) -> tuple[dict, str]:
    """Return (metadata_dict, body_text) from MD file content."""
    # Strip leading newlines before checking for opening --- marker
    stripped = content.lstrip('\n')
    leading_newlines = len(content) - len(stripped)
    if not stripped.startswith("---"):
        return {}, content
    end = stripped.find("\n---", 4)
    if end == -1:
        return {}, content
    fm_text = stripped[4:end]
    body    = stripped[end + 4:].lstrip("\n")

    meta = {}
    for line in fm_text.split("\n"):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        # Split on first colon only
        colon_idx = line.find(':')
        if colon_idx == -1:
            continue
        key = line[:colon_idx].strip()
        val = line[colon_idx+1:].strip()

        if val in ("null", "None"):
            meta[key] = None
        elif val in ("true", "True"):
            meta[key] = True
        elif val in ("false", "False"):
            meta[key] = False
        elif (val.startswith('"') and val.endswith('"')) or \
             (val.startswith("'") and val.endswith("'")):
            # Remove surrounding quotes only — do NOT decode unicode_escape
            # Unicode escape misinterprets UTF-8 bytes (em-dashes, etc.) as escape sequences
            meta[key] = val[1:-1]
        elif val.startswith('[') and val.endswith(']'):
            # JSON array
            try:
                meta[key] = json.loads(val)
            except Exception:
                meta[key] = val
        else:
            meta[key] = val
    # Doctrine (2026-08-05): meta description must be ≤160 chars
    # (Google truncates around 155-160). Trim if longer.
    # Apply to BOTH `description` and `summary` because some templates
    # (e.g. newsletters) use `summary` as the meta tag source.
    for _key in ("description", "summary"):
        _val = meta.get(_key)
        if _val and len(_val) > 160:
            meta[_key] = _val[:160]
    return meta, body


def slug_from_path(path: Path) -> str:
    return path.stem


# ── Word Count (strip front matter) ────────────────────────────────────────────
def story_word_count(raw_content: str) -> int:
    _, body = parse_front_matter(raw_content)
    return len(body.split())


# ── Chunk a story body into pages ─────────────────────────────────────────────
def chunk_body(body: str, chunk_size: int = CHUNK_SIZE) -> list[str]:
    """
    Split body text into pages of ~chunk_size words.
    Returns a list of page bodies. Always at least 1.
    """
    paras = [p.strip() for p in body.split("\n\n") if p.strip()]

    if len(paras) > 1:
        pages, current, words = [], [], 0
        for para in paras:
            w = len(para.split())
            if current and words + w > chunk_size:
                pages.append("\n\n".join(current))
                current, words = [], 0
            current.append(para)
            words += w
        if current:
            pages.append("\n\n".join(current))
    else:
        sentences = re.split(r"(?<=[.!?])\s+", body.strip())
        pages, current, words = [], [], 0
        for sent in sentences:
            sent = sent.strip()
            if not sent:
                continue
            w = len(sent.split())
            if current and words + w > chunk_size:
                pages.append(" ".join(current))
                current, words = [], 0
            current.append(sent)
            words += w
        if current:
            pages.append(" ".join(current))

    return pages if pages else [body]


# ── MD Body → HTML ─────────────────────────────────────────────────────────────
def md_to_html(body: str, meta: dict) -> str:
    """Convert simple Markdown to HTML paragraph block."""
    lines = body.split("\n")
    html_parts = []
    in_ul = False
    in_ol = False
    in_table = False

    def parse_table_row(line: str) -> str:
        """Parse a markdown table row into HTML <tr> cells."""
        # Strip leading/trailing pipes, split on pipe
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        cells_html = "".join(f"<td>{wrap_inline(c)}</td>" for c in cells)
        return f"<tr>{cells_html}</tr>\n"

    def wrap_inline(text: str) -> str:
        # Markdown links: [text](url) → <a href="url">text</a>
        def _link(m):
            label, href = m.group(1), m.group(2)
            extra = ' target="_blank" rel="noopener"' if href.startswith("http") else ""
            return f'<a href="{href}"{extra}>{label}</a>'
        text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", _link, text)
        text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
        text = re.sub(r"\*(.+?)\*",      r"<em>\1</em>",       text)
        text = re.sub(r"`(.+?)`",         r"<code>\1</code>",   text)
        return text

    for raw in lines:
        line = raw.strip()

        if line in ("---", "----"):
            continue

        # Markdown table: line starts with |
        if line.startswith("|"):
            # Close open lists before table
            if in_ul:
                html_parts.append("</ul>")
                in_ul = False
            if in_ol:
                html_parts.append("</ol>")
                in_ol = False
            if not in_table:
                html_parts.append('<div class="table-wrapper"><table>')
                in_table = True
            # Skip separator rows (| :-- | :-- |)
            if re.match(r"^\|[\s\-:|]+\|$", line):
                continue
            html_parts.append(parse_table_row(line))
            continue
        else:
            if in_table:
                html_parts.append("</table></div>")
                in_table = False

        if line.startswith("#### "):
            html_parts.append(f"<h4>{wrap_inline(line[5:])}</h4>")
            continue
        elif line.startswith("### "):
            html_parts.append(f"<h3>{wrap_inline(line[4:])}</h3>")
            continue
        elif line.startswith("## "):
            html_parts.append(f"<h2>{wrap_inline(line[3:])}</h2>")
            continue
        elif line.startswith("# "):
            html_parts.append(f"<h1>{wrap_inline(line[2:])}</h1>")
            continue

        if line.startswith("- ") or line.startswith("* "):
            if not in_ul:
                html_parts.append("<ul>")
                in_ul = True
            html_parts.append(f"  <li>{wrap_inline(line[2:])}</li>")
            continue
        else:
            if in_ul:
                html_parts.append("</ul>")
                in_ul = False

        m = re.match(r"^\d+\.\s+(.*)$", line)
        if m:
            if not in_ol:
                html_parts.append("<ol>")
                in_ol = True
            html_parts.append(f"  <li>{wrap_inline(m.group(1))}</li>")
            continue
        else:
            if in_ol:
                html_parts.append("</ol>")
                in_ol = False

        if line.startswith("> "):
            html_parts.append(f"<blockquote>{wrap_inline(line[2:])}</blockquote>")
            continue

        # Scene break: ··· (three dots with thin spaces)
        if line.strip() == "···" or line.strip() == "···":
            html_parts.append('<div class="scene-break" aria-hidden="true"></div>')
            continue

        # Markdown links: [text](url)
        m_link = re.match(r"^\[([^\]]+)\]\(([^)]+)\)", line.strip())
        if m_link:
            link_text = m_link.group(1)
            link_url = m_link.group(2)
            # External Amazon links get target=_blank
            extra = ' target="_blank" rel="noopener"' if link_url.startswith("http") else ""
            html_parts.append(f'<p><a href="{link_url}"{extra}>{link_text}</a></p>')
            continue

        # Markdown image: ![alt](url) → <img src="url" alt="alt">
        m_img = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)", line.strip())
        if m_img:
            alt_text = m_img.group(1) or ""
            img_url = m_img.group(2)
            html_parts.append(f'<p><img src="{img_url}" alt="{alt_text}" style="max-width:100%;border-radius:4px;margin-bottom:1.5rem;"></p>')
            continue

        # Lines containing HTML - pass through without any wrapping
        if line.strip().startswith('<'):
            html_parts.append(line.strip())
            continue

        if not line:
            continue

        html_parts.append(f"<p>{wrap_inline(line)}</p>")

    if in_table:
        html_parts.append("</table></div>")
        in_table = False

    html = "\n".join(html_parts)

    def md_to_html_link(m):
        href = m.group(1)
        rest = m.group(2)
        if href.endswith('.md'):
            href = href[:-3]  # strip .md extension (no .html added in directory structure)
        return f'href="{href}"{rest}'

    html = re.sub(r'href="([^"]+\.md)"([^>]*?)(?=>|\s)', md_to_html_link, html)

    # ── Post-process: wrap "### Get the Books" + <ul> in amazon-book-list div ──
    html = re.sub(
        r'(<h3>Get the Books</h3>\s*<ul>)',
        r'<div class="amazon-book-list">\1',
        html
    )
    # Close the div right after the </ul> that immediately follows Get the Books
    html = re.sub(
        r'(<h3>Get the Books</h3>\s*<ul>.*?</ul>)',
        r'\1\n</div>',
        html,
        flags=re.DOTALL
    )

    # Wrap " by Author Name" in each book list <li> with a <span class="book-author">
    html = re.sub(
        r'(</a>)(\s+by\s+[^<]+\s*)(</li>)',
        r'\1<span class="book-author">\2</span>\3',
        html
    )

    return html


# ── Load Template ───────────────────────────────────────────────────────────────
def load_template(name: str) -> str:
    p = TEMPLATE_DIR / name
    if p.exists():
        return p.read_text(encoding="utf-8")
    return ""


def wrap_in_template(page_title: str, page_desc: str, main_html: str,
                     active_nav: str = "", canonical_path: str = "/",
                     meta: dict = None, schema_type: str = "",
                     schema_extra: list = None) -> str:
    SFX = " | Bithues"
    page_title_full = page_title if page_title.endswith(SFX) else page_title + SFX

    tmpl = load_template("_template.html")
    tmpl = tmpl.replace("PAGE TITLE",        page_title_full,  1)
    tmpl = tmpl.replace("PAGE DESCRIPTION",  page_desc,        1)
    tmpl = tmpl.replace("<!-- PAGE CONTENT GOES HERE -->", main_html, 1)
    if active_nav:
        tmpl = tmpl.replace(
            f'href="/{active_nav}/"',
            f'href="/{active_nav}/" class="active"',
        )
        # legacy bare-form fallback (kept for templates that haven't been updated)
        tmpl = tmpl.replace(
            f'href="/{active_nav}"',
            f'href="/{active_nav}/" class="active"',
        )
    tmpl = tmpl.replace("CANONICAL_PLACEHOLDER", BASE_URL + canonical_path, 1)
    # Inject JSON-LD schema.org structured data before </head>
    canonical_url = BASE_URL + canonical_path
    json_ld = build_schema_json_ld(schema_type, meta or {}, canonical_url, page_title, page_desc,
                                   schema_extra=schema_extra or [])
    if json_ld:
        tmpl = tmpl.replace("</head>", json_ld + "\n</head>", 1)
    return tmpl


# ── Schema.org JSON-LD Builder ─────────────────────────────────────────────────
def _json_ld_escape(s: str) -> str:
    """Escape a string for safe inclusion in JSON-LD."""
    if not s:
        return ""
    return (s.replace("\\", "\\\\")
             .replace('"', '\\"')
             .replace("\n", " ")
             .replace("\r", "")
             .replace("\t", " "))[:2000]


def build_schema_json_ld(schema_type: str, meta: dict, canonical_url: str,
                         page_title: str, page_desc: str,
                         schema_extra: list = None) -> str:
    """
    Build a JSON-LD <script> block for the given page type.
    Returns "" for types that don't need page-specific schema (or no meta).

    Types:
      - "website"  : Homepage — WebSite + Organization
      - "review"   : Book review — Review + Book + BreadcrumbList
      - "article"  : Article/essay — Article + BreadcrumbList + Person
      - "story"    : Original fiction — CreativeWork + BreadcrumbList
      - "newsletter": Newsletter — Article + ItemList of books featured

    schema_extra: list of additional schema.org objects to append to the @graph
    (used for listing pages that want an ItemList appended).
    """
    if not schema_type:
        # If no page-level type but schema_extra is provided, wrap just the extras.
        if schema_extra:
            return _wrap_json_ld(schema_extra)
        return ""

    org_id = f"{BASE_URL}/#organization"
    website_id = f"{BASE_URL}/#website"
    og_image = f"{BASE_URL}/og-image.jpg"

    def _abs_image(path_or_url: str) -> str:
        """Convert a relative image path to an absolute URL for schema.org."""
        if not path_or_url:
            return ""
        if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
            return path_or_url
        # Relative — prepend BASE_URL with leading slash
        if path_or_url.startswith("/"):
            return BASE_URL + path_or_url
        return BASE_URL + "/" + path_or_url

    # ── Website + Organization (homepage) ──
    if schema_type == "website":
        graph = [
            {
                "@type": "WebSite",
                "@id": website_id,
                "url": BASE_URL + "/",
                "name": "Bithues",
                "description": "An independent book review site and indie short-fiction publisher. Honest, editor-vetted reviews of fiction, nonfiction, and children's literature — plus original short stories.",
                "publisher": {"@id": org_id},
                "potentialAction": {
                    "@type": "SearchAction",
                    "target": f"{BASE_URL}/search?q={{search_term_string}}",
                    "query-input": "required name=search_term_string"
                }
            },
            {
                "@type": "Organization",
                "@id": org_id,
                "name": "Bithues",
                "url": BASE_URL + "/",
                "logo": {"@type": "ImageObject", "url": og_image},
                "sameAs": []
            }
        ]
        return _wrap_json_ld(graph)

    # ── Review (book review pages) ──
    if schema_type == "review":
        book_title    = _json_ld_escape(meta.get("title", ""))
        book_author   = _json_ld_escape(meta.get("author", "") or meta.get("book_author", ""))
        rating        = meta.get("rating") or meta.get("score") or ""
        date_pub      = _json_ld_escape(meta.get("date", "") or meta.get("review_date", "") or "")
        review_author = _json_ld_escape(meta.get("reviewer", "") or meta.get("author", "") or "Bithues Editors")
        isbn          = _json_ld_escape(meta.get("isbn", "") or meta.get("isbn13", ""))
        genre         = _json_ld_escape(meta.get("genre", "") or meta.get("category", ""))
        cover_url     = _abs_image(meta.get("cover_image", "") or meta.get("card_image", "") or "")

        book = {"@type": "Book", "name": book_title}
        if book_author:
            book["author"] = {"@type": "Person", "name": book_author}
        if date_pub:
            book["datePublished"] = date_pub
        if genre:
            book["genre"] = genre
        if isbn:
            book["isbn"] = isbn
        if cover_url:
            book["image"] = cover_url

        review = {
            "@type": "Review",
            "itemReviewed": book,
            "reviewBody": _json_ld_escape(meta.get("summary", "") or page_desc),
            "author": {"@type": "Person", "name": review_author},
            "url": canonical_url,
            "publisher": {"@id": org_id},
        }
        if date_pub:
            review["datePublished"] = date_pub
        if rating and str(rating).replace(".", "").replace("-", "").isdigit():
            review["reviewRating"] = {
                "@type": "Rating",
                "ratingValue": str(rating),
                "bestRating": "5",
                "worstRating": "1"
            }

        breadcrumb = _breadcrumb([("Home", BASE_URL + "/"),
                                  ("Reviews", BASE_URL + "/reviews/"),
                                  (book_title, canonical_url)])

        return _wrap_json_ld([review, breadcrumb])

    # ── Article (article pages) ──
    if schema_type == "article":
        author = _json_ld_escape(meta.get("author", "") or meta.get("byline", "") or "Bithues Editors")
        date_pub = _json_ld_escape(meta.get("date", "") or "")
        image_url = _abs_image(meta.get("featured_image", "") or "") or og_image
        article = {
            "@type": "Article",
            "headline": _json_ld_escape(page_title.replace(" | Bithues", "")),
            "description": _json_ld_escape(page_desc),
            "image": image_url,
            "author": {"@type": "Person", "name": author},
            "publisher": {"@id": org_id},
            "mainEntityOfPage": {"@type": "WebPage", "@id": canonical_url},
            "url": canonical_url,
        }
        if date_pub:
            article["datePublished"] = date_pub
            article["dateModified"] = date_pub
        breadcrumb = _breadcrumb([("Home", BASE_URL + "/"),
                                  ("Articles", BASE_URL + "/articles/"),
                                  (_json_ld_escape(meta.get("title", page_title)), canonical_url)])
        return _wrap_json_ld([article, breadcrumb])

    # ── Story (original fiction at root) ──
    if schema_type == "story":
        author = _json_ld_escape(meta.get("author", "") or "Bithues Editors")
        date_pub = _json_ld_escape(meta.get("date", "") or "")
        story = {
            "@type": "CreativeWork",
            "name": _json_ld_escape(meta.get("title", page_title)),
            "description": _json_ld_escape(page_desc),
            "author": {"@type": "Person", "name": author},
            "isAccessibleForFree": True,
            "publisher": {"@id": org_id},
            "url": canonical_url,
        }
        if date_pub:
            story["datePublished"] = date_pub
        breadcrumb = _breadcrumb([("Home", BASE_URL + "/"),
                                  ("Stories", BASE_URL + "/stories/"),
                                  (_json_ld_escape(meta.get("title", page_title)), canonical_url)])
        return _wrap_json_ld([story, breadcrumb])

    # ── Newsletter ──
    if schema_type == "newsletter":
        author = _json_ld_escape(meta.get("author", "") or "Atlas Renner")
        date_pub = _json_ld_escape(meta.get("date", "") or "")
        article = {
            "@type": "Article",
            "headline": _json_ld_escape(meta.get("title", page_title)),
            "description": _json_ld_escape(page_desc),
            "author": {"@type": "Person", "name": author},
            "publisher": {"@id": org_id},
            "mainEntityOfPage": {"@type": "WebPage", "@id": canonical_url},
            "url": canonical_url,
        }
        if date_pub:
            article["datePublished"] = date_pub
        breadcrumb = _breadcrumb([("Home", BASE_URL + "/"),
                                  ("Newsletters", BASE_URL + "/newsletters/"),
                                  (_json_ld_escape(meta.get("title", page_title)), canonical_url)])
        graph = [article, breadcrumb]
        if schema_extra:
            graph.extend(schema_extra)
        return _wrap_json_ld(graph)

    return ""


def build_listing_schema(page_type: str, page_title: str, page_desc: str,
                         canonical_url: str, items: list[tuple[str, str, str]]) -> list[dict]:
    """
    Build schema.org graph items for a listing page (newsletters index,
    reviews index, etc.). `items` is [(slug, title, summary), ...] in display order.
    Returns [ItemList, BreadcrumbList, CollectionPage] ready to append.
    """
    itemlist_elements = []
    for i, (slug, title, _) in enumerate(items):
        # Path-prefix is callers' responsibility — slug is expected to be
        # the full URL path like "/newsletters/2026-07-11-..."
        url = slug if slug.startswith("http") else BASE_URL + slug
        itemlist_elements.append({
            "@type": "ListItem",
            "position": i + 1,
            "url": url,
            "name": title,
        })
    collection = {
        "@type": "CollectionPage",
        "name": page_title,
        "description": page_desc,
        "url": canonical_url,
        "publisher": {"@id": f"{BASE_URL}/#organization"},
        "mainEntity": {
            "@type": "ItemList",
            "name": page_title,
            "numberOfItems": len(items),
            "itemListOrder": "https://schema.org/ItemListOrderDescending",
            "itemListElement": itemlist_elements,
        }
    }
    return [collection]


def _breadcrumb(items: list[tuple[str, str]]) -> dict:
    """Build a schema.org BreadcrumbList from [(name, url), ...]."""
    return {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i + 1,
                "name": name,
                "item": url
            }
            for i, (name, url) in enumerate(items)
        ]
    }


def _wrap_json_ld(graph: list[dict]) -> str:
    """Wrap a list of schema objects into a <script type=\"application/ld+json\"> tag."""
    payload = {
        "@context": "https://schema.org",
        "@graph": [g for g in graph if g]
    }
    json_str = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return f'<script type="application/ld+json">\n{json_str}\n</script>'


# ── Card HTML ─────────────────────────────────────────────────────────────────
def story_card_html(slug: str, meta: dict, index: int) -> str:
    genre    = meta.get("genre_label") or meta.get("type_label") or "Short Story"
    date     = meta.get("date")
    date_str = f'<div class="date-text">{date}</div>' if date else ""
    summary  = meta.get("summary", "")
    img_path = meta.get("card_image", f"/stories/images/{slug}.jpg")
    if img_path.startswith('images/') or img_path.startswith('content-images/'):
        img_path = "/stories/images/" + img_path.split('/', 1)[-1]
    elif not img_path.startswith('/') and not img_path.startswith('http'):
        img_path = f"/stories/images/{img_path}"
    title    = meta.get("title", slug)

    return f"""<div class="article-card" data-genre="{genre}">
 <div class="card-thumb stories-thumb" style="background-image:url({img_path});" role="img" aria-label="{title}"></div>
 <div class="category-label">{genre}</div>
 {date_str}
 <h3><a href="/{slug}/">{title}</a></h3>
 <p>{summary}</p>
</div>"""


# ── Page-Turn Navigation ───────────────────────────────────────────────────────
def page_nav_html(slug: str, current_page: int, total_pages: int) -> str:
    prev_link = (
        f'<a href="/{slug}/?page={current_page - 1}#content" '
        f'class="page-prev">&#8592; Previous</a>'
        if current_page > 1
        else '<span class="page-prev disabled">&#8592; Previous</span>'
    )
    next_link = (
        f'<a href="/{slug}/?page={current_page + 1}#content" '
        f'class="page-next">Next &#8594;</a>'
        if current_page < total_pages
        else '<span class="page-next disabled">Next &#8594;</span>'
    )
    return (
        f'<div class="page-nav">'
        f'<span class="page-info">Page {current_page} of {total_pages}</span>'
        f'<div class="page-links">'
        f'{prev_link}{next_link}'
        f'</div></div>'
    )


# ── Story Page HTML ────────────────────────────────────────────────────────────
def story_page_html(slug: str, meta: dict, body_html: str,
                    prev_slug: str, prev_title: str,
                    next_slug: str, next_title: str,
                    current_page: int = 1,
                    total_pages: int  = 1) -> str:
    title = meta.get("title", slug)
    genre = meta.get("genre_label") or meta.get("type_label") or "Short Story"
    date  = meta.get("date") or ""
    summary = meta.get("summary", "")
    author = meta.get("author", "")
    img_src = meta.get("featured_image") or meta.get("card_image")
    if img_src:
        if img_src.startswith('images/') or img_src.startswith('content-images/'):
            img_src = "/stories/images/" + img_src.split('/', 1)[-1]
        elif not img_src.startswith('/') and not img_src.startswith('http'):
            img_src = f"/stories/images/{img_src}"
        img_html = f'''<div class="story-hero-img" style="background-image:url({img_src});" role="img" aria-label="{title}"></div>'''
    else:
        img_html = ""

    # page_nav = page_nav_html(slug, current_page, total_pages) if total_pages > 1 else ""

    nav_html = ""
    if prev_slug or next_slug:
        nav_parts = []
        if prev_slug:
            nav_parts.append(
                f'<a href="/{prev_slug}/" class="story-nav-item prev-item">'
                f'<div class="story-nav-label">&#8592; Previous</div>'
                f'<div class="story-nav-title">{prev_title}</div></a>'
            )
        if next_slug:
            nav_parts.append(
                f'<a href="/{next_slug}/" class="story-nav-item next-item">'
                f'<div class="story-nav-label">Next &#8594;</div>'
                f'<div class="story-nav-title">{next_title}</div></a>'
            )
        nav_html = f'<nav class="story-nav">{"".join(nav_parts)}</nav>'

    share_bar = SHARE_BAR


    date_div = f'<div class="story-meta">{date}</div>' if date else ""
    byline_html = f'<div class="story-byline">by {author}</div>' if author else ""

    return f"""<div class="story-page">
 {img_html}
 <div class="story-header">
  <span class="genre-pill">{genre}</span>
  <h1>{title}</h1>
  {date_div}
  {byline_html}
 </div>
 <div class="story-body" id="content">
  {body_html}
 </div>
 {share_bar}
 {ADSENSE_BLOCK_HORIZONTAL}
 {nav_html}
</div>"""


# ── Article Page HTML ────────────────────────────────────────────────────────────
SHARE_BAR = """<div class="share-bar">
  <span class="share-label">Share</span>
  <a class="share-btn share-x" href="#" target="_blank" rel="noopener" aria-label="Share on X">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-4.714-6.231-5.401 6.231H2.744l7.73-8.835L1.254 2.25H8.08l4.259 5.63 5.905-5.63Zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
  </a>
  <a class="share-btn share-facebook" href="#" target="_blank" rel="noopener" aria-label="Share on Facebook">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>
  </a>
  <a class="share-btn share-linkedin" href="#" target="_blank" rel="noopener" aria-label="Share on LinkedIn">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>
  </a>
  <button class="share-btn share-copy" aria-label="Copy link" onclick="navigator.clipboard.writeText(window.location.href).then(()=>{this.querySelector('.copy-label').textContent='Copied!';setTimeout(()=>{this.querySelector('.copy-label').textContent='Copy'},2000)})">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>
    <span class="copy-label">Copy</span>
  </button>
</div>
<script>
document.querySelectorAll(".share-x, .share-facebook, .share-linkedin").forEach(function(el) {
  var url = encodeURIComponent(window.location.href);
  var title = encodeURIComponent(document.title);
  if (el.classList.contains("share-x")) el.href = "https://x.com/intent/tweet?url=" + url + "&text=" + title;
  if (el.classList.contains("share-facebook")) el.href = "https://www.facebook.com/sharer/sharer.php?u=" + url;
  if (el.classList.contains("share-linkedin")) el.href = "https://www.linkedin.com/sharing/share-offsite/?url=" + url;
});
</script>"""

SHARE_BAR_MINI = """<div class="share-bar share-bar-mini">
  <a class="share-btn share-x" href="#" target="_blank" rel="noopener" aria-label="Share on X">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-4.714-6.231-5.401 6.231H2.744l7.73-8.835L1.254 2.25H8.08l4.259 5.63 5.905-5.63Zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
  </a>
  <a class="share-btn share-facebook" href="#" target="_blank" rel="noopener" aria-label="Share on Facebook">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>
  </a>
  <a class="share-btn share-linkedin" href="#" target="_blank" rel="noopener" aria-label="Share on LinkedIn">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>
  </a>
</div>
"""

# AdSense slot trio (per 2026-08-11 doctrine: 3 slots per page = AdSense-best-practice).
# All three slots belong to the same publisher account (ca-pub-9312870448453345).
# 1328672966 = fixed 336x280 medium-rectangle, succession's primary
# 7590828986 = responsive auto, the original bithues slot
# 1216992329 = responsive auto, alternate format for rotation
ADSENSE_SLOT_FIXED = "1328672966"   # 336x280 medium rectangle
ADSENSE_SLOT_RESPONSIVE = "7590828986"  # responsive auto (bithues original)
ADSENSE_SLOT_RESPONSIVE_ALT = "1216992329"  # responsive auto (alternate)

ADSENSE_BLOCK = """<div class="adsense-block">
  <div class="adsense-block__label">Advertisement</div>
  <ins class="adsbygoogle" style="display:block;width:100%" data-ad-client="ca-pub-9312870448453345" data-ad-slot="7590828986" data-ad-format="auto" data-full-width-responsive="true"></ins>
  <script>(adsbygoogle = window.adsbygoogle || []).push({});</script>
</div>"""

ADSENSE_BLOCK_SQUARE = """<div class="adsense-block adsense-block--square">
  <div class="adsense-block__label">Advertisement</div>
  <ins class="adsbygoogle" style="display:inline-block;width:336px;height:280px" data-ad-client="ca-pub-9312870448453345" data-ad-slot="1328672966"></ins>
  <script>(adsbygoogle = window.adsbygoogle || []).push({});</script>
</div>"""

ADSENSE_BLOCK_HORIZONTAL = """<div style="margin:2.5rem 0;padding:1rem;background:var(--surface);border-radius:var(--radius);box-shadow:var(--shadow);text-align:center;">
  <div style="font-size:.75rem;color:#666;margin-bottom:6px;">Advertisement</div>
  <ins class="adsbygoogle" style="display:block;width:100%" data-ad-client="ca-pub-9312870448453345" data-ad-slot="1216992329" data-ad-format="auto" data-full-width-responsive="true"></ins>
  <script>(adsbygoogle = window.adsbygoogle || []).push({});</script>
</div>"""

# Kindle Unlimited signup CTA — added to every book review page.
# Links to the Amazon Kindle Unlimited subscribe page with the bithues-20
# affiliate tag. Universal because the link is to the KU program itself
# (not the specific book) and most of the books we review are KU-eligible.
# Individual reviews can opt out by setting `ku_eligible: false` in MD
# frontmatter if a specific book is known NOT to be in KU.
KU_SIGNUP_URL = "https://www.amazon.com/kindle-dbs/hz/subscribe/ku?_encoding=UTF8&pd_rd_w=8aH8p&content-id=amzn1.sym.849514f8-65db-4c36-bbc7-f2c1ec330a3a&pf_rd_p=849514f8-65db-4c36-bbc7-f2c1ec330a3a&pf_rd_r=J723M074DXX5FFVVTBJ0&pd_rd_wg=rFslw&pd_rd_r=3bd8c347-81b0-4373-90e3-1bc1253a66d6&linkCode=ll2&tag=bithues-20&linkId=dd553d84cd7a37ab85cbf890480a6aa5&language=en_US&ref_=as_li_ss_tl"

KU_CTA_BLOCK = (
    '<div class="ku-cta" style="margin:8px 0 32px; padding:16px 20px; background:#f8f5ef; border-radius:4px; text-align:center;">\n'
    '  <p style="font-size:13px; color:#555; margin:0 0 8px; line-height:1.4;">Many of the books we review are available on <strong>Kindle Unlimited</strong> &mdash; read for free with a 30-day trial.</p>\n'
    f'  <a href="{KU_SIGNUP_URL}" target="_blank" rel="noopener nofollow sponsored"\n'
    '     style="display:inline-block; padding:8px 22px; background:#0070ba; color:#ffffff; font-size:13px; text-decoration:none; border-radius:3px; letter-spacing:0.03em; font-weight:500;">\n'
    '    Try Kindle Unlimited Free for 30 Days &rarr;\n'
    '  </a>\n'
    '  <p style="font-size:11px; color:#888; margin:8px 0 0;">Cancel anytime. After the free trial, $11.99/month.</p>\n'
    '</div>'
)


# ── Intro prose / "What is Bithues" narrow hero ─────────────────────────────
# Sits above the "More Articles / More Stories / More Book Reviews" catalog.
# Three short paragraphs: what the site is, a featured review excerpt with
# attribution, and what visitors can find in the catalog below. Uses the
# existing .page-hero pattern (centered, ~680px) for visual consistency with
# the About page intro.
HOMEPAGE_INTRO_HERO = """<section class="page-hero homepage-intro-hero" aria-label="About Bithues">
 <h2>What is Bithues?</h2>
 <p><strong>Bithues</strong> is an independent book review site and indie short-fiction publisher. We publish honest, editor-vetted reviews of books we think are worth your time &mdash; from sci-fi, fantasy, and literary fiction to nonfiction, children&rsquo;s literature, and everything in between. We also publish original short stories, written and curated by an independent editorial team you can name.</p>
 <blockquote class="homepage-featured-quote">
  <p>&ldquo;A luminous, quietly breathtaking first-contact novel that feels as intimate as a family journal and as vast as the night sky it invites us to look up at.&rdquo;</p>
  <footer>&mdash; <cite>Priya Mehta</cite>, reviewing <a href="/reviews/first-contact-diary/"><em>First Contact Diary</em> by Mira Ellison</a></footer>
 </blockquote>
 <p>Below you&rsquo;ll find our latest articles, short stories, and book reviews. Use the navigation above to browse by section, or visit the <a href="/about/">About page</a> to learn more about who we are and how we work.</p>
</section>

<section class="page-content homepage-eat" aria-label="How Bithues works">
 <h2>How Bithues works</h2>
 <p>Bithues is run by a small editorial team of working writers and editors. Each review you read here was written by the editor whose name is on the masthead, after they read the book end to end. The reviews are not paid for, are not contingent on the publisher providing the book, and are not influenced by any party other than the editor reading the book. Affiliate links, where they appear, are tied to the specific Bithues recommendation, not to a paid placement.</p>
 <p>The short fiction on the site is original work published with the writers&rsquo; permission under a non-exclusive license. We publish new fiction weekly, with a weekly roundup on Sunday afternoons. The fiction desk and the reviews desk are separate functions; the editorial team reads both, but the work is split so neither function is degraded by the other&rsquo;s deadlines.</p>

 <h2>What you&rsquo;ll find on the homepage</h2>
 <p>The editor&rsquo;s picks at the top of the page are updated when a new review, article, or short story warrants a featured slot. Featured here means the editorial team thinks the piece is worth your time and wants to make sure you see it &mdash; it does not mean the piece is more important than any other piece on the site. The &ldquo;more articles,&rdquo; &ldquo;more book reviews,&rdquo; and &ldquo;more stories&rdquo; lists below the editor&rsquo;s picks are the recent pieces in each category, sorted by publication date with the most recent first.</p>

 <h2>How new reviews are written</h2>
 <p>A new review takes one to two weeks from outline to publication. The review&rsquo;s editor reads the book in full, writes a draft that frames the book&rsquo;s argument or its lack of one, has a second editor read the draft for tone and accuracy, then publishes. Reviews are not first impressions; the books have been read end to end before the review is written, and the review takes its time before asking the reader to take theirs.</p>

 <h2>How we choose what to review</h2>
 <p>We choose what to review based on what the editorial team is reading. Books come to us in three ways: the editor picks the book up because they want to read it; the publisher sends us a book that they think will fit our editorial coverage; or we hear about a book from a reader whose recommendation the editor takes seriously. The books we accept for review are books we intend to read in full and engage with on their own terms, and we are honest with publishers when a book is not a fit for our coverage.</p>

 <h2>How to support Bithues</h2>
 <p>Bithues is supported by advertising and by an optional paid newsletter subscription. The advertising does not influence the editorial content, and the editorial content is the same whether or not you are a paid subscriber. Readers who want to support the site beyond the free coverage can subscribe to the paid tier; readers who want the free editorial coverage can simply read. The full revenue model is documented on the About page and is revisited annually.</p>
</section>"""


def _adsense_topic_from_meta(meta: dict) -> str:
    """Build a short topic-string for AdSense context hints from page frontmatter.

    Returns 3-8 keywords, comma-separated, that describe the page's primary topic.
    Used to inject a hidden HTML comment before each AdSense block, which gives
    the AdSense crawler a topical context hint that tends to lift eCPM.

    Falls back to a generic "books, literature, reading" string if the page has
    no useful metadata, so the AdSense comment is never empty.
    """
    if not meta:
        return "books, literature, reading"
    parts: list[str] = []

    # 1. Type / genre (the most specific signal)
    for k in ("genre_label", "type_label", "category"):
        v = meta.get(k)
        if v and isinstance(v, str) and v.strip():
            parts.append(v.strip())
            break

    # 2. Tags (up to 4)
    tags = meta.get("tags") or []
    if isinstance(tags, list):
        for t in tags[:4]:
            if isinstance(t, str) and t.strip() and t.strip() not in parts:
                parts.append(t.strip())

    # 3. Title keywords (low-signal but adds specificity)
    title = meta.get("title", "")
    if isinstance(title, str) and title:
        # Strip punctuation and only keep alpha words >3 chars
        import re as _re
        clean = _re.sub(r"[^A-Za-z\s]", " ", title)
        title_words = [w for w in clean.split() if len(w) > 3][:3]
        for w in title_words:
            if w.lower() not in (p.lower() for p in parts):
                parts.append(w)

    if not parts:
        return "books, literature, reading"

    # Cap at 8 keywords to keep the topic comment lean
    return ", ".join(parts[:8])


def inject_adsense_into_body(body_html: str, topic: str = "") -> str:
    """Inject AdSense blocks into article/story body.

    Two modes:
    1. Manual markers: If the body contains HTML-comment markers
       (<!-- adsense:square -->, <!-- adsense:vertical -->, <!-- adsense:horizontal -->),
       they are replaced with the matching AdSense block. This gives authors explicit
       control over ad placement at natural reading break points.
    2. Legacy auto-injection: If no markers are present, falls back to placing
       a SQUARE ad after the 1st </p> and a VERTICAL ad after the 2nd </p>.

    Optional `topic` string: when provided, an HTML comment `<!-- topic: ... -->` is
    emitted immediately before each injected AdSense block. This is invisible to users
    but gives the AdSense crawler a topical context hint, which tends to lift eCPM
    by improving ad relevance scoring. Topic should be 3-8 keywords, comma-separated.
    If empty, no comment is emitted (backward compatible).

    Returns body_html unchanged if input is empty.
    """
    if not body_html:
        return body_html

    # Build the topic comment prefix (empty if no topic given)
    topic_prefix = f"<!-- topic: {topic} -->\n" if topic else ""

    # Mode 1: explicit HTML-comment markers
    if '<!-- adsense:' in body_html:
        body_html = body_html.replace('<!-- adsense:square -->', topic_prefix + ADSENSE_BLOCK_SQUARE)
        body_html = body_html.replace('<!-- adsense:vertical -->', topic_prefix + ADSENSE_BLOCK)
        body_html = body_html.replace('<!-- adsense:horizontal -->', topic_prefix + ADSENSE_BLOCK_HORIZONTAL)
        return body_html

    # Mode 2: legacy auto-injection (backward compatible)
    first = body_html.find("</p>")
    if first == -1:
        return body_html
    body_html = body_html[:first + len("</p>")] + "\n" + topic_prefix + ADSENSE_BLOCK_SQUARE + body_html[first + len("</p>"):]
    second = body_html.find("</p>", first + len("</p>") + len(topic_prefix) + len(ADSENSE_BLOCK_SQUARE))
    if second == -1:
        return body_html
    body_html = body_html[:second + len("</p>")] + "\n" + topic_prefix + ADSENSE_BLOCK + body_html[second + len("</p>"):]
    return body_html

def article_page_html(slug: str, meta: dict, body_html: str,
                      prev_slug: str, prev_title: str,
                      next_slug: str, next_title: str) -> str:
    title   = meta.get("title", slug)
    genre_raw = meta.get("genre_label", "")
    genre   = string.capwords(genre_raw) if genre_raw else ""
    summary = meta.get("summary", "")
    author  = meta.get("author", "")
    img_src = meta.get("featured_image", f"/content-images/{slug}.jpg")
    # Normalize: strip leading "content-images/" before prepending (anti-pattern: doubled prefix)
    if img_src and not img_src.startswith('/') and not img_src.startswith('http'):
        img_src = img_src.removeprefix("content-images/")
        img_src = f"/content-images/{img_src}"

    # Build related links (up to 4) from same genre
    genre_label = meta.get("genre_label") or ""
    more_like = []
    if genre_label:
        all_articles = load_md_dir(ARTICLES_DIR)
        same_genre = [a for a in all_articles
                      if a[0] != slug and
                      (a[1].get("genre_label") == genre_label or a[1].get("type_label") == genre_label)]
        more_like = same_genre[:4]

    related_html = ""
    if more_like:
        links = []
        for a_slug, a_meta, _ in more_like:
            a_title = a_meta.get("title", a_slug)
            links.append(
                f'<a href="/articles/{a_slug}/" style="display:inline-block;padding:6px 14px;background:#f5f0e8;color:#3a2f1e;border:1px solid #3a2f1e;border-radius:3px;text-decoration:none;font-size:.85rem;">{a_title}</a>'
            )
        related_html = (
            '<div class="related-links">\n'
            '<h3 style="font-size:1rem;font-weight:600;margin-bottom:1rem;font-family:var(--font-heading,Georgia,serif);">Continue Reading</h3>\n'
            '<div style="display:flex;flex-wrap:wrap;gap:0.75rem;">\n'
            + '\n'.join(links) + '\n'
            '</div>\n</div>'
        )

    # NOTE: Further Reading sections must be added manually in the MD source.
    # Do NOT auto-generate — it creates duplicates when articles already have Amazon links
    # in the body. To add Further Reading, use: ### Further Reading\n- [Title](https://...)
    further_html = ""

    return f"""<div class="story-page">
 <header class="content-header">
  <div class="content-header-inner">
   <span class="tag tag--article">Article</span>
   <h1 class="content-title">{title}</h1>
   {f'<p class="content-meta">{genre}</p>' if genre else ''}
   {f'<p class="content-byline">by {author}</p>' if author else ''}
  </div>
 </header>

 <div class="content-image"><img src="{img_src}?v=1" alt="{title}" style="width:100%;max-height:400px;object-fit:cover;border-radius:4px;margin-bottom:1.5rem;"></div>

 <div class="content-body">
  <div class="article-body" style="font-size:1.05rem;line-height:1.8;color:var(--text);">
   {body_html}
  </div>
 </div>

 {further_html}
 {ADSENSE_BLOCK_HORIZONTAL}
 {SHARE_BAR}
 {related_html}
</div>"""


# ── Review Page HTML ────────────────────────────────────────────────────────────
def review_page_html(slug: str, meta: dict, body_html: str,
                     prev_slug: str, prev_title: str,
                     next_slug: str, next_title: str) -> str:
    page_title = meta.get("review_title") or meta.get("title", slug)
    title    = meta.get("title", slug)
    genre    = meta.get("genre_label") or "Book Review"
    book_author = meta.get("book_author", "")
    reviewer    = meta.get("reviewer", "")
    author_fallback = meta.get("author", "")
    if reviewer:
        author_display = f'Reviewed by {reviewer}'
    elif book_author:
        author_display = f'by {book_author}'
    else:
        author_display = f'Reviewed by {author_fallback}'
    date     = meta.get("date", "")
    summary  = meta.get("summary", "")
    asin     = meta.get("amazon_asin", "")
    price    = meta.get("price", "")
    cover    = meta.get("cover_image", "")

    # Amazon button href
    amazon_href = f"https://www.amazon.com/dp/{asin}?tag=bithues-20" if asin else "https://www.amazon.com/?tag=bithues-20"

    # Amazon CTA
    if asin:
        amazon_cta = (
            f'<div style="margin:32px 0 16px; padding:20px 0; border-top:1px solid #e8e4dd; border-bottom:1px solid #e8e4dd; text-align:center;">\n'
            f'  <p style="font-size:13px; color:#888; margin:0 0 10px; letter-spacing:0.04em; text-transform:uppercase;">Enjoyed this review?</p>\n'
            f'  <a href="{amazon_href}" target="_blank" rel="noopener"\n'
            f'     style="display:inline-block; padding:10px 28px; border:1px solid #8a6f3e; color:#8a6f3e; font-size:13px; text-decoration:none; border-radius:3px; letter-spacing:0.05em;">\n'
            f'    Buy on Amazon →\n'
            f'  </a>\n'
            f'</div>'
        )
    else:
        amazon_cta = ""

    # Kindle Unlimited CTA — opt-out per review with `ku_eligible: false`
    # in frontmatter. Most books we review are on KU, so default is on.
    ku_eligible = meta.get("ku_eligible", True)
    if isinstance(ku_eligible, str):
        ku_eligible = ku_eligible.strip().lower() not in ("false", "no", "0", "")
    ku_cta = KU_CTA_BLOCK if ku_eligible else ""

    # Related links — show up to 4 reviews sharing same genre_label.
    # Fall back to type_label if genre has fewer than 2 matches.
    genre_label = meta.get("genre_label") or ""
    type_label  = meta.get("type_label") or ""
    all_reviews = load_md_dir(REVIEWS_DIR)
    genre_matches = [r for r in all_reviews
                     if r[0] != slug and r[1].get("genre_label") == genre_label]
    if len(genre_matches) >= 2:
        more_like = genre_matches[:4]
    else:
        type_matches = [r for r in all_reviews
                       if r[0] != slug and r[1].get("type_label") == type_label]
        more_like = type_matches[:4]

    related_html = ""
    if more_like:
        links = []
        for r_slug, r_meta, _ in more_like:
            r_title = r_meta.get("title", r_slug)
            links.append(
                f'<a href="/reviews/{r_slug}/" style="display:inline-block;padding:6px 14px;background:#f5f0e8;color:#3a2f1e;border:1px solid #3a2f1e;border-radius:3px;text-decoration:none;font-size:.85rem;">{r_title}</a>'
            )
        related_html = (
            '<div class="related-links">\n'
            '<h3 style="font-size:1rem;font-weight:600;margin-bottom:1rem;font-family:var(--font-heading,Georgia,serif);">More Reviews</h3>\n'
            '<div style="display:flex;flex-wrap:wrap;gap:0.75rem;">\n'
            + '\n'.join(links) + '\n'
            '</div>\n</div>'
        )

    date_str = f'<div class="date-text">{date}</div>' if date else ""
    buy_str = f'<a href="{amazon_href}" target="_blank" rel="noopener" class="review-hero-buy" style="display:inline-block; margin-top:10px; padding:6px 16px; border:1px solid #8a6f3e; color:#8a6f3e; font-size:13px; text-decoration:none; border-radius:3px;">Buy on Amazon &#8594;</a>' if asin else ""

    return f"""<article class="content-article">
  <!-- HEADER (cover left, title right) -->
  <div class="review-page-header" style="max-width:680px; margin:48px auto 40px; padding:0 24px;">
    <div style="display:flex; align-items:flex-start; gap:32px;">
      <!-- Cover LEFT -->
      <div style="flex-shrink:0;">
        <a href="{amazon_href}" target="_blank" rel="noopener">
          <img src="{cover}" alt="{title}" class="review-cover-thumb" style="width:130px;">
        </a>
      </div>
      <!-- Title + meta RIGHT -->
      <div style="min-width:0;">
        <p style="margin:0 0 8px; font-size:11px; font-weight:600; color:#888; letter-spacing:0.08em; text-transform:uppercase;">{genre}</p>
        <h1 style="font-family:var(--font-heading,Georgia,serif); font-size:1.5rem; font-weight:700; color:var(--text); margin:0 0 10px; line-height:1.3;">{page_title}</h1>
        <p style="margin:0 0 6px; font-size:15px; color:#3a2e1e;">{author_display}</p>
        {date_str}
        {buy_str}
      </div>
    </div>
  </div>

  <!-- BODY + CTA -->
  <div class="review-body" style="max-width:680px; margin:0 auto; padding:0 24px 24px;">
   {body_html}
   {amazon_cta}
   {ku_cta}
  </div>

  <!-- SHARE + MORE REVIEWS (left-aligned, below body) -->
  <div style="max-width:680px; margin:0 auto; padding:0 24px 40px;">
    <!-- Share bar -->
    <div style="border-top:1px solid #e8e4dd; padding-top:20px; margin-bottom:32px;">
      <div style="display:flex; align-items:center; gap:16px; margin-bottom:12px;">
        <span style="font-size:11px; font-weight:600; color:#888; letter-spacing:0.08em; text-transform:uppercase;">Share</span>
        <div style="display:flex; gap:12px;">{SHARE_BAR_MINI}</div>
      </div>
    </div>
    <!-- More Reviews -->
    {related_html}
  </div>

  {ADSENSE_BLOCK_HORIZONTAL}
</article>"""


# ── Pagination (listing) ───────────────────────────────────────────────────────
def paginate(items: list, per_page: int) -> list[list]:
    return [items[i:i + per_page] for i in range(0, len(items), per_page)]


# ── Load All Stories ───────────────────────────────────────────────────────────
def load_all_stories() -> list[tuple[str, dict, str]]:
    stories = []
    if not STORIES_DIR.exists():
        print(f"WARNING: stories directory not found: {STORIES_DIR}")
        return stories

    for md_path in sorted(STORIES_DIR.glob("*.md")):
        slug    = slug_from_path(md_path)
        content = md_path.read_text(encoding="utf-8")
        meta, body = parse_front_matter(content)

        if meta.get("draft"):
            continue

        stories.append((slug, meta, body))

    return stories


# ── Load articles and reviews ───────────────────────────────────────────────────
def _parse_sort_date(value: str):
    """Parse a date string for chronological sort.

    Tries ISO 8601 first (YYYY-MM-DD), then common human formats seen on
    the site (e.g. 'July 26, 2023', 'February 20, 2026'), then year-only.
    Returns ``datetime.date`` on success, else ``date.min`` so undated items
    sort to the end (reverse=True sort places earliest first; we want
    undated items last, so key needs to be smallest for them).
    """
    if not value:
        return date.min
    v = value.strip().strip('"').strip("'")
    # ISO 8601
    try:
        return datetime.strptime(v, "%Y-%m-%d").date()
    except ValueError:
        pass
    # "Month D, YYYY" — most common human format on the site
    try:
        return datetime.strptime(v, "%B %d, %Y").date()
    except ValueError:
        pass
    # "Mon D, YYYY" — abbreviated
    try:
        return datetime.strptime(v, "%b %d, %Y").date()
    except ValueError:
        pass
    # Year-only
    try:
        return date(int(v), 1, 1)
    except ValueError:
        return date.min


def load_md_dir(dir_path: Path) -> list[tuple[str, dict, str]]:
    items = []
    if not dir_path.exists():
        return items
    for md_path in sorted(dir_path.glob("*.md")):
        slug    = md_path.stem
        content = md_path.read_text(encoding="utf-8")
        meta, body = parse_front_matter(content)
        if meta.get("draft"):
            continue
        items.append((slug, meta, body))
    return items


def truncate_words(text: str, max_len: int) -> str:
    """Truncate at word boundary near max_len, never mid-word."""
    if len(text) <= max_len:
        return text
    truncated = text[:max_len]
    last_space = truncated.rfind(' ')
    if last_space > max_len * 0.6:
        return truncated[:last_space]
    return truncated


def article_card(slug: str, meta: dict, index: int) -> str:
    genre_raw = meta.get("genre_label") or meta.get("type_label", "Article")
    genre  = string.capwords(genre_raw) if genre_raw.lower() == genre_raw else genre_raw
    date   = meta.get("date") or ""
    title  = meta.get("title", slug)
    summary = truncate_words(meta.get("summary", ""), 160)
    date_str = f'<div class="date-text">{date}</div>' if date else ""
    img_path = meta.get("card_image") or meta.get("featured_image", f"/content-images/{slug}.jpg")
    # featured_image may be "images/foo.jpg" or "content-images/foo.jpg" — convert to "/content-images/foo.jpg"
    if img_path and not img_path.startswith('/') and not img_path.startswith('http'):
        img_path = img_path.removeprefix("content-images/")
        img_path = f"/content-images/{img_path}"
    # Upgrade Amazon CDN image size for better card quality
    if img_path.startswith('http') and 'amazon.com/images' in img_path:
        img_path = re.sub(r'\._SX\d+_', '._SL300_', img_path)
        img_path = re.sub(r'\._SL\d+_', '._SL300_', img_path)

    return f"""<div class="article-card" data-genre="{genre}">
 <div class="card-thumb articles-thumb" style="background-image:url({img_path});" role="img" aria-label="{title}"></div>
 <div class="category-label">{genre}</div>
 {date_str}
 <h3><a href="/articles/{slug}/">{title}</a></h3>
 <p>{summary}</p>
</div>"""


def review_card(slug: str, meta: dict, index: int, variant: str = "compact") -> str:
    """Render a review card. variant='compact' for listing pages, 'feature' for Editor's Pick."""
    genre   = meta.get("genre_label") or meta.get("type_label", "Book Review")
    date    = meta.get("date") or ""
    title   = meta.get("title", slug)
    # Feature variant: longer summary for Editor's Pick (180 chars)
    # Compact variant: shorter summary for listing pages (120 chars)
    max_len = 250 if variant == "feature" else 120
    summary = meta.get("summary", "")[:max_len]
    date_str = f'<div class="date-text">{date}</div>' if date else ""
    book_author = meta.get("book_author", "")
    reviewer    = meta.get("reviewer", "")
    if reviewer:
        author_str = f'<div class="review-hero-author">Reviewed by {reviewer}</div>'
    elif book_author:
        author_str = f'<div class="review-hero-author">by {book_author}</div>'
    else:
        author_str = ""
    # Build Amazon buy URL from ASIN + Associates tag, fall back to explicit amazon_url
    asin = meta.get("amazon_asin", "")
    buy_url = meta.get("amazon_url", f"https://www.amazon.com/dp/{asin}?tag=bithues-20" if asin else "")
    buy_str = f'<a href="{buy_url}" class="review-hero-buy" target="_blank" rel="noopener">Buy on Amazon &#8594;</a>' if buy_url else ""

    if variant == "large":
        # Hero layout: cover LEFT, title/author/genre RIGHT — same as review detail page
        cover = meta.get("cover_image", "") or meta.get("card_image", "") or meta.get("featured_image", "")
        if cover.startswith('http') and 'amazon.com/images' in cover:
            cover = re.sub(r'\._SX\d+_', '_SX150_', cover)
            cover = re.sub(r'\._SL\d+_', '_SX150_', cover)
        elif not cover.startswith('/') and not cover:
            cover = f"/reviews/images/{slug}.jpg"
        return f"""<div class="article-card review-card-feature review-card-hero">
  <div class="review-hero-header">
    <a href="/reviews/{slug}/" class="review-hero-cover" style="display:block; flex-shrink:0;">
      <img src="{cover}" alt="{title}" class="review-cover-thumb">
    </a>
    <div class="review-hero-meta">
      <div class="category-label">{genre}</div>
      <h3><a href="/reviews/{slug}/">{title}</a></h3>
      {author_str}
      {date_str}
      {buy_str}
    </div>
  </div>
  <div class="review-hero-summary">
    <p>{summary}</p>
    <a href="/reviews/{slug}/" class="accent-link">Read Review &#8594;</a>
  </div>
</div>"""

    if variant == "feature":
        # Feature layout: title LEFT, cover RIGHT (original listing layout)
        cover = meta.get("cover_image", "") or meta.get("card_image", "") or meta.get("featured_image", "")
        if cover.startswith('http') and 'amazon.com/images' in cover:
            cover = re.sub(r'\._SX\d+_', '_SX150_', cover)  # same size as large
        elif not cover.startswith('/') and not cover:
            cover = f"/reviews/images/{slug}.jpg"
        return f"""<div class="article-card review-card-feature review-card-hero">
  <div class="review-hero-header">
    <div class="review-hero-meta">
      <div class="category-label">{genre}</div>
      <h3><a href="/reviews/{slug}/">{title}</a></h3>
      {author_str}
      {date_str}
      {buy_str}
    </div>
    <a href="/reviews/{slug}/" class="review-hero-cover" style="display:block; flex-shrink:0;">
      <img src="{cover}" alt="{title}" class="review-cover-thumb">
    </a>
  </div>
  <div class="review-hero-summary">
    <p>{summary}</p>
    <a href="/reviews/{slug}/" class="accent-link">Read Review &#8594;</a>
  </div>
</div>"""

    # Compact variant: horizontal card (cover left, text right).
    card_cls = "review-card-horizontal"
    cover = meta.get("cover_image", "") or meta.get("card_image", "") or meta.get("featured_image", "")
    if cover.startswith('http') and 'amazon.com/images' in cover:
        cover = re.sub(r'\._SX\d+_', '._SX150_', cover)
        cover = re.sub(r'\._SL\d+_', '._SX150_', cover)
    elif not cover.startswith('/') and not cover:
        cover = f"/reviews/images/{slug}.jpg"

    return f"""<div class="article-card" data-genre="{genre}">
 <div class="{card_cls}">
   <a href="/reviews/{slug}/" class="review-cover-left" style="display:block; flex-shrink:0;">
     <img src="{cover}" alt="{title}" class="review-cover-thumb">
   </a>
   <div class="review-card-text">
     <div class="category-label">{genre}</div>
     <h3><a href="/reviews/{slug}/">{title}</a></h3>
     <p>{summary}</p>
     {buy_str}
   </div>
 </div>
</div>"""


# ── Generate stories.html ───────────────────────────────────────────────────────
def generate_stories_page(all_stories: list[tuple[str, dict, str]], page: int = 1) -> str:
    pages        = paginate(all_stories, PAGINATE)
    total_pages  = len(pages)
    current_page = pages[page - 1] if 1 <= page <= total_pages else []

    cards = "\n".join(
        story_card_html(slug, meta, i)
        for i, (slug, meta, _) in enumerate(current_page)
    )

    pagination_html = ""  # pagination removed 2026-06-01

    main = f"""<section class="page-hero">
 <h1>All Stories</h1>
 <p>{len(all_stories)} short stories — exploring what it means to be alive, in worlds familiar, strange, and somewhere in between.</p>
</section>
<section style="padding-top:8px;">
 <div class="genre-filter-bar">
  <button class="filter-btn active" data-value="all">All</button>
  <button class="filter-btn" data-value="Literary Fiction">Literary Fiction</button>
  <button class="filter-btn" data-value="Science Fiction">Science Fiction</button>
  <button class="filter-btn" data-value="Fantasy">Fantasy</button>
 </div>
{ADSENSE_BLOCK_SQUARE}
 <div class="card-grid">
  {cards}
 </div>
{ADSENSE_BLOCK}
{pagination_html}
</section>

{ADSENSE_BLOCK_HORIZONTAL}
"""
    # ItemList schema for stories listing.
    listing_items = [
        (f"/{slug}/", meta.get("title", slug), meta.get("summary", ""))
        for slug, meta, _ in all_stories
    ]
    schema_extra = build_listing_schema(
        "stories",
        "All Stories",
        "Browse all short fiction from Bithues — dark fantasy, literary fiction, speculative worlds.",
        BASE_URL + "/stories/",
        listing_items,
    )
    return wrap_in_template("All Stories",
        "Browse all short fiction from Bithues — dark fantasy, literary fiction, speculative worlds.",
        main, "stories", canonical_path="/stories/",
        schema_extra=schema_extra)


# ── Generate articles.html listing ────────────────────────────────────────────
def generate_articles_listing(all_articles: list[tuple[str, dict, str]], page: int = 1) -> str:
    articles_sorted = sorted(all_articles, key=lambda a: _parse_sort_date(a[1].get("date") or ""), reverse=True)
    filtered = [a for a in articles_sorted if a[0] != 'index']
    pages = paginate(filtered, PAGINATE)
    total_pages = len(pages)
    current_page = pages[page - 1] if 1 <= page <= total_pages else []
    cards = "\n".join(
        article_card(slug, meta, i)
        for i, (slug, meta, _) in enumerate(current_page)
    )
    pagination_html = ""  # pagination removed 2026-06-01

    # 2026-08-08 INTERNAL LINKING FIX (class-7 cross-site-bug-ledger):
    # Wrap the listing in a 2-col sidebar layout: main content + newsletter sidebar.
    # Feeds crawl priority from /articles/ (indexed) to /newsletters/ (unindexed).
    all_newsletters = load_md_dir(NEWSLETTERS_DIR) if NEWSLETTERS_DIR.exists() else []
    sidebar_html = newsletter_sidebar(all_newsletters, count=4)
    main = f"""<section class="page-hero">
 <h1>Articles</h1>
 <p>{len(filtered)} articles on reading, books, and what books teach us about being human.</p>
</section>
<section style="padding-top:8px;">
 <div class="genre-filter-bar">
  <button class="filter-btn active" data-value="all">All</button>
  <button class="filter-btn" data-value="Lists">Lists</button>
  <button class="filter-btn" data-value="Nonfiction">Nonfiction</button>
  <button class="filter-btn" data-value="Business">Business</button>
  <button class="filter-btn" data-value="Children's">Children</button>
 </div>
{ADSENSE_BLOCK_SQUARE}
 <div class="section-sidebar">
 <div class="section-main">
  <div class="card-grid">
   {cards}
  </div>
{ADSENSE_BLOCK}
{pagination_html}
 </div>
{sidebar_html}
 </div>
</section>

{ADSENSE_BLOCK_HORIZONTAL}
"""
    # ItemList schema for articles listing.
    listing_items = [
        (f"/articles/{slug}/", meta.get("title", slug), meta.get("summary", ""))
        for slug, meta, _ in filtered
    ]
    schema_extra = build_listing_schema(
        "articles",
        "Articles",
        "Articles on reading, books, and what books teach us about being human.",
        BASE_URL + "/articles/",
        listing_items,
    )
    return wrap_in_template("Articles",
        "Articles on reading, books, and what books teach us about being human.",
        main, "articles", canonical_path="/articles/",
        schema_extra=schema_extra)


# ── Generate reviews.html listing ─────────────────────────────────────────────
def generate_reviews_listing(all_reviews: list[tuple[str, dict, str]], page: int = 1) -> str:
    reviews_sorted = sorted(all_reviews, key=lambda r: _parse_sort_date(r[1].get("date") or ""), reverse=True)
    pages = paginate(reviews_sorted, REVIEWS_PAGINATE)
    total_pages = len(pages)
    current_page = pages[page - 1] if 1 <= page <= total_pages else []
    cards = "\n".join(
        review_card(slug, meta, i, variant="compact")
        for i, (slug, meta, _) in enumerate(current_page)
    )
    adsense = ADSENSE_BLOCK
    adsense_horizontal = ADSENSE_BLOCK_HORIZONTAL
    adsense_square = ADSENSE_BLOCK_SQUARE
    if total_pages > 1:
        page_links = []
        for p in range(1, total_pages + 1):
            if p == page:
                page_links.append(f'<span class="active">{p}</span>')
            else:
                page_links.append(f'<a href="/reviews{p}/">{p}</a>')
        pagination_html = f'<div class="pagination">{" ".join(page_links)}</div>'
    else:
        pagination_html = ""

    # 2026-08-08 INTERNAL LINKING FIX (class-7 cross-site-bug-ledger):
    # Wrap the listing in a 2-col sidebar layout with newsletter sidebar.
    # /reviews/ is indexed but child /reviews/<slug>/ pages are not — adding a
    # newsletter sidebar creates a cross-link from the indexed hub to unindexed
    # newsletter spokes, plus the sidebar shows the editorial pipeline breadth.
    all_newsletters = load_md_dir(NEWSLETTERS_DIR) if NEWSLETTERS_DIR.exists() else []
    sidebar_html = newsletter_sidebar(all_newsletters, count=4)
    main = f"""<section class="page-hero">
 <h1>Book Reviews</h1>
 <p>{len(reviews_sorted)} book reviews — fiction, sci-fi, fantasy, nonfiction, and more.</p>
</section>
<section style="padding-top:8px;">
 <div class="genre-filter-bar">
  <button class="filter-btn active" data-value="all">All</button>
  <button class="filter-btn" data-value="Fiction">Fiction</button>
  <button class="filter-btn" data-value="Nonfiction">Nonfiction</button>
  <button class="filter-btn" data-value="Self-Help">Self-Help</button>
  <button class="filter-btn" data-value="Science Fiction">Science Fiction</button>
  <button class="filter-btn" data-value="Historical Fiction">Historical Fiction</button>
  <button class="filter-btn" data-value="Prehistorical Fiction">Prehistorical Fiction</button>
  <button class="filter-btn" data-value="Romance">Romance</button>
  <button class="filter-btn" data-value="Children's">Children</button>
 </div>
{adsense_square}
 <div class="section-sidebar">
 <div class="section-main">
  <div class="card-grid card-grid-compact">
   {cards}
  </div>
{adsense}
 {pagination_html}
 </div>
{sidebar_html}
 </div>
 {adsense_horizontal}
</section>"""
    # ItemList schema for reviews listing — feeds Google's "Top stories" carousel.
    listing_items = [
        (f"/reviews/{slug}/", meta.get("title", slug), meta.get("summary", ""))
        for slug, meta, _ in reviews_sorted
    ]
    schema_extra = build_listing_schema(
        "reviews",
        "Book Reviews",
        "In-depth book reviews across fiction, sci-fi, fantasy, nonfiction, and more.",
        BASE_URL + "/reviews/",
        listing_items,
    )
    return wrap_in_template("Book Reviews",
        "In-depth book reviews across fiction, sci-fi, fantasy, nonfiction, and more.",
        main, "reviews", canonical_path="/reviews/",
        schema_extra=schema_extra)


# ── Newsletter Card (used on the listing page) ────────────────────────────────
def newsletter_card(slug: str, meta: dict, index: int) -> str:
    """Render a uniform newsletter card for the /newsletters/ grid.

    Used by the listing page only. Format lifted from spaceorbitals's Editorial
    Mission Control — plain-text card, no thumbnail, title + meta line + summary
    + 'Read →'. Matched to bithues palette (cream surface, dark ink, warm
    accent). Mike 2026-07-10 ET: 'make it more like this setup/format with the
    boxes' referring to spaceorbitals.com/newsletters/.

    Updated 2026-07-22 to expose `issue_type` as a chip so the archive displays
    editorial variety (reader-state / backlist-revival / micro-season / etc.)
    per the redesign spec.
    """
    date    = meta.get("date") or ""
    title   = meta.get("title", slug)
    summary = truncate_words(meta.get("summary", ""), 160)
    author  = meta.get("author", "") or ""
    issue_type = (meta.get("issue_type") or "").lower().strip()

    # Meta line: "YYYY-MM-DD · author · Newsletter [· issue-type]"
    meta_parts = []
    if date:
        meta_parts.append(date)
    if author:
        meta_parts.append(author)
    meta_parts.append('<span class="tag tag--article">Newsletter</span>')
    if issue_type:
        meta_parts.append(f'<span class="tag tag--issue-type">{issue_type.replace("-", " ")}</span>')
    meta_html = " · ".join(meta_parts)

    return f"""<article class="newsletter-grid-card">
 <h3 class="newsletter-grid-card__title"><a href="/newsletters/{slug}/">{title}</a></h3>
 <div class="newsletter-grid-card__meta">{meta_html}</div>
 <p class="newsletter-grid-card__summary">{summary}</p>
 <a href="/newsletters/{slug}/" class="newsletter-grid-card__cta">Read →</a>
</article>"""


# ── Newsletter mini-card (for sidebar / cross-link blocks) ───────────────────────
def newsletter_mini_card(slug: str, meta: dict) -> str:
    """Compact newsletter card used in sidebar / cross-link strips.

    Shows date + title + summary. No CTA — verbose card. Used on /articles/ and
    /reviews/ sidebars to feed crawl priority from indexed pages to unindexed
    newsletter spokes. Mike 2026-08-08 directive: internal linking is the #1
    leverage point for getting /newsletters/ indexed.
    """
    date    = meta.get("date") or ""
    title   = meta.get("title", slug)
    summary = truncate_words(meta.get("summary", ""), 80)
    return f"""<div class="nl-mini-card">
 <div class="nl-mini-card__date">{date}</div>
 <h3 class="nl-mini-card__title"><a href="/newsletters/{slug}/">{title}</a></h3>
 <p class="nl-mini-card__summary">{summary}</p>
 <a href="/newsletters/{slug}/" class="nl-mini-card__cta">Read →</a>
</div>"""


# ── Review mini-card (for /newsletters/ sidebar cross-link to reviews) ────────────
def review_mini_card(slug: str, meta: dict) -> str:
    """Compact review card used in sidebar / cross-link strips."""
    title = meta.get("title", slug)
    genre = meta.get("genre_label") or meta.get("type_label", "Book Review")
    return f"""<div class="nl-mini-card">
 <div class="nl-mini-card__date">{genre}</div>
 <h3 class="nl-mini-card__title"><a href="/reviews/{slug}/">{title}</a></h3>
</div>"""


# ── Cross-link sidebar: list of recent newsletters for /articles/ + /reviews/ ──────
def newsletter_sidebar(newsletters: list, count: int = 4) -> str:
    """Return a sidebar of the N most recent newsletters as a string.

    Used on /articles/ and /reviews/ listing pages to cross-link from indexed
    pages to unindexed newsletter URLs. Anti-pattern #7 (internal linking gap)
    per cross-site-bug-ledger.md.
    """
    items = sorted(
        [n for n in newsletters if n[0] != "index"],
        key=lambda n: _parse_sort_date(n[1].get("date") or ""),
        reverse=True,
    )[:count]
    cards = "\n".join(newsletter_mini_card(slug, meta) for slug, meta, _ in items)
    return f"""<aside class="section-aside" aria-label="Daily Reading Signal newsletter">
 <h2>Daily Reading Signal</h2>
 <p style="font-size:0.85rem; color:#555; margin-bottom:12px;">A literary morning note on which books belong inside the week you're actually in.</p>
{cards}
 <a href="/newsletters/" class="see-all-link">See all {len([n for n in newsletters if n[0] != 'index'])} issues →</a>
</aside>"""


def review_sidebar(reviews: list, count: int = 5) -> str:
    """Return a sidebar of the N most recent reviews for /newsletters/ page."""
    items = sorted(
        [r for r in reviews if r[0] != "index"],
        key=lambda r: _parse_sort_date(r[1].get("date") or ""),
        reverse=True,
    )[:count]
    cards = "\n".join(review_mini_card(slug, meta) for slug, meta, _ in items)
    return f"""<aside class="section-aside" aria-label="Recent book reviews">
 <h2>Recent Book Reviews</h2>
 <p style="font-size:0.85rem; color:#555; margin-bottom:12px;">Honest, editor-vetted reviews from our reviews desk.</p>
{cards}
 <a href="/reviews/" class="see-all-link">See all reviews →</a>
</aside>"""


# ── Related-content strip (used at bottom of individual review/newsletter pages) ────
def related_strip_html(items: list[tuple[str, str, str]], item_kind: str) -> str:
    """Return a 3-column strip of related content cards.

    items: list of (slug, title, summary) tuples.
    item_kind: "newsletter" or "review" — controls the link target.
    """
    if not items:
        return ""
    cards = "\n".join(
        f"""<div class="related-strip-card">
 <div class="related-strip-card__meta">Daily Reading Signal</div>
 <h3 class="related-strip-card__title"><a href="/{item_kind}s/{slug}/">{title}</a></h3>
 <p class="related-strip-card__summary">{summary}</p>
</div>"""
        for slug, title, summary in items
    )
    return f"""<section class="related-strip" aria-label="Related reading">
 <h2>Related reading</h2>
 <div class="related-strip-grid">
{cards}
 </div>
</section>"""


# ── Newsletter Page HTML (individual newsletter) ──────────────────────────────
def newsletter_page_html(slug: str, meta: dict, body_html: str) -> str:
    title    = meta.get("title", slug)
    date     = meta.get("date", "")
    summary  = meta.get("summary", "")
    author   = meta.get("author", "")
    img_src  = meta.get("featured_image", f"/content-images/{slug}.jpg")
    # Normalize: strip leading "content-images/" before prepending (anti-pattern: doubled prefix)
    if img_src and not img_src.startswith('/') and not img_src.startswith('http'):
        img_src = img_src.removeprefix("content-images/")
        img_src = f"/content-images/{img_src}"

    date_str = f'<p class="content-meta">{date}</p>' if date else ""
    author_str = f'<p class="content-byline">by {author}</p>' if author else ""

    # ── Featured product callout (optional) ────────────────────────────────
    # If the newsletter frontmatter has `featured_product: <slug>`, look up
    # the product in the shop data and render a "Reading room → Wildwood Press"
    # block at the bottom. Best-effort: if the product is missing, skip silently.
    # When the callout is empty, the variable is "" and the literal newline
    # template position disappears (no extra blank line).
    featured_product_slug = (meta.get("featured_product") or "").strip()
    product_callout = ""
    if featured_product_slug:
        product_callout = _render_newsletter_product_callout(featured_product_slug)
    # When empty, drop the entire line (otherwise the f-string emits a blank line
    # at the {product_callout} position, polluting the 14 newsletters without a
    # featured product). When non-empty, prepend a newline so the callout gets
    # its own line in the rendered HTML.
    if product_callout:
        product_callout = "\n" + product_callout + "\n"
    else:
        product_callout = ""

    return f"""<div class="story-page">
 <header class="content-header">
  <div class="content-header-inner">
   <span class="tag tag--article">Newsletter</span>
   <h1 class="content-title">{title}</h1>
   {date_str}
   {author_str}
   {f'<p class="content-summary" style="font-size:1.05rem;color:#555;max-width:680px;margin:0 auto 1.5rem;">{summary}</p>' if summary else ''}
  </div>
 </header>

 <div class="content-image"><img src="{img_src}?v=1" alt="{title}" style="width:100%;max-height:400px;object-fit:cover;border-radius:4px;margin-bottom:1.5rem;"></div>

 <div class="content-body">
  <div class="article-body" style="font-size:1.05rem;line-height:1.8;color:var(--text);">
   {body_html}
  </div>
 </div>

 {ADSENSE_BLOCK_HORIZONTAL}
 {SHARE_BAR}{product_callout}
 <div class="related-links">
  <h3 style="font-size:1rem;font-weight:600;margin-bottom:1rem;font-family:var(--font-heading,Georgia,serif);">Read the latest newsletter</h3>
  <div style="display:flex;flex-wrap:wrap;gap:0.75rem;">
   <a href="/newsletters/" style="display:inline-block;padding:6px 14px;background:#f5f0e8;color:#3a2f1e;border:1px solid #3a2f1e;border-radius:3px;text-decoration:none;font-size:.85rem;">All Newsletters</a>
  </div>
 </div>
</div>"""


# ── Newsletter featured-product lookup ─────────────────────────────────────────
# Cached on first use. Reads from projects/printify-etsy-pod/exports/products-visible.json.
_SHOP_PRODUCTS_CACHE = None
_SHOP_SLUG_MAP_CACHE = None


def _load_shop_products():
    """Load the live shop products from disk (cached).

    Returns (products_list, slug_map) where slug_map maps product id → bithues
    URL slug. Both are loaded once per build.
    """
    global _SHOP_PRODUCTS_CACHE, _SHOP_SLUG_MAP_CACHE
    if _SHOP_PRODUCTS_CACHE is not None:
        return _SHOP_PRODUCTS_CACHE, _SHOP_SLUG_MAP_CACHE

    # products-visible.json lives next to the build script's parent's sibling project
    # (workspace-bacottibot/projects/printify-etsy-pod/exports/products-visible.json).
    candidates = [
        Path(__file__).parent.parent.parent / "printify-etsy-pod" / "exports" / "products-visible.json",
        Path(__file__).parent.parent / "exports" / "products-visible.json",
    ]
    products = []
    for path in candidates:
        if path.exists():
            try:
                with open(path) as f:
                    products = json.load(f)
                break
            except Exception:
                products = []
                continue

    # Build slug map (same logic as build_shop_pages.py — keep in sync).
    import re as _re
    slug_map = {}
    for p in products:
        slug = _re.sub(r"[^a-z0-9]+", "-", p["title"].lower()).strip("-")
        slug_map[p["id"]] = slug

    _SHOP_PRODUCTS_CACHE = products
    _SHOP_SLUG_MAP_CACHE = slug_map
    return products, slug_map


def _render_newsletter_product_callout(product_slug: str) -> str:
    """Render the bottom-of-newsletter 'Reading room → Wildwood Press' callout.

    Looks up `product_slug` in the loaded shop data. If not found, returns "".
    """
    products, slug_map = _load_shop_products()

    # Match by slug
    matched = None
    for p in products:
        if slug_map.get(p["id"]) == product_slug:
            matched = p
            break

    if matched is None:
        return ""

    title = _json_ld_escape(matched.get("title", ""))
    desc = (matched.get("description", "") or "").strip()
    # Trim description to ~200 chars for the callout.
    if len(desc) > 220:
        cut = desc[:220].rsplit(" ", 1)[0]
        desc = cut + "…"
    elif len(desc) > 0:
        # remove stray HTML tags if any
        desc = _re.sub(r"<[^>]+>", "", desc)

    img = (matched.get("images") or [{}])[0].get("src", "")
    external_url = (matched.get("external") or {}).get("handle", "") or \
                   (matched.get("external") or {}).get("url", "")
    product_url = f"/shop/wildwood-press/{product_slug}/"

    if not img:
        img_html = ""
    else:
        img_html = f'<a href="{product_url}" style="display:block; flex-shrink:0; width:120px; height:120px; border-radius:4px; background-image:url({img}); background-size:cover; background-position:center;" aria-label="{title}"></a>'

    buy_link = ""
    if external_url:
        buy_link = f'<a href="{external_url}" target="_blank" rel="noopener nofollow sponsored" style="display:inline-block; padding:8px 18px; background:#8a6f3e; color:#fff; text-decoration:none; border-radius:3px; font-weight:500; font-size:.95rem;">View on Etsy →</a>'

    return f"""<!-- Featured product from Wildwood Press Shop (auto-generated from frontmatter 'featured_product') -->
<aside class="newsletter-product-callout" aria-label="Featured from the Wildwood Press Shop" style="max-width:680px; margin:32px auto; padding:24px; background:#faf6ee; border:1px solid #e8e4dd; border-left:4px solid #8a6f3e; border-radius:4px;">
 <div style="display:flex; align-items:flex-start; gap:20px; flex-wrap:wrap;">
  {img_html}
  <div style="flex:1; min-width:240px;">
   <p style="margin:0 0 4px; font-size:.7rem; font-weight:600; color:#8a6f3e; letter-spacing:.1em; text-transform:uppercase;">Reading room → Wildwood Press</p>
   <h3 style="margin:0 0 6px; font-family:var(--font-heading, Georgia, serif); font-size:1.15rem; font-weight:600; line-height:1.3;">
    <a href="{product_url}" style="color:inherit; text-decoration:none;">{title}</a>
   </h3>
   {f'<p style="margin:0 0 12px; font-size:.92rem; line-height:1.55; color:#555;">{desc}</p>' if desc else ''}
   <div style="display:flex; gap:12px; flex-wrap:wrap; align-items:center;">
    {buy_link}
    <a href="{product_url}" style="font-size:.85rem; color:#8a6f3e;">See on Bithues →</a>
   </div>
  </div>
 </div>
</aside>"""


# ── Generate newsletters.html listing ──────────────────────────────────────
def generate_newsletter_page(slug: str, meta: dict, body: str) -> str:
    """Render one newsletter page with the site template and per-page canonical."""
    body_html = inject_adsense_into_body(md_to_html(body, meta), topic=_adsense_topic_from_meta(meta))
    content   = newsletter_page_html(slug, meta, body_html)
    title = meta.get("title", slug)
    desc  = meta.get("summary", f"Bithues Daily Reading Signal: {title}")

    # 2026-08-08 INTERNAL LINKING FIX (class-7 cross-site-bug-ledger):
    # Append a "Recent book reviews" strip to each newsletter page. Each
    # newsletter page becomes a cross-link target for the reviews desk, and
    # each review sees an inbound citation from the newsletter. This is the
    # spoke-to-spoke cross-link that hardens the editorial pipeline in
    # Google's topic-clustering.
    all_reviews = load_md_dir(REVIEWS_DIR)
    all_reviews.sort(key=lambda r: _parse_sort_date(r[1].get("date") or ""), reverse=True)
    related = []
    for r_slug, r_meta, _ in all_reviews:
        if r_slug == "index" or r_slug == slug:
            continue
        related.append((r_slug, r_meta.get("title", r_slug), truncate_words(r_meta.get("summary", ""), 100), r_meta.get("genre_label") or "Book Review"))
        if len(related) >= 3:
            break
    if related:
        cards = "\n".join(
            f"""<div class="related-strip-card">
 <div class="related-strip-card__meta">{r_genre}</div>
 <h3 class="related-strip-card__title"><a href="/reviews/{r_slug}/">{r_title}</a></h3>
 <p class="related-strip-card__summary">{r_summary}</p>
</div>"""
            for r_slug, r_title, r_summary, r_genre in related
        )
        content += f"""<section class="related-strip" aria-label="Recent book reviews">
 <h2>Recent book reviews</h2>
 <div class="related-strip-grid">
{cards}
 </div>
 <p style="margin-top:16px;"><a href="/reviews/" class="see-all-link" style="font-size:0.95rem;">See all reviews →</a></p>
</section>"""

    return wrap_in_template(
        f"{title}",
        desc,
        content,
        "newsletters",
        canonical_path=f"/newsletters/{slug}/",
        meta=meta,
        schema_type="newsletter",
    )


def generate_newsletters_listing(all_newsletters: list[tuple[str, dict, str]]) -> str:
    # Sorted newest first
    items = sorted(
        [n for n in all_newsletters if n[0] != "index"],
        key=lambda n: _parse_sort_date(n[1].get("date") or ""),
        reverse=True,
    )

    if items:
        # Mike 2026-07-10 ET directive: uniform grid of past newsletters +
        # rectangular hero box at the top for the latest issue. The hero box
        # is the wide card with full summary + CTA; the grid below shows all
        # previous issues in 3 columns (matches spaceorbitals layout, with
        # bithues palette).
        latest_slug, latest_meta, _ = items[0]
        latest_title   = latest_meta.get("title", latest_slug)
        latest_date    = latest_meta.get("date", "")
        latest_summary = latest_meta.get("summary", "")
        latest_author  = latest_meta.get("author", "") or ""

        meta_parts = []
        if latest_date:
            meta_parts.append(f'<span class="newsletter-hero__date">{latest_date}</span>')
        if latest_author:
            meta_parts.append(f'<span class="newsletter-hero__author">by {latest_author}</span>')
        meta_parts.append('<span class="newsletter-hero__chip">Latest Issue</span>')
        meta_html = " · ".join(meta_parts)

        latest_block = f"""<article class="newsletter-hero">
 <div class="newsletter-hero__meta">{meta_html}</div>
 <h2 class="newsletter-hero__title">
  <a href="/newsletters/{latest_slug}/">{latest_title}</a>
 </h2>
 <p class="newsletter-hero__summary">{latest_summary}</p>
 <a href="/newsletters/{latest_slug}/" class="newsletter-hero__cta">Read the full signal →</a>
</article>"""

        previous = items[1:]
        cards = "\n".join(newsletter_card(slug, meta, i) for i, (slug, meta, _) in enumerate(previous))
        if cards:
            grid_block = f"""<div class="newsletter-grid">
{cards}
</div>"""
        else:
            grid_block = ""
    else:
        latest_block = ""
        grid_block = """<div class="newsletter-grid">
 <article class="newsletter-grid-card newsletter-grid-card--empty">
  <p>The first daily reading signal arrives tomorrow morning at 7am ET.</p>
 </article>
</div>"""

    # ── 2026-07-22 REDESIGN: conversion-first landing page per spec §"Required Page Order" ──
    # Order: hero → form → benefits → samples → editorial standards → archive → final CTA → AdSense
    # The "archive below persuasion" principle: NO long archive list before the form.

    # ── Step 3: Email signup form (above the fold per spec §"Above-the-Fold Rules") ──
    # TODO (Mike): replace FORM_ACTION_PLACEHOLDER with your ESP endpoint.
    # Options for newsletter@<300-book audience>:
    #   - Buttondown: https://buttondown.email/api/emails/embed-subscribe/<username>
    #   - Mailchimp: https://<dc>.list-manage.com/subscribe/post?u=<u>&id=<id>
    #   - ConvertKit: https://app.convertkit.com/forms/<id>/subscriptions
    #   - Substack: https://<publication>.substack.com/embed
    # The form uses POST + email-only per spec.
    signup_form = """<section class="page-cta signup-form signup-form--hero" aria-label="Subscribe to the Daily Reading Signal">
 <form class="signup-form__form" action="FORM_ACTION_PLACEHOLDER" method="post" target="_blank" novalidate>
  <label for="nl-email" class="visually-hidden">Email address</label>
  <input id="nl-email" class="signup-form__input" type="email" name="EMAIL" placeholder="your@email.com" required autocomplete="email" />
  <button type="submit" class="signup-form__submit">Get tomorrow's signal</button>
 </form>
 <p class="signup-form__fineprint">One morning note a day, every day. Unsubscribe any time.</p>
</section>"""

    # ── Step 4: Three benefit blocks (reader outcomes, NOT features) ──
    # Spec §"Benefit Blocks" — "Each benefit block should express a reader outcome, not a feature."
    benefit_blocks = """<section class="nl-benefits" aria-label="What you get">
 <div class="nl-benefits-grid">
  <div class="nl-benefit">
   <h3 class="nl-benefit__title">Find the right book for the week you are actually in</h3>
   <p class="nl-benefit__body">Every issue names a specific reading condition — a season, an attention state, a problem — and matches it to books that earn their place in that condition. Not a list. A thesis.</p>
  </div>
  <div class="nl-benefit">
   <h3 class="nl-benefit__title">Recover overlooked books at exactly the right moment</h3>
   <p class="nl-benefit__body">A backlist revival returns once or twice a week — an older book whose timing has come back around, with the argument for why now is when it works.</p>
  </div>
  <div class="nl-benefit">
   <h3 class="nl-benefit__title">Build a reading life with more timing and less noise</h3>
   <p class="nl-benefit__body">No bestseller blasts, no marketing copy, no clickbait. One short essay plus 1–3 books, in under five minutes, before your day begins.</p>
  </div>
 </div>
</section>"""

    # ── Step 5: Sample issue cards — 3 hand-picked by issue_type variety ──
    # Priority order per spec SKILL.md "Sample Card Picker Logic":
    # reader-state > micro-season > backlist-revival > quiet-trio > reading-problem-solver > seasonal-shelf > weekly-digest
    PRIORITY_TYPES = [
        "reader-state", "micro-season", "backlist-revival", "quiet-trio",
        "reading-problem-solver", "seasonal-shelf", "weekly-digest",
    ]

    chosen_per_type: dict[str, tuple[str, dict]] = {}
    # Walk items oldest-first within type-priority, skipping the latest (which already lives in the hero).
    for slug, meta, _ in reversed(items[1:]):
        it = (meta.get("issue_type") or "").lower().strip()
        if it in PRIORITY_TYPES and it not in chosen_per_type:
            chosen_per_type[it] = (slug, meta)

    sample_blocks_html_parts = []
    for key in PRIORITY_TYPES:
        chosen = chosen_per_type.get(key)
        if not chosen:
            continue
        s_slug, s_meta = chosen
        s_title = s_meta.get("title", s_slug)
        s_summary = s_meta.get("summary", "")
        s_date = s_meta.get("date", "")
        s_author = s_meta.get("author", "")
        s_type_label = key.replace("-", " ")
        sample_blocks_html_parts.append(f"""<article class="nl-sample-card">
 <div class="nl-sample-card__meta">{s_date} &middot; by {s_author} &middot; <span class="nl-sample-card__type">{s_type_label}</span></div>
 <h3 class="nl-sample-card__title"><a href="/newsletters/{s_slug}/">{s_title}</a></h3>
 <p class="nl-sample-card__summary">{s_summary}</p>
 <a href="/newsletters/{s_slug}/" class="nl-sample-card__cta">Read this issue &rarr;</a>
</article>""")

    sample_block = ""
    if sample_blocks_html_parts:
        sample_block = f"""<section class="nl-samples" aria-label="Sample issues">
 <h2 class="nl-samples__heading">A few recent issues</h2>
 <div class="nl-samples-grid">
{''.join(sample_blocks_html_parts)}
 </div>
</section>"""

    # ── Step 6: Editorial standards ("Why readers stay") — compressed from prior 5 prose sections ──
    editorial_standards = """<section class="nl-standards" aria-label="Editorial standards">
 <h2>Why readers stay</h2>
 <p>Bithues is held to the same standard as the reviews: every book in the newsletter is one the editors have read end to end. Reading signals are framed as the editor's reading of the book, not a generic claim about what the book says. Affiliate links, where they appear, are tied to a specific Bithues recommendation, not to an algorithmic pull. The newsletter is editorial coverage, not a marketing channel.</p>
 <p>The signal runs daily at 5:45 AM ET, in under five minutes. Sunday is reserved for short fiction; there are no affiliate links on Sundays. The archive below goes back to launch and stays accessible.</p>
</section>"""

    # ── Step 8: Final signup CTA + form repeat ──
    # Note: reuse signup_form but rename the inner classes for the final CTA so the CSS hook
    # `.signup-form--final` applies to the OUTER section, not the inner one.
    final_form = signup_form.replace('signup-form signup-form--hero', 'signup-form signup-form--final-inner')
    final_cta = f"""<section class="page-cta signup-form signup-form--final" aria-label="Subscribe">
 <h2 class="signup-form__heading">Start your morning with a signal.</h2>
 <p class="signup-form__subheading">One short essay. 1 to 3 books. Sent at 5:45 AM ET, before the lists.</p>
 {final_form}
</section>"""

    # ── Step 7: Trending this week (NEW 2026-08-07 — Mike directive: surface trending books)
    # Reads .openclaw/tmp/bithues-trending-cache.json. If missing, section is omitted silently.
    # Adds internal cross-promotion to reviews/ when a Bithues review exists for a trending title.
    trending_block = ""
    try:
        trending_cache_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
            ".openclaw", "tmp", "bithues-trending-cache.json"
        )
        if os.path.exists(trending_cache_path):
            with open(trending_cache_path) as _tf:
                _tdata = json.loads(_tf.read())
            _trending_books = _tdata.get("trending_books", [])
            _trending_themes = _tdata.get("themes_observed", [])
            _date_researched = _tdata.get("date_researched", "")
            # Cross-reference trending books against review library
            _review_dir = REVIEWS_DIR
            _bithues_reviews = {}
            for _rf in _review_dir.glob("*.md"):
                _rtxt = _rf.read_text()
                _tm = re.search(r'^title:\s*["\'\u201c](.+?)["\'\u201d]', _rtxt, re.M)
                if _tm:
                    _bithues_reviews[_tm.group(1).lower()] = _rf.stem
            _trending_cards = []
            for _book in _trending_books[:6]:  # cap at 6 cards to keep section tight
                _btitle = _book.get("title", "")
                _bauthor = _book.get("author", "")
                _burl = _book.get("amazon_url", "#")
                _bsource = _book.get("source", "")
                # Internal cross-link if Bithues has a review
                _review_link_html = ""
                _bkey = _btitle.lower()
                for _rkey, _rslug in _bithues_reviews.items():
                    if _rkey in _bkey or _bkey in _rkey:
                        _review_link_html = f' <a class="nl-trending__review-link" href="/reviews/{_rslug}/">Read our review &rarr;</a>'
                        break
                _why = _book.get("why_trending", "")
                _trending_cards.append(f"""<article class="nl-trending__card">
 <div class="nl-trending__source">{_bsource}</div>
 <h3 class="nl-trending__title"><a href="{_burl}" rel="nofollow sponsored">{_btitle}</a><span class="nl-trending__author"> &mdash; {_bauthor}</span></h3>
 <p class="nl-trending__why">{_why}</p>{_review_link_html}
</article>""")
            _themes_html = ""
            if _trending_themes:
                _themes_html = '<ul class="nl-trending__themes">' + "".join(f"<li>{t}</li>" for t in _trending_themes[:4]) + "</ul>"
            if _trending_cards:
                trending_block = f"""<section class="nl-trending" aria-label="Trending this week">
 <div class="nl-trending__header">
  <h2 class="nl-trending__heading">What we are watching this week</h2>
  <p class="nl-trending__sub">Trending books, prizes, and literary conversations as of {_date_researched}. Updated daily from bestseller lists, prize cycles, and the Bithues editorial desk.</p>
 </div>
 <div class="nl-trending-grid">
{''.join(_trending_cards)}
 </div>
{_themes_html}
</section>"""
    except Exception as _trend_err:
        trending_block = ""  # silent fail — section is optional, never break the build

    main = f"""<section class="page-hero">
 <h1>Daily Reading Signal</h1>
 <p class="page-hero__lede">A literary morning note that names the reading condition of the moment and tells you which books belong inside it. Sent daily at 5:45 AM ET.</p>
</section>
{latest_block}
{signup_form}
{benefit_blocks}
{sample_block}
{editorial_standards}
{trending_block}

<!-- 2026-08-08 INTERNAL LINKING FIX (class-7 cross-site-bug-ledger): cross-link /newsletters/ to /reviews/.
     /newsletters/ is unindexed; cross-linking from it to /reviews/ (indexed pages)
     reinforces the editorial pipeline breadth AND helps Google's topic-clustering
     understand that the newsletter and reviews are part of the same content graph. -->
<section class="related-strip" aria-label="Browse book reviews">
 <h2>Browse book reviews</h2>
 <p style="font-size:0.95rem; color:#555; margin-bottom:16px;">Every book in the newsletter has a full review. Browse the reviews desk by genre, length, or mood.</p>
 <div class="related-strip-grid">
  <div class="related-strip-card">
   <div class="related-strip-card__meta">Prehistorical Fiction</div>
   <h3 class="related-strip-card__title"><a href="/reviews/beyond-the-leaning-trees/">Beyond the Leaning Trees</a></h3>
   <p class="related-strip-card__summary">A thoughtful prehistoric survival novella about a young hunter-gatherer who crosses the boundary of the leaning trees.</p>
  </div>
  <div class="related-strip-card">
   <div class="related-strip-card__meta">Science Fiction</div>
   <h3 class="related-strip-card__title"><a href="/reviews/first-contact-diary/">First Contact Diary</a></h3>
   <p class="related-strip-card__summary">A luminous first-contact novel as intimate as a journal and as vast as the night sky.</p>
  </div>
  <div class="related-strip-card">
   <div class="related-strip-card__meta">Hard Science Fiction</div>
   <h3 class="related-strip-card__title"><a href="/reviews/the-martian/">The Martian</a></h3>
   <p class="related-strip-card__summary">When Mark Watney wakes alone on Mars with six months of food, he must become an engineer of his own survival.</p>
  </div>
 </div>
 <p style="margin-top:16px;"><a href="/reviews/" class="see-all-link" style="font-size:0.95rem;">See all reviews →</a></p>
</section>

<section class="nl-archive" aria-label="Newsletter archive">
 <h2>The archive</h2>
 <p class="nl-archive__intro">Every issue, indexed chronologically with the most recent at the top.</p>
{grid_block}
</section>

{final_cta}

{ADSENSE_BLOCK_HORIZONTAL}
"""

    # Build an ItemList schema for the newsletter listing so the page is
    # eligible for the "Top stories" carousel in Google Discover and as a
    # navigational entry point for search engines.
    listing_items = [
        (f"/newsletters/{slug}/", meta.get("title", slug), meta.get("summary", ""))
        for slug, meta, _ in items
    ]
    schema_extra = build_listing_schema(
        "newsletters",
        "Daily Reading Signal",
        "A literary morning note that names the reading condition of the moment and tells you which books belong inside it. A daily newsletter from Bithues for serious readers.",
        BASE_URL + "/newsletters/",
        listing_items,
    )
    return wrap_in_template(
        "Daily Reading Signal — Bithues",
        "A literary morning note that names the reading condition of the moment and tells you which books belong inside it. Sent daily at 5:45 AM ET.",
        main, "newsletters", canonical_path="/newsletters/",
        schema_extra=schema_extra,
    )


# ── Generate index.html ───────────────────────────────────────────────────────
def generate_index(all_stories: list[tuple[str, dict, str]]) -> str:

    # Middle: featured story (first featured or most recent)
    featured = [s for s in all_stories if s[1].get("featured")]
    if not featured:
        featured = all_stories[:1]

    story_slug,  story_meta,  _  = featured[0]
    story_title = story_meta.get("title", story_slug)
    story_genre = story_meta.get("genre_label") or story_meta.get("type_label", "Short Story")
    story_date  = story_meta.get("date") or ""
    story_sum   = story_meta.get("summary", "")[:250]

    articles  = load_md_dir(ARTICLES_DIR)
    articles.sort(key=lambda a: _parse_sort_date(a[1].get("date") or ""), reverse=True)
    # Prefer article with featured:true — promotes manually chosen Editor's Pick
    featured_article = next((a for a in articles if a[1].get("featured")), articles[0] if articles else None)

    reviews   = load_md_dir(REVIEWS_DIR)
    reviews.sort(key=lambda r: _parse_sort_date(r[1].get("date") or ""), reverse=True)
    # Prefer review with featured:true — promotes manually chosen Editor's Pick
    featured_review = next((r for r in reviews if r[1].get("featured")), reviews[0] if reviews else None)

    def hero_col(cls: str, content: str) -> str:
        return f'<div class="hero-col {cls}">{content}</div>'

    # card_image for stories should be the full path or bare slug
    story_img = story_meta.get("card_image", f"/stories/images/{story_slug}.jpg")
    # If card_image already contains a path (e.g. "images/foo.jpg"), use as-is under /stories/images/
    if story_img.startswith('images/') or story_img.startswith('content-images/'):
        story_img = "/stories/images/" + story_img.split('/', 1)[-1]
    elif not story_img.startswith('/') and not story_img.startswith('http'):
        story_img = f"/stories/images/{story_img}"
    middle = f'''<div class="hero-thu-story" style="background-image:url({story_img});" role="img" aria-label="{story_title}"></div>
<div class="category-label">{story_genre}</div>
{('<div class="date-text">' + story_date + '</div>') if story_date else ''}
<h2><a href="/{story_slug}/">{story_title}</a></h2>
<p>{story_sum}</p>
<a href="/{story_slug}/" class="accent-link" style="font-weight:600;">Read Story &#8594;</a>'''

    left = ""
    if featured_article:
        a_slug, a_meta, _ = featured_article
        a_title = a_meta.get("title", a_slug)
        a_genre_raw = a_meta.get("genre_label") or a_meta.get("type_label", "Article")
        a_genre = string.capwords(a_genre_raw) if a_genre_raw.lower() == a_genre_raw else a_genre_raw
        a_sum   = a_meta.get("summary", "")[:180]
        a_img   = a_meta.get("card_image") or a_meta.get("featured_image", f"/content-images/{a_slug}.jpg")
        if a_img.startswith('http'):
            pass  # external URL, use as-is
        elif not a_img.startswith('/'):
            a_img = f"/content-images/{a_img}"
        left = f'''<div class="hero-thu-article" style="background-image:url({a_img});" role="img" aria-label="{a_title}"></div>
<div class="category-label">{a_genre}</div>
<h3><a href="/articles/{a_slug}/">{a_title}</a></h3>
<p>{a_sum}</p>
<a href="/articles/{a_slug}/" class="accent-link">Read Article &#8594;</a>'''

    right = ""
    if featured_review:
        r_slug, r_meta, _ = featured_review
        r_title = r_meta.get("title", r_slug)
        r_genre = r_meta.get("genre_label") or r_meta.get("type_label", "Book Review")
        r_sum   = r_meta.get("summary", "")[:180]
    right = review_card(r_slug, r_meta, 0, variant="feature")

    hero_html = (
        '<section class="hero-section">\n'
        '<div class="section-header hero-label"><h2>EDITOR\'S PICKS: Latest article, story &amp; book review</h2></div>\n'
        '<div class="hero-three-col">\n'
        + hero_col("hero-col--left",   left)   + '\n'
        + hero_col("hero-col--center", middle) + '\n'
        + hero_col("hero-col--right",  right)  + '\n'
        + '</div>\n</section>'
    )

    used_slugs = {
        story_slug,
        featured_article[0] if featured_article else '',
        featured_review[0] if featured_review else '',
    }
    more_stories  = [s for s in all_stories if s[0] not in used_slugs][:3]
    more_articles = [a for a in articles if a[0] not in used_slugs and a[0] != 'index'][:3]
    more_reviews  = [r for r in reviews if r[0] not in used_slugs][:6]

    # ── 2026-08-08 INTERNAL LINKING FIX (class-7 cross-site-bug-ledger) ──────────
    # Load 4 most recent newsletters for a 4-column "Daily Reading Signal" strip
    # below the 3-col section. The homepage is the highest-priority crawl path
    # on the site; cross-linking from it to /newsletters/ spokes is the single
    # highest-leverage change for getting /newsletters/ indexed. Each card uses
    # the standard newsletter_card() component so visual style matches.
    nl_items = load_md_dir(NEWSLETTERS_DIR) if NEWSLETTERS_DIR.exists() else []
    nl_items.sort(key=lambda n: _parse_sort_date(n[1].get("date") or ""), reverse=True)
    more_newsletters = [n for n in nl_items if n[0] != "index"][:4]

    newsletter_strip_html = (
        '<section>\n<div class="section-four-col">\n'

        '<div class="section-col">\n'
        '<div class="section-header">'
        '<h2>DAILY READING SIGNAL</h2>'
        '<a href="/newsletters/" class="explore-link">All issues &#8594;</a>'
        '</div>\n'
        + '\n'.join(newsletter_card(n_slug, n_meta, i)
                    for i, (n_slug, n_meta, _) in enumerate(more_newsletters))
        + '\n</div>\n'

        '</div>\n</section>'
    )

    sections_html = (
        '<section>\n<div class="section-three-col">\n'

        '<div class="section-col">\n'
        '<div class="section-header">'
        '<h2>MORE ARTICLES</h2>'
        '<a href="/articles/" class="explore-link">View all &#8594;</a>'
        '</div>\n'
        + '\n'.join(article_card(a_slug, a_meta, i)
                    for i, (a_slug, a_meta, _) in enumerate(more_articles))
        + '\n</div>\n'

        '<div class="section-col">\n'
        '<div class="section-header">'
        '<h2>MORE STORIES</h2>'
        '<a href="/stories/" class="explore-link">View all &#8594;</a>'
        '</div>\n'
        + '\n'.join(story_card_html(slug, meta, i)
                    for i, (slug, meta, _) in enumerate(more_stories))
        + '\n</div>\n'


        '<div class="section-col">\n'
        '<div class="section-header">'
        '<h2>MORE BOOK REVIEWS</h2>'
        '<a href="/reviews/" class="explore-link">View all &#8594;</a>'
        '</div>\n'
        + '\n'.join(review_card(r_slug, r_meta, i)
                    for i, (r_slug, r_meta, _) in enumerate(more_reviews))
        + '\n</div>\n'

        '</div>\n</section>'
    ) + '\n\n' + newsletter_strip_html

    return wrap_in_template(
        "Bithues — Book Reviews, Reading Guides & Original Stories",
        "In-depth book reviews across fiction, sci-fi, fantasy, nonfiction, and more — plus original short stories.",
        # Ad layout: 1) 336x280 square at the very top
        #           2) full-width responsive ad between Editor's Picks and the intro hero
        #           3) full-width responsive ad at the very bottom (no two stacked ads)
        # Intro hero ("What is Bithues?" + featured review excerpt) sits above
        # the catalog so it has the original prose Google Search Console and
        # AdSense reviewers expect to see on a homepage.
        ADSENSE_BLOCK_SQUARE + '\n'
        + hero_html + '\n'
        + ADSENSE_BLOCK + '\n'
        + HOMEPAGE_INTRO_HERO + '\n'
        + sections_html + '\n\n'
        + ADSENSE_BLOCK_HORIZONTAL,
        canonical_path="/",
        schema_type="website",
    )


# ── Generate individual story page(s) ─────────────────────────────────────────

import re as _re

import re as _re

def generate_story_page_chapters(slug: str, meta: dict, body: str,
                                 prev_slug: str, prev_title: str,
                                 next_slug: str, next_title: str) -> str:
    """Renders a story with chapter cards (expand/collapse) instead of full body."""
    title = meta.get("title", slug)
    genre = meta.get("genre_label") or meta.get("type_label") or "Short Story"
    date  = meta.get("date") or ""
    author = meta.get("author", "")
    img_src = meta.get("cover_image") or meta.get("featured_image") or meta.get("card_image")
    if img_src:
        if img_src.startswith('images/') or img_src.startswith('content-images/'):
            img_src = "/stories/images/" + img_src.split('/', 1)[-1]
        elif not img_src.startswith('/') and not img_src.startswith('http'):
            img_src = f"/stories/images/{img_src}"
        img_html = f'<div class="story-hero-img" style="background-image:url({img_src});" role="img" aria-label="{title}"></div>'
    else:
        img_html = ""

    chapters = meta.get("chapters", [])
    # If chapters is just True (boolean), derive from body markers ## 1., ## 2., etc
    if chapters == True:
        # Extract chapter titles from body: ## N. Title
        import re
        chapter_patterns = re.findall(r'^## (\d+)\. ([^\n]+)', body, re.MULTILINE)
        chapters = [{"num": n, "title": t.strip()} for n, t in chapter_patterns]
    chapter_cards = []

    for ch in chapters:
        num = str(ch.get("num", ""))
        ch_title = ch.get("title", f"Chapter {num}")
        ch_summary = ch.get("summary", "")

        # Find chapter content: between ## N. and the next ## or end of body
        pattern = _re.compile(r'(?:^|\n)## ' + _re.escape(num) + r'\. [^\n]+\n\n(.*?)(?=\n## \d+\. |$)', _re.DOTALL)
        match = pattern.search(body)
        if match:
            ch_text = match.group(1).strip()
            ch_body_html = md_to_html(ch_text, meta)
        else:
            ch_body_html = f'<p class="chapter-summary">{ch_summary}</p>'

        chapter_cards.append(f'''
    <div class="chapter-card" data-chapter="{num}">
     <button type="button" class="chapter-card-header" aria-expanded="false">
      <div class="chapter-num">Ch. {num}</div>
      <div class="chapter-title">{ch_title}</div>
      <div class="chapter-toggle">+</div>
     </button>
     <div class="chapter-card-body">
      {ch_body_html}
     </div>
    </div>''')

    cards_html = "\n".join(chapter_cards)

    nav_html = ""
    if prev_slug or next_slug:
        nav_parts = []
        if prev_slug:
            nav_parts.append(
                f'<a href="/{prev_slug}/" class="story-nav-item prev-item">'
                f'<div class="story-nav-label">&#8592; Previous</div>'
                f'<div class="story-nav-title">{prev_title}</div></a>'
            )
        if next_slug:
            nav_parts.append(
                f'<a href="/{next_slug}/" class="story-nav-item next-item">'
                f'<div class="story-nav-label">Next &#8594;</div>'
                f'<div class="story-nav-title">{next_title}</div></a>'
            )
        nav_html = f'<nav class="story-nav">{"".join(nav_parts)}</nav>'

    date_div = f'<div class="story-meta">{date}</div>' if date else ""
    byline_html = f'<div class="story-byline">by {author}</div>' if author else ""
    body_section = f'<div class="card-grid" style="grid-template-columns:repeat(3,1fr);">{cards_html}</div>'

    adsense = ADSENSE_BLOCK
    adsense_square = ADSENSE_BLOCK_SQUARE
    adsense_horizontal = ADSENSE_BLOCK_HORIZONTAL
    content = f"""<div class="story-page">
 {img_html}
 <div class="story-header">
  <span class="genre-pill">{genre}</span>
  <h1>{title}</h1>
  {date_div}
  {byline_html}
 </div>
 <div class="story-body" id="content">
  {body_section}
{adsense_square}
 </div>
 {SHARE_BAR}
{adsense}
 {nav_html}
</div>
{adsense_horizontal}"""
    return wrap_in_template(f"{title}", meta.get("summary", f"A short story: {title}"),
                            content, canonical_path=f"/{slug}/", meta=meta, schema_type="story")
def generate_story_page(slug: str, meta: dict, body: str,
                        prev_slug: str, prev_title: str,
                        next_slug: str, next_title: str,
                        page_num: int = 1, total_pages: int = 1) -> str:
    body_html = md_to_html(body, meta)
    body_html = inject_adsense_into_body(body_html, topic=_adsense_topic_from_meta(meta))
    content   = story_page_html(slug, meta, body_html,
                                prev_slug, prev_title,
                                next_slug, next_title,
                                page_num, total_pages)
    title = meta.get("title", slug)
    desc  = meta.get("summary", f"A short story: {title}")
    return wrap_in_template(f"{title}", desc, content, canonical_path=f"/{slug}/", meta=meta, schema_type="story")


# ── Generate individual article page ──────────────────────────────────────────
def generate_article_page(slug: str, meta: dict, body: str,
                          prev_slug: str, prev_title: str,
                          next_slug: str, next_title: str) -> str:
    body_html = md_to_html(body, meta)
    body_html = inject_adsense_into_body(body_html, topic=_adsense_topic_from_meta(meta))
    content   = article_page_html(slug, meta, body_html,
                                   prev_slug, prev_title,
                                   next_slug, next_title)
    title = meta.get("title", slug)
    desc  = meta.get("summary", f"An article: {title}")
    return wrap_in_template(f"{title}", desc, content, "articles", canonical_path=f"/articles/{slug}/", meta=meta, schema_type="article")


# ── Generate individual review page ───────────────────────────────────────────
def generate_review_page(slug: str, meta: dict, body: str,
                          prev_slug: str, prev_title: str,
                          next_slug: str, next_title: str) -> str:
    body_html = md_to_html(body, meta)
    body_html = inject_adsense_into_body(body_html, topic=_adsense_topic_from_meta(meta))
    title = meta.get("title", slug)
    desc  = meta.get("summary", f"A book review: {title}")

    # 2026-08-08 TITLE DIFFERENTIATION FIX (class-7 cross-site-bug-ledger):
    # Audit found unindexed reviews had generic titles like "The Martian | Bithues"
    # that compete with Wikipedia, Goodreads, Amazon for the same query. Indexed
    # articles on the site have keyword-rich titles. Pattern:

    #   "<Book Title> by <Author> — A <Genre> Review | Bithues"

    # This adds 3 high-value keyword slots (author name, genre, "review") that
    # differentiate from the dominant horizontal competitors and let Google match
    # to long-tail queries like "best science fiction book review".
    # Falls back through the chain if optional meta fields are missing.
    author = meta.get("author", "").strip()
    genre  = meta.get("genre_label", "").strip()
    if author and genre:
        page_title = f"{title} by {author} — A {genre} Review"
    elif author:
        page_title = f"{title} by {author} — A Book Review"
    elif genre:
        page_title = f"{title} — A {genre} Review"
    else:
        page_title = f"{title} — A Book Review"

    content   = review_page_html(slug, meta, body_html,
                                  prev_slug, prev_title,
                                  next_slug, next_title)

    # 2026-08-08 INTERNAL LINKING FIX (class-7 cross-site-bug-ledger):
    # Append a "Recent newsletters" strip below the review body. Each individual
    # review page becomes a cross-link target for the Daily Reading Signal, and
    # the newsletter sees its citation-graph grow per review. This is the spoke-
    # to-spoke cross-link that hardens the relationship between reviews and
    # newsletters in Google's topic-clustering.
    nl_items = load_md_dir(NEWSLETTERS_DIR) if NEWSLETTERS_DIR.exists() else []
    nl_items.sort(key=lambda n: _parse_sort_date(n[1].get("date") or ""), reverse=True)
    related = [(n_slug, n_meta.get("title", n_slug), truncate_words(n_meta.get("summary", ""), 100))
               for n_slug, n_meta, _ in nl_items[:3] if n_slug != "index"]
    if related:
        cards = "\n".join(
            f"""<div class="related-strip-card">
 <div class="related-strip-card__meta">Daily Reading Signal</div>
 <h3 class="related-strip-card__title"><a href="/newsletters/{r_slug}/">{r_title}</a></h3>
 <p class="related-strip-card__summary">{r_summary}</p>
</div>"""
            for r_slug, r_title, r_summary in related
        )
        content += f"""<section class="related-strip" aria-label="Recent newsletters">
 <h2>Recent from the Daily Reading Signal</h2>
 <div class="related-strip-grid">
{cards}
 </div>
 <p style="margin-top:16px;"><a href="/newsletters/" class="see-all-link" style="font-size:0.95rem;">See all issues →</a></p>
</section>"""

    return wrap_in_template(f"{page_title}", desc, content, "reviews", canonical_path=f"/reviews/{slug}/", meta=meta, schema_type="review")


# ── Simple pages ────────────────────────────────────────────────────────────────
def generate_about() -> str:
    # Bithues author roster. One-line blurbs, kept tight for the team grid.
    # Source of truth for full coverage: /content/authors/<name>.md
    team = [
        {
            "name":  "Eleanor Ashford",
            "role":  "Literary fiction, slow reads",
            "blurb": "Translated literature, historical fiction, literary romance, and character-driven prehistorical fiction. Reads to inhabit a voice, not to summarize a plot.",
        },
        {
            "name":  "Marcus Cole",
            "role":  "Sci-fi, fantasy, world-building",
            "blurb": "Hard SF, space opera, fantasy, horror, and the places where speculative metaphysics meets narrative architecture. Comes from game design, takes craft seriously.",
        },
        {
            "name":  "Julian Cross",
            "role":  "Editorial lead, cultural criticism, essays",
            "blurb": "Coordinates the editorial calendar across the desk and writes long-form essays on books, culture, and the publishing industry. Previously wrote for Rolling Stone and The Baffler; maintains a Substack with about 8,000 readers.",
        },
        {
            "name":  "Sarah Voss",
            "role":  "Short fiction, experimental, debuts",
            "blurb": "Short story collections, flash fiction, debut novelists, small press, experimental prose, and the literary edges of prehistorical fiction.",
        },
        {
            "name":  "David Okonkwo",
            "role":  "Non-fiction, guides, practical reads",
            "blurb": "History, biography, business, thrillers, self-help, travel guides, and our children's books coverage — picture books through early readers and family reads.",
        },
        {
            "name":  "Thomas Mercer",
            "role":  "Military, survival, action",
            "blurb": "Military thrillers, survival fiction, action-adventure, international intrigue, geopolitical thrillers, police procedurals, and military history.",
        },
        {
            "name":  "Priya Mehta",
            "role":  "Literary speculative fiction",
            "blurb": "Former astrophysicist. Reviews philosophical SF, weird fiction, literary horror, magical realism, slipstream, and contemplative science fiction.",
        },
    ]

    team_cards = "\n".join(
        f'   <div class="team-card">\n'
        f'    <h3 class="team-card-name">{m["name"]}</h3>\n'
        f'    <div class="team-card-role">{m["role"]}</div>\n'
        f'    <p class="team-card-blurb">{m["blurb"]}</p>\n'
        f'   </div>'
        for m in team
    )

    main = f"""<div class="page-hero">
 <h1>About Bithues</h1>
 <p>An independent book review site and short fiction publisher, in operation since 2024.</p>
</div>
<div class="page-content">
 <div class="about-body">
{ADSENSE_BLOCK_SQUARE}
  <p><strong>Bithues</strong> is an independent book review site and short fiction publisher. We write honest, long-form reviews of books we think are worth your time — fiction, nonfiction, sci-fi, fantasy, and everything in between — and we publish original short fiction from working writers. The site launched in <strong>March 2024</strong> and has published roughly 50 book reviews, 40+ short stories, and 60+ essays and roundups, each one read and edited by a person on the masthead below.</p>

  <h2>Editorial lead: Julian Cross</h2>
  <p>Bithues is edited by <strong>Julian Cross</strong>, who oversees the editorial calendar and writes the site's long-form essays and cultural criticism. Julian is a journalist who previously wrote for <em>Rolling Stone</em> and <em>The Baffler</em>, and who maintains a Substack with about 8,000 subscribers. He coordinates the seven editors on the masthead, decides the final editorial direction of the site, and writes the pieces that don't fit neatly into any one genre. Julian's coverage area is cultural criticism and essays — the books that sit at the intersection of literature and the rest of the world.</p>
  <p>If you want to know who is responsible for a particular review or article, every page on Bithues is signed by the editor who wrote it. If you want to reach Julian directly about editorial matters, you can email <a href="mailto:editor@bithues.com">editor@bithues.com</a>.</p>

  <h2>How we pick what to review</h2>
  <p>The short version: we read what interests us, and we write about what we think will interest you. The longer version is below.</p>
  <p>Each editor on the masthead has a defined coverage area. When a book arrives that fits an editor's coverage area — through a publisher pitch, a publicist email, a bookstore browse, or just the editor's own curiosity — that editor reads the book end-to-end before writing anything about it. We do not write reviews based on summaries, sample chapters, or publisher copy. We do not write reviews of books we have not finished. We do not write positive reviews because a publicist is friendly to us, and we do not write negative reviews because an author annoyed us on social media.</p>
  <p>About 60 percent of what we review is sent to us by publishers and publicists; about 40 percent is chosen by the editors themselves from bookstore browsing, library stacks, and recommendations from readers. We accept advance reader copies (galleys) for forthcoming books when they help us meet publication timing, but receiving a galley does not obligate us to review the book, and a negative review of a galley'd book is no more or less likely than a negative review of a book we bought ourselves.</p>

  <h2>Corrections policy</h2>
  <p>We make mistakes. When we do, we fix them as quickly as we can and we say so on the page.</p>
  <p>If you spot a factual error — a wrong publication date, a misspelled author name, a plot point that doesn't match what actually happens in the book — please email <a href="mailto:corrections@bithues.com">corrections@bithues.com</a>. We will verify the error, correct it on the page, and add a dated note at the bottom of the article explaining what was changed. We do not silently rewrite history; if a correction is made more than 30 days after publication, we leave a visible breadcrumb at the bottom of the article so a reader who saw the original version knows that something changed.</p>
  <p>Corrections of opinion are different from corrections of fact. If you disagree with a review, the right place to make that argument is your own blog, your own letter to us, or the comments on the review. We do not revise reviews because a reader disagreed with the take. We do revise reviews when the take was based on a factual error that we missed.</p>

  <h2>Meet the Bithues editors</h2>
  <p>Bithues is run by a small team of seven editors, each with a defined coverage area and a defined voice. The structure exists because no single editor can read everything well — the right reviewer for a literary novel is not the right reviewer for a hard SF novel, and the right reviewer for a children's picture book is not the right reviewer for a history of the Roman Empire. Each editor on the masthead reads within their coverage area and writes within it, and the editorial lead coordinates across coverage areas so the site has a coherent editorial direction.</p>
  <div class="team-grid">
{team_cards}
  </div>

  <h2>Book reviews</h2>
  <p>Our reviews are honest, independent takes on books we've read and think others should read. A typical Bithues review runs 1,000 to 2,000 words — long enough to engage with the book's actual argument, short enough to read in one sitting. We may earn a small affiliate commission when you purchase through links on this site — at no extra cost to you. Editorial decisions are never influenced by commissions or complimentary copies, and our reviews carry a clear disclosure when a book was received as a galley.</p>

  <h2>Short fiction</h2>
  <p>Every story on Bithues is original fiction, published here first. We believe short fiction is where writers take their best risks — with voice, structure, and the way a story moves through the world. We accept submissions through <a href="mailto:submissions@bithues.com">submissions@bithues.com</a>, we respond to every submission within four weeks, and we pay a small honorarium for published work. We also review books for children and young readers, including the <a href="/reviews/little-mike-learns-to-fly/">Little Mike series</a>.</p>

{ADSENSE_BLOCK}
  <h2>Contact</h2>
  <p>There are several ways to reach us, depending on what you want to talk about:</p>
  <ul>
   <li><strong>General inquiries:</strong> <a href="mailto:info@bithues.com">info@bithues.com</a> &mdash; reader letters, partnerships, and "where do I start" questions.</li>
   <li><strong>Editorial matters:</strong> <a href="mailto:editor@bithues.com">editor@bithues.com</a> &mdash; addressed to Julian Cross, the editorial lead.</li>
   <li><strong>Corrections:</strong> <a href="mailto:corrections@bithues.com">corrections@bithues.com</a> &mdash; factual errors, broken links, and accessibility issues.</li>
   <li><strong>Submissions:</strong> <a href="mailto:submissions@bithues.com">submissions@bithues.com</a> &mdash; original short fiction, 1,000 to 12,000 words.</li>
   <li><strong>Review requests:</strong> <a href="mailto:reviews@bithues.com">reviews@bithues.com</a> &mdash; authors, publicists, and publishers.</li>
  </ul>
  <p>All inquiries are read by a person. Not all replies come immediately — but they come. Our average response time is under five business days for review requests and press, and under four weeks for fiction submissions.</p>

  </div>
</div>
{ADSENSE_BLOCK_HORIZONTAL}"""
    return wrap_in_template("About",
        "About Bithues — who we are, what we do, and what we stand for.",
        main, "about", canonical_path="/about/")



def generate_contact() -> str:
    # Professional, literary contact page. Reuses the existing .page-hero /
    # .about-body patterns and adds structured "channel" blocks (small,
    # readable cards) so visitors can route themselves to the right inbox
    # instead of one catch-all address.
    main = f"""<div class="page-hero">
 <h1>Contact</h1>
 <p>The Bithues inbox is read by a real person. Use the channel below that fits your reason for writing, and you&rsquo;ll hear back faster.</p>
</div>
<div class="page-content">
 <div class="about-body">
{ADSENSE_BLOCK_SQUARE}
  <p>Bithues is an independent book review site and short fiction publisher, run by a small team based in the United States. We don&rsquo;t have a press office, a submissions portal, or a ticketing system. We have one editor and one inbox &mdash; and we read everything that comes in.</p>
  <p>If you&rsquo;re not sure where your message belongs, <strong><a href="mailto:info@bithues.com">info@bithues.com</a></strong> is always the right place to start. We&rsquo;ll route it from there.</p>

  <h2>How can we help?</h2>
  <p>Most messages fall into one of the four channels below. Use the address that fits &mdash; it helps us reply faster and keeps the right thing in front of the right person.</p>

  <div class="contact-channels">
   <div class="contact-channel">
    <h3>Story submissions</h3>
    <p><a href="mailto:submissions@bithues.com"><strong>submissions@bithues.com</strong></a></p>
    <p>Send us your short fiction &mdash; 1,000 to 12,000 words. Original work only; simultaneous submissions are fine if you let us know. Paste the story in the body of the email, or attach a clean <code>.doc</code> or <code>.docx</code>. Include a short bio and a one-sentence pitch. We respond to every submission within four weeks.</p>
   </div>

   <div class="contact-channel">
    <h3>Book review requests</h3>
    <p><a href="mailto:reviews@bithues.com"><strong>reviews@bithues.com</strong></a></p>
    <p>Authors, publicists, and publishers: send a one-paragraph pitch, a press kit or sample chapter, and the publication date. We do not guarantee a review, and we do not accept payment, gifts, or affiliate placement in exchange for coverage. We read what we&rsquo;re sent and we tell you honestly whether it&rsquo;s a fit.</p>
   </div>

   <div class="contact-channel">
    <h3>Press, partnerships &amp; rights</h3>
    <p><a href="mailto:press@bithues.com"><strong>press@bithues.com</strong></a></p>
    <p>Interview requests, podcast appearances, anthology invitations, translation and reprint rights, syndication, and brand or partnership inquiries. Tell us what you have in mind, the timeline, and any constraints (exclusivity, embargoes, deadlines).</p>
   </div>

   <div class="contact-channel">
    <h3>Everything else</h3>
    <p><a href="mailto:info@bithues.com"><strong>info@bithues.com</strong></a></p>
    <p>Reader letters, corrections, accessibility questions, takedown requests, and notes from people who just want to say hello. This is also the right address for privacy and data questions &mdash; we respond to every one.</p>
   </div>
  </div>

  <h2>What to include</h2>
  <p>A few details make it easier for us to act on a message quickly:</p>
  <ul>
   <li><strong>Your name</strong> and how you&rsquo;d like to be addressed in any reply.</li>
   <li><strong>A subject line that names the topic</strong> &mdash; &ldquo;Submission: <em>The Quiet Town</em>&rdquo; beats &ldquo;Hello!&rdquo; every time.</li>
   <li><strong>Links, not attachments</strong> &mdash; for press kits, author sites, retailer pages, and excerpts. We&rsquo;ll ask for the full file if we need it.</li>
   <li><strong>Your timezone</strong> &mdash; only if the timing of a reply actually matters.</li>
  </ul>

  <h2>What we won&rsquo;t do</h2>
  <p>In the interest of being clear about who we are and what we do:</p>
  <ul>
   <li>We don&rsquo;t run paid reviews, sponsored posts, or &ldquo;advertorial&rdquo; content, and we don&rsquo;t accept compensation in exchange for coverage.</li>
   <li>We don&rsquo;t sell, rent, or trade reader email addresses. The newsletter is opt-in only and you can unsubscribe in one click.</li>
   <li>We don&rsquo;t respond to AI-generated outreach, link-swap requests, or &ldquo;quick favor&rdquo; SEO pitches. Those go straight to the archive.</li>
  </ul>

  <h2>How long does a reply take?</h2>
  <p><strong>Submissions:</strong> within four weeks, usually sooner. If you haven&rsquo;t heard from us in six, feel free to follow up &mdash; we won&rsquo;t have forgotten you, but we may have missed the message.</p>
  <p><strong>Review requests and press:</strong> within five business days. We&rsquo;ll tell you yes, no, or &ldquo;not right now&rdquo; &mdash; and we&rsquo;ll mean it.</p>
  <p><strong>Reader letters and corrections:</strong> within a few days. Faster if it&rsquo;s a correction; we&rsquo;d rather fix something today than next week.</p>

  <h2>Snail mail</h2>
  <p>For rights, contracts, and legal correspondence, a physical mailing address is available on request &mdash; please email <strong><a href="mailto:press@bithues.com">press@bithues.com</a></strong> and we&rsquo;ll send it. We don&rsquo;t publish a street address on the open web.</p>
{ADSENSE_BLOCK}

  <h2>How the contact page is organized</h2>
  <p>This contact page is organized by the kind of message you're sending rather than by who on the masthead should receive it. Each channel below describes what it is for, what response time to expect, and what we will and will not do with the messages that arrive there. The page exists so writers and publicists do not have to guess who at Bithues handles what.</p>

  <h2>What we will reply to</h2>
  <p>We reply to every substantive message. We reply to corrections fastest, because corrections are the kind of message we most want to receive. We reply to story submissions according to the timeline stated on the channel. We reply to review requests with a yes, a no, or a "not right now," and we commit to meaning whichever one we send. We reply to reader letters within a few days. We reply to press inquiries within five business days.</p>

  <h2>What we will not reply to</h2>
  <p>We do not reply to pitch decks sent without prior introduction, link-exchange requests, requests to remove a critical review, requests for paid placement in the review queue, requests for backlinks or SEO boosts, "AI content" or "AI backlinks" solicitations, or messages that begin with compliments and pivot to a request. We read all of these; we do not reply to most of them. If you have written one of these, you will not hear back, and that silence is the reply.</p>

  <h2>Privacy and what we do with your message</h2>
  <p>The contact form and email channels exist so you can write to us; what you write is between us and is not republished. We do not sell, share, or rent the contact database. We do not use the messages for anything other than responding to them. Corrections that result from a reader message are credited in the relevant article unless the writer asks to remain anonymous; substantive feedback that leads to a follow-up piece is acknowledged in the piece. Full details are on the Privacy page.</p>
 </div>
</div>
{ADSENSE_BLOCK_HORIZONTAL}"""
    return wrap_in_template("Contact",
        "Contact Bithues — story submissions, review requests, press, and reader letters. Every message is read by a human, and we reply to all of them.",
        main, "contact", canonical_path="/contact/")



def generate_legal(page: str) -> str:
    if page == "privacy":
        title_s = "Privacy Policy"
        body_s = """<div class="page-header">
 <h1>Privacy Policy</h1>
</div>
<div class="legal-body">
 <p><strong>Last updated: May 2026</strong></p>
 <p>Bithues is a personal fiction publication. This policy explains how we collect, use, and protect information when you visit our website.</p>
 <h2>Information We Collect</h2>
 <p>Bithues does not require registration, subscription, or personal information to read our content. We do not collect names, email addresses, or any personally identifiable information through this website.</p>
 <h2>Automatically Collected Information</h2>
 <p>When you visit our site, our hosting provider (Cloudflare) may automatically collect standard server log information, including your IP address, browser type, pages visited, and referring URL. This information is used only for site operation, security, and aggregate analytics.</p>
 <h2>Third-Party Services</h2>
 <p><strong>Advertising:</strong> We use Google AdSense to display advertisements on our site. Google uses cookies to serve ads based on your prior visits to this or other websites. You may opt out of Google's use of cookies by visiting the <a href="https://www.google.com/settings/ads" target="_blank" rel="noopener">Google Ads Settings</a>.</p>
 <p><strong>Affiliate Links:</strong> Some links on this site are affiliate links (Amazon Associates program). If you click an affiliate link and make a purchase, we may earn a small commission at no additional cost to you. Amazon's privacy policy applies to purchases made through Amazon affiliate links.</p>
 <p><strong>External Links:</strong> Our site may link to external websites (e.g., book retailer pages). We are not responsible for the privacy practices of external sites. We encourage you to review the privacy policies of those services.</p>
 <h2>Cookies</h2>
 <p>We do not use first-party cookies for tracking or advertising. Third-party services (Google AdSense, Cloudflare) may use their own cookies as described in their respective privacy policies. You can manage cookie preferences through your browser settings.</p>
 <h2>Data Retention</h2>
 <p>Server log data is retained for a limited period as required by our hosting provider for security and operational purposes. We do not retain personal data beyond what is automatically collected in server logs.</p>
 <h2>Your Rights</h2>
 <p>You have the right to know what data is collected about you (though we collect very little). You may contact us at <strong>info@bithues.com</strong> with any questions about this policy.</p>
 <h2>Children's Privacy</h2>
 <p>Bithues is not directed at children under 13. We do not knowingly collect information from children.</p>
 <h2>Changes to This Policy</h2>
 <p>We may update this policy from time to time. Changes will be posted on this page with an updated revision date.</p>
 <h2>Contact</h2>
 <p>For any privacy-related questions, contact us at <strong>info@bithues.com</strong>.</p>

 <h2>What this policy covers</h2>
 <p>This privacy policy describes what information is collected when you visit this site, how that information is used, and the choices you have regarding the information. The policy applies to all pages on this domain. The policy is incorporated by reference into any service offered on the site (newsletter subscriptions, contact form submissions, comment threads, and any other interactive features).</p>
 <p>The policy is written in plain English rather than legal English because the goal is for readers to actually understand what is collected and what is not. Where the policy uses a term that has a specific legal meaning, the term is defined inline rather than in a glossary at the bottom. Where the policy makes commitments about what is and is not done with reader data, the commitments are stated as such and the consequences of breaching them are stated as well.</p>

 <h2>Information we do not collect</h2>
 <p>Bithues does not require registration, subscription, or personal information to read any of the content on the site. We do not collect names, email addresses, phone numbers, or any other directly identifying information from visitors. We do not require an account to read the books we review, the articles we publish, or the short fiction on the site. We do not run ads that target readers by name, email, or any other identifier.</p>

 <h2>Reader communication</h2>
 <p>When readers write to us through the contact form or by email, we keep what they sent in order to respond. We do not add readers to any marketing list based on a contact form message. We do not share the messages with third parties. Corrections that result from a reader message are credited in the relevant piece unless the writer asks to remain anonymous; substantive feedback that leads to a follow-up piece is acknowledged in the piece. The full archive of correspondence is not retained beyond what is needed for the relevant exchange.</p>

 <h2>Data retention</h2>
 <p>Server log data is retained for a limited period as required by our hosting provider for security and operational purposes. We do not retain personal data beyond what is automatically collected in server logs. Contact form submissions are retained for as long as needed to respond and to retain context for any follow-up; messages that are purely transient are deleted within ninety days.</p>

 <h2>Children's privacy</h2>
 <p>Bithues is not directed at children under 13. We do not knowingly collect information from children. We do not run content, advertising, or features that are specifically targeted at children under 13. The Bithues children's book coverage exists because parents and educators visit the site looking for book recommendations for their children; we write about children's books for adults who are choosing books on behalf of children, not for the children themselves.</p>
</div>"""
    else:
        title_s = "Terms of Service"
        body_s = """<div class="page-header">
 <h1>Terms of Service</h1>
</div>
<div class="legal-body">
 <p><strong>Last updated: May 2026</strong></p>
 <p>By using the Bithues website, you agree to these terms. If you do not agree, please do not use this site.</p>
 <h2>Content</h2>
 <p>All stories, articles, and reviews published on Bithues are original works of fiction or editorial content unless explicitly marked as nonfiction. Any resemblance to actual events, persons, or places is coincidental — and entirely intentional where the author intends it.</p>
 <p>The design, code, layout, and branding of this website are the property of Bithues. Content from this site may not be reproduced, distributed, or transmitted in any form without prior written permission, except where explicitly noted.</p>
 <h2>Affiliate Links</h2>
 <p>Bithues contains affiliate links, primarily through the Amazon Associates program. When you purchase products through these links, Bithues may earn a small commission at no extra cost to you. We only recommend products we believe in.</p>
 <h2>User Conduct</h2>
 <p>You agree to use this website only for lawful purposes. You may not use this site to copy, distribute, or scrape content without permission. Automated access must comply with our hosting provider's terms of service.</p>
 <h2>Disclaimer</h2>
 <p>The views expressed in any story, article, or review on Bithues are those of the respective author and do not reflect the views of Bithues as an entity or its operators. We are not responsible for content on external sites linked from here.</p>
 <p>The information on this site is provided as-is, without warranties of any kind, express or implied. We do not guarantee the accuracy, completeness, or usefulness of any content.</p>
 <h2>Limitations of Liability</h2>
 <p>Bithues and its operators will not be held liable for any direct, indirect, incidental, or consequential damages arising from your use of this website or any content on it.</p>
 <h2>Indemnification</h2>
 <p>You agree to indemnify and hold harmless Bithues and its operators from any claim, damage, or expense arising from your violation of these terms or your use of this website.</p>
 <h2>Governing Law</h2>
 <p>These terms are governed by the laws of the United States. Any disputes shall be resolved in the courts of the United States.</p>
 <h2>Changes to These Terms</h2>
 <p>We may update these terms at any time. Continued use of the site after changes constitutes acceptance of the new terms.</p>
 <h2>Contact</h2>
 <p>Questions about these terms? Contact us at <strong>info@bithues.com</strong>.</p>

 <h2>What these terms cover</h2>
 <p>These terms govern your use of the Bithues website. The terms apply to all visitors to the site, regardless of whether you are a reader, a subscriber, a contributor, or a casual visitor arriving from a search engine. The terms apply to all uses of the site, including reading articles and reviews, browsing the shop, signing up for the newsletter, submitting a story, and using the contact form. The terms do not extend to third-party sites that we link to; those sites have their own terms.</p>
 <p>The terms are written in plain English rather than legal English. Where a term has a specific legal meaning, the meaning is stated in plain English rather than in legal shorthand. Where the terms grant Bithues a right, the right is stated along with the limits on that right. Where the terms limit Bithues's liability, the limits are stated along with what is not excluded. The goal is for readers to be able to read these terms and understand what they are agreeing to.</p>

 <h2>Editorial standards</h2>
 <p>Reviews on Bithues are written by named editors after the editor has read the book end to end. The reviews state the editorial opinion of the editor; they are not objective assessments and should not be read as such. Reviews are not paid for, are not influenced by the publisher, and are not contingent on the publisher providing the book. The full editorial process is documented on the About page.</p>

 <h2>User contributions</h2>
 <p>When you submit a story to Bithues through the contact form, you retain copyright to the story. Bithues receives a license to publish the story on the site, in the newsletter, and in any anthology that Bithues produces with the story in it. The license is non-exclusive; you may publish the story elsewhere, including in a print collection, after the Bithues publication has run. We ask that you do not publish the story on another free-to-read site while it is live on Bithues, because the simultaneous publication splits the audience and reduces the readership for both.</p>

 <h2>Newsletter and email</h2>
 <p>Subscribing to the newsletter requires an email address. The email address is used only for the newsletter. Subscribers can unsubscribe at any time through the unsubscribe link in the footer of any newsletter email. We do not sell, share, or rent the email list. We do not use the list for anything other than the newsletter and the occasional site announcement related to the newsletter itself.</p>

 <h2>Review of these terms</h2>
 <p>We review these terms on the same schedule we review the privacy policy and the contact page — annually, or whenever a change in how the site operates demands it. The "Last updated" date at the top of this page is the date the current version took effect. Subscribers who want to know when the terms change can subscribe to the newsletter; substantial changes are flagged in a dedicated newsletter issue before they take effect. Readers who spot anything in these terms that is unclear, incorrect, or out of date are welcome to write to us through the contact form.</p>
</div>"""

    body_s_with_ads = inject_adsense_into_body(body_s)

    main = f"""<div class="story-page" style="max-width:800px;margin:0 auto;">
 {body_s_with_ads}
 {ADSENSE_BLOCK_HORIZONTAL}
</div>"""
    return wrap_in_template(f"{title_s}",
        f"{title_s} — Bithues.", main, canonical_path=f"/{page.lower()}")


# ── Reading Maps page ─────────────────────────────────────────────────────────
def generate_reading_maps() -> str:
    """Load content/reading-maps.md and render it as a standalone page at /reading-maps/.

    The MD file uses page_type: reading-maps in frontmatter.
    Output: OUTPUT_DIR/reading-maps/index.html
    """
    rm_path = Path(__file__).parent.parent / "content" / "reading-maps.md"
    if not rm_path.exists():
        return ""

    raw = rm_path.read_text(encoding="utf-8")
    meta, body = parse_front_matter(raw)
    body_html = md_to_html(body, meta)

    title = meta.get("title", "Reading Maps")
    desc  = meta.get("summary", "Curated paths through books, sequenced deliberately.")

    main = f"""<div class="story-page">
 <header class="content-header">
  <div class="content-header-inner">
   <span class="tag tag--article">Lists</span>
   <h1 class="content-title">{title}</h1>
  </div>
 </header>
 <div class="content-body" style="max-width:800px;margin:0 auto;padding:0 1rem;">
  <div class="article-body" style="font-size:1.05rem;line-height:1.8;color:var(--text);">
   {body_html}
  </div>
 </div>
 {ADSENSE_BLOCK_HORIZONTAL}
</div>"""

    return wrap_in_template(title, desc, main, active_nav="reading-maps",
                            canonical_path="/reading-maps/", meta=meta)


# ── Sitemap ─────────────────────────────────────────────────────────────────────
# Bithues canonicalizes to the bare domain (https://bithues.com/) on every page
# (see BASE_URL above). The sitemap must agree, or GSC flags "sitemap vs canonical
# mismatch" duplicate content. Force www → bare redirect at the _redirects level
# so this matches the rest of the site.
SITEMAP_BASE = "https://bithues.com"

def generate_sitemap(stories: list, articles: list, reviews: list, newsletters: list | None = None) -> str:
    """Return a valid XML sitemap string with all content pages.

    Every entry MUST include <lastmod>YYYY-MM-DD</lastmod> derived from each
    item's frontmatter `date` so Googlebot re-crawls updated content. Without
    lastmod, GSC returns "URL is unknown to Google" for newly updated pages
    and Google will not re-crawl on subsequent sitemap submissions (verified
    2026-07-09 via URL Inspection API after the newsletter upgrade).

    Static pages with no frontmatter date get today's date — they are touched
    on every site build, so today's date is accurate.
    """
    from datetime import date as _date
    today = _date.today().isoformat()
    urls = []

    # Static pages (all with trailing slash, lastmod = today — touched every build)
    # Added /shop/ 2026-08-04 (was missing from sitemap despite /shop/index.html
    # existing on disk, causing "URL unknown to Google" — fix per cross-site
    # sitemap audit).
    static = [
        "/",
        "/about/",
        "/articles/",
        "/book-match/",
        "/reviews/",
        "/stories/",
        "/newsletters/",
        "/shop/",
        "/contact/",
        "/privacy/",
        "/terms/",
        "/best/",
        "/reading-maps/",
    ]
    for path in static:
        urls.append((f"{SITEMAP_BASE}{path}", today))

    # Best-of roundup pages (generated by gen_best_pages.py). Add each
    # /best/<slug>/ URL to the sitemap with lastmod = today.
    best_dir = Path(__file__).parent / "best"
    if best_dir.exists():
        for best_subdir in sorted(best_dir.iterdir()):
            if not best_subdir.is_dir():
                continue
            urls.append((f"{SITEMAP_BASE}/best/{best_subdir.name}/", today))

    def _entry(slug: str, meta: dict, path_prefix: str = "/") -> tuple[str, str]:
        # path_prefix default is "/" so root-level stories (no section dir) get
        # the separator. Articles/reviews/newsletters pass explicit "/articles/"
        # etc. so they keep working.
        loc = f"{SITEMAP_BASE}{path_prefix}{slug}/"
        # Lastmod = the item's frontmatter date (YYYY-MM-DD). Fall back to today.
        lastmod = (meta.get("date") or "").strip() or today
        # Validate format — lastmod must be ISO date or W3C datetime.
        # If the frontmatter is malformed, fall back to today rather than emit garbage.
        if len(lastmod) < 10 or lastmod[4:5] != "-" or lastmod[7:8] != "-":
            lastmod = today
        return (loc, lastmod[:10])

    # Stories: /{slug}/  (root-level, not /stories/{slug}/)
    for slug, meta, _ in stories:
        urls.append(_entry(slug, meta))

    # Articles: /articles/{slug}/  — skip index.md (listing source, not a page)
    for slug, meta, _ in articles:
        if slug == "index":
            continue
        urls.append(_entry(slug, meta, "/articles/"))

    # Reviews: /reviews/{slug}/
    for slug, meta, _ in reviews:
        urls.append(_entry(slug, meta, "/reviews/"))

    # Newsletters: /newsletters/{slug}/  (skip index.md if it ever appears)
    if newsletters:
        for slug, meta, _ in newsletters:
            if slug == "index":
                continue
            urls.append(_entry(slug, meta, "/newsletters/"))

    # Series hubs: /series/{slug}/  — walk OUTPUT_DIR/series/ for any subdir with index.html
    # (Added 2026-06-17: /series/otomi/ was missing from sitemap, showing as
    # "Discovered - currently not indexed" in GSC. /series/otomi/index.html is
    # a committed static page, not MD-built, so we walk the filesystem.)
    # (Retired 2026-07-18: /series/ renamed under /collections/ as part of the
    # Collections consolidation. /collections/otomi-saga/ now lives alongside
    # /collections/physics-consciousness/ and /collections/little-mike-books/.
    # Old /series/otomi/ URL is 301'd in _redirects for legacy index entries.)
    series_root = OUTPUT_DIR / "series"
    if series_root.exists():
        for series_dir in sorted(series_root.iterdir()):
            if series_dir.is_dir() and (series_dir / "index.html").exists():
                # Series pages don't have an MD frontmatter date; use today.
                urls.append((f"{SITEMAP_BASE}/series/{series_dir.name}/", today))

    # Collections (non-index, static-HTML): /collections/{slug}/ for any
    # subdir with index.html. Mirrors the series_root walk pattern.
    # (Added 2026-07-18 to cover /collections/little-mike-books/ and
    # /collections/otomi-saga/ which are committed static pages, not MD-built.)
    collections_root = OUTPUT_DIR / "collections"
    if collections_root.exists():
        # Manual set: skip the umbrella /collections/index.html — it's the
        # listing page itself, already linked from footer + nav and added
        # explicitly below.
        _collection_umbrella = {"index.html"}
        for coll_dir in sorted(collections_root.iterdir()):
            if coll_dir.is_dir() and (coll_dir / "index.html").exists():
                urls.append(
                    (f"{SITEMAP_BASE}/collections/{coll_dir.name}/", today)
                )
        # Also include the umbrella /collections/ itself.
        if (collections_root / "index.html").exists():
            urls.append((f"{SITEMAP_BASE}/collections/", today))

    url_blocks = "\n".join(
        f"    <url>\n      <loc>{loc}</loc>\n      <lastmod>{lastmod}</lastmod>\n    </url>"
        for loc, lastmod in urls
    )

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{url_blocks}
</urlset>
"""


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    print("Building Bithues site...")

    # ── Best-of roundup pages (run first so they exist before sitemap gen) ─────
    try:
        import gen_best_pages
        n_best = gen_best_pages.generate_all()
        print(f"  Generated {n_best} best-of roundup pages")
    except Exception as e:
        print(f"  WARNING: best-of page generation failed: {e}")

    stories = load_all_stories()
    print(f"  Loaded {len(stories)} stories")

    # Sort: by date descending, then featured first (stable sort = two passes)
    stories.sort(key=lambda s: _parse_sort_date(s[1].get("date") or ""), reverse=True)
    stories.sort(key=lambda s: not s[1].get("featured", False))

    articles = load_md_dir(ARTICLES_DIR)
    articles.sort(key=lambda a: _parse_sort_date(a[1].get("date") or ""), reverse=True)
    print(f"  Loaded {len(articles)} articles")

    reviews = load_md_dir(REVIEWS_DIR)
    reviews.sort(key=lambda r: _parse_sort_date(r[1].get("date") or ""), reverse=True)
    print(f"  Loaded {len(reviews)} reviews")

    newsletters = load_md_dir(NEWSLETTERS_DIR) if NEWSLETTERS_DIR.exists() else []
    newsletters.sort(key=lambda n: _parse_sort_date(n[1].get("date") or ""), reverse=True)
    print(f"  Loaded {len(newsletters)} newsletters")

    # ── index.html ───────────────────────────────────────────────────────────
    index_html = generate_index(stories)
    (OUTPUT_DIR / "index.html").write_text(index_html, encoding="utf-8")
    print("  Wrote index.html")

    # ── stories.html ─────────────────────────────────────────────────────────
    stories_html = generate_stories_page(stories, 1)
    stories_dir = OUTPUT_DIR / "stories"
    stories_dir.mkdir(exist_ok=True)
    (stories_dir / "index.html").write_text(stories_html, encoding="utf-8")
    print("  Wrote stories.html")

    # ── Stories listing (single page — pagination removed 2026-06-01) ─────────
    stories_html = generate_stories_page(stories, 1)
    (OUTPUT_DIR / "stories/index.html").write_text(stories_html, encoding="utf-8")
    print("  Wrote stories/index.html")

    # ── Individual story pages (with page-turn for long stories) ─────────────
    for i, (slug, meta, body) in enumerate(stories):
        prev_s = stories[i - 1][0] if i > 0 else None
        prev_t = stories[i - 1][1].get("title", prev_s) if i > 0 else ""
        next_s = stories[i + 1][0] if i < len(stories) - 1 else None
        next_t = stories[i + 1][1].get("title", next_s) if i < len(stories) - 1 else ""

        wc = story_word_count(body)
        chapters_meta = meta.get("chapters")
        has_chapters = bool(chapters_meta) and (chapters_meta == True or isinstance(chapters_meta, list))

        if has_chapters:
            page_html = generate_story_page_chapters(
                slug, meta, body,
                prev_s, prev_t, next_s, next_t,
            )
            slug_dir = OUTPUT_DIR / slug
            slug_dir.mkdir(exist_ok=True)
            (slug_dir / "index.html").write_text(page_html, encoding="utf-8")
            print(f"  Wrote {slug}/ (chapter cards, {wc} words)")
        else:
            page_html = generate_story_page(
                slug, meta, body,
                prev_s, prev_t, next_s, next_t,
                1, 1,
            )
            slug_dir = OUTPUT_DIR / slug
            slug_dir.mkdir(exist_ok=True)
            (slug_dir / "index.html").write_text(page_html, encoding="utf-8")
            print(f"  Wrote {slug}/ (single page, {wc} words)")

    # ── Article listing page ──────────────────────────────────────────────────
    articles_dir = OUTPUT_DIR / "articles"
    articles_dir.mkdir(exist_ok=True)
    (articles_dir / "index.html").write_text(
        generate_articles_listing(articles, 1), encoding="utf-8")
    print("  Wrote articles/index.html")
    # ── Individual article pages ─────────────────────────────────────────────
    for i, (slug, meta, body) in enumerate(articles):
        prev_s = articles[i - 1][0] if i > 0 else None
        prev_t = articles[i - 1][1].get("title", prev_s) if i > 0 else ""
        next_s = articles[i + 1][0] if i < len(articles) - 1 else None
        next_t = articles[i + 1][1].get("title", next_s) if i < len(articles) - 1 else ""

        page_html = generate_article_page(slug, meta, body, prev_s, prev_t, next_s, next_t)
        slug_dir = OUTPUT_DIR / "articles" / slug
        slug_dir.mkdir(exist_ok=True)
        (slug_dir / "index.html").write_text(page_html, encoding="utf-8")

    print(f"  Wrote {len(articles)} article pages")

    # ── Review listing page ──────────────────────────────────────────────────
    reviews_dir = OUTPUT_DIR / "reviews"
    reviews_dir.mkdir(exist_ok=True)
    (reviews_dir / "index.html").write_text(
        generate_reviews_listing(reviews, 1), encoding="utf-8")
    print("  Wrote reviews/index.html")
    # Paginated review listing pages
    reviews_sorted_all = sorted(reviews, key=lambda r: _parse_sort_date(r[1].get("date") or ""), reverse=True)
    all_review_pages = paginate(reviews_sorted_all, REVIEWS_PAGINATE)
    for page_num, _ in enumerate(all_review_pages, start=1):
        page_slug = f"reviews/{page_num}/index.html" if page_num > 1 else "reviews/index.html"
        page_html = generate_reviews_listing(reviews, page_num)
        if page_num > 1:
            pg_dir = OUTPUT_DIR / f"reviews/{page_num}"
            pg_dir.mkdir(exist_ok=True)
            (pg_dir / "index.html").write_text(page_html, encoding="utf-8")
        else:
            (OUTPUT_DIR / "reviews/index.html").write_text(page_html, encoding="utf-8")
        print(f"  Wrote {page_slug}")

    # ── Individual review pages ──────────────────────────────────────────────
    for i, (slug, meta, body) in enumerate(reviews):
        prev_s = reviews[i - 1][0] if i > 0 else None
        prev_t = reviews[i - 1][1].get("title", prev_s) if i > 0 else ""
        next_s = reviews[i + 1][0] if i < len(reviews) - 1 else None
        next_t = reviews[i + 1][1].get("title", next_s) if i < len(reviews) - 1 else ""

        page_html = generate_review_page(slug, meta, body, prev_s, prev_t, next_s, next_t)
        slug_dir = OUTPUT_DIR / "reviews" / slug
        slug_dir.mkdir(exist_ok=True)
        (slug_dir / "index.html").write_text(page_html, encoding="utf-8")

    print(f"  Wrote {len(reviews)} review pages")

    # ── Newsletter listing page ────────────────────────────────────────────
    newsletters_dir = OUTPUT_DIR / "newsletters"
    newsletters_dir.mkdir(exist_ok=True)
    (newsletters_dir / "index.html").write_text(
        generate_newsletters_listing(newsletters), encoding="utf-8")
    print("  Wrote newsletters/index.html")

    # ── Individual newsletter pages ───────────────────────────────────────
    for slug, meta, body in newsletters:
        if slug == "index":
            continue
        page_html = generate_newsletter_page(slug, meta, body)
        slug_dir = OUTPUT_DIR / "newsletters" / slug
        slug_dir.mkdir(exist_ok=True)
        (slug_dir / "index.html").write_text(page_html, encoding="utf-8")
    if newsletters:
        print(f"  Wrote {len([n for n in newsletters if n[0] != 'index'])} newsletter pages")

    # ── About, Contact, Legal ─────────────────────────────────────────────────
    (OUTPUT_DIR / "about").mkdir(exist_ok=True)
    (OUTPUT_DIR / "about/index.html").write_text(generate_about(), encoding="utf-8")
    (OUTPUT_DIR / "contact").mkdir(exist_ok=True)
    (OUTPUT_DIR / "contact/index.html").write_text(generate_contact(), encoding="utf-8")
    (OUTPUT_DIR / "privacy").mkdir(exist_ok=True)
    (OUTPUT_DIR / "privacy/index.html").write_text(generate_legal("privacy"), encoding="utf-8")
    (OUTPUT_DIR / "terms").mkdir(exist_ok=True)
    (OUTPUT_DIR / "terms/index.html").write_text(generate_legal("terms"), encoding="utf-8")
    print("  Wrote static pages (about, contact, privacy, terms)")

    # ── Reading Maps ─────────────────────────────────────────────────────────
    rm_html = generate_reading_maps()
    if rm_html:
        rm_dir = OUTPUT_DIR / "reading-maps"
        rm_dir.mkdir(exist_ok=True)
        (rm_dir / "index.html").write_text(rm_html, encoding="utf-8")
        print("  Wrote reading-maps/index.html")

    # ── Sitemap ───────────────────────────────────────────────────────────────
    sitemap_xml = generate_sitemap(stories, articles, reviews, newsletters)
    (OUTPUT_DIR / "sitemap.xml").write_text(sitemap_xml, encoding="utf-8")
    print("  Wrote sitemap.xml")

    # ── Sync critical static assets to website/ ─────────────────────────────
    # website/ is the deploy target git repo. style.css lives there separately
    # and must stay in sync with bithues-may24/style.css — drift causes broken pages.
    WEBSITE_DIR = Path(__file__).parent.parent / "website"
    if WEBSITE_DIR.exists():
        src_css = Path(__file__).parent / "style.css"
        dst_css = WEBSITE_DIR / "style.css"
        if src_css.exists() and dst_css.exists():
            src_txt = src_css.read_text(encoding="utf-8")
            dst_txt = dst_css.read_text(encoding="utf-8")
            if src_txt != dst_txt:
                shutil.copy2(src_css, dst_css)
                print(f"  Synced style.css → website/")

    print("Done.")


if __name__ == "__main__":
    main()