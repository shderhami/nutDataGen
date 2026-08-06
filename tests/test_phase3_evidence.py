"""
Tests for the Phase 3 items of the AI-validation plan.

3.1 web search (tool declaration, content-block iteration, pause_turn) and
3.2 the local bulk-CSV peer median. The bulk datasets are gitignored, so the
peer-median tests that need real data skip when they are absent; the pure
logic (cohort rules, formatting, wiring) is tested without them.
"""
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import ai_validation
import config
import cv_config
import peer_median

DATASETS_PRESENT = (cv_config.FDC_SRL_DIR / "food_nutrient.csv").exists()
needs_datasets = pytest.mark.skipif(
    not DATASETS_PRESENT, reason="USDA bulk datasets not present (gitignored)"
)


def block(block_type: str, **kwargs) -> SimpleNamespace:
    return SimpleNamespace(type=block_type, **kwargs)


class TestContentBlockExtraction:
    """3.1 [audit] — never index content[0]: web search leads with tool blocks."""

    def test_plain_text_response(self):
        content = [block("text", text='{"recommendation": "sr_legacy"}')]
        assert ai_validation._extract_text_from_content(content) == (
            '{"recommendation": "sr_legacy"}'
        )

    def test_skips_leading_server_tool_blocks(self):
        content = [
            block("server_tool_use", id="x", name="web_search"),
            block("web_search_tool_result", tool_use_id="x"),
            block("text", text='{"recommendation": "literature"}'),
        ]
        assert ai_validation._extract_text_from_content(content) == (
            '{"recommendation": "literature"}'
        )

    def test_joins_multiple_text_blocks(self):
        content = [block("text", text="a"), block("text", text="b")]
        assert ai_validation._extract_text_from_content(content) == "a\nb"

    def test_no_text_blocks_yields_empty_string(self):
        content = [block("web_search_tool_result", tool_use_id="x")]
        assert ai_validation._extract_text_from_content(content) == ""


class TestWebSearchToolDeclaration:
    """3.1 — off by default; correct tool version when enabled."""

    def test_disabled_by_default(self, monkeypatch):
        monkeypatch.setattr(ai_validation, "AI_WEB_SEARCH_ENABLED", False)
        assert ai_validation._web_search_tools() == []

    def test_enabled_declares_dynamic_filtering_version(self, monkeypatch):
        monkeypatch.setattr(ai_validation, "AI_WEB_SEARCH_ENABLED", True)
        tools = ai_validation._web_search_tools()
        assert len(tools) == 1
        assert tools[0]["type"] == "web_search_20260209"
        assert tools[0]["name"] == "web_search"
        assert tools[0]["max_uses"] == config.AI_WEB_SEARCH_MAX_USES

    def test_code_execution_not_declared(self, monkeypatch):
        """Dynamic filtering is built in; a second execution environment
        confuses the model."""
        monkeypatch.setattr(ai_validation, "AI_WEB_SEARCH_ENABLED", True)
        assert all("code_execution" not in t["type"] for t in ai_validation._web_search_tools())


