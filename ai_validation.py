"""
AI-powered literature validation for nutrition data.

Uses Claude AI to validate nutrient values against scientific literature
and provide recommendations for discrepancies.
"""
import asyncio
import hashlib
import json
import math
import os
import statistics
import time
from functools import lru_cache
from typing import Optional
from dataclasses import dataclass

from config import (
    AI_MODEL,
    AI_RATE_LIMIT_RPM,
    AI_MIN_REQUEST_INTERVAL,
    AI_MAX_RETRIES,
    AI_RETRY_BASE_DELAY,
    SKIP_VALIDATION_THRESHOLD,
    AI_CONCURRENT_LIMIT,
    AI_MAX_CONCURRENT_LIMIT,
    AI_MOCK_MODE,
    ALLOW_LIVE_AI_CALLS,
    AI_MASS_FAILURE_THRESHOLD,
    AI_WEB_SEARCH_ENABLED,
    AI_WEB_SEARCH_MAX_USES,
    AI_WEB_SEARCH_TOOL_TYPE,
    AI_MAX_PAUSE_RESUMES,
    AI_SELF_CONSISTENCY_SAMPLES,
    AI_SELF_CONSISTENCY_MAX_SPREAD,
)


# Mock mode flag - imported from config (default: False = real API calls)
MOCK_MODE = AI_MOCK_MODE

# In-process grant for billed calls, separate from the environment variable so an
# interactive run can ask the user rather than requiring them to export anything.
_LIVE_CALLS_GRANTED = False


class LiveAPICallBlocked(RuntimeError):
    """Raised when a billed Anthropic call is attempted without permission."""


def permit_live_ai_calls(reason: str) -> None:
    """
    Grant permission for billed Anthropic calls for the rest of this process.

    Call this only after the operator has actually agreed to spend money — see
    main.py, which asks before running validation. `reason` is echoed so the
    grant is visible in the run's output rather than silent.
    """
    global _LIVE_CALLS_GRANTED
    _LIVE_CALLS_GRANTED = True
    print(f"[LIVE AI] Billed Anthropic calls enabled: {reason}")


def live_ai_calls_allowed() -> bool:
    """Whether billed Anthropic calls are currently permitted."""
    return _LIVE_CALLS_GRANTED or ALLOW_LIVE_AI_CALLS


def assert_live_ai_calls_allowed() -> None:
    """
    Guard every billed call site.

    Deliberately raises rather than falling back to mock data: a silent mock
    would let a caller believe it had real validation when it did not.
    """
    if live_ai_calls_allowed():
        return
    raise LiveAPICallBlocked(
        "Billed Anthropic API calls are not permitted in this process. "
        "Set ALLOW_LIVE_AI_CALLS=1, or call ai_validation.permit_live_ai_calls() "
        "after the operator agrees. Use AI_MOCK_MODE=true for offline runs."
    )


class AIValidationError(Exception):
    """Exception raised for AI validation errors."""
    pass


class NonRetryableAPIError(AIValidationError):
    """
    An API failure that will not succeed on retry (bad request, auth, model).

    Typed so the retry wrappers can stop immediately instead of substring-
    matching an error message that lost its exception type.
    """


def _classify_api_exception(exc: Exception) -> Exception:
    """
    Map an SDK exception onto our retry policy, preserving the type.

    Wrapping everything in RuntimeError destroyed the typed exception and
    forced the retry wrappers to substring-match the message. Rate limits,
    overloads, timeouts and connection errors are retryable; 4xx request
    errors are not, and retrying them just burns backoff and quota.
    """
    try:
        import anthropic
    except ImportError:
        return RuntimeError(f"Claude API error: {exc}")

    non_retryable = (
        getattr(anthropic, "BadRequestError", ()),
        getattr(anthropic, "AuthenticationError", ()),
        getattr(anthropic, "PermissionDeniedError", ()),
        getattr(anthropic, "NotFoundError", ()),
        getattr(anthropic, "UnprocessableEntityError", ()),
    )
    non_retryable = tuple(t for t in non_retryable if isinstance(t, type))
    if non_retryable and isinstance(exc, non_retryable):
        return NonRetryableAPIError(f"{type(exc).__name__}: {exc}")

    return RuntimeError(f"Claude API error: {exc}")


@dataclass
class AIValidationResult:
    """Result from AI validation for a single nutrient."""
    nutrient_id: Optional[int]
    nutrient_name: str
    prompt_type: str  # "sr_only", "both_sources", "missing"
    recommendation: str  # "sr_legacy", "foundation", "estimate", "literature"
    recommended_value: Optional[float]
    justification: str
    literature_source: str
    confidence: str  # "high", "medium", "low"


@lru_cache(maxsize=1)
def prompt_version_hash() -> str:
    """
    Short digest of the prompt-building logic in this module.

    Stored beside `ai_model` so a justification in the database can be traced
    to the prompt that produced it. Mirrors the CV pipeline's AST-normalized
    hashing (cv_config.normalized_source): comments, docstrings and formatting
    do not move the digest, but prompt text and logic do.

    Falls back to "unknown" rather than raising — provenance metadata must
    never break a validation run.
    """
    try:
        import cv_config

        digest = hashlib.sha256(
            cv_config.normalized_source(__file__).encode("utf-8")
        ).hexdigest()
        return digest[:12]
    except Exception:  # noqa: BLE001 - provenance is metadata, never fatal
        return "unknown"


def model_provenance() -> str:
    """
    The value stored in `ai_model`: model ID plus prompt version.

    e.g. "claude-opus-4-6+p:1a2b3c4d5e6f". Fits the column's 50 chars.
    """
    return f"{AI_MODEL}+p:{prompt_version_hash()}"


def _format_provenance(metadata: dict) -> str:
    """
    Render USDA provenance metadata as prompt INPUT lines.

    num_samples is the single most diagnostic field: a value with no data
    points and no derivation is a database placeholder, not a measurement —
    exactly the signal whose absence caused the EPA/DHA HIGH-confidence
    failure on FDC 174326.
    """
    def fmt(value: object) -> object:
        return "n/a" if value is None else value

    num_samples = metadata.get("num_samples")
    return "\n".join([
        f"- Data Points: {num_samples if num_samples is not None else 'none recorded'}",
        f"- Min / Median / Max: {fmt(metadata.get('min_value'))} / "
        f"{fmt(metadata.get('median_value'))} / {fmt(metadata.get('max_value'))}",
        f"- Derivation: {metadata.get('derivation_description') or 'none recorded'}",
        f"- Sample Date: {metadata.get('year_acquired') or 'unknown'}",
    ])


# Appended to every prompt that shows a USDA value, so the model treats the
# provenance block as evidence rather than decoration.
_PROVENANCE_RULE = (
    "PROVENANCE MATTERS: a value backed by no data points and no derivation is "
    "a database placeholder USDA never measured — do not treat it as evidence. "
    "Validate as if the value were unknown, and never rate such a value high "
    "confidence on agreement alone."
)


def _confidence_criteria(source_label: str) -> str:
    """
    Confidence criteria that rate the ANSWER, not agreement with USDA.

    The original criteria defined every level as distance from the USDA value
    ("high: sources agree within +/-5% of SR Legacy value"), which had three
    consequences:

      * A well-evidenced disagreement was forced to score LOW — the model had
        no way to say "I am confident USDA is wrong", which is exactly the
        case the whole validator exists to catch.
      * It contradicted the provenance rule above, which tells the model to
        validate as if the value were unknown.
      * +/-5% is tighter than the biological variation the peer block itself
        reports (8-26%), so a correct value could never earn "high".

    Agreement with USDA is computable on our side — we hold both numbers — so
    spending the label on it wasted the one signal we need. `build_prompt_
    missing`, the one prompt that scored agreement AMONG SOURCES rather than
    against USDA, is also the path that performed best; this generalises it.
    """
    return f"""CONFIDENCE CRITERIA — rate your confidence in the value you are RECOMMENDING, not in how closely it matches the {source_label} value. A well-evidenced disagreement with {source_label} is HIGH confidence, not low.
- high: several independent sources converge within ~15% of each other, and clearly describe this same food (same species, same cut, same raw state)
- medium: sources exist but scatter more widely, or describe a related but not identical cut or preparation
- low: few or conflicting sources, or the food cannot be matched confidently

The local peer cohort, if shown, is a plausibility check and NOT an independent source — do not count it toward source agreement."""


