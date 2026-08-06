# Emotional Weather Radar

**Status:** Idea (not started). Stored 2026-07-22 17:43 ET.
**Owner:** Mike
**Trigger date for possible start:** Monday 2026-07-27
**Subdomain candidates:** `weather.bithues.com`, `radar.bithues.com`, `climate.bithues.com`
**Associated site:** bithues.com (michaelbacoti/bithues-rebuild — Cloudflare Pages)

## Concept

A website/subdomain that visualizes **emotion like weather**. Instead of just showing mood scores, it treats emotions as atmospheric conditions: storms, pressure systems, clear skies, fronts, seasons, and volatility. The site should feel like an emotional climate dashboard rather than a basic sentiment app.

## Why it matters

This is meant to be a **novel, imaginative concept for bithues** — not just a re-skin of a journal or mood tracker. The point is to create a more poetic and visually compelling way to explore emotional patterns over time, across people, topics, places, or communities.

Bithues' editorial brand is about books as emotional cartography — a quiet, reader-first space. Emotional Weather Radar extends that thesis off the page into an interactive atmospheric visualization.

## Initial direction

- **Atmospheric and immersive** feel. Not a clinical dashboard.
- Visualize emotion as **radar, forecast, climate, or weather systems**.
- Use **"emotional weather"** as the core metaphor.
- Subdomain options (in order of preference, TBD):
  - `weather.bithues.com` — most direct read
  - `radar.bithues.com` — emphasizes the live-data/realtime aspect
  - `climate.bithues.com` — emphasizes long-term patterns

## Open questions to resolve before building

These are blockers — Mike to think on these before next Monday.

### Source of data
What data feeds the visualizations? Options:

1. **Book-driven** — pull sentiment/emotion data from the bithues review corpus (50 books, 6,000+ paragraphs). Each book becomes a "region" with its own emotional climate. This is the most on-brand option and ties the project back to the editorial mission.
2. **Community-driven** — readers submit short reflections or mood notes, and the site aggregates anonymized patterns. Higher engagement but needs moderation + privacy work.
3. **Public-corpus-driven** — third-party data (Twitter, Reddit, news) tracked for emotion patterns over time. Easier to launch but not unique.

### Visualization unit
What does one "data point" on the radar represent?

- A book's emotional arc over its chapters
- A topic's emotional signature over time
- A region's emotional climate based on submissions
- A "weather event" — a single emotional moment that ripples across the corpus

### Time scales
- Real-time radar (last 24 hours)
- Daily forecast (today + tomorrow)
- Weekly outlook (the emotional "week ahead")
- Long-term climate (seasonal patterns over months/years)

### Reader participation
- **Passive** — site is read-only (like bithues reviews)
- **Active** — readers submit their own mood notes that feed the radar
- **Hybrid** — readers can submit, but the primary visualization is editorial

## Possible sections (v0 mental sketch)

- **Radar (live)** — a moving visualization of the day's emotional climate. Storms, pressure systems, fronts.
- **Forecast** — editorial weekly outlook on emotional patterns in the current reading.
- **Climate** — long-term seasonal trends in the bithues review corpus.
- **Weather stations** — individual books as "stations" with their own emotional readings.
- **Field reports** — short editorial pieces that read like weather reports on books or reading moods.

## Technical direction (preliminary)

- **Stack**: Cloudflare Pages (matches bithues) + Pages Functions for any aggregation logic.
- **Data source**: bithues review corpus as the seed data for the visualization. Each book = one "weather station."
- **Frontend**: vanilla JS or D3.js for the radar/climate visualizations. No build tooling if possible.
- **Storage**: KV for any reader-submitted data. Analytics Engine for event counts.
- **Privacy**: anonymized, no personal names (consistent with bithues privacy doctrine).

## Next steps

When Mike is ready (planned start: **Monday 2026-07-27**):

1. Decide on **data source** (book-driven vs community-driven vs hybrid) — biggest design decision.
2. Decide on **subdomain** — pick one of `weather.bithues.com` / `radar.bithues.com` / `climate.bithues.com`.
3. Sketch a **visual direction** — does the radar look like a meteorological radar, a topographic climate map, or an abstract atmospheric canvas?
4. Write a **concept spec** — 1-2 pages that turn this into something an LLM or contractor can build from.
5. Build a **sitemap** — what pages does the site need?
6. Set up the **subdomain** in Cloudflare DNS.

## Do not start before Mike says so

This file is a **parking lot**, not a build plan. The trigger date (Monday 2026-07-27) is a hint, not a directive. Mike will explicitly say "start building" or equivalent before any work begins.

---

**Source:** Saved from Mike's directive on 2026-07-22 17:43 EDT — "Remember this project idea for bithues: Emotional Weather Radar."