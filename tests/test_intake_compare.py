"""Rule-engine behavior (intake/compare.py) on synthetic evidence."""
from intake.compare import (
    NutrientComparison,
    V_ADOPT,
    V_CONFIRM,
    V_FORM_DEFECT,
    V_NO_EVIDENCE,
    V_REGION_KEEP,
    V_REPLACE,
    V_REVIEW,
    V_USDA_ONLY,
    _stats_from,
    closest_to_median,
    judge,
    screen_echoes,
)
from intake.model import (
    FORM_TOTAL_K,
    Extraction,
    Q_ANALYSED,
    Q_BORROWED,
    Q_CENSORED,
    Q_COMPILED,
    Q_ECHO,
    Q_TRACE,
    SourceValue,
)


def sv(nid, value, source="X", quality=Q_ANALYSED, food="test food", **kw):
    return SourceValue(source=source, source_food=food, nutrient_id=nid,
                       value=value, quality=quality, **kw)


def comparison(nid, fnd=None, sr=None, foreign=()):
    from intake.model import FEDIAF_BY_ID
    info = FEDIAF_BY_ID[nid]
    c = NutrientComparison(nutrient_id=nid, name=info["nutrient_name"],
                           unit=info["unit"], foundation=fnd, sr=sr,
                           foreign=list(foreign))
    judge(c)
    return c


class TestEchoScreen:
    def test_verbatim_copy_is_flagged(self):
        usda = {nid: sv(nid, v, source="SR")
                for nid, v in [(1003, 19.66), (1004, 4.12), (1087, 7.0),
                               (1089, 0.81), (1092, 242.0), (1093, 95.0)]}
        copycat = [sv(nid, u.value, source="CIQUAL", quality=Q_COMPILED,
                      food="copy food") for nid, u in usda.items()]
        honest = [sv(1003, 21.0, source="MEXT", food="honest food"),
                  sv(1004, 5.0, source="MEXT", food="honest food")]
        extraction = Extraction(sr=usda, foreign=copycat + honest)
        verdicts = screen_echoes(extraction)
        assert any("ECHO" in v for k, v in verdicts.items() if "copy food" in k)
        assert all(svv.quality == Q_ECHO for svv in extraction.foreign
                   if svv.source_food == "copy food")
        assert all(svv.quality != Q_ECHO for svv in extraction.foreign
                   if svv.source_food == "honest food")

    def test_sr_copy_flagged_even_when_foundation_differs(self):
        # audit 2026-08-18: the screener used to compare only the FIRST USDA
        # table (Foundation), letting verbatim SR copies escape
        ids = (1003, 1004, 1087, 1089, 1092, 1093)
        fnd = {nid: sv(nid, v, source="FND")
               for nid, v in zip(ids, (18.6, 7.9, 5.65, 0.6, 271.8, 62.3))}
        srt = {nid: sv(nid, v, source="SR")
               for nid, v in zip(ids, (19.66, 4.12, 7.0, 0.81, 242.0, 95.0))}
        copycat = [sv(nid, srt[nid].value, source="CIQUAL", quality=Q_COMPILED,
                      food="sr copy") for nid in ids]
        extraction = Extraction(foundation=fnd, sr=srt, foreign=copycat)
        verdicts = screen_echoes(extraction)
        assert any("ECHO" in v for k, v in verdicts.items() if "sr copy" in k)

    def test_lineage_source_labeled_never_independent(self):
        lineage = [sv(1100, 0.9, source="IodineDB", food="ndb food",
                      usda_lineage=True)]
        extraction = Extraction(foreign=lineage)
        verdicts = screen_echoes(extraction)
        assert any("USDA-affiliated" in v for v in verdicts.values())