def _format_food_context(food_name: str, food_info: Optional[dict]) -> str:
    """
    Identify the food precisely in prompts.

    The console name alone ("lamb shoulder") lets the model anchor on a
    different cut than the row being validated, so species, category and the
    FDC ID are threaded through.

    `cooking_method` is deliberately EXCLUDED. Ingredients are entered as raw
    and cooking is adjusted for downstream, so the stored cooking method
    describes later preparation, not the composition being validated. Passing
    it would ask the model to validate a raw USDA value while describing the
    food as cooked — e.g. an ingredient named "...raw" carrying
    cooking_method='cooked' — which inflates every nutrient the model reasons
    about, since cooking concentrates them per 100 g.
    """
    if not food_info:
        return food_name
    parts = []
    if food_info.get("protein_species"):
        parts.append(f"protein species: {food_info['protein_species']}")
    if food_info.get("category"):
        parts.append(f"category: {food_info['category']}")
    if food_info.get("sr_fdc_id"):
        parts.append(f"SR Legacy FDC ID {food_info['sr_fdc_id']}")
    if food_info.get("foundation_fdc_id"):
        parts.append(f"Foundation FDC ID {food_info['foundation_fdc_id']}")
    if not parts:
        return food_name
    return f"{food_name} ({'; '.join(parts)})"


def build_prompt_sr_only(
    food_name: str,
    nutrient_name: str,
    sr_value: float,
    unit: str,
    metadata: dict,
    food_info: Optional[dict] = None
) -> str:
    """
    Build prompt for nutrients only available in SR Legacy.
    Asks AI to validate against independent sources (not SR Legacy-derived).
    """
    food_desc = _format_food_context(food_name, food_info)

    return f"""You are a cat food nutrition science expert. The following is the amount of {nutrient_name} in 100g of {food_desc} and was obtained from USDA SR Legacy food database. Search valid scientific resources to confirm or revise this value for cat food formulation.

INPUT:
- Nutrient: {nutrient_name}
- Value: {sr_value} {unit}/100g
{_format_provenance(metadata)}

RULES:
1. Do NOT use USDA SR Legacy or SR Legacy-derived sources as validation—this is the source being evaluated
2. Search ONLY scientific literature, peer-reviewed studies, and established food composition databases to confirm or estimate a value.
3. Do NOT search USDA Foundation—this nutrient is not available in that database
4. {_PROVENANCE_RULE}

PRIORITY SOURCES:
- National DBs: Japanese MEXT, UK CoFID, Australian AFCD, Canadian CNF, German BLS, Danish DTU, Dutch NEVO, French CIQUAL
- International: FAO/INFOODS, EuroFIR
- Journals (2015+): J Food Comp Anal, Food Chemistry, J Agric Food Chem, Br J Nutr
- Pet nutrition: NRC 2006, J Anim Physiol Anim Nutr

{_confidence_criteria('SR Legacy')}

Respond in this exact JSON format:
{{
    "recommendation": "sr_legacy" or "literature",
    "recommended_value": <number or null if keeping SR Legacy>,
    "justification": "<2 sentences explaining your reasoning>",
    "literature_source": "<citation or 'USDA SR Legacy' if keeping original>",
    "confidence": "high", "medium", or "low"
}}"""


def build_prompt_foundation_only(
    food_name: str,
    nutrient_name: str,
    foundation_value: float,
    unit: str,
    metadata: dict,
    food_info: Optional[dict] = None
) -> str:
    """
    Build prompt for nutrients only available in Foundation.
    Asks AI to validate against independent sources (not Foundation-derived).
    """
    food_desc = _format_food_context(food_name, food_info)

    return f"""You are a cat food nutrition science expert. The following is the amount of {nutrient_name} in 100g of {food_desc} and was obtained from USDA Foundation food database. Search valid scientific resources to confirm or revise this value for cat food formulation.

INPUT:
- Nutrient: {nutrient_name}
- Value: {foundation_value} {unit}/100g
{_format_provenance(metadata)}

RULES:
1. Do NOT use USDA Foundation or Foundation-derived sources as validation—this is the source being evaluated
2. Search ONLY scientific literature, peer-reviewed studies, and established food composition databases to confirm or estimate a value.
3. Do NOT search USDA SR Legacy—this nutrient is not available in that database
4. {_PROVENANCE_RULE}

PRIORITY SOURCES:
- National DBs: Japanese MEXT, UK CoFID, Australian AFCD, Canadian CNF, German BLS, Danish DTU, Dutch NEVO, French CIQUAL
- International: FAO/INFOODS, EuroFIR
- Journals (2015+): J Food Comp Anal, Food Chemistry, J Agric Food Chem, Br J Nutr
- Pet nutrition: NRC 2006, J Anim Physiol Anim Nutr

{_confidence_criteria('Foundation')}

Respond in this exact JSON format:
{{
    "recommendation": "foundation" or "literature",
    "recommended_value": <number or null if keeping Foundation>,
    "justification": "<2 sentences explaining your reasoning>",
    "literature_source": "<citation or 'USDA Foundation' if keeping original>",
    "confidence": "high", "medium", or "low"
}}"""


def build_prompt_both_sources(
    food_name: str,
    nutrient_name: str,
    sr_value: float,
    foundation_value: float,
    unit: str,
    discrepancy_percent: float,
    sr_metadata: dict,
    foundation_metadata: dict,
    food_info: Optional[dict] = None
) -> str:
    """
    Build prompt for nutrients available in both sources with discrepancy.
    Asks AI which value is more supported by independent literature.
    """
    food_desc = _format_food_context(food_name, food_info)

    return f"""You are a cat food nutrition science expert. The followings are the amout of {nutrient_name} in 100g of {food_desc} and were obtained from USDA SR Legacy and Foundation food databases. Search valid scientific resources to confirm which value is more accurate or estimate a new value. This is for cat food formulation (FEDIAF 2025 compliance).

INPUT:
- Nutrient: {nutrient_name}
- Discrepancy: {discrepancy_percent:.1f}%

SR LEGACY VALUE: {sr_value} {unit}/100g
{_format_provenance(sr_metadata)}

FOUNDATION VALUE: {foundation_value} {unit}/100g
{_format_provenance(foundation_metadata)}

RULES:
1. Do NOT use USDA SR Legacy or USDA Foundation as validation—these are the sources being evaluated
2. Search ONLY scientific literature, peer-reviewed studies, and established food composition databases to estimate a value.
3. {_PROVENANCE_RULE}

PRIORITY SOURCES:
- National DBs: Japanese MEXT, UK CoFID, Australian AFCD, Canadian CNF, German BLS, Danish DTU, Dutch NEVO, French CIQUAL
- International: FAO/INFOODS, EuroFIR
- Journals (2015+): J Food Comp Anal, Food Chemistry, J Agric Food Chem, Br J Nutr
- Pet nutrition: NRC 2006, J Anim Physiol Anim Nutr

{_confidence_criteria('USDA')}

Respond in this exact JSON format:
{{
    "recommendation": "foundation" or "sr_legacy" or "literature",
    "recommended_value": <number or null if recommending foundation or sr_legacy>,
    "justification": "<2 sentences explaining your reasoning>",
    "literature_source": "<citation or 'USDA SR Legacy' or 'USDA Foundation' if recommending these databases>",
    "confidence": "high" or "medium" or "low"
}}"""


