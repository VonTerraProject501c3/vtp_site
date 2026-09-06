#!/usr/bin/env node
/* Sync the shared header/footer from _partials.js into every page.
 *
 * Why this exists: _partials.js was described in three places as the generator for the shared
 * shell, but nothing ever ran it. Pages are hand-edited, so the "generator" drifted behind the
 * pages it supposedly produced — and regenerating from it would have silently reverted real
 * changes. This makes it canonical for real.
 *
 *   node tools/sync_shell.mjs          apply
 *   node tools/sync_shell.mjs --check  exit 1 if any page would change (used by CI)
 *
 * Per-page state that the shared shell cannot know is re-applied after the swap:
 *   - aria-current on the nav item for the current page, or its parent section
 *   - root-relative paths on 404.html, which GitHub Pages serves at arbitrary depth
 */

import { readFileSync, writeFileSync, readdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const CHECK = process.argv.includes("--check");

// _partials.js is a plain script, not a module — evaluate it and read the constants back out.
const src = readFileSync(join(ROOT, "_partials.js"), "utf8");
const { HEADER, FOOTER } = new Function(`${src}; return { HEADER, FOOTER };`)();

// Which nav item should be lit for a page that is not itself a nav entry.
const PARENT = {
  "programs.html": ["mentorship.html", "professional-development.html", "grant-initiative.html",
                    "cyberhero.html", "flyspacea.html", "flyspacea-impact-2026.html"],
  "resource-hub.html": ["self-assessment.html", "start-security.html"],
  "about.html": ["team.html", "faq.html", "documents.html", "lines-of-effort.html",
                 "terms.html", "contact.html", "VTP-Report-2025.html"],
};
const childToParent = {};
for (const [parent, kids] of Object.entries(PARENT)) for (const k of kids) childToParent[k] = parent;

const pages = readdirSync(ROOT).filter((f) => f.endsWith(".html"));
for (const f of pages) {
  if (f.startsWith("team-")) childToParent[f] ??= "about.html";
}

function applyCurrent(html, file) {
  if (file === "404.html") return html;                    // 404 is not "a page you are on"
  const self = pages.includes(file) && html.includes(`href="${file}"`);
  if (self && html.includes(`<a class="nav-link" href="${file}"`)) {
    return html.replace(`<a class="nav-link" href="${file}"`,
                        `<a class="nav-link" href="${file}" aria-current="page"`);
  }
  const parent = childToParent[file];
  if (parent && html.includes(`<a class="nav-link" href="${parent}"`)) {
    return html.replace(`<a class="nav-link" href="${parent}"`,
                        `<a class="nav-link" href="${parent}" aria-current="true"`);
  }
  return html;
}

const rootRelative = (s) =>
  s.replace(/(href|src)="(?!https?:|mailto:|#|\/)([^"]+)"/g, '$1="/$2"');

let changed = [];
for (const file of pages) {
  const path = join(ROOT, file);
  const original = readFileSync(path, "utf8");

  let header = HEADER, footer = FOOTER;
  if (file === "404.html") { header = rootRelative(header); footer = rootRelative(footer); }
  header = applyCurrent(header, file);

  // HEADER carries the skip link, which lives BEFORE <header> in the page. Replace from the
  // skip link (if present) through </header> so the two cannot end up duplicated.
  const topRe = /(?:<a class="skip-link"[\s\S]*?<\/a>\s*)?<header class="site-header">[\s\S]*?<\/header>/;
  let out = original
    .replace(topRe, () => header.trimEnd())
    .replace(/<footer class="site-footer">[\s\S]*?<\/footer>/, () => footer.trimEnd());

  if (out !== original) {
    changed.push(file);
    if (!CHECK) writeFileSync(path, out);
  }
}

if (CHECK) {
  if (changed.length) {
    console.error(`shell drift — ${changed.length} page(s) differ from _partials.js:`);
    for (const f of changed) console.error(`  ${f}`);
    console.error("\nRun: node tools/sync_shell.mjs");
    process.exit(1);
  }
  console.log(`shell in sync across ${pages.length} pages`);
} else {
  console.log(changed.length
    ? `shell synced — ${changed.length} page(s) updated:\n  ${changed.join("\n  ")}`
    : `shell already in sync across ${pages.length} pages`);
}
