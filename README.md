# The Von Terra Project — Website

A multi-page static website built from `VTP_website_BUILD_INSTRUCTIONS.md`. Point your host
(or any static file server) at this folder; `index.html` is the entry page. No build step
is required.

## Brand source & content owners (this repo renders; it does not own facts)

VTP is three repos, one system. **This site consumes; it is not the source of truth:**

- **Brand tokens, voice, and design system** are canonical in **`vtp_voice`**
  (github.com/TheColtonWilliams/vtp_voice). Don't hand-tune colors/type here — they're mirrored from
  there (see the provenance comments in `css/style.css`). Mission/vision/values come from
  `vtp_voice/brand/facts.json`.
- **Governance/transparency documents, the embedded report, team roster, EIN, and
  donation/campaign IDs** are owned in **`vtp_governance`** (github.com/TheColtonWilliams/vtp_governance,
  private) and published via its `public` Drive. The Drive embeds on `documents.html` /
  `VTP-Report-2025.html` are keyed to file IDs tracked in
  `vtp_governance/governance/classification/website-embed-manifest.md` — don't re-upload those
  files (it changes the ID and breaks the embed).

## Structure
- 14 primary pages + 8 team biography pages (22 `.html` files total)
- `css/style.css` — the single shared stylesheet
- `js/main.js` — mobile hamburger nav, dropdown menus, FAQ accordion
- `website_images/` — logo, team headshots (resized to 640px / ~60–110KB each for performance)
- `_partials.js` — generator-only template for the shared header/footer (not referenced by
  any page; safe to delete before deploying, kept so the header/footer can be regenerated
  consistently)

## TBD / missing assets (drop-in ready)
The build instructions reference assets that were not provided. Everything renders with a
graceful fallback meanwhile; add the files to `website_images/` with these exact names to
activate them — no code changes needed:

| Missing file | Where it's used | Current fallback |
|---|---|---|
| `VTPWallpaper.png` | Home hero background | Navy gradient |
| `DonorBoxWallpaper.png` | Donate hero background | Navy gradient |
| `Telephone.png`, `Email.png`, `Linkedin.png` | Contact/footer icons | Inline SVG icons in matching style (to switch to the PNGs, replace the `.ico` spans) |
| `Docs.png`, `Docs2.png` | Resource Hub / Documents decorative graphics | Omitted (HTML comments mark the spots); document cards use an inline SVG icon |
| Decorative illustrations (`2025-09-27…png`) | Optional feature imagery | Omitted per spec ("do not invent") |

Other TBDs in content:
- **Elisha Angeles** — no headshot provided → initials avatar ("EA"). Drop a photo in and
  update `team.html` / `team-elisha-angeles.html` (or ask me to wire it).
- **Saren Bennett** — no biography text provided (per spec, the bio page has no body).
- `href="#"` anchors that remain are intentional per spec: all Start-Security vendor
  buttons and the Documents "View / Download" links (governing docs not yet supplied).

### Live embeds (wired in)
- **Donate** (`donate.html`) — live Donorbox form (`donate-to-vtp`) + donor wall; "Donate Now" links to the campaign.
- **CyberHERo** (`cyberhero.html`) — live Donorbox form (`donate-824785`) + donor wall; program donate button links to the campaign.
- **Documents** (`documents.html`) — embedded Google Drive viewer for the 2025 Impact & Insight Report.
- Each embed has a plain-link fallback in case a browser blocks the third-party frame. The
  Drive report requires its sharing to be **"Anyone with the link"** to display publicly.

### Still awaiting a real embed (`[EMBED PLACEHOLDER]` boxes remain)
- **Self-Assessment Survey** (`self-assessment.html`) — no embed/URL provided yet.
- **Contact Form** (`contact.html`) — no embed/URL provided yet.

## Notes
- The VTP logo lockup (`VTP Logo.png`) was composed from the organization's emblem +
  wordmark assets at 506×120 for crisp rendering at the 40px header height.
- **Styling matches the VTP brand / design system** (dark `#2E2E2E` field, olive `#5C754A`,
  sage `#A0B98C`, gold `#D8B45C`, **Lexend**, wide-tracked UPPERCASE headings) — not the
  earlier navy/teal build-file palette. All of it lives in the single `css/style.css`.
- **Lexend is self-hosted** in `assets/fonts/` (`@font-face` in `style.css`); no external font
  fetch is required. The Google-Fonts `<link>` tags for Montserrat/Inter remain in each page's
  `<head>` but are now unused (the browser won't download those files) — safe to remove later.
