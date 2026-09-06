# What this changes

<!-- One or two sentences. What is different after this merges? -->

Closes #

## Why

<!-- The reason, not the mechanics. If it's tracked in an issue, a line is enough. -->

## Fact fidelity

The site **renders** the organization's facts; it does not decide them. Facts originate in
`vtp_governance` (`governance/canonical-facts.json`) and flow outward.

- [ ] This PR changes no organizational facts (names, titles, EIN, legal status, dates, figures), **or**
- [ ] It does, and the matching change is already in `vtp_governance` — link it here:

> ⚠️ Anything touching **legal or financial facts** — EIN, board roster, 501(c)(3) or
> registration status, compliance dates, donation handling — needs a human review before
> merge, even when the change looks obvious.

## Checks

- [ ] Every page I touched still renders correctly (opened it, didn't just diff it)
- [ ] Nav and footer still match the other pages (they are hand-copied across ~25 files)
- [ ] New or changed images have `alt` text, and `width`/`height` where practical
- [ ] Links I added resolve — internal targets exist, external ones load
- [ ] `target="_blank"` links carry `rel="noopener"`
- [ ] Colors and spacing come from the design tokens, not freelanced values
- [ ] Checked at a narrow viewport (~375px) as well as desktop
- [ ] Keyboard-navigable: I can reach and operate anything interactive with Tab and Enter

## Deploy note

`main` **is** production — GitHub Pages rebuilds vonterraproject.org on every push to `main`.
There is no staging environment and no build step.

## Screenshots

<!-- Before/after for anything visual. Delete if not applicable. -->
