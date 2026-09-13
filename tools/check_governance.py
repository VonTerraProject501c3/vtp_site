#!/usr/bin/env python3
"""Governance checks for vtp_site — the deterministic half of the promotion gate.

check_site.py covers HTML correctness: markup, links, alt text, ids. This covers the things
that are correct HTML and still wrong for a 501(c)(3): a fact the organization never said, a
disclaimer someone helpfully deleted, a home address, an exemption-status claim VTP cannot
make, a Drive embed nobody vetted.

WHY THESE ARE SCRIPTS AND NOT AGENTS
------------------------------------
A gate made only of model judgment is not a gate: it is not reproducible, it has no stable
pass/fail to bind to a required status check, and it can be argued out of a finding by a
convincing PR description. Agents are good at *noticing*. Scripts are what *block*.

WHY THE FROZEN-LANGUAGE CHECK IS A BASELINE, NOT A GREP
-------------------------------------------------------
DECISIONS-LOG.md carries ~73 guard phrases, but they are ISSUE-ROUTING signals — words that
should make a human read a ticket ("phone", "Secretary", "GIAC", "inbox"). Grepping site HTML
for them would produce constant noise and get the check switched off within a week.

What the site actually needs is the opposite shape: a BASELINE of where legally-sensitive
language currently sits, so that BOTH directions are caught. The likelier failure here is not
a contributor adding a compliance claim — it is a contributor tidying one away. A
presence-check cannot see a deletion. A baseline can.

It is also why the baseline is over *normalized sentences*, not whole files: privacy.html
shipped "501(c)(3) nonprofit corporation registered in Maryland" — the same status claim as
the frozen wording, reordered, asserting a state charitable registration VTP has never held.
Escaped-literal matching could not see it. Matching the status token and hashing the sentence
around it can.

    python3 tools/check_governance.py                    run everything
    python3 tools/check_governance.py --only facts       run one check
    python3 tools/check_governance.py --update-baseline  re-record baselines (deliberate act)

Exit 0 clean, 1 on any error. Warnings never fail the build.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POLICY = ROOT / "tools" / "policy"
FACTS = POLICY / "canonical-facts.snapshot.json"
BASELINE = POLICY / "content-baseline.json"

SKIP_DIRS = {"tools", "node_modules", "js", "css", "website_images", ".git", ".github"}

ERRORS: list[str] = []
WARNINGS: list[str] = []


def err(page: str, msg: str) -> None:
    ERRORS.append(f"ERROR  {page}: {msg}")


def warn(page: str, msg: str) -> None:
    WARNINGS.append(f"WARN   {page}: {msg}")


def pages() -> list[Path]:
    out = [p for p in ROOT.glob("*.html")]
    for d in ROOT.iterdir():
        if not d.is_dir() or d.name.startswith(".") or d.name in SKIP_DIRS:
            continue
        out.extend(p for p in d.rglob("index.html"))
    return sorted(out)


def rel(p: Path) -> str:
    return str(p.relative_to(ROOT))


def text_of(html: str) -> str:
    """Visible-ish text: drop script/style, unwrap tags, collapse whitespace."""
    html = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<!--.*?-->", " ", html, flags=re.S)
    html = re.sub(r"<[^>]+>", " ", html)
    html = (html.replace("&nbsp;", " ").replace("&amp;", "&")
                .replace("&lt;", "<").replace("&gt;", ">").replace("&#39;", "'")
                .replace("&quot;", '"').replace("&rsquo;", "'").replace("&mdash;", "—"))
    return re.sub(r"\s+", " ", html).strip()


REDIRECT_STUB = re.compile(r'<meta\s+http-equiv=["\']refresh["\']', re.I)


def is_redirect_stub(html: str) -> bool:
    """A page whose only job is to forward an old URL to its replacement.

    Requires BOTH the refresh and a canonical link, so an ordinary page that happens to use a
    meta refresh for some other reason is not silently exempted from the checks.
    """
    return bool(REDIRECT_STUB.search(html)) and 'rel="canonical"' in html


def strip_shell(html: str) -> str:
    """Drop the shared header/footer so a check sees only what this page actually says.

    The header and footer are baked into every page by _partials.js. Anything in them is
    site-wide by construction, so matching on them makes a per-page check fire on all 46
    pages at once.
    """
    html = re.sub(r"<header\b[^>]*>.*?</header>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<footer\b[^>]*>.*?</footer>", " ", html, flags=re.S | re.I)
    return html


def sentences(t: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", t) if s.strip()]


def norm(s: str) -> str:
    """Normalize a sentence so trivial edits don't churn the baseline but wording does."""
    s = re.sub(r"\s+", " ", s).strip().lower()
    return re.sub(r"[^\w\s()/$.,-]", "", s)


