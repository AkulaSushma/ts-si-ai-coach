# Research plan — official TGPRB SI 2026 source acquisition

**Plan id:** `PLAN-OFF-001` · **Written:** 2026-09-06 · **Session:** 003
**Spec:** `specs/features/official-knowledge-foundation.md` (`SPEC-OFF-001`)
**Manifest:** `research/manifests/official/2026-09-06-tgprb-si-2026.json`

## Objective

Obtain the controlling official document set for Telangana Police Recruitment 2026,
SCT SI (Civil) and equivalent posts, and establish the 25 facts in
`knowledge/official/required_facts.json` from it — each with page, section and a
verbatim quote.

## Authority boundary

One rule decides every judgement in this plan: **only a TGPRB / TSLPRB document is
authority for an official fact.** A search engine may point at a document. A coaching
site may host a copy. Neither is the document. A copy hosted elsewhere cannot be hashed
against the publisher and may be edited, truncated, or superseded without notice.

## Steps

| # | Step | Status |
| - | ---- | ------ |
| 1 | Enumerate candidate official documents and their URLs | `COMPLETE` — 7 enumerated, recorded in the manifest |
| 2 | Retrieve each document | `BLOCKED` — egress allowlist refuses every official host |
| 3 | Store under `source_material/official/`, hash, ledger | `BLOCKED` — depends on step 2 |
| 4 | Resolve the official-domain conflict `CONF-OFF-001` | `BLOCKED` — needs both hosts loadable |
| 5 | Determine which document is controlling where two conflict | `BLOCKED` — depends on step 3 |
| 6 | Extract the 25 facts with page, section, verbatim quote | `BLOCKED` — depends on step 3 |
| 7 | Map the official syllabus, subject → topic → subtopic, in document order | `BLOCKED` — depends on step 3 |
| 8 | Record official marks structure; leave historical and estimated weightage empty | `BLOCKED` — depends on step 6 |

Steps 1 and the whole container (schemas, registries, separation, tests) are done.
Steps 2 onward need one thing that is not code.

## Enumeration method, and what it does not prove

A web search restricted to the official domain returned four URLs on that domain, and
two further documents were inferred by analogy with sibling file names. `expected = 7`
is therefore a **counted enumeration of candidates**, not a count read from the board's
own index page. The real total is unknown and may be larger, which is why the manifest
says so explicitly rather than implying the set is complete.

## Conflicts to resolve before any fact is trusted

| id | Conflict | Why it matters |
| -- | -------- | -------------- |
| `CONF-OFF-001` | `tgprb.in` versus `tslprb.in` as the controlling official domain | Every provenance record cites a URL; citing a superseded domain makes the chain unverifiable |
| — | A supplementary notification dated after the main notification exists | A later document does not automatically win. Which is controlling must be read, not assumed |

## Deliberately not done

- No fetch by any route other than the tool that reported the block. The restriction is
  a rule about this environment, not an obstacle to be routed around.
- No use of a coaching-site mirror as a substitute for the official file.
- No syllabus, mark, duration, age limit, vacancy count or physical standard written
  from model recall anywhere in this repository.

## Definition of done

`PLAN-OFF-001` is `COMPLETE` when every `OFF-F##` record has status `VERIFIED` with a
resolvable retrieved document and a verbatim quote, the syllabus is mapped from that
document, `CONF-OFF-001` is resolved, and the manifest's identity balances with
`processed` greater than zero. Anything less is `PARTIAL` or `BLOCKED`.
