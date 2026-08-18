"""Review artifacts: report.md (for the operator walkthrough) and
proposed_decisions.json (the rule engine's suggestions, to be edited during
review and then fed to the writer).
"""
from __future__ import annotations

import json
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Optional

from intake.compare import NutrientComparison, V_CONFIRM, V_USDA_ONLY
from intake.model import (
    FEDIAF_BY_ID,
    Extraction,
    Q_ANALYSED,
    Q_BORROWED,
    Q_CENSORED,
    Q_COMPILED,
    Q_COMPUTED,
    Q_ECHO,
    Q_ESTIMATED,
    Q_TRACE,
    Q_UNKNOWN,
    SourceValue,
)
from intake.spec import IntakeSpec

_MARK = {
    Q_ANALYSED: "", Q_BORROWED: "†", Q_COMPILED: "°", Q_COMPUTED: "‡",
    Q_ESTIMATED: "~", Q_CENSORED: "<", Q_TRACE: " tr", Q_ECHO: "≈", Q_UNKNOWN: "?",
}
_LEGEND = ("value marks: † borrowed  ° compiled  ‡ computed  ~ estimated  "
           "< censored upper bound  tr trace  ≈ echo of USDA  ? unknown origin; "
           "(n=x) sample count")


def _cell(sv: Optional[SourceValue]) -> str:
    if sv is None:
        return "—"
    mark = _MARK.get(sv.quality, "?")
    txt = f"{sv.value:g}{mark}"
    if sv.n:
        txt += f" (n={sv.n})"
    return txt


def _foreign_cell(svs: list[SourceValue]) -> str:
    return " / ".join(_cell(sv) for sv in svs) if svs else "—"


def render_report(spec: IntakeSpec, extraction: Extraction,
                  comparisons: list[NutrientComparison],
                  echo_verdicts: dict[str, str]) -> str:
    foreign_labels = sorted({sv.source for sv in extraction.foreign})
    lines = [
        f"# Intake report: {spec.food['food_name']}",
        "",
        f"- generated: {date.today().isoformat()}  |  spec: `{spec.path}`",
        f"- Foundation FDC: {spec.foundation_fdc_id or '—'}  |  SR Legacy FDC: {spec.sr_fdc_id or '—'}",
        f"- category: {spec.food.get('category')}  |  per {spec.food.get('portion_qty')} {spec.food.get('base_unit')}",
    ]
    for note in spec.notes:
        lines.append(f"- note: {note}")
    lines += ["", "## Matched sources", "",
              "| source food | frame note | independence screen |", "|---|---|---|"]
    for label, verdict in echo_verdicts.items():
        note = extraction.source_notes.get(label, "")
        lines.append(f"| {label} | {note or '—'} | {verdict} |")
    lines += ["", f"_{_LEGEND}_", ""]

    by_category: dict[str, list[NutrientComparison]] = {}
    for comparison in comparisons:
        cat = FEDIAF_BY_ID[comparison.nutrient_id]["category"]
        by_category.setdefault(cat, []).append(comparison)

    needs_attention: list[NutrientComparison] = []
    for cat, comps in by_category.items():
        lines += [f"## {cat}", "",
                  "| nutrient | unit | FND | SR | " + " | ".join(foreign_labels)
                  + " | verdict |",
                  "|---|---|---|---|" + "---|" * (len(foreign_labels) + 1)]
        for c in comps:
            per_label = {lab: [sv for sv in c.foreign if sv.source == lab]
                         for lab in foreign_labels}
            row = [f"| {c.name} ({c.nutrient_id})", c.unit,
                   _cell(c.foundation), _cell(c.sr)]
            row += [_foreign_cell(per_label[lab]) for lab in foreign_labels]
            row.append(f"**{c.verdict}**")
            lines.append(" | ".join(row) + " |")
            if c.verdict not in (V_CONFIRM, V_USDA_ONLY):
                needs_attention.append(c)
        lines.append("")

    lines += ["## Needs attention (everything not confirm/usda_only)", ""]
    if not needs_attention:
        lines.append("None.")
    for c in needs_attention:
        lines.append(f"### {c.name} ({c.nutrient_id}) — {c.verdict}")
        for reason in c.reasons:
            lines.append(f"- {reason}")
        if c.suggestion:
            lines.append(f"- suggestion: {c.suggestion.value:g} {c.unit} "
                         f"(source `{c.suggestion.source}`)")
        for sv in c.foreign:
            lines.append(f"  - {sv.source} [{sv.quality}] {sv.value:g} — {sv.note[:120]}")
        lines.append("")

    lines += ["## Verdict summary", ""]
    counts: dict[str, int] = {}
    for c in comparisons:
        counts[c.verdict] = counts.get(c.verdict, 0) + 1
    for verdict, count in sorted(counts.items(), key=lambda kv: -kv[1]):
        lines.append(f"- {verdict}: {count}")
    return "\n".join(lines) + "\n"


def proposed_decisions(spec: IntakeSpec,
                       comparisons: list[NutrientComparison]) -> dict:
    decisions = []
    for c in comparisons:
        entry: dict = {
            "nutrient_id": c.nutrient_id, "name": c.name, "unit": c.unit,
            "verdict": c.verdict, "reasons": c.reasons,
        }
        if c.suggestion:
            entry["decision"] = {k: v for k, v in asdict(c.suggestion).items()
                                 if v is not None}
        else:
            entry["decision"] = {"value": None, "source": None,
                                 "comment": "FILL ME: no rule-engine suggestion"}
        decisions.append(entry)
    return {"slug": spec.slug, "generated": date.today().isoformat(),
            "decisions": decisions}


def write_artifacts(spec: IntakeSpec, extraction: Extraction,
                    comparisons: list[NutrientComparison],
                    echo_verdicts: dict[str, str]) -> tuple[Path, Path]:
    out_dir = spec.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "report.md"
    report_path.write_text(
        render_report(spec, extraction, comparisons, echo_verdicts))
    decisions_path = out_dir / "proposed_decisions.json"
    decisions_path.write_text(
        json.dumps(proposed_decisions(spec, comparisons), indent=2, ensure_ascii=False))
    return report_path, decisions_path
