#!/usr/bin/env python3
"""Static checks for the VTP website. No dependencies, no build step.

Run locally before pushing:
    python3 tools/check_site.py

Exit 0 = clean. Exit 1 = at least one ERROR. Warnings never fail the build.

Every check here exists because the problem it catches was actually found on this site.
`main` is production — GitHub Pages rebuilds vonterraproject.org on every push — so there is
no staging environment to catch these later.
"""

from __future__ import annotations

import html
import json
import os
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parent.parent
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr"}
SKIP_DIRS = {".git", ".github", "build", "node_modules", "tools"}

# Brand rule (vtp_voice guidelines/voice-and-tone.md, Punctuation): no arrows in copy, ever.
# A link says where it goes; "Read the announcement ->" is decoration. Founder, 2026-10-19.
# Covers the arrow block, the arrow dingbats, guillemets and angle quotes used as arrows, the
# small triangles used as carets, and their HTML entities and CSS escapes.
ARROW_CHARS = "\u2190-\u21ff\u27f0-\u27ff\u2794-\u27bf\u2b00-\u2b2f\u00ab\u00bb\u2039\u203a\u25b2-\u25c5"
ARROWS = re.compile(
    "[" + ARROW_CHARS + "]"
    r"|&(?:[lrudh]arr|[lrudh]Arr|[lr]aquo|[lr]saquo|[lr]arrw|[lr]arrhk|xrarr|xlarr|blacktriangle(?:down|left|right)?|triangle(?:down|left|right)?);"
    r"|&#(?:x(?:21[9a-f][0-9a-f]|27[9a-f][0-9a-f]|2b[0-2][0-9a-f]|203[9a]|a[b]|bb|25b[2-9a-f]|25c[0-5])|8592|8593|8594|8595|8596|8249|8250|171|187);",
    re.I)
CSS_ARROWS = re.compile(r"[" + ARROW_CHARS + r"]|\\(?:0{0,2}21[9a-f][0-9a-f]|0{0,2}27[9a-f][0-9a-f]|0{0,2}25b[2-9a-f]|0{0,2}25c[0-5]|0{0,2}203[9a]|0{0,4}a[b]|0{0,4}bb)\b", re.I)


def blank(text: str, pattern: str) -> str:
    """Blank out matches of `pattern` (comments) but keep their newlines, so line numbers hold."""
    return re.sub(pattern, lambda m: re.sub(r"[^\n]", " ", m.group(0)), text, flags=re.S)

errors: list[str] = []
warnings: list[str] = []


def err(page: Path, msg: str) -> None:
    errors.append(f"{page.relative_to(ROOT)}: {msg}")


def warn(page: Path, msg: str) -> None:
    warnings.append(f"{page.relative_to(ROOT)}: {msg}")


def pages() -> list[Path]:
    out = []
    for p in sorted(ROOT.rglob("*.html")):
        if any(part in SKIP_DIRS for part in p.relative_to(ROOT).parts):
            continue
        out.append(p)
    return out


class Doc(HTMLParser):
    """Collects structure while checking nesting."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, tuple[int, int]]] = []
        self.nesting: list[str] = []
        self.ids: dict[str, int] = {}
        self.imgs: list[tuple[dict, int]] = []
        self.links: list[tuple[dict, int]] = []
        self.headings: list[tuple[int, int]] = []
        self.title = ""
        self.metas: list[dict] = []
        self.has_lang = False
        self.has_charset = False
        self.has_viewport = False
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        line = self.getpos()[0]

        if tag == "html":
            self.has_lang = bool(a.get("lang"))
        if tag == "meta":
            self.metas.append(a)
            if "charset" in a:
                self.has_charset = True
            if a.get("name") == "viewport":
                self.has_viewport = True
        if tag == "title":
            self._in_title = True
        if tag == "img":
            self.imgs.append((a, line))
        if tag == "a":
            self.links.append((a, line))
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.headings.append((int(tag[1]), line))
        if "id" in a:
            self.ids[a["id"]] = self.ids.get(a["id"], 0) + 1

        if tag not in VOID:
            self.stack.append((tag, self.getpos()))

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        if tag in VOID:
            return
        if not self.stack:
            self.nesting.append(f"stray </{tag}> at line {self.getpos()[0]}")
            return
        if self.stack[-1][0] == tag:
            self.stack.pop()
            return
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                for unclosed, pos in self.stack[i + 1:]:
                    self.nesting.append(f"unclosed <{unclosed}> opened line {pos[0]}")
                del self.stack[i:]
                return
        self.nesting.append(f"stray </{tag}> at line {self.getpos()[0]}")

    def handle_data(self, data):
        if self._in_title:
            self.title += data


def resolve(page: Path, href: str) -> Path | None:
    """Map an href to a file on disk, or None if it isn't a local file ref."""
    u = urlparse(href)
    if u.scheme or u.netloc:
        return None
    path = unquote(u.path)
    if not path:
        return None
    base = ROOT if path.startswith("/") else page.parent
    target = (base / path.lstrip("/")).resolve()
    if target.is_dir():
        target = target / "index.html"
    return target


