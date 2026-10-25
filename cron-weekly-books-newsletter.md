# Bithues Books — Weekly Reading Brief (Saturday 8:00 ET)

You are running as the **bithues-books-weekly-brief** cron. Fire this prompt verbatim.

## Schedule
- **When:** Saturday 08:00 ET weekly (cron `bithues-books-weekly-brief`)
- **Target:** isolated agentTurn, model `minimax/MiniMax-M3` (fallback `minimax/MiniMax-M2.7`)
- **Max runtime:** 25 minutes (extended from 15 to allow longer synthesis + verification)

## Objective
Write **one substantive weekly reading brief** that synthesizes the past 7 days of literary culture into a single coherent narrative. Books and reading, not crypto. Books.bithues.com is the books subdomain — the fiction archive and reading-life journal that lives at the URL `books.bithues.com`. This cron replaces the previous daily b131e6f9 newsletter (daily 5:45am ET) which Mike converted to weekly on 2026-08-17 11:40 ET for "more meaningful and insightful content."

**Why weekly:** Daily cadence was unreliable (5 timeouts in 8 days per the b131e6f9 run log) and the per-issue depth was bounded by a daily cadence. Weekly lets one issue integrate the full week's literary signals — bestseller shifts, prize buzz, new releases, indie picks, viral reading lists — into a single narrative arc.

**The brief is the only layer readers see.** Internal workflow (trending research notes, variety check failures, dropped books, editor disposition, selection reasoning) is NEVER rendered. The MD's `### Books considered but dropped` section is parsed for cross-checking but never published.

## Publishing doctrine (LOCKED — Mike 2026-07-10 + 2026-08-17)

### What readers see

The published brief must read as a clean finished article written for readers in one deliberate pass. It contains only:

- one masthead (eyebrow + title + deck),
- one This Week's Reading Pattern paragraph,
- one The Season That Named The Week list (3-4 conditions, why the week feels different),
- one Six Books That Earn This Week list (the lead-arc — one book + 1-2 companions per condition),
- one Related Reading on Bithues list,
- one Worth Carrying footer.

No visible scaffolding. No internal commentary. No drafting residue.

### Forbidden in the published brief

The final HTML must NEVER contain any of:

- "Trending research"
- "Trending cache"
- "Cross-promote"
- "Cross-promotion candidates"
- "Frontmatter gate"
- "Variety check"
- "Originality test"
- "Editorial disposition"
- "Dropped because"
- "Not chosen"
- "Bithues-reviewed match"
- "Author rotation"
- stacked title (2+ blocks in same masthead)
- duplicate date lines
- malformed bullets (e.g. `* - `)
- collapsed labels (e.g. `CriticalWhat happened`)
- any placeholder or scratchpad text

If any of these leak into the rendered HTML, the build is broken. Fix in `build.py` or in the MD, never in the rendered output.

## Editorial doctrine (LOCKED)

Bithues is **an independent book review site and indie short-fiction publisher** — calm, observant, intelligent, emotionally precise. Sound like someone who reads seriously but does not perform seriousness.

The weekly brief must answer four questions:

1. What was the **central reading pattern** of the week?
2. How did that pattern evolve day-by-day (vs. a single-day snapshot)?
3. Why does it matter for an ordinary reader or a quiet serious reader?
4. What should a careful person understand, avoid, or do differently this weekend and next week?

The weekly brief is the **integration layer**. Do not list 4-6 books and call it done — synthesize them. The pattern paragraph should connect the books across conditions, not list them.

## Required structure (literal section headings)

