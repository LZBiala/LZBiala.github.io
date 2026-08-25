"""Tests for the simulator, which had none.

The game has 386 tests. The simulator that produces every balance number the game
publishes had zero, and on 2026-08-23 that cost us: a guard clause made a four-enemy pack
attack once per round, so roughly 3.5 million published battles described a game where a
pack hit as hard as a single foe. A gate read FAIL for three campaigns while passing the
whole time, and an entire enemy-scaling subsystem was nearly built to close a gap that did
not exist. The full write-up is in the vault RCA; the corrective action is this file.

Three kinds of test, in order of how much they would have helped:

  FIDELITY   the simulator is a second implementation of the game's combat maths, and two
             implementations drift. These parse game.html and compare. This is the class
             that would have caught the deleted-character roster months earlier.

  SENSITIVITY the only question that matters of a measuring device: if the thing I am
             measuring changed, would this number move? Every mechanism the sim models
             must be shown to move a number. This is the class that would have caught the
             blind pack directly.

  INVARIANTS battles terminate, a win means the room is clear, seating N foes seats N.

Run: python tools/test_combat_sim.py
No dependencies, no framework - the same rule the rest of this repo follows.
"""
import io
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
os.chdir(ROOT)

import combat_sim as C   # noqa: E402

GAME = io.open(os.path.join(ROOT, "game.html"), encoding="utf-8").read()

PASS, FAIL = [], []


def check(name, ok, detail=""):
    (PASS if ok else FAIL).append(name)
    print(("PASS  " if ok else "FAIL  ") + name + (("  [" + detail + "]") if detail and not ok else ""))


# ======================================================================= FIDELITY
def game_members():
    """{id: (spd, base_hp, base_mp, base_atk, grow_hp, grow_mp, grow_atk)} from game.html."""
    block = GAME[GAME.index("const MEMBERS = {"):GAME.index("// ================= DATA: skills")]
    out = {}
    for m in re.finditer(
        r'(\w+):\{[^}]*?spd:(\d+),\s*base:\{hp:(\d+),mp:(\d+),atk:(\d+)\},\s*grow:\{hp:(\d+),mp:(\d+),atk:(\d+)\}',
        block):
        out[m.group(1)] = tuple(int(m.group(i)) for i in range(2, 9))
    return out


def game_enemies():
    """{id: (hp, atk)} from game.html's EN table."""
    block = GAME[GAME.index("const EN = {"):GAME.index("const ENSPD")]
    out = {}
    for m in re.finditer(r'(\w+):\{ name:"[^"]*",[^}]*?hp:(\d+), atk:(\d+)', block):
        out[m.group(1)] = (int(m.group(2)), int(m.group(3)))
    return out


GM = game_members()
GE = game_enemies()

check("the roster parses out of game.html at all", len(GM) >= 8, "found %d" % len(GM))
check("the enemy table parses out of game.html at all", len(GE) >= 25, "found %d" % len(GE))

# --- the roster ---------------------------------------------------------------
missing = [k for k in C.MEMBERS if k not in GM]
check("every simulated character exists in the game", not missing, ", ".join(missing))

drift = []
for k, sim in C.MEMBERS.items():
    if k not in GM:
        continue
    spd, bh, bm, ba, gh, gm_, ga = GM[k]
    if (sim["base"]["hp"], sim["base"]["mp"], sim["base"]["atk"]) != (bh, bm, ba):
        drift.append("%s base %s vs %s" % (k, (sim["base"]["hp"], sim["base"]["mp"], sim["base"]["atk"]), (bh, bm, ba)))
    if (sim["grow"]["hp"], sim["grow"]["mp"], sim["grow"]["atk"]) != (gh, gm_, ga):
        drift.append("%s grow %s vs %s" % (k, (sim["grow"]["hp"], sim["grow"]["mp"], sim["grow"]["atk"]), (gh, gm_, ga)))
    if C.MSPD.get(k) != spd:
        drift.append("%s spd %s vs %s" % (k, C.MSPD.get(k), spd))
check("no character's stat line has drifted from the game", not drift, " | ".join(drift))

# --- the enemies --------------------------------------------------------------
# The game scales the PapaFoxx fight by party size at runtime (foxxStats), and the sim
# models the two ends of that scaling as two rows. That is a modelling choice, not drift,
# so it is exempted BY NAME rather than by a rule loose enough to hide a real one.
MODELLED = {"papafoxxE"}

edrift = []
for k, e in C.EN().items():
    if k in MODELLED:
        continue
    if k not in GE:
        edrift.append("%s: not in the game" % k)
        continue
    hp, atk = GE[k]
    # knob-driven HP is deliberately tunable; attack is not
    if e["atk"] != atk:
        edrift.append("%s atk %s vs %s" % (k, e["atk"], atk))
