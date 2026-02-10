"""
AI-powered literature validation for nutrition data.

Uses Claude AI to validate nutrient values against scientific literature
and provide recommendations for discrepancies.
"""
import asyncio
import json
import os
import time
from typing import Optional
from dataclasses import dataclass

from config import (
    AI_RATE_LIMIT_RPM,
    AI_MIN_REQUEST_INTERVAL,
    AI_MAX_RETRIES,
    AI_RETRY_BASE_DELAY,
    SKIP_VALIDATION_THRESHOLD,
    AI_CONCURRENT_LIMIT,
    AI_MAX_CONCURRENT_LIMIT,
    AI_MOCK_MODE,
)


# Mock mode flag - imported from config (default: False = real API calls)
MOCK_MODE = AI_MOCK_MODE


class AIValidationError(Exception):
    """Exception raised for AI validation errors."""
    pass


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


def build_prompt_sr_only(
    food_name: str,
    nutrient_name: str,
    sr_value: float,
    unit: str,
    metadata: dict
) -> str:
    """
    Build prompt for nutrients only available in SR Legacy.
    Asks AI to validate against independent sources (not SR Legacy-derived).
    """
    sample_date = metadata.get("year_acquired", "unknown")

    return f"""You are a cat food nutrition science expert. The following is the amount of {nutrient_name} in 100g of {food_name} and was obtained from USDA SR Legacy food database. Search valid scientific resources to confirm or revise this value for cat food formulation.

INPUT:
- Nutrient: {nutrient_name}
- Value: {sr_value} {unit}/100g
- Sample Date: {sample_date}

RULES:
1. Do NOT use USDA SR Legacy or SR Legacy-derived sources as validation—this is the source being evaluated
2. Search ONLY scientific literature, peer-reviewed studies, and established food composition databases to confirm or estimate a value.
3. Do NOT search USDA Foundation—this nutrient is not available in that database

PRIORITY SOURCES:
- National DBs: Japanese MEXT, UK CoFID, Australian AFCD, Canadian CNF, German BLS, Danish DTU, Dutch NEVO, French CIQUAL
- International: FAO/INFOODS, EuroFIR
- Journals (2015+): J Food Comp Anal, Food Chemistry, J Agric Food Chem, Br J Nutr
- Pet nutrition: NRC 2006, J Anim Physiol Anim Nutr

CONFIDENCE CRITERIA:
- high: Multiple independent sources agree within ±5% of SR Legacy value
- medium: Sources vary 5-30% from SR Legacy value, report median
- low: >30% variance, limited data, or no clear consensus

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
    metadata: dict
) -> str:
    """
    Build prompt for nutrients only available in Foundation.
    Asks AI to validate against independent sources (not Foundation-derived).
    """
    sample_date = metadata.get("year_acquired", "unknown")

    return f"""You are a cat food nutrition science expert. The following is the amount of {nutrient_name} in 100g of {food_name} and was obtained from USDA Foundation food database. Search valid scientific resources to confirm or revise this value for cat food formulation.

INPUT:
- Nutrient: {nutrient_name}
- Value: {foundation_value} {unit}/100g
- Sample Date: {sample_date}

RULES:
1. Do NOT use USDA Foundation or Foundation-derived sources as validation—this is the source being evaluated
2. Search ONLY scientific literature, peer-reviewed studies, and established food composition databases to confirm or estimate a value.
3. Do NOT search USDA SR Legacy—this nutrient is not available in that database

PRIORITY SOURCES:
- National DBs: Japanese MEXT, UK CoFID, Australian AFCD, Canadian CNF, German BLS, Danish DTU, Dutch NEVO, French CIQUAL
- International: FAO/INFOODS, EuroFIR
- Journals (2015+): J Food Comp Anal, Food Chemistry, J Agric Food Chem, Br J Nutr
- Pet nutrition: NRC 2006, J Anim Physiol Anim Nutr

