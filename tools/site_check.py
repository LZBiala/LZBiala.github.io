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
# If git is missing or fails, `tracked` used to fall back to [] - and an empty scan produced
# an empty `dashed`, which printed PASS. The rule then silently stopped being enforced at all.
# Scanning nothing is now a failure, not a pass.
scan_errors: list[str] = []
try:
    _ls = subprocess.run(["git", "-C", str(ROOT), "ls-files"],
                         capture_output=True, text=True, timeout=30, check=True)
    tracked = _ls.stdout.split("\n")
except Exception as exc:                      # noqa: BLE001 - reported, never swallowed
    tracked = []
    scan_errors.append(f"could not list tracked files: {exc}")
TEXT_SUFFIXES = {".md", ".html", ".py", ".txt", ".yml", ".yaml", ".json", ".css", ".js", ".cfg", ".toml"}
dashed: list[str] = []
scanned = 0
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
    except UnicodeDecodeError:
        continue                                  # genuinely binary, not our business
    except OSError as exc:
        scan_errors.append(f"{rel}: {exc}")       # a file we MEANT to read and could not
        continue
    scanned += 1
    n = sum(body.count(d) for d in DASHES)
    if n:
        dashed.append(f"{rel} ({n})")
check("hyphens only across every tracked text file",
      scanned >= 10 and not scan_errors and not dashed,
      "; ".join(dashed + scan_errors) or f"only {scanned} files were scanned at all")

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
# `continue` used to DELETE this check when a page stopped quoting the figures - reword the
# claim and the caveat requirement silently disappeared along with it. The check is now
# always emitted, and at least one page has to still be carrying the figures, so the rule
# cannot evaporate by attrition.
carried = 0
for pname, body in (("index.html", index), ("walkthrough.html", walk)):
    for claims, caveats, label in BOUNDED:
        quoted = [c for c in claims if c in body]
        has = any(c.lower() in body.lower() for c in caveats)
        carried += len(quoted)
        check(f"{label} in {pname}", (not quoted) or has,
              f"quotes {', '.join(quoted)} with no limiting phrase")
check("the flip-test figures are still quoted somewhere a reader will meet them", carried > 0,
      "no page quotes them, so the rule above guards nothing")

# 10b. game.html needs a sharper version of the same rule, for two reasons.
# It is one file holding both the game and its test suite, and the first version of this
# scan was reading the SUITE's own regex literals - /(0 of 8|3 of 8|3 of 4)/ - as if they
# were prose a player reads. And a page-wide "is the caveat somewhere in this file" test is
# far too weak for an 8000-line file: a limit in the credits does not bound a number quoted
# in a battle tip 6000 lines earlier. So: shipped text only, and the limit has to live in
# the SAME string as the number it bounds.
game_txt = (ROOT / "game.html").read_text(encoding="utf-8")
shipped = game_txt.split("const TESTS = [")[0]
check("game.html's shipped half is separable from its test suite",
      "const TESTS = [" in game_txt and len(shipped) > 40000, f"{len(shipped)} chars before the suite")
FLIP = re.compile(r"0\s*(?:of|/)\s*8|3\s*(?:of|/)\s*8|3\s*(?:of|/)\s*4"
                  r"|none of eight|three of eight|three of four", re.I)
CAVEAT = re.compile(r"true by construction|not a benchmark|case study|case story"
                    r"|four verdicts is four verdicts|you cannot rerun", re.I)
strings = re.findall(r'"((?:[^"\\]|\\.)*)"', shipped)
quoting = [s for s in strings if FLIP.search(s)]
unbounded = [s for s in quoting if not CAVEAT.search(s)]
check("every flip-test figure a player reads carries its limit in the same breath",
      bool(quoting) and not unbounded,
      f"{len(quoting)} quote(s), unbounded: " + " | ".join(s[:90] for s in unbounded[:3]))

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

# 12. The ledger has to add up.
# It exists to make the title screen's battle count checkable, and on 2026-08-23 it was out
# by 521,024 because three separate updates edited the stated total rather than recomputing
# it. A reader with a calculator was the only check that would have caught it, so the build
# does that now: sum the campaign table, and require the ledger's own total and every figure
# quoted inside the game to match it exactly.
ledger = (ROOT / "tools" / "BALANCE-LEDGER.md").read_text(encoding="utf-8")
rows = re.findall(r"^\| lab\d+[^|]*\|\s*([\d,]+)\s*\|", ledger, re.M)
table_sum = sum(int(r.replace(",", "")) for r in rows)
stated = re.search(r"\*\*Published total: ([\d,]+) battles\*\*", ledger)
check("the ledger states a total", bool(stated) and len(rows) >= 6,
      f"{len(rows)} campaign rows found")
