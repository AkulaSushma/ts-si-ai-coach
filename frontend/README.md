# frontend/ — User interface (not yet built)

Status: **empty by design.** Bootstrap deliberately built no UI.

## Intent

A local web interface served to the browser on this machine. The framework choice is
deferred: it is open decision `D-0003` in `DECISIONS.md` and will be settled when the
first UI spec is written, not before.

## Rules

- Nothing is written here until a spec in `specs/features/` describing the screen is
  marked `APPROVED`.
- The UI is a client of the backend API. It must not contain exam knowledge, methods,
  or answer keys — those live in `knowledge/` and are served by the backend.
- Any figure shown to the student that came from an incomplete dataset must be
  labelled as partial in the interface itself. Silently rounding a `PARTIAL` result
  into a confident-looking number defeats the purpose of the whole project.