# --- articles (ARTICLES.md) ---
# Every page in the Articles menu carries the same parts: label, byline with the author's
# headshot, name and role, dates, methods, author box, corrections line, sources, and Article
# JSON-LD. The parts come from the Trust Project's Trust Indicators and Google's Article
# structured data; ARTICLES.md lists them. The byline is checked against the author's team page,
# so a role typed by hand cannot drift from the one the site already renders from the record.
SITE = "https://vonterraproject.org/"
ARTICLE_LD_TYPES = {"Article", "NewsArticle", "Report", "AnalysisNewsArticle", "BlogPosting"}
ARTICLE_LABELS = {"News", "Guide", "Report", "Analysis", "Opinion"}
ARTICLE_LD_KEYS = ("headline", "description", "datePublished", "dateModified", "author", "publisher")
# Published before ARTICLES.md and with no named author. Warned about on every run until someone
# names the authors and the page is brought up to standard; then remove it from this set.
ARTICLES_BEFORE_STANDARD = {"google-org-award-2026.html", "flyspacea-impact-2026.html"}
ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}$")


def text(fragment: str) -> str:
    """Visible text of an HTML fragment, entities decoded, whitespace collapsed."""
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def block(raw: str, cls: str) -> str | None:
    """Inner HTML of the first element whose class list includes `cls`, or None."""
    m = re.search(r'<([a-z0-9]+)\b[^>]*\bclass="(?:[^"]*\s)?' + re.escape(cls) + r'(?:\s[^"]*)?"[^>]*>', raw)
    if not m:
        return None
    tag = m.group(1)
    if tag in VOID:
        return ""
    depth = 1
    for t in re.finditer(r"<(/?)" + tag + r"\b[^>]*>", raw[m.end():], re.I):
        depth += -1 if t.group(1) else 1
        if depth == 0:
            return raw[m.end():m.end() + t.start()]
    return None


def h1_text(raw: str) -> str:
    m = re.search(r"<h1\b[^>]*>(.*?)</h1>", raw, re.S)
    return text(m.group(1)) if m else ""