class TestJudge:
    def test_confirm_within_20pct(self):
        c = comparison(1003, sr=sv(1003, 19.66, "SR"),
                       foreign=[sv(1003, 19.0, "MEXT")])
        assert c.verdict == V_CONFIRM
        assert c.suggestion and c.suggestion.source == "sr_legacy"

    def test_usda_only_when_no_independent(self):
        c = comparison(1180, sr=sv(1180, 53.6, "SR"),
                       foreign=[sv(1180, 65.7, "FCDB", quality=Q_BORROWED)])
        assert c.verdict == V_USDA_ONLY
        assert "no independent" in c.suggestion.comment

    def test_replace_for_assumed_zero(self):
        c = comparison(1280, sr=sv(1280, 0.0, "SR", quality=Q_BORROWED,
                                   note="deriv Z: assumed zero"),
                       foreign=[sv(1280, 0.02, "MEXT"), sv(1280, 0.03, "FCDB")])
        assert c.verdict == V_REPLACE
        assert c.suggestion.source == "literature"

    def test_region_keep_for_selenium(self):
        c = comparison(1103, sr=sv(1103, 22.9, "SR"),
                       foreign=[sv(1103, 12.4, "FCDB"), sv(1103, 14.0, "CoFID")])
        assert c.verdict == V_REGION_KEEP
        assert c.suggestion.value == 22.9

    def test_review_for_non_region_disagreement(self):
        c = comparison(1177, sr=sv(1177, 4.0, "SR"),
                       foreign=[sv(1177, 21.0, "FCDB"), sv(1177, 32.0, "AFCD")])
        assert c.verdict == V_REVIEW
        assert c.suggestion.value == 4.0    # USDA stays the starting point

    def test_form_defect_vitamin_k(self):
        c = comparison(1185, sr=sv(1185, 2.9, "SR", quality=Q_BORROWED),
                       foreign=[sv(1185, 23.0, "MEXT", form=FORM_TOTAL_K,
                                   note="menaquinone-inclusive total K"),
                                sv(1185, 36.8, "CIQUAL", quality=Q_COMPILED,
                                   form=FORM_TOTAL_K,
                                   note="K1+K2 total-K; K2=34.3")])
        assert c.verdict == V_FORM_DEFECT
        assert c.suggestion.value == 23.0

    def test_form_defect_needs_declared_form_not_note_text(self):
        # a K1-only value whose NOTE happens to contain "total" must not fire
        c = comparison(1185, sr=sv(1185, 2.9, "SR", quality=Q_BORROWED),
                       foreign=[sv(1185, 23.0, "CoFID", quality=Q_COMPILED,
                                   note="refs: Total Diet Study 1994")])
        assert c.verdict != V_FORM_DEFECT

    def test_adopt_median_anchor_when_no_usda(self):
        c = comparison(1176, foreign=[sv(1176, 3.6, "MEXT"),
                                      sv(1176, 3.7, "AFCD"),
                                      sv(1176, 3.0, "CoFID", quality=Q_COMPILED)])
        assert c.verdict == V_ADOPT
        assert c.suggestion.value == 3.6    # closest to the median

    def test_adopt_keeps_measured_zeros_in_median(self):
        # audit 2026-08-18: analysed zeros were dropped, biasing anchors up
        c = comparison(1100, foreign=[sv(1100, 0.4, "FCDB"),
                                      sv(1100, 0.0, "MEXT"),
                                      sv(1100, 2.0, "CIQUAL", quality=Q_COMPILED),
                                      sv(1100, 0.0, "AFCD"),
                                      sv(1100, 6.0, "CoFID", quality=Q_COMPILED)])
        assert c.verdict == V_ADOPT
        # median of [0, 0, 0.4, 2, 6] is 0.4 — the zeros stay in the pool
        assert c.suggestion.value == 0.4

    def test_adopt_uses_lineage_evidence_when_no_usda(self):
        c = comparison(1100, foreign=[sv(1100, 0.9, "IodineDB", usda_lineage=True)])
        assert c.verdict == V_ADOPT and c.suggestion.value == 0.9

    def test_lineage_cannot_confirm_usda(self):
        c = comparison(1100, sr=sv(1100, 1.0, "SR"),
                       foreign=[sv(1100, 1.0, "IodineDB", usda_lineage=True)])
        assert c.verdict == V_USDA_ONLY
        assert any("USDA-lineage evidence" in r for r in c.reasons)

    def test_trace_is_information_not_disagreement(self):
        # audit 2026-08-18: a trace used to manufacture a false review and
        # suppress the censored-bounds line
        c = comparison(1090, sr=sv(1090, 5.0, "SR"),
                       foreign=[sv(1090, 0.0, "CoFID", quality=Q_TRACE),
                                sv(1090, 0.1, "CIQUAL", quality=Q_CENSORED)])
        assert c.verdict == V_USDA_ONLY
        assert any("detection-limit info" in r for r in c.reasons)

    def test_no_evidence(self):
        c = comparison(1234)
        assert c.verdict == V_NO_EVIDENCE and c.suggestion is None


