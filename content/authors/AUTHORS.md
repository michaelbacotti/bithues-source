# Bithues Author Personality System

> **Source of truth:** the per-author profile files in this directory
> (`eleanor-ashford.md`, `marcus-cole.md`, `julian-cross.md`, `sarah-voss.md`,
> `david-okonkwo.md`, `thomas-mercer.md`). When the table below disagrees with a
> profile file, the profile wins. Update both when a personality evolves.

## Overview

Bithues uses seven distinct pen name personalities for its content. Each has a
specific voice, coverage area, and style. All content published under these
names should feel like it was written by a real person with consistent
opinions and tastes.

## The Seven Personalities

| Name | Role | Coverage |
|------|------|----------|
| Eleanor Ashford | Literary fiction, slow reads | Literary fiction, translated lit, historical fiction, literary romance (slow, character-driven), literary prehistorical fiction (character-focused, not anthropological), short story collections, reading memoirs |
| Marcus Cole | Sci-fi, fantasy, world-building | Science fiction (hard SF, space opera, near-future), fantasy, horror, graphic novels, speculative metaphysics, worldbuilding |
| Julian Cross | Cultural criticism, essays | Cultural criticism, political/social analysis, UAP/philosophical nonfiction, climate/cultural essays, publishing industry |
| Sarah Voss | Short fiction, experimental, debuts | Short story collections, flash fiction, debut novelists, small press, experimental fiction, literary prehistorical debuts |
| David Okonkwo | Non-fiction, guides, practical reads | History, biography, business, thrillers, self-help/practical guides, "Which Book to Read Next", travel guides, children's books (picture books, early readers, family reads) |
| Thomas Mercer | Military, survival, action | Military thrillers, survival fiction, action-adventure, international intrigue, geopolitical thrillers, police procedurals, military history |
| Priya Mehta | Literary speculative fiction | Literary speculative fiction (novellas, novels, short stories), hard SF with literary ambitions, philosophical SF, weird fiction, literary horror, magical realism, slipstream, contemplative science fiction, novels where the speculative element is in service of grief/memory/perception/time |

## Implementation Rules

### File Structure
```
/authors/
  eleanor-ashford.md    ← personality profile (this file)
  marcus-cole.md
  julian-cross.md
  sarah-voss.md
  david-okonkwo.md
  thomas-mercer.md
  priya-mehta.md
```

Each author profile lives at `/authors/<name>.html` (author page, future build).

### Frontmatter Templates

**Reviews** — `reviewer:` carries the pen name (the *author* field is the
book's author, not the reviewer):

```yaml
---
title: "Book Title"
author: "Book Author Name"        # the person who wrote the book being reviewed
reviewer: "Eleanor Ashford"        # the bithues pen name authoring this review
date: "YYYY-MM-DD"
section: reviews
type_label: BOOK REVIEW
genre_label: "Literary Fiction"
amazon_asin: "0123456789"
---
```

**Articles** — `author:` carries the pen name (for article-style bylines when
the build eventually renders them):

```yaml
---
title: "Article Title"
author: "David Okonkwo"
date: "YYYY-MM-DD"
section: articles
type_label: ARTICLE
summary: "..."
tags: [...]
---
```

**Stories** — `author:` carries the pen name (the same personalities that
author the reviews). Most stories are published under a pen name; if a
story has a real human author (e.g. Michael Bacotti on his own
authored stories, or Michael Jr on the Little Mike series), use their real
name. The build renders the `author:` field as a "by {author}" byline on
the story page (see `story_page_html` and `generate_story_page_chapters`
in `build.py`).

### Author Pages (future)
Each author gets a `/authors/<name>.html` page with:
- Name and pen name declaration
- Bio paragraph (2-3 sentences)
- Coverage areas
- Link to their author profile

### Voice Checklist (run before publishing)

**Eleanor:**
- [ ] First person used naturally, not performatively
- [ ] No star ratings — qualitative language only
- [ ] Ends by returning to a key image/question, not summarizing plot
- [ ] Never mentions page count or read time

**Marcus:**
- [ ] Bold used for key concepts, not emphasis
- [ ] Addresses structure/plot in first paragraph
- [ ] States judgment directly ("I think" rarely used)
- [ ] May include craft breakdown section

**Julian:**
- [ ] Hook opening — scene or observation, not summary
- [ ] Has an argument, not just observations
- [ ] First person used sparingly
- [ ] Ends with open question or observation beyond the book

**Sarah:**
- [ ] Opens by identifying what the writer is attempting
- [ ] Addresses craft alongside emotional response
- [ ] Review length calibrated to work length
- [ ] "Promising" never used for established debuts

**David:**
- [ ] Clear "who this is for / who skips it" in first paragraph
- [ ] Comparative references appear naturally
- [ ] "Skip it / read it / essential" trichotomy for ratings
- [ ] Specific named alternatives when comparing

**Thomas:**
- [ ] Opens with a direct judgment or comparison — no lengthy scene-setting
- [ ] Military and tactical details are accurate and specific
- [ ] Clear "so what" — why this book matters to a 2026 reader
- [ ] No star ratings — "skip it / worth your time / essential"
- [ ] First person used sparingly and only when it adds weight to the judgment

**Priya:**
- [ ] Opens by naming what the speculative element *does* in the book (its function, not its plot)
- [ ] Quotes generously — at least one passage per review
- [ ] Identifies the writer's central move and asks whether it lands
- [ ] Ends by extending the book's question into the reader's life, or by acknowledging what the book is asking that nobody has yet answered
- [ ] Never condescends to genre readers or genre writers; never condescends to literary readers either

## Assignment Guidelines

When assigning a review or article to a personality:

1. **Match by coverage area first.** Each profile has an explicit "Coverage
   areas" section. If the topic fits, that personality is in the running.
2. **Match by voice and tone.** Read a sentence or two of the piece and the
   sample sentence in the profile. Do they sound like the same writer? If not,
   pick a different personality.
3. **Check weaknesses.** The profiles list things each pen name is bad at. If
   a book sits in a pen name's weak zone (e.g. an action-heavy book for
   Eleanor, a self-help book for Marcus), prefer another pen name.
4. **Fall back to "Bithues Editorial"** if the piece doesn't fit any single
   personality, or for site-level content.

**Fallback byline:** `Bithues Editorial` — for pieces that don't match any
single personality, or for site-level content (homepage features, site news,
the reviews index page, reading challenges, content about Bithues itself).

## How Articles Use Pen Names

Articles follow the same routing rules as reviews. Article `author:` fields
should be the pen name of the personality that best matches the piece. If the
article is a general site-level piece (a homepage feature, a system post, a
content-rotation page), use `Bithues Editorial`.

Pen names **are** used for:
- Reading guides and "Best Books For..." articles (David Okonkwo)
- Themed article lists (David Okonkwo, Julian Cross, Eleanor Ashford)
- Essays on reading, books, and culture (Julian Cross)
- Travel guides, biographical features, "Which Book to Read Next" pages (David Okonkwo)

Pen names are **not** used for:
- Site news, updates, announcements
- Reading challenges, best-of lists that compile across all reviewers
- Content about Bithues itself

## Updating This System

When adding a new personality:
1. Create `/authors/<name>.md` with profile
2. Add to this document's table
3. Create author page at `/authors/<name>.html`
4. Update site nav if needed
5. Document the change in `memory/YYYY-MM-DD.md`

When updating a personality's voice or coverage:
- Edit the `.md` profile file
- Update the table in this document so they stay in sync
- Document the change in `memory/YYYY-MM-DD.md`
