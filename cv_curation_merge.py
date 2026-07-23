#!/usr/bin/env python3
"""Merge the keyword keep-scores (all_scored.json) with the LLM second-opinion
scores (llm_scores.json, written from the scoring workflow) into a single
per-food verdict, and surface keyword-vs-LLM DISAGREEMENTS for human review.

Two policies are computed for transparency:
  * AND-rule (conservative baseline): final KEEP iff kw_keep AND llm_keep.
  * LLM-primary + keyword HARD-veto (SHIPPED): trust the LLM's semantic call,
    but still DROP anything keyword flags with an unambiguous processing/branding
    signal. This was chosen after finding the keyword `_DISH` heuristic
    false-drops plain stew-cut meats / "Cereals, oats" / spaghetti squash, which
    the LLM correctly rescued (57 direction-B disagreements), while the LLM
    correctly caught 508 composites keyword missed (direction A).

Judge thresholds:  keyword keeps iff kw_score >= 0.60 ; llm keeps iff llm_score >= 0.50.
Foods never sent to the LLM were slam-dunk keyword keeps -> treated as llm-keep.

HARD keyword veto = any of these drop reasons is present (soft -dish / -cut /
-multi-ingredient are NOT hard, the LLM adjudicates those):
    -brand   -fastfood/babyfood/restaurant   -processed-meat
    -imitation   -plant-analog

Writes:
  data/cv_curation/merged/<class>.csv        — every food, both scores, both verdicts
  data/cv_curation/merged/disagreements.csv  — the conflicts, for eyeballing
  data/cv_curation/merged/final_keep_ids.json — {class: [source_food_id,...]} SHIPPED keeps
Prints a per-category summary + the disagreement counts.

Usage:  python cv_curation_merge.py
"""
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

import cv_config

DIR = Path(__file__).parent / "data" / "cv_curation"
OUT = DIR / "merged"

KW_KEEP = 0.60
LLM_KEEP = 0.50

HARD_VETO = ("-brand", "-fastfood/babyfood/restaurant", "-processed-meat",
             "-imitation", "-plant-analog")


def main() -> None:
    allrows = json.loads((DIR / "all_scored.json").read_text())
    llm = json.loads((DIR / "llm_scores.json").read_text())
    llm_by_id = {r["id"]: r for r in llm}

    OUT.mkdir(parents=True, exist_ok=True)
    by_class: dict[str, list[dict]] = defaultdict(list)
    disagreements: list[dict] = []

    for row in allrows:
        ic = row["ingredient_class"]
        fid = f"{ic}:{row['source_food_id']}"
        kw = float(row["score"])
        kw_keep = kw >= KW_KEEP
        lr = llm_by_id.get(fid)
        # foods that never went to the LLM were slam-dunk keeps -> treat as llm keep
        if lr is None:
            llm_score, llm_keep, llm_reason, wrong = 1.0, True, "slam-dunk keep (not sent to LLM)", ""
        else:
            llm_score = float(lr.get("keep_score", 0.0))
            llm_keep = bool(lr.get("keep", llm_score >= LLM_KEEP))
            llm_reason = lr.get("reason", "")
            wrong = lr.get("wrong_class", "") or ""
        kw_reasons = row.get("reasons", "")
        hard_veto = any(v in kw_reasons for v in HARD_VETO)
        and_keep = kw_keep and llm_keep                      # conservative baseline
        final_keep = llm_keep and not hard_veto              # SHIPPED policy
        disagree = kw_keep != llm_keep
        rec = {
            "final": "KEEP" if final_keep else "DROP",
            "and_rule": "KEEP" if and_keep else "DROP",
            "disagree": "Y" if disagree else "",
            "hard_veto": "Y" if hard_veto else "",
            "kw_score": f"{kw:.2f}", "kw_keep": "Y" if kw_keep else "",
            "llm_score": f"{llm_score:.2f}", "llm_keep": "Y" if llm_keep else "",
            "prep": row.get("prep", ""), "n_obs": row.get("n_obs", ""),
            "source_dataset": row.get("source_dataset", ""),
            "source_food_id": row.get("source_food_id", ""),
            "description": row.get("description", ""),
            "kw_reasons": kw_reasons,
            "llm_reason": llm_reason, "wrong_class": wrong,
        }
        by_class[ic].append(rec)
        if disagree:
            disagreements.append({"ingredient_class": ic, **rec})

    fields = ["final", "and_rule", "disagree", "hard_veto", "kw_score", "kw_keep",
              "llm_score", "llm_keep", "prep", "n_obs", "source_dataset",
              "source_food_id", "description", "kw_reasons", "llm_reason", "wrong_class"]

    print("=" * 96)
    print("MERGED CURATION   SHIPPED = LLM-keep(>=%.2f) AND no keyword hard-veto  |  "
          "AND-rule = kw&llm both keep" % LLM_KEEP)
    print("=" * 96)
    final_ids: dict[str, list] = {}
    tot_final = tot_and = 0
    for ic in sorted(by_class):
        rows = sorted(by_class[ic], key=lambda r: (r["final"] == "KEEP", float(r["llm_score"])))
        with open(OUT / f"{ic}.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader(); w.writerows(rows)
        fc = Counter(r["final"] for r in rows)
        ac = Counter(r["and_rule"] for r in rows)
        dis = sum(1 for r in rows if r["disagree"])
        final_ids[ic] = [r["source_food_id"] for r in rows if r["final"] == "KEEP"]
        tot_final += fc["KEEP"]; tot_and += ac["KEEP"]
        print(f"### {ic.upper():8s} {len(rows):4d} foods  SHIP-KEEP={fc['KEEP']:4d} "
              f"(AND-rule={ac['KEEP']:4d})  DROP={fc['DROP']:4d}  disagree={dis:3d}  -> merged/{ic}.csv")

    # Stamp with the pipeline version so cv_extract can warn if the keep-set is stale
    # relative to a changed classifier/pipeline (keys are (class, food_id)).
    (OUT / "final_keep_ids.json").write_text(json.dumps(
        {"pipeline_version": cv_config.PIPELINE_VERSION, "keep": final_ids}))
    with open(OUT / "disagreements.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["ingredient_class"] + fields)
        w.writeheader()
        w.writerows(sorted(disagreements, key=lambda r: (r["ingredient_class"], r["llm_score"])))
    print(f"\nSHIPPED keeps: {tot_final}   (AND-rule keeps: {tot_and})")
    print(f"Total disagreements (keyword vs LLM): {len(disagreements)}  -> merged/disagreements.csv")
    print("Final keep id-set -> merged/final_keep_ids.json")


if __name__ == "__main__":
    main()