def build_prompt_missing(
    food_name: str,
    nutrient_name: str,
    unit: str,
    food_info: Optional[dict] = None
) -> str:
    """
    Build prompt for nutrients missing from both USDA sources.
    Asks AI to estimate the value based on literature.
    """
    food_desc = _format_food_context(food_name, food_info)

    return f"""You are a cat food nutrition science expert. Provide your best estimate for the amount of {nutrient_name} content in 100g of {food_desc} for cat food formulation (FEDIAF 2025 compliance).

INPUT:
- Ingredient: {food_desc}
- Nutrient: {nutrient_name}
- Unit: {unit}/100g

RULES:
1. Do NOT search USDA SR Legacy or USDA Foundation—this nutrient is not available in either database
2. Search ONLY scientific literature, peer-reviewed studies, and established food composition databases to estimate a value.
3. If the nutrient is genuinely absent from this food (not merely unmeasured), use recommendation "confirmed_zero" with recommended_value 0. Reserve "insufficient_data" for values that are genuinely undeterminable.

PRIORITY SOURCES:
- National DBs: Japanese MEXT, UK CoFID, Australian AFCD, Canadian CNF, German BLS, Danish DTU, Dutch NEVO, French CIQUAL
- International: FAO/INFOODS, EuroFIR
- Journals (2015+): J Food Comp Anal, Food Chemistry, J Agric Food Chem, Br J Nutr
- Pet nutrition: NRC 2006, J Anim Physiol Anim Nutr

{_confidence_criteria('USDA')}

Respond in this exact JSON format:
{{
    "recommendation": "literature" or "insufficient_data" or "confirmed_zero",
    "recommended_value": <number, 0 for confirmed_zero, or null if insufficient data>,
    "justification": "<2 sentences explaining your reasoning>",
    "literature_source": "<citation or 'No reliable sources found' if insufficient data>",
    "confidence": "high" or "medium" or "low"
}}"""


# Legal `recommendation` values per prompt type. Enforced server-side via
# structured outputs, so the model cannot return a value outside the set.
_RECOMMENDATION_ENUMS = {
    "sr_only": ["sr_legacy", "literature"],
    "foundation_only": ["foundation", "literature"],
    "both_sources": ["foundation", "sr_legacy", "literature"],
    "missing": ["literature", "insufficient_data", "confirmed_zero"],
}


def _response_schema(prompt_type: str) -> dict:
    """
    JSON schema for structured outputs (`output_config.format`).

    Numeric range constraints are not supported by structured-output schemas,
    so plausibility bounds on recommended_value stay in code
    (_coerce_recommended_value and downstream checks).
    """
    return {
        "type": "object",
        "properties": {
            "recommendation": {
                "type": "string",
                "enum": _RECOMMENDATION_ENUMS[prompt_type],
            },
            "recommended_value": {"type": ["number", "null"]},
            "justification": {"type": "string"},
            "literature_source": {"type": "string"},
            "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
        },
        "required": [
            "recommendation", "recommended_value", "justification",
            "literature_source", "confidence",
        ],
        "additionalProperties": False,
    }


def _extract_text_from_content(content: list) -> str:
    """
    Concatenate the text blocks of a response.

    Never index content[0]: with web search enabled the response leads with
    server_tool_use / web_search_tool_result blocks, so the first block is not
    the model's answer. Blocks without a `.text` are skipped.
    """
    parts = []
    for block in content:
        if getattr(block, "type", None) == "text":
            text = getattr(block, "text", "")
            if text:
                parts.append(text)
    return "\n".join(parts)


def _web_search_tools() -> list[dict]:
    """The web search tool definition, or [] when the feature is off."""
    if not AI_WEB_SEARCH_ENABLED:
        return []
    return [{
        "type": AI_WEB_SEARCH_TOOL_TYPE,
        "name": "web_search",
        "max_uses": AI_WEB_SEARCH_MAX_USES,
    }]


def _search_directive() -> str:
    """
    Explicit instruction to actually use the web_search tool.

    Opus 4.7 and later reach for tools markedly less often than 4.6, preferring
    to reason from parametric memory. Merely attaching the tool is not enough:
    a measured call with the tool attached came back with server_tool_use=None
    and a confident recalled answer — paying ~5,500 extra input tokens for a
    tool definition the model ignored. The existing prompt language ("Search
    ONLY scientific literature") reads as a scope restriction, not as an
    instruction to invoke a tool, so the directive has to be explicit.

    Empty when search is off, so the no-search arm is unaffected.
    """
    if not AI_WEB_SEARCH_ENABLED:
        return ""
    return (
        "\nSEARCH REQUIRED: use the web_search tool before you answer. Do not "
        "answer from recalled knowledge. Every citation in literature_source "
        "must come from a page you actually retrieved in this session — if you "
        "did not retrieve it, do not cite it. If your searches return nothing "
        "usable for this nutrient and food, say so plainly and lower your "
        "confidence accordingly rather than falling back on memory.\n"
    )


def call_claude_api(
    prompt: str,
    api_key: Optional[str] = None,
    schema: Optional[dict] = None,
) -> str:
    """
    Call Claude API with the given prompt.

    Args:
        prompt: The prompt to send
        api_key: Anthropic API key (uses env var if not provided)
        schema: JSON schema for structured outputs (constrains the response)

    Returns:
        API response text
    """
    if MOCK_MODE:
        return _get_mock_response(prompt)

    assert_live_ai_calls_allowed()

    # Real API call
    try:
        import anthropic

        key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        if not key:
            raise ValueError("No Anthropic API key provided")

        # max_retries=0: this module owns retry policy (typed classification +
        # our own backoff). Leaving the SDK's default 2 on top multiplied one
        # rate-limited nutrient into ~15 requests and ~60s of backoff.
        client = anthropic.Anthropic(api_key=key, max_retries=0)

        extra: dict = {}
        if schema is not None:
            extra["output_config"] = {
                "format": {"type": "json_schema", "schema": schema}
            }
        tools = _web_search_tools()
        if tools:
            extra["tools"] = tools

        messages: list[dict] = [{"role": "user", "content": prompt}]

        # A server-side tool loop can stop with stop_reason "pause_turn"; the
        # turn is resumed by re-sending it, not by adding a new user message.
        for _ in range(AI_MAX_PAUSE_RESUMES + 1):
            message = client.messages.create(
                model=AI_MODEL,
                max_tokens=4096,
                messages=messages,
                **extra
            )
            if getattr(message, "stop_reason", None) != "pause_turn":
                break
            messages = [
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": message.content},
            ]

        return _extract_text_from_content(message.content)

    except ImportError:
        raise ImportError("anthropic package not installed. Run: pip install anthropic")
    except LiveAPICallBlocked:
        raise
    except Exception as e:
        raise _classify_api_exception(e)


def _get_mock_response(prompt: str) -> str:
    """
    Generate mock AI response for testing.
    Parses the prompt to understand context and generates appropriate response.
    """
    import re

    # SR Legacy only prompt
    if "USDA SR Legacy food database" in prompt and "Do NOT search USDA Foundation" in prompt:
        # Extract nutrient name from prompt for more realistic mock
        match = re.search(r"amount of ([^\n]+) in 100g", prompt)
        nutrient_name = match.group(1) if match else "nutrient"

        return json.dumps({
            "recommendation": "sr_legacy",
            "recommended_value": None,
            "justification": f"The SR Legacy value for {nutrient_name} aligns with Japanese MEXT and UK CoFID databases within ±3%.",
            "literature_source": "Cross-validated with MEXT (Japan) and CoFID (UK)",
            "confidence": "high"
        })

    # Both sources prompt (discrepancy)
    if "SR Legacy and Foundation food databases" in prompt or "Discrepancy:" in prompt:
        # Extract discrepancy percentage
        match = re.search(r"Discrepancy: ([\d.]+)%", prompt)
        disc_pct = float(match.group(1)) if match else 10.0

        # Higher discrepancy = lower confidence, prefer Foundation
        if disc_pct > 20:
            return json.dumps({
                "recommendation": "literature",
                "recommended_value": None,
                "justification": "Significant discrepancy between sources. Literature suggests Foundation value is closer to consensus.",
                "literature_source": "FAO/INFOODS and EuroFIR databases",
                "confidence": "medium"
            })
        else:
            return json.dumps({
                "recommendation": "foundation",
                "recommended_value": None,
                "justification": "Foundation Foods uses more recent analytical methods. Value consistent with recent literature.",
                "literature_source": "USDA Foundation Foods (2020+)",
                "confidence": "high"
            })

    # Missing nutrient prompt
    if "not available in either database" in prompt or "Provide your best estimate" in prompt:
        # Extract nutrient name
        match = re.search(r"amount of ([^\n]+) content in 100g", prompt)
        nutrient_name = match.group(1) if match else "nutrient"

        # Taurine is a special case
        if "taurine" in nutrient_name.lower():
            return json.dumps({
                "recommendation": "literature",
                "recommended_value": 50.0,
                "justification": "Taurine content estimated from Spitze et al. (2003) reference data for raw meat sources.",
                "literature_source": "Spitze et al. (2003) J Anim Physiol Anim Nutr",
                "confidence": "medium"
            })

        return json.dumps({
            "recommendation": "literature",
            "recommended_value": 0.05,
            "justification": f"Estimated {nutrient_name} content based on comparative analysis of similar foods in literature.",
            "literature_source": "FAO/INFOODS food composition tables",
            "confidence": "low"
        })

    # Foundation only (uses modified SR Legacy prompt)
    if "Foundation" in prompt and "USDA" in prompt:
        return json.dumps({
            "recommendation": "foundation",
            "recommended_value": None,
            "justification": "Foundation value confirmed by cross-reference with international databases.",
            "literature_source": "Cross-validated with EuroFIR",
            "confidence": "high"
        })

    # Fallback for any other prompt format
    return json.dumps({
        "recommendation": "sr_legacy",
        "recommended_value": None,
        "justification": "Value is consistent with available scientific literature.",
        "literature_source": "General food composition references",
        "confidence": "medium"
    })


