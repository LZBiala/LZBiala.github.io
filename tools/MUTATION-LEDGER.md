# The mutation ledger

A green test suite tells you the tests passed. It does not tell you the tests would have
noticed if the code were wrong. This file is where that second question gets an answer, and
a number.

Run it yourself: serve the repository root over http and open
`tools/mutation-lab.html`. It seeds each defect from `tools/mutations.json` into
`game.html`, runs the game's whole test suite against the mutated file in a sandboxed
iframe, and reports how many defects at least one test noticed.

## The number

| run | date | tests | seeded defects | caught | kill rate |
|---|---|---:|---:|---:|---:|
| round 1, before | 2026-08-24 | 425 | 32 (mine) | 17 | **53.1%** |
| round 1, after  | 2026-08-24 | 439 | 32 (mine) | 32 | **100%** |
| round 2, before | 2026-08-24 | 439 | 143 | 41 | **28.7%** |
| round 2, after  | 2026-08-24 | 446 | 143 | 49 | **34.3%** |

### The only comparison that is actually matched

An earlier version of this file headlined "100% against my own defects, 8.1% against
independent ones" and called the gap a measure of authorship. **That was wrong, and the
correction matters more than the original claim.**

The 100% is *training-set* performance. The suite was patched until those exact 32 defects
died, then scored against the catalogue it had been fitted to. The 8.1% is a held-out score.
Comparing them attributes to authorship a gap that is partly plain overfitting.

The matched pair was already in the table above - both measured **before** any targeted
fixing:

| who designed the defect | seeded | caught | blind kill rate |
|---|---:|---:|---:|
| me, the author of the tests | 32 | 17 | **53.1%** |
| designed independently | 111 | 9 | **8.1%** |

**6.5x, not 12x.** Still the finding; just the honest size of it.

The same correction applies to the round-2 "after" row. Seven guards were written against
eight specifically named critical mutants and iterated until they killed, so the 17 of 111
is not a detection rate either. Excluding the eight that were targeted, the suite's blind
rate on independent defects went from 9 of 111 to **9 of 103 (8.7%)** - which is to say it
did not move. What moved was the number of holes repaired. Those are different quantities
and this file previously reported them as one.

**The rule this earns: never publish a kill rate against a catalogue the suite was patched
against.** "Before" numbers are the measurement. "After" numbers are repair progress, and
are labelled as such from here on.

### Known confounds in the 6.5x, stated rather than defended

- **Subsystem stratification.** The independent catalogue was drawn one pass per subsystem,
  deliberately covering areas this file admits are barely probed - dual techs, limit breaks,
  crafting, the growth tree. My own 32 cluster where my attention already was, which is also
  where the tests already were. Part of the gap therefore measures how unevenly the suite
  covers the file, not who wrote the defect.
- **Screening was not symmetric.** "Screened" for the independent set meant: the find string
  occurs exactly once, lands in production code, keeps the file parsing, and is not a no-op -
  plus a dedup against the existing catalogue on the (find, replace) pair, which removed
  exactly one candidate. My own 32 had no such screen.
- **Equivalent and unreachable mutants are not excluded.** The standard first objection to
  any low kill rate, and it applies here: some survivors may be semantically equivalent or
  sit on states a real playthrough cannot reach. That deflates the independent rate only.
- **111 draws are not 111 independent samples.** Agents working from the same instructions
  have correlated taste in defects. The effective n is smaller than it looks.

### What "killed" does and does not mean here

A mutant counts as killed if ANY test fails. Many tests in this suite are source greps over
the file's own text, so some kills mean "a check noticed the source changed", not "a
behavioural assertion failed". A textual kill gives no assurance against the same defect
spelled differently. The construct being measured is *would some test notice this exact
edit*, which is weaker than "the suite covers this behaviour".

**That gap is the finding.** Round 1's ledger warned that a kill rate measured against
defects chosen by the person who wrote the tests is optimistic. Round 2 measured how
optimistic: a suite that catches everything I thought to check catches about one defect in
twelve that somebody else thought to check.

The 111 independent defects were designed by readers working from the source with no
knowledge of the tests, one per subsystem, then screened against the file for uniqueness and
for being real rather than cosmetic. Not one of them failed to apply.

Every surviving mutation stays in `mutations.json`, and always will: a mutation that quietly
left the catalogue once the suite learned to catch it would make every later number a lie.

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

## What round 2's survivors are, and are not

**They are not bugs in the shipped game.** Every one is a defect that was seeded on purpose
and then removed; the game does not contain them. What survived is a statement about the
TESTS: 102 things this suite would not notice if somebody broke them tomorrow.

