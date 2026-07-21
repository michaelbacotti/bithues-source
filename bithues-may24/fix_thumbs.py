#!/usr/bin/env python3
import re

with open('projects/bithues/bithues-may24/build.py', 'r') as f:
    content = f.read()

# Fix story_card_html - old pattern
old1 = '''    return f"""<div class="article-card">
 <div class="card-thumb" style="background-image:url({img_path}); background-size:cover; background-position:center; min-height:100px; margin-bottom:12px; border-radius:2px;" role="img" aria-label="{title}"></div>
 <div class="category-label">{genre}</div>
 {date_str}
 <h3><a href="/{slug}.html">{title}</a></h3>
 <p>{summary}</p>
</div>"""'''

new1 = '''    return f"""<div class="article-card">
 <div class="card-thumb stories-thumb" style="background-image:url({img_path});" role="img" aria-label="{title}"></div>
 <div class="category-label">{genre}</div>
 {date_str}
 <h3><a href="/{slug}.html">{title}</a></h3>
 <p>{summary}</p>
</div>"""'''

count1 = content.count(old1)
print(f"story_card_html matches: {count1}")
if count1 == 1:
    content = content.replace(old1, new1)

# Fix article_card
old2 = '''    return f"""<div class="article-card">
 <div class="card-thumb" style="background-image:url({img_path}); background-size:cover; background-position:center; min-height:100px; margin-bottom:12px; border-radius:2px;" role="img" aria-label="{title}"></div>
 <div class="category-label">{genre}</div>
 {date_str}
 <h3><a href="/articles/{slug}.html">{title}</a></h3>
 <p>{summary}</p>
</div>"""'''

new2 = '''    return f"""<div class="article-card">
 <div class="card-thumb articles-thumb" style="background-image:url({img_path});" role="img" aria-label="{title}"></div>
 <div class="category-label">{genre}</div>
 {date_str}
 <h3><a href="/articles/{slug}.html">{title}</a></h3>
 <p>{summary}</p>
</div>"""'''

count2 = content.count(old2)
print(f"article_card matches: {count2}")
if count2 == 1:
    content = content.replace(old2, new2)

# Fix review_card  
old3 = '''    return f"""<div class="article-card">
 <div class="card-thumb" style="background-image:url({img_path}); background-size:cover; background-position:center; min-height:100px; margin-bottom:12px; border-radius:2px;" role="img" aria-label="{title}"></div>
 <div class="category-label">{genre}</div>
 {date_str}
 <h3><a href="/reviews/{slug}.html">{title}</a></h3>
 <p>{summary}</p>
</div>"""'''

new3 = '''    return f"""<div class="article-card">
 <div class="card-thumb portrait-book" style="background-image:url({img_path});" role="img" aria-label="{title}"></div>
 <div class="category-label">{genre}</div>
 {date_str}
 <h3><a href="/reviews/{slug}.html">{title}</a></h3>
 <p>{summary}</p>
</div>"""'''

count3 = content.count(old3)
print(f"review_card matches: {count3}")
if count3 == 1:
    content = content.replace(old3, new3)

with open('projects/bithues/bithues-may24/build.py', 'w') as f:
    f.write(content)

print("Done")