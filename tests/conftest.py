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