class FakeMessages:
    """Records requests and replays a scripted list of responses."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def create(self, **kwargs):
        self.requests.append(kwargs)
        return self.responses.pop(0)


class TestPauseTurnHandling:
    """3.1 — a paused server-tool turn is resumed by re-sending the turn."""

    def _client(self, monkeypatch, responses):
        fake = FakeMessages(responses)
        client = SimpleNamespace(messages=fake)
        monkeypatch.setattr(ai_validation, "MOCK_MODE", False)
        monkeypatch.setattr(ai_validation, "_LIVE_CALLS_GRANTED", True)
        import anthropic
        monkeypatch.setattr(anthropic, "Anthropic", lambda **kwargs: client)
        return fake

    def test_resumes_until_not_paused(self, monkeypatch):
        paused = SimpleNamespace(
            stop_reason="pause_turn",
            content=[block("server_tool_use", id="x", name="web_search")],
        )
        done = SimpleNamespace(
            stop_reason="end_turn", content=[block("text", text='{"ok": true}')]
        )
        fake = self._client(monkeypatch, [paused, done])

        result = ai_validation.call_claude_api("prompt", api_key="k")

        assert result == '{"ok": true}'
        assert len(fake.requests) == 2
        # The resume re-sends the paused turn rather than adding a new user message
        resume_messages = fake.requests[1]["messages"]
        assert resume_messages[-1]["role"] == "assistant"

    def test_resume_count_is_capped(self, monkeypatch):
        always_paused = [
            SimpleNamespace(stop_reason="pause_turn", content=[block("text", text="partial")])
            for _ in range(config.AI_MAX_PAUSE_RESUMES + 5)
        ]
        fake = self._client(monkeypatch, always_paused)

        ai_validation.call_claude_api("prompt", api_key="k")

        assert len(fake.requests) == config.AI_MAX_PAUSE_RESUMES + 1

    def test_no_tools_sent_when_search_disabled(self, monkeypatch):
        monkeypatch.setattr(ai_validation, "AI_WEB_SEARCH_ENABLED", False)
        done = SimpleNamespace(stop_reason="end_turn", content=[block("text", text="{}")])
        fake = self._client(monkeypatch, [done])

        ai_validation.call_claude_api("prompt", api_key="k")

        assert "tools" not in fake.requests[0]


class TestPeerCohortRules:
    """3.2 — cohort selection logic, independent of the datasets."""

    def test_state_classification(self):
        assert peer_median._state_of("Lamb, shoulder, raw") == "raw"
        assert peer_median._state_of("Lamb, shoulder, cooked, braised") == "cooked"
        assert peer_median._state_of("Lamb, shoulder") == "unknown"

    def test_no_species_yields_nothing(self):
        assert peer_median.compute_peer_medians([1003], None) == {}
        assert peer_median.compute_peer_median(1003, None) is None

    def test_no_nutrients_yields_nothing(self):
        assert peer_median.compute_peer_medians([], "lamb") == {}

    def test_format_of_absent_peer_is_empty(self):
        assert peer_median.format_peer_median(None) == ""

    def test_format_reports_cohort_and_caveats(self):
        peer = peer_median.PeerMedian(
            nutrient_id=1003, median=20.0, minimum=18.0, maximum=22.0,
            sample_size=30, state="raw", species="lamb", source="FDC-SRL",
        )
        text = peer_median.format_peer_median(peer)
        assert "30 lamb foods (raw)" in text
        assert "20.0" in text and "18.0" in text and "22.0" in text
        # The caveats are part of the evidence, not decoration
        assert "provenance bias" in text
        assert "plausibility check" in text


@needs_datasets
class TestPeerMedianAgainstRealData:
    """3.2 — behaviour against the pinned bulk datasets."""

    def test_lamb_protein_cohort_is_plausible(self):
        peer = peer_median.compute_peer_median(1003, "lamb", "raw")
        assert peer is not None
        assert peer.sample_size >= peer_median.MIN_COHORT_SIZE
        assert 15.0 < peer.median < 25.0     # raw lamb protein, g/100g
        assert peer.state == "raw"

    def test_batch_matches_single(self):
        batch = peer_median.compute_peer_medians([1003, 1004], "lamb", "raw")
        single = peer_median.compute_peer_median(1003, "lamb", "raw")
        assert batch[1003] == single

    def test_unknown_species_yields_nothing(self):
        assert peer_median.compute_peer_medians([1003], "unobtainium") == {}

    def test_cohort_excludes_unmeasured_rows(self):
        """Rows with no data_points are USDA placeholders; a cohort built from
        them would drag the median toward zero for exactly the nutrients this
        check exists to scrutinise."""
        import csv

        fdc_ids, _ = peer_median._matching_fdc_ids(cv_config.FDC_SRL_DIR, "lamb", "raw")
        measured = peer_median._measured_amounts_by_nutrient(
            cv_config.FDC_SRL_DIR, frozenset(fdc_ids)
        )
        counted = sum(len(v) for v in measured.values())

        raw_rows = 0
        with open(cv_config.FDC_SRL_DIR / "food_nutrient.csv", newline="") as fh:
            for row in csv.DictReader(fh):
                try:
                    if int(row["fdc_id"]) in fdc_ids:
                        raw_rows += 1
                except (KeyError, TypeError, ValueError):
                    continue
        assert counted < raw_rows


class TestPeerMedianWiring:
    """3.2 — the block reaches the prompt, and its absence is never fatal."""

    def test_attach_is_noop_without_species(self):
        nutrients = [{"nutrient_id": 1003, "nutrient_name": "Protein"}]
        ai_validation.attach_peer_medians(nutrients, {"food_name": "x"})
        assert "peer_block" not in nutrients[0]

    def test_attach_survives_peer_module_failure(self, monkeypatch, capsys):
        monkeypatch.setattr(
            peer_median, "compute_peer_medians",
            lambda *a, **k: (_ for _ in ()).throw(RuntimeError("dataset corrupt")),
        )
        nutrients = [{"nutrient_id": 1003, "nutrient_name": "Protein"}]
        ai_validation.attach_peer_medians(nutrients, {"protein_species": "lamb"})
        assert "peer_block" not in nutrients[0]
        assert "peer medians unavailable" in capsys.readouterr().out

    def test_peer_block_is_appended_to_prompt(self):
        nutrient = {
            "nutrient_id": 1003, "nutrient_name": "Protein", "unit": "g",
            "prompt_type": "sr_only", "sr_value": 20.0, "sr_metadata": {},
            "peer_block": "\nLOCAL USDA PEER COHORT (test marker)\n",
        }
        prompt = ai_validation._build_prompt("lamb shoulder", nutrient)
        assert "LOCAL USDA PEER COHORT (test marker)" in prompt

    def test_prompt_without_peer_block_is_unchanged(self):
        nutrient = {
            "nutrient_id": 1003, "nutrient_name": "Protein", "unit": "g",
            "prompt_type": "sr_only", "sr_value": 20.0, "sr_metadata": {},
        }
        assert ai_validation._build_prompt("lamb shoulder", nutrient) == (
            ai_validation._build_prompt_body("lamb shoulder", nutrient)
        )
