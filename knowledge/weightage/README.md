# knowledge/weightage/ — three categories that must never be mixed

Three different questions get three different files, three different tiers, and three
different sources. Mixing them is how "coaching institutes emphasise X" quietly becomes
"the board weights X", which is exactly the error this project exists to prevent.

| File | Question it answers | Tier | Only valid source |
| ---- | ------------------- | ---- | ----------------- |
| `official_marks_structure.json` | What marks and duration does the notification prescribe? | `T1_OFFICIAL` | The official notification |
| `historical_observed.json` | How many questions did real past papers actually ask, per topic? | `T2_HISTORICAL_PYQ` | Counted questions from acquired papers |
| `estimated_priority.json` | What should be studied first, given the above? | `T4_AI` | Explicit judgement, with its inputs named |

Specification: `specs/features/official-knowledge-foundation.md` (`SPEC-OFF-001`) §7.

## The rules

- Each file declares exactly one `provenance_tier` and contains no other tier string.
  `tests/official/test_official_knowledge.py` asserts this.
- `official_marks_structure.json` may contain **only** what the notification itself
  states. A marks distribution across topics is `T1_OFFICIAL` only if the notification
  prints a topic-wise distribution. If it prints only per-paper totals, then that is
  all the official weightage that exists, and the file says so.
- `historical_observed.json` requires **counted** papers, never impressions. Under
  `research/README.md` the count must satisfy
  `expected = processed + inaccessible + irrelevant + duplicate + failed`, and a
  partial count is reported as `120 / 250`, not rounded up to "most".
- `estimated_priority.json` is a judgement and is labelled as one. It must name the
  official and historical inputs it used, so a reader can disagree with the judgement
  without doubting the data.
- No file here may be presented to a learner without its tier. A priority ordering that
  looks official is worse than no ordering, because the learner cannot tell it is a
  guess.

## Current state — 2026-09-06

All three are empty and `BLOCKED`:

- official marks structure — no notification retrieved (`B-09`)
- historical observed — no past paper acquired (`B-02`)
- estimated priority — depends on both of the above; producing it now would be a
  judgement over no data, which is indistinguishable from invention