def format_ai_suggestion(result: AIValidationResult) -> str:
    """
    Format AI validation result for display in user prompts.

    Args:
        result: AIValidationResult object

    Returns:
        Formatted string for display
    """
    # An error is not an opinion: render it unmistakably differently from "the
    # model had no recommendation" so a hard failure can't be waved through.
    if result.recommendation == "error":
        return f"[!! ERROR] AI validation FAILED — treat as unvalidated: {result.justification}"

    confidence_marker = {
        "high": "[HIGH]",
        "medium": "[MED]",
        "low": "[LOW]",
        "skipped": "[SKIPPED]",
    }.get(result.confidence, "[???]")

    if result.recommendation == "insufficient_data":
        return (
            f"{confidence_marker} AI: insufficient data — no reliable literature "
            f"value found: {result.justification}"
        )

    if result.recommendation == "confirmed_zero":
        return (
            f"{confidence_marker} AI: confirmed zero — nutrient genuinely absent "
            f"from this food: {result.justification}"
        )

    if result.recommendation == "confirmed":
        rec_text = "AI confirms this value"
    elif result.recommendation == "sr_legacy":
        rec_text = "AI recommends: SR Legacy"
    elif result.recommendation == "foundation":
        rec_text = "AI recommends: Foundation"
    elif result.recommendation == "estimate":
        # Compare against None, not truthiness: a recommended value of 0 is a real
        # answer ("this nutrient is genuinely absent") and must still be shown.
        value_text = (
            f" ({result.recommended_value})"
            if result.recommended_value is not None else ""
        )
        rec_text = f"AI estimate{value_text}"
    elif result.recommendation == "literature":
        value_text = (
            f" ({result.recommended_value})"
            if result.recommended_value is not None else ""
        )
        rec_text = f"AI suggests literature value{value_text}"
    else:
        rec_text = "AI: No recommendation"

    return f"{confidence_marker} {rec_text}: {result.justification}"


# =============================================================================
# Per-Nutrient Validation (Phase 1)
# =============================================================================

def call_claude_api_with_retry(
    prompt: str,
    api_key: Optional[str] = None,
    schema: Optional[dict] = None,
) -> str:
    """
    Call Claude API with retry logic and exponential backoff.

    Args:
        prompt: The prompt to send
        api_key: Anthropic API key (uses env var if not provided)
        schema: JSON schema for structured outputs

    Returns:
        API response text

    Raises:
        AIValidationError: After all retries exhausted
    """
    if MOCK_MODE:
        return _get_mock_response(prompt)

    last_error = None

    for attempt in range(AI_MAX_RETRIES):
        try:
            return call_claude_api(prompt, api_key, schema)
        except LiveAPICallBlocked:
            # A permission refusal is not a transient API failure. It subclasses
            # RuntimeError, so without this clause the loop below would retry it
            # five times and burn ~60s of backoff before surfacing it — and would
            # disguise a policy decision as an API error.
            raise
        except NonRetryableAPIError:
            # Typed by _classify_api_exception: a 4xx will fail identically on
            # every retry.
            raise
        except RuntimeError as e:
            last_error = e

            # Exponential backoff
            if attempt < AI_MAX_RETRIES - 1:
                delay = AI_RETRY_BASE_DELAY * (2 ** attempt)
                time.sleep(delay)

    raise AIValidationError(f"API call failed after {AI_MAX_RETRIES} attempts: {last_error}")


def _extract_json_from_response(response: str) -> dict:
    """
    Extract JSON from AI response that may contain text before/after JSON.

    Handles:
    - Pure JSON responses
    - JSON wrapped in markdown code blocks (```json ... ```)
    - JSON embedded in explanatory text

    Args:
        response: Raw AI response text

    Returns:
        Parsed dict from JSON

    Raises:
        json.JSONDecodeError: If no valid JSON found
    """
    import re

    # First try: parse as pure JSON
    try:
        return json.loads(response.strip())
    except json.JSONDecodeError:
        pass

    # Second try: extract from markdown code block
    code_block_pattern = r'```(?:json)?\s*(\{[\s\S]*?\})\s*```'
    match = re.search(code_block_pattern, response)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # No brace-slicing heuristic: structured outputs make the live response
    # pure JSON, and slicing first-{ to last-} mis-parsed prose braces. A
    # response that fails both parses above is a parse failure, full stop.
    raise json.JSONDecodeError("No valid JSON found in response", response, 0)


def _coerce_recommended_value(raw: object) -> tuple[Optional[float], bool]:
    """
    Coerce the model's recommended_value to a float.

    Returns (value, ok). ok is False when a non-null value could not be read
    as a number ("trace", "50 mg") — the caller downgrades confidence so a
    unit-bearing string can't ride into the database on a HIGH result, where
    a g/mg confusion would be a silent 1000x error.
    """
    if raw is None:
        return None, True
    if isinstance(raw, bool):
        return None, False
    if isinstance(raw, (int, float)):
        value = float(raw)
    elif isinstance(raw, str):
        try:
            value = float(raw.strip())
        except ValueError:
            return None, False
    else:
        return None, False
    # float() accepts "nan"/"inf"; neither is a usable nutrient amount and a
    # NaN in the database poisons every downstream comparison silently.
    if not math.isfinite(value):
        return None, False
    return value, True


def parse_single_response(response: str, nutrient_data: dict) -> AIValidationResult:
    """
    Parse single nutrient AI response into AIValidationResult.

    Args:
        response: Raw AI response text (may contain JSON with surrounding text)
        nutrient_data: Original nutrient data for context

    Returns:
        AIValidationResult object
    """
    try:
        parsed = _extract_json_from_response(response)

        value, value_ok = _coerce_recommended_value(parsed.get("recommended_value"))
        confidence = parsed.get("confidence", "low")
        justification = parsed.get("justification", "")
        if not value_ok:
            confidence = "low"
            justification = (
                f"{justification} [non-numeric recommended_value "
                f"{parsed.get('recommended_value')!r} discarded]"
            ).strip()

        recommendation = parsed.get("recommendation", "unknown")
        if recommendation == "confirmed_zero" and value is None:
            # confirmed_zero IS the value: the model asserts genuine absence,
            # which must map to 0.0, never to null/unknown.
            value = 0.0

        return AIValidationResult(
            nutrient_id=nutrient_data.get("nutrient_id"),
            nutrient_name=nutrient_data.get("nutrient_name", "Unknown"),
            prompt_type=nutrient_data.get("prompt_type", "unknown"),
            recommendation=recommendation,
            recommended_value=value,
            justification=justification,
            literature_source=parsed.get("literature_source", ""),
            confidence=confidence
        )

    except json.JSONDecodeError:
        return AIValidationResult(
            nutrient_id=nutrient_data.get("nutrient_id"),
            nutrient_name=nutrient_data.get("nutrient_name", "Unknown"),
            prompt_type=nutrient_data.get("prompt_type", "unknown"),
            recommendation="error",
            recommended_value=None,
            justification=f"Failed to parse AI response: {response[:100]}...",
            literature_source="",
            confidence="low"
        )


