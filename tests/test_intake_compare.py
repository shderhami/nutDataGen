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
    judge,
    screen_echoes,
)
from intake.model import (
    Extraction,
    Q_ANALYSED,
    Q_BORROWED,
    Q_COMPILED,
    Q_ECHO,
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
                       foreign=[sv(1185, 23.0, "MEXT",
                                   note="menaquinone-inclusive total K"),
                                sv(1185, 36.8, "CIQUAL", quality=Q_COMPILED,
                                   note="K1+K2 total-K; K2=34.3")])
        assert c.verdict == V_FORM_DEFECT
        assert c.suggestion.value == 23.0

    def test_adopt_median_anchor_when_no_usda(self):
        c = comparison(1176, foreign=[sv(1176, 3.6, "MEXT"),
                                      sv(1176, 3.7, "AFCD"),
                                      sv(1176, 3.0, "CoFID", quality=Q_COMPILED)])
        assert c.verdict == V_ADOPT
        assert c.suggestion.value == 3.6    # closest to the median

    def test_no_evidence(self):
        c = comparison(1234)
        assert c.verdict == V_NO_EVIDENCE and c.suggestion is None


class TestStatsFrom:
    def test_coherent_range_is_stored(self):
        s = _stats_from(sv(1004, 7.9, n=8, vmin=6.3, vmax=9.9))
        assert s == {"num_samples": 8, "min_value": 6.3, "max_value": 9.9}

    def test_censored_min_zero_range_rejected(self):
        # runbook: don't store censored ranges (min=0)
        s = _stats_from(sv(1100, 0.9, n=35, vmin=0.0, vmax=9.5))
        assert s == {"num_samples": 35}
