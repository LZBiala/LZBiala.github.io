# The balance ledger

The game's title screen says its balance was tuned on 23,000,000+ simulated battles.
This file is where that number is accounted for, because a claim nobody can check is
just a number in a nice font.

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

**Published total: 1,229,824 battles**, every one of them reproducible from the script
and the seeds in it.

## The rest of the number, stated plainly

The 23,000,000+ figure is cumulative across the whole build, not just the campaigns above.
The earlier campaigns - encounter tuning, the boss table, limit breaks, dual techs, the
companion roster, the crafting economy - ran across earlier sessions and are recorded in a
private engineering journal, not in this repo. Their counts are asserted here; they are not
independently checkable by a reader, and I am not going to pretend otherwise.

So, precisely:

- **checkable from this repo: 1,229,824 battles**, with logs and a runnable script.
- **asserted from the build journal: the remainder**, roughly 21.8M, carried forward as a
  running total in dated entries.

If you only trust what you can run yourself, trust the first number. The simulator is right
there.

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
