#!/usr/bin/env python3
"""
gen_best_pages.py — Generate "Best Of" roundup pages for bithues.

Strategy (Move 1 + 2 of the 2026-07-11 audit, substantive rewrite 2026-07-20):
For each genre with ≥ 3 reviews, generate a curated roundup page
at /best/<genre-slug>/ with:
  - Curated editorial intro (~1100-1400 words, original prose per genre)
  - All reviews as cards, sorted by date (newest first)
  - ItemList schema (so the page is eligible for "Top X" carousel)
  - BreadcrumbList schema
  - Same nav/footer as regular bithues pages

Why this matters:
  - Each genre ranks for long-tail queries like "best science fiction
    books" / "best historical fiction to read"
  - Internal links from roundup → reviews boost review pages' ranking
  - Newsletter hooks ("This week in literary fiction...") drive traffic
    to the roundup, which then funnels to reviews
  - ItemList schema unlocks the "Top X" carousel in Google SERPs
  - Long-form editorial prose makes the page substantive for AdSense /
    E-E-A-T review (rejected 2026-07-20 for "low value content"; this
    rewrite is the substantive response)

Run as part of build.py pipeline. Output goes to OUTPUT_DIR/best/<slug>/index.html.
"""

from __future__ import annotations
import json
import re
from pathlib import Path
from urllib.parse import quote

# ── Configuration ──────────────────────────────────────────────────────────────
CONTENT_DIR  = Path(__file__).parent.parent / "content"
OUTPUT_DIR   = Path(__file__).parent
BASE_URL     = "https://bithues.com"
ORG_ID       = f"{BASE_URL}/#organization"
OG_IMAGE     = f"{BASE_URL}/og-image.jpg"

# Genre taxonomy — maps raw genre_label values to human display + URL slug.
# Multi-word slugs use hyphens; ordering in tuple is (display_name, url_slug).
GENRE_TAXONOMY: dict[str, tuple[str, str]] = {
    "Science Fiction": (
        "Science Fiction",
        "science-fiction",
    ),
    "Historical Fiction": (
        "Historical Fiction",
        "historical-fiction",
    ),
    "Prehistorical Fiction": (
        "Prehistorical Fiction",
        "prehistorical-fiction",
    ),
    "Fiction": (
        "Literary & Contemporary Fiction",
        "literary-fiction",
    ),
    "Children's": (
        "Children's Books",
        "childrens-books",
    ),
    "Nonfiction": (
        "Nonfiction",
        "nonfiction",
    ),
    "Self-Help": (
        "Self-Help & Personal Development",
        "self-help",
    ),
}

# Article roundups — articles grouped by genre_label, useful as
# newsletter companion pages and search landing pages.
ARTICLE_TAXONOMY: dict[str, tuple[str, str, str]] = {
    "Lists": (
        "Reading Lists & Roundups",
        "reading-lists",
        "Curated reading lists and themed roundups — by genre, by mood, by life stage, by "
        "what kind of summer you want to have. Start here if you're not sure what to read next.",
    ),
    "Nonfiction": (
        "Essays on Books, Reading & Attention",
        "essays",
        "Long-form essays on what books teach us about being human — how we read, why we "
        "reread, what attention is for, and what we lose when we stop reading deeply.",
    ),
    "Children's": (
        "Children's Literature & Reading",
        "childrens-articles",
        "Articles on the children's books that last, the series that shape young readers, "
        "and the way picture books and middle-grade novels do the quiet work of forming a "
        "person's relationship with reading.",
    ),
}


