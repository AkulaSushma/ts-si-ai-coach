# research/ — Research process and accounting

This folder tracks **how** material was gathered and, critically, **what was not**.

## Subfolders

| Folder         | Contents                                                                |
| -------------- | ----------------------------------------------------------------------- |
| `plans/`       | Research plans written before a harvest starts                           |
| `manifests/`   | Harvest manifests: the item-level accounting for every source            |
| `extractions/` | Structured extractions produced from sources, **before** verification    |
| `notes/`       | Working notes and dead ends                                              |

## The accounting identity (non-negotiable)

Every harvest manifest must satisfy:

```
expected = processed + inaccessible + irrelevant + duplicate + failed
```

If the identity does not balance, the harvest is `BLOCKED`, not `PARTIAL`, because
the numbers cannot be trusted at all.

A harvest may only be marked `COMPLETE` when `expected` is a **counted** figure
(not an estimate) and every non-processed item has a recorded reason.

## Rules

- Never write "processed the whole channel" or "scanned all papers". Write
  `processed 120 / expected 250` and mark it `PARTIAL`.
- `expected` must be justified. Record how the count was obtained (e.g. "channel
  video count read from the channel page on 2026-09-05").
- Extractions in `extractions/` are `UNVERIFIED` by default and must never be read
  directly by the tutor. They graduate into `knowledge/` only after passing
  `VERIFICATION_POLICY.md`.
