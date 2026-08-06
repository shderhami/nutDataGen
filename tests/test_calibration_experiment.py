"""
Tests for the design-of-experiment layer (calibration_experiment.py).

The statistics here decide whether real money gets spent on further arms, so
the pieces that must be right are: the pre-checks correctly identify a
degenerate signal, McNemar detects a real paired difference and stays silent
on noise, the factorial decomposition is arithmetically correct, and a small
pilot spreads across foods instead of truncating onto one.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import ai_validation
import calibration_experiment as ce
import calibration_harness as ch
import cv_config

DATASETS_PRESENT = (cv_config.FDC_SRL_DIR / "food_nutrient.csv").exists()


def scored(
    food: str, nutrient_id: int, correct: bool, confidence: str = "high"
) -> ch.ScoredCase:
    return ch.ScoredCase(
        nutrient_id=nutrient_id, description=food, sr_value=10.0,
        foundation_value=10.0 if correct else 20.0, predicted_value=10.0,
        recommendation="sr_legacy", confidence=confidence, correct=correct,
        relative_error=0.0 if correct else 1.0,
    )


def labeled(food: str, nutrient_id: int) -> ch.LabeledCase:
    return ch.LabeledCase(
        fdc_id_sr=1, fdc_id_foundation=2, description=food,
        nutrient_id=nutrient_id, sr_value=10.0, foundation_value=12.0, unit="g",
        protein_species="chicken", cooking_method="raw", category="Muscle Meat",
    )


class TestArmDefinitions:
    """The four arms are a 2x2 factorial, not four ad-hoc configurations."""

    def test_arms_form_a_two_by_two(self):
        cells = {(a.samples > 1, a.web_search) for a in ce.ARMS.values()}
        assert cells == {(False, False), (True, False), (False, True), (True, True)}

    def test_none_arm_is_current_defaults(self):
        import config

        assert ce.ARMS["none"].samples == config.AI_SELF_CONSISTENCY_SAMPLES
        assert ce.ARMS["none"].web_search == config.AI_WEB_SEARCH_ENABLED

    def test_cost_ordering_matches_configuration(self):
        costs = {n: a.cost_per_case() for n, a in ce.ARMS.items()}
        assert costs["none"] < costs["selfcons"] < costs["both"]
        assert costs["none"] < costs["search"] < costs["both"]


class TestArmConfigContext:
    """An arm's knobs must be applied and then restored."""

    def test_applies_and_restores(self):
        before = (
            ai_validation.AI_SELF_CONSISTENCY_SAMPLES,
            ai_validation.AI_WEB_SEARCH_ENABLED,
        )
        with ce._arm_config(ce.ARMS["both"]):
            assert ai_validation.AI_SELF_CONSISTENCY_SAMPLES == ce.SELF_CONSISTENCY_N
            assert ai_validation.AI_WEB_SEARCH_ENABLED is True
        assert (
            ai_validation.AI_SELF_CONSISTENCY_SAMPLES,
            ai_validation.AI_WEB_SEARCH_ENABLED,
        ) == before

    def test_restores_on_exception(self):
        before = ai_validation.AI_WEB_SEARCH_ENABLED
        with pytest.raises(RuntimeError):
            with ce._arm_config(ce.ARMS["search"]):
                raise RuntimeError("boom")
        assert ai_validation.AI_WEB_SEARCH_ENABLED == before


class TestConfidenceSpreadPrecheck:
    """Pre-check 1: is calibration measurable at all?"""

    def test_constant_confidence_is_not_measurable(self):
        cases = [scored("f", i, True, "high") for i in range(20)]
        result = ce.assess_confidence_spread(cases)
        assert result["measurable"] is False
        assert "constant" in result["reason"]

    def test_real_spread_is_measurable(self):
        cases = (
            [scored("f", i, True, "high") for i in range(10)]
            + [scored("f", 100 + i, False, "low") for i in range(10)]
        )
        result = ce.assess_confidence_spread(cases)
        assert result["measurable"] is True
        assert set(result["levels_with_n_ge_5"]) == {"high", "low"}

    def test_thin_second_level_is_not_enough(self):
        cases = (
            [scored("f", i, True, "high") for i in range(30)]
            + [scored("f", 100 + i, False, "low") for i in range(2)]
        )
        assert ce.assess_confidence_spread(cases)["measurable"] is False

    def test_no_cases_is_handled(self):
        assert ce.assess_confidence_spread([])["measurable"] is False


class TestMcNemar:
    """Pairwise arm comparison — the number that justifies further spend."""

    def test_identical_arms_have_no_discordance(self):
        a = [scored("f", i, i % 2 == 0) for i in range(20)]
        result = ce.mcnemar(a, list(a))
        assert result["n_discordant"] == 0
        assert result["p_value_exact"] is None

    def test_detects_a_real_one_sided_difference(self):
        """Arm B right on 20 cases where A is wrong, A right on none where B
        is wrong — an unambiguous win that must reach significance."""
        a = [scored("f", i, False) for i in range(20)]
        b = [scored("f", i, True) for i in range(20)]
        result = ce.mcnemar(a, b)
        assert result["n_discordant"] == 20
        assert result["second_arm_only_correct"] == 20
        assert result["p_value_exact"] < 0.001

    def test_balanced_discordance_is_not_significant(self):
        a = [scored("f", i, i < 10) for i in range(20)]
        b = [scored("f", i, i >= 10) for i in range(20)]
        result = ce.mcnemar(a, b)
        assert result["n_discordant"] == 20
        assert result["p_value_exact"] > 0.5

    def test_pairs_only_on_shared_cases(self):
        a = [scored("f", i, True) for i in range(10)]
        b = [scored("f", i, True) for i in range(5)]
        assert ce.mcnemar(a, b)["n_paired"] == 5

    def test_warns_when_underpowered(self):
        a = [scored("f", i, False) for i in range(5)]
        b = [scored("f", i, True) for i in range(5)]
        assert "Underpowered" in ce.mcnemar(a, b)["note"]

    def test_pairing_key_uses_food_and_nutrient(self):
        """Two foods sharing a nutrient id must not collide."""
        a = [scored("food A", 1003, True), scored("food B", 1003, False)]
        b = [scored("food A", 1003, True), scored("food B", 1003, False)]
        assert ce.mcnemar(a, b)["n_paired"] == 2