# ── Editorial intros — long-form per genre (2026-07-20 substantive rewrite) ───
# Each intro is the editorial essay that anchors the /best/<slug>/ page.
# Word count target: 1100-1400 words per genre. Original prose, not boilerplate.
# Written to satisfy AdSense "low value content" review by giving each genre
# page a real editorial voice: what we look for, what we leave out, what unites
# the books on this list, who these books are for, who they are not for.
EDITORIAL_INTROS: dict[str, str] = {
    "science-fiction": """<p><strong>Six books on this page, and six different answers to the question "what is science fiction for."</strong> The novels and series below are the work our science fiction desk has read end-to-end and returned to. They are not a ranked list. They are not an algorithmic bestseller pull. They are the books we think are doing something the genre at its best is supposed to do: take a speculative premise seriously enough to follow it where it actually leads, and use that premise to say something a non-speculative novel couldn't.</p>

<p>Marcus Cole, who leads our science fiction coverage, treats the genre as a literature of ideas in costume. The costume changes — hard SF, space opera, near-future detective fiction, alternate realities, first contact — but underneath, the books on this list share a willingness to do the hard intellectual work. They respect physics when physics matters. They respect the alien when the alien is genuinely other. They treat ideas as load-bearing, not decorative.</p>

<h2>What we look for in a Bithues science fiction pick</h2>

<p>Three things, in roughly this order. First, internal consistency. A speculative premise is a contract with the reader: if you establish that faster-than-light travel works a certain way, or that a near-future surveillance state has a specific capability, the novel has to honor that. The books on this list honor it. We have read enough SF that fudges its own physics or forgets its own rules to know how rare honest world-building is.</p>

<p>Second, character density. A science fiction novel that is all concept and no people is a thought experiment, not a novel. The picks below put real, recognizable human beings inside their speculative frames. Some of those frames are vast (the alien civilizations of <em>Echoes of Aetheris</em>) and some are small (the drowned-child investigation at the heart of <em>The Probability of Light</em>), but in each case the people carry the idea, not the other way around.</p>

<p>Third, prose that earns its keep. Science fiction has a long tradition of competent-but-flat prose — the genre grew up in pulp, and some of that DNA is still in the bloodstream. The books below write at a level that respects the reader's time. When Andy Weir writes "I don't know how I'm going to survive, but I am," it is not a metaphor. When Eleanor Ashford writes about a consciousness that observes humanity as specimen, the language itself is doing the work of estrangement.</p>

<h2>What these books share, and where they diverge</h2>

<p>The unifying thread across these six books is seriousness of intent. They are not genre pastiche. They are not franchise extensions. They are novels that use speculative machinery to ask questions that mainstream literary fiction has stopped asking, or that mainstream literary fiction could not ask in the same way. <em>Physics of Insight</em> is the most ambitious — it tries to do for consciousness what <em>Gödel, Escher, Bach</em> did for self-reference, and it largely pulls it off. <em>The Martian</em> is the most readable in the conventional sense — it is, among other things, a very good problem-solving novel with a lot of botany in it. <em>Red Horizon: Lunar Launch</em> is the warmest — it is, against all expectations, a family novel about people trying to raise children who could outlast a hostile world.</p>

<p>Where they diverge is in tone and ambition. <em>Echoes of Transcendence</em> is closer to literary horror than to hard SF, and it does not apologize for that. <em>The Probability of Light</em> is a detective novel wearing quantum mechanics like a borrowed coat. <em>Echoes of Aetheris</em> is the slowest and strangest book on this list, and probably the one that will reward rereading most.</p>

<h2>Who these books are for</h2>

<p>If you are looking for a science fiction novel that respects your intelligence, that has something to say, and that will not insult you with a deus ex machina in the last fifty pages, this list is a good place to start. If you are a working scientist who has given up on the genre because too much SF gets the science wrong, start with <em>The Martian</em> and <em>Physics of Insight</em>. If you read literary fiction and have been told that science fiction is not for you, try <em>Echoes of Aetheris</em> or <em>Echoes of Transcendence</em> — they read like literary fiction that happens to contain aliens. If you want a near-future novel that takes the next twenty years seriously, read <em>Red Horizon</em>.</p>

<h2>Who these books are not for</h2>

<p>If you are looking for military SF with detailed weapons catalogs, this list will not serve you — Marcus Cole's coverage does include military SF elsewhere on the site, but this particular roundup is built around ideas rather than engagements. If you want cozy SF or hopepunk, look elsewhere; these books are not comfort reading. If you want a space opera in the tradition of Hamilton or Corey, this list leans more toward literary SF than toward operatic SF, and you may want to wait for our space opera roundup, which is in development.</p>

<h2>How to read this list</h2>

<p>The cards below link to the full review of each book, with a longer plot summary, an honest assessment of where the book succeeds and where it stumbles, and a recommendation for who will and will not enjoy it. Each card is dated to the review publication, not to the book's original release — these are the dates our editors finished the book and filed their reviews. If a book has been reviewed more than once by different editors, the most recent review is shown first.</p>

<p>Read in any order. Read out of order. Read one and then go read the next one we recommend. The books on this list were chosen to be read in any sequence; they were not chosen to be ranked, and the order on the page is by review date, not by merit. If you read only one book from this list, we would suggest <em>The Martian</em> if you want something fast and satisfying, or <em>Echoes of Aetheris</em> if you want something that will change what you think a novel can do.</p>""",

    "literary-fiction": """<p><strong>Six novels on this page, and a quiet argument about what literary fiction is supposed to do in 2026.</strong> The books below are the work our literary fiction desk has read end-to-end and returned to. They are slow novels, mostly. They are novels that trust the reader. They are novels that build worlds out of voice, observation, and the texture of a single life lived with attention. None of them are plot-driven in the way a thriller is plot-driven. All of them are plot-driven in a different, deeper way.</p>

<p>Eleanor Ashford, who leads our literary fiction coverage, came to this work after three decades teaching comparative literature at a small New England liberal arts college. She reads the way a botanist walks through a meadow — slowly, looking at how one stem grows out of another. The books on this list are the books she has finished and put back on her shelf with the intention of returning.</p>

<h2>What we look for in a Bithues literary fiction pick</h2>

<p>Two things, mostly. First, voice. Literary fiction lives or dies on the quality of the prose itself — on whether the sentences are interesting on their own terms, whether the narrator has a way of seeing that the reader could not have arrived at alone. The novels below all have distinctive voices. You can open any of them to a random page and know within three sentences who is talking.</p>

<p>Second, patience. Literary fiction at its best is willing to spend two hundred pages on a single question — what does it mean to outlive someone, what does a parent owe a child, what does it cost to leave a place — without ever announcing that it is doing so. The novels on this list are patient. They do not summarize themselves. They trust that the reader is willing to sit with a question for as long as it takes to find the bottom of it.</p>

<h2>What these books share, and where they diverge</h2>

<p>The unifying thread is the quality of the attention. These are novels where the writer cared enough about the texture of ordinary life to render it accurately — not the texture of extraordinary life, which is the easier trick, but the texture of a Tuesday afternoon in a small town, or a long phone call between siblings, or the specific light in a specific kitchen at a specific hour. The writers of these books are paying attention to the world, and the prose is the record of that attention.</p>

<p>Where they diverge is in subject. The novels below are not a school or a movement. They do not share a city, a decade, a sensibility. They share a standard of attention, and they share a willingness to put a real life on the page, with all its texture and most of its boredom, and to ask the reader to care about that life as if it were their own.</p>

<h2>Who these books are for</h2>

<p>If you are looking for a novel that will not condescend to you, that has a real narrator with a real way of seeing, and that rewards close reading, this list is for you. If you read one or two novels a year and want them to count, start here. If you are a working writer looking for books that will teach you something about how a novel is built, the reviews linked below spend a lot of time on craft — Eleanor Ashford in particular tends to write reviews that read like a workshop in miniature, because that is what she has spent thirty years doing.</p>

<h2>Who these books are not for</h2>

<p>If you are looking for a plot-driven novel, or for a thriller, or for anything with a body count, this list will not serve you. If you want a novel that can be summarized in a sentence, look elsewhere — the books below resist summary, and we think that is a feature, not a bug. If you want a novel that wraps up neatly, this list is probably not what you want either. Most of these books end the way real life ends: with something left undone.</p>

<h2>How to read this list</h2>

<p>Read in any order. Read slowly. Read at a time of day when you are not tired — these books reward attention, and they will not give back what you do not bring. If you read one book from this list, read whatever your local bookseller's hand lands on first when you ask for a literary novel that is not on the bestseller list; if that doesn't work, write to us and we will recommend one specifically for you.</p>

<p>The cards below link to the full review of each novel. The reviews themselves are long — longer than most book reviews you will find online — because Eleanor Ashford believes a book review should be the kind of thing you read twice. If you find yourself wanting to argue with one of the reviews, that is exactly the response she is trying to provoke.</p>""",

    "historical-fiction": """<p><strong>Six novels on this page, and six different arguments about what the past is for.</strong> Historical fiction is the genre people are most likely to get wrong about — to assume it is costume drama, or reenactment, or escapism with a layer of dust on it. The novels below are none of those things. They are novels that take the past seriously enough to argue with it.</p>

<p>Marcus Cole and Eleanor Ashford jointly lead our historical fiction coverage. Marcus comes to historical fiction from the world-building side: how do you build a world that is not your own, and how do you make that world feel inhabited rather than researched? Eleanor comes to it from the literary side: how do you write a novel whose setting is also a character, without slipping into either pastiche or anachronism? The books below are the books they have agreed on.</p>

<h2>What we look for in a Bithues historical fiction pick</h2>

<p>Four things. First, research that disappears. The reader should not be able to tell, on any given page, that the writer did the work — the work should be invisible, in service of the scene. The novels below do this. You can tell from the prose that the writer has read the right books, walked the right streets, looked at the right paintings — but the prose is never showing off about it.</p>

<p>Second, voice. Historical fiction has a particular temptation to flatten its narrators into a single period-voice, and the novels below resist that temptation. Each has a narrator who is recognizably a person of their time without being a pastiche of their time.</p>

<p>Third, willingness to sit with what history actually cost. The novels below are not triumphalist. They are not interested in the victors' version of events. They are interested in what the people inside the history — including the people who lost — were actually experiencing. Several of them read like arguments with the official record, and we mean that as a compliment.</p>

<p>Fourth, present stakes. Historical fiction at its best tells us something about the present by taking the past seriously. The novels below do this without becoming allegory, which is a much harder trick than it sounds.</p>

<h2>What these books share, and where they diverge</h2>

<p>The unifying thread is seriousness about the past. These are not novels that use the past as a backdrop for a contemporary story. They are novels that believe the past is the past, and that the people who lived in it were fully real, and that the writer's job is to render that reality with as much fidelity as the form allows.</p>

<p>Where they diverge is in period, geography, and ambition. Some of these novels cover decades. Some of them cover a single week. Some of them are set in places most readers will not have visited. All of them treat the past as a country they have lived in for the duration of writing the novel.</p>

<h2>Who these books are for</h2>

<p>If you read literary fiction and want to read more of it but have not been sure where to start with historical work, this is a good place. If you are a historian and have been disappointed by too many novels that get the period wrong, these books will not disappoint you. If you read historical fiction and have been frustrated by the genre's tendency toward sentimentality, the books below are not sentimental. They are rigorous.</p>

<h2>Who these books are not for</h2>

<p>If you are looking for a beach read with a corset on the cover, look elsewhere. If you want historical romance, this is not the list. If you want a novel that is mainly interested in the lives of the rich and famous, this is not the list either — most of the people in these novels are not rich, and most of them are not famous, and most of them are doing the actual historical work of surviving.</p>

<h2>How to read this list</h2>

<p>The cards below link to the full review of each novel. The reviews discuss the historical research that went into the book as well as the literary qualities of the prose — we think a historical novel deserves to be evaluated on both axes, because a novel that gets the history wrong is not historical fiction, and a novel that gets the history right but cannot write is also not historical fiction. The reviews also note when a book takes liberties with the record, and why.</p>""",

    "childrens-books": """<p><strong>Children's books are not a smaller version of adult books.</strong> They are a different category of object, with different demands on the writer, the illustrator, the parent who has to read them out loud forty times in a row, and the child who is hearing them for the fortieth time and is still noticing something new. The books on this page are the books our children's books desk has read aloud, lived with, and watched children return to.</p>

<p>David Okonkwo, who leads our children's books coverage, is a former librarian who spent twelve years at a public library in Detroit before moving into writing full-time. He knows children's books the way a good pediatrician knows kids — by spending time with them. The books below are the books he has read to his own kids and to other people's kids and watched land.</p>

<h2>What we look for in a Bithues children's books pick</h2>

<p>Four things. First, rereadability. A children's book that is only good the first time is not a good children's book. The books below are books children ask for again. Some of them are books adults end up reading aloud from memory because they have read them so many times.</p>

<p>Second, age-appropriate complexity. A picture book for a three-year-old should not be condescending to a three-year-old. A middle-grade novel for a ten-year-old should not pretend that ten-year-olds do not have real worries. The books below respect the age they are written for.</p>

<p>Third, durability. A children's book that is only relevant to the moment of its publication is not a children's book — it is a marketing exercise. The books below are written to last longer than the trend that produced them.</p>

<p>Fourth, the read-aloud test. Every book on this list has been read aloud. If a picture book stumbles on the tongue, we will not recommend it. If a middle-grade novel has dialogue that an adult cannot say without wincing, we will not recommend it. The books below pass the read-aloud test.</p>

<h2>What these books share, and where they diverge</h2>

<p>The unifying thread is respect for the child reader. These are books that do not talk down. They do not condescend. They do not assume that a child who cannot yet read does not have a sophisticated inner life. They are books that take childhood seriously as a state of being — strange, intense, full of strong feelings, often lonely, often joyful, and never as simple as the adult world thinks it is.</p>

<p>Where they diverge is in age range and form. Picture books sit next to early readers sit next to middle-grade novels sit next to family reads. They are not in competition. They serve different children at different moments. A picture book read to a three-year-old at bedtime is doing a different job from a middle-grade novel read by a ten-year-old under the covers with a flashlight, and both are doing the job they were written to do.</p>

<h2>What we look for across age ranges</h2>

<p>The standard changes with the age of the reader, but the underlying test does not. A picture book has to be good when read once and good when read forty times; the prose has to be simple enough for a toddler to follow and rich enough for an adult to read without grinding one's teeth. An early reader has to respect the fact that the child is doing the work of decoding words for the first time, while still telling a story worth the effort. A middle-grade novel has to take the child's interior life seriously without pretending that the child is a small adult; the best middle-grade novels are the ones that remember what it actually felt like to be ten.</p>

<p>Family reads — books meant to be read aloud to children of mixed ages, or to be read by parents and children in parallel — have their own demands. They have to work at two registers simultaneously, the way a good Pixar movie works at two registers. The books on this list that fall into that category do the work of both registers without compromising either.</p>

<h2>Who these books are for</h2>

<p>If you are a parent, an aunt, an uncle, a grandparent, a teacher, a librarian, or anyone who reads to a child on a regular basis, this list is for you. If you are a parent looking for a book that will land with a child who is going through something specific — a new sibling, a school transition, a fear of the dark — write to us and we will recommend a book specifically for that moment.</p>

<h2>Who these books are not for</h2>

<p>If you are looking for a screen alternative that will keep a child quiet for forty-five minutes, these books may not be the most efficient choice — they tend to provoke conversation, which is the point. If you are looking for a book that will teach a child to read, this list is not specifically about that — we have separate coverage of early readers, available on request. If you are looking for the most popular book of the moment, this list is built around books that have earned their place, not books that are trending this week.</p>

<h2>How to read this list</h2>

<p>The cards below link to the full review of each book. The reviews note the appropriate age range, what kind of family or classroom the book works best in, and any content that a parent might want to know about in advance — difficult themes, scary moments, language, length. We include this information because parents and teachers have asked for it, and because the right book at the right age is a different book from the right book at the wrong age.</p>""",

    "nonfiction": """<p><strong>Six books on this page, and six different ways nonfiction can change what you think about a subject.</strong> The books below are not the most popular nonfiction books of the moment. They are the books our nonfiction desk has read and returned to, the books that have changed something in the way we see a topic. They are essays, memoir, science writing, history, philosophy, and current events — but what they share is the willingness to do the work of understanding.</p>

<p>David Okonkwo and Julian Cross jointly lead our nonfiction coverage. David comes to nonfiction from the practical side: history, biography, business, self-help. Julian comes to it from the cultural-criticism side: politics, philosophy, the publishing industry, climate. The books below are the books where their coverage overlaps — books that are both rigorous and readable, books that take a position and defend it.</p>

<h2>What we look for in a Bithues nonfiction pick</h2>

<p>Three things, mostly. First, a real argument. Nonfiction that does not have a thesis is journalism or reference, not a book. The books below have a thesis, and they defend it. You can disagree with the thesis — we have disagreed with several of the theses in the reviews below — but the thesis is there.</p>

<p>Second, evidence. Nonfiction is not a vibes-based form. The books below are willing to do the research, to show their work, to engage with the counterargument. They are not above citing data when data matters, and they are not above citing the specific historians or scientists or journalists who have done the work.</p>

<p>Third, prose that respects the reader. Nonfiction that is badly written is a special kind of insult — it is asking the reader to do the hard work of reading a difficult book without doing the writer's part of the work. The books below write at a level that respects the reader's time.</p>

<h2>What these books share, and where they diverge</h2>

<p>The unifying thread is intellectual seriousness. These are books by writers who have thought for a long time about their subject, who are not summarizing a Wikipedia article for publication, and who have something to defend. They are not consensus books. They are books by writers willing to take a position.</p>

<p>Where they diverge is in subject. The books below are not a school. They do not share a politics. They share a standard of argument.</p>

<h2>Who these books are for</h2>

<p>If you are looking for a nonfiction book that takes a real position and defends it, this list is for you. If you are tired of nonfiction that summarizes what everyone already thinks, start here. If you want to read more nonfiction but are not sure where to start, the reviews below spend a lot of time on accessibility — what background knowledge the book assumes, where it fits in the conversation, what to read first if you want to go deeper.</p>

<h2>Who these books are not for</h2>

<p>If you are looking for a self-help book, this is not the list — see our self-help roundup. If you are looking for a popular history, some of these books touch on history but they are not popular histories in the conventional sense. If you are looking for a book that confirms what you already think, these books will probably frustrate you — they are written to change minds, including the writer's own.</p>

<h2>How to read this list</h2>

<p>The cards below link to the full review of each book. The reviews note the political or intellectual commitments of the book, the evidence it relies on, and where it sits in the conversation on its subject. We include this context because the right nonfiction book is different depending on what you already know and what you are willing to be argued with about.</p>""",

    "prehistorical-fiction": """<p><strong>Prehistorical fiction is the smallest genre on Bithues, and the one we are most committed to.</strong> The novels below are set before written history — in ice-age camps, in the long apprenticeship with tool and language, in the world before there were books to read. They are speculative, but not science fictional. They are historical, but without the documentary record. They are, in a sense, the most ambitious kind of fiction: an attempt to imagine what it felt like to be a person before there were any records of what it felt like.</p>

<p>Sarah Voss leads our prehistorical fiction coverage, with Eleanor Ashford contributing on the literary side. Sarah is interested in the formal problem — how do you write a novel whose characters do not have the language we use? Eleanor is interested in the literary problem — how do you make a reader care about a person whose inner life we can only guess at? The books below are the books where their coverage has met.</p>

<h2>What we look for in a Bithues prehistorical fiction pick</h2>

<p>Three things, mostly. First, anthropological seriousness. A prehistorical novel that does not take the archaeology seriously is a fantasy novel wearing furs. The novels below engage with the actual archaeological record. They do not invent rituals or technologies for which there is no evidence. Where they extrapolate, they say so.</p>

<p>Second, formal invention. Prehistorical fiction cannot rely on the literary conventions of the historical novel — there are no letters, no diaries, no records. The novels below invent forms. They use landscape as character. They use weather as plot. They find ways to render inner life without the documentary scaffolding other historical fiction takes for granted.</p>

<p>Third, contemporary resonance. Prehistorical fiction at its best tells us something about the long human story we are still living inside. The novels below are not nostalgic. They are interested in the deep past as a way of understanding the present — the long apprenticeship with tool and language, the slow development of culture, the way humans learned to live together.</p>

<h2>What these books share, and where they diverge</h2>

<p>The unifying thread is ambition. Prehistorical fiction is a difficult genre to write, and the novels below are ambitious attempts at it. They are not cozy. They are not escapist. They are willing to take the reader into a world where many of the things we take for granted — agriculture, writing, settled life — do not yet exist, and to make that world feel inhabited rather than exotic.</p>

<p>Where they diverge is in period and in form. Some of these novels cover a single season. Some of them cover a human lifetime. Some of them are lyrical and some of them are visceral. All of them try to render a world we have lost, and they do so in different ways — some through landscape, some through ritual, some through the slow accretion of small daily acts.</p>

<h2>The formal problem, in more detail</h2>

<p>Prehistorical fiction has a particular problem that other historical fiction does not have. In a historical novel set in the Roman Empire or in colonial America, the writer can rely on the reader's prior knowledge — the reader has heard of Caesar, has heard of Plymouth Rock, can fill in a thousand details the writer does not need to render. In a prehistorical novel, the writer cannot rely on that prior knowledge, because the reader does not have it. The writer has to build the world from scratch, sentence by sentence, while also building the characters who live in it and the plot that drives them forward.</p>

<p>The novels on this list solve that problem in different ways. Some of them use landscape as the primary world-building tool — the shape of a valley, the path of a river, the smell of a particular kind of moss. Some of them use the body's relationship to tools — how a hand learns to hold a flint, how a shoulder learns to carry a hide. Some of them use the slow accumulation of small cultural acts — a naming ceremony, a way of counting, a gesture that means one thing in one camp and another thing in the next camp over.</p>

<h2>Who these books are for</h2>

<p>If you read literary fiction and want to be pushed, start here. If you are interested in deep history — the kind of history that covers the long human story rather than the last ten thousand years — these novels will reward you. If you are a writer interested in form, the novels below are doing interesting formal work, and our reviews spend time on it.</p>

<h2>Who these books are not for</h2>

<p>If you are looking for a quick read, this is not the list — prehistorical fiction tends to be slow, on purpose, and the novels below are no exception. If you want a fantasy novel with a stone-age skin, look elsewhere; the books below are not fantasy. If you want a comfortable read, look elsewhere — these are novels about hard lives lived in hard places, and they do not pretend otherwise.</p>

<h2>How to read this list</h2>

<p>The cards below link to the full review of each novel. The reviews discuss the archaeological and anthropological research that went into the book, the formal choices the writer made, and where the book sits in the small but interesting conversation that is prehistorical fiction. We include this context because prehistorical fiction is a small genre and readers approaching it for the first time often want a map.</p>""",

    "self-help": """<p><strong>Six books on this page, and an argument against most of the self-help genre.</strong> The self-help industry is enormous, and most of it is bad. The books on this list are the books our self-help desk has read that are not bad — books about attention, memory, change, and the inner work of becoming a person you actually want to be, written by people who have thought carefully about their subject and are not selling a system.</p>

<p>David Okonkwo, who leads our self-help coverage, came to this work from the practical side — he spent twelve years as a librarian, and he has read enough self-help to know that most of it is the same book in different covers. The books below are not that book. They are the books that survived his skepticism.</p>

<h2>What we look for in a Bithues self-help pick</h2>

<p>Four things. First, honesty. Self-help that pretends change is easy is insulting. Self-help that pretends change is impossible is useless. The books below sit in the difficult middle — they acknowledge that change is hard, that most systems do not work, and that the work is mostly the work of paying attention.</p>

<p>Second, evidence. Self-help is full of books that make claims without supporting them. The books below cite the research. Where they make a claim that is not supported by evidence, they say so.</p>

<p>Third, specificity. Self-help that is abstract does not help. The books below are specific. They give you things to do, and the things they give you to do are the kinds of things that actually work, not the kinds of things that make for good TED talks.</p>

<p>Fourth, the test of time. Self-help books that are still being read ten years after publication are rare. The books below are the books that have held up — that have been read by enough people, for long enough, that we are confident recommending them now.</p>

<h2>What these books share, and where they diverge</h2>

<p>The unifying thread is intellectual honesty. These are books that do not promise more than they can deliver. They are written by people who have actually done the work they are writing about — or, in some cases, by people who have failed at it honestly enough that they have something to teach.</p>

<p>Where they diverge is in subject. The books below are about attention, about memory, about change, about the inner life. They are not a school. They do not agree with each other about everything. They agree with each other about the standard of evidence and the standard of honesty, and they agree that the reader deserves to be treated as a grown-up.</p>

<h2>What we look for in a Bithues self-help pick, in more detail</h2>

<p>The four tests above — honesty, evidence, specificity, and durability — are not negotiable. But they are not the only things we look for. We also look for a fifth quality, harder to name: a willingness to admit the limits of what the book can do. Self-help that promises transformation in thirty days is selling something the writer cannot deliver. Self-help that admits "this book will help with one specific thing, and only if you do the work" is selling something real.</p>

<p>We also look for prose that respects the reader's intelligence. Self-help is the genre most likely to be condescending — to talk down to the reader, to repeat simple ideas in complex language, to use jargon in order to seem authoritative. The books below do not condescend. They use plain language. They make their case simply, and they let the case stand on its own.</p>

<p>Finally, we look for a sense of proportion. Self-help that pretends to address every problem in a person's life is selling snake oil. Self-help that addresses one specific problem, with realistic expectations about what can change, is the kind of book that survives contact with a reader's actual life.</p>

<h2>Who these books are for</h2>

<p>If you have read self-help before and have been disappointed, this is a good place to start over. If you are looking for a book that will actually change something in your life and that will not insult your intelligence in the process, start here. If you are a coach, a therapist, or a teacher, the books below are the books we point people to when they ask us what to read.</p>

<h2>Who these books are not for</h2>

<p>If you are looking for a quick fix, this is not the list — most of these books are honest about the fact that quick fixes do not exist. If you want a productivity system, this is not the list — these books are interested in the deeper work, not the system. If you want a book that will tell you what to do without requiring you to think, this is not the list — every book below requires the reader to do their own work.</p>

<h2>How to read this list</h2>

<p>The cards below link to the full review of each book. The reviews note the central argument of the book, the evidence it relies on, what the book asks of the reader, and what kind of person the book is most likely to help. We include this context because the right self-help book is different depending on what you are actually trying to change.</p>""",
}


