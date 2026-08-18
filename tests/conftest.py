"""
Shared pytest configuration.

Its main job is to make billed Anthropic API calls impossible from the test
suite. Before this existed, config.load_dotenv() put a real ANTHROPIC_API_KEY
into the environment and AI_MOCK_MODE defaulted to false, so 16 tests that call
the validators without patching were issuing real, billed requests on every run.

Two independent layers, so a newly added test cannot reintroduce the leak:
  1. MOCK_MODE is forced on for every test, so the validators take their mock
     path and never construct a client.
  2. The anthropic client classes are replaced with ones that raise, so any code
     path that bypasses MOCK_MODE fails loudly instead of spending money.

A test that genuinely needs the live API must be marked @pytest.mark.live_api
AND run with ALLOW_LIVE_AI_CALLS=1; otherwise it is skipped.
"""
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


LIVE_CALLS_ENV = "ALLOW_LIVE_AI_CALLS"


def _live_calls_permitted() -> bool:
    return os.environ.get(LIVE_CALLS_ENV, "").strip().lower() in ("1", "true", "yes")


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "live_api: test makes a real, billed Anthropic API call. Skipped unless "
        f"{LIVE_CALLS_ENV}=1 is set.",
    )


def pytest_collection_modifyitems(config, items):
    """Skip live-API tests unless explicitly permitted for this run."""
    if _live_calls_permitted():
        return
    skip = pytest.mark.skip(
        reason=f"live API test; set {LIVE_CALLS_ENV}=1 to permit billed calls"
    )
    for item in items:
        if "live_api" in item.keywords:
            item.add_marker(skip)


class BilledAPICallBlocked(RuntimeError):
    """Raised when test code tries to construct a real Anthropic client."""


@pytest.fixture(autouse=True)
def _block_billed_api_calls(request, monkeypatch):
    """
    Force mock mode and make real client construction raise.

    Autouse, so it applies to every test without the test having to opt in.
    """
    if "live_api" in request.keywords and _live_calls_permitted():
        # Explicitly permitted for this run — leave the real client in place.
        return

    import ai_validation

    monkeypatch.setattr(ai_validation, "MOCK_MODE", True, raising=False)

    try:
        import anthropic
    except ImportError:  # pragma: no cover - anthropic is a hard dependency
        return

    def _blocked(*args, **kwargs):
        raise BilledAPICallBlocked(
            "A test tried to construct a real Anthropic client. Billed API calls "
            "are blocked in the test suite. Use mock mode, patch the call site, or "
            f"mark the test @pytest.mark.live_api and run with {LIVE_CALLS_ENV}=1."
        )

    monkeypatch.setattr(anthropic, "Anthropic", _blocked)
    monkeypatch.setattr(anthropic, "AsyncAnthropic", _blocked)


# =============================================================================
# Production-mutation tripwire (added 2026-08-18)
# =============================================================================
# An audit harness with an incomplete monkeypatch once wrote a 52-row test
# ingredient into the PRODUCTION database while its own report claimed no DB
# was touched. Tests must never mutate production — this fixture proves it
# every run instead of trusting assertions: it snapshots production row
# counts before the session and fails loudly if they changed after. Skips
# when the DB is unreachable or the session already targets a test database.

_PRODUCTION_DB = "cat_food_formulator"


def _prod_counts():
    import config as _config
    if _config.DATABASE_NAME != _PRODUCTION_DB:
        return None  # session already points at a test DB — nothing to guard
    try:
        from db_connection import get_db
        db = get_db()
        with db.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS n FROM ingredients")
            foods = cur.fetchone()["n"]
            cur.execute("SELECT COUNT(*) AS n FROM ingredient_nutrients")
            rows = cur.fetchone()["n"]
        return foods, rows
    except Exception:  # noqa: BLE001 - unreachable DB means nothing to guard
        return None


@pytest.fixture(scope="session", autouse=True)
def production_db_mutation_tripwire():
    before = _prod_counts()
    yield
    if before is None:
        return
    after = _prod_counts()
    if after is not None and after != before:
        raise RuntimeError(
            f"PRODUCTION DATABASE MUTATED DURING TESTS: ingredients "
            f"{before[0]}->{after[0]}, ingredient_nutrients "
            f"{before[1]}->{after[1]}. A test or harness wrote to "
            f"{_PRODUCTION_DB}. Find and remove the stray rows, and fix the "
            f"test to target cat_food_formulator_test (DATABASE_NAME env).")