def _build_prompt(
    food_name: str,
    nutrient_data: dict,
    food_info: Optional[dict] = None,
) -> str:
    """
    Build the prompt for a nutrient, dispatching on prompt_type.

    Shared by the sync and async validators so the two cannot drift. A peer
    block precomputed by the caller (plan 3.2) is appended verbatim.

    Raises:
        AIValidationError: On unknown prompt type.
    """
    prompt = _build_prompt_body(food_name, nutrient_data, food_info)
    return prompt + nutrient_data.get("peer_block", "") + _search_directive()


def _build_prompt_body(
    food_name: str,
    nutrient_data: dict,
    food_info: Optional[dict] = None,
) -> str:
    """Prompt text without the peer-cohort block."""
    prompt_type = nutrient_data.get("prompt_type")
    nutrient_name = nutrient_data.get("nutrient_name", "Unknown")
    unit = nutrient_data.get("unit", "")

    if prompt_type == "sr_only":
        return build_prompt_sr_only(
            food_name=food_name,
            nutrient_name=nutrient_name,
            sr_value=nutrient_data.get("sr_value", 0),
            unit=unit,
            metadata=nutrient_data.get("sr_metadata", {}),
            food_info=food_info,
        )
    if prompt_type == "both_sources":
        return build_prompt_both_sources(
            food_name=food_name,
            nutrient_name=nutrient_name,
            sr_value=nutrient_data.get("sr_value", 0),
            foundation_value=nutrient_data.get("foundation_value", 0),
            unit=unit,
            discrepancy_percent=nutrient_data.get("discrepancy_percent", 0),
            sr_metadata=nutrient_data.get("sr_metadata", {}),
            foundation_metadata=nutrient_data.get("foundation_metadata", {}),
            food_info=food_info,
        )
    if prompt_type == "missing":
        return build_prompt_missing(
            food_name=food_name,
            nutrient_name=nutrient_name,
            unit=unit,
            food_info=food_info,
        )
    if prompt_type == "foundation_only":
        return build_prompt_foundation_only(
            food_name=food_name,
            nutrient_name=nutrient_name,
            foundation_value=nutrient_data.get("foundation_value", 0),
            unit=unit,
            metadata=nutrient_data.get("foundation_metadata", {}),
            food_info=food_info,
        )
    raise AIValidationError(f"Unknown prompt type: {prompt_type}")


def validate_nutrient_single(
    food_name: str,
    nutrient_data: dict,
    api_key: Optional[str] = None,
    food_info: Optional[dict] = None
) -> AIValidationResult:
    """
    Validate a single nutrient using AI.

    Args:
        food_name: Name of the food item
        nutrient_data: Dict containing nutrient info:
            - nutrient_id: USDA nutrient ID
            - nutrient_name: Name of the nutrient
            - unit: Unit of measurement
            - prompt_type: "sr_only", "both_sources", "missing", "foundation_only"
            - sr_value: SR Legacy value (if applicable)
            - foundation_value: Foundation value (if applicable)
            - discrepancy_percent: Discrepancy percentage (for both_sources)
            - sr_metadata: SR Legacy metadata dict
            - foundation_metadata: Foundation metadata dict
        api_key: Anthropic API key (uses env var if not provided)
        food_info: Optional food identity dict (species, cooking method, FDC IDs)

    Returns:
        AIValidationResult object
    """
    prompt = _build_prompt(food_name, nutrient_data, food_info)
    schema = _response_schema(nutrient_data["prompt_type"])

    # Self-consistency sampling (plan 4.1); N defaults to 1.
    samples = []
    for _ in range(max(1, AI_SELF_CONSISTENCY_SAMPLES)):
        response = call_claude_api_with_retry(prompt, api_key, schema)
        samples.append(parse_single_response(response, nutrient_data))

    return reconcile_samples(samples)


def should_skip_validation(nutrient_data: dict) -> tuple[bool, str]:
    """
    Determine if AI validation can be skipped for this nutrient.

    Smart skipping: Skip when SR Legacy and Foundation values match closely (<5%).

    Args:
        nutrient_data: Nutrient data dict

    Returns:
        Tuple of (should_skip: bool, reason: str)
    """
    prompt_type = nutrient_data.get("prompt_type")

    # Can only skip when both sources are available and match
    if prompt_type == "match":
        sr_value = nutrient_data.get("sr_value")
        foundation_value = nutrient_data.get("foundation_value")

        if sr_value is not None and foundation_value is not None:
            # Calculate percentage difference
            if sr_value == 0 and foundation_value == 0:
                diff_percent = 0.0
            elif sr_value == 0 or foundation_value == 0:
                diff_percent = 100.0
            else:
                avg = (sr_value + foundation_value) / 2
                diff_percent = abs(sr_value - foundation_value) / avg * 100

            if diff_percent < SKIP_VALIDATION_THRESHOLD:
                return True, f"SR/Foundation match within {diff_percent:.1f}% - using Foundation value"

    return False, ""


def create_skipped_result(nutrient_data: dict, skip_reason: str) -> AIValidationResult:
    """
    Create an AIValidationResult for a skipped nutrient.

    Args:
        nutrient_data: Nutrient data dict
        skip_reason: Reason for skipping validation

    Returns:
        AIValidationResult with skipped status
    """
    return AIValidationResult(
        nutrient_id=nutrient_data.get("nutrient_id"),
        nutrient_name=nutrient_data.get("nutrient_name", "Unknown"),
        prompt_type="skipped",
        recommendation="foundation",  # Use Foundation when SR/Foundation match
        recommended_value=None,
        justification=skip_reason,
        literature_source="USDA Foundation (auto-selected - values match)",
        # NOT "high": this nutrient was never sent to the AI. Stamping "high"
        # made ai_confidence='high' mean either "the model was confident" or
        # "we never asked", so any query filtering on it swept in unvalidated
        # rows. "skipped" is a distinct, queryable state.
        confidence="skipped"
    )


def attach_peer_medians(
    nutrients_data: list[dict],
    food_info: Optional[dict],
) -> None:
    """
    Attach a local peer-cohort block to each nutrient, in place.

    Computed in one dataset scan for the whole food (plan 3.2). Best-effort:
    the bulk datasets are gitignored and may be absent, and a missing peer
    block only means the prompt carries less evidence — never a failed
    validation.
    """
    if not food_info:
        return
    species = food_info.get("protein_species")
    if not species:
        return

    nutrient_ids = [
        nid for nid in (n.get("nutrient_id") for n in nutrients_data)
        if nid is not None
    ]
    if not nutrient_ids:
        return

    try:
        import peer_median

        # Cohort state comes from the food NAME, not the cooking_method column:
        # ingredients are entered raw and cooking is adjusted for downstream, so
        # that column describes later preparation. Using it would pool cooked
        # peers against a raw value, and cooking concentrates nutrients per 100 g.
        medians = peer_median.compute_peer_medians(
            nutrient_ids, species, food_info.get("food_name", "")
        )
    except Exception as exc:  # noqa: BLE001 - evidence is optional, never fatal
        print(f"  WARNING: peer medians unavailable ({exc}); prompts will omit them")
        return

    for nutrient in nutrients_data:
        peer = medians.get(nutrient.get("nutrient_id"))
        if peer is not None:
            nutrient["peer_block"] = peer_median.format_peer_median(peer)