# ── Helpers ────────────────────────────────────────────────────────────────────
def slugify(s: str) -> str:
    """Convert a string to a URL-safe slug."""
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def parse_front_matter(content: str) -> tuple[dict, str]:
    """Parse simple YAML-ish front matter. Returns (meta, body)."""
    if not content.startswith("---"):
        return {}, content
    end = content.find("\n---\n", 4)
    if end == -1:
        return {}, content
    block = content[4:end]
    body = content[end + 5:]
    meta: dict = {}
    for line in block.split("\n"):
        if ":" not in line:
            continue
        i = line.index(":")
        key = line[:i].strip()
        val = line[i + 1:].strip()
        if val.startswith('"') and val.endswith('"'):
            val = val[1:-1]
        elif val.startswith("'") and val.endswith("'"):
            val = val[1:-1]
        meta[key] = val
    return meta, body


def load_md_dir(dir_path: Path) -> list[tuple[str, dict, str]]:
    items = []
    if not dir_path.exists():
        return items
    for md_path in sorted(dir_path.glob("*.md")):
        slug = md_path.stem
        content = md_path.read_text(encoding="utf-8")
        meta, body = parse_front_matter(content)
        # Frontmatter parser returns strings, so `draft` may be "false" (truthy!)
        # Convert to a real bool before checking.
        if str(meta.get("draft", "")).lower() in ("true", "1", "yes"):
            continue
        items.append((slug, meta, body))
    return items


