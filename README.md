# lzbiala.github.io

Personal site of **Lito Zarate Biala** - Site Reliability → AI Reliability →
Forward Deployed.

## What this is

A portfolio site (index.html) with a guided-tour page, a resume, and an 8-bit browser role-playing game (game.html), all plain static files. The game's balance was tuned by a Python simulator that fights battles with seeded dice. Every campaign counted in the game's published battle total has a log and a seed in this repo; earlier campaigns whose logs live in a private journal were dropped from the total rather than asserted. Then 250 deliberate defects were planted in the game, one at a time, to measure how many its own tests would notice.

## Why it matters

A battle count and a green test suite both sound like proof. The count matters only if a stranger can re-run it; a green suite says the tests passed, not that they would have caught a bug. Three times a number or a check in this repo was wrong and nobody had noticed, and each time the fix was a check that measures the thing rather than a promise to be careful:

- The ledger's stated battle total was 521,024 higher than its own table, because three updates edited the total instead of re-adding the column. Now tools/site_check.py adds the column on every run.
- The simulator let a group of four enemies attack once per round, so a four-enemy room hit as hard as one enemy and roughly 3.5 million published battles described a game that did not exist. Now tools/test_combat_sim.py checks that damage per round rises with the enemy count, and the gate runs it.
- Four guards in this repo were passing while checking nothing (one compared two empty lists). Now the mutation lab measures whether the tests notice a planted defect.

## Try it in 60 seconds

Tested with Python 3.12 and git, from the repo root:

```
python tools/site_check.py
```

49 "PASS" lines and "ALL PASS" in 3 to 4 seconds on a laptop; the count is today's and grows as checks are added. That is the whole gate, simulator self-tests included.

```
python tools/combat_sim.py lab12 - 20
```

A 20-repetition run of the shipped dungeon walk, about a second: "LAB12 VERDICT: ALL GATES PASS" and "lab12 simulated battles: 13,425". Treat that verdict as a demo, not evidence: the ledger records one lab's verdict flipping with sample size, and the logged 2026-08-31 lab12 run used ten times as many repetitions.

To watch the game test itself, run `python -m http.server 8123` and open http://localhost:8123/game.html?test=1. On 2026-09-01 that showed 507 of 507 passing. The count is shown live rather than pinned here because the suite generates some of its entries at load, so no fixed number could be checked against the file.

## How it works, intuitively

The simulator (tools/combat_sim.py) is a second copy of the game's fight arithmetic, written in Python. It plays a fight thousands of times with random dice and counts wins, knockouts and turns. The dice start from a seed, a fixed number that picks the whole sequence of rolls, so the same seed on the same code gives the same result. Each campaign's pass/fail rules, called gates, are written down before the first battle; the two times a gate was changed after seeing results, the ledger says so. Two copies of the same arithmetic can drift apart, and they did: the simulator was found modelling three enemies under names the game does not use, letting a character act twice in one round, and rounding damage the other way from the game. The fidelity tests in tools/test_combat_sim.py compare the copy against game.html; they found the first of those on their first run, and the other two were found by a code review and then written as tests that failed before the fix and pass after it.

The mutation lab (tools/mutation-lab.html) checks the checkers, the way you would test a smoke alarm with smoke rather than trusting its test button. A mutation is one small deliberate change to the game's code. The lab applies one, runs all of the game's tests against the changed file, and records whether any test failed; over 250 mutations, the share that made a test fail (the kill rate) estimates how many bugs of that kind the tests would notice.

The gate (tools/site_check.py) recomputes the numbers it can reach from disk - the battle total, the roster size, the project count, whether every planted defect still applies - and fails when the text disagrees. The kill rates are measured in the browser, outside the gate.

## What the numbers mean (and what they do not)

- 7,313,561 simulated battles is the sum of 18 campaign rows in tools/BALANCE-LEDGER.md, re-added by the gate on every run, each row naming a log under tools/sim-runs/ and a seed in the script; the ledger says only the last two rows describe the shipped game, that everything above the "instrument fixed" pair "was measured by a simulator that could not see the thing it was measuring", and all 18 rows were logged before two further simulator defects were fixed on 2026-08-31, after which 9,814,299 validation battles on the fixed simulator were logged separately and deliberately not added to the headline.
- After seven test guards were written to close gaps the lab found, the tests caught 32 of 32 defects the test author designed (100%), 61 of 111 designed independently (55%) and 6 of 107 sealed away before the guards were written (5.6%), per tools/MUTATION-LEDGER.md dated 2026-08-24; the ledger calls the first two "training-set" scores because the guards were fitted to those catalogues, which is like grading a student on the exact questions they practised, calls the 5.6% a floor with a wide interval ("6 of 107 is a small numerator"), and notes the sealed set was drawn by a different protocol, so part of the drop may be sampling rather than overfitting. The game's suite has grown since (the ledger's table last records 446 tests; 507 run today), so today's rates may differ; the lab re-derives them in your browser.

Both are checkable here, one from the terminal and one in a browser. The five project cards on index.html quote numbers measured in those projects' own repos; this repo only asserts them.

## Where it loses

In its own words: the simulator's "four-pack hit exactly as hard as one foe" (a group of four enemies did the damage of one); one lab's verdict "depends on the sample size"; "many tests in this suite are source greps over the file's own text" (a grep is a text search, so those tests notice that the code changed, not that it behaves wrongly); and the seven guards "closed the holes they were pointed at and almost nothing else".

Not written anywhere in the repo until now: there is no continuous integration, meaning no server re-runs the checks when code is pushed. The gate runs only when someone runs it locally, and the game's in-page tests and the mutation lab run only in a browser, by hand.

## Try your own case

Plant one defect: add an entry to tools/mutations.json with an id, a "find" string that occurs exactly once in game.html before the line `const TESTS = [`, a "replace" string that differs from it, and an "origin" tag of your own (say "reader") so it does not join the three published populations. Run `python tools/site_check.py`; it refuses a find string that matches zero or two places, a no-op, or a duplicate. Then open http://localhost:8123/tools/mutation-lab.html and press "Run the mutation suite"; the lab runs the whole catalogue and lists your row by id, KILLED if any test noticed and SURVIVED if none did.

---

## For engineers

Everything below is the original technical README: the design, the measurements, and how to reproduce them.

One static file (`index.html`), no frameworks, no trackers, no external
requests - built the same way as the five projects it presents:

- [wiki-memory-lab](https://github.com/LZBiala/wiki-memory-lab) - the memory layer
- [agent-mutation-lab](https://github.com/LZBiala/agent-mutation-lab) - the evaluation layer
- [adversarial-chambers](https://github.com/LZBiala/adversarial-chambers) - decision calibration
- [memory-repair-lab](https://github.com/LZBiala/memory-repair-lab) - the control loop

Every measured number those repos publish regenerates in CI with zero API
keys; the build fails if a claim drifts.