def reconcile_samples(samples: list[AIValidationResult]) -> AIValidationResult:
    """
    Reduce N self-consistency samples to one result (plan 4.1).

    Takes the median of the numeric answers and treats material disagreement
    between samples as the escalation signal — a measured confidence, rather
    than the model's uncalibrated self-report. Confidence is only ever lowered
    here, never raised: agreement across samples is not proof of correctness.

    A single sample passes through unchanged.
    """
    if not samples:
        raise ValueError("reconcile_samples requires at least one sample")
    if len(samples) == 1:
        return samples[0]

    usable = [s for s in samples if s.recommendation not in ("error", "unknown")]
    if not usable:
        return samples[0]

    # Majority recommendation; ties resolve to the first sample's, which keeps
    # the reduction deterministic.
    counts: dict[str, int] = {}
    for sample in usable:
        counts[sample.recommendation] = counts.get(sample.recommendation, 0) + 1
    top_count = max(counts.values())
    winners = [r for r, c in counts.items() if c == top_count]
    recommendation = (
        usable[0].recommendation if usable[0].recommendation in winners else winners[0]
    )

    agreeing = [s for s in usable if s.recommendation == recommendation]
    values = [s.recommended_value for s in agreeing if s.recommended_value is not None]

    value: Optional[float] = None
    spread: Optional[float] = None
    if values:
        value = float(statistics.median(values))
        if len(values) > 1 and value != 0:
            spread = (max(values) - min(values)) / abs(value)
        elif len(values) > 1:
            spread = 0.0 if max(values) == min(values) else float("inf")

    # Confidence is the weakest of: the samples' own agreement, the numeric
    # spread, and the lowest self-reported confidence among agreeing samples.
    order = ["low", "medium", "high"]
    reported = min(
        (s.confidence for s in agreeing if s.confidence in order),
        key=order.index,
        default="low",
    )
    confidence = reported
    notes = []
    if len(agreeing) < len(usable):
        confidence = "low"
        notes.append(
            f"samples disagreed on recommendation ({len(agreeing)}/{len(usable)} agreed)"
        )
    if values and len(values) < len(agreeing):
        # Some samples produced a number and others abstained. That is a
        # material disagreement about whether the value is knowable at all,
        # even though the recommendation label matched.
        confidence = "low"
        notes.append(
            f"{len(agreeing) - len(values)}/{len(agreeing)} agreeing samples "
            "returned no value"
        )
    if spread is not None and spread > AI_SELF_CONSISTENCY_MAX_SPREAD:
        confidence = "low"
        notes.append(f"sample spread {spread:.0%} exceeds {AI_SELF_CONSISTENCY_MAX_SPREAD:.0%}")

    base = agreeing[0]
    justification = base.justification
    suffix = f" [self-consistency over {len(samples)} samples"
    suffix += f"; {'; '.join(notes)}" if notes else "; samples agreed"
    suffix += "]"

    return AIValidationResult(
        nutrient_id=base.nutrient_id,
        nutrient_name=base.nutrient_name,
        prompt_type=base.prompt_type,
        recommendation=recommendation,
        recommended_value=value,
        justification=f"{justification}{suffix}",
        literature_source=base.literature_source,
        confidence=confidence,
    )


def _store_result(
    results_dict: dict[int, AIValidationResult],
    nutrient_id: Optional[int],
    nutrient_name: str,
    result: AIValidationResult,
) -> None:
    """
    Store a validation result keyed by nutrient_id.

    Results are keyed by ID only (see the validators' return annotations) and
    every consumer looks up by ID, so a result with no ID has no reader —
    drop it loudly rather than storing it under a name nobody reads.
    """
    if nutrient_id is None:
        print(
            f"  WARNING: dropping AI result for '{nutrient_name}': "
            "no nutrient_id to key it by"
        )
        return
    results_dict[nutrient_id] = result


def describe_auto_accept_disagreement(
    result: Optional[AIValidationResult],
    written_source: str,
) -> Optional[str]:
    """
    Describe an AI/database contradiction on a path that never prompts.

    Matches and Foundation-only nutrients are written without asking the
    operator. When the model recommended something other than the value being
    written, the database silently records a contradiction — `ai_recommendation`
    disagreeing with `source` — with no review trail. This renders that
    disagreement so it can be stored in the row's comment.

    Returns None when there is nothing to record (no result, an error result,
    a skipped nutrient, or agreement).
    """
    if result is None:
        return None
    if result.recommendation in ("error", "unknown"):
        return None
    if result.prompt_type == "skipped":
        return None
    if result.recommendation == written_source:
        return None

    value_text = (
        f" (suggested {result.recommended_value})"
        if result.recommended_value is not None else ""
    )
    return (
        f"AI disagreed: recommended '{result.recommendation}'{value_text} "
        f"at {result.confidence} confidence; wrote '{written_source}' "
        f"(auto-accepted without review)"
    )


def detect_mass_failure(results: dict[int, AIValidationResult]) -> Optional[str]:
    """
    Detect a wholesale validation failure (credits exhausted, outage).

    Counts error results among the results that actually went to the API —
    auto-skipped matches always "succeed", so including them would dilute a
    fully-failed billed set below any threshold.

    Returns:
        A human-readable reason when the error fraction exceeds
        AI_MASS_FAILURE_THRESHOLD (or every non-skipped result failed),
        else None.
    """
    considered = [r for r in results.values() if r.prompt_type != "skipped"]
    if not considered:
        return None
    errors = [r for r in considered if r.recommendation == "error"]
    if not errors:
        return None
    fraction = len(errors) / len(considered)
    if fraction > AI_MASS_FAILURE_THRESHOLD or len(errors) == len(considered):
        return (
            f"{len(errors)} of {len(considered)} non-skipped nutrients failed "
            f"AI validation ({fraction:.0%}). First error: {errors[0].justification}"
        )
    return None


def validate_nutrients_sequential(
    food_name: str,
    comparison_result: dict,
    sr_data: dict,
    foundation_data: Optional[dict],
    missing_nutrients: list[dict],
    api_key: Optional[str] = None,
    verbose: bool = False,
    food_info: Optional[dict] = None
) -> dict[int, AIValidationResult]:
    """
    Validate all nutrients sequentially with rate limiting.

    Args:
        food_name: Name of the food item
        comparison_result: Result from compare_nutrients()
        sr_data: SR Legacy data
        foundation_data: Foundation data (optional)
        missing_nutrients: List of nutrients not in USDA
        api_key: Anthropic API key
        verbose: If True, print progress information

    Returns:
        Dict mapping nutrient_id to AIValidationResult
    """
    nutrients_data = []
    results_dict = {}

    # Collect all nutrients to validate
    # Add matches (< 5% difference) - candidates for skipping
    for match in comparison_result.get("matches", []):
        nutrients_data.append({
            "nutrient_id": match["nutrient_id"],
            "nutrient_name": match["nutrient_name"],
            "unit": match.get("unit", ""),
            "prompt_type": "match",
            "sr_value": match["sr_value"],
            "foundation_value": match["foundation_value"],
            "sr_metadata": match.get("sr_metadata", {}),
            "foundation_metadata": match.get("foundation_metadata", {}),
        })

    # Add discrepancies (>= 5% difference)
    for disc in comparison_result.get("discrepancies", []):
        discrepancy_info = disc.get("discrepancy", {})
        nutrients_data.append({
            "nutrient_id": disc["nutrient_id"],
            "nutrient_name": disc["nutrient_name"],
            "unit": disc.get("unit", ""),
            "prompt_type": "both_sources",
            "sr_value": disc["sr_value"],
            "foundation_value": disc["foundation_value"],
            "discrepancy_percent": discrepancy_info.get("percentage", 0),
            "sr_metadata": disc.get("sr_metadata", {}),
            "foundation_metadata": disc.get("foundation_metadata", {}),
        })

    # Add SR-only nutrients
    for nutrient in comparison_result.get("sr_only", []):
        nutrients_data.append({
            "nutrient_id": nutrient["nutrient_id"],
            "nutrient_name": nutrient["nutrient_name"],
            "unit": nutrient.get("unit", ""),
            "prompt_type": "sr_only",
            "sr_value": nutrient["sr_value"],
            "sr_metadata": nutrient.get("sr_metadata", {}),
        })

    # Add Foundation-only nutrients
    for nutrient in comparison_result.get("foundation_only", []):
        nutrients_data.append({
            "nutrient_id": nutrient["nutrient_id"],
            "nutrient_name": nutrient["nutrient_name"],
            "unit": nutrient.get("unit", ""),
            "prompt_type": "foundation_only",
            "foundation_value": nutrient["foundation_value"],
            "foundation_metadata": nutrient.get("foundation_metadata", {}),
        })

    # Add missing nutrients (not in USDA)
    for nutrient in missing_nutrients:
        nutrients_data.append({
            "nutrient_id": nutrient.get("nutrient_id"),
            "nutrient_name": nutrient["nutrient_name"],
            "unit": nutrient.get("unit", ""),
            "prompt_type": "missing",
        })

    if not nutrients_data:
        return {}

    attach_peer_medians(nutrients_data, food_info)

    total = len(nutrients_data)
    validated_count = 0
    skipped_count = 0
    last_request_time = 0.0

    if verbose:
        print(f"\nValidating {total} nutrients for {food_name}...")

    for i, nutrient_data in enumerate(nutrients_data, 1):
        nutrient_name = nutrient_data.get("nutrient_name", "Unknown")
        nutrient_id = nutrient_data.get("nutrient_id")

        # Check if we can skip validation
        should_skip, skip_reason = should_skip_validation(nutrient_data)

        if should_skip:
            result = create_skipped_result(nutrient_data, skip_reason)
            skipped_count += 1
            if verbose:
                print(f"  [{i}/{total}] {nutrient_name}: SKIPPED - {skip_reason}")
        else:
            # Rate limiting - ensure minimum interval between requests
            if not MOCK_MODE:
                elapsed = time.time() - last_request_time
                if elapsed < AI_MIN_REQUEST_INTERVAL:
                    sleep_time = AI_MIN_REQUEST_INTERVAL - elapsed
                    time.sleep(sleep_time)

            if verbose:
                print(f"  [{i}/{total}] {nutrient_name}: Validating...", end="", flush=True)

            try:
                result = validate_nutrient_single(food_name, nutrient_data, api_key, food_info)
                validated_count += 1
                last_request_time = time.time()

                if verbose:
                    print(f" {result.confidence.upper()} - {result.recommendation}")

            except AIValidationError as e:
                result = AIValidationResult(
                    nutrient_id=nutrient_id,
                    nutrient_name=nutrient_name,
                    prompt_type=nutrient_data.get("prompt_type", "unknown"),
                    recommendation="error",
                    recommended_value=None,
                    justification=str(e),
                    literature_source="",
                    confidence="low"
                )
                if verbose:
                    print(f" ERROR: {e}")

        _store_result(results_dict, nutrient_id, nutrient_name, result)

    if verbose:
        print(f"\nValidation complete: {validated_count} validated, {skipped_count} skipped")

    return results_dict