CONFIDENCE CRITERIA:
- high: Multiple independent sources agree within ±5% of Foundation value
- medium: Sources vary 5-30% from Foundation value, report median
- low: >30% variance, limited data, or no clear consensus

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
    foundation_metadata: dict
) -> str:
    """
    Build prompt for nutrients available in both sources with discrepancy.
    Asks AI which value is more supported by independent literature.
    """
    sr_year = sr_metadata.get("year_acquired", "unknown")
    found_year = foundation_metadata.get("year_acquired", "unknown")

    return f"""You are a cat food nutrition science expert. The followings are the amout of {nutrient_name} in 100g of {food_name} and were obtained from USDA SR Legacy and Foundation food databases. Search valid scientific resources to confirm which value is more accurate or estimate a new value. This is for cat food formulation (FEDIAF 2025 compliance).

INPUT:
- Nutrient: {nutrient_name}
- SR Legacy: {sr_value} {unit}/100g (Sampled: {sr_year})
- Foundation: {foundation_value} {unit}/100g (Sampled: {found_year})
- Discrepancy: {discrepancy_percent:.1f}%

RULES:
1. Do NOT use USDA SR Legacy or USDA Foundation as validation—these are the sources being evaluated
2. Search ONLY scientific literature, peer-reviewed studies, and established food composition databases to estimate a value.

PRIORITY SOURCES:
- National DBs: Japanese MEXT, UK CoFID, Australian AFCD, Canadian CNF, German BLS, Danish DTU, Dutch NEVO, French CIQUAL
- International: FAO/INFOODS, EuroFIR
- Journals (2015+): J Food Comp Anal, Food Chemistry, J Agric Food Chem, Br J Nutr
- Pet nutrition: NRC 2006, J Anim Physiol Anim Nutr

CONFIDENCE CRITERIA:
- high: Multiple independent sources agree within ±5% of selected value
- medium: Sources vary 5-30%, selected value is median or best supported
- low: >30% variance, limited data, or no clear consensus

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
    unit: str
) -> str:
    """
    Build prompt for nutrients missing from both USDA sources.
    Asks AI to estimate the value based on literature.
    """
    return f"""You are a cat food nutrition science expert. Provide your best estimate for the amount of {nutrient_name} content in 100g of {food_name} for cat food formulation (FEDIAF 2025 compliance).

INPUT:
- Ingredient: {food_name}
- Nutrient: {nutrient_name}
- Unit: {unit}/100g

RULES:
1. Do NOT search USDA SR Legacy or USDA Foundation—this nutrient is not available in either database
2. Search ONLY scientific literature, peer-reviewed studies, and established food composition databases to estimate a value.

PRIORITY SOURCES:
- National DBs: Japanese MEXT, UK CoFID, Australian AFCD, Canadian CNF, German BLS, Danish DTU, Dutch NEVO, French CIQUAL
- International: FAO/INFOODS, EuroFIR
- Journals (2015+): J Food Comp Anal, Food Chemistry, J Agric Food Chem, Br J Nutr
- Pet nutrition: NRC 2006, J Anim Physiol Anim Nutr

CONFIDENCE CRITERIA:
- high: Multiple independent sources agree within ±5%
- medium: Sources vary 5-30%, value is median or best supported
- low: >30% variance, limited data, or no clear consensus