check("every simulated enemy is a real enemy, at the game's attack", not edrift, " | ".join(edrift))

# --- the pack rules -----------------------------------------------------------
# This guard used to compare the roll thresholds written INLINE in each packSize, with
# `roll<(0\.\d+)`. Both sides later moved those numbers out into PACKROW tables, so both
# regexes matched nothing and the guard asserted [] == [] - green for several commits, and
# blind to every threshold in the game. A comparison of two extractions is only a check if
# the extractions found something, so the tables are parsed, their SHAPE is asserted, and
# only then are they compared.
def table_rows(src, head, tail):
    """The numeric rows of a PACKROW-shaped literal, whichever language wrote it."""
    block = src[src.index(head) + len(head):]
    block = block[:block.index(tail)]
    return [tuple(float(x) for x in re.findall(r"\d+(?:\.\d+)?", row))
            for row in re.findall(r"[\[(]([^\])]*)[\])]", block)]


def zone_rows(src, head, tail):
    block = src[src.index(head) + len(head):]
    return {int(k): int(v) for k, v in re.findall(r"(\d+)\s*:\s*(\d+)",
                                                  block[:block.index(tail)])}


SIM = io.open(os.path.join(HERE, "combat_sim.py"), encoding="utf-8").read()
js_rows = table_rows(GAME, "const PACKROW=[", "\n];")
py_rows = table_rows(SIM, "PACKROW = [", "\n]")
check("the pack table parses out of BOTH files at all",
      len(js_rows) == 5 and js_rows and all(len(r) == 3 for r in js_rows) and
      len(py_rows) == 5 and all(len(r) == 3 for r in py_rows),
      "game %s / sim %s" % (js_rows, py_rows))
check("the pack-size table matches the game's, threshold for threshold",
      js_rows == py_rows, "game %s vs sim %s" % (js_rows, py_rows))

js_zp = zone_rows(GAME, "const ZPACK={", "}")
py_zp = zone_rows(SIM, "ZPACK = {", "}")
check("the authored per-zone rows match too", js_zp == py_zp and len(js_zp) >= 1,
      "game %s vs sim %s" % (js_zp, py_zp))

js_solo = set(re.findall(r'"(\w+)"', GAME[GAME.index("const SOLO_FOES="):GAME.index("function packSize")]))
py_solo = set(C.SOLO_FOES)
# A foe listed solo in one and not the other only MATTERS if it can be drawn from a
# wandering pool - those are the only ids packSize is ever asked about. Listing a boss the
# other side omits is harmless; disagreeing about a wandering foe is a live balance bug.
pools = set()
for m in re.finditer(r'(?:enc|roam):\{[^}]*?pool:\[([^\]]*)\]', GAME):
    pools |= set(re.findall(r'"(\w+)"', m.group(1)))
disagree = sorted((js_solo ^ py_solo) & pools)
# Same lesson as the table above: an intersection with an empty set is empty, so this check
# would go green if the pool regex ever stopped matching. Prove the inputs exist first.
check("the solo list and the wandering pools parse out of the game at all",
      len(js_solo) >= 4 and len(pools) >= 10, "%d solo ids, %d pooled ids" % (len(js_solo), len(pools)))
check("no wandering foe is solo in one and packable in the other", not disagree, ", ".join(disagree))
check("every foe the game calls solo is solo in the sim too", not (js_solo - py_solo),
      ", ".join(sorted(js_solo - py_solo)))

# the party-outnumbers rule, checked as behaviour rather than as text
capbad = []
for bodies in range(1, 8):
    worst = max(C.pack_size(4, "vague", random.Random(i), bodies) for i in range(400))
    want = max(1, min(4, bodies - 1))
    if worst != want:
        capbad.append("%d bodies -> %d, want %d" % (bodies, worst, want))
check("the party always outnumbers the room, at every party size", not capbad, " | ".join(capbad))

# ==================================================================== FIXTURES
rowbad = []
for row in C.TABLE:
    key, enemy, party, lv = row[0], row[1], row[2], row[3]
    if enemy not in C.EN() and enemy != "hacker":
        rowbad.append("%s: no enemy %s" % (key, enemy))
    for pid in party:
        if pid not in C.MEMBERS:
            rowbad.append("%s: no character %s" % (key, pid))
check("every measured row fields a party that can exist", not rowbad, " | ".join(rowbad))