# =============================================================================
# Async Concurrent Validation (Phase 2)
# =============================================================================

class _AsyncRateLimiter:
    """
    Async-safe rate limiter to enforce minimum interval between requests.

    Uses asyncio.Lock to ensure thread-safety in async context.
    """

    def __init__(self, min_interval: float):
        """
        Args:
            min_interval: Minimum seconds between requests
        """
        self._min_interval = min_interval
        self._last_request_time = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """
        Wait until it's safe to make a request.
        Ensures minimum interval between requests across all concurrent tasks.
        """
        async with self._lock:
            now = time.time()
            elapsed = now - self._last_request_time
            if elapsed < self._min_interval:
                wait_time = self._min_interval - elapsed
                await asyncio.sleep(wait_time)
            self._last_request_time = time.time()


async def _call_claude_api_async(
    prompt: str,
    client,  # anthropic.AsyncAnthropic
    semaphore: asyncio.Semaphore,
    rate_limiter: _AsyncRateLimiter,
    schema: Optional[dict] = None
) -> str:
    """
    Async version of Claude API call with semaphore-controlled concurrency.

    Args:
        prompt: The prompt to send
        client: AsyncAnthropic client instance (shared)
        semaphore: Semaphore to limit concurrent requests
        rate_limiter: Rate limiter to enforce minimum request interval
        schema: JSON schema for structured outputs

    Returns:
        API response text
    """
    if MOCK_MODE:
        # Small delay to simulate API latency for realistic testing
        await asyncio.sleep(0.05)
        return _get_mock_response(prompt)

    async with semaphore:
        await rate_limiter.acquire()

        extra: dict = {}
        if schema is not None:
            extra["output_config"] = {
                "format": {"type": "json_schema", "schema": schema}
            }
        tools = _web_search_tools()
        if tools:
            extra["tools"] = tools

        messages: list[dict] = [{"role": "user", "content": prompt}]

        # See the sync twin: a paused server-tool turn is resumed by re-sending.
        for _ in range(AI_MAX_PAUSE_RESUMES + 1):
            message = await client.messages.create(
                model=AI_MODEL,
                max_tokens=4096,
                messages=messages,
                **extra
            )
            if getattr(message, "stop_reason", None) != "pause_turn":
                break
            messages = [
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": message.content},
            ]

        return _extract_text_from_content(message.content)


async def _call_claude_api_async_with_retry(
    prompt: str,
    client,  # anthropic.AsyncAnthropic
    semaphore: asyncio.Semaphore,
    rate_limiter: _AsyncRateLimiter,
    schema: Optional[dict] = None
) -> str:
    """
    Async API call with exponential backoff retry logic.

    Args:
        prompt: The prompt to send
        client: AsyncAnthropic client instance
        semaphore: Semaphore for concurrency control
        rate_limiter: Rate limiter for request pacing
        schema: JSON schema for structured outputs

    Returns:
        API response text

    Raises:
        AIValidationError: After all retries exhausted
    """
    if MOCK_MODE:
        return await _call_claude_api_async(prompt, client, semaphore, rate_limiter, schema)

    last_error = None

    for attempt in range(AI_MAX_RETRIES):
        try:
            return await _call_claude_api_async(prompt, client, semaphore, rate_limiter, schema)
        except LiveAPICallBlocked:
            # See the sync twin: permission refusals must not be retried.
            raise
        except NonRetryableAPIError:
            # See the sync twin: a 4xx fails identically on every retry.
            raise
        except Exception as e:
            last_error = e

            # Exponential backoff
            if attempt < AI_MAX_RETRIES - 1:
                delay = AI_RETRY_BASE_DELAY * (2 ** attempt)
                await asyncio.sleep(delay)

    raise AIValidationError(f"API call failed after {AI_MAX_RETRIES} attempts: {last_error}")


async def _validate_nutrient_async(
    food_name: str,
    nutrient_data: dict,
    client,  # anthropic.AsyncAnthropic
    semaphore: asyncio.Semaphore,
    rate_limiter: _AsyncRateLimiter,
    food_info: Optional[dict] = None
) -> AIValidationResult:
    """
    Validate a single nutrient using async AI call.

    Args:
        food_name: Name of the food item
        nutrient_data: Dict containing nutrient info
        client: AsyncAnthropic client instance
        semaphore: Semaphore for concurrency control
        rate_limiter: Rate limiter for request pacing
        food_info: Optional food identity dict (species, cooking method, FDC IDs)

    Returns:
        AIValidationResult object
    """
    nutrient_name = nutrient_data.get("nutrient_name", "Unknown")
    nutrient_id = nutrient_data.get("nutrient_id")

    try:
        # Prompt building shares _build_prompt with the sync validator; an
        # unknown prompt type raises AIValidationError and lands in the same
        # error-result branch as an API failure.
        prompt = _build_prompt(food_name, nutrient_data, food_info)
        schema = _response_schema(nutrient_data["prompt_type"])

        # Self-consistency sampling (plan 4.1): N samples, reconciled to one
        # result whose confidence is measured rather than self-reported.
        # AI_SELF_CONSISTENCY_SAMPLES defaults to 1, so this is a single call
        # unless explicitly enabled.
        samples = []
        for _ in range(max(1, AI_SELF_CONSISTENCY_SAMPLES)):
            response = await _call_claude_api_async_with_retry(
                prompt, client, semaphore, rate_limiter, schema
            )
            samples.append(parse_single_response(response, nutrient_data))

        return reconcile_samples(samples)

    except AIValidationError as e:
        return AIValidationResult(
            nutrient_id=nutrient_id,
            nutrient_name=nutrient_name,
            prompt_type=nutrient_data.get("prompt_type") or "unknown",
            recommendation="error",
            recommended_value=None,
            justification=str(e),
            literature_source="",
            confidence="low"
        )


