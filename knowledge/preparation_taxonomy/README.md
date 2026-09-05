# knowledge/preparation_taxonomy/ — what to teach, not what the board said

The official syllabus is often shorter and vaguer than what actually gets asked.
"General Science" as a syllabus line does not tell a candidate to study lens formulae.
This folder is where that practical breakdown lives — and it lives **here** precisely
so it can never be mistaken for the official syllabus.

Specification: `specs/features/official-knowledge-foundation.md` (`SPEC-OFF-001`).

## What belongs here

- Subtopics that coaching institutes teach but the official document does not name
- Question families and skill groupings observed in previous-year papers
- Groupings useful for scheduling, revision and diagnostics

## What must never happen here

- A node tiered `T1_OFFICIAL`. Nothing in this folder is official, by definition.
  `tests/official/test_official_knowledge.py` fails if the string appears in a node.
- A node presented to a learner without its tier visible.
- A node with no `official_anchor` and no `NO_OFFICIAL_ANCHOR` marker. Every node either
  hangs off an official syllabus node or openly admits it hangs off nothing.
- Editing `knowledge/official/syllabus.json` to make an anchor exist. If the official
  document does not name it, the anchor does not exist, and the node says so.

## Tiers used here

| Tier | When |
| ---- | ---- |
| `T3_EXPERT` | Derived from a named educator, book, or coaching source, which is cited |
| `T2_HISTORICAL_PYQ` | Derived from counted previous-year questions, which are cited |
| `T4_AI` | Derived by model reasoning, with the reasoning recorded |

## Current state — 2026-09-06

**Empty by design, and empty for two further reasons.** The official syllabus it should
anchor to does not exist yet (`B-09`), and no past paper or expert source has been
ingested (`B-02`, `B-08`). Populating it now would mean inventing a breakdown of a
syllabus nobody has read.

`taxonomy.json` holds the node shape and the anchor rule so that the first real node
has somewhere correct to go.
