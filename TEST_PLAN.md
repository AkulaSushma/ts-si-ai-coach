# TEST_PLAN.md

## Purpose

Define what must be tested, and how, before any component may be called `COMPLETE`.
A component with no test has not been verified — it has only been written.

## How to run everything

From the project folder:

```
python scripts/validate_bootstrap.py
python -m unittest discover -s tests -v
```

Both use only the Python standard library, so there is nothing to install
(decision `D-0006`).

## Test layers

| Layer            | Scope                                                  | Exists now |
| ---------------- | ------------------------------------------------------ | ---------- |
| L0 Structural    | Repository layout, governance files, config validity     | Yes        |
| L1 Data integrity| Schema validation, referential links, provenance present | No         |
| L2 Deterministic | Mathematical methods and shortcut validity boundaries    | No         |
| L3 Accounting    | Research manifests balance; weightage denominators stated | No        |
| L4 Backend       | API contract behaviour                                   | No         |
| L5 Tutor         | Answers trace to `VERIFIED` knowledge only               | No         |

Layers L1 to L5 are `BLOCKED` on the components they test existing. That is a real
status, not an omission.

## L0 — Structural checks (implemented)

Acceptance criteria, each independently checked by
`scripts/validate_bootstrap.py` and asserted by `tests/bootstrap/test_bootstrap.py`:

1. Every required directory exists.
2. Every required governance file exists at the repository root.
3. No governance file is empty or near-empty.
4. Each governance file contains its required section headings.
5. Every top-level directory has a `README.md`.
6. `config/model_routing.json` is valid JSON.
7. Every agent role named in `agents/README.md` appears in `model_routing.json`.
8. No authoring role shares a provider with its matching verification role.
9. `.gitignore` exists and excludes `.env`, key files, and the runtime database.
10. No tracked file contains a plausible API key pattern.
11. The status vocabulary is defined in `CLAUDE.md` and used consistently.
12. `data/` is git-ignored while `data/README.md` remains tracked.

## L1 — Data integrity (planned)

Every knowledge record validates against its schema; every record cites at least one
`SOURCE_LEDGER.md` ID that exists; no record is `VERIFIED` without a matching run in
`verification/runs/`; no `T4_AI` record is `VERIFIED` by the provider that authored it;
counts in `KNOWLEDGE_LEDGER.md` match actual file counts.

## L2 — Deterministic mathematics (planned, and the most important layer)

For every method and shortcut in `knowledge/methods/`:

- the standard method computes the correct result across a generated input range
- the fast method agrees with the standard method within its stated
  `validity_conditions`
- the fast method **disagrees** outside those conditions, and the test asserts that it
  does

That last point is the one that matters. A shortcut whose failure boundary is untested
is a trap waiting to cost marks in the exam, and it must not be labelled `VERIFIED`.

## L3 — Accounting checks (planned)

Every research manifest satisfies
`expected = processed + inaccessible + irrelevant + duplicate + failed`; every
non-processed item carries a reason; every weightage table states its paper set,
question total, and unclassifiable count; no percentage is published from an
uncounted denominator.

## L4 — Backend (planned)

Endpoint contracts match `specs/api/`; SQL is parameterised everywhere; the server
binds only to `127.0.0.1`; no secret appears in any response or log.

## L5 — Tutor behaviour (planned)

The hardest and most important guarantee: every factual statement the tutor makes
traces to a `VERIFIED` knowledge record. Tests must include adversarial prompts that
try to make the tutor answer beyond its knowledge base, and assert that it says it does
not know instead of improvising.

## Non-negotiable testing rules

- Never weaken, skip, or delete a test to obtain a pass. If a test fails, decide whether
  the code or the expectation is wrong, fix that, and record the reasoning.
- A failing test means `PARTIAL` or `BLOCKED`. It never means `COMPLETE`.
- Test evidence is the actual output, pasted into `docs/reports/`. Never a paraphrase.
- A test that has never been observed to fail when it should has not been shown to work.

## Status

`PARTIAL` — L0 implemented and passing. L1 to L5 specified but `BLOCKED` on the
components they test.