async def _validate_nutrients_async(
    food_name: str,
    nutrients_data: list[dict],
    api_key: Optional[str] = None,
    concurrent_limit: int = AI_CONCURRENT_LIMIT,
    verbose: bool = False,
    food_info: Optional[dict] = None
) -> dict[int, AIValidationResult]:
    """
    Internal async function to validate nutrients concurrently.

    Args:
        food_name: Name of the food item
        nutrients_data: List of nutrient data dicts to validate
        api_key: Anthropic API key
        concurrent_limit: Max concurrent requests
        verbose: Print progress information

    Returns:
        Dict mapping nutrient_id to AIValidationResult
    """
    if not nutrients_data:
        return {}

    results_dict = {}
    validated_count = 0
    skipped_count = 0

    # Separate nutrients into skippable and those needing validation
    to_validate = []
    for nutrient_data in nutrients_data:
        nutrient_name = nutrient_data.get("nutrient_name", "Unknown")
        nutrient_id = nutrient_data.get("nutrient_id")

        # Check if we can skip validation
        should_skip, skip_reason = should_skip_validation(nutrient_data)

        if should_skip:
            result = create_skipped_result(nutrient_data, skip_reason)
            skipped_count += 1
            if verbose:
                print(f"  SKIPPED: {nutrient_name} - {skip_reason}")

            _store_result(results_dict, nutrient_id, nutrient_name, result)
        else:
            to_validate.append(nutrient_data)

    if verbose and to_validate:
        print(f"\nValidating {len(to_validate)} nutrients concurrently (limit={concurrent_limit})...")

    if not to_validate:
        if verbose:
            print(f"\nValidation complete: {validated_count} validated, {skipped_count} skipped")
        return results_dict

    # Create async resources
    semaphore = asyncio.Semaphore(concurrent_limit)
    rate_limiter = _AsyncRateLimiter(AI_MIN_REQUEST_INTERVAL)

    # Create client
    if MOCK_MODE:
        client = None  # Not needed in mock mode
    else:
        assert_live_ai_calls_allowed()
        try:
            import anthropic
            key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
            if not key:
                raise AIValidationError("No Anthropic API key provided")
            # max_retries=0: see the sync client — this module owns retries.
            client = anthropic.AsyncAnthropic(api_key=key, max_retries=0)
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")

    try:
        # Create tasks for all nutrients
        tasks = [
            _validate_nutrient_async(
                food_name, nutrient_data, client, semaphore, rate_limiter, food_info
            )
            for nutrient_data in to_validate
        ]

        # Run all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for nutrient_data, result in zip(to_validate, results):
            nutrient_name = nutrient_data.get("nutrient_name", "Unknown")
            nutrient_id = nutrient_data.get("nutrient_id")

            if isinstance(result, Exception):
                # Create error result for failed task
                error_result = AIValidationResult(
                    nutrient_id=nutrient_id,
                    nutrient_name=nutrient_name,
                    prompt_type=nutrient_data.get("prompt_type", "unknown"),
                    recommendation="error",
                    recommended_value=None,
                    justification=f"Concurrent validation error: {str(result)}",
                    literature_source="",
                    confidence="low"
                )
                if verbose:
                    print(f"  ERROR: {nutrient_name} - {str(result)}")

                _store_result(results_dict, nutrient_id, nutrient_name, error_result)
            else:
                validated_count += 1
                if verbose:
                    print(f"  {result.confidence.upper()}: {nutrient_name} - {result.recommendation}")

                _store_result(results_dict, nutrient_id, nutrient_name, result)

    finally:
        # Clean up client if needed
        if client is not None and hasattr(client, 'close'):
            await client.close()

    if verbose:
        print(f"\nValidation complete: {validated_count} validated, {skipped_count} skipped")

    return results_dict


def validate_nutrients_concurrent(
    food_name: str,
    comparison_result: dict,
    sr_data: dict,
    foundation_data: Optional[dict],
    missing_nutrients: list[dict],
    api_key: Optional[str] = None,
    concurrent_limit: int = AI_CONCURRENT_LIMIT,
    verbose: bool = False,
    food_info: Optional[dict] = None
) -> dict[int, AIValidationResult]:
    """
    Validate all nutrients concurrently with rate limiting.

    This is a synchronous wrapper around the async implementation.
    Can be called from synchronous code (main.py).

    Args:
        food_name: Name of the food item
        comparison_result: Result from compare_nutrients()
        sr_data: SR Legacy data
        foundation_data: Foundation data (optional)
        missing_nutrients: List of nutrients not in USDA
        api_key: Anthropic API key
        concurrent_limit: Max concurrent requests (default: AI_CONCURRENT_LIMIT)
        verbose: If True, print progress information

    Returns:
        Dict mapping nutrient_id to AIValidationResult

    Note:
        This function has the same signature and return type as
        validate_nutrients_sequential() for drop-in replacement.
    """
    # Validate concurrent_limit
    concurrent_limit = max(1, min(concurrent_limit, AI_MAX_CONCURRENT_LIMIT))

    # Prepare nutrients data (same logic as validate_nutrients_sequential)
    nutrients_data = []

    # Add matches (< 5% difference) - candidates for skipping
    for match in comparison_result.get("matches", []):
        nutrients_data.append({
            "nutrient_id": match["nutrient_id"],
            "nutrient_name": match["nutrient_name"],
            "unit": match.get("unit", ""),
            "prompt_type": "match",
            "sr_value": match["sr_value"],
            "foundation_value": match["foundation_value"],
            "sr_metadata": match.get("sr_metadata", {}),
            "foundation_metadata": match.get("foundation_metadata", {}),
        })

    # Add discrepancies (>= 5% difference)
    for disc in comparison_result.get("discrepancies", []):
        discrepancy_info = disc.get("discrepancy", {})
        nutrients_data.append({
            "nutrient_id": disc["nutrient_id"],
            "nutrient_name": disc["nutrient_name"],
            "unit": disc.get("unit", ""),
            "prompt_type": "both_sources",
            "sr_value": disc["sr_value"],
            "foundation_value": disc["foundation_value"],
            "discrepancy_percent": discrepancy_info.get("percentage", 0),
            "sr_metadata": disc.get("sr_metadata", {}),
            "foundation_metadata": disc.get("foundation_metadata", {}),
        })

    # Add SR-only nutrients
    for nutrient in comparison_result.get("sr_only", []):
        nutrients_data.append({
            "nutrient_id": nutrient["nutrient_id"],
            "nutrient_name": nutrient["nutrient_name"],
            "unit": nutrient.get("unit", ""),
            "prompt_type": "sr_only",
            "sr_value": nutrient["sr_value"],
            "sr_metadata": nutrient.get("sr_metadata", {}),
        })

    # Add Foundation-only nutrients
    for nutrient in comparison_result.get("foundation_only", []):
        nutrients_data.append({
            "nutrient_id": nutrient["nutrient_id"],
            "nutrient_name": nutrient["nutrient_name"],
            "unit": nutrient.get("unit", ""),
            "prompt_type": "foundation_only",
            "foundation_value": nutrient["foundation_value"],
            "foundation_metadata": nutrient.get("foundation_metadata", {}),
        })

    # Add missing nutrients (not in USDA)
    for nutrient in missing_nutrients:
        nutrients_data.append({
            "nutrient_id": nutrient.get("nutrient_id"),
            "nutrient_name": nutrient["nutrient_name"],
            "unit": nutrient.get("unit", ""),
            "prompt_type": "missing",
        })

    if not nutrients_data:
        return {}

    attach_peer_medians(nutrients_data, food_info)

    if verbose:
        print(f"\nValidating {len(nutrients_data)} nutrients for {food_name} (concurrent)...")

    # Run the async function
    return asyncio.run(_validate_nutrients_async(
        food_name=food_name,
        nutrients_data=nutrients_data,
        api_key=api_key,
        concurrent_limit=concurrent_limit,
        verbose=verbose,
        food_info=food_info
    ))
