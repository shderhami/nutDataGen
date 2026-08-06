"""
Tests for the billed-API guard.

These pin the invariant that cost money when it was missing: no code path may
reach the Anthropic API without an explicit grant. If one of these fails, the
test suite is billing the operator on every run.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import ai_validation

# Everything below goes through the `ai_validation` module object rather than
# from-imports. The project root has an __init__.py, so the module can be loaded
# under two identities in one pytest session ("ai_validation" and
# "nutDataGen.ai_validation"); a from-imported exception class then isn't the
# same object as the one raised, and pytest.raises silently fails to catch it.
# (See the "avoid isinstance issues" comment in test_ai_validation.py.)


class TestGuardBlocksByDefault:
    """Billed calls must be refused unless explicitly permitted."""

    def test_not_allowed_by_default(self, monkeypatch):
        """A plain process has no grant."""
        monkeypatch.setattr(ai_validation, "_LIVE_CALLS_GRANTED", False)
        monkeypatch.setattr(ai_validation, "ALLOW_LIVE_AI_CALLS", False)

        assert ai_validation.live_ai_calls_allowed() is False

    def test_assert_raises_when_not_allowed(self, monkeypatch):
        """The guard raises rather than silently degrading."""
        monkeypatch.setattr(ai_validation, "_LIVE_CALLS_GRANTED", False)
        monkeypatch.setattr(ai_validation, "ALLOW_LIVE_AI_CALLS", False)

        with pytest.raises(ai_validation.LiveAPICallBlocked):
            ai_validation.assert_live_ai_calls_allowed()

    def test_call_claude_api_blocked_outside_mock_mode(self, monkeypatch):
        """The sync call site is guarded before any client is constructed."""
        monkeypatch.setattr(ai_validation, "MOCK_MODE", False)
        monkeypatch.setattr(ai_validation, "_LIVE_CALLS_GRANTED", False)
        monkeypatch.setattr(ai_validation, "ALLOW_LIVE_AI_CALLS", False)

        with pytest.raises(ai_validation.LiveAPICallBlocked):
            ai_validation.call_claude_api("test prompt")

    def test_env_var_permits(self, monkeypatch):
        """ALLOW_LIVE_AI_CALLS is an accepted grant."""
        monkeypatch.setattr(ai_validation, "_LIVE_CALLS_GRANTED", False)
        monkeypatch.setattr(ai_validation, "ALLOW_LIVE_AI_CALLS", True)

        assert ai_validation.live_ai_calls_allowed() is True
        ai_validation.assert_live_ai_calls_allowed()  # must not raise

    def test_explicit_grant_permits(self, monkeypatch, capsys):
        """permit_live_ai_calls() grants and announces itself."""
        monkeypatch.setattr(ai_validation, "_LIVE_CALLS_GRANTED", False)
        monkeypatch.setattr(ai_validation, "ALLOW_LIVE_AI_CALLS", False)

        ai_validation.permit_live_ai_calls("unit test")

        assert ai_validation.live_ai_calls_allowed() is True
        assert "unit test" in capsys.readouterr().out


class TestMockModeStillWorks:
    """Mock mode must bypass the guard — offline runs stay possible."""

    def test_mock_mode_needs_no_grant(self, monkeypatch):
        """Mock responses are returned without any billed-call permission."""
        monkeypatch.setattr(ai_validation, "MOCK_MODE", True)
        monkeypatch.setattr(ai_validation, "_LIVE_CALLS_GRANTED", False)
        monkeypatch.setattr(ai_validation, "ALLOW_LIVE_AI_CALLS", False)

        assert ai_validation.call_claude_api("test prompt")


class TestConftestBlocksClientConstruction:
    """The suite-wide backstop must be active for every test."""

    def test_anthropic_client_construction_raises(self):
        """Even bypassing MOCK_MODE, constructing a client fails in tests."""
        import anthropic

        with pytest.raises(Exception) as exc:
            anthropic.Anthropic(api_key="sk-not-a-real-key")
        assert "blocked" in str(exc.value).lower()

    def test_async_client_construction_raises(self):
        """Same backstop covers the async client."""
        import anthropic

        with pytest.raises(Exception) as exc:
            anthropic.AsyncAnthropic(api_key="sk-not-a-real-key")
        assert "blocked" in str(exc.value).lower()

    def test_mock_mode_forced_on_for_tests(self):
        """The autouse fixture forces mock mode regardless of .env."""
        assert ai_validation.MOCK_MODE is True


class TestGuardIsNotRetried:
    """A permission refusal must surface immediately, not after backoff.

    LiveAPICallBlocked subclasses RuntimeError, which the sync retry loop
    catches. Without an explicit re-raise the guard was retried AI_MAX_RETRIES
    times (~60s of backoff) and then reported as a generic AIValidationError,
    disguising a policy decision as an API failure.
    """

    def test_sync_retry_does_not_swallow_guard(self, monkeypatch):
        """call_claude_api_with_retry re-raises the block without retrying."""
        monkeypatch.setattr(ai_validation, "MOCK_MODE", False)
        monkeypatch.setattr(ai_validation, "_LIVE_CALLS_GRANTED", False)
        monkeypatch.setattr(ai_validation, "ALLOW_LIVE_AI_CALLS", False)

        calls = []
        real = ai_validation.call_claude_api

        def counting(prompt, api_key=None, schema=None):
            calls.append(prompt)
            return real(prompt, api_key, schema)

        monkeypatch.setattr(ai_validation, "call_claude_api", counting)

        with pytest.raises(ai_validation.LiveAPICallBlocked):
            ai_validation.call_claude_api_with_retry("test prompt")

        assert len(calls) == 1, f"guard was retried {len(calls)} times"

    def test_guard_is_not_reported_as_generic_api_error(self, monkeypatch):
        """The refusal must not be reclassified as AIValidationError."""
        monkeypatch.setattr(ai_validation, "MOCK_MODE", False)
        monkeypatch.setattr(ai_validation, "_LIVE_CALLS_GRANTED", False)
        monkeypatch.setattr(ai_validation, "ALLOW_LIVE_AI_CALLS", False)

        with pytest.raises(ai_validation.LiveAPICallBlocked) as exc:
            ai_validation.call_claude_api_with_retry("test prompt")
        assert "not permitted" in str(exc.value)
