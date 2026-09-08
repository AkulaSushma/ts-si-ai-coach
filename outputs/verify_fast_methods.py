"""Retired unsafe verifier. Historical JSON is deliberately not rewritten.

The exact old implementation remains in Git at commit
ce938a916b1042dcba90707af66f14a4f7a59db9 (this same path).
See SPEC-INT-010 and scripts/evidence_store.py for revision-bound assessment
eligibility. Legacy VERIFIED labels are not sufficient evidence of eligibility.
"""
import sys


def main():
    print('BLOCKED: legacy verifier disabled because it promoted FAIL results and '
          'overwrote history. No records changed. Use independently produced, '
          'revision-bound evidence; see scripts/evidence_store.py.', file=sys.stderr)
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
