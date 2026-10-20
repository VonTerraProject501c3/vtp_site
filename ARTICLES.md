# Articles: what every VTP article carries

**VTP's standard for every article, wherever it is published.** Adopted by Colton Williams,
Founder & Executive Director, on 2026-10-20. Anyone writing an article for VTP, person or agent,
starts here: on the website, in a shared document or PDF, or on another site.

On the website, every page in the **Articles** menu meets it, and `tools/check_site.py` fails
the build when an article page is missing a part, so a new article cannot ship in a different
shape.

The standard is not invented here. It takes its parts from two public standards and from
`vtp_voice`:

- **The Trust Project, Trust Indicators** (thetrustproject.org/trust-indicators). Used by
  news publishers to show readers who wrote a piece, what kind of piece it is, where its facts
  come from, how it was reported, and how to report an error.
- **Google Search Central, Article structured data**
  (developers.google.com/search/docs/appearance/structured-data/article). Gives search engines and
  link previews the headline, the dates, and the author as a Person with a name, a job title and
  a profile page.
- **`vtp_voice`**: `guidelines/editorial-styles.md` (Lead, Eyebrow, References, ISO dates) and
  `guidelines/voice-and-tone.md` (point first, APA 7 citations, no arrows).

## The parts, in page order

| # | Part | Markup | Rule | From |
|---|---|---|---|---|
| 1 | Label | `<p class="article-label">` | One of: News, Guide, Report, Analysis, Opinion. | Trust Project, Labels |
| 2 | Headline | the page's one `<h1>` | Same text as the JSON-LD `headline`. | Google, `headline` |
| 3 | Standfirst | `<p class="sub-lede">` | One sentence: what the reader gets. | Publishing convention |
| 4 | Byline | `<div class="byline">` | Headshot, name linked to the author's `team-<slug>.html`, role, published date. Name, role and headshot must match the author's team page exactly. | Trust Project, Journalist Expertise; Google, `author` |
| 5 | Dates | `<time datetime="YYYY-MM-DD">` in the byline | Published date. Add `Updated YYYY-MM-DD` when the text changes after publishing. | Google, `datePublished` / `dateModified`; voice, ISO dates |
| 6 | Lead | `<p class="lead">` | Point first. A reader who stops here has the takeaway. | voice, Lead |
| 7 | Body | `<h2>` sections | APA 7 in-text citations for every claim from a source. | voice, Sourcing |
| 8 | How we checked this | `<section class="article-methods">` | What was checked, against what, and on what date. | Trust Project, Methods |
| 9 | About the author | `<section class="article-author">` | Headshot, name, role and the one-line bio from the author's `team.html` card, linked to the full bio. | Trust Project, Journalist Expertise |
| 10 | Corrections | `<section class="article-feedback">` | How to report an error (contact@vonterraproject.org). | Trust Project, Actionable Feedback |
| 11 | Sources | `<section class="sources">` with an `<ol>` | APA 7 reference list. | Trust Project, References; voice, References |
| 12 | Structured data | JSON-LD `Article`, `NewsArticle` or `Report` | `headline`, `description`, `datePublished`, `dateModified`, `author` (Person: `name`, `jobTitle`, `url`, `image`), `publisher` pointing at `#organization`. | Google, Article structured data |
| 13 | Listing | Articles menu in `_partials.js`, `sitemap.xml` | Newest first in the menu. Run `node tools/sync_shell.mjs` after editing `_partials.js`. | |

Two Trust Indicators are editorial practice rather than parts of a page (Locally Sourced and
Diverse Voices), and the third (Best Practices: who funds us and how we work) lives on
`about.html` and `documents.html`.

## Outside the website

A Google Doc, a PDF, a Claude Doc or a post on another site carries parts 1 to 11 in the same
order: label, headline, standfirst, byline with the headshot, name, role and date, lead, body with
APA citations, how we checked this, about the author, corrections, sources. Parts 12 and 13
(structured data and the menu listing) apply only on the website. Nothing checks these copies
automatically, so check them against the table by hand before they go out. When the piece is also
on the website, link to the website version so corrections reach every reader.

## The author

- The author is a person on `team.html`. Their **name** and **role** come from the team page,
  which renders `canonical-facts.json` `leadership[]`. Do not type a role by hand; copy it.
- The **headshot** is the one already on their team page (`website_images/team-<slug>.jpg`).
- More than one author: one `byline` entry and one JSON-LD `author` entry for each.
- Someone not on `team.html` cannot be credited until they have a team page. Add them first.

## Corrections

When a published article is wrong, fix the text, set **Updated** in the byline and
`dateModified` in the JSON-LD to the date of the fix, and add one line under "How we checked
this" that says what changed. Do not quietly rewrite.

## Making a new article

1. Copy the newest article page (`dod-8140-nonprofit-certifications-2026.html`). Its styles live
   in `css/style.css` under **Articles**, so the copy looks the same without page-scoped CSS.
2. Replace the label, headline, standfirst, author, dates, body, methods, sources and the JSON-LD.
3. Add the page to the top of the Articles menu in `_partials.js`, then `node tools/sync_shell.mjs`.
4. Add it to `sitemap.xml`.
5. `python3 tools/check_site.py` and `python3 tools/check_governance.py`. A new page always
   carries the shared footer sentence, so the status-language baseline needs re-recording
   (`--update-baseline`); say in the commit that no new status wording was added.

## Pages published before this standard

`google-org-award-2026.html` (News) and `flyspacea-impact-2026.html` (Report) were published
before the standard, and both were written by Colton Williams. They were brought up to it on
2026-10-20. Published dates come from the deployment history: the Google.org page went live on
2026-10-20, and the FlySpaceA report on 2026-06-14, updated on 2026-09-11. The report keeps its own
design and adds the closing parts after its last section (`.article-close`).
