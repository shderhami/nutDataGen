#!/usr/bin/env python3
"""Score every source food assigned to a category with a KEEP-confidence (0..1)
so the pools contain only clean single-ingredient whole foods.

Score is transparent/rule-based (reasons emitted). Two axes:
  * keep_score : confidence the food is a clean single-ingredient <category> food.
  * prep_state : raw | cooked | other (proteins prefer raw).

Writes per-category review CSVs to data/cv_curation/<class>.csv (sorted by score;
edit the `decision` column to override) and prints a terminal summary.

Usage:  python cv_curation.py
"""
from __future__ import annotations

import csv
import os
import re
from collections import Counter
from pathlib import Path

import psycopg2

OUT_DIR = Path(__file__).parent / "data" / "cv_curation"

# ── strong DROP markers (composite / branded / prepared / processed) ─────────
# NOTE: tokens tuned to avoid false-positives on legitimate cuts — no bare
# "plate"/"tender"/"medallion"/"loaf" (plate steak, mock/shoulder tender), and
# "chili con" not "chili" (chili peppers are a real plant).
_DISH = re.compile(r"\b(sandwich|burger|cheeseburger|hamburger|burrito|\btaco\b|pizza|submarine|\bsub\b|wrap|biscuit|croissan\w*|bagel|muffin|casserole|lasagna|ravioli|macaroni|spaghetti|noodle|pot pie|soup|stew|chili con|gravy|gumbo|chowder|\bsauce\b|salsa|\bdip\b|dressing|marinade|cereal|granola|pastry|cheesecake|cookie|brownie|\bpie\b|dessert|pudding|custard|ice cream|sherbet|novelties|snack|potato chips|cracker|pretzel|\bdinner\b|entree|entrée|nuggets?|chicken tenders|popper|fritter|croquette|meatball|meatloaf|quiche|omelet|scrambled|souffle)", re.I)
_PROCMEAT = re.compile(r"\b(luncheon|bologna|salami|pepperoni|frankfurter|\bfrank\b|hot dog|sausage|bratwurst|bacon|chorizo|pastrami|prosciutto|jerky|spam|potted|deviled|corned|headcheese|liverwurst|braunschweiger|pâté|pate|kielbasa|mortadella|capicola)", re.I)
_CONTEXT = re.compile(r"\b(fast\s?foods?|babyfood|baby food|restaurant|school lunch|commodity|infant formula|formula,)", re.I)
_BRAND = re.compile(r"(MCDONALD|BURGER KING|WENDY|SUBWAY|\bKFC\b|TACO BELL|DENNY|JIMMY DEAN|GERBER|KELLOGG|GENERAL MILLS|KRAFT|NESTLE|CAMPBELL|SMART BALANCE|OSCAR MAYER|HORMEL|TYSON|PERDUE|DIGIORNO|STOUFFER|BANQUET|HEALTHY CHOICE|LEAN CUISINE|MORNINGSTAR|\bBOCA\b|APPLEGATE|BUTTERBALL|HEBREW NATIONAL|LOUIS RICH|POPEYES|CHICK-FIL-A|ARBY|SONIC|CARL|HARDEE|LITTLE CAESARS|DOMINO|PIZZA HUT|PAPA JOHN|STARBUCKS)")
_IMITATION = re.compile(r"\b(imitation|substitute|non-?dairy|meatless|vegetarian|vegan|analog|alternative)\b", re.I)
_PLANT_ANALOG = re.compile(r"\b(almond|soy|oat|coconut|cashew|hemp|rice|pea|hazelnut|macadamia)\b.*\b(milk|cream|butter|cheese|yogurt)\b", re.I)
_WITH_INGR = re.compile(r"\bwith\b.*\b(cheese|sauce|gravy|egg|bacon|sausage|vegetable|rice|bean|noodle|cream|dressing|ham)\b", re.I)
# Additive / preservation processing (smoked/salted/sugared/cured/brined/…). A soft
# drop so such a food can never be a slam-dunk keyword keep that bypasses the LLM.
# 'dried' is deliberately EXCLUDED here — it is the native form for plant seeds/grains.
_PRESERVED = re.compile(r"\b(smoked|salted|sugared|brined|cured|corned|pickled|marinated|fermented|jerky|lox|kippered)\b", re.I)

# ── clean single-ingredient KEEP signals ────────────────────────────────────
_RAW = re.compile(r"\braw\b", re.I)
_COOK = re.compile(r"\b(cooked|roasted|braised|boiled|grilled|stewed|pan-?fried|fried|baked|broiled|simmered|poached|steamed|microwaved)\b", re.I)
_CUT = re.compile(r"\b(thigh|breast|drumstick|wing|\bleg\b|meat only|round|loin|chuck|\brib\b|flank|sirloin|shank|tenderloin|skirt|fillet|filet|liver|heart|kidney|gizzard|spleen|tongue|tripe|yolk|white,|whole,)\b", re.I)


