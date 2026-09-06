# Decisions

**This repository does not keep its own decisions log. There is one, and it is central:**

### → [`vtp_command/DECISIONS-LOG.md`](https://github.com/VonTerraProject501c3/vtp_command/blob/main/DECISIONS-LOG.md)

That is where to find what VTP decided about the public website — and everything else — along with when,
by whom, and why.

## Why not one per repo

Most decisions here span repos. "The programs are these six" changes the charter in
`vtp_governance`, the canonical facts, the nav in `vtp_site`, and what the brand may claim in
`vtp_voice`. Written in four places it becomes four entries that drift, and then four answers
to the same question. One log, four readers.

## Where things live

| Question | File |
|---|---|
| What did we decide, and why? | [`DECISIONS-LOG.md`](https://github.com/VonTerraProject501c3/vtp_command/blob/main/DECISIONS-LOG.md) — permanent, append-only |
| What is still undecided? | [`DECISIONS-NEEDED.md`](https://github.com/VonTerraProject501c3/vtp_command/blob/main/DECISIONS-NEEDED.md) — an inbox |
| What work is open? | [`OUTSTANDING.md`](https://github.com/VonTerraProject501c3/vtp_command/blob/main/OUTSTANDING.md) and the GitHub issues it indexes |
| Where do I file something? | `vtp_command` issues — see [`CONTRIBUTING.md`](CONTRIBUTING.md) |

## The log is enforced, not just documentation

`.claude/workflows/org-issues.js` parses `DECISIONS-LOG.md` at run time. An entry marked
`Status: active` and `Constrains: frozen` makes its `Guards:` phrases off-limits to automated
agents — any issue touching one is routed to a human instead.

So freezing a subject means **writing a decision**, not editing code. A superseded decision
stops constraining automatically.