def h(s: str) -> str:
    return hashlib.sha256(norm(s).encode()).hexdigest()[:16]


def load_facts() -> dict:
    if not FACTS.exists():
        err("tools/policy", "canonical-facts.snapshot.json is missing — run "
                            "`node tools/export_policy.mjs` from vtp_command")
        return {}
    return json.loads(FACTS.read_text())


# ---------------------------------------------------------------------------
# 1. FACT DRIFT — the site renders governance's facts; it does not decide them.
# ---------------------------------------------------------------------------
def check_facts(docs: dict[Path, str]) -> None:
    f = load_facts()
    if not f:
        return
    org, contact = f.get("org", {}), f.get("contact", {})
    ein, phone = org.get("ein"), contact.get("phone")
    addr = (contact.get("mailingAddress") or {}).get("oneLine")

    for p, html in docs.items():
        t = text_of(html)

        # Any EIN-shaped token must BE the EIN. A wrong EIN on a nonprofit site is a
        # donor-facing defect and a filing inconsistency at once.
        for found in set(re.findall(r"\b\d{2}-\d{7}\b", html)):
            if found != ein:
                err(rel(p), f"EIN-shaped number {found!r} is not the canonical EIN {ein!r}")

        # JSON-LD is machine-read by search engines and charity aggregators, so a stale value
        # there propagates further than a stale one in prose. check_site.py validates JSON-LD
        # syntax; nothing validated the values.
        for blk in re.findall(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', html, re.S | re.I):
            try:
                data = json.loads(blk)
            except json.JSONDecodeError:
                continue  # check_site.py owns syntax
            for node in _walk(data):
                if not isinstance(node, dict):
                    continue
                if node.get("propertyID") == "EIN" and node.get("value") not in (None, ein):
                    err(rel(p), f"JSON-LD EIN value {node.get('value')!r} != canonical {ein!r}")
                if node.get("@type") == "Organization" and node.get("legalName") not in (None, org.get("legalName")):
                    err(rel(p), f"JSON-LD legalName {node.get('legalName')!r} != canonical {org.get('legalName')!r}")

        if phone and re.search(r"\(\d{3}\)\s*\d{3}-\d{4}", t):
            for found in set(re.findall(r"\(\d{3}\)\s*\d{3}-\d{4}", t)):
                # (410) 974-5534 is the Maryland Secretary of State, a required element of the
                # §6-411 notice — not VTP's number and not drift.
                if found not in (phone, "(410) 974-5534"):
                    err(rel(p), f"phone {found!r} is neither VTP's canonical {phone!r} nor the MD SOS number")

        if addr and "Redland" in t:
            if addr.lower() not in t.lower():
                warn(rel(p), f"mentions Redland but not the exact canonical address {addr!r}")

    # Leadership: every team page must correspond to someone in the record, and vice versa.
    roster = {m["slug"]: m for m in f.get("leadership", []) if m.get("slug")}
    # A redirect stub is SUPPOSED to be unlinked and is not presenting anyone — it forwards.
    # Excluding it here is what lets a retired duplicate URL keep working without the orphan
    # rule flagging it forever, which would train people to ignore the rule.
    on_site = {
        p.stem[len("team-"):]: p
        for p in docs
        if p.name.startswith("team-") and not is_redirect_stub(docs[p])
    }

    for slug, p in sorted(on_site.items()):
        if slug in roster:
            name = roster[slug]["name"]
            title = roster[slug].get("title") or ""
            t = text_of(docs[p])
            if name.lower() not in t.lower():
                err(rel(p), f"page for {slug!r} does not contain that person's name {name!r}")
            if title and title.lower() not in t.lower():
                warn(rel(p), f"title {title!r} from the record does not appear on the page")
        else:
            # Not automatically wrong — the record only holds `leadership`, so a non-officer
            # contributor legitimately has no entry. But the site is presenting a person the
            # source of record does not describe, and that is a human's call, not a script's.
            warn(rel(p), f"team page for {slug!r} has no entry in canonical-facts leadership[] "
                         f"— either add them to the record or remove the page")

    linked = set()
    for p, html in docs.items():
        linked.update(re.findall(r"team-([a-z0-9-]+)\.html", html))
    sitemap = ROOT / "sitemap.xml"
    if sitemap.exists():
        linked.update(re.findall(r"team-([a-z0-9-]+)\.html", sitemap.read_text()))

    for slug, p in sorted(on_site.items()):
        if slug not in linked:
            err(rel(p), "orphan team page — nothing on the site or in sitemap.xml links to it. "
                        "A published page about a real person that no one can reach and no one "
                        "maintains is a stale-bio hazard; delete it or link it.")

    for slug, m in sorted(roster.items()):
        if slug not in on_site:
            warn("canonical-facts", f"{m['name']} ({slug}) is in the record but has no team-{slug}.html")


def _walk(o):
    yield o
    if isinstance(o, dict):
        for v in o.values():
            yield from _walk(v)
    elif isinstance(o, list):
        for v in o:
            yield from _walk(v)


# ---------------------------------------------------------------------------
# 2. STATUS LANGUAGE — baseline diff, both directions.
# ---------------------------------------------------------------------------
STATUS_TOKEN = re.compile(
    r"501\s*\(?\s*c\s*\)?\s*\(?\s*3\s*\)?"          # exemption status, any spacing
    r"|tax[- ]exempt"
    r"|tax[- ]deductible"
    r"|registered\s+(?:in|with|to\s+solicit)"        # the privacy.html failure
    r"|good\s+standing"
    r"|charitable\s+(?:registration|solicitation)"
    r"|Solicitations?\s+Act",
    re.I,
)


def collect_status(docs: dict[Path, str]) -> dict[str, list[dict]]:
    found: dict[str, list[dict]] = {}
    for p, html in docs.items():
        hits = []
        for s in sentences(text_of(html)):
            if STATUS_TOKEN.search(s):
                hits.append({"hash": h(s), "excerpt": s[:150]})
        if hits:
            found[rel(p)] = sorted(hits, key=lambda x: x["hash"])
    return found


def check_status_language(docs: dict[Path, str]) -> None:
    before = len(ERRORS)
    current = collect_status(docs)
    if not BASELINE.exists():
        err("tools/policy", "content-baseline.json is missing — run "
                            "`python3 tools/check_governance.py --update-baseline`")
        return
    base = json.loads(BASELINE.read_text()).get("status_language", {})

    for page in sorted(set(base) | set(current)):
        was = {x["hash"]: x["excerpt"] for x in base.get(page, [])}
        now = {x["hash"]: x["excerpt"] for x in current.get(page, [])}
        for hh, ex in now.items():
            if hh not in was:
                err(page, "NEW compliance/status language not in the baseline — "
                          f"VTP's exemption and registration wording is under legal review "
                          f"(D-0010, D-0003): {ex!r}")
        for hh, ex in was.items():
            if hh not in now:
                err(page, "compliance/status language was REMOVED OR REWORDED. This is the "
                          "failure a presence-check cannot see — a required disclaimer can be "
                          f"tidied away as easily as added: {ex!r}")

    # Only advertise the baseline escape hatch when THIS check is what failed. Printing it
    # after an unrelated error invites someone to "fix" a fact-drift failure by re-recording
    # a baseline that has nothing to do with it.
    if len(ERRORS) > before:
        ERRORS.append(
            "       ↑ if these changes are intended AND cleared, re-record with "
            "`python3 tools/check_governance.py --update-baseline` and say so in the PR. "
            "Updating the baseline is a deliberate act, which is the point."
        )


# ---------------------------------------------------------------------------
# 3. RETIRED PHONE — D-0035. Zero-ambiguity check.
# ---------------------------------------------------------------------------
def check_retired_phone(docs: dict[Path, str]) -> None:
    for p, html in docs.items():
        if re.search(r"\(?202\)?[\s.-]?870[\s.-]?9825", html):
            err(rel(p), "contains the RETIRED phone (202) 870-9825. D-0035 replaced it with "
                        "(301) 531-4526, which is the number listed under oath in the COR-92 draft.")


# ---------------------------------------------------------------------------
# 4. SOLICITATION NOTICE — MD Solicitations Act §6-411.
# ---------------------------------------------------------------------------
SOLICIT_EMBED = re.compile(r"<iframe[^>]*donorbox\.org|donorbox\.org/(?:embed|widget)|donorbox\.js", re.I)
# An ANCHOR whose href is Donorbox — not any mention of the string. Every page carries
# `frame-src https://donorbox.org` in its Content-Security-Policy meta tag, so a bare
# substring match flagged all 46 pages, including team bios, as soliciting donations. It was
# reading a security header as a solicitation.
SOLICIT_LINK = re.compile(r"<a\b[^>]*href=[\"'][^\"']*donorbox\.org", re.I)


def check_solicitation(docs: dict[Path, str]) -> None:
    f = load_facts()
    contact = f.get("contact", {}) if f else {}
    phone = contact.get("phone")
    addr = (contact.get("mailingAddress") or {}).get("oneLine")

    for p, html in docs.items():
        t = text_of(html)
        has_notice = "Solicitations Act" in t
        if SOLICIT_EMBED.search(html):
            # vtp_site#11 was exactly this: cyberhero.html took donations with no notice block.
            if not has_notice:
                err(rel(p), "takes donations (Donorbox embed) but carries NO Maryland "
                            "Solicitations Act notice. This exact defect shipped once already "
                            "(vtp_site#11).")
                continue
            if addr and addr.lower() not in t.lower():
                err(rel(p), f"Solicitations Act notice does not carry the canonical address {addr!r}")
            if phone and phone not in t:
                err(rel(p), f"Solicitations Act notice does not carry the canonical phone {phone!r}")
            if "Maryland Secretary of State" not in t:
                err(rel(p), "Solicitations Act notice omits the Maryland Secretary of State "
                            "contact, which the statutory notice requires")
        elif SOLICIT_LINK.search(strip_shell(html)) and not has_notice:
            # A donate LINK in page CONTENT is arguably a solicitation too, and whether that
            # triggers §6-411 is a question for counsel — so this informs rather than blocks.
            #
            # strip_shell() is load-bearing. The shared footer carries a donate link on all 46
            # pages, so checking raw HTML warned about every page in the site — 41 identical
            # lines carrying no information, which is precisely how a check gets ignored and
            # then switched off. A signal that fires everywhere is not a signal.
            warn(rel(p), "page content (not the shared footer) links to Donorbox without a "
                         "Solicitations Act notice. Whether a link is itself a solicitation "
                         "under §6-411 is a question for counsel — flagging, not blocking.")


# ---------------------------------------------------------------------------
# 5. PII — "PII stays on main, restricted; never public" had zero enforcement.
# ---------------------------------------------------------------------------
STALE_ADDRESS = re.compile(r"2648\s+Hardaway|Hanover,?\s+MD", re.I)
PERSONAL_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@(gmail|yahoo|hotmail|outlook|icloud|aol|proton(mail)?|pm)\.(com|me)\b", re.I)
SSN = re.compile(r"\b(?!000|666|9\d\d)\d{3}-(?!00)\d{2}-(?!0000)\d{4}\b")
STREET = re.compile(
    r"\b\d{1,6}\s+(?:[A-Z][A-Za-z.'-]+\s+){1,4}"
    r"(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Circle|Cir|Way|Terrace|Ter|Place|Pl)\b\.?"
)


def check_pii(docs: dict[Path, str]) -> None:
    f = load_facts()
    approved = (f.get("contact", {}).get("mailingAddress") or {}).get("oneLine", "") if f else ""

    for p, html in docs.items():
        t = text_of(html)
        if STALE_ADDRESS.search(t):
            err(rel(p), "contains the STALE Articles address (Hardaway Circle / Hanover MD). "
                        "That is a residential address, D-0002 records it as stale, and the "
                        "public EIN notice already exposed a home address once (D-0037).")
        if SSN.search(t):
            err(rel(p), "contains something formatted like a Social Security number")
        for m in set(PERSONAL_EMAIL.findall(t)):
            err(rel(p), f"contains a personal-domain email address (@{m[0]}.…) — VTP "
                        "correspondence uses vonterraproject.org")
        for m in set(STREET.findall(t)):
            if approved and m.lower() in approved.lower():
                continue
            if "State House" in t and "Annapolis" in t:
                pass  # the MD SOS address in the §6-411 notice carries no house number anyway
            warn(rel(p), f"street address that is not VTP's approved mailing address: {m!r}")

    for pat in ("*.xlsx", "*.csv", "*.docx", "*.xls", "*.doc"):
        for f2 in ROOT.rglob(pat):
            if any(part in SKIP_DIRS for part in f2.parts):
                continue
            err(rel(f2), "spreadsheet/document committed to the PUBLIC site repo. Drive content "
                         "stays on the Drive; these are the file types that carry rosters, "
                         "intake responses and donor exports.")


# ---------------------------------------------------------------------------
# 6. DRIVE EMBEDS — baselined, because a new file ID is a publication decision.
# ---------------------------------------------------------------------------
DRIVE_ID = re.compile(r"drive\.google\.com/file/d/([A-Za-z0-9_-]+)")


def collect_embeds(docs: dict[Path, str]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for p, html in docs.items():
        ids = sorted(set(DRIVE_ID.findall(html)))
        if ids:
            out[rel(p)] = ids
    return out


def check_embeds(docs: dict[Path, str]) -> None:
    current = collect_embeds(docs)
    if not BASELINE.exists():
        return  # check_status_language already reported the missing baseline
    base = json.loads(BASELINE.read_text()).get("drive_embeds", {})

    for page in sorted(set(base) | set(current)):
        was, now = set(base.get(page, [])), set(current.get(page, []))
        for fid in sorted(now - was):
            err(page, f"NEW Google Drive embed {fid} not in the baseline. Publishing a Drive "
                      "document is a disclosure decision (IRC 6104 / PII), not a content edit.")
        for fid in sorted(was - now):
            err(page, f"Drive embed {fid} REMOVED. D-0039 exists because re-importing a file "
                      "mints a new ID and breaks every link aimed at the old one — check this "
                      "is a deliberate unpublish, not a broken embed.")


# ---------------------------------------------------------------------------

CHECKS = {
    "facts": check_facts,
    "status-language": check_status_language,
    "retired-phone": check_retired_phone,
    "solicitation": check_solicitation,
    "pii": check_pii,
    "embeds": check_embeds,
}


def update_baseline(docs: dict[Path, str]) -> int:
    payload = {
        "_about": "Baseline for vtp_site/tools/check_governance.py. Regenerating this is a "
                  "DELIBERATE act — it records that a human looked at a change to compliance "
                  "language or a Drive embed and accepted it. Never regenerate to make CI green.",
        "status_language": collect_status(docs),
        "drive_embeds": collect_embeds(docs),
    }
    BASELINE.parent.mkdir(parents=True, exist_ok=True)
    BASELINE.write_text(json.dumps(payload, indent=2) + "\n")
    n_s = sum(len(v) for v in payload["status_language"].values())
    n_e = sum(len(v) for v in payload["drive_embeds"].values())
    print(f"baseline recorded: {n_s} status sentence(s) across "
          f"{len(payload['status_language'])} page(s); {n_e} Drive embed(s) across "
          f"{len(payload['drive_embeds'])} page(s)")
    print(f"  → {rel(BASELINE)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", choices=sorted(CHECKS), help="run a single check")
    ap.add_argument("--update-baseline", action="store_true", help="re-record the baselines")
    args = ap.parse_args()

    docs = {p: p.read_text(encoding="utf-8", errors="replace") for p in pages()}

    if args.update_baseline:
        return update_baseline(docs)

    for name, fn in CHECKS.items():
        if args.only and name != args.only:
            continue
        fn(docs)

    for line in WARNINGS:
        print(line)
    for line in ERRORS:
        print(line)

    print(f"\n{len(docs)} pages checked — {len(ERRORS)} error(s), {len(WARNINGS)} warning(s)")
    return 1 if ERRORS else 0


if __name__ == "__main__":
    sys.exit(main())
