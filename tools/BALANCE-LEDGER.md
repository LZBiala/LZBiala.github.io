# The balance ledger

The game's title screen says its balance was tuned on 3,230,485 simulated battles.
This file is where that number is accounted for, because a claim nobody can check is
just a number in a nice font.

Every one of those battles has a log in `sim-runs/` and a seed in `combat_sim.py`. You can
re-run any campaign in this table and get the numbers back.

## What is published here

- `combat_sim.py` - the simulator itself. It reimplements the game's combat maths in
  Python so a design question can be answered in minutes instead of playtests. Run a lab
  with `python tools/combat_sim.py lab9 - 400`.
- `sim-runs/*.log` - the raw stdout of the campaigns listed below, gates and all,
  including the runs that FAILED. The failures are the point; they are what changed the
  design.

## The campaigns behind the number

Each lab freezes its gates in the docstring **before** the first run. A gate that fails
sends the design back, not the gate.

| campaign | battles | what it asked | verdict | evidence |
|---|---:|---|---|---|
| lab9 round 1 | 256,000 | do the 18 shipped growth-tree nodes hold up, node by node | 3 gates FAILED | `sim-runs/lab9_run.log` |
| lab9 round 2 | 256,000 | after halving two keystones | 3 gates FAILED | `sim-runs/lab9_run2.log` |
| lab9 round 3 | 256,000 | after redesigning the observability fork | 2 gates FAILED | `sim-runs/lab9_run3.log` |
| lab9 round 4 | 256,000 | after the breaker stopped erasing death | **all 7 PASS** | `sim-runs/lab9_run4.log` |
| lab10 round 1 | 102,400 | is the incident-response kit worth carrying | K1 FAILED | `sim-runs/lab10_run.log` |
| lab10 round 2 | 102,400 | after the kit's real lifetimes and numbers | K1 fails by design, K2-K5 pass | `sim-runs/lab10_run2.log` |
| lab11 baseline | 480,000 | what does a crowded room do to the rooms players walk into | D1 and D3 FAILED | `sim-runs/lab11-lab12-baseline-2026-08-23.log` |
| lab12 baseline | 519,942 | six fights with no rest: what do packs COST | E2 FAILED | same log |
| lab11 shipped | 480,000 | the same question after the two remedies | D1 fails, D3 now passes | `sim-runs/lab11-lab12-shipped-2026-08-23.log` |
| lab12 shipped | 520,719 | the walk after the two remedies | E1 fails, E2-E5 pass | same log |

**Published total: 3,230,485 battles**, every one of them reproducible from the script
and the seeds in it. That is the whole number the game claims.

## Why the headline number went DOWN

It used to say 25,000,000+. That figure was true and it was mostly uncheckable: about
21.8M of it came from earlier campaigns - encounter tuning, the boss table, limit breaks,
dual techs, the companion roster, the crafting economy - that ran in sessions whose logs
live in a private engineering journal rather than in this repo.

A reader could not verify them, and this site's whole argument is that a system should
prove it worked. A big number I am asking you to take on faith undercuts that argument
more than a smaller one strengthens it, so the headline now counts only what ships with a
log and a seed.

The earlier work still happened and the design still rests on it. It is simply no longer
being counted in a number presented as evidence.

## Why the failures are in the table

Three of the six campaigns failed their own gates, and each failure killed a design rather
than a number:

- A free death-save was taking the KO rate on an underleveled party from 17.9% to 2.0%. It
  now catches only a blow that fells a healthy ally, never a slow bleed.
- One side of a three-cost fork beat the other on all ten rows. A fork with a strictly
  better side is not a choice, so the losing side was redesigned, not buffed.
- One node ran **slower** than owning no tree at all and dropped fights the control won.

Two gates were changed after seeing results, and both changes are disclosed in
`combat_sim.py` where they live: one was **tightened**, and one was **re-scoped** away from
fights under three turns, where saving a single round is 0.84 of the control by arithmetic
alone and the gate was measuring rounding rather than power creep.

## Two gates that still fail, and why they were not quietly moved

**lab11 D1** asked for the KO rate on wandering fights to rise by 3 points once rooms
could hold up to four. It rose by 0.2. That answer is true and the question was wrong:
a trash fight is not meant to threaten a wipe, and lab11 handed the party a full bar
before every single battle, so it could not see a cost even in principle. lab12 exists
because of that failure.

**lab12 E1** asked for a 10-point drop in resources across a six-fight walk. The shipped
game gets 8.7. Getting the last 1.3 means more crowds, and more crowds put the opening
walk and the 1999 arc back over the wipe ceiling that E2 guards - the two gates are in
direct tension and this configuration cannot satisfy both. E1's threshold was a guess made
before any data existed, and the game it would produce is worse than the one that misses
it, so it stays missed and stays recorded. The real lever is that wandering foes do not
scale with the story; changing that is an enemy-strength change and it gets its own
pre-registered run rather than a quiet edit here.

Neither number was moved to make a gate green. That is the whole point of writing them
down first.
