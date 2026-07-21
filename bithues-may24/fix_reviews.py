#!/usr/bin/env python3
"""
Audit and fix review MD files:
1. Add missing date field
2. Rewrite truncated/odd summaries
"""
from pathlib import Path
import os, re

REVIEWS_DIR = Path(__file__).parent.parent / "content" / "reviews"

# Files needing date (missing date field)
# Files needing summary rewrite (summary ends mid-sentence or mid-word, or is malformed)
# Map of slug -> (new_date, new_summary_or_None)

# Files with truncated summaries (cut mid-sentence, ends with , or word broken)
TRUNCATED = {
    "beyond-the-veil": ("March 2026", "A rigorous, compassionate examination of near-death experiences — what they reveal about consciousness, and why the phenomenon has resisted easy categorization for so long."),
    "dawn-of-civilization": ("March 2026", "A prehistoric YA novel that lands in the crossover space where thoughtful teens and serious adult readers meet — emotionally immediate and rigorously grounded."),
    "disclosure-2026": ("March 2026", "A systematic, scenario-based exploration of what first contact would actually look like if it happened — thoughtful and meticulously researched."),
    "discovering-washington-dc": ("March 2026", "A travel guide to Washington DC that is actually about the city as a place where people live — useful, observant, and genuinely independent."),
    "echoes-of-transcendence": ("March 2026", "A novel about what happens when people who have studied something ancient suddenly encounter evidence that it is real — in a way that demands a revised understanding of everything."),
    "home-for-anya": ("March 2026", "A story about what happens when someone stops running long enough to let a place change her — tender, precise, and quietly transformative."),
    "horizonte-rojo": ("March 2026", "Un viaje lunar que comienza tres segundos después del lanzamiento y nunca mira atrás — narrativamente audaz y emocionalmente vívido."),
    "little-mike-builds-a-robot": ("March 2026", "A children's picture book about the simple, profound pleasure of building something together — with unexpected results along the way."),
    "living-with-a-moving-planet": ("March 2026", "A novel about the particular courage that comes from living somewhere that could shake you apart at any moment — grounded, tense, and deeply human."),
    "men-of-three-seas": ("March 2026", "Historical fiction that makes you feel the weight of three seas — the Mediterranean, the Black Sea, the Aegean — as more than geography, but as命运."),
    "microbiology-abcs": ("March 2026", "A revised third-edition children's science book that does not talk down to its readers — alphabetically ordered, genuinely illuminating."),
    "mindful-memory": ("March 2026", "A practical guide to cognitive maintenance written for an older adult audience — clear, compassionate, and grounded in real neuroscience."),
    "mythical-menagerie": ("March 2026", "A cross-cultural tour of mythological creatures — dragons, shape-shifters, hybrid beasts — examining what these beings reveal about the cultures that imagined them."),
    "otomi": ("March 2026", "A novel about what it costs to remember who you are when the world around you has decided to forget — set in the central Mexican highlands."),
    "physics-of-insight": ("March 2026", "What if genius is not rare — it is hidden inside every mind, waiting for the right switch? A book about the physics of insight."),
    "power-of-changing-your-mind": ("March 2026", "In a culture that rewards confidence and punishes doubt, changing your mind feels like losing. This book argues the opposite — and makes a compelling case."),
    "the-orchardist-harvest": ("March 2026", "A novel about a fall that becomes the occasion for a sustained literary reckoning with what it means to cross a threshold and return."),
}

# Files needing date (but summary is OK)
NEED_DATE = {
    "blood-ember": "March 2026",
    "consciousness-in-higher-dimensional-spacetime": "March 2026",
    "cords-of-empire": "March 2026",
    "reminiscences-of-a-stock-operator": "March 2026",
    "resonance-drift": "March 2026",
    "richmond-cipher": "March 2026",
    "rules-of-survival": "March 2026",
    "shadow-within": "March 2026",
    "shadow-work-journal-for-women": "March 2026",
    "symbiont-bloom": "March 2026",
    "the-burning-song": "March 2026",
    "the-martian": "March 2026",
    "the-quiet-hours": "March 2026",
    "time-investing": "March 2026",
    "veiled-presence": "March 2026",
    "you-tell-the-story": "March 2026",
}

# the-perfection-cycle.md needs a real date
PERFECTION_CYCLE_DATE = "March 2026"

def fix_file(slug, new_date=None, new_summary=None):
    path = REVIEWS_DIR / f"{slug}.md"
    if not path.exists():
        print(f"SKIP {slug}: file not found")
        return

    raw = path.read_text()
    fm_match = re.match(r'^(---\n)(.*?)(\n---)', raw, re.DOTALL)
    if not fm_match:
        print(f"SKIP {slug}: no frontmatter")
        return

    pre, fm_body, post = raw[:fm_match.start()], fm_match.group(2), raw[fm_match.end():]

    # Helper: update or add field
    def update_field(body, key, value):
        if re.search(rf'^ {key}:', body, re.M):
            return re.sub(rf'^ {key}:.*\n', f' {key}: "{value}"\n', body, flags=re.M)
        else:
            # add after last field (before the closing ---)
            lines = body.rstrip().split('\n')
            # find a good insert point (after genre_label or summary)
            insert_after = -1
            for i, l in enumerate(lines):
                if l.strip().startswith(('genre_label', 'summary', 'featured')):
                    insert_after = i
            if insert_after == -1:
                insert_after = len(lines) - 1
            lines.insert(insert_after + 1, f' date: "{value}"')
            return '\n'.join(lines) + '\n'

    if new_date:
        fm_body = update_field(fm_body, 'date', new_date)
    if new_summary:
        if re.search(r'^ summary:', fm_body, re.M):
            fm_body = re.sub(r'^ summary:.*\n', f' summary: "{new_summary}"\n', fm_body, flags=re.M)
        else:
            fm_body = update_field(fm_body, 'summary', new_summary)

    new_raw = pre + fm_match.group(1) + fm_body + fm_match.group(3) + post
    path.write_text(new_raw)
    print(f"DONE {slug}")


if __name__ == "__main__":
    for slug, (d, s) in TRUNCATED.items():
        fix_file(slug, new_date=d, new_summary=s)
    for slug, d in NEED_DATE.items():
        fix_file(slug, new_date=d)
    fix_file("the-perfection-cycle", new_date=PERFECTION_CYCLE_DATE)