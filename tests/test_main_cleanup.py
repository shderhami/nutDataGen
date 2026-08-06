"""
Tests for main()'s incomplete-ingredient cleanup.

The broad exception handler in main() deletes the ingredient row created
before a failure — but only rows whose nutrients were never saved. These pin
the two edges of the food_id lifecycle that decide "incomplete":

  1. Once add_food_nutrients succeeds the row is committed data; a failure in
     anything after it (CV assignment, prompts) must NOT delete it.
  2. A failure before the first loop iteration (initialize_database) must
     surface the original error, not an UnboundLocalError from the handler
     referencing food_id before its first assignment.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import config
import main


SAVED_FOOD_ID = 99999


@pytest.fixture
def deleted_foods(monkeypatch):
    """Record delete_food calls instead of touching the database."""
    calls: list[int] = []
    monkeypatch.setattr(main, "delete_food", lambda food_id: calls.append(food_id))
    return calls


@pytest.fixture
def stub_pipeline_through_save(monkeypatch):
    """Stub everything main() touches so one food reaches a successful save."""
    records = [{"food_id": SAVED_FOOD_ID}]

    monkeypatch.setattr(config, "AI_MOCK_MODE", True)  # skip the billing prompt
    monkeypatch.setattr(main, "initialize_database", lambda: None)
    monkeypatch.setattr(main, "close_db", lambda: None)
    monkeypatch.setattr(main, "display_welcome", lambda: None)
    monkeypatch.setattr(main, "display_final_summary", lambda records, name: None)
    monkeypatch.setattr(main, "food_exists_by_name", lambda name: None)
    monkeypatch.setattr(
        main,
        "prompt_food_info",
        lambda: {
            "food_name": "test food",
            "category": "Meat",
            "base_unit": "g",
            "portion_qty": 1,
            "grams_per_unit": 100.0,
            "price_per_unit": 1.0,
        },
    )
    monkeypatch.setattr(main, "add_ingredient", lambda **kwargs: SAVED_FOOD_ID)
    monkeypatch.setattr(
        main, "process_single_food", lambda food_id, food_info: records
    )
    # The completeness check compares against get_all_nutrients(); keep equal.
    monkeypatch.setattr(main, "get_all_nutrients", lambda: [None] * len(records))
    # Answers "Save to database?" (and any later confirmation) with yes.
    monkeypatch.setattr(main, "prompt_confirmation", lambda msg: True)
    monkeypatch.setattr(main, "add_food_nutrients", lambda recs: len(recs))


class TestSavedFoodSurvivesLaterFailure:
    """A committed ingredient must never be handed to cleanup."""

    def test_failure_after_save_does_not_delete_the_food(
        self, stub_pipeline_through_save, deleted_foods, monkeypatch
    ):
        """A crash in CV assignment — after the save — must not trigger cleanup."""

        def boom(food_id):
            raise RuntimeError("cv assignment crashed")

        monkeypatch.setattr(main, "assign_cv_for_food", boom)

        with pytest.raises(RuntimeError, match="cv assignment crashed"):
            main.main()

        assert deleted_foods == [], (
            f"cleanup deleted saved food(s) {deleted_foods} after a post-save failure"
        )


class TestEarlyFailureCleanupIsSafe:
    """Cleanup must be inert when no ingredient row exists yet."""

    def test_failure_before_first_food_reraises_original_error(
        self, deleted_foods, monkeypatch
    ):
        """initialize_database failing must surface its own error, not an
        UnboundLocalError from the handler referencing an unassigned food_id."""
        monkeypatch.setattr(config, "AI_MOCK_MODE", True)
        monkeypatch.setattr(main, "display_welcome", lambda: None)
        monkeypatch.setattr(main, "close_db", lambda: None)

        def db_down():
            raise RuntimeError("db down")

        monkeypatch.setattr(main, "initialize_database", db_down)

        with pytest.raises(RuntimeError, match="db down"):
            main.main()

        assert deleted_foods == []