Rated by the readers who designed them, the survivors were 8 critical, 47 high, 43 medium
and 4 low. A sample of what "critical" meant:

- a ward is never spent when it absorbs a hit, so one cast makes an ally immune for the
  rest of the battle
- KERNEL MODE, the final boss of the rescue arc, loses a digit of health and dies in a round
- beating NULLBYTE's first form marks the room cleared, so a party that then loses to the
  second form can never fight it again - the rescue becomes unwinnable with no way back
- the hero's attack stops growing with level
- the manual save slots point at the previous schema's namespace and overwrite un-migrated
  saves
- WIKI's recruit trigger is one square off its own battle tile, so winning that fight
  recruits nobody

**The eight critical gaps are closed.** Seven guards, written as invariants: a ward is spent
and the next hit lands; a boss chain never escalates to something weaker than the form
before it; beating form one does not clear the room form two stands in; every character
gains HP, MP and attack from levelling; every save slot lives in the current schema's
namespace; a limit break lands through armour, fog and unverified regeneration; and every
recruit is wired to a fight that exists on that square.

Three of those guards were wrong on the first attempt, which is the point of checking them
against a good file and then against a bad one:

- one was a bad fixture - a hand-built battle object without the `foes` array the whole
  combat path reads through, a shape production never has;
- one found a real exception worth naming - the inn's third bed is a fight square wired by
  hand rather than listed in the zone's battle table;
- and one **was itself vacuous**. The limit-break guard accepted `a.lb===0` as evidence the
  limit had fired, and `castLimit` zeroes the gauge on the way in - so the condition was true
  whatever happened, and it passed with the defect present. It was caught only because the
  lab reported the mutant surviving a guard written specifically to kill it.

That last one is the argument for this instrument in a single incident: a vacuous guard,
written during an audit of vacuous guards, by someone who had spent the day thinking about
nothing else. Review did not catch it. Measurement did.

**The 94 remaining survivors are a published backlog, not a secret.** They stay in
`mutations.json` with their ids, so anyone can re-run the lab and watch them survive. Fixing
them by deleting them was available and was not taken.

## The held-out result, and it is the one that matters

A second catalogue of 107 defects was sealed BEFORE any of the round-3 guards were written,
drawn by a different sampling protocol (by defect TYPE - off-by-one, inverted comparison,
wrong variable, dropped guard, wrong constant, copy-paste, missing clamp, lifecycle - rather
than by subsystem). Nothing in it was visible while the guards were being built.

| population | seeded | caught | rate |
|---|---:|---:|---:|
| mine - guards were fitted to these | 32 | 32 | 100% |
| independent - guards were fitted to these | 111 | 61 | 55% |
| **HELD OUT - sealed before the guards existed** | **107** | **6** | **5.6%** |

**Seven guards written as general rules took the fitted rate from 15.3% to 55% and the
held-out rate to 5.6%.** They closed the holes they were pointed at and almost nothing else.

That is the finding, and it is worth more than the improvement it disproves. The guards were
deliberately written as invariants rather than as answers to specific mutations - a sheet
earned by fighting must equal a sheet built at that level; exits must pair up both ways;
every skill must move the number its own description promises. They FELT general. Measured
against defects nobody had pointed at, they were not.

The agents who designed the held-out catalogue predicted that **none** of their 117 defects
would be caught. Six were. They were slightly pessimistic and essentially right.

### What this does not prove

- The two catalogues were drawn by different protocols, so part of the 55-to-5.6 drop is
  sampling difference rather than held-out effect. The clean version of this experiment
  draws both sets the same way, and that has not been done.
- 6 of 107 is a small numerator; the interval around 5.6% is wide.
- No equivalent-mutant screening was applied to the held-out set either, so it is a floor.

### What it does suggest, and what it changes

Hardening a suite against a list of known gaps buys you that list. If the goal is a suite
that notices what nobody predicted, the gaps have to keep coming from outside - which makes
"get the next catalogue from somewhere else" a standing practice rather than a one-off, and
makes any kill rate quoted without saying which population it came from close to meaningless.

The 151 survivors stay in `mutations.json`, ids and all.

## Round 3: closing gaps by family, not by mutation

94 named survivors invites the obvious move - write 94 tests, one per mutation, and watch
the number go up. That is teaching to the test at scale, and this file already argues
against it.

So the survivors were grouped by the RULE each violates, and seven guards were written to
assert those rules:

| family | what it asserts |
|---|---|
| world | exits pair up both ways, doors come home beside their own entrance, walking off an edge lands you on the opposite edge, spawns are walkable, ambushes happen in undergrowth and not on the road |
| bestiary | prose that promises fog gets a foe that has it, escalation flags are ordered, every speed belongs to a real enemy, chains never escalate to something weaker |
| skills | every skill moves exactly the number ITS OWN description promises, parsed from the shipped text rather than restated in the test |
| stacks | putting things in a pile adds to it - bank, shop counter and grave all checked, because all three had assign-where-it-should-add defects |
| gear | one copy, one pair of hands; and a transmute leaves no slot pointing at an item the player no longer owns |
| saves | loading is lossless and idempotent, the Cleric merge fires wherever she sat, rows survive the trip, the clock accumulates |
| growth | a sheet earned by fighting equals a sheet built at that level - two independent paths to the same character, which must agree |

The last one is the shape worth stealing. `mkActor(id, 8)` builds a level-8 character
directly; `gainXP` walks one up from level 1. Neither knows about the other. Asserting they
agree catches drift anywhere in the level-up maths without naming a single stat, and it
would have caught the seeded defect that grew max MP by the HP growth figure.

### Seven guards, and what writing them cost

Five of the seven were wrong on the first attempt. Every one of those five was the same
mistake in a different costume: **a fixture too weak to make the guard fail.**

- the ward check built a battle object by hand, without the `foes` array the whole combat
  path reads through - a shape production never has
- the interior-landing check ran with an empty party, and `npcsFor` HIDES companion NPCs
  until they join, so the square it was meant to catch looked empty
- the Compass check never equipped the Compass, so the function returned 0 for every case
  and all three of its assertions passed for the same wrong reason
- the merge check made the hero the deepest investment, which left two of the three
  candidates interchangeable
- the Trial check exercised the reload path and never the path that grants the gift

None of these were caught by reading them. All five were caught by running the guard against
the defect it was written for and watching it pass. **A guard is not finished when it goes
green on a clean file; it is finished when it goes red on a broken one.**

Two rules were also written, run, and then DELETED for being untrue rather than kept and
weakened: a "superboss is the fastest thing in the game" rule that this game simply does not
obey, and a "her notes run forward in time" rule that cannot fail, because exactly one note
carries a date. The mutations they were aimed at stay in the catalogue as survivors. Keeping
a check that cannot fail would have been the worse trade, and this file has already paid for
that lesson once.

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

- **A catalogue written by the author of the tests is worth very little.** Round 1 said this
  as a caveat. Round 2 measured it: 100% against my own defects, 8.1% against somebody
  else's. If you read only one number from this file, read the second one - and treat any
  mutation score whose catalogue came from the same hands as the tests with the suspicion
  that gap deserves. It is the same failure mode `wiki-memory-lab` labels "upper bound by
  construction" on its own precision row, and it is much larger than I expected.
- **It measures the in-page suite only.** `site_check.py` and `test_combat_sim.py` are
  separate nets that this harness cannot run, and at least one round-1 survivor was already
  caught by them.
- **32 is a small sample.** Whole subsystems are barely probed: dual techs, limit breaks,
  crafting recipes, the growth tree's individual nodes, most story flags. The catalogue is
  meant to grow, and the honest reading of the current number is "this is what 32 defects
  found", not "the suite is 100% effective".
- **A 100% kill rate is not a finish line.** It means the catalogue no longer contains a
  defect this suite misses. The next round's job is to find defects that are not in it yet.

## What would turn this from a number into a measurement

An adversarial review of this methodology (2026-08-24) named one change worth more than
every other correction on this page combined:

> Freeze the suite. Generate one fresh author batch and one fresh independent batch under
> the **identical** protocol - same quotas, same screening, neither seen while writing
> guards - run both once, and let that pair be the headline.

That isolates authorship, which is the thing being claimed. Everything else adjusts the
number; this is what makes it an experiment. The independent half is already sealed. The
matching author batch is not yet drawn, so the 6.5x above still carries the stratification
confound named earlier, and should be read as indicative rather than measured.

Recorded here rather than quietly fixed, because the gap between "we know what would make
this rigorous" and "we did it" is exactly the kind of thing this file exists to keep honest.

## Calibration

Before trusting a single result, the harness was checked against two mutations with known
answers: changing a boss's HP (a value one test asserts directly) must be caught, and
rewording a battle tip from "the whole round" to "the entire round" - a genuinely null
change - must survive. Both behaved correctly. The unmutated baseline is also run first
every time, and if it is not clean the whole run is declared void rather than reported.

The suite is triggered by a query string and a blob URL cannot carry one, so the harness
rewrites that one line in every mutant. The same rewrite is applied to the baseline, which
is how we know it biases nothing: if it broke anything, the baseline would not be clean.
