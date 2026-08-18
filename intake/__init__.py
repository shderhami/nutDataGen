"""Programmatic ingredient intake: USDA bulk + international cross-validation.

Replaces the billed AI-validation step of the interactive add flow with the
reproducible process proven by the 2026-08 23-food validation sweep:

    spec (data/intake/<slug>.json)        curated per ingredient — food identity
        |                                  + the matched entry in each source
    extract                                USDA pinned bulk + 8 source adapters,
        |                                  unit-normalized to FEDIAF units
    compare + rule engine                  echo screening, sweep decision rules;
        |                                  verdicts are ADVISORY
    report.md + proposed_decisions.json    reviewed nutrient-by-nutrient with
        |                                  the operator (in chat)
    write --commit                         gated DB insert (52-completeness,
                                           PUFA invariant, backup first)

Every stage reads pinned repo files and writes an artifact, so a stored row
remains explainable years later. See Docs/intake_pipeline.md.
"""
