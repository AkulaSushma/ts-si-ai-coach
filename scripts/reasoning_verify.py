"""Deterministic, independent checks for candidate reasoning/arithmetic rules.

This module never reads a source claim and never marks anything VERIFIED. It
recomputes a rule from first principles so that an assessment recorded in the
evidence journal is backed by an actual computation instead of a restated
expert claim. Correctness is the only dimension it can support; speed,
applicability, recognition and retention require separate evidence.
"""
from __future__ import annotations

import json
from pathlib import Path


def digits(value):
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError('Expected a non-negative integer')
    return [int(c) for c in str(value)]


def digit_product_scaled(value, factor):
    """Apply 'multiply the digits together, then multiply by factor'.

    For 86 with factor 6: 8*6 = 48 (digit product), then 48*6 = 288.
    """
    product = 1
    for d in digits(value):
        product *= d
    return {'digit_product': product, 'result': product * factor}


def check_analogy(pairs, factor):
    """Recompute each (input, expected_output) pair under the candidate rule."""
    results = []
    for value, expected in pairs:
        computed = digit_product_scaled(value, factor)
        results.append({'input': value, 'expected_output': expected,
                        'computed_output': computed['result'],
                        'stages': computed, 'matches': computed['result'] == expected})
    return results


def failure_boundary(value, factor):
    """Report whether the rule degenerates for a given input.

    Any input containing a zero digit collapses to 0, so the rule cannot
    produce a non-zero analogue. This is a real applicability limit of the
    candidate rule, derived here rather than taken from the source.
    """
    computed = digit_product_scaled(value, factor)
    return {'input': value, 'result': computed['result'],
            'degenerate': computed['result'] == 0,
            'reason': 'a zero digit makes the digit product zero'
                      if 0 in digits(value) else 'no zero digit'}


def alternative_rule_count(observed_pair, limit=99):
    """Count simple alternative rules consistent with a single observed pair.

    Demonstrates that one worked example does not determine a unique rule, so a
    single matching PYQ can never establish a universal method.
    """
    value, expected = observed_pair
    matches = []
    for factor in range(1, limit + 1):
        product = 1
        for d in digits(value):
            product *= d
        if product * factor * factor == expected:
            matches.append({'rule': 'digit_product * f * f', 'f': factor})
        elif product * factor == expected:
            matches.append({'rule': 'digit_product * f', 'f': factor})
        if value * factor == expected:
            matches.append({'rule': 'value * f', 'f': factor})
    return matches


def write_report(path, payload):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=1, sort_keys=True) + '\n',
                      encoding='utf-8')
    return target