Respond in this exact JSON format:
{{
    "recommendation": "literature" or "insufficient_data",
    "recommended_value": <number or null if insufficient data>,
    "justification": "<2 sentences explaining your reasoning>",
    "literature_source": "<citation or 'No reliable sources found' if insufficient data>",
    "confidence": "high" or "medium" or "low"
}}"""


def call_claude_api(prompt: str, api_key: Optional[str] = None) -> str:
    """
    Call Claude API with the given prompt.

    Args:
        prompt: The prompt to send
        api_key: Anthropic API key (uses env var if not provided)

    Returns:
        API response text
    """
    if MOCK_MODE:
        return _get_mock_response(prompt)

    # Real API call
    try:
        import anthropic

        key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        if not key:
            raise ValueError("No Anthropic API key provided")

        client = anthropic.Anthropic(api_key=key)

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return message.content[0].text

    except ImportError:
        raise ImportError("anthropic package not installed. Run: pip install anthropic")
    except Exception as e:
        raise RuntimeError(f"Claude API error: {str(e)}")


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
    confidence_marker = {
        "high": "[HIGH]",
        "medium": "[MED]",
        "low": "[LOW]"
    }.get(result.confidence, "[???]")

    if result.recommendation == "confirmed":
        rec_text = "AI confirms this value"
    elif result.recommendation == "sr_legacy":
        rec_text = "AI recommends: SR Legacy"
    elif result.recommendation == "foundation":
        rec_text = "AI recommends: Foundation"
    elif result.recommendation == "estimate":
        value_text = f" ({result.recommended_value})" if result.recommended_value else ""
        rec_text = f"AI estimate{value_text}"
    elif result.recommendation == "literature":
        value_text = f" ({result.recommended_value})" if result.recommended_value else ""
        rec_text = f"AI suggests literature value{value_text}"
    else:
        rec_text = "AI: No recommendation"

    return f"{confidence_marker} {rec_text}: {result.justification}"


# =============================================================================
# Per-Nutrient Validation (Phase 1)
# =============================================================================

def call_claude_api_with_retry(prompt: str, api_key: Optional[str] = None) -> str:
    """
    Call Claude API with retry logic and exponential backoff.

    Args:
        prompt: The prompt to send
        api_key: Anthropic API key (uses env var if not provided)

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
            return call_claude_api(prompt, api_key)
        except RuntimeError as e:
            last_error = e
            error_msg = str(e).lower()

            # Don't retry on non-retryable errors
            if "invalid" in error_msg or "api key" in error_msg:
                raise AIValidationError(f"Non-retryable error: {e}")

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

    # Third try: find JSON object in text (look for { ... })
    # Find the first { and last } to extract the JSON object
    first_brace = response.find('{')
    last_brace = response.rfind('}')

    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        json_str = response[first_brace:last_brace + 1]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass

    # If all attempts fail, raise error
    raise json.JSONDecodeError("No valid JSON found in response", response, 0)


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

        return AIValidationResult(
            nutrient_id=nutrient_data.get("nutrient_id"),
            nutrient_name=nutrient_data.get("nutrient_name", "Unknown"),
            prompt_type=nutrient_data.get("prompt_type", "unknown"),
            recommendation=parsed.get("recommendation", "unknown"),
            recommended_value=parsed.get("recommended_value"),
            justification=parsed.get("justification", ""),
            literature_source=parsed.get("literature_source", ""),
            confidence=parsed.get("confidence", "low")
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


def validate_nutrient_single(
    food_name: str,
    nutrient_data: dict,
    api_key: Optional[str] = None
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

    Returns:
        AIValidationResult object
    """
    prompt_type = nutrient_data.get("prompt_type")
    nutrient_name = nutrient_data.get("nutrient_name", "Unknown")
    unit = nutrient_data.get("unit", "")

    # Build the appropriate prompt
    if prompt_type == "sr_only":
        prompt = build_prompt_sr_only(
            food_name=food_name,
            nutrient_name=nutrient_name,
            sr_value=nutrient_data.get("sr_value", 0),
            unit=unit,
            metadata=nutrient_data.get("sr_metadata", {})
        )
    elif prompt_type == "both_sources":
        prompt = build_prompt_both_sources(
            food_name=food_name,
            nutrient_name=nutrient_name,
            sr_value=nutrient_data.get("sr_value", 0),
            foundation_value=nutrient_data.get("foundation_value", 0),
            unit=unit,
            discrepancy_percent=nutrient_data.get("discrepancy_percent", 0),
            sr_metadata=nutrient_data.get("sr_metadata", {}),
            foundation_metadata=nutrient_data.get("foundation_metadata", {})
        )
    elif prompt_type == "missing":
        prompt = build_prompt_missing(
            food_name=food_name,
            nutrient_name=nutrient_name,
            unit=unit
        )
    elif prompt_type == "foundation_only":
        prompt = build_prompt_foundation_only(
            food_name=food_name,
            nutrient_name=nutrient_name,
            foundation_value=nutrient_data.get("foundation_value", 0),
            unit=unit,
            metadata=nutrient_data.get("foundation_metadata", {})
        )
    else:
        raise AIValidationError(f"Unknown prompt type: {prompt_type}")

    # Call API with retry
    response = call_claude_api_with_retry(prompt, api_key)

    # Parse response
    return parse_single_response(response, nutrient_data)


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
        confidence="high"
    )


def validate_nutrients_sequential(
    food_name: str,
    comparison_result: dict,
    sr_data: dict,
    foundation_data: Optional[dict],
    missing_nutrients: list[dict],
    api_key: Optional[str] = None,
    verbose: bool = False
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
                result = validate_nutrient_single(food_name, nutrient_data, api_key)
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

        # Store result
        if nutrient_id is not None:
            results_dict[nutrient_id] = result
        else:
            results_dict[nutrient_name] = result

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
    rate_limiter: _AsyncRateLimiter
) -> str:
    """
    Async version of Claude API call with semaphore-controlled concurrency.

    Args:
        prompt: The prompt to send
        client: AsyncAnthropic client instance (shared)
        semaphore: Semaphore to limit concurrent requests
        rate_limiter: Rate limiter to enforce minimum request interval

    Returns:
        API response text
    """
    if MOCK_MODE:
        # Small delay to simulate API latency for realistic testing
        await asyncio.sleep(0.05)
        return _get_mock_response(prompt)

    async with semaphore:
        await rate_limiter.acquire()

        message = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )

        return message.content[0].text


async def _call_claude_api_async_with_retry(
    prompt: str,
    client,  # anthropic.AsyncAnthropic
    semaphore: asyncio.Semaphore,
    rate_limiter: _AsyncRateLimiter
) -> str:
    """
    Async API call with exponential backoff retry logic.

    Args:
        prompt: The prompt to send
        client: AsyncAnthropic client instance
        semaphore: Semaphore for concurrency control
        rate_limiter: Rate limiter for request pacing

    Returns:
        API response text

    Raises:
        AIValidationError: After all retries exhausted
    """
    if MOCK_MODE:
        return await _call_claude_api_async(prompt, client, semaphore, rate_limiter)

    last_error = None

    for attempt in range(AI_MAX_RETRIES):
        try:
            return await _call_claude_api_async(prompt, client, semaphore, rate_limiter)
        except Exception as e:
            last_error = e
            error_msg = str(e).lower()

            # Don't retry on non-retryable errors
            if "invalid" in error_msg or "api key" in error_msg:
                raise AIValidationError(f"Non-retryable error: {e}")

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
    rate_limiter: _AsyncRateLimiter
) -> AIValidationResult:
    """
    Validate a single nutrient using async AI call.

    Args:
        food_name: Name of the food item
        nutrient_data: Dict containing nutrient info
        client: AsyncAnthropic client instance
        semaphore: Semaphore for concurrency control
        rate_limiter: Rate limiter for request pacing

    Returns:
        AIValidationResult object
    """
    prompt_type = nutrient_data.get("prompt_type")
    nutrient_name = nutrient_data.get("nutrient_name", "Unknown")
    nutrient_id = nutrient_data.get("nutrient_id")
    unit = nutrient_data.get("unit", "")

    # Build the appropriate prompt (reuse existing sync functions)
    if prompt_type == "sr_only":
        prompt = build_prompt_sr_only(
            food_name=food_name,
            nutrient_name=nutrient_name,
            sr_value=nutrient_data.get("sr_value", 0),
            unit=unit,
            metadata=nutrient_data.get("sr_metadata", {})
        )
    elif prompt_type == "both_sources":
        prompt = build_prompt_both_sources(
            food_name=food_name,
            nutrient_name=nutrient_name,
            sr_value=nutrient_data.get("sr_value", 0),
            foundation_value=nutrient_data.get("foundation_value", 0),
            unit=unit,
            discrepancy_percent=nutrient_data.get("discrepancy_percent", 0),
            sr_metadata=nutrient_data.get("sr_metadata", {}),
            foundation_metadata=nutrient_data.get("foundation_metadata", {})
        )
    elif prompt_type == "missing":
        prompt = build_prompt_missing(
            food_name=food_name,
            nutrient_name=nutrient_name,
            unit=unit
        )
    elif prompt_type == "foundation_only":
        prompt = build_prompt_foundation_only(
            food_name=food_name,
            nutrient_name=nutrient_name,
            foundation_value=nutrient_data.get("foundation_value", 0),
            unit=unit,
            metadata=nutrient_data.get("foundation_metadata", {})
        )
    else:
        return AIValidationResult(
            nutrient_id=nutrient_id,
            nutrient_name=nutrient_name,
            prompt_type=prompt_type or "unknown",
            recommendation="error",
            recommended_value=None,
            justification=f"Unknown prompt type: {prompt_type}",
            literature_source="",
            confidence="low"
        )

    try:
        # Call API with retry
        response = await _call_claude_api_async_with_retry(
            prompt, client, semaphore, rate_limiter
        )

        # Parse response (reuse existing sync function)
        return parse_single_response(response, nutrient_data)

    except AIValidationError as e:
        return AIValidationResult(
            nutrient_id=nutrient_id,
            nutrient_name=nutrient_name,
            prompt_type=nutrient_data.get("prompt_type", "unknown"),
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
    verbose: bool = False
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

            # Store result
            if nutrient_id is not None:
                results_dict[nutrient_id] = result
            else:
                results_dict[nutrient_name] = result
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
        try:
            import anthropic
            key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
            if not key:
                raise AIValidationError("No Anthropic API key provided")
            client = anthropic.AsyncAnthropic(api_key=key)
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")

    try:
        # Create tasks for all nutrients
        tasks = [
            _validate_nutrient_async(
                food_name, nutrient_data, client, semaphore, rate_limiter
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

                if nutrient_id is not None:
                    results_dict[nutrient_id] = error_result
                else:
                    results_dict[nutrient_name] = error_result
            else:
                validated_count += 1
                if verbose:
                    print(f"  {result.confidence.upper()}: {nutrient_name} - {result.recommendation}")

                if nutrient_id is not None:
                    results_dict[nutrient_id] = result
                else:
                    results_dict[nutrient_name] = result

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
    verbose: bool = False
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

    if verbose:
        print(f"\nValidating {len(nutrients_data)} nutrients for {food_name} (concurrent)...")

    # Run the async function
    return asyncio.run(_validate_nutrients_async(
        food_name=food_name,
        nutrients_data=nutrients_data,
        api_key=api_key,
        concurrent_limit=concurrent_limit,
        verbose=verbose
    ))
