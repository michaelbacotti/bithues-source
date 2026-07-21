def generate_index(all_stories: list[tuple[str, dict, str]]) -> str:

    # ── Top hero: 3 columns ───────────────────────────────────────────────────
    # Middle: featured story (first featured or most recent)
    featured = [s for s in all_stories if s[1].get("featured")]
    if not featured:
        featured = all_stories[:1]

    story_slug,  story_meta,  _  = featured[0]
    story_title = story_meta.get("title", story_slug)
    story_genre = story_meta.get("genre_label") or story_meta.get("type_label", "Short Story")
    story_date  = story_meta.get("date") or ""
    story_sum   = story_meta.get("summary", "")

    # Left: featured article (most recent)
    articles  = load_md_dir(ARTICLES_DIR)
    articles.sort(key=lambda a: a[1].get("date") or "", reverse=True)
    featured_article = articles[0] if articles else None

    # Right: featured review (most recent)
    reviews   = load_md_dir(REVIEWS_DIR)
    reviews.sort(key=lambda r: r[1].get("date") or "", reverse=True)
    featured_review = reviews[0] if reviews else None

    def hero_col(cls: str, content: str) -> str:
        return f'<div class="hero-col {cls}">{content}</div>'

    story_img = story_meta.get("card_image", f"/stories/images/{story_slug}.jpg")
    middle = f'''<div class="hero-col-img" style="background-image:url({story_img}); background-size:cover; background-position:center; min-height:160px; margin-bottom:20px; border-radius:2px;" role="img" aria-label="{story_title}"></div>
<div class="category-label">{story_genre}</div>
{('<div class="date-text">' + story_date + '</div>') if story_date else ''}
<h2><a href="/{story_slug}.html">{story_title}</a></h2>
<p>{story_sum}</p>
<a href="/{story_slug}.html" class="accent-link" style="font-weight:600;">Read Story &#8594;</a>'''

    left = ""
    if featured_article:
        a_slug, a_meta, _ = featured_article
        a_title = a_meta.get("title", a_slug)
        a_genre = a_meta.get("genre_label") or a_meta.get("type_label", "Article")
        a_sum   = a_meta.get("summary", "")[:120]
        a_img   = a_meta.get("card_image", f"/articles/images/{a_slug}.jpg")
        left = f'''<div class="hero-col-img" style="background-image:url({a_img}); background-size:cover; background-position:center; min-height:120px; margin-bottom:16px; border-radius:2px;" role="img" aria-label="{a_title}"></div>
<div class="category-label">{a_genre}</div>
<h3><a href="/articles/{a_slug}.html">{a_title}</a></h3>
<p>{a_sum}</p>
<a href="/articles/{a_slug}.html" class="accent-link">Read Article &#8594;</a>'''

    right = ""
    if featured_review:
        r_slug, r_meta, _ = featured_review
        r_title = r_meta.get("title", r_slug)
        r_genre = r_meta.get("genre_label") or r_meta.get("type_label", "Book Review")
        r_sum   = r_meta.get("summary", "")[:120]
        r_img   = r_meta.get("card_image", f"/reviews/images/{r_slug}.jpg")
        right = f'''<div class="hero-col-img" style="background-image:url({r_img}); background-size:cover; background-position:center; min-height:120px; margin-bottom:16px; border-radius:2px;" role="img" aria-label="{r_title}"></div>
<div class="category-label">{r_genre}</div>
<h3><a href="/reviews/{r_slug}.html">{r_title}</a></h3>
<p>{r_sum}</p>
<a href="/reviews/{r_slug}.html" class="accent-link">Read Review &#8594;</a>'''

    hero_html = (
        '<section class="hero-section">\n'
        '<div class="hero-three-col">\n'
        + hero_col("hero-col--left",   left)   + '\n'
        + hero_col("hero-col--center", middle) + '\n'
        + hero_col("hero-col--right",  right)  + '\n'
        + '</div>\n</section>'
    )

    # ── Below hero: 3-column sections ────────────────────────────────────────
    # Exclude the featured story from "more stories"
    used_slugs = {story_slug}
    more_stories = [s for s in all_stories if s[0] not in used_slugs][:3]
    more_articles = [a for a in articles if a[0] not in used_slugs][:3]
    more_reviews  = [r for r in reviews if r[0] not in used_slugs][:3]

    sections_html = (
        '<section>\n<div class="section-three-col">\n'

        '<div class="section-col">\n'
        '<div class="section-header">'
        '<h2>MORE STORIES</h2>'
        '<a href="/stories.html" class="explore-link">View all &#8594;</a>'
        '</div>\n'
        + '\n'.join(story_card_html(slug, meta, i)
                    for i, (slug, meta, _) in enumerate(more_stories))
        + '\n</div>\n'

        '<div class="section-col">\n'
        '<div class="section-header">'
        '<h2>MORE ARTICLES</h2>'
        '<a href="/articles.html" class="explore-link">View all &#8594;</a>'
        '</div>\n'
        + '\n'.join(article_card(a_slug, a_meta, i)
                    for i, (a_slug, a_meta, _) in enumerate(more_articles))
        + '\n</div>\n'

        '<div class="section-col">\n'
        '<div class="section-header">'
        '<h2>MORE BOOK REVIEWS</h2>'
        '<a href="/reviews.html" class="explore-link">View all &#8594;</a>'
        '</div>\n'
        + '\n'.join(review_card(r_slug, r_meta, i)
                    for i, (r_slug, r_meta, _) in enumerate(more_reviews))
        + '\n</div>\n'

        '</div>\n</section>'
    )

    return wrap_in_template(
        "Bithues — Book Reviews, Reading Guides & Original Stories",
        "In-depth book reviews across fiction, sci-fi, fantasy, nonfiction, and more — plus original short stories.",
        hero_html + '\n' + sections_html + '\n'
    )