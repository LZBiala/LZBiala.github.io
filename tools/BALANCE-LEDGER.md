# The balance ledger

The game's title screen says its balance was tuned on 7,313,561 simulated battles.
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
| lab11 instrument fixed | 480,000 | the same questions, on an instrument that can see a pack | D1, D3 fail | `sim-runs/lab11-lab12-instrument-fixed-2026-08-23.log` |
| lab12 instrument fixed | 514,714 | the walk, measured properly for the first time | E1 PASSES; E2, E4 fail badly | same log |
| lab11 corrected | 480,000 | after the party-outnumbers rule and the right rosters | D1, D3 fail (both known) | `sim-runs/lab11-lab12-corrected-2026-08-23.log` |
| lab12 corrected | 520,947 | the walk as the game actually ships it | **ALL GATES PASS** | same log |
| lab11 zoned | 480,000 | on a TESTED instrument, with honest walk fixtures | D1, D3 fail (both known) | `sim-runs/lab11-lab12-zoned-2026-08-23.log` |
| lab12 zoned | 607,704 | the walk, once the party stops being given what it has not earned | **ALL GATES PASS** | same log |

**Published total: 7,313,561 battles**, every one of them reproducible from the script
and the seeds in it. That is the whole number the game claims.

**Only the last two rows describe the shipped game**, and they are the first rows in this
table produced by an instrument that has tests of its own. Everything above the "instrument
fixed" pair was measured by a simulator that could not see the thing it was measuring - see
the retraction below.

## The time this file did not add up

On 2026-08-23 the bolded total above, and the headline on the game's title screen, both
read 7,834,585 while the campaign table summed to 7,313,561 - out by 521,024. A
mis-addition entered when the instrument-fixed rows landed and was carried forward through
two more updates, because every one of those updates edited the total instead of
recomputing it.

The number is corrected. More usefully, `site_check.py` now ADDS THE COLUMN itself and
fails if the table, this file's stated total, and every figure quoted inside the game do
not agree. The one check nobody had run was a reader with a calculator, and that reader is
now part of the build.

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

## RETRACTION: every pack number above the last two rows was measured blind

This is the biggest thing this ledger has had to say, so it goes near the top of the
failures rather than at the end.

**The simulator gave a whole pack one attack per round.** When the simulator learned about
packs, a per-body loop was added at the end of the round - and put behind `if not
foe_done`. There was already an interleave path that fires one foe action and sets
`foe_done` as soon as an ally slower than the foe is reached. REFUTER is speed 3 and WIKI
is 4, so that path fires in very nearly every battle, and the per-body loop was dead code
from the day it was written. A four-pack hit exactly as hard as one foe.

It is the mirror image of a defect that was found and fixed in the game itself the same
day - `nextUnit` discarding the foe index so one body swung four times. The fix went into
the game, and then the same mistake was written into the instrument that was supposed to
check the game.

**Two walks were also measured with parties that cannot walk them.** `tileAt` gates the
1999 rift on `S.won` and the internet gateway on `S.haxKnown`, and `ending()` sets `S.won`
alongside `S.stage=4`. So those zones are only ever walked after the finale, by a
post-victory party in full kit - and they were being simulated at level 7-8 with partial
gear and stage tags of 2 and 3.

Both errors pushed the same way: they made packs look weaker than they are.

What the corrected instrument says, on the same six walks:

| | measured blind | measured properly |
|---|---:|---:|
| resources left, one foe per room | 50.1% | 60.3% |
| resources left, packs as shipped | 41.4% | 44.3% |
| the drop (gate E1, needs >= 10) | 8.7pp - FAIL | **16.0pp - PASS** |
| walks ending under half | 78.9% | 74.9% |
| worst single walk's wipe rate | 6.8% | 5.6% |

**The gate that had been failing all along was passing all along.** Every previous entry in
this file that quotes an 8.7-point drop, or says E1 could not be satisfied without pushing
some walk over the wipe ceiling, was describing an instrument rather than a game.

There is a design consequence worth stating plainly. That failing gate was the entire
reason for a planned enemy-scaling system - five independent designs were drafted and
adversarially reviewed to close a 1.3-point gap that did not exist. **No enemy's numbers
were changed, and none needed to be.** The adversarial pass on those designs is what found
the bug; not one of the designs survived its own review, and that turned out to be the most
valuable thing the exercise produced.

One real change did come out of it. With a pack finally able to swing, the opening walk -
a HERO and one Ranger - wiped about one run in five, and the rule that had allowed an even
fight became "the party always outnumbers the room". It binds only at party sizes two to
four and costs the late game nothing.

## The simulator has tests now

`tools/test_combat_sim.py`, run by `site_check.py` as part of the gate. Twenty-three checks
in three classes, and each class earned its place by finding something on its first run.

**Fidelity** parses `game.html` and compares - rosters, enemy attacks, the pack table, the
solo list. Two implementations of the same combat maths drift, and this found three enemies
the simulator modelled under names the game does not use.

**Sensitivity** asks the only question that matters of a measuring device: if the thing I
am measuring changed, would this number move? It took two attempts. The obvious version -
a four-pack costs more per BATTLE - passes WITH the pack bug in place, because four foes
carry four times the health so the fight runs four times as long. It measured the pack's
health bar rather than its damage. The real check measures damage per ROUND, and it was
verified the only way that counts: the bug was put back and the suite was watched failing
on it, reading 1.38 per round at one body and 1.38 at four.

**Fixtures** check that a measured party is one the game can actually produce. This found
the internet walk being handed SHARONDUH, who joins at the END of that arc; missing LITO,
who joins in the statement that opens the GATEWAY; and carrying two transmutes gated on a
flag it has not set. All three made the arc look easier than it is.

With honest fixtures the Firewall Bastion wiped 11.0% against a 10% ceiling - the only walk
that failed, invisible until the party stopped being given things it had not earned. The
remedy was pack odds, as the ladder requires, applied to the zone that failed rather than
to all four that share its stage. A test asserts every other zone draws exactly the
distribution it drew before, so the change is provably local.

## Two gates that still fail, and why they were not quietly moved

**lab11 D1** asked for the KO rate on wandering fights to rise by 3 points once rooms
could hold up to four. It rose by 0.2. That answer is true and the question was wrong:
a trash fight is not meant to threaten a wipe, and lab11 handed the party a full bar
before every single battle, so it could not see a cost even in principle. lab12 exists
because of that failure.

**lab11 D3** asks that no wandering row stay above 85% wins at a forced four-pack. It fails
on `w_gremlin`, which wins 1% - and that row is a two-body party facing four foes, which
the party-outnumbers rule makes structurally impossible. The gate measures a configuration
the game cannot produce. Earlier it merely wobbled across the threshold on the seed;
now it fails unmistakably, for a reason that is about the gate rather than the game.

Re-scoping D3 to the rows where four foes can actually occur is the obvious repair, and it
is a gate change made after seeing results, so it belongs to a fresh pre-registration.

**lab12 E1 used to be on this list and no longer is.** It asked for a 10-point drop and the
game delivers 16.0. It was recorded here as an honest failure for as long as the instrument
was wrong, which is exactly how it should have looked from the inside.

No number was ever moved to make a gate green. That is the whole point of writing them
down first - and it is what made the retraction above possible to write, because the
failing number was still sitting there when the instrument was fixed.

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