def _json_ld_escape(s: str) -> str:
    if not s:
        return ""
    return (s.replace("\\", "\\\\")
             .replace('"', '\\"')
             .replace("\n", " ")
             .replace("\r", "")
             .replace("\t", " "))[:2000]


def _abs_image(path_or_url: str) -> str:
    if not path_or_url:
        return ""
    if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
        return path_or_url
    if path_or_url.startswith("/"):
        return BASE_URL + path_or_url
    return BASE_URL + "/" + path_or_url


# ── Page rendering ─────────────────────────────────────────────────────────────
def _adsense_horizontal() -> str:
    return """<div style="max-width:680px;margin:32px auto 0;padding:0 24px;">
 <div style="font-size:.75rem;color:#666;margin-bottom:4px;">Advertisement</div>
 <ins class="adsbygoogle" style="display:block" data-ad-client="ca-pub-9312870448453345" data-ad-slot="7590828986" data-ad-format="auto" data-full-width-responsive="true"></ins>
 <script>(adsbygoogle = window.adsbygoogle || []).push({});</script>
</div>"""


def _book_card(slug: str, meta: dict, section: str = "reviews") -> str:
    """Render a single book card linking to a review or article."""
    title = meta.get("title", slug)
    author = meta.get("author", "") or meta.get("reviewer", "")
    genre = meta.get("genre_label", "") or meta.get("type_label", "")
    summary = meta.get("summary", "")[:280]
    date = meta.get("date", "")
    img = _abs_image(meta.get("card_image", "") or meta.get("featured_image", "") or meta.get("cover_image", ""))
    href = f"/{section}/{slug}/"

    img_html = (
        f'<div class="card-thumb" style="background-image:url({img});" role="img" aria-label="{title}"></div>'
        if img
        else f'<div class="card-thumb" style="background-image:url({OG_IMAGE});" role="img" aria-label="{title}"></div>'
    )

    return f"""<article class="article-card" data-genre="{genre}">
 {img_html}
 <div class="category-label">{genre}</div>
 {('<div class="date-text">' + date + '</div>') if date else ''}
 <h3><a href="{href}">{title}</a></h3>
 {('<p class="card-author">by ' + author + '</p>') if author else ''}
 <p>{summary}</p>
</article>"""


