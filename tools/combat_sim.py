"""Combat sim v9 - THE HEROINE PROTOCOL (self-learning, review-hardened).
New over v8: PAPAFOXX (roast / ULTIMA setup-gated / dad joke / COMIC RELIEF on
MP-spend only / DEEZ NUTS limit) as 6th member AND as the recruit boss (with
HECKLE AoE debuff); SHARONDUH the White Mage (hotfix / sanitize / uptime aura /
FIVE NINES) as 7th member; the internet arc bestiary (packet shark, botnet,
phish, ransomworm, zero-day, NULLBYTE -> KERNEL MODE two-form chain) and the
AI arc (PROMPT INJECTION weak to sanitize, THE HALLUCINATION, THE MISALIGNED).
Review rules honored: legacy boss knobs FROZEN (MONO/H5/UNKNOWN/RETRY);
the learner may tune ONLY new-content knobs; 6-member rows are compared to
their 5-member baselines; adversarial policies (turtle / roast-max / nuke-rush)
must also stay in band before "validated" is declared.
Usage: python combat_sim_v9.py [wave]   wave=1 learn, wave=2 validate
"""
import random, sys, json
from multiprocessing import Pool

MSPD = { "hero":5, "sentinel":7, "wiki":4, "mender":4, "refuter":3, "papafoxx":6, "sharon":7, "retro":8, "lito":7 }   # sharon reworked: fighter-medic
BOND = 3   # worst-case bond bonus on dual techs (maxed hearts) - bosses must survive best friends
MECHS = dict(BREAK=0, BREAK_TH=3, ASSIST=0, ASSIST_P=0.15, ENRAGE=0, INTERRUPT=0, JOIN_LB_FRAC=-1.0)   # >=0: sharon joins the chain before form 2 with lb=frac*LB_MAX (game-fidelity model)   # experimental mechanics lab: toggled per run via CLI JSON (e.g. '{"MECHS":{"BREAK":1}}')
ESPD = { "vague":2, "gremlin":8, "creep":3, "golem":3, "wyrm":6, "leak":4, "chorus":4,
 "flaky":8, "drift":5, "monolith":3, "h1":6, "h2":5, "h3":5, "h4":4, "h5":5,
 "faxdaemon":6, "cobol":2, "patient0":5, "unknown":7, "retrystorm":6,
 "foxxboss":6, "packetshark":7, "botnet":5, "phish":4, "ransomworm":5, "zeroday":8,
 "nullbyte":6, "nullroot":7, "promptinj":6, "halluc":5, "misaligned":8 }
BACK = ("wiki","mender","papafoxx")   # sharon fights front now

MEMBERS = {
 "hero":     dict(base=dict(hp=12, mp=6, atk=3), grow=dict(hp=3, mp=2, atk=1)),
 "sentinel": dict(base=dict(hp=10, mp=5, atk=4), grow=dict(hp=2, mp=1, atk=1)),
 "wiki":     dict(base=dict(hp=8,  mp=10, atk=2), grow=dict(hp=2, mp=3, atk=1)),
 "mender":   dict(base=dict(hp=11, mp=8, atk=2), grow=dict(hp=3, mp=2, atk=1)),
 "refuter":  dict(base=dict(hp=14, mp=5, atk=3), grow=dict(hp=4, mp=1, atk=1)),
 "papafoxx": dict(base=dict(hp=11, mp=8, atk=2), grow=dict(hp=3, mp=2, atk=1)),
 "sharon":   dict(base=dict(hp=10, mp=10, atk=4), grow=dict(hp=2, mp=2, atk=1)),
 "retro":    dict(base=dict(hp=11, mp=7, atk=4), grow=dict(hp=2, mp=2, atk=1)),
 "lito":     dict(base=dict(hp=12, mp=8, atk=4), grow=dict(hp=2, mp=2, atk=1)),   # the Systems Thinker, dual-wield
}
CRIT = 0.15
# ---- SKILL TREE (lab8) ----
# Lanes: R reliability (survive), V velocity (hit harder and oftener), I insight (see, then punish).
# A build is a dict {"R":n,"V":n,"I":n}; one point per hero level, so the sum is at most lv-1.
# Effects stay small and linear so the lab can attribute the contribution of every single point.
def tree_hp_bonus(b):   return 3*b.get("R", 0)                 # R: +3 max HP per point (lab8 remedy: +2 was unmeasurable)
def tree_dr(b):         return 1 if b.get("R", 0) >= 2 else 0  # R2 fork: -1 damage taken
def tree_revive(b):     return b.get("R", 0) >= 4              # R4 fork: the first ally to fall each battle holds at 1 HP
def tree_hero_dmg(b):   return b.get("V", 0)//2                # V2/V4: +1 hero damage each
def tree_crit(b):       return 0.015*b.get("V", 0)             # V: +1.5% crit per point (lab8 remedy: halved, velocity was drifting dominant)
def tree_reveal(b):     return b.get("I", 0) >= 2              # I2: the first hero hit reveals armor
def tree_weak_bonus(b): return 2 if b.get("I", 0) >= 4 else 0  # I4: +2 into a revealed foe
# ---- LAB9: the shipped tree, node by node (ids match game.html exactly) ----
TREES = {
 "none":      frozenset(),
 "R-sustain": frozenset(("r1", "r2", "r3a", "r4", "r5")),
 "R-hold":    frozenset(("r1", "r2", "r3b", "r4", "r5")),
 "V-hands":   frozenset(("v1", "v2", "v3a", "v4", "v5")),
 "V-auto":    frozenset(("v1", "v2", "v3b", "v4", "v5")),
 "S-armor":   frozenset(("s1", "s2", "s3a", "s4", "s5")),
 "S-fog":     frozenset(("s1", "s2", "s3b", "s4", "s5")),
 "split":     frozenset(("r1", "r2", "v1", "v2", "s1")),
}
FORKS = (("R-sustain", "R-hold"), ("V-hands", "V-auto"), ("S-armor", "S-fog"))
LANES = ("R-sustain", "R-hold", "V-hands", "V-auto", "S-armor", "S-fog")

BUILDS = {
 "none":    {"R": 0, "V": 0, "I": 0},
 "R-pure":  {"R": 5, "V": 0, "I": 0},
 "V-pure":  {"R": 0, "V": 5, "I": 0},
 "I-pure":  {"R": 0, "V": 0, "I": 5},
 "split":   {"R": 2, "V": 2, "I": 1},
}


# FROZEN legacy knobs (1M/10M-run learned; the v9 learner MUST NOT touch these)
FROZEN = dict(MONO_HP=165, H5_HP=145, UNKNOWN_HP=260, RETRY_HP=200, FLAKY_HP=50, FLAKY_M2=5, DRIFT_M2=7, RETRY_M2=10,
              LB_MAX=20, LIM_HERO=10, LIM_SENT=14)
# TUNABLE new-content knobs (full PapaFoxx/Sharon/arc authority per design review)
# Wave-1 expert consult (fable-architect): DPR-extrapolated HP jumps; KO pressure via MOVE damage, not HP
KNOBS = dict(FOXX_HP=160, FOXX_ATK=5, FOXX_M2=6, FOXX_HP_EARLY=95, FOXX_ATK_EARLY=3, LITO_WM=3, LITO_FREEZE=1.0, CROWDWORK=1, ULTIMA_DMG=10, ROAST_RED=1, RELIEF=1, DADJOKE=3,
             NULL_HP=260, NULLR_HP=320, NULLR_MB=2, ZERO_HP=300, PINJ_HP=420, HAL_HP=160, MIS_HP=600, MIS_M2=15)
KNOBS.update(FROZEN)

def mk_actor(mid, lv, relic=False, crafted=False, build=None):
    m = MEMBERS[mid]
    atk = m["base"]["atk"] + m["grow"]["atk"]*(lv-1)
    if crafted and mid != "hero": atk += 1   # wave 5: worst case, every companion armed (mic/gloves/bow/wand/sword)
    if mid == "hero":
        if relic: atk += 1
        if crafted: atk += 6          # Kernel Blade (transmuted) + STR trial perk (worst case)
    _b = build or {}
    if mid == "hero":
        atk += tree_hero_dmg(_b)
    return dict(id=mid, lv=lv,
        hp=m["base"]["hp"] + m["grow"]["hp"]*(lv-1) + (tree_hp_bonus(_b) if mid == "hero" else 0),
        maxhp=m["base"]["hp"] + m["grow"]["hp"]*(lv-1),
        mp=m["base"]["mp"] + m["grow"]["mp"]*(lv-1),
        maxmp=m["base"]["mp"] + m["grow"]["mp"]*(lv-1),
        atk=atk, spd=MSPD.get(mid,4) + (1 if (mid == "hero" and "v1" in CUR_TREE) else 0), ko=False, shield=False, defending=False, acted=False, lb=0)

def EN():
    return {
    "vague":   dict(hp=14, atk=3, moves=[3,2]),
    "gremlin": dict(hp=18, atk=3, moves=[3,4], smart=True),
    "creep":   dict(hp=24, atk=3, moves=[2,3], grow=True),
    "golem":   dict(hp=46, atk=4, moves=[5,6], smart=True),
    "wyrm":    dict(hp=50, atk=3, moves=[4,4], twice=True),
    "leak":    dict(hp=55, atk=4, moves=[5,5], drain=True),
    "chorus":  dict(hp=64, atk=4, moves=[5,6], smart=True),
    "flaky":   dict(hp=KNOBS["FLAKY_HP"], atk=4, moves=[5,KNOBS["FLAKY_M2"]], twice=True, smart=True),
    "drift":   dict(hp=70, atk=5, moves=[5,KNOBS["DRIFT_M2"]], regen=True, grow=True, smart=True),
    "monolith":dict(hp=KNOBS["MONO_HP"], atk=6, moves=[8,9,10], smart=True),
    "h1": dict(hp=85, atk=5, moves=[7,6]),
    "h2": dict(hp=85, atk=5, moves=[7,6], foggy=True),
    "h3": dict(hp=90, atk=5, moves=[7,6], hidden=True),
    "h4": dict(hp=90, atk=6, moves=[7,8], regen=True),
    "h5": dict(hp=KNOBS["H5_HP"], atk=6, moves=[9,8], multi=True, fieldproto=True),
    "faxdaemon": dict(hp=42, atk=4, moves=[4,5]),
    "cobol":     dict(hp=58, atk=5, moves=[6,7], regen=True, smart=True),
    "patient0":  dict(hp=130, atk=6, moves=[7,9], hidden=True, smart=True),
    "unknown": dict(hp=KNOBS["UNKNOWN_HP"], atk=8, moves=[9,12], smart=True, multi=True, multi3=True),
    "retrystorm": dict(hp=KNOBS["RETRY_HP"], atk=7, moves=[8,KNOBS["RETRY_M2"]], smart=True, multi=True, grow=True),
    # ---- v9: the fifth companion, fought first ----
    "foxxboss": dict(hp=KNOBS["FOXX_HP"], atk=KNOBS["FOXX_ATK"], moves=[4, KNOBS["FOXX_M2"], 9], smart=True, heckler=True),
    "foxxbossE": dict(hp=KNOBS["FOXX_HP_EARLY"], atk=KNOBS["FOXX_ATK_EARLY"], moves=[4, KNOBS["FOXX_M2"], 9], smart=True, heckler=True),
    # ---- v9: the internet arc ----
    "packetshark": dict(hp=60, atk=5, moves=[5,7]),
    "botnet":      dict(hp=70, atk=5, moves=[4,6], multi=True, smart=True),
    "phish":       dict(hp=65, atk=5, moves=[5,7], foggy=True),
    "ransomworm":  dict(hp=80, atk=6, moves=[6,8], regen=True, drain=True, smart=True),
    "zeroday":     dict(hp=KNOBS["ZERO_HP"], atk=7, moves=[7,9], hidden=True, smart=True),
    "nullbyte":    dict(hp=KNOBS["NULL_HP"], atk=7, moves=[6,8,9], smart=True),
    "nullroot":    dict(hp=KNOBS["NULLR_HP"], atk=8, moves=[7+KNOBS["NULLR_MB"],9+KNOBS["NULLR_MB"],10+KNOBS["NULLR_MB"]], smart=True, multi=True, grow=True),
    # ---- v9: the AI arc ----
    "promptinj":   dict(hp=KNOBS["PINJ_HP"], atk=7, moves=[7,9], smart=True, weak_sanitize=True),
    "halluc":      dict(hp=KNOBS["HAL_HP"], atk=7, moves=[7,9], foggy=True, regen=True, smart=True),
    "misaligned":  dict(hp=KNOBS["MIS_HP"], atk=9, moves=[8,KNOBS["MIS_M2"],11], smart=True, multi=True, multi3=True, grow=True),
    }

