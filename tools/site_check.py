"""Site conformance checks — the page's promises, executable.

Run: python tools/site_check.py   (exit 0 = all pass; prints one line per check)
Written RED-first on 2026-08-21 before the recruiter-clarity redesign: these
assert the DESIRED state (dusk palette, no terminal chrome, plain-English
glossary, walkthrough page), so they fail on the pre-redesign page by design.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAILS: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(("PASS  " if ok else "FAIL  ") + name + (f"  [{detail}]" if detail and not ok else ""))
    if not ok:
        FAILS.append(name)


index = (ROOT / "index.html").read_text(encoding="utf-8")
walk_path = ROOT / "walkthrough.html"
walk = walk_path.read_text(encoding="utf-8") if walk_path.exists() else ""
pages = {"index.html": index, "walkthrough.html": walk}

# 1. The terminal look is gone
for token in ("lito@prod", "termbar", "--term:", "--term-ink"):
    check(f"terminal chrome gone: {token!r}", token not in index, "still present")

# 2. Twin Cities skyline art present and labeled
check("skyline art present", 'id="skyline"' in index)
check("skyline accessibly labeled", bool(re.search(r"(Minneapolis|Twin Cities)", index)))

# 3. Dusk palette replaces the terminal palette
check("dusk palette tokens defined", "--dusk" in index)

# 4. Walkthrough page exists and is linked
check("walkthrough.html exists", walk_path.exists())
check("index links the walkthrough", 'href="walkthrough.html"' in index)

# 5. Plain-English coverage
for term in ("best-of-k", "unhobbl", "mutation testing", "drift gate",
             "placebo", "held-out", "calibration", "defense-in-depth"):
    check(f"walkthrough explains {term!r}", term.lower() in walk.lower())
check("index carries the guided-tour on-ramp", "uided tour" in index)

# 6. AI-slop scan (both pages)
SLOP = ("delve", "seamless", "cutting-edge", "harness the power", "game-changer",
        "revolutioniz", "stands as a testament", "in today's fast-paced")
for pname, body in pages.items():
    hits = [s for s in SLOP if s in body.lower()]
    check(f"no AI-slop in {pname}", not hits, ", ".join(hits))

# 7. Internal links resolve to real files
for pname, body in pages.items():
    if not body:
        continue
    broken = []
    for href in re.findall(r'href="([^"#][^":]*?)"', body):
        if href.startswith(("http", "mailto:", "data:")):
            continue
        if not (ROOT / href.split("#")[0]).exists():
            broken.append(href)
    check(f"internal links resolve in {pname}", not broken, ", ".join(broken))

# 8. Basics on every page
for pname, body in pages.items():
    if not body:
        check(f"{pname} basics", False, "page missing")
        continue
    check(f"{pname} basics", all((
        "<title>" in body,
        'name="description"' in body,
        "prefers-reduced-motion" in body,
        "prefers-color-scheme" in body,
    )))

# 9. Career surface: resume + certificates visible
check("resume link present", "Lito-Biala-Resume.pdf" in index)
check("resume file exists", (ROOT / "Lito-Biala-Resume.pdf").exists())
check("Anthropic courses named on site", "Claude Code in Action" in index)

print()
if FAILS:
    print(f"{len(FAILS)} FAILED")
    sys.exit(1)
print("ALL PASS")