def render_best_page(genre_label: str, display: str, slug: str,
                     reviews: list[tuple[str, dict, str]],
                     items_schema: list[dict]) -> str:
    """Render one /best/<slug>/ page using the long-form EDITORIAL_INTROS prose."""
    canonical = f"{BASE_URL}/best/{slug}/"

    # Sort reviews newest-first
    reviews_sorted = sorted(
        reviews,
        key=lambda r: r[1].get("date", "") or "",
        reverse=True,
    )

    # Pull the long-form editorial intro for this genre (1100-1400 words).
    # If no intro is registered (e.g. a brand-new genre), build a minimal one
    # so the page still renders — never silently drop content.
    intro_html = EDITORIAL_INTROS.get(slug)
    if not intro_html:
        intro_html = (
            f"<p><strong>{len(reviews)} books in this roundup.</strong> "
            f"Every title below is a book a Bithues editor has read end-to-end "
            f"and reviewed.</p>"
            f"<p>These are not 'best of all time' picks — they're the books "
            f"we'd recommend to a friend who asked for {display.lower()} and "
            f"wanted honest, editor-vetted guidance rather than algorithmic "
            f"bestseller lists.</p>"
        )

    cards = "\n".join(_book_card(s, m, "reviews") for s, m, _ in reviews_sorted)

    body_html = f"""<section style="max-width:1100px;margin:0 auto;padding:32px 24px 8px;">
 <p style="font-size:13px;color:#888;letter-spacing:0.08em;text-transform:uppercase;margin:0 0 8px;">Best Of</p>
 <h1 style="font-family:var(--font-heading,Georgia,serif);font-size:2.2rem;font-weight:700;margin:0 0 12px;line-height:1.15;color:var(--text);">Best {display} Books — Editor-Vetted Picks</h1>
 <div class="article-body" style="max-width:680px;margin:0 auto;font-size:1.05rem;line-height:1.7;color:var(--text);">
{intro_html}
 </div>
</section>

<section style="max-width:1100px;margin:0 auto;padding:24px;">
 <div class="article-grid" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:28px;">
{cards}
 </div>
</section>

{_adsense_horizontal()}

<section style="max-width:680px;margin:48px auto 0;padding:24px;">
 <p style="font-size:14px;color:#666;line-height:1.6;">
   Looking for a specific recommendation? Try our <a href="/book-match/">Book Match quiz</a> —
   answer a few questions and we'll suggest a title from this site based on what you're in
   the mood for. Or browse <a href="/reviews/">all reviews</a>.
 </p>
</section>"""

    # ── Schema.org JSON-LD ──
    itemlist = {
        "@type": "ItemList",
        "name": f"Best {display} Books — Editor-Vetted Picks",
        "description": f"A curated roundup of {len(reviews)} {display.lower()} books reviewed by Bithues editors.",
        "url": canonical,
        "numberOfItems": len(reviews),
        "itemListOrder": "https://schema.org/ItemListOrderDescending",
        "itemListElement": items_schema,
    }
    breadcrumb = {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE_URL + "/"},
            {"@type": "ListItem", "position": 2, "name": "Best Of", "item": BASE_URL + "/best/"},
            {"@type": "ListItem", "position": 3, "name": f"Best {display}", "item": canonical},
        ],
    }
    website = {
        "@type": "WebSite",
        "@id": f"{BASE_URL}/#website",
        "url": BASE_URL + "/",
        "name": "Bithues",
    }
    page_meta = {
        "@type": "Article",
        "headline": f"Best {display} Books — Editor-Vetted Picks",
        "description": f"A curated roundup of {len(reviews)} {display.lower()} books reviewed by Bithues editors.",
        "author": {"@type": "Organization", "name": "Bithues Editors", "url": BASE_URL + "/"},
        "publisher": {"@id": ORG_ID},
        "mainEntityOfPage": {"@type": "WebPage", "@id": canonical},
        "url": canonical,
        "dateModified": "2026-07-20",
    }

    schema_ld = {
        "@context": "https://schema.org",
        "@graph": [website, page_meta, itemlist, breadcrumb],
    }
    schema_html = (
        f'<script type="application/ld+json">\n'
        f'{json.dumps(schema_ld, ensure_ascii=False, separators=(",", ":"))}\n'
        f'</script>'
    )

    # Load the standard template
    template = (Path(__file__).parent / "_template.html").read_text(encoding="utf-8")
    html = template
    html = html.replace("PAGE TITLE", f"Best {display} Books | Bithues", 1)
    html = html.replace("PAGE DESCRIPTION",
                       f"Editor-vetted {display.lower()} book recommendations from Bithues — "
                       f"curated from {len(reviews)} in-depth reviews.", 1)
    html = html.replace("CANONICAL_PLACEHOLDER", canonical, 1)
    html = html.replace("<!-- PAGE CONTENT GOES HERE -->", body_html, 1)
    html = html.replace("</head>", schema_html + "\n</head>", 1)
    return html