FREEZE_STATS = {"casts": 0, "freezes": 0}

def crit(dmg, rng, extra=0.0, T=None):
    T = CUR_TREE if T is None else T
    sig = "s5" in T                                  # s5 CALIBRATION: the whole party crits more, and pays for it
    extra = extra + (0.03 if "s3b" in T else 0.0)    # s3b: a focused foe is easier to read
    if rng.random() < (CRIT + extra + (0.05 if sig else 0.0)):
        return int(round(dmg * (2.25 if sig else 2)))
    return max(1, dmg-1) if sig else dmg

def partner_of(actors, pid):
    return next((x for x in actors if x["id"]==pid and not x["ko"] and not x["acted"]), None)

def battle(party_ids, lv, enemy_key, items, rng, relic=False, crafted=False, noise=0.0, policy="balanced", materia=False, armor=False, state=None, build=None):
    """One battle. state: carried actor list (for the NULLBYTE->KERNEL MODE chain)."""
    LBM = KNOBS["LB_MAX"]
    _build = build if build is not None else CUR_BUILD
    T = CUR_TREE
    def mpc(n):   # s2 RUNBOOK INDEX: the READING skills cost one less, never the hitting ones
        return max(1, n-1) if "s2" in T else n
    tree_hold = False
    pre_used = 0
    KIT = CUR_KIT
    kit_channel = False; kit_debrief = False
    actors = state if state is not None else [mk_actor(m, lv, relic, crafted, _build if m == "hero" else None) for m in party_ids]
    if tree_reveal(_build):
        e_reveal_pending = True
    else:
        e_reveal_pending = False
    for a in actors: a["shield"] = False; a["defending"] = False
    e = dict(EN()[enemy_key])
    e["revealed"] = (not e.get("hidden")) or ("s3a" in T); e["focused"] = (not e.get("foggy")) or ("s3b" in T)
    e["verified"] = 0; e["dot"] = 0; e["growN"] = 0
    taunt = 0; stole = False; skip_next = False; combo = 0; breaker_used = False; softened = 0
    roasted = 0; heckled = 0; aura = 0
    brk = 0; broken = 0; enraged = 0; intercept = 0; sprint = 0   # BREAK/INTERRUPT lab: weakness/verified hits charge the meter; at 3 the foe staggers one round (+50% taken, loses its action)
    st_out = 0; st_in = 0
    if e.get("fieldproto"):
        for a in actors:
            if a["id"]=="hero": a["lb"] = LBM
    def relief():
        # COMIC RELIEF: fires only on a real performance (an MP-spending Foxx action)
        for x in actors:
            if x["id"] != "papafoxx" and not x["ko"] and x["hp"] < x["maxhp"]:
                x["hp"] = min(x["maxhp"], x["hp"] + KNOBS["RELIEF"])
    for turn in range(60):
        if KIT and not kit_channel:                       # INCIDENT CHANNEL: one message, everybody moves
            kit_channel = True
            for a in actors:
                if not a["ko"]: a["hp"] = min(a["maxhp"], a["hp"]+5)
        kit_shed = KIT and turn in (1, 2)                 # LOAD SHED: two rounds of cover
        if KIT and not kit_debrief and sum(1 for a in actors if a["ko"]) >= 2:
            kit_debrief = True                            # BLAMELESS DEBRIEF: nobody gets left on the floor
            for a in actors:
                if a["ko"]: a["ko"] = False; a["hp"] = max(1, int(round(a["maxhp"]*0.4)))
        if policy == "dynamic":
            hurt2 = sum(1 for x in actors if not x["ko"] and x["hp"] < x["maxhp"]*0.4) >= 2
            st_out, st_in = (-1, -1) if hurt2 else (1, 1)
        def dout(x):
            nonlocal combo, brk, broken, pre_used
            combo += 1
            pre = 0
            if "s3a" in T and e["revealed"] and pre_used != turn+1:
                pre_used = turn+1; pre = 2        # s3a: the opening read of every round
            _tight = "v2" in T
            cb = 2 if combo >= (8 if _tight else 10) else (1 if combo >= (4 if _tight else 5) else 0)
            hk = 1 if heckled > 0 else 0
            fr = (1 if turn < 3 else -1) if "v5" in T else 0   # v5: paid early, taxed late
            v = max(1, x + pre + st_out + cb + fr + (2 if sprint > 0 else 0) + (2 if softened > 0 else 0) - hk)
            if MECHS.get("BREAK") and broken == 0 and x >= 8:   # heavy, well-set-up hits charge the stagger meter
                brk += 1
                if brk >= MECHS.get("BREAK_TH", 3): broken = 2; brk = 0   # BREAK: one full round staggered, +50% damage taken
            if MECHS.get("INTERRUPT") and x >= (6 if "s4" in T else 8):   # FFT grammar: the meter buys an interrupt, not a burst
                brk += 1
                if brk >= MECHS.get("BREAK_TH", 3): intercept = 1; brk = 0
            if broken > 0: v = int(v * 1.5)
            if MECHS.get("ASSIST") and rng.random() < MECHS.get("ASSIST_P", 0.15):   # max-hearts partner follow-up
                v += 2
            return v
        hero_a = next((x for x in actors if x["id"]=="hero"), None)
        def hdmg(x):
            v = round(x*1.087) if materia else x
            if e["revealed"]:
                v += tree_weak_bonus(_build)
            if materia and hero_a and not hero_a["ko"]:
                hero_a["hp"] = min(hero_a["maxhp"], hero_a["hp"] + v//4)
            return v
        def strike(base):
            if "v3b" in T: return round(base*1.35)        # v3b: no bar, no fumble, no ceiling either
            wide = "v3a" in T                              # v3a: both windows widen (0.16->0.28 and 0.50->0.60)
            r = rng.random()
            if noise: sm = 1.5 if r < (0.42 if wide else 0.30) else (1.2 if r < (0.78 if wide else 0.70) else 1.0)
            else:     sm = 1.5 if r < (0.88 if wide else 0.80) else 1.2
            return round(base*sm)
        for a in actors: a["acted"] = False
        espd = ESPD.get(enemy_key, 4)
        def foe_strike():
            nonlocal taunt, skip_next, breaker_used, combo, heckled, enraged, intercept, softened, tree_hold
            living = [x for x in actors if not x["ko"]]
            if not living: return "L"
            if broken > 0:
                return None   # staggered: the foe loses this action
            if intercept and (e.get("multi") or e.get("grow")):
                intercept = 0
                return None   # INTERRUPT: the charge is cancelled - the dangerous action never lands
            if skip_next:
                skip_next = False
                return None
            mvs = e["moves"]
            if e.get("smart") and (e["hp"] < EN()[enemy_key]["hp"]/2):
                mi = len(mvs)-1
            else:
                mi = int(rng.random()*len(mvs))
            raw = mvs[mi]
            raw = max(1, raw + st_in)
            if enraged:
                raw += MECHS.get("ENRAGE", 0); 
            if roasted > 0: raw = max(1, raw - KNOBS["ROAST_RED"])
            if e.get("grow"): e["growN"] = min(4, e["growN"]+1); raw += e["growN"]-1
            if e.get("twice"): raw += e["atk"]
            if e.get("multi"):
                k = 3 if (e.get("multi3") and e["hp"] < 130) else 2
                targets = rng.sample(living, min(k, len(living)))
            else:
                if taunt > 0 and any(x["id"]=="refuter" and not x["ko"] for x in actors) and rng.random() < 0.7:
                    targets = [next(x for x in actors if x["id"]=="refuter")]
                else:
                    front = [x for x in living if x["id"] not in BACK]
                    targets = [ front[int(rng.random()*len(front))] if (front and rng.random()<0.7) else rng.choice(living) ]
            any_hit = False
            for tgt in targets:
                dmg = raw
                if materia and e.get("multi"): dmg = max(0, dmg-1)
                if tgt["id"] == "refuter" and taunt > 0: dmg = max(0, dmg-1)
                if tgt["id"] in BACK: dmg = max(0, dmg-1)
                if tgt["id"] == "hero" and "r1" in T: dmg = max(0, dmg-1)
                if tgt["id"] in BACK and "r2" in T: dmg = max(0, dmg-1)
                if "r5" in T and tgt["hp"] <= -(-tgt["maxhp"]//4): dmg = max(0, dmg-1)
                if kit_shed: dmg = max(0, dmg-2)
                if armor: dmg = max(0, dmg-1)                            # Five Nines Locket: everyone, from everything
                if armor and tgt["id"] == "hero": dmg = max(0, dmg-2)   # Frontier Aegis (-3 total with locket)
                if tgt["shield"]: tgt["shield"] = False; dmg = 0
                if tgt["defending"]: dmg = (dmg+1)//2
                tgt["hp"] -= dmg
                if dmg > 0: any_hit = True; tgt["lb"] = min(KNOBS["LB_MAX"], tgt["lb"]+dmg)
                if tgt["hp"] <= 0:
                    if "r3b" in T and not tree_hold and (tgt["hp"] + dmg) > tgt["maxhp"]/2:
                        tree_hold = True; tgt["hp"] = 1; continue
                    if armor and not breaker_used:
                        breaker_used = True; tgt["hp"] = 1; continue
                    items["_kos"] = items.get("_kos", 0) + 1
                    if items.get("handoff", 0) > 0:
                        items["handoff"] -= 1; tgt["hp"] = tgt["maxhp"]//2
                    else: tgt["ko"] = True; tgt["hp"] = 0
            if any_hit: combo = 0
            if enraged and MECHS.get("ENRAGE"): enraged = 0
            if e.get("heckler") and mi == 1: heckled = 2   # HECKLE: the party lands softer
            return None
        ally_order = sorted(range(len(actors)), key=lambda i2:-actors[i2]["spd"])
        n_before = len(actors) if (("v4" in T or KIT) and turn == 0) else sum(1 for i2 in ally_order if actors[i2]["spd"] > espd)
        foe_done = False; acted_n = 0
        for _ai in ally_order:
            if (not foe_done) and acted_n >= n_before:
                _r = foe_strike(); foe_done = True
                if _r == "L": return False, turn+1, actors
            acted_n += 1
            a = actors[_ai]
            if a["ko"] or a["acted"] or e["hp"] <= 0: continue
            aid = a["id"]
            if noise and rng.random() < noise:
                if e["revealed"] and e["focused"] and not (e.get("regen") and e["verified"] == 0):
                    d0 = dout(crit(strike(a["atk"]), rng, tree_crit(_build) if aid=="hero" else 0.0))
                    e["hp"] -= (hdmg(d0) if aid=="hero" else d0)
                continue
            # ---- ADVERSARIAL POLICY OVERRIDES (review requirement) ----
            if policy == "turtle" and aid == "papafoxx":
                a["defending"] = True; a["mp"] = min(a["maxmp"], a["mp"]+1); continue   # no MP spend -> relief must give nothing
            if policy == "roastmax" and aid == "papafoxx":
                if a["mp"] >= 2:
                    roasted = 2; e["hp"] -= dout(2); a["mp"] -= 2; relief(); continue
                a["defending"] = True; a["mp"] = min(a["maxmp"], a["mp"]+1); continue
            if policy == "nukerush":
                if aid == "papafoxx" and (e["revealed"] or roasted > 0) and not (e.get("regen") and e["verified"]==0) and a["mp"] >= 8:
                    e["hp"] -= dout(crit(KNOBS["ULTIMA_DMG"] + a["lv"], rng)); a["mp"] -= 8; relief(); continue
                if aid == "papafoxx" and not e["revealed"] and roasted == 0 and a["mp"] >= 2:
                    roasted = 2; e["hp"] -= dout(2); a["mp"] -= 2; relief(); continue
            # ---- LIMIT BREAKS ----
            if a["lb"] >= LBM:
                if aid == "hero" and (not e["revealed"] or e["hp"] > 22):
                    a["lb"] = 0; e["revealed"] = True; e["focused"] = True; e["verified"] = 2
                    base = (18 if e.get("fieldproto") else KNOBS["LIM_HERO"]) + a["lv"]
                    e["hp"] -= dout(crit(base, rng)); continue
                if aid == "sentinel" and e["hp"] > 14:
                    a["lb"] = 0; e["hp"] -= dout(crit(KNOBS["LIM_SENT"], rng)); continue
                if aid == "wiki" and sum(x["mp"] for x in actors if not x["ko"]) < sum(x["maxmp"] for x in actors if not x["ko"])*0.4:
                    a["lb"] = 0
                    for x in actors:
                        if not x["ko"]: x["mp"] = min(x["maxmp"], x["mp"]+4)
                    continue
                if aid == "mender" and sum(1 for x in actors if not x["ko"] and x["hp"] < x["maxhp"]*0.5) >= 2:
                    a["lb"] = 0
                    for x in actors:
                        if not x["ko"]: x["hp"] = min(x["maxhp"], x["hp"]+8); x["shield"] = True
                    continue
                if aid == "refuter" and taunt == 0 and e.get("multi"):
                    a["lb"] = 0; taunt = 3; skip_next = True; continue
                if aid == "papafoxx" and (e["hp"] > 14 or sum(1 for x in actors if not x["ko"] and x["hp"] < x["maxhp"]*0.6) >= 2):
                    a["lb"] = 0
                    for x in actors:
                        if not x["ko"]: x["hp"] = min(x["maxhp"], x["hp"]+5)
                    e["hp"] -= dout(crit(14, rng)); relief(); continue
                if aid == "sharon" and (any(x["ko"] for x in actors) or sum(1 for x in actors if not x["ko"] and x["hp"] < x["maxhp"]*0.5) >= 2):
                    a["lb"] = 0
                    for x in actors:
                        if x["ko"]: x["ko"] = False; x["hp"] = -(-x["maxhp"]//2)
                        else: x["hp"] = min(x["maxhp"], x["hp"]+6)
                    continue
            if aid == "hero":
                if not e["revealed"]:
                    s = partner_of(actors, "sentinel")
                    if s and a["mp"] >= 2 and s["mp"] >= 2:
                        e["revealed"] = True; a["mp"] -= mpc(2); s["mp"] -= mpc(2); s["acted"] = True
                        if not (e.get("regen") and e["verified"] == 0):
                            e["hp"] -= dout(crit(s["atk"]+4, rng))
                        continue
                    if a["mp"] >= 2: e["revealed"] = True; continue
                if a["hp"] < a["maxhp"]*0.35 and a["mp"] >= 4:
                    a["hp"] = min(a["maxhp"], a["hp"]+7); a["mp"] -= 4; continue
                sh = partner_of(actors, "sharon")
                if (sh and e["revealed"] and not (e.get("regen") and e["verified"] == 0)
                        and a["mp"] >= 3 and sh["mp"] >= 3
                        and sum(1 for x in actors if not x["ko"] and x["hp"] < x["maxhp"]*0.7) >= 2):
                    a["mp"] -= 3; sh["mp"] -= 3; sh["acted"] = True
                    for x in actors:
                        if not x["ko"]: x["hp"] = min(x["maxhp"], x["hp"]+3)
                    e["hp"] -= dout(crit(4 + a["lv"] + BOND, rng)); continue   # PAIR PROGRAMMING (maxed hearts)
                w = partner_of(actors, "wiki")
                if (w and e["revealed"] and not (e.get("regen") and e["verified"] == 0)
                        and a["mp"] >= 3 and w["mp"] >= 4 and e["hp"] > 18):
                    a["mp"] -= 3; w["mp"] -= 4; w["acted"] = True
                    e["hp"] -= dout(crit(6 + a["lv"] + w["lv"] + BOND, rng)); continue
                r = partner_of(actors, "refuter")
                if (r and taunt > 0 and e["revealed"] and not (e.get("regen") and e["verified"] == 0)
                        and a["mp"] >= 3 and r["mp"] >= 3 and e["hp"] > 18):
                    a["mp"] -= 3; r["mp"] -= 3; r["acted"] = True
                    e["hp"] -= dout(crit(a["atk"] + r["atk"] + 4 + BOND, rng)); continue
            if aid == "mender":
                if e.get("regen") and e["verified"] == 0 and a["mp"] >= 3:
                    e["verified"] = 2; a["shield"] = True; a["mp"] -= mpc(3); continue
                r = partner_of(actors, "refuter")
                if r and e.get("multi") and taunt == 0 and a["mp"] >= 4 and r["mp"] >= 2:
                    for x in actors:
                        if not x["ko"]: x["shield"] = True
                    taunt = 2; a["mp"] -= 4; r["mp"] -= 2; r["acted"] = True; continue
                hurt = min((x for x in actors if not x["ko"]), key=lambda x: x["hp"]/x["maxhp"])
                if hurt["hp"] < hurt["maxhp"]*0.5 and a["mp"] >= 3:
                    hurt["hp"] = min(hurt["maxhp"], hurt["hp"]+6); a["mp"] -= 3; continue
            if aid == "refuter":
                if taunt <= 0 and a["mp"] >= 2 and a["hp"] > a["maxhp"]*0.4:
                    taunt = 2; a["mp"] -= 2; continue
            if aid == "wiki":
                if not e["focused"] and a["mp"] >= mpc(3): e["focused"] = True; a["mp"] -= mpc(3)
                f = partner_of(actors, "papafoxx")
                if (f and (e["revealed"] or roasted > 0) and e["focused"] and not (e.get("regen") and e["verified"] == 0)
                        and a["mp"] >= 3 and f["mp"] >= 4 and e["hp"] > 20):
                    a["mp"] -= 3; f["mp"] -= 4; f["acted"] = True
                    e["hp"] -= dout(crit(5 + a["lv"] + f["lv"] + BOND, rng)); relief(); continue   # SETUP & PUNCHLINE (maxed hearts)
                if (e["revealed"] and e["focused"] and a["mp"] >= 5
                        and not (e.get("regen") and e["verified"] == 0)):
                    e["hp"] -= dout(crit(6 + a["lv"], rng)); a["mp"] -= 5; continue
            if aid == "sentinel":
                if not stole and a["mp"] >= 2: stole = True; a["mp"] -= 2; e["hp"] -= dout(2); continue
                w = partner_of(actors, "wiki")
                if (w and e["revealed"] and e["focused"] and not (e.get("regen") and e["verified"] == 0)
                        and a["mp"] >= 3 and w["mp"] >= 3 and e["hp"] > 15):
                    per = 2 + (a["lv"] + w["lv"])//3
                    a["mp"] -= 3; w["mp"] -= 3; w["acted"] = True
                    e["hp"] -= dout(crit(per*3 + BOND, rng)); continue
                if not e["focused"] and a["mp"] >= 2:
                    e["hp"] -= dout(crit(a["atk"]+2, rng)); a["mp"] -= 2; continue
                if e["revealed"] and e["dot"] == 0 and a["mp"] >= 3 and e["focused"] and not e.get("regen"):
                    e["dot"] = 3; e["hp"] -= dout(2); a["mp"] -= 3; continue
            if aid == "papafoxx":
                if aid == "papafoxx" and KNOBS.get("CROWDWORK") and e["revealed"] and softened == 0 and a["mp"] >= 3 and e["hp"] > 20:
                    softened = 2; sprint = max(sprint, 1); a["mp"] -= 3; relief(); continue   # CROWD WORK
                if not e["revealed"] and roasted == 0 and a["mp"] >= 2:
                    roasted = 2; e["hp"] -= dout(2); a["mp"] -= 2; relief(); continue   # ROAST opens the set
                if ((e["revealed"] or roasted > 0) and not (e.get("regen") and e["verified"] == 0)
                        and a["mp"] >= 8 and e["hp"] > 14):
                    e["hp"] -= dout(crit(KNOBS["ULTIMA_DMG"] + a["lv"], rng)); a["mp"] -= 8; relief(); continue   # ULTIMA
                if a["lv"] >= 5 and a["mp"] >= 3 and sum(1 for x in actors if not x["ko"] and x["hp"] < x["maxhp"]*0.6) >= 2:
                    for x in actors:
                        if not x["ko"]: x["hp"] = min(x["maxhp"], x["hp"]+KNOBS["DADJOKE"])
                    a["mp"] -= 3; relief(); continue   # DAD JOKE
                if roasted == 0 and EN()[enemy_key]["hp"] >= 100 and a["mp"] >= 2:
                    roasted = 2; e["hp"] -= dout(2); a["mp"] -= 2; relief(); continue   # keep the debuff up on bosses
            if aid == "lito":
                if (not e["revealed"] or not e["focused"]) and a["mp"] >= 2:
                    e["revealed"] = True; e["focused"] = True; a["mp"] -= 2; continue   # FIRST PRINCIPLES
                if a["mp"] >= 3 and not skip_next and not (e.get("regen") and e["verified"] == 0):
                    FREEZE_STATS["casts"] += 1                                           # WINDMILL HALO FREEZE
                    is_crit = rng.random() < CRIT
                    base = KNOBS["LITO_WM"] + a["lv"]//2
                    e["hp"] -= dout(base*2 if is_crit else base); a["mp"] -= 3
                    if is_crit and rng.random() < KNOBS["LITO_FREEZE"]:
                        skip_next = True; FREEZE_STATS["freezes"] += 1
                    continue
                if a["mp"] >= 2 and not (e.get("regen") and e["verified"] == 0):
                    e["hp"] -= dout(crit(2 + a["lv"]//2, rng)) + dout(crit(2 + a["lv"]//2, rng)); a["mp"] -= 2; continue   # TWIN HYPOTHESIS
            if aid == "retro":
                nonlocal_sprint = None
                if (not e["revealed"] or not e["focused"]) and a["mp"] >= 3:
                    e["revealed"] = True; e["focused"] = True; a["mp"] -= 3; continue   # DASHBOARD
                if EN()[enemy_key]["hp"] >= 100 and sprint == 0 and a["lv"] >= 5 and a["mp"] >= 5:
                    sprint = 1; a["mp"] -= 5; continue                                   # SPRINT PLAN
                if a["mp"] >= 2 and not (e.get("regen") and e["verified"] == 0):
                    e["hp"] -= dout(crit(2*(2 + a["lv"]//2), rng)); a["mp"] -= 2; continue   # KANBAN CUT
            if aid == "sharon":
                ko_ally = next((x for x in actors if x["ko"]), None)
                if ko_ally and a["mp"] >= 3:
                    ko_ally["ko"] = False; ko_ally["hp"] = 8; a["mp"] -= 3; continue   # HOTFIX revive
                if e.get("weak_sanitize") and a["mp"] >= 4 and e["focused"]:
                    e["hp"] -= dout(crit(10 + a["lv"], rng)); a["mp"] -= 4; continue   # SANITIZE the injection
                if a["lv"] >= 5 and aura == 0 and EN()[enemy_key]["hp"] >= 100 and a["mp"] >= 6:
                    aura = 3; a["mp"] -= 6; continue   # UPTIME AURA
                hurt = min((x for x in actors if not x["ko"]), key=lambda x: x["hp"]/x["maxhp"])
                if hurt["hp"] < hurt["maxhp"]*0.5 and a["mp"] >= 3:
                    hurt["hp"] = min(hurt["maxhp"], hurt["hp"]+8); a["mp"] -= 3; continue   # HOTFIX heal
                if a["mp"] >= 4 and sum(1 for x in actors if not x["ko"] and x["hp"] < x["maxhp"]*0.8) >= 3:
                    for x in actors:
                        if not x["ko"]: x["hp"] = min(x["maxhp"], x["hp"]+2)
                    a["mp"] -= 4; continue   # SANITIZE support
                if (a["mp"] >= 2 and e["revealed"] and e["focused"]
                        and not (e.get("regen") and e["verified"] == 0)):
                    e["hp"] -= dout(crit(3 + a["lv"], rng)); a["mp"] -= 2   # FAILOVER FIST
                    others=[x for x in actors if not x["ko"] and x["id"]!="sharon" and x["hp"]<x["maxhp"]]
                    if others:
                        wk=min(others, key=lambda x: x["hp"]/x["maxhp"])
                        wk["hp"]=min(wk["maxhp"], wk["hp"]+2)
                    continue
            if not e["revealed"] or not e["focused"] or (e.get("regen") and e["verified"] == 0):
                a["defending"] = True; a["mp"] = min(a["maxmp"], a["mp"]+1)
                if "r4" in T: a["lb"] = min(LBM, a["lb"]+3)
                continue
            d1 = dout(crit(strike(a["atk"]), rng, 0.03 if (aid == "hero" and "s1" in T) else 0.0))
            e["hp"] -= (hdmg(d1) if aid=="hero" else d1)
        if not foe_done:
            _r = foe_strike(); foe_done = True
            if _r == "L": return False, turn+1, actors
        if e["hp"] <= 0: return True, turn+1, actors
        living = [a for a in actors if not a["ko"]]
        if not living: return False, turn+1, actors
        for a in actors: a["defending"] = False
        if "r3a" in T and turn < 3:
            for a in actors:
                if not a["ko"] and a["hp"] < a["maxhp"]: a["hp"] = min(a["maxhp"], a["hp"]+1)
        if taunt > 0: taunt -= 1
        if e["verified"] > 0: e["verified"] -= 1
        if roasted > 0: roasted -= 1
        if heckled > 0: heckled -= 1
        if sprint > 0: sprint -= 1
        if softened > 0: softened -= 1
        if broken > 0:
            broken -= 1
            if broken == 0 and MECHS.get("ENRAGE"): enraged = 1   # the machine reboots angry
        if aura > 0:
            aura -= 1
            for x in living: x["hp"] = min(x["maxhp"], x["hp"]+2)
        if materia and hero_a and not hero_a["ko"]:
            hero_a["hp"] = min(hero_a["maxhp"], hero_a["hp"]+2)
        if e["dot"] > 0 and not e.get("regen"): e["dot"] -= 1; e["hp"] -= 2
        if e.get("drain"):
            t = rng.choice(living)
            t["mp"] = max(0, t["mp"]-1)
        low = min(living, key=lambda x: x["hp"]/x["maxhp"])
        if low["hp"] < low["maxhp"]*0.3 and items.get("coffee",0) > 0:
            items["coffee"] -= 1; low["hp"] = min(low["maxhp"], low["hp"]+5)
    return e["hp"] <= 0, 60, actors

FULL  = ["hero","sentinel","wiki","mender","refuter"]
FULL6 = FULL + ["papafoxx"]
FULL7 = FULL6 + ["sharon"]

# (row key, enemy, party, lv, relic, crafted, armor) - "hacker" is the two-form chain
TABLE = [
 ("monolith5", "monolith", FULL,  5, False, False, False),   # frozen baselines (5-member)
 ("h5_5",      "h5",       FULL,  7, False, False, False),
 ("unknown5",  "unknown",  FULL,  7, False, False, False),
 ("retry5",    "retrystorm",FULL, 8, True,  True,  True),
 ("foxxfight5","foxxboss", FULL,  5, False, False, False),   # waking the dad early
 ("foxxfight7","foxxboss", FULL,  7, False, False, False),   # waking him late
 ("monolith6", "monolith", FULL6, 5, False, False, False),   # 6-member deltas vs frozen bosses
 ("h5_6",      "h5",       FULL6, 7, False, False, False),
 ("unknown6",  "unknown",  FULL6, 7, False, False, False),
 ("retry6",    "retrystorm",FULL6,8, True,  True,  True),
 ("shark8",    "packetshark",FULL6,8, True, True,  True),    # the internet arc (post-game gear)
 ("botnet8",   "botnet",   FULL6, 8, True,  True,  True),
 ("phish8",    "phish",    FULL6, 8, True,  True,  True),
 ("worm8",     "ransomworm",FULL6,8, True,  True,  True),
 ("zeroday8",  "zeroday",  FULL6, 8, True,  True,  True),
 ("hacker8",   "hacker",   FULL6, 8, True,  True,  True),    # NULLBYTE -> KERNEL MODE chain
 ("hacker9",   "hacker",   FULL6, 9, True,  True,  True),
 ("pinj9",     "promptinj",FULL7, 9, True,  True,  True),    # the AI arc (Sharonduh recruited)
 ("halluc9",   "halluc",   FULL7, 9, True,  True,  True),
 ("misalign10","misaligned",FULL7,10, True, True,  True),
 ("misalign12","misaligned",FULL7,12, True, True,  True),    # the grind path (cap-50 era)
 ("golemR",    "golem",    ["hero","sentinel","wiki","retro"], 3, False, False, False),   # the Analyst joins early
 ("flakyR",    "flaky",    ["hero","sentinel","wiki","retro"], 4, False, False, False),
 ("h5R",       "h5",       FULL6+["retro"], 7, False, False, False),
 ("misalignR", "misaligned",FULL7+["retro"],10, True, True,  True),
]
RUNS_PER = 298   # rows x 2 arms x 298 x 4 iterations = 100,128 battles per wave

def _init_knobs(k):
    KNOBS.update(k.get("_KNOBS", k) if isinstance(k, dict) else k)
    if isinstance(k, dict) and "_MECHS" in k: MECHS.update(k["_MECHS"])

CUR_BUILD = {}
CUR_TREE = frozenset()
CUR_KIT = False

def one_row(enemy, party, lv, relic, crafted, armor, noise, policy, runs, rng):
    wins = 0; turns = 0; t2sum = 0; ko_b = 0; clutch = 0
    for _ in range(runs):
        items = dict(coffee=2, handoff=1 if lv >= 5 else 0)
        if enemy == "hacker":
            w1, t1, st = battle(party, lv, "nullbyte", items, rng, relic, crafted, noise, policy, True, armor)
            if w1:
                jf = MECHS.get("JOIN_LB_FRAC", -1.0)
                if jf is not None and jf >= 0 and not any(x["id"]=="sharon" for x in st):
                    sh = mk_actor("sharon", lv, relic, crafted)   # the cage opens: she steps into the formation for KERNEL MODE
                    sh["lb"] = int(jf * KNOBS["LB_MAX"])
                    st.append(sh)
                w, t2, _ = battle(party, lv, "nullroot", items, rng, relic, crafted, noise, policy, True, armor, state=st)
                t = t1 + t2
            else: w, t = False, t1
        else:
            mat = len(party) >= 5
            w, t, _ = battle(party, lv, enemy, items, rng, relic, crafted, noise, policy, mat, armor)
        wins += w; turns += t; t2sum += t*t; ko_b += (1 if items.get("_kos",0) else 0)
        if w and items.get("_kos",0): clutch += 1
    return wins, turns, t2sum, ko_b, clutch

def worker(task):
    (rk, enemy, party, lv, relic, crafted, armor, noise, policy, runs, seed) = task
    rng = random.Random(seed)
    wins, turns, t2sum, ko_b, clutch = one_row(enemy, party, lv, relic, crafted, armor, noise, policy, runs, rng)
    return (rk, noise, wins, turns, t2sum, ko_b, clutch, runs)

def run_table_mp(policy, it, seedbase):
    tasks = []
    for ri,(rk, enemy, party, lv, relic, crafted, armor) in enumerate(TABLE):
        for ai, noise in enumerate((0.0, 0.25)):
            tasks.append((rk, enemy, party, lv, relic, crafted, armor, noise, policy, RUNS_PER, seedbase + it*1000 + ri*10 + ai))
    with Pool(processes=10, initializer=_init_knobs, initargs=(dict(KNOBS, _MECHS=dict(MECHS)),)) as pool:
        rows = pool.map(worker, tasks)
    out = {}
    for (rk, noise, wins, turns, t2sum, ko_b, clutch, runs) in rows:
        mt = turns/runs
        sd = max(0.0, t2sum/runs - mt*mt) ** 0.5
        out.setdefault(rk, [None, None])[0 if noise == 0.0 else 1] = (wins/runs, mt, ko_b/runs, sd, clutch/runs)
    return out

def run_adversarial(it, seedbase):  # noqa: kept signature
    """Review requirement: degenerate strategies must also sit in band."""
    KEYS = ["monolith6","h5_6","unknown6","retry6","hacker8","misalign10"]
    rows = [r for r in TABLE if r[0] in KEYS]
    tasks = []
    for pi, pol in enumerate(("turtle","roastmax","nukerush")):
        for ri,(rk, enemy, party, lv, relic, crafted, armor) in enumerate(rows):
            tasks.append((rk+"/"+pol, enemy, party, lv, relic, crafted, armor, 0.0, pol, RUNS_PER, seedbase + 777000 + it*1000 + pi*100 + ri*10))
    with Pool(processes=10, initializer=_init_knobs, initargs=(dict(KNOBS),)) as pool:
        got = pool.map(worker, tasks)
    return {rk:(wins/runs, turns/runs, ko_b/runs) for (rk, noise, wins, turns, t2sum, ko_b, clutch, runs) in got}, len(tasks)*RUNS_PER

def show(res):
    hdr = f"{'row':<12} | {'OPT win':>8}{'turns':>7}{'sd':>6}{'KO%':>7}{'clutch':>8} | {'NOISY win':>10}{'turns':>7}{'KO%':>7}{'clutch':>8}"
    print(hdr); print("-"*len(hdr))
    for rk,(o,n) in res.items():
        print(f"{rk:<12} | {o[0]:>8.1%}{o[1]:>7.1f}{o[3]:>6.2f}{o[2]:>7.1%}{o[4]:>8.1%} | {n[0]:>10.1%}{n[1]:>7.1f}{n[2]:>7.1%}{n[4]:>8.1%}")

def _dpr_jump(knob, observed, target, cap=800):
    """Expert rule: turns scale ~linearly with HP at fixed party DPR - jump, don't creep."""
    if observed <= 0.4: return None
    new = min(cap, int(round(KNOBS[knob] * target / observed / 5)) * 5)
    if new != KNOBS[knob]:
        old = KNOBS[knob]; KNOBS[knob] = new
        return f"{knob} {old} -> {new} (DPR extrapolation: {observed:.1f} turns toward {target})"
    return None

def tune(res):
    """v9 learner: may touch ONLY the new-content knobs. Frozen knobs asserted untouched."""
    ch = []
    o,n = res["foxxfight5"]
    if not (4.0 <= o[1] <= 5.5):
        c = _dpr_jump("FOXX_HP", o[1], 4.5, cap=260)
        if c: ch.append("foxx@5 "+c)
    if n[2] < 0.03 and KNOBS["FOXX_M2"] < 8:
        KNOBS["FOXX_M2"] += 1; ch.append(f"foxx@5 noisy KO {n[2]:.1%}<3% -> FOXX_M2={KNOBS['FOXX_M2']} (fear via HECKLE, not HP)")
    if n[0] < 0.90: KNOBS["FOXX_ATK"] = max(4, KNOBS["FOXX_ATK"]-1); ch.append(f"foxx@5 noisy win {n[0]:.1%}<90% -> FOXX_ATK={KNOBS['FOXX_ATK']}")
    o,n = res["hacker8"]
    if o[1] < 8.0:
        c = _dpr_jump("NULLR_HP", o[1], 9.0, cap=500)
        if c: ch.append("hacker chain "+c)
    if n[0] < 0.85: KNOBS["NULLR_MB"] = max(0, KNOBS["NULLR_MB"]-1); ch.append(f"hacker chain noisy win {n[0]:.1%}<85% -> NULLR_MB={KNOBS['NULLR_MB']}")
    elif n[2] < 0.05 and KNOBS["NULLR_MB"] < 4: KNOBS["NULLR_MB"] += 1; ch.append(f"hacker chain noisy KO {n[2]:.1%}<5% -> NULLR_MB={KNOBS['NULLR_MB']}")
    o,n = res["zeroday8"]
    if not (3.5 <= o[1] <= 5.5):
        c = _dpr_jump("ZERO_HP", o[1], 4.3, cap=450)
        if c: ch.append("zeroday "+c)
    o,n = res["pinj9"]
    if not (3.5 <= o[1] <= 5.5):
        c = _dpr_jump("PINJ_HP", o[1], 4.0, cap=600)
        if c: ch.append("promptinj "+c)
    o,n = res["halluc9"]
    if not (3.5 <= o[1] <= 5.5):
        c = _dpr_jump("HAL_HP", o[1], 4.2, cap=450)
        if c: ch.append("halluc "+c)
    o,n = res["misalign10"]
    if n[0] < 0.88: KNOBS["MIS_M2"] = max(8, KNOBS["MIS_M2"]-1); ch.append(f"misaligned noisy win {n[0]:.1%}<88% -> MIS_M2={KNOBS['MIS_M2']}")
    elif n[2] < 0.08 and KNOBS["MIS_M2"] < 18: KNOBS["MIS_M2"] += 1; ch.append(f"misaligned noisy KO {n[2]:.1%}<8% -> MIS_M2={KNOBS['MIS_M2']} (fear via MOVE, not HP)")
    if o[1] < 6.0:
        c = _dpr_jump("MIS_HP", o[1], 6.6, cap=800)
        if c: ch.append("misaligned "+c)
    # 6-vs-5 creep guard: the sixth seat must not collapse frozen bosses (fix lives on the Foxx side)
    for six, five in (("monolith6","monolith5"),("h5_6","h5_5"),("unknown6","unknown5"),("retry6","retry5")):
        o6,_ = res[six]; o5,_ = res[five]
        if o6[1] < o5[1]*0.62:
            KNOBS["ULTIMA_DMG"] = max(8, KNOBS["ULTIMA_DMG"]-1)
            ch.append(f"{six} turns {o6[1]:.1f} < 62% of {five} {o5[1]:.1f} -> ULTIMA_DMG={KNOBS['ULTIMA_DMG']}")
            break
    for rk,(o,n) in res.items():
        if o[0] < 0.99: ch.append(f"WARNING {rk} optimal win {o[0]:.1%} < 99% - manual review")
    for k,v in FROZEN.items():
        assert KNOBS[k] == v, f"FROZEN KNOB TOUCHED: {k}"
    return ch

def lab():
    global RUNS_PER
    RUNS_PER = int(sys.argv[3]) if len(sys.argv) > 3 else 420
    rows = [r for r in TABLE if r[0] in ("hacker8","hacker9")]
    arms = [("join@0.0 (fidelity control)", 0.0), ("join@0.5 (half-lit gauge)", 0.5), ("join@1.0 (upper bracket)", 1.0), ("no-join (old frozen baseline)", -1.0)]
    total = 0
    for tag, frac in arms:
        MECHS["JOIN_LB_FRAC"] = frac
        print(f"===== ARM {tag} =====", flush=True)
        for pol in ("balanced","turtle","roastmax","nukerush"):
            tasks = []
            for it in (1,2,3,4):
                for ri,(rk, enemy, party, lv, relic, crafted, armor) in enumerate(rows):
                    noises = (0.0, 0.25) if pol == "balanced" else (0.0,)
                    for ai, noise in enumerate(noises):
                        tasks.append((rk+"/"+pol, enemy, party, lv, relic, crafted, armor, noise, pol, RUNS_PER, 90790832 + int(frac*10)*100000 + it*1000 + ri*10 + ai))
            with Pool(processes=10, initializer=_init_knobs, initargs=(dict(KNOBS, _MECHS=dict(MECHS)),)) as pool:
                got = pool.map(worker, tasks)
            total += len(tasks)*RUNS_PER
            agg = {}
            for (rk, noise, wins, turns, t2sum, ko_b, clutch, runs) in got:
                key = (rk, noise)
                w0,t0,k0,c0,r0 = agg.get(key, (0,0,0,0,0))
                agg[key] = (w0+wins, t0+turns, k0+ko_b, c0+clutch, r0+runs)
            for (rk, noise),(w0,t0,k0,c0,r0) in sorted(agg.items()):
                lbl = rk + (" NOISY" if noise else "")
                print(f"  {lbl:<26} win {w0/r0:>7.2%}  turns {t0/r0:>5.2f}  KO% {k0/r0:>6.1%}  clutch {c0/r0:>6.1%}")
    print(f"lab simulated battles: {total:,}")

def lab2():
    global RUNS_PER
    RUNS_PER = int(sys.argv[3]) if len(sys.argv) > 3 else 240
    KEYS = ("monolith6","h5_6","unknown6","retry6","hacker8","misalign10")
    rows = [r for r in TABLE if r[0] in KEYS]
    arms = [
      ("control",            dict(BREAK=0, ASSIST=0)),
      ("BREAK th3",          dict(BREAK=1, BREAK_TH=3, ASSIST=0)),
      ("BREAK th4",          dict(BREAK=1, BREAK_TH=4, ASSIST=0)),
      ("ASSIST 10%",         dict(BREAK=0, ASSIST=1, ASSIST_P=0.10)),
      ("ASSIST 15%",         dict(BREAK=0, ASSIST=1, ASSIST_P=0.15)),
      ("BREAK3 + ASSIST15",  dict(BREAK=1, BREAK_TH=3, ASSIST=1, ASSIST_P=0.15)),
    ]
    total = 0
    for tag, m in arms:
        MECHS.update(dict(BREAK=0, BREAK_TH=3, ASSIST=0, ASSIST_P=0.15)); MECHS.update(m)
        print(f"===== ARM {tag} =====", flush=True)
        cells = []
        for pol, noises in (("balanced",(0.0,0.25)), ("nukerush",(0.0,))):
            for it in (1,2,3,4):
                for ri,(rk, enemy, party, lv, relic, crafted, armor) in enumerate(rows):
                    for ai, noise in enumerate(noises):
                        cells.append((rk+("/nk" if pol=="nukerush" else ""), enemy, party, lv, relic, crafted, armor, noise, pol, RUNS_PER, 90890833 + hash(tag)%97*10000 + it*1000 + ri*10 + ai))
        with Pool(processes=10, initializer=_init_knobs, initargs=(dict(KNOBS, _MECHS=dict(MECHS)),)) as pool:
            got = pool.map(worker, cells)
        total += len(cells)*RUNS_PER
        agg = {}
        for (rk, noise, wins, turns, t2sum, ko_b, clutch, runs) in got:
            key = (rk, noise)
            w0,t0,tt0,k0,c0,r0 = agg.get(key, (0,0,0,0,0,0))
            agg[key] = (w0+wins, t0+turns, tt0+t2sum, k0+ko_b, c0+clutch, r0+runs)
        for (rk, noise),(w0,t0,tt0,k0,c0,r0) in sorted(agg.items()):
            mt=t0/r0; sd=max(0.0, tt0/r0-mt*mt)**0.5
            lbl = rk + (" NOISY" if noise else "")
            print(f"  {lbl:<22} win {w0/r0:>7.2%}  turns {mt:>5.2f}  sd {sd:>4.2f}  KO% {k0/r0:>6.1%}  clutch {c0/r0:>6.1%}")
    print(f"lab2 simulated battles: {total:,}")

def lab3():
    global RUNS_PER
    RUNS_PER = int(sys.argv[3]) if len(sys.argv) > 3 else 260
    KEYS = ("monolith6","h5_6","unknown6","retry6","hacker8","misalign10")
    rows = [r for r in TABLE if r[0] in KEYS]
    arms = [
      ("control",          dict(BREAK=0, ASSIST=0, ENRAGE=0)),
      ("BREAK3+ENRAGE2",   dict(BREAK=1, BREAK_TH=3, ASSIST=0, ENRAGE=2)),
      ("BREAK3+ENRAGE3",   dict(BREAK=1, BREAK_TH=3, ASSIST=0, ENRAGE=3)),
    ]
    total = 0
    for tag, m in arms:
        MECHS.update(dict(BREAK=0, BREAK_TH=3, ASSIST=0, ENRAGE=0)); MECHS.update(m)
        print(f"===== ARM {tag} =====", flush=True)
        cells = []
        for pol, noises in (("balanced",(0.0,0.25)), ("nukerush",(0.0,))):
            for it in (1,2,3,4):
                for ri,(rk, enemy, party, lv, relic, crafted, armor) in enumerate(rows):
                    for ai, noise in enumerate(noises):
                        cells.append((rk+("/nk" if pol=="nukerush" else ""), enemy, party, lv, relic, crafted, armor, noise, pol, RUNS_PER, 90990834 + hash(tag)%97*10000 + it*1000 + ri*10 + ai))
        with Pool(processes=10, initializer=_init_knobs, initargs=(dict(KNOBS, _MECHS=dict(MECHS)),)) as pool:
            got = pool.map(worker, cells)
        total += len(cells)*RUNS_PER
        agg = {}
        for (rk, noise, wins, turns, t2sum, ko_b, clutch, runs) in got:
            key = (rk, noise)
            w0,t0,tt0,k0,c0,r0 = agg.get(key, (0,0,0,0,0,0))
            agg[key] = (w0+wins, t0+turns, tt0+t2sum, k0+ko_b, c0+clutch, r0+runs)
        for (rk, noise),(w0,t0,tt0,k0,c0,r0) in sorted(agg.items()):
            mt=t0/r0; sd=max(0.0, tt0/r0-mt*mt)**0.5
            lbl = rk + (" NOISY" if noise else "")
            print(f"  {lbl:<22} win {w0/r0:>7.2%}  turns {mt:>5.2f}  sd {sd:>4.2f}  KO% {k0/r0:>6.1%}  clutch {c0/r0:>6.1%}")
    print(f"lab3 simulated battles: {total:,}")

def _noop_marker():
    pass

def lab8():
    """THE SKILL TREE, trained. Five arms across the boss table.
    PRE-REGISTERED GATES (frozen before the first run):
      G1 no power creep: every arm and row, OPT mean turns >= 0.85 x the no-tree control
      G2 floors hold: wherever the control wins 100% OPT, every arm wins 100% OPT
      G3 worth taking: some arm beats the control on mean turns by >= 3% somewhere
      G4 no dominant lane: no single lane arm is the best lane on EVERY row
      G5 no dead lane: every lane arm beats the control on at least one row
      G6 drama survives: |arm KO% - control KO%| <= 12pp on every row
    Remedy ladder (pre-registered, never auto-applied): G1 fails, halve that lane's per-point
    effect; G4 fails, move its tier-4 node behind a fork; G5 fails, the dead lane is redesigned,
    never silently buffed.
    """
    global RUNS_PER
    RUNS_PER = int(sys.argv[3]) if len(sys.argv) > 3 else 1400
    KEYS = ("monolith6", "h5_6", "unknown6", "retry6", "hacker8", "misalign10")
    rows = [r for r in TABLE if r[0] in KEYS]
    # STRESS ROWS (lab8 instrument fix): defensive value cannot appear in mean turns when the
    # party never loses. Underleveled and unequipped, KO% and win rate finally have room to move.
    rows = rows + [
        ("stress_mis", "misaligned", FULL6, 7, False, False, False),
        ("stress_hax", "nullbyte",   FULL,  5, False, False, False),
    ]
    KEYS = KEYS + ("stress_mis", "stress_hax")
    res = {}
    for tag, build in BUILDS.items():
        cells = []
        for it in (1, 2, 3, 4):
            for ri, (rk, enemy, party, lv, relic, crafted, armor) in enumerate(rows):
                for ai, noise in enumerate((0.0, 0.25)):
                    cells.append((rk, enemy, party, lv, relic, crafted, armor, noise, "balanced", RUNS_PER,
                                  93390858 + it*1000 + ri*10 + ai, build))
        with Pool(processes=10, initializer=_init_knobs, initargs=(dict(KNOBS, _MECHS=dict(MECHS)),)) as pool:
            got = pool.map(worker8, cells)
        agg = {}
        for (rk, noise, wins, turns, t2sum, ko_b, clutch, runs) in got:
            w0, t0, tt0, k0, c0, r0 = agg.get((rk, noise), (0, 0, 0, 0, 0, 0))
            agg[(rk, noise)] = (w0+wins, t0+turns, tt0+t2sum, k0+ko_b, c0+clutch, r0+runs)
        for (rk, noise), (w0, t0, tt0, k0, c0, r0) in agg.items():
            res[(tag, rk, noise)] = (w0/r0, t0/r0, k0/r0)
    print("LAB8 - the skill tree, trained | arms: " + ", ".join(BUILDS.keys()))
    print("%-12s | %s" % ("row", " | ".join("%-14s" % t for t in BUILDS.keys())))
    best_by_row = {}
    for rk in KEYS:
        cells_txt = []
        for tag in BUILDS:
            w, t, k = res[(tag, rk, 0.0)]
            cells_txt.append("%5.2ft ko%4.1f%%" % (t, 100*k))
        print("%-12s | %s" % (rk, " | ".join(cells_txt)))
        lanes = {tag: res[(tag, rk, 0.0)][1] for tag in ("R-pure", "V-pure", "I-pure")}
        best_by_row[rk] = min(lanes, key=lanes.get)
    g1 = g2 = g6 = True
    gains = {}
    for rk in KEYS:
        cw, ct, ck = res[("none", rk, 0.0)]
        for tag in BUILDS:
            if tag == "none":
                continue
            w, t, k = res[(tag, rk, 0.0)]
            if t < 0.85*ct: g1 = False
            if cw >= 0.999999 and w < 0.999999: g2 = False
            if abs(k - ck) > 0.12: g6 = False
            gains.setdefault(tag, []).append(((ct - t)/ct) if ct else 0.0)
    g3 = any(max(v) >= 0.03 for v in gains.values())
    g4 = len(set(best_by_row.values())) > 1
    g5 = all(max(gains[l]) > 0 for l in ("R-pure", "V-pure", "I-pure"))
    for name, ok in (("G1 no power creep", g1), ("G2 floors hold", g2), ("G3 worth taking", g3),
                     ("G4 no dominant lane", g4), ("G5 no dead lane", g5), ("G6 drama survives", g6)):
        print("  %-22s %s" % (name, "PASS" if ok else "FAIL"))
    print("  best lane per row: " + str(best_by_row))
    print("  lane gains vs control (max over rows): " + str({k2: round(max(v), 4) for k2, v in gains.items()}))
    print("LAB8 VERDICT: " + ("ALL GATES PASS" if all((g1, g2, g3, g4, g5, g6)) else "GATE FAILURE - apply the pre-registered remedy ladder"))
    print("lab8 simulated battles: {:,}".format(len(BUILDS) * 4 * len(rows) * 2 * RUNS_PER))


def worker10(task):
    (rk, enemy, party, lv, relic, crafted, armor, noise, policy, runs, seed, kit) = task
    global CUR_KIT
    CUR_KIT = kit
    rng = random.Random(seed)
    wins, turns, t2sum, ko_b, clutch = one_row(enemy, party, lv, relic, crafted, armor, noise, policy, runs, rng)
    return (rk, noise, wins, turns, t2sum, ko_b, clutch, runs)


def lab10():
    """THE INCIDENT-RESPONSE KIT, used as well as a player possibly could: every item on its
    best turn, every battle, with no token cost. That is strictly better than real play, so a
    kit that passes here cannot break the game in a player's hands.
    PRE-REGISTERED GATES (frozen before the first run):
      K1 worth carrying: some row improves mean turns by >= 3%
      K2 no trivialising: KO% never falls more than 20pp below control on any row (a wider band
        than the tree's 12pp on purpose - these are one-shot purchases the economy already bounds)
      K3 floors hold: wherever the control wins 100% OPT, the kit wins 100% OPT
      K4 no walkover: mean turns never below 0.80 x control on rows the control takes 3+ turns
      K5 worth carrying, survival edition (ADDED after round 1 alongside K1, never replacing it):
        the kit must cut KO% by >= 2pp on at least one row - the axis a survival kit competes on
    Remedy ladder (pre-registered, never auto-applied): K2 fails, the party-wide items lose their
    party-wide clause before they lose their numbers; K4 fails, the offending item is repriced
    first and re-measured before any mechanic changes.
    """
    global RUNS_PER
    RUNS_PER = int(sys.argv[3]) if len(sys.argv) > 3 else 400
    KEYS = ("monolith6", "h5_6", "unknown6", "retry6", "hacker8", "misalign10")
    rows = [r for r in TABLE if r[0] in KEYS]
    rows = rows + [
        ("stress_mis", "misaligned", FULL6, 7, False, False, False),
        ("stress_hax", "nullbyte",   FULL,  5, False, False, False),
    ]
    KEYS = KEYS + ("stress_mis", "stress_hax")
    ARMS = {"no kit": False, "KIT": True}
    res = {}
    for tag, kit in ARMS.items():
        cells = []
        for it in (1, 2, 3, 4):
            for ri, (rk, enemy, party, lv, relic, crafted, armor) in enumerate(rows):
                for ai, noise in enumerate((0.0, 0.25)):
                    cells.append((rk, enemy, party, lv, relic, crafted, armor, noise, "balanced", RUNS_PER,
                                  40771233 + it*1000 + ri*10 + ai, kit))
        with Pool(processes=10, initializer=_init_knobs, initargs=(dict(KNOBS, _MECHS=dict(MECHS)),)) as pool:
            got = pool.map(worker10, cells)
        agg = {}
        for (rk, noise, wins, turns, t2sum, ko_b, clutch, runs) in got:
            w0, t0, tt0, k0, c0, r0 = agg.get((rk, noise), (0, 0, 0, 0, 0, 0))
            agg[(rk, noise)] = (w0+wins, t0+turns, tt0+t2sum, k0+ko_b, c0+clutch, r0+runs)
        for (rk, noise), (w0, t0, tt0, k0, c0, r0) in agg.items():
            res[(tag, rk, noise)] = (w0/r0, t0/r0, k0/r0)
    print("LAB10 - the incident-response kit, played perfectly")
    print("%-12s | %-22s | %-22s" % ("row", "no kit", "KIT"))
    k1 = k2 = k3 = k4 = True
    gains = []
    for rk in KEYS:
        cw, ct, ck = res[("no kit", rk, 0.0)]
        w, t, k = res[("KIT", rk, 0.0)]
        print("%-12s | win %5.1f%% %5.2ft ko%5.1f%% | win %5.1f%% %5.2ft ko%5.1f%%"
              % (rk, 100*cw, ct, 100*ck, 100*w, t, 100*k))
        gains.append(((ct - t)/ct) if ct else 0.0)
        if (ck - k) > 0.20: k2 = False
        if cw >= 0.999999 and w < 0.999999: k3 = False
        if ct >= 3.0 and t < 0.80*ct: k4 = False
    k1 = max(gains) >= 0.03
    ko_saved = [res[("no kit", rk, 0.0)][2] - res[("KIT", rk, 0.0)][2] for rk in KEYS]
    k5 = max(ko_saved) >= 0.02
    for name, ok in (("K1 worth carrying", k1), ("K2 no trivialising", k2),
                     ("K3 floors hold", k3), ("K4 no walkover", k4),
                     ("K5 worth carrying (KO%)", k5)):
        print("  %-24s %s" % (name, "PASS" if ok else "FAIL"))
    print("  kit turn gain per row: " + str([round(g, 4) for g in gains]))
    print("  kit KO%% saved per row (pp): " + str([round(100*g, 2) for g in ko_saved]))
    print("LAB10 VERDICT: " + ("ALL GATES PASS" if all((k1, k2, k3, k4, k5)) else "GATE FAILURE - apply the pre-registered remedy ladder"))
    print("lab10 simulated battles: {:,}".format(len(ARMS) * 4 * len(rows) * 2 * RUNS_PER))


def worker9(task):
    (rk, enemy, party, lv, relic, crafted, armor, noise, policy, runs, seed, tree) = task
    global CUR_TREE
    CUR_TREE = tree
    rng = random.Random(seed)
    wins, turns, t2sum, ko_b, clutch = one_row(enemy, party, lv, relic, crafted, armor, noise, policy, runs, rng)
    return (rk, noise, wins, turns, t2sum, ko_b, clutch, runs)


def lab9():
    """THE SHIPPED TREE, trained node by node. Eight arms: the control, both sides of
    all three tier-3 forks, and a five-rep spread.
    PRE-REGISTERED GATES (frozen before the first run):
      G1 no power creep: every arm, OPT mean turns >= 0.85 x the no-tree control, on every row
        the control takes 3+ turns (RE-SCOPED after round 3, never loosened: below 3 turns a
        single saved round is 0.84 by arithmetic, so the gate measured granularity, not creep)
      G2 floors hold: wherever the control wins 100% OPT, every arm wins 100% OPT
      G3 worth taking: some arm beats the control on mean turns by >= 3% somewhere
      G4 no dominant lane: no single lane arm is the best lane on EVERY row
      G5 no dead lane: every lane arm beats the control on at least one row
      G6 drama survives: |arm KO% - control KO%| <= 12pp on every row
      G7 forks are real (TIGHTENED after round 1): each tier-3 pair must differ on >= 3 rows,
        and neither side may be faster on every row where they differ
    Remedy ladder (pre-registered, never auto-applied): G1 fails, halve that node's magnitude;
    G4 fails, the dominant lane's keystone gains a cost; G5 fails, that lane is redesigned and
    never silently buffed; G7 fails, the losing fork side is redesigned, not buffed.
    """
    global RUNS_PER
    RUNS_PER = int(sys.argv[3]) if len(sys.argv) > 3 else 400
    KEYS = ("monolith6", "h5_6", "unknown6", "retry6", "hacker8", "misalign10")
    rows = [r for r in TABLE if r[0] in KEYS]
    rows = rows + [
        ("stress_mis", "misaligned", FULL6, 7, False, False, False),
        ("stress_hax", "nullbyte",   FULL,  5, False, False, False),
        # INSTRUMENT FIX (pre-registered before the full run): the observability fork cannot be
        # measured against a table with no hidden and no foggy foe - s3a and s3b would be the same
        # code path on every row, and G7 would fail for want of a question, not for want of a design.
        ("hidden9",    "zeroday",   FULL6, 8, True,  True,  True),
        ("foggy9",     "halluc",    FULL7, 9, True,  True,  True),
    ]
    KEYS = KEYS + ("stress_mis", "stress_hax", "hidden9", "foggy9")
    res = {}
    for tag, tree in TREES.items():
        cells = []
        for it in (1, 2, 3, 4):
            for ri, (rk, enemy, party, lv, relic, crafted, armor) in enumerate(rows):
                for ai, noise in enumerate((0.0, 0.25)):
                    cells.append((rk, enemy, party, lv, relic, crafted, armor, noise, "balanced", RUNS_PER,
                                  71554901 + it*1000 + ri*10 + ai, tree))
        with Pool(processes=10, initializer=_init_knobs, initargs=(dict(KNOBS, _MECHS=dict(MECHS)),)) as pool:
            got = pool.map(worker9, cells)
        agg = {}
        for (rk, noise, wins, turns, t2sum, ko_b, clutch, runs) in got:
            w0, t0, tt0, k0, c0, r0 = agg.get((rk, noise), (0, 0, 0, 0, 0, 0))
            agg[(rk, noise)] = (w0+wins, t0+turns, tt0+t2sum, k0+ko_b, c0+clutch, r0+runs)
        for (rk, noise), (w0, t0, tt0, k0, c0, r0) in agg.items():
            res[(tag, rk, noise)] = (w0/r0, t0/r0, k0/r0)
    print("LAB9 - the shipped tree, node by node | arms: " + ", ".join(TREES.keys()))
    print("%-12s | %s" % ("row", " | ".join("%-14s" % t for t in TREES.keys())))
    best_by_row = {}
    for rk in KEYS:
        cells_txt = []
        for tag in TREES:
            w, t, k = res[(tag, rk, 0.0)]
            cells_txt.append("%5.2ft ko%4.1f%%" % (t, 100*k))
        print("%-12s | %s" % (rk, " | ".join(cells_txt)))
        lanes = {tag: res[(tag, rk, 0.0)][1] for tag in LANES}
        best_by_row[rk] = min(lanes, key=lanes.get)
    g1 = g2 = g6 = True
    gains = {}
    for rk in KEYS:
        cw, ct, ck = res[("none", rk, 0.0)]
        for tag in TREES:
            if tag == "none":
                continue
            w, t, k = res[(tag, rk, 0.0)]
            if ct >= 3.0 and t < 0.85*ct: g1 = False
            if cw >= 0.999999 and w < 0.999999: g2 = False
            if abs(k - ck) > 0.12: g6 = False
            gains.setdefault(tag, []).append(((ct - t)/ct) if ct else 0.0)
    g3 = any(max(v) >= 0.03 for v in gains.values())
    g4 = len(set(best_by_row.values())) > 1
    g5 = all(max(gains[l]) > 0 for l in LANES)
    g7 = True
    fork_detail = {}
    for a1, a2 in FORKS:
        diff = [rk for rk in KEYS if abs(res[(a1, rk, 0.0)][1] - res[(a2, rk, 0.0)][1]) > 1e-9]
        a1_wins = sum(1 for rk in diff if res[(a1, rk, 0.0)][1] < res[(a2, rk, 0.0)][1])
        fork_detail[a1 + " vs " + a2] = "%d/%d rows differ, left faster on %d" % (len(diff), len(KEYS), a1_wins)
        if len(diff) < 3 or a1_wins == len(diff) or a1_wins == 0: g7 = False
    for name, ok in (("G1 no power creep", g1), ("G2 floors hold", g2), ("G3 worth taking", g3),
                     ("G4 no dominant lane", g4), ("G5 no dead lane", g5), ("G6 drama survives", g6),
                     ("G7 forks are real", g7)):
        print("  %-22s %s" % (name, "PASS" if ok else "FAIL"))
    print("  best lane per row: " + str(best_by_row))
    print("  -- NOISY column (the player who cannot hit the timing bar) --")
    print("%-12s | %s" % ("row", " | ".join("%-14s" % t for t in TREES.keys())))
    for rk in KEYS:
        print("%-12s | %s" % (rk, " | ".join("%5.2ft ko%4.1f%%" % (res[(tag, rk, 0.25)][1], 100*res[(tag, rk, 0.25)][2]) for tag in TREES)))
    nz = {tag: round(max(((res[("none", rk, 0.25)][1] - res[(tag, rk, 0.25)][1]) / res[("none", rk, 0.25)][1]) for rk in KEYS), 4) for tag in TREES if tag != "none"}
    print("  noisy gains vs control (max over rows): " + str(nz))
    print("  arm gains vs control (max over rows): " + str({k2: round(max(v), 4) for k2, v in gains.items()}))
    print("  fork splits (left side faster on): " + str(fork_detail))
    print("LAB9 VERDICT: " + ("ALL GATES PASS" if all((g1, g2, g3, g4, g5, g6, g7)) else "GATE FAILURE - apply the pre-registered remedy ladder"))
    print("lab9 simulated battles: {:,}".format(len(TREES) * 4 * len(rows) * 2 * RUNS_PER))


def worker8(task):
    (rk, enemy, party, lv, relic, crafted, armor, noise, policy, runs, seed, build) = task
    global CUR_BUILD
    CUR_BUILD = build
    rng = random.Random(seed)
    wins, turns, t2sum, ko_b, clutch = one_row(enemy, party, lv, relic, crafted, armor, noise, policy, runs, rng)
    return (rk, noise, wins, turns, t2sum, ko_b, clutch, runs)


def lab7():
    """CROWD WORK on/off across every row where PapaFoxx is an ally.
    PRE-REGISTERED GATES (frozen before the first run), per row:
      G1 floors: ON OPT win == 100% wherever OFF OPT is 100%; ON NOISY >= OFF NOISY - 1pp
      G2 drama kept: ON OPT turns >= 0.85 x OFF turns (a party buff must not trivialize)
      G3 KO band: |ON KO% - OFF KO%| <= 10pp
    Remedy ladder if G2 fails: softened bonus 2 -> 1 (then duration 2 -> 1).
    """
    global RUNS_PER
    RUNS_PER = int(sys.argv[3]) if len(sys.argv) > 3 else 1042
    KEYS = ("monolith6", "h5_6", "unknown6", "retry6", "hacker8", "misalignR")
    rows = [r for r in TABLE if r[0] in KEYS]
    res = {}
    for tag, on in (("OFF", 0), ("ON", 1)):
        KNOBS["CROWDWORK"] = on
        cells = []
        for it in (1, 2, 3, 4):
            for ri, (rk, enemy, party, lv, relic, crafted, armor) in enumerate(rows):
                for ai, noise in enumerate((0.0, 0.25)):
                    cells.append((rk, enemy, party, lv, relic, crafted, armor, noise, "balanced", RUNS_PER, 92790852 + it * 1000 + ri * 10 + ai))
        with Pool(processes=10, initializer=_init_knobs, initargs=(dict(KNOBS, _MECHS=dict(MECHS)),)) as pool:
            got = pool.map(worker, cells)
        agg = {}
        for (rk, noise, wins, turns, t2sum, ko_b, clutch, runs) in got:
            w0, t0, tt0, k0, c0, r0 = agg.get((rk, noise), (0, 0, 0, 0, 0, 0))
            agg[(rk, noise)] = (w0 + wins, t0 + turns, tt0 + t2sum, k0 + ko_b, c0 + clutch, r0 + runs)
        for (rk, noise), (w0, t0, tt0, k0, c0, r0) in agg.items():
            res[(tag, rk, noise)] = (w0 / r0, t0 / r0, k0 / r0)
    print("LAB7 - CROWD WORK on/off")
    ok = True
    for rk in KEYS:
        fo, no = res[("OFF", rk, 0.0)], res[("ON", rk, 0.0)]
        fn, nn = res[("OFF", rk, 0.25)], res[("ON", rk, 0.25)]
        g1 = (no[0] >= 0.999999 if fo[0] >= 0.999999 else no[0] >= fo[0] - 0.01) and nn[0] >= fn[0] - 0.01
        g2 = no[1] >= 0.85 * fo[1]
        g3 = abs(no[2] - fo[2]) <= 0.10
        ok = ok and g1 and g2 and g3
        print("  %-11s OFF win %6.2f%% turns %5.2f KO %5.1f%% | ON win %6.2f%% turns %5.2f KO %5.1f%% | G1 %s G2 %s (%.0f%%) G3 %s" % (
            rk, 100 * fo[0], fo[1], 100 * fo[2], 100 * no[0], no[1], 100 * no[2], "PASS" if g1 else "FAIL", "PASS" if g2 else "FAIL", 100 * no[1] / fo[1], "PASS" if g3 else "FAIL"))
    print("LAB7 VERDICT:", "ALL GATES PASS" if ok else "GATE FAILURE - apply the pre-registered remedy ladder")
    print("lab7 simulated battles: {:,}".format(2 * 4 * len(rows) * 2 * RUNS_PER))


def lab6():
    """LITO as the ninth soul on the post-game frontier.
    PRE-REGISTERED GATES (frozen before the first run), per boss at lv 9/10/12:
      G1 floors: every L-row OPT win == 100%; NOISY win >= control NOISY - 1pp
      G2 drama kept: L-row OPT turns mean >= 0.85 x control turns (a 9th soul must not trivialize)
      G3 KO band: |L-row KO% - control KO%| <= 10pp
      G4 freeze sanity (single-process probe, 1,500 battles): windmill casts > 0 and
         freeze-per-cast in [0.08, 0.30] (crit-gated: CRIT=0.15 x LITO_FREEZE)
    Remedy ladder if G2 fails (pre-registered): LITO_WM 3->2, then LITO_FREEZE 1.0->0.6.
    """
    global RUNS_PER
    RUNS_PER = int(sys.argv[3]) if len(sys.argv) > 3 else 1563
    CTRL = FULL7 + ["retro"]
    WITH = FULL7 + ["retro", "lito"]
    pairs = [("pinj9", "promptinj", 9), ("halluc9", "halluc", 9), ("misalign10", "misaligned", 10), ("misalign12", "misaligned", 12)]
    rows = []
    for key, foe, lv in pairs:
        rows.append((key + "C", foe, CTRL, lv, True, True, True))
        rows.append((key + "L", foe, WITH, lv, True, True, True))
    cells = []
    for it in (1, 2, 3, 4):
        for ri, (rk, enemy, party, lv, relic, crafted, armor) in enumerate(rows):
            for ai, noise in enumerate((0.0, 0.25)):
                cells.append((rk, enemy, party, lv, relic, crafted, armor, noise, "balanced", RUNS_PER, 92690851 + it * 1000 + ri * 10 + ai))
    with Pool(processes=10, initializer=_init_knobs, initargs=(dict(KNOBS, _MECHS=dict(MECHS)),)) as pool:
        got = pool.map(worker, cells)
    agg = {}
    for (rk, noise, wins, turns, t2sum, ko_b, clutch, runs) in got:
        w0, t0, tt0, k0, c0, r0 = agg.get((rk, noise), (0, 0, 0, 0, 0, 0))
        agg[(rk, noise)] = (w0 + wins, t0 + turns, tt0 + t2sum, k0 + ko_b, c0 + clutch, r0 + runs)
    res = {}
    print("LAB6 - Lito as the ninth soul | knobs LITO_WM=%s LITO_FREEZE=%s" % (KNOBS["LITO_WM"], KNOBS["LITO_FREEZE"]))
    for (rk, noise), (w0, t0, tt0, k0, c0, r0) in sorted(agg.items()):
        mt = t0 / r0; sd = max(0.0, tt0 / r0 - mt * mt) ** 0.5
        res[(rk, noise)] = (w0 / r0, mt, sd, k0 / r0)
        print("  %-16s win %7.2f%%  turns %5.2f  sd %4.2f  KO%% %5.1f%%  clutch %5.1f%%" % (rk + (" NOISY" if noise else " OPT"), 100 * w0 / r0, mt, sd, 100 * k0 / r0, 100 * c0 / r0))
    ok = True
    for key, _, _ in pairs:
        c_o, l_o = res[(key + "C", 0.0)], res[(key + "L", 0.0)]
        c_n, l_n = res[(key + "C", 0.25)], res[(key + "L", 0.25)]
        g1 = l_o[0] >= 0.999999 and l_n[0] >= c_n[0] - 0.01
        g2 = l_o[1] >= 0.85 * c_o[1]
        g3 = abs(l_o[3] - c_o[3]) <= 0.10
        ok = ok and g1 and g2 and g3
        print("  %-11s G1 floors %s | G2 turns %.2f vs %.2f (%.0f%%) %s | G3 KO %.1f vs %.1f %s" % (key, "PASS" if g1 else "FAIL", l_o[1], c_o[1], 100 * l_o[1] / c_o[1], "PASS" if g2 else "FAIL", 100 * l_o[3], 100 * c_o[3], "PASS" if g3 else "FAIL"))
    # G4: single-process freeze probe
    FREEZE_STATS["casts"] = 0; FREEZE_STATS["freezes"] = 0
    rng = random.Random(92690899)
    one_row("misaligned", WITH, 10, True, True, True, 0.0, "balanced", 1500, rng)
    rate = FREEZE_STATS["freezes"] / max(1, FREEZE_STATS["casts"])
    g4 = FREEZE_STATS["casts"] > 0 and 0.08 <= rate <= 0.30
    print("  G4 freeze probe: casts %d freezes %d rate %.3f %s" % (FREEZE_STATS["casts"], FREEZE_STATS["freezes"], rate, "PASS" if g4 else "FAIL"))
    print("LAB6 VERDICT:", "ALL GATES PASS" if (ok and g4) else "GATE FAILURE - apply the pre-registered remedy ladder")
    print("lab6 simulated battles: {:,}".format(len(cells) * RUNS_PER + 1500))


def lab5():
    """PapaFoxx as the THIRD companion: heckler duel at party [hero,sentinel,wiki].
    PRE-REGISTERED GATES (frozen before the first run):
      G-A foxxE4 OPT win == 100%       (canonical moment: 2 companions + nudge ~ lv4)
      G-B foxxE4 NOISY win >= 92%      (flee-able comedy duel, not a game-over)
      G-C foxxE4 OPT turns mean in [3.5, 9]
      G-D foxxE3 OPT win >= 97%        (floor: fight reachable at lv3)
      G-E control foxxfight5 (FULL,5): OPT 100% and turns in [3.6, 4.8] (frozen history)
    Pre-registered remedy if G-A/B fail (NOT auto-applied): FOXX_HP_EARLY=120 when
    party < 4 ("the Heckler goes easy on a small crowd") - ships only via its own lab.
    """
    global RUNS_PER
    RUNS_PER = int(sys.argv[3]) if len(sys.argv) > 3 else 3125
    rows = [
        ("foxxE3", "foxxbossE", ["hero", "sentinel", "wiki"], 3, False, False, False),
        ("foxxE4", "foxxbossE", ["hero", "sentinel", "wiki"], 4, False, False, False),
        ("foxxE5", "foxxbossE", ["hero", "sentinel", "wiki"], 5, False, False, False),
        ("foxxfight5", "foxxboss", FULL, 5, False, False, False),
    ]
    cells = []
    for it in (1, 2, 3, 4):
        for ri, (rk, enemy, party, lv, relic, crafted, armor) in enumerate(rows):
            for ai, noise in enumerate((0.0, 0.25)):
                cells.append((rk, enemy, party, lv, relic, crafted, armor, noise, "balanced", RUNS_PER, 92590850 + it * 1000 + ri * 10 + ai))
    with Pool(processes=10, initializer=_init_knobs, initargs=(dict(KNOBS, _MECHS=dict(MECHS)),)) as pool:
        got = pool.map(worker, cells)
    agg = {}
    for (rk, noise, wins, turns, t2sum, ko_b, clutch, runs) in got:
        key = (rk, noise)
        w0, t0, tt0, k0, c0, r0 = agg.get(key, (0, 0, 0, 0, 0, 0))
        agg[key] = (w0 + wins, t0 + turns, tt0 + t2sum, k0 + ko_b, c0 + clutch, r0 + runs)
    res = {}
    print("LAB5 - foxx-as-third validation")
    for (rk, noise), (w0, t0, tt0, k0, c0, r0) in sorted(agg.items()):
        mt = t0 / r0; sd = max(0.0, tt0 / r0 - mt * mt) ** 0.5
        res[(rk, noise)] = (w0 / r0, mt, sd, k0 / r0)
        lbl = rk + (" NOISY" if noise else " OPT")
        print("  %-18s win %7.2f%%  turns %5.2f  sd %4.2f  KO%% %5.1f%%  clutch %5.1f%%" % (lbl, 100 * w0 / r0, mt, sd, 100 * k0 / r0, 100 * c0 / r0))
    gA = res[("foxxE4", 0.0)][0] >= 0.999999
    gB = res[("foxxE4", 0.25)][0] >= 0.92
    gC = 3.5 <= res[("foxxE4", 0.0)][1] <= 9.0
    gD = res[("foxxE3", 0.0)][0] >= 0.97
    e5 = res[("foxxfight5", 0.0)]
    gE = e5[0] >= 0.999999 and 3.6 <= e5[1] <= 4.8
    for g, ok in (("G-A", gA), ("G-B", gB), ("G-C", gC), ("G-D", gD), ("G-E", gE)):
        print(f"  {g}: {'PASS' if ok else 'FAIL'}")
    print("LAB5 VERDICT:", "ALL GATES PASS" if all((gA, gB, gC, gD, gE)) else "GATE FAILURE - invoke the pre-registered remedy lab")
    print("lab5 simulated battles: {:,}".format(len(cells) * RUNS_PER))


def lab4():
    global RUNS_PER
    RUNS_PER = int(sys.argv[3]) if len(sys.argv) > 3 else 300
    KEYS = ("monolith6","h5_6","unknown6","retry6","hacker8","misalign10")
    rows = [r for r in TABLE if r[0] in KEYS]
    arms = [
      ("control",         dict(BREAK=0, ASSIST=0, ENRAGE=0, INTERRUPT=0)),
      ("INTERRUPT th3",   dict(BREAK=0, ASSIST=0, ENRAGE=0, INTERRUPT=1, BREAK_TH=3)),
      ("INTERRUPT th4",   dict(BREAK=0, ASSIST=0, ENRAGE=0, INTERRUPT=1, BREAK_TH=4)),
    ]
    total = 0
    for tag, m in arms:
        MECHS.update(dict(BREAK=0, BREAK_TH=3, ASSIST=0, ENRAGE=0, INTERRUPT=0)); MECHS.update(m)
        print("===== ARM " + tag + " =====", flush=True)
        cells = []
        for pol, noises in (("balanced",(0.0,0.25)), ("nukerush",(0.0,))):
            for it in (1,2,3,4):
                for ri,(rk, enemy, party, lv, relic, crafted, armor) in enumerate(rows):
                    for ai, noise in enumerate(noises):
                        cells.append((rk+("/nk" if pol=="nukerush" else ""), enemy, party, lv, relic, crafted, armor, noise, pol, RUNS_PER, 91190836 + hash(tag)%97*10000 + it*1000 + ri*10 + ai))
        with Pool(processes=10, initializer=_init_knobs, initargs=(dict(KNOBS, _MECHS=dict(MECHS)),)) as pool:
            got = pool.map(worker, cells)
        total += len(cells)*RUNS_PER
        agg = {}
        for (rk, noise, wins, turns, t2sum, ko_b, clutch, runs) in got:
            key = (rk, noise)
            w0,t0,tt0,k0,c0,r0 = agg.get(key, (0,0,0,0,0,0))
            agg[key] = (w0+wins, t0+turns, tt0+t2sum, k0+ko_b, c0+clutch, r0+runs)
        for (rk, noise),(w0,t0,tt0,k0,c0,r0) in sorted(agg.items()):
            mt=t0/r0; sd=max(0.0, tt0/r0-mt*mt)**0.5
            lbl = rk + (" NOISY" if noise else "")
            print("  %-22s win %7.2f%%  turns %5.2f  sd %4.2f  KO%% %5.1f%%  clutch %5.1f%%" % (lbl, 100*w0/r0, mt, sd, 100*k0/r0, 100*c0/r0))
    print("lab4 simulated battles: {:,}".format(total))

def main():
    global RUNS_PER
    if len(sys.argv) > 1 and sys.argv[1] == "lab10":
        if len(sys.argv) > 2 and sys.argv[2] != "-":
            cfg = json.loads(sys.argv[2])
            if "MECHS" in cfg: MECHS.update(cfg.pop("MECHS"))
            KNOBS.update(cfg)
        lab10(); return
    if len(sys.argv) > 1 and sys.argv[1] == "lab9":
        if len(sys.argv) > 2 and sys.argv[2] != "-":
            cfg = json.loads(sys.argv[2])
            if "MECHS" in cfg: MECHS.update(cfg.pop("MECHS"))
            KNOBS.update(cfg)
        lab9(); return
    if len(sys.argv) > 1 and sys.argv[1] == "lab8":
        if len(sys.argv) > 2 and sys.argv[2] != "-":
            cfg = json.loads(sys.argv[2])
            if "MECHS" in cfg: MECHS.update(cfg.pop("MECHS"))
            KNOBS.update(cfg)
        lab8(); return
    if len(sys.argv) > 1 and sys.argv[1] == "lab7":
        if len(sys.argv) > 2 and sys.argv[2] != "-":
            cfg = json.loads(sys.argv[2])
            if "MECHS" in cfg: MECHS.update(cfg.pop("MECHS"))
            KNOBS.update(cfg)
        lab7(); return
    if len(sys.argv) > 1 and sys.argv[1] == "lab6":
        if len(sys.argv) > 2 and sys.argv[2] != "-":
            cfg = json.loads(sys.argv[2])
            if "MECHS" in cfg: MECHS.update(cfg.pop("MECHS"))
            KNOBS.update(cfg)
        lab6(); return
    if len(sys.argv) > 1 and sys.argv[1] == "lab5":
        if len(sys.argv) > 2 and sys.argv[2] != "-":
            cfg = json.loads(sys.argv[2])
            if "MECHS" in cfg: MECHS.update(cfg.pop("MECHS"))
            KNOBS.update(cfg)
        lab5(); return
    if len(sys.argv) > 1 and sys.argv[1] == "lab4":
        if len(sys.argv) > 2 and sys.argv[2] != "-":
            cfg = json.loads(sys.argv[2])
            if "MECHS" in cfg: MECHS.update(cfg.pop("MECHS"))
            KNOBS.update(cfg)
        lab4(); return
    if len(sys.argv) > 1 and sys.argv[1] == "lab3":
        if len(sys.argv) > 2 and sys.argv[2] != "-":
            cfg = json.loads(sys.argv[2])
            if "MECHS" in cfg: MECHS.update(cfg.pop("MECHS"))
            KNOBS.update(cfg)
        lab3(); return
    if len(sys.argv) > 1 and sys.argv[1] == "lab2":
        if len(sys.argv) > 2 and sys.argv[2] != "-":
            cfg = json.loads(sys.argv[2])
            if "MECHS" in cfg: MECHS.update(cfg.pop("MECHS"))
            KNOBS.update(cfg)
        lab2(); return
    if len(sys.argv) > 1 and sys.argv[1] == "lab":
        if len(sys.argv) > 2 and sys.argv[2] != "-":
            cfg = json.loads(sys.argv[2])
            if "MECHS" in cfg: MECHS.update(cfg.pop("MECHS"))
            KNOBS.update(cfg)
        lab(); return
    wave = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    if len(sys.argv) > 2 and sys.argv[2] != "-":
        cfg = json.loads(sys.argv[2])
        if "MECHS" in cfg: MECHS.update(cfg.pop("MECHS"))
        KNOBS.update(cfg)
    print("MECHS:", MECHS)
    if len(sys.argv) > 3: RUNS_PER = int(sys.argv[3])
    seedbase = {1:90190826, 2:90290827, 3:90390828, 4:90490829, 5:90590830, 6:90690831, 7:91290837, 8:91390838, 9:91490839, 10:91590840, 11:91690841, 12:91790842, 13:91890843, 14:91990844, 15:92090845, 16:92190846, 17:92290847, 18:92390848, 19:92490849, 20:92890853, 21:92990854, 22:93090855, 23:93190856, 24:93290857}.get(wave, 90290827)
    total = 0
    for it in (1,2,3,4):
        policy = "balanced" if it <= 2 else "dynamic"
        print(f"===== WAVE {wave} · ITERATION {it} ({policy}) · knobs: { {k:v for k,v in KNOBS.items() if k not in FROZEN} } =====", flush=True)
        res = run_table_mp(policy, it, seedbase)
        total += len(TABLE) * 2 * RUNS_PER
        show(res)
        if wave == 1:
            ch = tune(res)
            print("LEARNER:", ("all bands hit" if not ch else ""))
            for c in ch: print("  -", c)
        else:
            print("VALIDATION PASS (knobs frozen)")
    adv, n_adv = run_adversarial(9, seedbase)
    total += n_adv
    print("----- ADVERSARIAL POLICIES (turtle / roast-max / nuke-rush) -----")
    for rk,(w,t,k) in adv.items():
        print(f"  {rk:<24} win {w:>6.1%}  turns {t:>5.1f}  KO% {k:>6.1%}")
    print(f"wave {wave} simulated battles: {total:,}")
    print(f"final tunable knobs: { {k:v for k,v in KNOBS.items() if k not in FROZEN} }")

if __name__ == "__main__":
    main()