class TestFactorialEffects:
    def test_needs_all_four_arms(self):
        assert ce.factorial_effects({"none": [], "both": []})["available"] is False

    def test_main_effects_and_interaction_arithmetic(self):
        def arm(accuracy: float, n: int = 100) -> list[ch.ScoredCase]:
            hits = int(accuracy * n)
            return [scored("f", i, i < hits) for i in range(n)]

        effects = ce.factorial_effects({
            "none": arm(0.50), "search": arm(0.60),
            "selfcons": arm(0.55), "both": arm(0.65),
        })
        assert effects["available"] is True
        # search: mean of (.60-.50) and (.65-.55) = .10
        assert effects["search_main_effect"] == pytest.approx(0.10, abs=1e-6)
        # sampling: mean of (.55-.50) and (.65-.60) = .05
        assert effects["sampling_main_effect"] == pytest.approx(0.05, abs=1e-6)
        # additive -> no interaction
        assert effects["interaction"] == pytest.approx(0.0, abs=1e-6)

    def test_negative_interaction_when_fixes_overlap(self):
        def arm(accuracy: float, n: int = 100) -> list[ch.ScoredCase]:
            hits = int(accuracy * n)
            return [scored("f", i, i < hits) for i in range(n)]

        effects = ce.factorial_effects({
            "none": arm(0.50), "search": arm(0.60),
            "selfcons": arm(0.60), "both": arm(0.62),
        })
        assert effects["interaction"] < 0


class TestStratification:
    """A small pilot must span foods, not truncate onto whichever sorts first."""

    def test_spreads_across_foods(self):
        cases = [labeled(f"food {f}", 1000 + i) for f in range(5) for i in range(20)]
        picked = ce.stratify(cases, 10)
        assert len(picked) == 10
        assert len({c.description for c in picked}) == 5

    def test_truncation_would_have_used_one_food(self):
        cases = [labeled(f"food {f}", 1000 + i) for f in range(5) for i in range(20)]
        assert len({c.description for c in cases[:10]}) == 1

    def test_handles_uneven_foods(self):
        cases = (
            [labeled("big", 1000 + i) for i in range(20)]
            + [labeled("small", 2000)]
        )
        picked = ce.stratify(cases, 10)
        assert len(picked) == 10
        assert "small" in {c.description for c in picked}

    def test_limit_above_available_returns_everything(self):
        cases = [labeled("only", 1000 + i) for i in range(3)]
        assert len(ce.stratify(cases, 99)) == 3


class TestCostEstimate:
    def test_scales_with_cases_and_arms(self):
        one = ce.estimate_cost([ce.ARMS["none"]], 100)
        two = ce.estimate_cost([ce.ARMS["none"], ce.ARMS["none"]], 100)
        assert two["total_usd"] == pytest.approx(2 * one["total_usd"], rel=1e-6)

    def test_search_arm_costs_more_than_baseline(self):
        est = ce.estimate_cost([ce.ARMS["none"], ce.ARMS["search"]], 50)
        assert est["per_arm_usd"]["search"] > est["per_arm_usd"]["none"]


class TestPilotVerdict:
    def test_flags_both_degenerate_signals(self):
        verdict = ce._pilot_verdict({
            "precheck_confidence_spread": {"measurable": False, "reason": "constant"},
            "precheck_sample_divergence": {"informative": False, "reason": "identical"},
        })
        text = " ".join(verdict["next_steps"])
        assert "not measurable" in text
        assert "drop the 'selfcons'" in text

    def test_greenlights_when_both_have_signal(self):
        verdict = ce._pilot_verdict({
            "precheck_confidence_spread": {"measurable": True, "reason": "ok"},
            "precheck_sample_divergence": {"informative": True, "reason": "ok"},
        })
        text = " ".join(verdict["next_steps"])
        assert "proceed" in text
        assert "keep it in the factorial" in text


@pytest.mark.skipif(
    not DATASETS_PRESENT, reason="USDA bulk datasets not present (gitignored)"
)
class TestAgainstRealData:
    def test_db_cases_are_in_domain_and_clustered(self):
        from fediaf_nutrients import get_usda_nutrient_ids

        cases = ch.build_labeled_set_from_db(get_usda_nutrient_ids())
        if not cases:
            pytest.skip("database unavailable")
        foods = {c.description for c in cases}
        assert cases
        # Every case carries the identity the prompts and peer cohorts need
        assert all(c.food_info["food_name"] for c in cases)
        # Clustering is the design's limiting factor — assert it is reported
        experiment = ce.Experiment(cases=cases)
        assert experiment.design_summary()["n_foods_effective_clusters"] == len(foods)
        assert "clustered" in experiment.design_summary()["clustering_warning"].lower() \
            or "nested" in experiment.design_summary()["clustering_warning"].lower()

    def test_pilot_runs_end_to_end_in_mock_mode(self):
        cases = ce.load_cases(limit=6)
        if not cases:
            pytest.skip("no labeled cases available")
        result = ce.run_arm(ce.ARMS["none"], cases)
        assert isinstance(result, list)
