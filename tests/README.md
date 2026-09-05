# tests/ — Automated checks

Tests are the only evidence this project accepts for "it works".

## Subfolders

| Folder       | Contents                                                          |
| ------------ | ----------------------------------------------------------------- |
| `bootstrap/` | Structural checks on the repository itself (present since bootstrap) |

Feature test folders are added alongside the features they cover.

## Running the tests

From the project folder:

```
python -m unittest discover -s tests -v
```

No test framework needs to be installed. The suite uses only the Python standard
library, on purpose — a test suite that cannot run until you install something is a
test suite that does not get run.

## Rules

- **Never weaken, skip, or delete a test to make the project look finished.** If a
  test fails, either the code is wrong or the test encodes a wrong expectation.
  Decide which, fix that, and record the decision. Deleting the test is not an option.
- A failing test means the task is `PARTIAL` or `BLOCKED`, never `COMPLETE`.
- Every mathematical method or shortcut added to `knowledge/methods/` gets a
  deterministic test that includes inputs where the shortcut is expected to **fail**.
  A shortcut is only understood once its failure boundary is tested.
- Test output is evidence: paste the real output into the completion report in
  `docs/reports/`. Do not paraphrase it.
