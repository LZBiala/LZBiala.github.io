# The mutation ledger

A green test suite tells you the tests passed. It does not tell you the tests would have
noticed if the code were wrong. This file is where that second question gets an answer, and
a number.

Run it yourself: serve the repository root over http and open
`tools/mutation-lab.html`. It seeds each defect from `tools/mutations.json` into
`game.html`, runs the game's whole test suite against the mutated file in a sandboxed
iframe, and reports how many defects at least one test noticed.

## The number

| run | date | tests in the suite | seeded defects | caught | kill rate |
|---|---|---:|---:|---:|---:|
| round 1, before | 2026-08-24 | 425 | 32 | 17 | **53.1%** |
| round 1, after  | 2026-08-24 | 439 | 32 | 32 | **100%** |

The fifteen defects that survived round 1 were live in production code with every one of
425 tests green. They are still in `mutations.json`, and they always will be: a mutation
that quietly left the catalogue once the suite learned to catch it would make every later
number a lie.

## Why this exists

On 2026-08-24 an adversarial review found four guards in this repository that were reporting
green while measuring nothing at all - a comparison of two empty lists, a regex searching for
words the prose does not use, a scan that stripped nothing, and a bracket-matcher that read a
space as an opening bracket. All four had been written in good faith, passed on the day they
were written, and rotted silently when the thing they watched moved.

Finding them was luck. This is the instrument that replaces the luck.

## What the round-1 survivors were

Every one is a real defect a tired engineer could write.

**Combat, six of them.** The minimum-one-damage floor could be removed and no test noticed,
so a debuffed party could hit for nothing forever. Damage could be allowed to go negative,
which means being hit HEALS you. The base crit rate could move from 0.15 to 0.25 - a change
that invalidates all 7,313,561 published balance battles - silently. The default enemy speed
could jump from 4 to 9 and reorder every fight. PapaFoxx, a caster, could be moved into the
melee row, in either of the two places that rule is written.

**Saves, two.** The schema version check could be deleted, so a save from another build
loads without migration. `GHOST_IDS` could be emptied - and that array is what the "never
seats a soul the roster deleted" guard iterates over, so emptying it makes that guard check
nothing. A vacuous guard, found by mutating the data it reads.

**World, two.** Barrels could stop being solid and the player could walk through the
scenery. The interact scan order could be reversed, which shadows every neighbour behind
whatever you happen to be standing on.

**Economy and display, four.** Resource nodes could pay double, which is the whole crafting
economy. A consumable could heal almost twice what its own text promises. A heal could stop
being clamped to maximum HP. The XP bar could render past its own ends.

**Claims, one.** A flip-test figure in a battle tip could lose the caveat that makes it
honest. Worth separating out: this one was NOT undetected by the project - `site_check.py`
catches it over the file on disk. It was undetected by the in-page suite, which is what a
writer editing this file actually runs. The guard has been ported into the game as well, so
both nets now hold it.

## How the guards were written

**Assert the invariant, not the mutant.** A test written to notice one specific edit is
teaching to the test. Where the rule could be exercised, it is: damage is dealt with a raw
value of -9 and the result checked, `incoming` is called across a sweep with every reduction
stacked, a node is gathered with the random roll forced to both ends, a save is written at
three schema versions. Those tests catch the whole family, not the one edit that provoked
them.

**Pin a constant only when the constant is the contract, and say why.** The base crit rate
is pinned at 0.15 because `BALANCE-LEDGER.md` accounts for 7,313,561 battles that were all
fought at 0.15; move it and the published campaigns stop describing the shipped game.

**A guard that derives its expectation from the thing it checks is blind by construction.**
The reachability guards read `IACT`, the interact scan order, in order to walk it - so they
cannot notice `IACT` changing. That is why reversing the scan order survived. There is now
one test that states the order rather than reading it, and the reachability guards still read
it, so the two cannot drift apart.

**Two files are better than one witness.** Six of the surviving combat constants also exist
in `combat_sim.py`, because the simulator reimplements the same maths. `test_combat_sim.py`
now holds the two files to the same values from the other side. If they ever disagree,
either the game changed without the balance numbers being re-run, or the instrument drifted
away from the game it claims to model.

## What this number is not

- **It is an upper bound, and the catalogue is mine.** I chose the 32 defects. A kill rate
  measured against defects chosen by the same person who wrote the tests is optimistic in
  exactly the way `wiki-memory-lab`'s 0.95 precision/recall row is optimistic, and for the
  same reason. It is a floor on how bad things are, not a ceiling on how good they are.
- **It measures the in-page suite only.** `site_check.py` and `test_combat_sim.py` are
  separate nets that this harness cannot run, and at least one round-1 survivor was already
  caught by them.
- **32 is a small sample.** Whole subsystems are barely probed: dual techs, limit breaks,
  crafting recipes, the growth tree's individual nodes, most story flags. The catalogue is
  meant to grow, and the honest reading of the current number is "this is what 32 defects
  found", not "the suite is 100% effective".
- **A 100% kill rate is not a finish line.** It means the catalogue no longer contains a
  defect this suite misses. The next round's job is to find defects that are not in it yet.

## Calibration

Before trusting a single result, the harness was checked against two mutations with known
answers: changing a boss's HP (a value one test asserts directly) must be caught, and
rewording a battle tip from "the whole round" to "the entire round" - a genuinely null
change - must survive. Both behaved correctly. The unmutated baseline is also run first
every time, and if it is not clean the whole run is declared void rather than reported.

The suite is triggered by a query string and a blob URL cannot carry one, so the harness
rewrites that one line in every mutant. The same rewrite is applied to the baseline, which
is how we know it biases nothing: if it broke anything, the baseline would not be clean.