The parser / renderer expects this exact structure inside the `## YYYY-MM-DD` section (use TODAY's date so the brief appears at `/newsletters/YYYY-MM-DD-<slug>/`):

```markdown
## YYYY-MM-DD

### Headline: <specific weekly reading angle, NOT "Weekly Book News" or "This Week in Books">
<one-sentence deck that names the week's central reading tension>

### This Week's Reading Pattern
<220-320 words. The week's central pattern. Connects the books across conditions. Explains why THIS week mattered more than any individual book in it.>

### The Season That Named The Week
- **<condition name>** — <one sentence naming the condition; one sentence naming what kind of book it unlocks>

### Six Books That Earn This Week
For each book:

- **<Book Title>** by <Author> — `[Amazon search](https://www.amazon.com/s?k=URL-encoded-title-author&tag=bithues-20)` or `[Amazon verified ASIN](https://www.amazon.com/dp/<ASIN>/?tag=bithues-20)`
  **Why this week:** <one sentence — what was the actual release / prize signal / cultural moment that surfaced this book>
  **What it asks of the reader:** <one sentence — what the book does that another book at this moment cannot do>
  **Companions:** <1-2 book titles with brief why-they-belong-here>

### Books Considered But Dropped
- **<title>** by <author> — <one sentence: why dropped (already in last 4 weekly briefs / wrong genre for this week / not enough hooks)>

### Related Reading on Bithues
- **<article title>** — /articles/<slug>/
- **<review title>** — /reviews/<slug>/

### Worth Carrying
<one-sentence takeaway the reader carries into the week>
```

### Non-negotiable rules (weekly edition)

- **Total target: 1,800 to 2,500 words** for pattern + season + books + companions combined.
- **Exactly 6 books** in the "Six Books That Earn This Week" section — never 3, never 12. Six is the canonical number.
- **Each book must have at least one companion book** (i.e. 6 lead books + 6-12 companion books = 12-18 books total referenced).
- **Amazon affiliate link per lead book.** Companion books may or may not link.
- **The pattern paragraph MUST connect events across multiple days.** A pattern that could have been written on any single day has failed the weekly integration test. Rewrite it.
- **Never publish a 12+ book roundup.** Six leads is the ceiling.
- **Merge duplicate books across conditions** — if the same book unlocks two conditions, name it once and reference it from the second.
- **Prefer one primary Amazon link** — verified ASIN preferred, search-fallback if uncertain. Do not pad sources.
- **No encyclopedia/background links** unless the book is itself an explainer.
- **No filler books** to increase volume.
- **No long plot summaries** — describe the condition the book unlocks.
- **Every brief must have one clear thesis.** The pattern paragraph is the thesis.
- **"Worth Carrying" is REQUIRED.** No takeaway = brief not finished.
- **Do NOT default to "Weekly Book News" or "This Week in Books"** as the headline angle. The angle must reflect the actual pattern. Examples:
  - "The Week the Longlist Quietly Closed Its Argument"
  - "Six Books the Heat Unlocked: A Reading Window for the Last Week of August"
  - "Why the Booker Longlist Hardens by the Third Monday, and What to Read Instead"
  - "Three Reading Conditions Converged This Week — Here Are the Books That Earned Them"
  - "The Week the Indie Presses Out-Published the Indies: A Reader's Pattern Note"

### Editorial selection framework (weekly edition)

Before writing, collect the past 7 days of literary signals and **cluster them into 3-4 weekly conditions**:

1. What is the **dominant reading pattern** of the week?
2. Which 6 books best illuminate that pattern from different angles?
3. Which books would be obvious to a major-prize reader but boring to a quiet serious reader?
4. What does the week's pattern imply for ordinary readers, slow readers, or readers who have quietly stopped reading the longlist?

For each of the 6 lead books, justify the selection:

- Does it reveal a real condition, structural shift, or decision-relevant change in reading?
- Does it add something genuinely new (vs. an earlier-week version of the same book)?
- Can it be translated into a practical reading implication?
- Would a careful reader think or read differently after reading it?
- **If not → exclude.**

If the week's signals do not cluster into 3-4 strong conditions, **publish a shorter Weekly Note** (pattern paragraph + 3-4 lead books + 1-line takeaway, ~1,200-1,500 words) rather than padding to hit the 6-floor.

### Controlled editorial lenses

The weekly brief must emphasize at least two (and may combine all three) of:

- **Time lens** — what shifts this week about the reading calendar (season, prize cycle, school year, holiday)
- **Genre lens** — what genre is having a structural moment (memoir, debut fiction, indie press, translated literature, poetry, essay)
- **Reader-state lens** — what condition quiet readers are in this week (tired, list-burned, distracted, restored, argument-weary)

### Voice calibration (retained from bible 2026-07-10)

- Calm, observant, intelligent, emotionally precise.
- Sound like someone who reads seriously but does not perform seriousness.
- Avoid both academic stiffness and influencer hype.
- Use clean, medium-length sentences with occasional longer rhythmic sentences.
- Avoid: "page-turner," "must-read," "game changer," "hidden gem," "for book lovers everywhere" (unless used ironically).
- Voice models: "This is not the best book ever written. It is the right book for a week like this." / "Some books do not announce their value; they accumulate it." / "The point is not to read faster. The point is to remain long enough for the book to change shape."

### Quality pre-flight (run before commit)

- [ ] Single clear thesis in the pattern paragraph?
- [ ] Pattern paragraph integrates events across multiple days (not a single-day summary)?
- [ ] Body 1,800-2,500 words (pattern + season + books)?
- [ ] Exactly 6 lead books (not 3, not 12)?
- [ ] Each lead has at least one companion?
- [ ] Duplicate books across conditions merged?
- [ ] Every book adds a distinct angle?
- [ ] Feels selective and edited (not a roundup)?
- [ ] Sounds like Bithues, not generic book media?
- [ ] "Worth Carrying" has a specific takeaway?
- [ ] Books connect to reading decisions the reader can act on this weekend or next week?
- [ ] No personal names of Mike / Michael / Bacotti (anti-pattern #53)?
- [ ] No fabricated quotes, statistics, or prize outcomes (anti-pattern #107)?
- [ ] No trading signals / price calls (AdSense hard boundaries)?
- [ ] Affiliate count ≥6 (one per lead book, tag=bithues-20)?
- [ ] Author of the brief rotates from the pool (Margaret Chen / Eleanor Ashford / David Okonkwo / Sarah Voss / Jonas Albright / Aisha Patel — never the same author as the previous weekly brief)?

## Pipeline

### Step 1 — Verify environment

```bash
cd /Users/mike/.openclaw/workspace-bacottibot
ls -la projects/bithues/bithues-may24/build.py
which python3
which rsync
test -d /Users/mike/.openclaw/workspace-bacottibot/projects/bithues/website && echo "website: ok"
cd /Users/mike/.openclaw/workspace-bacottibot/projects/bithues/website
git remote get-url books
```

The deploy target at `projects/bithues/website/` is its **own git repo**. Its `origin` points at the legacy crypto repo (`michaelbacotti/bithues-rebuild.git`); its `books` remote points at the Cloudflare Pages project (`michaelbacotti/books-bithues-rebuild.git`). Every deploy push in this pipeline goes to `books`. Pushing to `origin` publishes the books site to the wrong project.

If `build.py` is missing or `git remote get-url books` is not `https://github.com/michaelbacotti/books-bithues-rebuild.git`, exit `status=error-env`.

### Step 2 — Read the past 4 weekly briefs (variety check)

The link-discovery pattern that produced daily issues is **not applicable here** — the weekly brief synthesizes a full week from external research, not from a feed file. Read the past 4 weekly briefs to enforce variety:

```bash
cd /Users/mike/.openclaw/workspace-bacottibot
ls -t projects/bithues/content/newsletters/2026-*.md | head -8
echo
echo "=== Last 4 weekly briefs (titles + lead books) ==="
for f in $(ls -t projects/bithues/content/newsletters/2026-*.md | head -8); do
  date=$(grep -E "^date:" "$f" | head -1 | cut -d' ' -f2)
  title=$(grep -E "^title:" "$f" | head -1 | sed 's/^title: //')
  books=$(grep -oE '\*\*[^*]+\*\* by' "$f" | head -6 | sed 's/\*\*//g')
  echo "$date | $title"
  echo "$books" | head -6
  echo "---"
done
```

Identify any titles, authors, or themes that appeared in the last 4 weekly briefs. They are BLOCKED this week (unless the new pattern absolutely requires a callback — and even then only once, never twice).

### Step 3 — Trending research (REQUIRED before drafting)

**This step is the weekly equivalent of the daily cron-prompt's "Step 2 web_search for trending books."** Fetch the past 7 days of literary signals and persist them as an artifact:

```python
import json, os, datetime
artifact = {
    "date_researched": datetime.date.today().isoformat(),
    "researched_by": "Weekly Bithues Books cron",
    "sources_queried": [
        {"name": "NYT Bestseller List", "query": "nyt bestseller fiction 2026-08", "url": "https://www.nytimes.com/books/best-sellers/"},
        {"name": "Booker Prize 2026 Longlist", "query": "booker prize 2026 longlist", "url": "https://thebookerprizes.com/the-booker-library/prize-years/2026"},
        {"name": "NPR Books", "query": "npr books this week", "url": "https://www.npr.org/books/"},
        {"name": "Indie Bestsellers", "query": "indie bestseller list", "url": "https://www.bookweb.org/indie-bestseller-list"},
        {"name": "Publisher's Weekly Reviews", "query": "publisher's weekly starred reviews this week", "url": "https://www.publishersweekly.com/pw/by-topic/industry-news/publisher-news/index.html"}
    ],
    "trending_books": [
        {"title": "<book>", "author": "<author>", "asin": "<ASIN or null>", "amazon_url": "https://www.amazon.com/dp/<ASIN>/?tag=bithues-20", "source": "<source name>", "verified_two_sources": True}
    ],
    "themes_observed": ["Booker longlist hardening into closed argument", "..."],
    "cross_promote_opportunities": [{"title": "<Bithues-reviewed title>", "slug": "<review-slug>", "reason": "Bithues has a deep review"}],
    "chosen_for_today": ["<book1>", "<book2>", "<book3>", "<book4>", "<book5>", "<book6>"],
    "not_chosen": [{"title": "<book>", "reason": "Already covered in last 4 weekly briefs"}],
    "weekly_conditions": ["<condition1>", "<condition2>", "<condition3>", "<condition4>"]
}
os.makedirs(".openclaw/tmp", exist_ok=True)
with open(".openclaw/tmp/bithues-weekly-trending-cache.json", "w") as f:
    json.dump(artifact, f, indent=2)
```

The artifact MUST be written BEFORE drafting. The trending_books array MUST contain ≥10 entries (so you can pick 6 strong ones after cross-referencing variety). The weekly_conditions array MUST contain 3-4 entries (so the lead books cluster cleanly).

### Step 4 — Cross-promotion check (REQUIRED)

After trending research, scan the trending_books list against `content/reviews/`:

```bash
cd /Users/mike/.openclaw/workspace-bacottibot
python3 -c "
from pathlib import Path
import json, re

REVIEW_DIR = Path('projects/bithues/content/reviews')
reviews = {}
for f in REVIEW_DIR.glob('*.md'):
    text = f.read_text()
    title_m = re.search(r'^title:\s*[\"\'\u201c](.*?)[\"\'\u201d]', text, re.M)
    if title_m:
        reviews[title_m.group(1).lower()] = f.stem

trend = json.loads(open('.openclaw/tmp/bithues-weekly-trending-cache.json').read())
matches = []
for book in trend.get('trending_books', []):
    t = book['title'].lower()
    for rt, slug in reviews.items():
        if rt in t or t in rt:
            matches.append({'title': book['title'], 'slug': slug, 'review_title': rt})
import json as _j
print(_j.dumps(matches, indent=2))
" > .openclaw/tmp/bithues-weekly-cross-promote-candidates.json
```

If the candidates JSON is non-empty, AT LEAST TWO of the 6 lead books must have an inline `/reviews/<slug>/` link in the body. This drives newsletter readers → review pages (Amazon CTA) → book sales.

### Step 5 — Frontmatter validation gate (anti-pattern #98)

Before writing the MD, verify the frontmatter will be complete:

```bash
cd /Users/mike/.openclaw/workspace-bacottibot
DATE=$(date +%Y-%m-%d)
mkdir -p projects/bithues/content/newsletters
echo "Required frontmatter fields for the weekly brief:"
echo "  title, author, date, issue_type (MUST be 'weekly-digest'), topic, summary, description, featured_image, section (MUST be 'newsletters'), category (MUST be 'newsletters'), slug, genre_label (MUST be 'Weekly Digest')"
```

The author MUST rotate from: Margaret Chen / Eleanor Ashford / David Okonkwo / Sarah Voss / Jonas Albright / Aisha Patel. Identify the previous weekly brief's author first (Step 2) and pick a different one.

### Step 6 — Write the weekly brief MD

Use **this exact structure** (replace existing `## YYYY-MM-DD` content if present; if not present, append a new section):

```markdown
---
title: "<two-part title per directive>"
author: "<rotating author from pool>"
date: YYYY-MM-DD
issue_type: "weekly-digest"
topic: "<fiction|nonfiction|memoir|poetry|history|science|literary-criticism|essays|translated|short-stories|booker-watch|reading-practice>"
summary: "One short sentence summary here. NO em-dashes, NO smart quotes."
description: "One sentence meta description, similar in length to summary."
featured: true
draft: false
featured_image: "content-images/YYYY-MM-DD-<slug>.jpg"
card_image: "content-images/YYYY-MM-DD-<slug>.jpg"
section: newsletters
category: newsletters
slug: YYYY-MM-DD-<slug>
genre_label: "Weekly Digest"
---

## Headline: <TITLE>

<DECK SENTENCE>

## This Week's Reading Pattern

<PATTERN PARAGRAPH 220-320 words>

## The Season That Named The Week

- **<CONDITION 1>** — <one sentence naming the condition; one sentence naming what kind of book it unlocks>
- **<CONDITION 2>** — ...
- **<CONDITION 3>** — ...

## Six Books That Earn This Week

- **<Book Title>** by <Author> — [Amazon](https://www.amazon.com/...)
  **Why this week:** <one sentence>
  **What it asks of the reader:** <one sentence>
  **Companions:** <Book1 by Author1>, <Book2 by Author2>

- **<Book Title>** by <Author> — ...
  ... (5 more, total 6)

## Books Considered But Dropped

- **<title>** by <author> — <reason>
- ...

## Related Reading on Bithues

- **<article title>** — /articles/<slug>/
- **<review title>** — /reviews/<slug>/

## Worth Carrying

<one sentence>
```

Slug: lowercase, hyphenated, no em-dashes. 5-8 words that capture the central idea.

### Step 7 — Build the site

```bash
cd /Users/mike/.openclaw/workspace-bacottibot/projects/bithues/bithues-may24 && python3 build.py 2>&1 | tail -10
```

If `python3 build.py` exits non-zero, exit `status=error-build`.

### Step 8 — Sync to website/ deploy target

```bash
cd /Users/mike/.openclaw/workspace-bacottibot/projects/bithues
rsync -av --exclude='*.py' --exclude='*.md' --exclude='content/' --exclude='_template.html' --exclude='__pycache__' --exclude='.git' --exclude='website/' bithues-may24/ website/ 2>&1 | tail -5
```

The `--exclude='website/'` prevents the build tree's empty `website/` directory from being recreated as a nested `website/website/` inside the deploy target (that nesting previously carried a stale 143-URL sitemap).

### Step 9 — Commit + push to books CF Pages

```bash
cd /Users/mike/.openclaw/workspace-bacottibot/projects/bithues/website
# The gateway proxy makes git fail with "CONNECT tunnel failed, response 403".
# Every git call in this step runs with the proxy vars unset.
noproxy() { env -u HTTPS_PROXY -u HTTP_PROXY -u https_proxy -u http_proxy -u ALL_PROXY -u all_proxy "$@"; }

noproxy git add -A
noproxy git diff --cached --stat
noproxy git commit -q -m "weekly books digest <DATE> — <HEADLINE>" || echo "(no staged changes)"
noproxy git push books main 2>&1 | tail -5
```

`git add -A` is deliberate: the deploy repo contains only generated output, and staging everything keeps the sitemap, robots.txt, webmanifest, and page HTML from drifting apart. The build regenerates the whole tree, so partial staging is what caused the host-canonical mismatch in the first place.

Verify the push landed on the correct remote:

```bash
noproxy git ls-remote books refs/heads/main
```

If push fails with GH013 push-protection, the commit history has a Cloudflare Global API key leaked in TOOLS.md. Use `git push --no-verify books main` as documented in TOOLS.md — the leaked secret is unrelated to this commit.

### Step 9.5 — Re-submit sitemap to Google Search Console (REQUIRED)

```bash
cd /Users/mike/.openclaw/workspace-bacottibot
noproxy() { env -u HTTPS_PROXY -u HTTP_PROXY -u https_proxy -u http_proxy -u ALL_PROXY -u all_proxy "$@"; }
noproxy bash /Users/mike/.openclaw/workspace-bacottibot/.openclaw/tmp/gsc-sitemap-resubmit.sh books.bithues.com
# Expected: GSC sitemap re-submit: books.bithues.com → HTTP 204
```

Submit the **books** host. The books sitemap lives at `https://books.bithues.com/sitemap.xml`; the apex `bithues.com` belongs to the crypto project and has its own sitemap and its own GSC property.

If non-zero exit, log it but do NOT fail the run. Sitemap resubmit is best-effort. A `Token refresh failed` result means the Google OAuth refresh token is expired — that is a credential problem for the operator to fix, not a publishing failure; continue and report it.

### Step 10 — Verify live

```bash
cd /Users/mike/.openclaw/workspace-bacottibot
sleep 60
DATE=$(date +%Y-%m-%d)
SLUG=$(grep -lE "^date: ${DATE}" projects/bithues/content/newsletters/*.md | head -1 | xargs basename | sed 's/\.md$//')
# The gateway proxy returns 403 for these hosts; unset it for every curl.
noproxy() { env -u HTTPS_PROXY -u HTTP_PROXY -u https_proxy -u http_proxy -u ALL_PROXY -u all_proxy "$@"; }

# Preferred verification host is the canonical books host. While the registrar
# still delegates bithues.com to GoDaddy, books.bithues.com does not resolve,
# so fall back to the CF Pages deployment host that serves the same build.
CANON="https://books.bithues.com"
PAGES="https://books-bithues-rebuild.pages.dev"
if noproxy curl -sI -o /dev/null -w "%{http_code}" --max-time 15 "$CANON/" | grep -q 200; then
  BASE="$CANON"
else
  BASE="$PAGES"
  echo "NOTE: $CANON not serving (200). Verifying against Pages deployment host $BASE."
  echo "      Canonical-host reachability is a registrar delegation issue, not a build issue."
fi
echo "verification base: $BASE"

INDEX_CODE=$(noproxy curl -sI -o /dev/null -w "%{http_code}" "$BASE/newsletters/" --max-time 15)
BRIEF_CODE=$(noproxy curl -sI -o /dev/null -w "%{http_code}" "$BASE/newsletters/${SLUG}/" --max-time 15)
echo "books index: $INDEX_CODE"
echo "weekly brief ($SLUG): $BRIEF_CODE"

# Verify "0 developments" / empty-page markers are GONE
EMPTY=$(noproxy curl -sL "$BASE/newsletters/${SLUG}/" 2>&1 | grep -ciE "no books|no developments|empty|nothing to read|todo" || true)
echo "empty markers: $EMPTY"
[ "$EMPTY" -eq 0 ] && echo "OK: no empty markers" || echo "FAIL: empty markers present"

# Verify forbidden tokens are not in rendered HTML
FORBIDDEN=$(noproxy curl -sL "$BASE/newsletters/${SLUG}/" 2>&1 | grep -ciE "trending research|cross-promote|frontmatter gate|variety check|originality test|editorial disposition|dropped because|not chosen|author rotation" || true)
echo "forbidden tokens in HTML: $FORBIDDEN"
[ "$FORBIDDEN" -eq 0 ] && echo "OK: no internal-workflow tokens" || echo "FAIL: forbidden tokens leaked"

# Verify affiliate link count
AFFILIATE=$(noproxy curl -sL "$BASE/newsletters/${SLUG}/" 2>&1 | grep -c "tag=bithues-20")
echo "affiliate links: $AFFILIATE (floor 6)"
[ "$AFFILIATE" -ge 6 ] && echo "OK: >=6 affiliate links" || echo "FAIL: only $AFFILIATE affiliate links"

# Verify the canonical host and sitemap agree (book host, never the crypto apex)
CANON_TAG=$(noproxy curl -sL "$BASE/newsletters/${SLUG}/" 2>&1 | grep -oE '<link rel="canonical" href="[^"]*"' | head -1)
echo "canonical tag: $CANON_TAG"
echo "$CANON_TAG" | grep -q 'https://books.bithues.com' && echo "OK: canonical is books.bithues.com" || echo "FAIL: canonical is not books.bithues.com"

SITEMAP_HOSTS=$(noproxy curl -sL "$BASE/sitemap.xml" 2>&1 | grep -oE '<loc>https://[^/]+' | sort -u)
echo "sitemap hosts:"; echo "$SITEMAP_HOSTS"
echo "$SITEMAP_HOSTS" | grep -q 'bithues.com' && echo "OK: sitemap is books-only" || echo "FAIL: sitemap host drift"
```

**Do not declare done until every check passes.** Report the verification base used. If you verified against the Pages host because the canonical host was unreachable, say so explicitly in the status report — it is a registrar-delegation blocker owned by Mike, not a publishing failure.

## Status reporting

Report back with one of:

- `status=ok`: editorial written + build clean + push ok + live verification clean (include: body word count, lead book count, top 3 conditions, affiliate count)
- `status=ok-no-pattern`: signals did not cluster into a strong week-level thesis; shorter Weekly Note written (~1,200-1,500 words, 3-4 lead books)
- `status=error: <type>`: tool or pre-flight gate failure

## Failure modes to avoid

- Do not pad sources (one Amazon link per lead book).
- Do not write more than 2,500 body words.
- Do not duplicate books across conditions — merge them.
- Do not default to "Weekly Book News" or "This Week in Books" — write the SPECIFIC angle.
- Do not write vague "Worth Carrying" sentences. Each must be concrete.
- Do not write commentary that restates book plots.
- Do not write a pattern paragraph that could have been written on any single day — it must integrate events across the week.
- Do not include any personal names (anti-pattern #53).
- Do not fabricate quotes, statistics, or prize outcomes (anti-pattern #107).
- Do not include trading signals, price predictions, or buy/sell recommendations (AdSense hard boundaries).
- Do not write more than 6 lead books.
- Do not write fewer than 6 lead books unless status=ok-no-pattern is reported.
- Do not skip the live verification curl.

## Reference

- **Legacy daily prompt (deprecated):** `projects/bithues/cron-daily-newsletter.md` — read for historical context only; DO NOT use.
- **Daily cron job (to be deleted):** `b131e6f9-d143-4a41-856f-e59a2b84c88c` (Daily Bithues Newsletter — Auto Generate 5:45am ET). This weekly cron replaces it.
- bithues-books source: `projects/bithues/`
- Build pipeline: `projects/bithues/bithues-may24/build.py`
- Deploy target: `projects/bithues/website/` → GitHub `michaelbacotti/books-bithues-rebuild` (git remote `books`) → CF Pages project `books-bithues-rebuild` → custom domain `books.bithues.com`
- Host split: `bithues.com` + `www.bithues.com` are the **crypto** project (`michaelbacotti/bithues-rebuild`, CF Pages `crypto-bithues-rebuild`). `books.bithues.com` is the **books** project. Never point books canonicals, sitemap entries, or redirects at the apex.
- Bible (legacy daily doctrine): `skills/bithues-content-publishing/references/newsletter-bible.md` (kept for the author pool + canonical voice templates)
- Boundary doctrine: SKILL.md §"AdSense Hard Boundaries"
- Anti-pattern #107 (no fabrication): `AGENTS-anti-patterns.md`
- Anti-pattern #53 (no personal names): `AGENTS-anti-patterns.md`
- Anti-pattern #116 (MD source before HTML): `AGENTS-anti-patterns.md`