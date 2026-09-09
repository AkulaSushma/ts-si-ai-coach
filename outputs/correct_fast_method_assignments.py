"""RETIRED: unsafe in-place mutator for pyq/intelligence/questions.json.

The original script rewrote historical intelligence records in place from a
hardcoded mapping, with no evidence gate, no backup and no history retention.
It is the same failure class as the retired outputs/verify_fast_methods.py.

The original source remains available in Git history. This entry point now
refuses to run and changes nothing. Method state must be projected from
revision-bound evidence via scripts/evidence_store.fast_method_state.
"""

MESSAGE = (
    'BLOCKED: legacy assignment script disabled because it overwrote historical '
    'intelligence records from a hardcoded mapping with no evidence gate. '
    'No records changed. Use revision-bound evidence; see scripts/evidence_store.py '
    'and scripts/run_reasoning_pilot.py.'
)


def main():
    print(MESSAGE)
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