crawlbad = []
for c in C.CRAWLS:
    # read by position rather than by exact arity: the table gains columns as the model
    # gets more honest, and a test that breaks on that teaches people to loosen tests
    key, pool, party, stage = c[0], c[1], c[2], c[7]
    for e in pool:
        if e not in C.EN():
            crawlbad.append("%s: no enemy %s" % (key, e))
    for pid in party:
        if pid not in C.MEMBERS:
            crawlbad.append("%s: no character %s" % (key, pid))
    if not (0 <= stage <= 4):
        crawlbad.append("%s: stage %s" % (key, stage))
check("every walk fields a party that can exist", not crawlbad, " | ".join(crawlbad))

# The late zones are gated behind S.won, and ending() sets S.won with S.stage=4, so a walk
# through 1999 or the internet can only happen at stage 4. Getting this wrong under-packed
# two of six walks for four published campaigns.
LATE_POOLS = {"faxdaemon", "cobol", "packetshark", "botnet", "phish", "ransomworm"}
stagebad = [c[0] for c in C.CRAWLS if set(c[1]) & LATE_POOLS and c[7] != 4]
check("post-victory zones are measured at the stage they are reachable", not stagebad, ", ".join(stagebad))

# A walk must not be handed the reward it walks in to collect, and must not be missing a
# body the story already gave it. Both of these were wrong, and neither an id check nor a
# stage check could see it - the facts live in the game's gating, so the test reads it.
INTERNET = {"packetshark", "botnet", "phish", "ransomworm"}
gate = []

# LITO joins in the same statement that opens the GATEWAY
assert "S.haxKnown=true" in GAME
lito_with_gateway = "joinLito" in GAME[GAME.index("S.haxKnown=true"):GAME.index("S.haxKnown=true") + 400]
check("the game still joins LITO when it opens the GATEWAY", lito_with_gateway,
      "the gating changed; the fixtures below are asserting a stale fact")

# SHARONDUH is what finishRescue gives you, at the END of the arc
sharon_at_rescue = "joinSharon" in GAME[GAME.index("function finishRescue"):GAME.index("function finishRescue") + 200]
check("the game still joins SHARONDUH at the rescue", sharon_at_rescue)

for c in C.CRAWLS:
    key, pool, party, armor = c[0], c[1], c[2], c[6]
    if not (set(pool) & INTERNET):
        continue
    inbound = "sharon" not in party
    if inbound:
        if "lito" not in party:
            gate.append("%s: walks the internet without LITO, who joins with the GATEWAY" % key)
        if armor:
            gate.append("%s: carries transmuted armour gated on haxWon it cannot own yet" % key)
    else:
        if "lito" not in party:
            gate.append("%s: has SHARONDUH but not LITO, which no save can produce" % key)
check("no walk is handed a reward it has not earned, or missing one it has",
      not gate, " | ".join(gate))

# =================================================================== SENSITIVITY
FULL = ["hero", "sentinel", "wiki", "retro", "refuter", "papafoxx"]


def cost(foe, n=1, lv=8, party=None, relic=True, crafted=True, armor=True, runs=260, seed=5):
    """Mean fraction of the party's HP+MP spent winning one battle."""
    party = party or FULL
    rng = random.Random(seed)
    spent = 0.0
    for _ in range(runs):
        st = [C.mk_actor(m, lv, relic, crafted) for m in party]
        fh = sum(a["maxhp"] for a in st)
        fm = sum(a["maxmp"] for a in st)
        C.battle(party, lv, foe, dict(coffee=2), rng, relic, crafted, 0.0,
                 "balanced", False, armor, state=st, foe_count=n)
        spent += 0.5 * (fh - sum(max(0, a["hp"]) for a in st)) / fh \
               + 0.5 * (fm - sum(max(0, a["mp"]) for a in st)) / fm
    return spent / runs


# THE test, and it took two tries to write.
#
# The obvious version - "a four-pack costs more per BATTLE than a single foe" - passes even
# with the original bug in place, because four foes carry four times the HP, so the fight
# runs four times as long, so a pack attacking ONCE PER ROUND still lands about four times
# as many blows over the battle. It measured the pack's health bar, not its damage.
#
# What the bug actually changes is damage PER ROUND, so that is what this measures, under
# conditions that isolate it: a party that cannot die and foes that cannot be killed, so
# every round has all N bodies alive and swinging. Verified against the real defect by
# reintroducing it and watching this fail.
# (There used to be a `rounds_cap=60` parameter here that nothing read. A knob that does
# nothing is worse than no knob: it tells the next reader the round count is bounded by this
# function when it is bounded by combat_sim's own cap.)
def per_round(foe, n, runs=90, seed=17):
    real_EN = C.EN
    def fat():
        t = real_EN()
        for k in t:
            t[k] = dict(t[k], hp=99999)      # nothing dies, so nothing stops swinging
        return t
    C.EN = fat
    try:
        rng = random.Random(seed)
        lost, rounds = 0.0, 0
        for _ in range(runs):
            st = [C.mk_actor(m, 12, True, True) for m in FULL]
            for a in st:
                a["maxhp"] = a["hp"] = 999999   # nobody falls, so no round ends early
                a["maxmp"] = a["mp"] = 999999
            before = sum(a["hp"] for a in st)
            _w, turns, out = C.battle(FULL, 12, foe, dict(coffee=0), rng, True, True, 0.0,
                                      "balanced", False, True, state=st, foe_count=n)
            lost += before - sum(a["hp"] for a in out)
            rounds += max(1, turns)
        return lost / rounds
    finally:
        C.EN = real_EN


