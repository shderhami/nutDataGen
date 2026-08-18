# Intake pipeline: programmatic ingredient add + international validation

`intake/` replaces the billed AI-validation step of the interactive add flow
with the reproducible process proven by the 2026-08 23-food sweep. Every stage
reads pinned repo files and leaves a committed artifact, so any stored row
remains mechanically explainable. The AI flow (`main.py`) remains available
for foods with zero local-source coverage.

## Stages & commands

```
data/intake/<slug>.json          1. SPEC     curated matches (the manual step)
        |
python -m intake report ...      2. EXTRACT  USDA bulk + 8 adapters -> FEDIAF units
        |                        3. COMPARE  echo screen + rule engine (advisory)
data/intake/<slug>/report.md          + proposed_decisions.json
        |
   operator review               4. REVIEW   walk the report with the agent,
        |                                    edit decisions (the audit record)
python -m intake write ...       5. WRITE    gated insert (backup, 52-complete,
        --commit                             PUFA invariant, unit conversion)
```

```bash
# find candidate keys per source while curating a spec
.venv/bin/python -m intake search "chicken thigh"
.venv/bin/python -m intake search "cuisse" --source ciqual

# generate the review artifacts (no DB access)
.venv/bin/python -m intake report --spec data/intake/chicken_thigh_skinless.json

# write after review (dry-run first; --commit takes a pg_dump backup itself)
.venv/bin/python -m intake write --spec data/intake/chicken_thigh_skinless.json \
    --decisions data/intake/chicken_thigh_skinless/decisions.json
.venv/bin/python -m intake write --spec ... --decisions ... --commit
```

After a committed write, the runbook's Phases 3–5 still apply: `cv_assign.py
--food-id <id>` (dry then signed commit), `cv_intl.FOOD_MAP` extension when
FCDB carries stats for the food, pytest, memory update.

## Spec format

```json
{
  "slug": "chicken_thigh_skinless",
  "food":  { ...exact database.add_ingredient kwargs... },
  "notes": ["frame stories, price placeholders, sibling foods"],
  "sources": {
    "fcdb":   [{"key": 795,      "note": "whole-bird flesh — frame caveat"}],
    "ciqual": [{"key": 36024},   {"key": 36019, "note": "echo suspect"}],
    "mext":   [{"key": "11224"}]
  },
  "literature": [
    {"source": "Spitze03", "item": "Chicken, dark meat, raw",
     "nutrient_id": 1234, "value": 169, "unit": "mg", "n": 6,
     "note": "p6 source b: 1690±370 mg/kg wet /10"}
  ]
}
```

Adapters: `fcdb` (Danish, per-value Source decode + min/max/n), `bls` (German,
origin column), `mext` (Japanese, 3 volumes, form quirks), `ciqual` (French,
K1+K2, censored values), `afcd` (Australian, sampling-details borrow scan),
`cofid` (UK compilation, underlying refs), `iodine_db` (USDA iodine R4,
n/SD/min/max by NDB number). Keys are each table's native id; `note` is the
frame caveat printed verbatim in the report.

`literature` is the curated channel for book/paper evidence — NRC 2006
(tables 13-1/5/6/7; +1 header offset, mg/kg as-fed ÷10, fatty-carcass
frames), Spitze 2003 (mg/kg wet ÷10), Donadelli 2019, Seong 2014/2015,
Biel 2019. These are page/table lookups with food-matching judgment, so they
are curated per food rather than parsed: each entry carries its citation in
`note`, converts through the same unit layer, and flows through comparison,
verdicts and the report like any adapter value.

## What the machinery guarantees

- **Units**: everything leaves an adapter in the nutrient's FEDIAF unit
  (retinol µg→IU ×3.33, vit E mg→IU ×1.49, vit D µg→IU ×40, mass rescales,
  kJ→kcal). Unknown pairs fail loud (`intake/units.py`).
- **Independence**: per-value origin decoding (FCDB Source sheet, BLS
  Datenherkunft, AFCD sampling details, USDA derivation codes) plus the echo
  screener (≥5 values identical to USDA at <0.5% flags the whole source-food).
  Borrowed/echo/computed values never count as independent confirmation.
- **Form quirks**: MEXT thiamin HCl ×0.887; vitamin K totals composed per the
  menaquinone doctrine (K1+K2), with SR's K1-only blindness surfaced; MEXT
  `(x)` = estimated, `Tr` = trace; CIQUAL `< x` kept as censored upper bound.
- **Verdicts are advisory.** The rule engine implements runbook §2.3
  (measured-beats-derived, region rule, assumed-zero replacement, ±20%
  agreement with scale-aware epsilon) so review time goes to contested rows;
  nothing writes without operator-approved decisions.
- **Write gates**: exactly 52 FEDIAF nutrients, value+source+comment each,
  coherent ranges (no censored min=0 stats), PUFA total ≥ component sum,
  pg_dump backup before insert, orphan cleanup on failure, AI columns NULL.

## Review conventions (unchanged from the sweep)

Comments follow `Validated YYYY-MM-DD: ...` with sources+n cited; keeps get
evidence comments; store the anchor source's {n, min, max} when coherent
(cv-v7 rewards it with a same-source `literature_range` CV); region-sensitive
nutrients keep sound US means; `no_evidence` rows need an explicit operator
value with a literature citation (taurine → Spitze/Donadelli route).

## Tests

`tests/test_intake_units.py` (conversion contract),
`test_intake_usda_bulk.py` + `test_intake_sources.py` (golden pins against the
pinned datasets — a failure means a regressed adapter or a mutated data file),
`test_intake_compare.py` (rule engine), `test_intake_writer.py` (gates).
