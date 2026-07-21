# Bithues Content Quality Standards

> Standards for all content published on bithues.com. These ensure consistency, readability, and quality that readers would pay for.

---

## Story Standards (`content/stories/*.md`)

### Frontmatter
```yaml
---
title: "Title in Proper Title Case"           # NOT ALL CAPS, NOT lowercase
date: "YYYY-MM-DD"                             # ISO date
section: stories
type_label: SHORT STORY
summary: "A compelling 1–2 sentence hook that makes a reader want to click. No meta-language like 'A short story about...' — just the story's own voice."
card_image: null                               # null unless custom image is commissioned
genre_label: "Fiction"                         # Literary Fiction, Sci-Fi, Dark Fantasy, Historical Mystery, etc.
featured: false
draft: false
---
```

### Genre Labels (approved values)
- `Literary Fiction` — character-driven, realistic, quiet
- `Historical Fiction` — set in documented historical periods
- `Sci-Fi` — science, space, technology
- `Dark Fantasy` — fantasy with horror edges
- `Fantasy` — secondary worlds, magic systems
- `Speculative Fiction` — slipstream, near-future, uncanny
- `Spiritual Fiction` — interior, contemplative, metaphysical
- `Children's Fiction` — middle grade or younger
- `Self-Help Fiction` — fiction structured around personal growth lessons

### Prose Quality
- **Lead with the story, not the premise.** First paragraph should pull the reader into a scene, not explain what the story is about.
- **No meta-commentary.** No lines like "This is a story about..." or "The narrator wanted..."
- **Literary craft.** Varied sentence length, precise diction, scenes that earn their place.
- **No trailing whitespace artifacts** (e.g., `····` used as fake indentation — these are markup remnants).
- **Paragraphs are real.** No giant 2,000-word opening paragraphs. Break at natural scene/logical beats.
- **Punctuation:** em dashes `—` (not `--`), proper ellipses `…` (not `...`), curly quotes preferred.

### Summary Quality
- Write the summary as if you are the protagonist speaking a single sentence to a stranger at a party.
- It should be specific, atmospheric, and hint at stakes without summarizing the plot.
- ❌ "A short story about a woman who discovers something about her past."
- ✅ "On the day her mother's estate clears probate, a woman finds a letter she doesn't remember writing to someone she's never heard of."

---

## Review Standards (`content/reviews/*.md`)

### Frontmatter
```yaml
---
title: "Book Title"                             # The book being reviewed
date: "YYYY-MM-DD"
section: reviews
type_label: BOOK REVIEW
summary: "A 1–2 sentence assessment. Include the star rating contextually: 'Ingber's debut bends time-loops into something achingly personal [⭐⭐⭐⭐]'"
card_image: null
author: "Reviewer Name"                        # The person writing the review — real name
genre_label: "Fiction"                         # Genre of the book being reviewed
rating: 4                                      # Integer 1–5. 0 means unrated; we should have real ratings.
featured: false
draft: false
---
```

### Body Structure (recommended order)
1. **Hook paragraph** — lead with a striking observation from the book or a counter-intuitive take
2. **Book metadata line** — author, year, genre, page count in one sentence
3. **Summary** — one paragraph capturing what the book is and what it's trying to do
4. **Analysis** — 2–4 paragraphs on what works, what doesn't, why it matters
5. **Recommendation** — who should read this, who should skip it, and the bottom-line verdict

### Rating Standards
- **We should rate.** A rating of `null` signals we didn't finish the book or couldn't form an opinion — neither of which is true. Pick a number 1–5.
- Rating guide: `1` = do not recommend, `2` =瑕疵多但有亮点, `3` = average/readable, `4` = strongly recommended, `5` = essential/read-before-you-die
- If the review discusses the book critically but still recommends it, rate `3–4` and let the prose carry the nuance.
- The rating is an anchor for the card display, not a substitute for the review.

### Reviewer Voice
- Write as a knowledgeable friend who read the book, not a professional critic.
- Be specific: quote a sentence that demonstrates the prose quality, name a structural choice that worked, point to a character moment that earned its emotion.
- Avoid vague praise: "This is a book everyone should read" without evidence is not a review.
- Own your opinion. "I found the second act bloated" is more useful than "some readers might find pacing issues."

---

## Article Standards (`content/articles/*.md`)

