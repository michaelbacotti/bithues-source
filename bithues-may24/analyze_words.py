#!/usr/bin/env python3
"""Analyze story lengths for pagination planning."""

import re
from pathlib import Path

STORIES_DIR = Path(__file__).parent.parent / "content" / "stories"

def parse_front_matter(content: str) -> tuple[dict, str]:
    if not content.startswith("---"):
        return {}, content
    end = content.find("\n---", 4)
    if end == -1:
        return {}, content
    body = content[end + 4:].lstrip("\n")
    return {}, body

def count_words(text: str) -> int:
    # Strip front matter if present
    meta, body = parse_front_matter(text)
    return len(body.split())

stories = []
for md_path in sorted(STORIES_DIR.glob("*.md")):
    content = md_path.read_text(encoding="utf-8")
    word_count = count_words(content)
    stories.append((md_path.stem, word_count))

stories.sort(key=lambda x: -x[1])

print(f"{'Story':<45} {'Words':>6}")
print("-" * 52)
for slug, wc in stories:
    print(f"{slug:<45} {wc:>6}")

print()
print(f"Total stories: {len(stories)}")
print()

# Pagination analysis: chunk threshold of 2000 words, ~1500 words per page
THRESHOLD = 2000
CHUNK_SIZE = 1500

print("=== PAGINATION ANALYSIS ===")
print(f"Threshold: {THRESHOLD}+ words → paginated")
print(f"Chunk size: ~{CHUNK_SIZE} words per page")
print()

total_pages_needed = 0
paginated_stories = []
for slug, wc in stories:
    if wc >= THRESHOLD:
        pages = max(1, (wc + CHUNK_SIZE - 1) // CHUNK_SIZE)
        total_pages_needed += pages
        paginated_stories.append((slug, wc, pages))
        print(f"  {slug:<45} {wc:>5} words → {pages} page(s)")

print()
print(f"Stories needing pagination: {len(paginated_stories)}")
print(f"Total story pages (incl. short stories): {len(stories) + total_pages_needed - len(paginated_stories)}")
print(f"Short stories (< {THRESHOLD} words): {len(stories) - len(paginated_stories)}")