def ld_nodes(raw: str):
    for m in re.finditer(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', raw, re.S):
        try:
            data = json.loads(m.group(1))
        except Exception:
            continue                                  # syntax is reported by main()
        stack = [data]
        while stack:
            node = stack.pop()
            if isinstance(node, dict):
                yield node
                stack.extend(node.values())
            elif isinstance(node, list):
                stack.extend(node)


def menu_articles() -> list[str]:
    """Pages linked from the Articles menu in _partials.js, the generator for every page's nav."""
    src = (ROOT / "_partials.js").read_text(encoding="utf-8")
    m = re.search(r">Articles</a>.*?</div>", src, re.S)
    return re.findall(r'href=\\?"([^"\\]+)\\?"', m.group(0)) if m else []


def check_articles(all_pages: list[Path]) -> None:
    menu = menu_articles()
    team_cards = (ROOT / "team.html").read_text(encoding="utf-8")
    for page in all_pages:
        raw = page.read_text(encoding="utf-8", errors="replace")
        is_article = re.search(r'<meta[^>]+property="og:type"[^>]+content="article"', raw)
        name = str(page.relative_to(ROOT))
        if name in menu and not is_article:
            err(page, 'in the Articles menu but not marked <meta property="og:type" content="article">, '
                      "so the article standard (ARTICLES.md) is not being checked on it")
        if not is_article:
            continue
        if name in ARTICLES_BEFORE_STANDARD:
            warn(page, "article published before ARTICLES.md: no named author, byline or sources yet")
            continue

        def need(ok, msg):
            if not ok:
                err(page, f"article standard (ARTICLES.md): {msg}")

        need(name in menu, "not listed in the Articles menu in _partials.js")
        arts = [n for n in ld_nodes(raw) if n.get("@type") in ARTICLE_LD_TYPES]
        need(len(arts) == 1, f"needs exactly one JSON-LD Article node, found {len(arts)}")
        if len(arts) != 1:
            continue
        art = arts[0]
        for key in ARTICLE_LD_KEYS:
            need(art.get(key), f"JSON-LD Article has no {key!r}")
        published, modified = str(art.get("datePublished", "")), str(art.get("dateModified", ""))
        need(ISO_DATE.match(published) and ISO_DATE.match(modified),
             "datePublished and dateModified must be YYYY-MM-DD")
        need(modified >= published, "dateModified is before datePublished")
        need((art.get("publisher") or {}).get("@id") == SITE + "#organization",
             f'publisher must be {{"@id": "{SITE}#organization"}}')
        need(h1_text(raw) == art.get("headline"), "the <h1> and the JSON-LD headline differ")

        label = block(raw, "article-label")
        need(label is not None and text(label) in ARTICLE_LABELS,
             f"needs a <p class=\"article-label\"> reading one of {sorted(ARTICLE_LABELS)}")
        for part in ("sub-lede", "lead", "article-methods", "article-author", "article-feedback", "sources"):
            need(block(raw, part) is not None, f'no element with class "{part}"')
        sources = block(raw, "sources") or ""
        need("<li" in sources, "the sources section has no entries")
        need("contact@vonterraproject.org" in (block(raw, "article-feedback") or ""),
             "the corrections section does not give contact@vonterraproject.org")

        byline = block(raw, "byline")
        need(byline is not None, 'no <div class="byline">')
        byline = byline or ""
        need(f'datetime="{published}"' in byline, f"the byline does not show the published date {published}")
        if modified != published:
            need(f'datetime="{modified}"' in byline, f"the byline does not show the updated date {modified}")

        authors = art.get("author")
        authors = authors if isinstance(authors, list) else [authors] if authors else []
        about = block(raw, "article-author") or ""
        for a in authors:
            if not isinstance(a, dict) or a.get("@type") != "Person":
                need(False, "every JSON-LD author must be a Person with a team page")
                continue
            for key in ("name", "jobTitle", "url", "image"):
                need(a.get(key), f"JSON-LD author has no {key!r}")
            url = str(a.get("url", ""))
            slug = url[len(SITE):] if url.startswith(SITE) else ""
            team = ROOT / slug
            if not (slug.startswith("team-") and team.exists()):
                need(False, f"author url {url!r} is not a team page on this site")
                continue
            tp = team.read_text(encoding="utf-8")
            role = block(tp, "sub-lede")
            avatar = re.search(r'<img class="bio-band-avatar" src="([^"]+)"', tp)
            need(h1_text(tp) == a.get("name"), f"author name {a.get('name')!r} differs from {slug}")
            need(role is not None and text(role) == a.get("jobTitle"),
                 f"author role {a.get('jobTitle')!r} differs from the one on {slug}")
            need(avatar and unquote(urlparse(str(a.get("image", ""))).path).lstrip("/") == avatar.group(1),
                 f"author image differs from the headshot on {slug}")
            card = re.search(r'<p class="bio">((?:(?!</p>).)*)</p>\s*<a href="' + re.escape(slug) + '"', team_cards, re.S)
            for where, frag in (("byline", byline), ("about-the-author section", about)):
                need(f'href="{slug}"' in frag, f"the {where} does not link to {slug}")
                need(avatar and f'src="{avatar.group(1)}"' in frag, f"the {where} does not show the headshot from {slug}")
                need(a.get("name", "") in text(frag), f"the {where} does not name {a.get('name')!r}")
                need(a.get("jobTitle", "") in text(frag), f"the {where} does not give the role {a.get('jobTitle')!r}")
            need(card and text(card.group(1)) in text(about),
                 f"the about-the-author section does not carry the one-line bio from the team.html card")


def main() -> int:
    all_pages = pages()
    if not all_pages:
        print("no pages found", file=sys.stderr)
        return 1

    titles: dict[str, list[str]] = {}
    linked_to: set[Path] = set()

    for page in all_pages:
        raw = page.read_text(encoding="utf-8", errors="replace")
        doc = Doc()
        doc.feed(raw)
        for tag, pos in doc.stack:
            doc.nesting.append(f"unclosed <{tag}> opened line {pos[0]}")

        # --- structure ---
        for n in doc.nesting:
            err(page, f"malformed HTML: {n}")
        for elem_id, count in doc.ids.items():
            if count > 1:
                err(page, f'duplicate id="{elem_id}" ({count}x) — invalid, breaks anchors and a11y')

        # --- arrows (brand rule) ---
        for m in ARROWS.finditer(blank(raw, r"<!--.*?-->")):
            line = raw.count("\n", 0, m.start()) + 1
            err(page, f"arrow {m.group(0)!r} at line {line}: the brand bans arrows in copy (vtp_voice voice-and-tone, Punctuation)")

        if not raw.lstrip().lower().startswith("<!doctype html>"):
            err(page, "missing <!DOCTYPE html>")
        if not doc.has_lang:
            err(page, "<html> missing lang attribute — screen readers guess the language")
        if not doc.has_charset:
            err(page, "missing <meta charset>")
        if not doc.has_viewport:
            err(page, "missing <meta name=viewport> — page will not scale on mobile")

        # --- title / description ---
        t = doc.title.strip()
        if not t:
            err(page, "missing or empty <title>")
        else:
            titles.setdefault(t, []).append(str(page.relative_to(ROOT)))
        if not any(m.get("name") == "description" for m in doc.metas):
            warn(page, "no meta description — search engines and link previews invent one")

        # --- headings ---
        h1s = [ln for lvl, ln in doc.headings if lvl == 1]
        if len(h1s) == 0:
            warn(page, "no <h1>")
        elif len(h1s) > 1:
            warn(page, f"{len(h1s)} <h1> elements (lines {h1s}) — expected exactly one")
        prev = 0
        for lvl, line in doc.headings:
            if prev and lvl > prev + 1:
                warn(page, f"heading jumps h{prev} to h{lvl} at line {line} — skipped level")
            prev = lvl

        # --- images ---
        for a, line in doc.imgs:
            if "alt" not in a:
                err(page, f'<img> missing alt at line {line} (src={a.get("src","?")})')
            src = a.get("src", "")
            target = resolve(page, src)
            if target is not None and not target.exists():
                err(page, f"image not found at line {line}: {src}")

        # --- links ---
        for a, line in doc.links:
            href = a.get("href")
            if href is None:
                continue
            if href == "#":
                warn(page, f'dead placeholder href="#" at line {line}')
                continue
            if a.get("target") == "_blank":
                rel = (a.get("rel") or "").lower()
                if "noopener" not in rel:
                    err(page, f'target="_blank" without rel="noopener" at line {line} — tabnabbing risk')
            target = resolve(page, href.split("#")[0]) if not href.startswith("#") else None
            if target is not None:
                if target.exists():
                    linked_to.add(target)
                else:
                    err(page, f"broken link at line {line}: {href}")

    # --- JSON-LD validity ---
    # Structured data is consumed by machines without a human reading the page, so a
    # syntactically broken block fails silently and invisibly.
    import json as _json
    for page in all_pages:
        raw = page.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', raw, re.S):
            try:
                _json.loads(m.group(1))
            except Exception as exc:
                err(page, f"invalid JSON-LD: {exc}")

    check_articles(all_pages)

    # --- shell drift ---
    # Superseded by tools/sync_shell.mjs --check, which diffs the ACTUAL rendered
    # shell against _partials.js instead of probing for a handful of strings. The
    # probe version passed while the generator still carried the pre-restructure
    # ribbon, which is exactly the drift it was meant to catch.

    # --- gitignored but tracked ---
    gi = ROOT / ".gitignore"
    if gi.exists():
        import subprocess
        try:
            tracked = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True,
                                     text=True, timeout=20).stdout.split()
            for pat in [l.strip().rstrip("/") for l in gi.read_text().splitlines()
                        if l.strip() and not l.startswith("#")]:
                if "*" in pat or "." == pat:
                    continue
                hits = [t for t in tracked if t == pat or t.startswith(pat + "/")]
                if hits:
                    warnings.append(
                        f".gitignore: '{pat}' is ignored but {len(hits)} file(s) are still "
                        f"tracked — edits to them will be committed while new files are not")
        except Exception:
            pass

    # --- duplicate titles ---
    for t, where in titles.items():
        if len(where) > 1:
            warn(ROOT / "sitemap.xml", f'duplicate <title> "{t}" on: {", ".join(where)}')

    # --- arrows in stylesheets: a CSS `content:` arrow is still an arrow on the page ---
    for css in sorted(ROOT.rglob("*.css")):
        if any(part in SKIP_DIRS for part in css.relative_to(ROOT).parts):
            continue
        text = css.read_text(encoding="utf-8", errors="replace")
        for m in CSS_ARROWS.finditer(blank(text, r"/\*.*?\*/")):
            line = text.count("\n", 0, m.start()) + 1
            err(css, f"arrow {m.group(0)!r} at line {line}: the brand bans arrows (vtp_voice voice-and-tone, Punctuation)")

    # --- orphans ---
    # A noindex redirect stub is unlinked ON PURPOSE: it exists to catch inbound
    # links from outside the site after a URL changes, so nothing here should
    # point at it. Same reasoning as the sitemap exemption below. Flagging these
    # trains people to ignore the orphan warning, which is worth keeping sharp.
    entry = {"index.html", "404.html"}
    for page in all_pages:
        if page.name in entry or page in linked_to:
            continue
        body = page.read_text(encoding="utf-8", errors="replace")
        is_noindex = re.search(r'<meta[^>]+name=["\']robots["\'][^>]+noindex', body, re.I)
        redirects = re.search(r'<meta[^>]+http-equiv=["\']refresh["\']', body, re.I)
        if is_noindex and redirects:
            continue
        warn(page, "orphan — no other page links to it")

    # --- sitemap consistency ---
    sm = ROOT / "sitemap.xml"
    if not sm.exists():
        warn(ROOT / "sitemap.xml", "no sitemap.xml")
    else:
        listed = set(re.findall(r"<loc>\s*([^<]+?)\s*</loc>", sm.read_text(encoding="utf-8")))
        def _norm(u):
            q = urlparse(u).path.lstrip("/")
            if q == "" or q.endswith("/"):
                q += "index.html"
            return q
        listed_paths = {_norm(u) for u in listed}
        actual = {str(p.relative_to(ROOT)) for p in all_pages} - {"404.html"}
        for missing in sorted(listed_paths - actual):
            cand = ROOT / missing
            if not cand.exists() and not (cand / "index.html").exists():
                errors.append(f"sitemap.xml: lists a page that does not exist: {missing}")
        # A page that declares robots=noindex SHOULD be absent from the sitemap — listing it
        # would contradict the page's own directive. Only flag indexable pages.
        for absent in sorted(actual - listed_paths):
            body = (ROOT / absent).read_text(encoding="utf-8", errors="replace")
            if re.search(r'<meta[^>]+name=["\']robots["\'][^>]+noindex', body, re.I):
                continue
            warnings.append(f"sitemap.xml: {absent} is not listed")

    # --- report ---
    for w in warnings:
        print(f"WARN  {w}")
    if warnings and errors:
        print()
    for e in errors:
        print(f"ERROR {e}")

    print()
    print(f"{len(all_pages)} pages checked — {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
