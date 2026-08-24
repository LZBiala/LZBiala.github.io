"""Site conformance checks - the page's promises, executable.

Run: python tools/site_check.py   (exit 0 = all pass; prints one line per check)
Written RED-first on 2026-08-21 before the recruiter-clarity redesign: these
assert the DESIRED state (dusk palette, no terminal chrome, plain-English
glossary, walkthrough page), so they fail on the pre-redesign page by design.
"""
from __future__ import annotations

import os
import re
import subprocess
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

# 8b. The hyphens-only rule applies to EVERY tracked text file, not just the two pages.
# README.md is the first thing a visitor to the GitHub repo reads, and it was never covered:
# it carried six em dashes while the log claimed zero remained. A rule enforced on a subset
# is a rule that drifts everywhere else.
DASHES = ("\u2014", "\u2013")
try:
    tracked = subprocess.run(["git", "-C", str(ROOT), "ls-files"],
                             capture_output=True, text=True, timeout=30).stdout.split("\n")
except Exception:
    tracked = []
TEXT_SUFFIXES = {".md", ".html", ".py", ".txt", ".yml", ".yaml", ".json", ".css", ".js", ".cfg", ".toml"}
dashed = []
for rel in tracked:
    rel = rel.strip()
    if not rel:
        continue
    f = ROOT / rel
    if not (f.exists() and f.is_file()):
        continue
    if f.suffix.lower() not in TEXT_SUFFIXES and f.name not in (".gitignore", ".gitattributes"):
        continue
    try:
        body = f.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        continue
    n = sum(body.count(d) for d in DASHES)
    if n:
        dashed.append(f"{rel} ({n})")
check("hyphens only across every tracked text file", not dashed, ", ".join(dashed))

# 9. Career surface: resume + certificates visible
check("resume link present", "Lito-Biala-Resume.pdf" in index)
check("resume file exists", (ROOT / "Lito-Biala-Resume.pdf").exists())
check("Anthropic courses named on site", "Claude Code in Action" in index)

# 10. A number that travels must take its limits with it.
# The flip-test figures are the most quotable thing on this site and the easiest to read as
# a benchmark result, which they are not: the scripted-judge run is true by construction and
# the four-verdict run is a single labeled case study. Any page that quotes one must also
# say so, on the same page, or the number is doing work it has not earned.
BOUNDED = (
    (("3 of 4", "3/4", "0/8", "3/8"),
     ("true by construction", "not a benchmark", "case study"),
     "flip-test numbers carry their limits"),
)
game_txt = (ROOT / "game.html").read_text(encoding="utf-8")
# game.html joined this scan when the FORWARD DEPLOYED act started quoting the flip test
# inside a teaching card. A number that travels into the game is still a number that
# travels.
for pname, body in (("index.html", index), ("walkthrough.html", walk), ("game.html", game_txt)):
    for claims, caveats, label in BOUNDED:
        quoted = [c for c in claims if c in body]
        if not quoted:
            continue
        has = any(c.lower() in body.lower() for c in caveats)
        check(f"{label} in {pname}", has,
              f"quotes {', '.join(quoted)} with no limiting phrase")

# 11. The simulator has tests now, and they are part of the gate rather than a thing to
# remember. It produces every balance number this site publishes; on 2026-08-23 a guard
# clause made a four-enemy pack attack once per round and roughly 3.5 million published
# battles described a game that did not exist. Slow (it fights a few thousand battles), so
# it can be skipped deliberately with SKIP_SIM_TESTS=1 - never by forgetting.
if os.environ.get("SKIP_SIM_TESTS") != "1":
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "test_combat_sim.py")],
                       cwd=str(ROOT), capture_output=True, text=True)
    tail = [l for l in (r.stdout + r.stderr).splitlines() if l.startswith("FAIL")]
    check("simulator self-tests pass", r.returncode == 0, "; ".join(tail)[:300])
else:
    print("SKIP  simulator self-tests (SKIP_SIM_TESTS=1)")

print()
if FAILS:
    print(f"{len(FAILS)} FAILED")
    sys.exit(1)
print("ALL PASS")