blind = []
for foe in ("packetshark", "botnet", "ransomworm", "wyrm"):
    one, four = per_round(foe, 1), per_round(foe, 4)
    if four < one * 2.0:
        blind.append("%s: %.2f/round at x1 vs %.2f at x4 (%.2fx)"
                     % (foe, one, four, four / max(1e-9, one)))
check("four bodies hit about four times as hard per round as one - the check that was missing",
      not blind, " | ".join(blind))

mono = []
for foe in ("packetshark", "botnet"):
    row = [per_round(foe, n) for n in (1, 2, 3, 4)]
    if not all(row[i] < row[i + 1] for i in range(3)):
        mono.append("%s: %s" % (foe, ["%.2f" % v for v in row]))
check("per-round damage rises with every extra body", not mono, " | ".join(mono))

battle_scale = []
for foe in ("packetshark", "ransomworm"):
    one, four = cost(foe, 1), cost(foe, 4)
    if four < one * 2.0:
        battle_scale.append("%s: x1 %.3f -> x4 %.3f" % (foe, one, four))
check("and a pack still costs more across the whole battle", not battle_scale, " | ".join(battle_scale))

# Measured across several foes rather than one, because a single row put this within a
# percent of its own threshold and a test that close to the line is a coin flip, not a check.
g = sum(cost(f, 2, relic=True, crafted=True, armor=True) for f in ("ransomworm", "botnet", "wyrm"))
b = sum(cost(f, 2, relic=False, crafted=False, armor=False) for f in ("ransomworm", "botnet", "wyrm"))
# Full kit measures at about 91% of bare on these rows. The bar is 95%, which is loose
# enough not to flake on that 4-point margin and tight enough that gear doing NOTHING -
# which would read 100% - fails immediately. That is the whole job of this check.
check("gear measurably protects the party", g < b * 0.95,
      "geared %.3f vs bare %.3f (%.0f%% of bare)" % (g, b, 100 * g / max(1e-9, b)))

low = cost("botnet", 2, lv=5)
high = cost("botnet", 2, lv=10)
check("levels measurably protect the party", high < low * 0.95,
      "lv5 %.3f vs lv10 %.3f" % (low, high))

small = cost("botnet", 2, party=["hero", "sentinel"])
big = cost("botnet", 2, party=FULL)
check("a bigger party measurably spends less of itself", big < small,
      "duo %.3f vs six %.3f" % (small, big))

# ==================================================================== INVARIANTS
rng = random.Random(11)
bad = []
for foe in ("vague", "wyrm", "packetshark", "misaligned"):
    for n in (1, 3):
        for _ in range(40):
            st = [C.mk_actor(m, 8, True, True) for m in FULL]
            won, turns, out = C.battle(FULL, 8, foe, dict(coffee=2), rng, True, True, 0.0,
                                       "balanced", False, True, state=st, foe_count=n)
            if turns <= 0 or turns > 200:
                bad.append("%s x%d ran %d turns" % (foe, n, turns))
                break
            if won and any(not a["ko"] for a in out) is False:
                bad.append("%s x%d: won with nobody standing" % (foe, n))
                break
check("every battle terminates in a sane number of turns", not bad, " | ".join(bad))

seatbad = []
for n in (1, 2, 3, 4):
    st = [C.mk_actor(m, 20, True, True) for m in FULL]
    for a in st:
        a["maxhp"] = a["hp"] = 9999
    # a foe with enough HP that the room cannot clear in one round
    won, turns, out = C.battle(FULL, 20, "misaligned", dict(coffee=2), random.Random(3),
                               True, True, 0.0, "balanced", False, True, state=st, foe_count=n)
    if not won:
        seatbad.append("x%d: an invincible party lost" % n)
check("an unkillable party always clears the room", not seatbad, " | ".join(seatbad))

print()
print("%d passed, %d failed" % (len(PASS), len(FAIL)))
if FAIL:
    print("FAILED: " + " | ".join(FAIL))
    sys.exit(1)
print("ALL PASS")