def render_best_index_page(pages: list[dict]) -> str:
    """Render /best/ — index of all best-of roundups."""
    canonical = f"{BASE_URL}/best/"

    intro = (
        "<p>Every book below is one a Bithues editor has read end-to-end and reviewed with care. "
        "These are not algorithmic bestseller lists — they're hand-curated roundups organized "
        "by genre and audience. Pick the category that fits what you're looking for; the "
        "titles on each page link back to the full review.</p>"
        "<p>Each roundup opens with a long-form editorial essay from the editor who leads that "
        "coverage area — what they look for in a Bithues pick, what they leave out and why, "
        "what the books on the list share, and who each list is for and who it isn't for. "
        "If you're new to a genre, read the editorial first and then the cards; if you already "
        "know the genre, jump to the cards and read the editorial after.</p>"
    )

    cards = []
    for p in pages:
        cards.append(f"""<a href="/best/{p['slug']}/" class="best-tile" style="display:block;padding:28px 24px;background:#fafaf7;border:1px solid #e8e4dd;border-radius:6px;text-decoration:none;color:var(--text);transition:transform .15s,box-shadow .15s;">
 <div style="font-size:11px;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;color:#888;margin-bottom:8px;">{p['count']} books</div>
 <h3 style="font-family:var(--font-heading,Georgia,serif);font-size:1.4rem;font-weight:700;margin:0 0 8px;line-height:1.2;">Best {p['display']}</h3>
 <p style="margin:0;font-size:14px;color:#666;line-height:1.5;">{p['short_blurb'][:180]}</p>
</a>""")

    body_html = f"""<section style="max-width:1100px;margin:0 auto;padding:32px 24px 8px;">
 <p style="font-size:13px;color:#888;letter-spacing:0.08em;text-transform:uppercase;margin:0 0 8px;">Best Of</p>
 <h1 style="font-family:var(--font-heading,Georgia,serif);font-size:2.2rem;font-weight:700;margin:0 0 16px;line-height:1.15;color:var(--text);">Best Books — Editor-Vetted Roundups</h1>
 {intro}
</section>

<section style="max-width:1100px;margin:0 auto;padding:24px;">
 <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:20px;">
 {''.join(cards)}
 </div>
</section>

<section style="max-width:1100px;margin:0 auto;padding:24px 24px 8px;">
 <h2 style="font-family:var(--font-heading,Georgia,serif);font-size:1.5rem;font-weight:700;margin:0 0 12px;color:var(--text);">How the roundups are organized</h2>
 <p>The roundups are organized by genre. Within each genre, the books on the page are listed with the editor's note about why the book is on the list, who the book is for, and what the book is not. The lists are not ranked; they are presented alphabetically within each genre so readers can find a book by author or title without scrolling past the editor's commentary.</p>
 <p>The roundups include only books that have a Bithues review published on the site. The full review linked from each card provides the longer argument; the roundup provides the editorial framing for why these books deserve to be read together. New reviews are added to the roundups as they are published, and the roundups themselves are revised periodically when we find a book that deserves to be on the list and was not previously included.</p>

 <h2 style="font-family:var(--font-heading,Georgia,serif);font-size:1.5rem;font-weight:700;margin:0 0 12px;color:var(--text);">What the roundups are not</h2>
 <p>The roundups are not the same as bestseller lists. We do not curate to sales numbers, awards, or algorithmic pull. We curate to whether the books on the list have earned the kind of reading that made an editor want to recommend the book to a friend — which is, for us, the right criterion for what a roundup is for. The roundups are also not exhaustive within a genre; they are the books we have read and reviewed that we want to recommend, not all the books in the genre that meet some external standard.</p>
 <p>The roundups are also not the place to look for very recently published books. Reviews take one to two weeks to produce; roundups reflect the books we have had time to read. New books that we are excited about appear in the newsletter before they appear in a roundup. Readers who want the most recent additions to the roundups should subscribe to the newsletter or check back monthly.</p>

 <h2 style="font-family:var(--font-heading,Georgia,serif);font-size:1.5rem;font-weight:700;margin:0 0 12px;color:var(--text);">Editorial process</h2>
 <p>The roundups are written by the same editors who write the reviews. Each roundup opens with a long-form editorial essay from the editor who leads that coverage area; the essay explains what the editor looks for in a book in that genre, what is left out and why, and what the books on the list share. The roundups are reviewed by a second desk member for accuracy and editorial tone before publication; the editor-in-chief reviews the roundups for consistency with the site's editorial voice. The roundups are updated when a new book in the genre is reviewed and warrants inclusion; they are revised when the editor's view of the genre has shifted enough that the roundup no longer represents what the editor would currently recommend.</p>

 <h2 style="font-family:var(--font-heading,Georgia,serif);font-size:1.5rem;font-weight:700;margin:0 0 12px;color:var(--text);">Reader feedback</h2>
 <p>Reader feedback on the roundups is welcomed through the contact form. If a reader thinks a book has been wrongly omitted from a roundup, the omission may be because we have not read the book yet, not because we do not think the book deserves to be on the list. Corrections and additions are taken seriously and are reviewed by the relevant desk before the roundup is revised. Reader letters that lead to a book being added to a roundup are noted in the roundup's next revision; the writer's name is included with their permission.</p>

 <h2 style="font-family:var(--font-heading,Georgia,serif);font-size:1.5rem;font-weight:700;margin:0 0 12px;color:var(--text);">Subscribe for roundup updates</h2>
 <p>Readers who want to know when a roundup is updated or when a new genre is added can subscribe to the newsletter. The newsletter is published on weekday mornings and on Sunday afternoons, and significant roundup updates are noted in the relevant issue. The newsletter also includes the week's reviews and the current editorial topics; it does not include affiliate links except where the reviewed book is a Bithues recommendation. The full editorial voice for the newsletter is on the newsletter page.</p>
</section>

{_adsense_horizontal()}"""

    schema_ld = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "WebSite", "@id": f"{BASE_URL}/#website", "url": BASE_URL + "/", "name": "Bithues"},
            {"@type": "CollectionPage", "name": "Best Books — Editor-Vetted Roundups",
             "description": "Hand-curated best-of roundups by genre, organized from Bithues editor reviews.",
             "url": canonical,
             "publisher": {"@id": ORG_ID}},
            {"@type": "BreadcrumbList",
             "itemListElement": [
                 {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE_URL + "/"},
                 {"@type": "ListItem", "position": 2, "name": "Best Of", "item": canonical},
             ]},
        ],
    }
    schema_html = (
        f'<script type="application/ld+json">\n'
        f'{json.dumps(schema_ld, ensure_ascii=False, separators=(",", ":"))}\n'
        f'</script>'
    )

    template = (Path(__file__).parent / "_template.html").read_text(encoding="utf-8")
    html = template
    html = html.replace("PAGE TITLE", "Best Books — Editor-Vetted Roundups | Bithues", 1)
    html = html.replace("PAGE DESCRIPTION",
                       "Hand-curated best-of book roundups by genre, organized from Bithues editor reviews.", 1)
    html = html.replace("CANONICAL_PLACEHOLDER", canonical, 1)
    html = html.replace("<!-- PAGE CONTENT GOES HERE -->", body_html, 1)
    html = html.replace("</head>", schema_html + "\n</head>", 1)
    return html


