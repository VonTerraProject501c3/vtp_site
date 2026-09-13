#!/usr/bin/env python3
"""Self-test for check_governance.py — inject each defect class, assert it is caught.

WHY THIS EXISTS
---------------
A check that has never fired has never been shown to work, and a governance check that
silently stopped working is worse than no check: every promotion comes back clean, which is
indistinguishable from "nothing was wrong". Each case below is a defect that either actually
shipped on vonterraproject.org or is one the gate exists to prevent.

Every case also has a NEGATIVE twin where relevant, because the failure mode that kills a
check is not missing a defect — it is crying wolf until someone turns it off. The
Donorbox/CSP case is here specifically: the first draft of the solicitation check read
`frame-src https://donorbox.org` out of the Content-Security-Policy meta tag and reported all
46 pages, team bios included, as soliciting donations.

    python3 tools/test_check_governance.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_governance as cg  # noqa: E402

PASS, FAIL = 0, 0


def run(check, docs) -> tuple[list[str], list[str]]:
    cg.ERRORS.clear()
    cg.WARNINGS.clear()
    check(docs)
    return list(cg.ERRORS), list(cg.WARNINGS)


def page(name: str, body: str) -> tuple[Path, str]:
    return cg.ROOT / name, (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta http-equiv="Content-Security-Policy" content="frame-src https://donorbox.org">'
        f"</head><body>{body}"
        '<footer class="site-footer"><a href="https://donorbox.org/donate-to-vtp">Donate</a>'
        "<p>EIN 33-2041628</p></footer></body></html>"
    )


def case(label: str, check, docs, *, expect_error: str | None = None,
         expect_warn: str | None = None, expect_clean: bool = False,
         ignore: str | None = None) -> None:
    """`ignore` drops findings that are correct but irrelevant to the case under test.

    check_facts walks the whole roster, so against a one-page synthetic doc set it correctly
    reports that six real people have no team page. That is right on the real site and noise
    here; suppressing it in the assertion is honest, weakening the check to make the test pass
    would not be.
    """
    global PASS, FAIL
    errs, warns = run(check, docs)
    if ignore:
        errs = [e for e in errs if not re.search(ignore, e, re.I)]
        warns = [w for w in warns if not re.search(ignore, w, re.I)]
    blob = " ".join(errs + warns)
    if expect_clean:
        real = [e for e in errs if "↑ if these changes" not in e]
        ok = not real and not warns
        detail = f"expected clean, got {len(real)} error(s) {len(warns)} warning(s): {blob[:160]}"
    elif expect_error:
        ok = any(re.search(expect_error, e, re.I) for e in errs)
        detail = f"expected ERROR matching {expect_error!r}, got: {blob[:200] or '(nothing)'}"
    else:
        ok = any(re.search(expect_warn, w, re.I) for w in warns)
        detail = f"expected WARN matching {expect_warn!r}, got: {blob[:200] or '(nothing)'}"

    if ok:
        PASS += 1
        print(f"  ok    {label}")
    else:
        FAIL += 1
        print(f"  FAIL  {label}\n          {detail}")


# ---------------------------------------------------------------------------
print("fact drift")

case("a wrong EIN is caught", cg.check_facts,
     dict([page("t.html", "<p>Our EIN is 99-1234567.</p>")]),
     expect_error=r"not the canonical EIN")

case("the real EIN is not flagged", cg.check_facts,
     dict([page("t.html", "<p>Our EIN is 33-2041628.</p>")]),
     expect_clean=True, ignore=r"is in the record but has no team-")

case("a JSON-LD EIN value that disagrees with prose is caught", cg.check_facts,
     dict([page("t.html",
                '<script type="application/ld+json">'
                '{"@type":"Organization","identifier":{"@type":"PropertyValue",'
                '"propertyID":"EIN","value":"99-1234567"}}</script>')]),
     expect_error=r"JSON-LD EIN"),

case("a stranger's phone number is caught", cg.check_facts,
     dict([page("t.html", "<p>Call us on (555) 123-4567.</p>")]),
     expect_error=r"neither VTP's canonical")

case("the MD Secretary of State number is NOT drift", cg.check_facts,
     dict([page("t.html", "<p>Maryland Secretary of State, (410) 974-5534.</p>")]),
     expect_clean=True, ignore=r"is in the record but has no team-")

# ---------------------------------------------------------------------------
print("status language (the privacy.html failure)")

cg.BASELINE_CACHE = None
_docs = dict([page("privacy.html", "<p>VTP is a 501(c)(3) nonprofit corporation.</p>")])
_base = cg.collect_status(_docs)


def status_against(baseline, docs):
    """Run the baseline diff against an explicit baseline rather than the on-disk file."""
    import json
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
        json.dump({"status_language": baseline, "drive_embeds": {}}, fh)
        tmp = Path(fh.name)
    old = cg.BASELINE
    cg.BASELINE = tmp
    try:
        return run(cg.check_status_language, docs)
    finally:
        cg.BASELINE = old
        tmp.unlink()


cg.ERRORS.clear()
errs, _ = status_against(_base, dict([page("privacy.html",
    "<p>VTP is a 501(c)(3) nonprofit corporation registered in Maryland.</p>")]))
if any("NEW compliance" in e for e in errs):
    PASS += 1
    print("  ok    reworded status claim is caught (the exact privacy.html defect)")
else:
    FAIL += 1
    print(f"  FAIL  reworded status claim NOT caught: {errs}")

errs, _ = status_against(_base, dict([page("privacy.html", "<p>VTP is a nonprofit.</p>")]))
if any("REMOVED OR REWORDED" in e for e in errs):
    PASS += 1
    print("  ok    DELETED status language is caught (a presence-check cannot see this)")
else:
    FAIL += 1
    print(f"  FAIL  deletion NOT caught: {errs}")

errs, _ = status_against(_base, _docs)
if not [e for e in errs if "↑" not in e]:
    PASS += 1
    print("  ok    an unchanged page is clean")
else:
    FAIL += 1
    print(f"  FAIL  unchanged page reported: {errs}")

# ---------------------------------------------------------------------------
print("retired phone (D-0035)")

case("the retired (202) number is caught", cg.check_retired_phone,
     dict([page("t.html", "<p>Call (202) 870-9825.</p>")]),
     expect_error=r"RETIRED phone")

case("the current number is fine", cg.check_retired_phone,
     dict([page("t.html", "<p>Call (301) 531-4526.</p>")]),
     expect_clean=True)

# ---------------------------------------------------------------------------
print("solicitation notice (vtp_site#11)")

case("a Donorbox embed with no notice is caught", cg.check_solicitation,
     dict([page("give.html", '<iframe src="https://donorbox.org/embed/x"></iframe>')]),
     expect_error=r"NO Maryland\s+Solicitations Act notice")

case("an embed WITH a complete notice passes", cg.check_solicitation,
     dict([page("give.html",
                '<iframe src="https://donorbox.org/embed/x"></iframe>'
                "<p>A copy of the current financial statement is available by writing "
                "17533 Redland Rd. #5582, Derwood, MD 20855 or by calling (301) 531-4526. "
                "Documents submitted under the Maryland Solicitations Act are also available "
                "from the Maryland Secretary of State, State House, Annapolis MD 21401, "
                "(410) 974-5534.</p>")]),
     expect_clean=True)

case("an embed whose notice has the WRONG address is caught", cg.check_solicitation,
     dict([page("give.html",
                '<iframe src="https://donorbox.org/embed/x"></iframe>'
                "<p>Maryland Solicitations Act. Write to 1 Nowhere Ave, Nowhere MD, or call "
                "(301) 531-4526. Maryland Secretary of State.</p>")]),
     expect_error=r"does not carry the canonical address")

case("the CSP meta tag alone is NOT a solicitation", cg.check_solicitation,
     dict([page("team-someone.html", "<h1>Someone</h1><p>A bio.</p>")]),
     expect_clean=True)

# ---------------------------------------------------------------------------
print("PII")

case("the stale Hardaway/Hanover address is caught", cg.check_pii,
     dict([page("t.html", "<p>2648 Hardaway Circle, Hanover, MD</p>")]),
     expect_error=r"STALE Articles address")

case("an SSN is caught", cg.check_pii,
     dict([page("t.html", "<p>123-45-6789</p>")]),
     expect_error=r"Social Security")

case("a personal gmail address is caught", cg.check_pii,
     dict([page("t.html", "<p>Write to someone@gmail.com</p>")]),
     expect_error=r"personal-domain email")

case("a vonterraproject.org address is fine", cg.check_pii,
     dict([page("t.html", "<p>Write to contact@vonterraproject.org</p>")]),
     expect_clean=True)

# ---------------------------------------------------------------------------
print("team pages")

case("a team page that does not name its own subject is caught", cg.check_facts,
     dict([page("team-eric-stewart.html", "<h1>Colton Williams</h1><p>Bio.</p>")]),
     expect_error=r"does not contain that person's name")

# ---------------------------------------------------------------------------
print(f"\n{PASS} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
