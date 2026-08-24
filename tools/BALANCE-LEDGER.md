# The balance ledger

The game's title screen says its balance was tuned on 4,231,220 simulated battles.
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
| lab11 shipped | 480,000 | the same question after the two remedies | D1 fails, D3 borderline | `sim-runs/lab11-lab12-shipped-2026-08-23.log` |
| lab12 shipped | 520,719 | the walk after the two remedies | E1 fails, E2-E5 pass | same log |
| lab11 with AoE | 480,000 | does the room-hitting INDEX STORM undo the packs | no: +0.2pp KO, unchanged | `sim-runs/lab11-lab12-with-aoe-2026-08-23.log` |
| lab12 with AoE | 520,735 | the walk, with the AoE the game actually ships | E1 fails, E2-E5 pass | same log |

**Published total: 4,231,220 battles**, every one of them reproducible from the script
and the seeds in it. That is the whole number the game claims.

The last two rows are the ones that describe the shipped game. The four before them
describe it accurately in every respect except the room-hitting INDEX STORM, which landed
after they ran - see below.

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

From here the number only goes up, and it goes up one archived campaign at a time.

## Why the failures are in the table

Most of the campaigns in that table failed at least one of their own gates, and the
failures are the reason the design is what it is. From the growth-tree rounds:

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

## Two things the last campaign was run specifically to find out

**Did the published numbers describe a game nobody plays?** Room-hitting INDEX STORM
shipped after the campaign above had already run, and handing the party a room-wide attack
right after making rooms crowded is exactly the kind of change that quietly invalidates a
measurement. So the simulator learned the AoE and the whole campaign ran again.

It changed almost nothing: attrition across the walk went from -8.7 to -8.6 points, wipes
stayed at 2.5%, walks ending under half moved 78.9% to 78.3%. The reason is visible in the
turn counts - wandering fights end in two to three turns, and the storm needs the foe
revealed, unfogged and five MP, so it rarely gets cast before the room is already clear.
The suspicion was worth a million battles; the answer was that the earlier numbers stood.

**D3 is a gate that cannot give a stable answer, on a row that cannot happen.** It asks
that no wandering row fall below 85% wins at a forced four-pack. `w_vague` lands on 85%
one run and 84% the next - the verdict is decided by the seed, not by the design. And a
four-pack of `w_vague` is unreachable in play: stage 0 tops out at two foes, and a
two-body party is capped at two regardless.

Both facts are recorded rather than fixed. Re-scoping D3 to the rows where four foes can
actually occur is the obvious repair, and it is a gate change made after seeing results,
so it belongs to a fresh pre-registration rather than to a quiet edit in the run that
found it.
