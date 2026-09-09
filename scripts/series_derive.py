"""SPEC-INT-012: deterministic derivation for observed number-code / series tables.

A coaching image can show a code table without stating the rule. The rule is
then a MODEL hypothesis until an actual procedure reproduces every observed
pair. This module searches a DECLARED, finite rule space and reports what it
actually found. It never invents a rule that does not reproduce the data, and
it reports FAIL rather than choosing the closest match.

It also reports how many distinct rules in the space fit the data, because a
rule that is not uniquely determined cannot be presented as "the" trick.
"""
from __future__ import annotations

from fractions import Fraction

MAX_POLY_DEGREE = 4
MAX_STEP_DEGREE = 3
COEFF_RANGE = range(-12, 13)
EXPONENTS = (1, 2, 3)


def differences(values):
    return [values[i + 1] - values[i] for i in range(len(values) - 1)]


def difference_table(values, depth=5):
    """Observed finite-difference table. Pure observation, no interpretation."""
    rows, current = [], list(values)
    for _ in range(depth):
        if len(current) < 2:
            break
        current = differences(current)
        rows.append(list(current))
    return rows


def polynomial_degree(values):
    """Smallest exact polynomial degree in n, or None within MAX_POLY_DEGREE.

    A sequence is a degree-d polynomial in n (for equally spaced n) exactly when
    its (d+1)-th finite differences are all zero and enough terms exist.
    """
    current = list(values)
    for degree in range(0, MAX_POLY_DEGREE + 1):
        if len(current) >= 2 and all(x == 0 for x in current):
            return degree - 1 if degree else 0
        if len(current) < 2:
            return None
        current = differences(current)
    return None if any(x != 0 for x in current) else MAX_POLY_DEGREE


def fits_polynomial(values):
    """True with the degree when a polynomial of degree <= MAX_POLY_DEGREE fits.

    Requires at least degree+2 terms so the fit is constrained, not fitted.
    """
    table = difference_table(values, depth=MAX_POLY_DEGREE + 1)
    for degree, row in enumerate(table, start=1):
        if row and all(x == 0 for x in row):
            if len(values) >= degree + 2:
                return True, degree - 1
            return False, degree - 1
    return False, None


def closed_form_candidates(pairs):
    """Rules of the form a*n**p + b*n + c over the declared coefficient range."""
    matches = []
    tested = 0
    for p in EXPONENTS:
        for a in COEFF_RANGE:
            if a == 0:
                continue
            for b in COEFF_RANGE:
                for c in COEFF_RANGE:
                    tested += 1
                    if all(a * (n ** p) + b * n + c == v for n, v in pairs):
                        matches.append({
                            'family': 'closed_form',
                            'expression': f'{a}*n**{p} + {b}*n + {c}',
                        })
    return matches, tested


def step_rule_candidates(pairs):
    """Rules a(n) = a(n-1) + (a*n**p + b*n + c) over the declared range."""
    matches = []
    tested = 0
    ns = [n for n, _ in pairs]
    vs = [v for _, v in pairs]
    if ns != list(range(ns[0], ns[0] + len(ns))):
        return matches, tested  # steps only meaningful for consecutive n
    for p in range(1, MAX_STEP_DEGREE + 1):
        for a in COEFF_RANGE:
            if a == 0:
                continue
            for b in COEFF_RANGE:
                for c in COEFF_RANGE:
                    tested += 1
                    ok = True
                    for i in range(1, len(vs)):
                        n = ns[i]
                        if vs[i] - vs[i - 1] != a * (n ** p) + b * n + c:
                            ok = False
                            break
                    if ok:
                        matches.append({
                            'family': 'step_rule',
                            'expression': f'a(n) = a(n-1) + {a}*n**{p} + {b}*n + {c}',
                        })
    return matches, tested


def ratio_observations(pairs):
    """Exact ratios v/n as fractions. Observation, not a rule."""
    return [
        {'n': n, 'value': v, 'ratio': str(Fraction(v, n)) if n else None}
        for n, v in pairs
    ]


def derive(pairs):
    """Search the declared space and report the actual outcome.

    result is PASS only when at least one rule reproduces every observed pair.
    unique is True only when exactly one rule in the space does so.
    """
    if len(pairs) < 4:
        raise ValueError('Refusing to derive a rule from fewer than four pairs')
    if any(not isinstance(n, int) or not isinstance(v, int) for n, v in pairs):
        raise ValueError('Pairs must be integers as observed')

    values = [v for _, v in pairs]
    poly_ok, poly_degree = fits_polynomial(values)
    closed, closed_tested = closed_form_candidates(pairs)
    stepped, step_tested = step_rule_candidates(pairs)
    matches = closed + stepped

    return {
        'pairs': [list(p) for p in pairs],
        'observed_difference_table': difference_table(values),
        'observed_ratios': ratio_observations(pairs),
        'polynomial_fit': {'fits': poly_ok, 'degree': poly_degree},
        'search_space': {
            'closed_form_rules_tested': closed_tested,
            'step_rules_tested': step_tested,
            'coefficient_range': [min(COEFF_RANGE), max(COEFF_RANGE)],
            'exponents': list(EXPONENTS),
            'max_step_degree': MAX_STEP_DEGREE,
        },
        'matching_rules': matches,
        'unique': len(matches) == 1,
        'result': 'PASS' if matches else 'FAIL',
        'interpretation_limits': [
            'The searched space is finite and declared; absence of a match does '
            'not prove that no rule exists.',
            'A match reproduces the observed pairs only; it does not establish '
            'that the source taught this rule.',
        ],
    }


def deterministic_checks(pairs, expression_eval):
    """Per-pair checks for evidence_store.assess.

    expression_eval(n) must be a pure function of n. Boundary case is the last
    observed pair, which is where a wrong rule usually diverges.
    """
    checks = []
    for index, (n, v) in enumerate(pairs):
        checks.append({
            'kind': 'boundary_case' if index == len(pairs) - 1 else 'valid_case',
            'procedure': f'evaluate candidate rule at n={n}',
            'observed': expression_eval(n),
            'expected': v,
            'passed': expression_eval(n) == v,
        })
    return checks
