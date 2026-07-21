#!/usr/bin/env python3
"""
Cleanup orphan .html files from the website/ directory.

Orphan .html = a file like /about.html where /about/ directory also exists.
These are leftover from older build processes and cause Google to find
duplicate content (both the .html file AND the clean URL exist).

For CF Pages, clean URLs (/about/) serve from directories, so .html files
at the same path are always redundant.
"""
import os
from pathlib import Path

WEBSITE = Path(__file__).parent / "website"
DELETED = []

def is_orphan(html_path: Path) -> bool:
    """Check if html file has a corresponding directory (clean URL takes precedence)."""
    rel = html_path.relative_to(WEBSITE)
    name_without_ext = rel.stem  # "about" from "about.html"
    parent = rel.parent  # Path to parent dir
    
    # Build the clean URL path: parent / name_without_ext
    clean_path = WEBSITE / parent / name_without_ext
    
    # If a directory exists at the clean path, this .html is an orphan
    if clean_path.is_dir():
        return True
    
    # Also orphan if it's in a subdirectory AND the same-named file exists in parent
    # e.g., /stories/about.html where /about.html also exists at root
    if parent != Path("."):
        root_file = WEBSITE / name_without_ext
        if root_file.suffix == ".html":
            return True
    
    return False

def main():
    os.chdir(WEBSITE)
    html_files = list(WEBSITE.rglob("*.html"))
    print(f"Scanning {len(html_files)} .html files in {WEBSITE}")
    
    orphans = []
    for f in html_files:
        if is_orphan(f):
            orphans.append(f)
    
    print(f"\nFound {len(orphans)} orphan .html files:")
    for f in orphans:
        rel = f.relative_to(WEBSITE)
        print(f"  DELETE: {rel}")
    
    confirm = input(f"\nDelete {len(orphans)} files? [y/N] ")
    if confirm.lower() != 'y':
        print("Aborted.")
        return
    
    for f in orphans:
        f.unlink()
        DELETED.append(str(f.relative_to(WEBSITE)))
    
    print(f"\nDeleted {len(DELETED)} files.")
    
    # Report what remains
    remaining = list(WEBSITE.rglob("*.html"))
    print(f"Remaining .html files: {len(remaining)}")

if __name__ == "__main__":
    main()
