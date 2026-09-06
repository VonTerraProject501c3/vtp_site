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
                warn(page, f"heading jumps h{prev} → h{lvl} at line {line} — skipped level")
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

    # --- orphans ---
    entry = {"index.html", "404.html"}
    for page in all_pages:
        if page.name in entry or page in linked_to:
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