if stated:
    said = int(stated.group(1).replace(",", ""))
    check("the ledger's campaigns add up to the total it claims", said == table_sum,
          f"table sums to {table_sum:,}, file claims {said:,} (out by {abs(said-table_sum):,})")
    quoted = set(re.findall(r"([\d][\d,]{6,})\s*\+?\s*(?:Monte Carlo|simulated|balance simulations|simulations)",
                            (ROOT / "game.html").read_text(encoding="utf-8")))
    wrong = sorted(q for q in quoted if int(q.replace(",", "")) != table_sum)
    # `not wrong` alone was true when `quoted` was EMPTY - reword the title screen to
    # "7.3M battles" and the headline stops being checked while this still prints PASS.
    check("every battle count in the game matches the ledger's arithmetic",
          bool(quoted) and not wrong,
          f"game says {', '.join(wrong)}; the table sums to {table_sum:,}"
          if wrong else "the game no longer quotes the figure in a form this can read")

# 12b. The landing page's roster claim tracks the shipped roster.
# It said "a roster of nine" for weeks after the Cleric was merged away and the roster
# became eight - the exact number the game's own menu shows anyone who recruits everyone.
# The claim is now derived: count the members table, require the page to state that number.
WORDS = {7: "seven", 8: "eight", 9: "nine", 10: "ten"}
mem_block = game_txt[game_txt.index("const MEMBERS = {"):game_txt.index("// ================= DATA: skills")]
roster_n = len(re.findall(r"^ (\w+):\{ name:\"", mem_block, re.M))
check("the members table still parses", 6 <= roster_n <= 12, f"counted {roster_n}")
if roster_n in WORDS:
    check(f"the landing page says the roster is {WORDS[roster_n]}",
          f"roster of {WORDS[roster_n]}" in index,
          f"the game ships {roster_n} members; index.html says otherwise")
    stale_words = [w for n, w in WORDS.items() if n != roster_n and f"roster of {w}" in index]
    check("no stale roster count survives anywhere on the page", not stale_words,
          f"still says roster of {', '.join(stale_words)}")
# And the page may not pin the in-game test count: the suite partly GENERATES its entries
# at load, so no static count can verify a pinned number - the title screen shows it live
# instead. A pinned "ships NNN of its own tests" is a number nobody can regenerate.
check("the page does not pin the live test count",
      not re.search(r"ships \d+ of its own tests", index),
      "quote the live screen, not a number that rots")

# 13. The mutation catalogue has to stay runnable.
# tools/mutation-lab.html publishes a kill rate against tools/mutations.json, and that number
# is only meaningful if every seeded defect still applies to the file it targets. A mutation
# whose search string has drifted does not fail loudly in the lab - it drops out of the
# denominator, quietly flattering the score. So the build checks the catalogue the same way
# the lab does, and refuses to let it rot.
cat_path = ROOT / "tools" / "mutations.json"
check("the mutation catalogue exists", cat_path.exists())
if cat_path.exists():
    import json

    cat = json.loads(cat_path.read_text(encoding="utf-8"))
    muts = cat.get("mutations", [])
    split = game_txt.index("const TESTS = [")
    stale, misplaced, noop, dupes = [], [], [], []
    seen_ids, seen_pairs = set(), set()
    for m in muts:
        f, r, mid = m.get("find", ""), m.get("replace", ""), m.get("id", "?")
        n = game_txt.count(f) if f else 0
        if n != 1:
            stale.append(f"{mid} matches {n}x")
        elif game_txt.index(f) > split:
            misplaced.append(mid)
        if f == r:
            noop.append(mid)
        if mid in seen_ids or (f, r) in seen_pairs:
            dupes.append(mid)
        seen_ids.add(mid)
        seen_pairs.add((f, r))
    check("every seeded defect still applies to game.html", not stale,
          "; ".join(stale[:4]) + (f" (+{len(stale)-4} more)" if len(stale) > 4 else ""))
    check("no seeded defect targets the test suite instead of the game", not misplaced,
          ", ".join(misplaced[:4]))
    check("no seeded defect is a no-op or a duplicate", not noop and not dupes,
          ", ".join((noop + dupes)[:4]))
    # The catalogue only grows. A survivor deleted to raise the score would make every later
    # number a lie, so the floor is asserted rather than trusted.
    check("the catalogue has not shrunk below its published size", len(muts) >= 250,
          f"{len(muts)} mutations, expected at least 250")
    origins = {m.get("origin", "author") for m in muts}
    # Three populations, and the distinction is load-bearing: guards were fitted to the first
    # two, and the third was sealed before any of them was written. Lose the tag and the
    # held-out number silently becomes an in-sample one.
    check("the catalogue still records who designed each defect",
          {"author", "independent", "held-out"} <= origins,
          f"origins present: {sorted(origins)}")

# The project count in the prose must match the shipped cards - the four-vs-five drift
# of 2026-08-31 showed a count with no gate quietly forks across meta/og/thesis/about.
_cards = index.count('<div class="card"')
_words = {"four": 4, "five": 5, "six": 6, "seven": 7}
_claims = re.findall(r"\b(Four|Five|Six|Seven|four|five|six|seven) open-source projects", index)
check("the copy states the project count somewhere", bool(_claims))
check("every project-count word matches the shipped cards",
      all(_words[w.lower()] == _cards for w in _claims),
      f"copy says {sorted(set(_claims))}, cards: {_cards}")

print()
if FAILS:
    print(f"{len(FAILS)} FAILED")
    sys.exit(1)
print("ALL PASS")
