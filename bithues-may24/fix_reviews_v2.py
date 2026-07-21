#!/usr/bin/env python3
"""Fix all review MD files: proper frontmatter, clean summaries, consistent fields."""
from pathlib import Path
import re

REVIEWS = Path(__file__).parent.parent / "content" / "reviews"

# All files and their desired date + summary
FIXES = {
    # (slug): (date, summary)
    "american-journeys":      ("March 2026", None),  # keep existing summary
    "beyond-the-veil":        ("March 2026", "A rigorous, compassionate examination of near-death experiences — what they reveal about consciousness, and why the phenomenon has resisted easy categorization for so long."),
    "blood-ember":             ("March 2026", None),  # keep existing
    "consciousness-in-higher-dimensional-spacetime": ("March 2026", None),
    "cords-of-empire":        ("March 2026", None),
    "dawn-of-civilization":   ("March 2026", "A prehistoric YA novel that lands in the crossover space where thoughtful teens and serious adult readers meet — emotionally immediate and rigorously grounded."),
    "disclosure-2026":        ("March 2026", "A systematic, scenario-based exploration of what first contact would actually look like if it happened — meticulous and thought-provoking."),
    "discovering-washington-dc": ("March 2026", "A travel guide to Washington DC that is actually about the city as a place where people live — useful, observant, and genuinely independent."),
    "echoes-of-transcendence": ("March 2026", "A novel about what happens when people who have studied something ancient suddenly encounter evidence that it is real — demanding a complete revision of how the world works."),
    "home-for-anya":          ("March 2026", "A story about what happens when someone stops running long enough to let a place change her — tender, precise, and quietly transformative."),
    "horizonte-rojo":          ("March 2026", "Un viaje lunar que comienza tres segundos después del lanzamiento y nunca mira atrás — narrativamente audaz y emocionalmente vívido."),
    "little-mike-builds-a-robot": ("March 2026", "A children's picture book about the simple, profound pleasure of building something together — with unexpected results along the way."),
    "little-mike-fun-at-the-beach": ("March 2026", None),  # keep
    "little-mike-learns-to-fly": ("March 2026", None),  # keep
    "living-with-a-moving-planet": ("March 2026", "A novel about the courage that comes from living somewhere that could shake you apart at any moment — grounded, tense, and deeply human."),
    "men-of-three-seas":       ("March 2026", None),  # keep
    "microbiology-abcs":       ("March 2026", None),
    "mindful-memory":          ("March 2026", None),
    "mythical-menagerie":      ("March 2026", None),
    "otomi":                   ("March 2026", None),
    "physics-of-insight":      ("March 2026", None),
    "power-of-changing-your-mind": ("March 2026", "In a culture that rewards confidence and punishes doubt, changing your mind feels like losing. This book argues the opposite — and makes a compelling case."),
    "reminiscences-of-a-stock-operator": ("March 2026", None),
    "resonance-drift":         ("March 2026", None),
    "richmond-cipher":         ("March 2026", None),
    "rules-of-survival":       ("March 2026", None),
    "shadow-within":           ("March 2026", None),
    "shadow-work-journal-for-women": ("March 2026", None),
    "symbiont-bloom":          ("March 2026", None),
    "the-burning-song":        ("March 2026", None),
    "the-martian":             ("March 2026", None),
    "the-orchardist-harvest":  ("March 2026", None),
    "the-perfection-cycle":    ("March 2026", "A book about the pursuit of perfection — and what gets lost when the process becomes the point."),
    "the-physics-of-time":     ("March 2026", None),
    "the-quiet-hours":         ("March 2026", None),
    "time-investing":          ("March 2026", None),
    "veiled-presence":         ("March 2026", None),
    "you-tell-the-story":      ("March 2026", None),
    "red-horizon":             ("March 2026", None),
}

def fix_file(slug, new_date=None, new_summary=None):
    path = REVIEWS / f"{slug}.md"
    if not path.exists():
        print(f"SKIP {slug}: not found")
        return
    raw = path.read_text()
    fm_match = re.match(r'^---\n(.*?)\n---\n', raw, re.DOTALL)
    if not fm_match:
        print(f"SKIP {slug}: no frontmatter")
        return
    # Parse YAML frontmatter
    fm_lines = fm_match.group(1).split('\n')
    data = {}
    for line in fm_lines:
        m = re.match(r'^(\w+):\s*(.*)$', line)
        if m:
            data[m.group(1)] = m.group(2).strip().strip('"')
    # Update date
    if new_date:
        data['date'] = new_date
    # Update summary
    if new_summary:
        data['summary'] = new_summary
    # Rewrite frontmatter
    new_fm_lines = []
    for key in ['title','author','date','section','type_label','cover_image','amazon_asin','card_image','genre_label','summary','featured','draft']:
        if key in data:
            val = data[key]
            if val:
                new_fm_lines.append(f'{key}: "{val}"')
    new_fm = '\n'.join(new_fm_lines) + '\n'
    new_raw = '---\n' + new_fm + '---\n' + raw[fm_match.end():]
    path.write_text(new_raw)
    print(f"DONE {slug} (date={data.get('date','?')[:20]})")

for slug, (d, s) in FIXES.items():
    fix_file(slug, new_date=d, new_summary=s)
print("All done.")