### Frontmatter
```yaml
---
title: "Title in Proper Title Case"
date: "YYYY-MM-DD"
section: articles
type_label: ARTICLE
summary: "A 1–2 sentence description. What is this article, who is it for, what will they learn or understand?"
card_image: null
tags: ["tag1", "tag2"]                         # Non-empty array. Use existing tags when possible.
featured: false
draft: false
---
```

### Body Structure
1. **Lead paragraph** — a hook, question, or striking statement that contextualizes why this matters now
2. **Body sections** — use `##` and `###` headers to organize logically
3. **Supporting paragraphs** — provide evidence, examples, named books/author comparisons
4. **Closing** — a synthesis, call to action, or provocation that leaves the reader with something to consider

### Quality Bar
- Every article should answer: "Why should someone spend 10 minutes reading this instead of doing something else?"
- Cite specific books, authors, and passages — vague references undermine credibility.
- Lists (e.g., "Top 10 Fantasy Books for Beginners") must have real, defensible recommendations, not placeholder copy.
- No padding: every paragraph should earn its place. If you can cut it without losing meaning, cut it.

### Tag Standards (approved tags — expand as needed)
`reading-guides`, `sci-fi`, `fantasy`, `literary-fiction`, `self-help`, `children's-books`, `book-clubs`, `nonfiction`, `horror`, `historical-fiction`, `romance`, `how-we-review`, `homeschool`, `entrepreneurs`, `retirees`, `military`

---

## Missing Content Audit (May 2026)

### Stories — 6 Missing from `content/stories/`
These exist in the Hugo archive but not in the current content folder:
- [ ] `blood-ties.md` — Dark Fantasy
- [ ] `the-quiet-town.md` — Literary Fiction (Hugo archive file exists but is empty — needs writing)
- [ ] `the-shadow-garden.md` — Fiction (Hugo archive file exists but is empty — needs writing)
- [ ] `the-sound-between-stars.md` — Sci-Fi (Hugo archive file exists but is empty — needs writing)
- [ ] `the-space-between.md` — Spiritual Fiction (✅ full content available from Hugo archive)
- [ ] `the-time-auction.md` — Self-Help Fiction (✅ full content available from Hugo archive)

**Note:** Three stories (`the-quiet-town`, `the-shadow-garden`, `the-sound-between-stars`) have empty Hugo archive files — the full content was found in the `bithues-next` HTML archive and needs to be reconstructed from that source.

### Content Source Priority
1. Hugo archive MD file (best — clean prose, clean frontmatter)
2. `bithues-next` HTML archive (second — prose available, needs frontmatter extraction)
3. Hugo public HTML (fallback — only if nothing else available)

---

## Common Fixes Required

| Problem | Fix |
|---|---|
| ALL CAPS title | Convert to Title Case |
| `summary: null` or generic summary | Write a compelling 1–2 sentence hook |
| `genre_label: null` | Assign from approved genre list |
| `rating: null` | Read the book or review carefully enough to assign 1–5 |
| `tags: []` (articles) | Add 2–4 relevant tags from approved tag list |
| `card_image: null` | Keep null unless custom image exists |
| Placeholder author like "Bithues Staff" | Use real reviewer name from pen name system |
| Trailing whitespace `····` | Remove and normalize paragraph breaks |
| Draft: false missing | Add it |

---

## Pen Name System (6 authors)

> **Source of truth:** `/content/authors/AUTHORS.md` and the per-author
> profile `.md` files. The names below must match those. If you change a
> profile, update both this file and the table in `AUTHORS.md`.

These personalities write Bithues content. Assign based on coverage and voice:

- **Eleanor Ashford** — Literary fiction, translated lit, historical fiction, reading memoirs, literary prehistorical
- **Marcus Cole** — Sci-fi, fantasy, horror, graphic novels, speculative metaphysics, worldbuilding
- **Julian Cross** — Cultural criticism, essays, UAP/philosophical nonfiction, climate/cultural essays
- **Sarah Voss** — Short fiction, flash fiction, debut novelists, small press, experimental
- **David Okonkwo** — Non-fiction, guides, history, biography, business, self-help, travel guides, "Which Book to Read Next", children's STEM
- **Thomas Mercer** — Military thrillers, survival, action, international intrigue, geopolitical thrillers

For a complete voice and coverage map, see `/content/authors/AUTHORS.md`.

*When in doubt, match the content's tone to the author's voice. If nothing
fits, use `Bithues Editorial` as the fallback byline.*

---

*Last updated: 2026-05-21*