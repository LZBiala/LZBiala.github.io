# lzbiala.github.io

Personal site of **Lito Zarate Biala** - Site Reliability → AI Reliability →
Forward Deployed.

## What this is

A test rig for code reviewers. It takes three short clean Python files (143 lines in all), plants exactly one known bug into a copy, mixes the 10 bugged copies with the 3 untouched originals under numbered filenames that reveal nothing, and scores a reviewer on naming the kind of bug within 2 lines of where it was planted. Any finding on an untouched copy counts against it. What ships is the rig, not a verdict on any AI.

## Why it matters

AI code reviewers are being wired in as gates that approve merges and block releases; that is the repo's premise, not something it measures. A gate never fed a bug you already know is there is an unmeasured gate: nobody knows what it catches or waves through. A reviewer that flags everything looks diligent while useless; this rig turns both failures, the missed bug and the false alarm, into numbers.

## Try it in 60 seconds

Python 3.11 or newer; the program needs no packages, keys or network. What was actually run, in a bash shell:

```
git clone https://github.com/LZBiala/agent-mutation-lab
cd agent-mutation-lab
PYTHONPATH=src python -m mutationlab demo
```

PowerShell: `$env:PYTHONPATH="src"; python -m mutationlab demo` (also run). The repo's own quickstart uses `pip install -e .`; not re-run here.

In under a second it prints a verdict per file (`HIT`, one deliberate `MISS`, `CLEAN-OK` on untouched copies), a score line and a one-line summary of the voting study. Then `git diff --exit-code` prints nothing: the demo rebuilt all 19 committed artifacts and the README byte-for-byte, checked on Python 3.12.10 in a scratch copy. Not re-checked, so the repo's claims: that CI (the automatic check on every push) passes on Windows and Linux, and that the byte-for-byte match is promised only on the 3.12 it pins, so 3.11 runs the demo without the no-diff guarantee.

## How it works, intuitively

The repo's own picture is a smoke-alarm drill: light a controlled puff of smoke, check the alarm rings, then check it stays quiet on a normal day. The puff is a planted bug; the normal day is an untouched copy. Two differences: this alarm must also say what kind of smoke and where, within 2 lines; and the person who lit the puff also wrote the bundled alarm's rules, so a ring proves the drill works, not that the alarm is good. The alarm worth testing is the one you bring.

Each kind of bug is one exact text pattern and its broken replacement (nine kinds, in `src/mutationlab/defects.py`). The engine swaps that one line and writes the answer to a key file outside the folder the reviewer reads; if the pattern is absent it refuses rather than guess, a contract the tests enforce. The bundled reviewer is eight text rules for nine kinds; the ninth is missing on purpose, so the demo can show a miss.

A second study asks whether nine unreliable copies of that reviewer, voting, beat one. Each copy is made unreliable with fixed dice: it drops each real finding with probability 0.30 and, with probability 0.10 per file, invents one that is not there. A finding survives only if more than half the copies name the same line and kind. Every number is averaged over 200 repeats with fresh dice.

## What the numbers mean (and what they do not)

- 9 of 10 planted bugs flagged at the right place (`metrics.jsonl`) is what the repo calls harness conformance: the measuring rig works. It is not a catch rate, because the same author wrote the bugs and the rules. The 1 miss is boolean-precedence (a dropped pair of parentheses that changes what an and/or means), which has no rule on purpose so the demo shows failure.
- 0 false alarms on the 3 untouched copies is 0 by construction with text rules, in the repo's own words; checked here that none of the eight rule patterns occurs in the clean files. It proves only that the clean-file check exists, so a live reviewer cannot score by flagging everything.
- In the voting study (`metrics-ttc.jsonl`), where the noise is dice, not a model, and the copies are independent by construction: nine independent copies lift the catch rate on the 9 bugs the rules can see from 0.6917 to 0.9006 (about 69 to 90 in 100; 1800 reviews per point); nine copies sharing one set of dice rolls stay at exactly 0.6917; copies wrong more often than right fall from 0.3328 to 0.1783, about fifteen points; and the kind of bug no copy can see scores 0 however many copies vote, again by construction. The repo's caveat travels with these: real copies of one model share mistakes, so real gains sit at or below the independent line, and below one-half accuracy voting hurts.

## Where it loses

The repo's own words: "not a benchmark of any AI model, not a bug-finding tool for your codebase". Only 4 of the 9 kinds of bug have an executable proof of harm, a test that runs the bugged file and watches it misbehave; the other 5 are documented patterns, not run. One toy domain (a town-library catalog), one bug per file, one-line edits, a 2-line slack the repo itself calls "generous", and a vote that counts agreement only on the exact line and kind, which it calls "the optimistic simplification". The voting study is synthetic throughout: errors that behave like dice are the friendly case, not the normal one.

## Try your own case

Add a kind of bug: append one entry to `MUTATORS` in `src/mutationlab/defects.py` (an id, a title, a short story of the harm, the text pattern, its broken replacement). Run the demo and `python -m pytest -q` (pytest is the one development package), then commit what they regenerate, or CI fails. Add no matching rule and your bug joins the miss column and the voting study's wall automatically. Score your own reviewer: implement the small `Reviewer` contract in `src/mutationlab/reviewer.py` (take a file's text, return findings, each a line and a kind) and call `run_pipeline` in `src/mutationlab/runner.py` with it; there is no command-line switch yet. Keep `runs/answer-key.json` out of its sight. Those numbers are yours and stay out of this README.

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