def score_food(desc: str, ingredient_class: str) -> tuple[float, list[str]]:
    d = desc or ""
    s, reasons = 0.65, []
    if _RAW.search(d):
        s += 0.25; reasons.append("+raw")
    if _CUT.search(d):
        s += 0.10; reasons.append("+cut/part")
    if _CONTEXT.search(d):
        s -= 0.65; reasons.append("-fastfood/babyfood/restaurant")
    if _BRAND.search(d):
        s -= 0.60; reasons.append("-brand")
    if _DISH.search(d):
        s -= 0.60; reasons.append("-dish/prepared")
    if _PROCMEAT.search(d) and ingredient_class in ("muscle", "organ", "fish"):
        s -= 0.50; reasons.append("-processed-meat")
    if _IMITATION.search(d):
        s -= 0.60; reasons.append("-imitation")
    if _PLANT_ANALOG.search(d) and ingredient_class in ("dairy", "fat_oil"):
        s -= 0.70; reasons.append("-plant-analog(wrong-class)")
    if _WITH_INGR.search(d):
        s -= 0.25; reasons.append("-multi-ingredient")
    if _PRESERVED.search(d):
        s -= 0.55; reasons.append("-preserved/additive")
    return max(0.0, min(1.0, s)), reasons


KEEP_HI, DROP_LO = 0.60, 0.30


def decision(score: float) -> str:
    return "keep" if score >= KEEP_HI else ("drop" if score < DROP_LO else "review")


def prep(desc: str) -> str:
    d = desc or ""
    if _COOK.search(d):
        return "cooked"
    if _RAW.search(d):
        return "raw"
    return "other"


def main() -> None:
    c = psycopg2.connect(host=os.environ["DATABASE_HOST"], port=os.environ["DATABASE_PORT"],
                         dbname=os.environ["DATABASE_NAME"], user=os.environ["DATABASE_USER"],
                         password=os.environ["DATABASE_PASSWORD"])
    cur = c.cursor()
    cur.execute("""SELECT ingredient_class, source_dataset, source_food_id,
                          max(source_food_desc), count(*)
                   FROM cv_observations GROUP BY 1,2,3""")
    foods = cur.fetchall()
    c.close()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    by_class: dict[str, list] = {}
    for ic, ds, sid, desc, nobs in foods:
        sc, reasons = score_food(desc, ic)
        by_class.setdefault(ic, []).append({
            "score": round(sc, 2), "decision": decision(sc), "prep": prep(desc),
            "n_obs": nobs, "source_dataset": ds, "source_food_id": sid,
            "description": desc, "reasons": " ".join(reasons)})

    print("=" * 88)
    print(f"CURATION SCORING  (keep>={KEEP_HI}  review  drop<{DROP_LO})   proteins prefer prep=raw")
    print("=" * 88)
    for ic in sorted(by_class):
        rows = sorted(by_class[ic], key=lambda r: r["score"])
        dcount = Counter(r["decision"] for r in rows)
        praw = sum(1 for r in rows if r["prep"] == "raw")
        with open(OUT_DIR / f"{ic}.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["score", "decision", "prep", "n_obs",
                                              "source_dataset", "source_food_id", "description", "reasons"])
            w.writeheader(); w.writerows(rows)
        print(f"\n### {ic.upper()}  ({len(rows)} foods)  keep={dcount['keep']} review={dcount['review']} "
              f"drop={dcount['drop']}  raw={praw}  -> data/cv_curation/{ic}.csv")
        drops = [r for r in rows if r["decision"] == "drop"]
        revs = [r for r in rows if r["decision"] == "review"]
        print(f"  -- sample DROP ({len(drops)}): ")
        for r in drops[:6]:
            print(f"     {r['score']:.2f} [{r['reasons']}] {r['description'][:52]}")
        print(f"  -- REVIEW band ({len(revs)}): ")
        for r in revs[:8]:
            print(f"     {r['score']:.2f} [{r['reasons']}] {r['description'][:52]}")

    # Full scored dump (all foods) + the subset that needs an LLM second opinion:
    # everything that is not a slam-dunk clean keep (score>=0.8, no negative reason).
    import json
    allrows, needs = [], []
    for ic in by_class:
        for r in by_class[ic]:
            row = {**r, "ingredient_class": ic}
            allrows.append(row)
            slam_keep = row["score"] >= 0.8 and "-" not in row["reasons"]
            if not slam_keep:
                needs.append({"id": f"{ic}:{row['source_food_id']}",
                              "ingredient_class": ic, "description": row["description"]})
    (OUT_DIR / "all_scored.json").write_text(json.dumps(allrows))
    (OUT_DIR / "needs_llm.json").write_text(json.dumps(needs))
    print(f"\nWrote {len(allrows)} scored foods; {len(needs)} need an LLM second opinion "
          f"-> data/cv_curation/{{all_scored,needs_llm}}.json")


if __name__ == "__main__":
    main()