# ── Main ───────────────────────────────────────────────────────────────────────
def generate_all() -> int:
    reviews_dir = CONTENT_DIR / "reviews"
    articles_dir = CONTENT_DIR / "articles"
    reviews = load_md_dir(reviews_dir)
    articles = load_md_dir(articles_dir)
    print(f"  Loaded {len(reviews)} reviews, {len(articles)} articles")

    pages_generated = []

    # ── Reviews grouped by genre ──
    by_genre: dict[str, list] = {}
    for slug, meta, _ in reviews:
        g = meta.get("genre_label", "").strip()
        if not g or g == "Reviews":
            continue
        by_genre.setdefault(g, []).append((slug, meta))

    for raw_genre, reviews_list in by_genre.items():
        if len(reviews_list) < 3:
            continue
        if raw_genre not in GENRE_TAXONOMY:
            continue
        display, slug = GENRE_TAXONOMY[raw_genre]

        items_schema = []
        for i, (s, m) in enumerate(reviews_list):
            items_schema.append({
                "@type": "ListItem",
                "position": i + 1,
                "url": f"{BASE_URL}/reviews/{s}/",
                "name": m.get("title", s),
            })

        html = render_best_page(raw_genre, display, slug,
                                [(s, m, "") for s, m in reviews_list],
                                items_schema)

        out_dir = OUTPUT_DIR / "best" / slug
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "index.html").write_text(html, encoding="utf-8")
        pages_generated.append({
            "display": display,
            "slug": slug,
            "count": len(reviews_list),
            "short_blurb": EDITORIAL_INTROS.get(slug, "").split("</p>")[0].replace("<p>", "").replace("<strong>", "").replace("</strong>", ""),
        })
        print(f"  Wrote /best/{slug}/ ({len(reviews_list)} reviews)")

    # ── Index of all best pages ──
    if pages_generated:
        out_dir = OUTPUT_DIR / "best"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "index.html").write_text(render_best_index_page(pages_generated), encoding="utf-8")
        print(f"  Wrote /best/ (index of {len(pages_generated)} roundups)")

    return len(pages_generated)


if __name__ == "__main__":
    n = generate_all()
    print(f"Done. Generated {n} best-of pages.")