class TestClosestToMedian:
    def test_tie_broken_by_n_not_float_noise(self):
        # audit 2026-08-18: a two-way split was decided by the 16th decimal
        a = sv(1234, 169.0, "Spitze03", n=6)
        b = sv(1234, 33.7, "Spitze03", n=12)
        anchor, tied = closest_to_median([a, b])
        assert tied is True
        assert anchor.value == 33.7   # n=12 beats n=6, deterministically

    def test_no_tie_for_odd_count(self):
        svs = [sv(1176, 3.6, "A"), sv(1176, 3.7, "B"), sv(1176, 3.0, "C")]
        anchor, tied = closest_to_median(svs)
        assert (anchor.value, tied) == (3.6, False)

    def test_identical_values_are_agreement_not_a_split(self):
        # round-2 audit: the flag fired on every even-count set, teaching
        # operators to skim past the arbitrate sentence
        anchor, tied = closest_to_median([sv(1100, 2.0, "A"), sv(1100, 2.0, "B")])
        assert anchor.value == 2.0 and tied is False


class TestRoundTwoRegressions:
    def test_replace_not_fired_when_independents_median_is_zero(self):
        # independents mostly measuring zero AGREE with the assumed zero
        c = comparison(1280, sr=sv(1280, 0.0, "SR", quality=Q_BORROWED,
                                   note="deriv Z: assumed zero"),
                       foreign=[sv(1280, 0.0, "MEXT"), sv(1280, 0.0, "AFCD"),
                                sv(1280, 0.02, "FCDB")])
        assert c.verdict != "replace_suggest"

    def test_no_usda_overlap_is_labeled_not_independent(self):
        extraction = Extraction(foreign=[sv(1100, 2.0, "CIQUAL", food="lone food")])
        verdicts = screen_echoes(extraction)
        assert any("independence not establishable" in v for v in verdicts.values())

    def test_bounds_info_visible_on_confirm(self):
        c = comparison(1090, sr=sv(1090, 23.0, "SR"),
                       foreign=[sv(1090, 24.0, "MEXT"),
                                sv(1090, 0.1, "CIQUAL", quality=Q_CENSORED)])
        assert c.verdict == V_CONFIRM
        assert any("detection-limit" in r for r in c.reasons)

    def test_compare_all_echo_flows_into_judge(self):
        # end-to-end: a verbatim copy must not confirm USDA (round-2 audit:
        # nothing previously ran the screener and judge on the same data)
        from intake.compare import compare_all
        ids = (1003, 1004, 1087, 1089, 1092, 1093)
        srt = {nid: sv(nid, v, source="SR")
               for nid, v in zip(ids, (19.66, 4.12, 7.0, 0.81, 242.0, 95.0))}
        copycat = [sv(nid, srt[nid].value, source="CIQUAL", quality=Q_COMPILED,
                      food="copy food") for nid in ids]
        extraction = Extraction(sr=srt, foreign=copycat)
        comparisons, verdicts = compare_all(extraction)
        assert any("ECHO" in v for v in verdicts.values())
        by_id = {c.nutrient_id: c for c in comparisons}
        for nid in ids:
            assert by_id[nid].verdict == V_USDA_ONLY   # echo cannot confirm


class TestStatsFrom:
    def test_coherent_range_is_stored(self):
        s = _stats_from(sv(1004, 7.9, n=8, vmin=6.3, vmax=9.9))
        assert s == {"num_samples": 8, "min_value": 6.3, "max_value": 9.9}

    def test_censored_min_zero_range_rejected(self):
        # runbook: don't store censored ranges (min=0)
        s = _stats_from(sv(1100, 0.9, n=35, vmin=0.0, vmax=9.5))
        assert s == {"num_samples": 35}
