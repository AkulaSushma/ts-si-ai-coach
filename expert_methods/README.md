# expert_methods/ — Educator- and coaching-derived claims (unverified by default)

This folder is the staging area for techniques learned from teachers, coaching
institutes, YouTube channels, and books. Everything here is provenance tier
`T3_EXPERT`.

## Subfolders

| Folder       | Contents                                                                  |
| ------------ | ------------------------------------------------------------------------- |
| `claims/`    | One record per claimed method or shortcut, as the educator stated it        |
| `educators/` | One profile per educator/channel/institute, with a stable source ID        |

## Why this is separate from `knowledge/methods/`

`expert_methods/claims/` is what somebody **said**. `knowledge/methods/` is what the
project has **verified**. Keeping them apart is what makes the provenance rules
enforceable rather than decorative.

A claim graduates into `knowledge/methods/` only after:

1. its `validity_conditions` are stated explicitly, and
2. its arithmetic has been checked by deterministic calculation over a range of
   inputs, including edge cases where the shortcut should fail, and
3. its `when_not_to_use` is populated — a shortcut with no stated failure mode has
   not been understood yet.

## Rules

- Attribute honestly. Record the educator, the video/page, and a timestamp or page
  reference so the claim can be re-checked.
- Never merge two educators' methods into one record and present it as a single
  method. Conflicting methods are recorded separately and reconciled in
  `verification/disputes/`.
- A fast trick that is wrong outside a narrow range is a **trap**, not a method.
  Record it in `knowledge/traps/` as well.
