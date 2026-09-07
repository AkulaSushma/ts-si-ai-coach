# pyq/weightage/ — Observed frequency (weightage) analysis

Historical topic-weightage analysis outputs, with the inputs used to compute them. Each
output is `T2_HISTORICAL_PYQ` — a count over real past papers, not a rule about future
papers and not an official figure.

**This folder holds no computed weightage yet.** No previous-year paper has been
acquired, so there is nothing to count. An empty folder is the correct, honest state,
not a gap.

## The expose fields every entry must show

Shape defined in `knowledge/schemas/pyq_weightage.schema.json`. Every entry exposes, so
a reader can always see what a number counts:

- `numerator` — questions in this subject / topic / question-type
- `denominator` — total classified questions in the counted paper set
- `papers_included` — which paper ids were counted
- `years_included` — which years those papers came from
- `classification_confidence` — `EXACT` / `NEAR` / `AMBIGUOUS` / `UNKNOWN`
- `basis` — always `OBSERVED`. The official figure is a different file
  (`knowledge/weightage/official_marks_structure.json`), and the two never mix.

## Rules

- **No entry without a denominator.** A numerator with no denominator, or a denominator
  of zero, is invalid and rejected by the tests.
- **Partial coverage is labelled.** A percentage over an incomplete paper set is
  recorded as `PARTIAL` with counted/intended stated — never rounded up to a claim
  about the whole set.
- **No computation without an enumerated set.** An entry may be created only after the
  paper set is enumerated and every counted paper resolves to a registered paper.
- A coaching-site copy is a legitimate count source but is recorded as
  `COACHING_COPY`, never as board-issued.
