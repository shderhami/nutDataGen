"""
Configuration settings for the USDA Nutrition Data Extraction System.
"""
import os
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Look for .env in the package directory
    env_path = Path(__file__).parent / ".env"
    load_dotenv(env_path)
except ImportError:
    # python-dotenv not installed, fall back to environment variables only
    pass

# API Configuration
API_KEY = os.environ.get("USDA_API_KEY", "")
BASE_URL = "https://api.nal.usda.gov/fdc/v1"

# Discrepancy thresholds (percentage difference)
DISCREPANCY_THRESHOLDS = {
    "trivial": 5,      # < 5% difference - auto-accept SR Legacy
    "moderate": 15,    # 5-15% - flag for review
    "significant": 30  # 15-30% - requires decision
    # > 30% is "major" - definitely requires review
}

# AI Validation Rate Limiting (Anthropic Tier 1)
AI_RATE_LIMIT_RPM = 50           # Requests per minute (Tier 1)
AI_MIN_REQUEST_INTERVAL = 1.2    # Seconds between requests (60/50 = 1.2s)
AI_MAX_RETRIES = 5               # Max retry attempts on failure
AI_RETRY_BASE_DELAY = 4.0        # Base delay for exponential backoff (seconds)

# Smart Skipping Threshold — derived, not independently declared: comparison.py
# classifies a nutrient as a "match" below DISCREPANCY_THRESHOLDS["trivial"], and
# only "match" nutrients may skip AI validation. If the two diverged, matches in
# the gap would reach the validators with a prompt type none of them accept.
SKIP_VALIDATION_THRESHOLD = float(DISCREPANCY_THRESHOLDS["trivial"])

# Mass-failure gate: abort a food when more than this fraction of the
# non-skipped AI validation results are errors (credits exhausted, outage),
# instead of walking the operator through a review loop full of error text.
AI_MASS_FAILURE_THRESHOLD = 0.25

# Web search grounds citations in real sources instead of parametric memory,
# but costs money and latency per nutrient. Off by default: measure the Phase 2
# prompt delta before turning it on for all ~52 nutrients per ingredient.
AI_WEB_SEARCH_ENABLED = os.environ.get(
    "AI_WEB_SEARCH_ENABLED", ""
).strip().lower() in ("1", "true", "yes")
AI_WEB_SEARCH_MAX_USES = int(os.environ.get("AI_WEB_SEARCH_MAX_USES", "5"))
# Server-side tool version with dynamic filtering built in. Do NOT also declare
# code_execution — a second execution environment confuses the model.
AI_WEB_SEARCH_TOOL_TYPE = "web_search_20260209"
# A paused turn must be resumed; cap the resumes so a pathological loop can't
# bill indefinitely.
AI_MAX_PAUSE_RESUMES = 3

# Self-consistency sampling: N independent samples per nutrient, median of the
# numeric answers, with material disagreement as the escalation signal. This
# replaces the model's uncalibrated self-reported confidence with a measured
# one, and multiplies cost by N — off by default (N=1).
AI_SELF_CONSISTENCY_SAMPLES = int(
    os.environ.get("AI_SELF_CONSISTENCY_SAMPLES", "1")
)
# Relative spread across samples above which agreement is "material
# disagreement" and confidence is forced down regardless of what the model
# claimed. 0.30 = samples differ by more than 30% of their median.
AI_SELF_CONSISTENCY_MAX_SPREAD = 0.30

# Async Concurrent Validation Settings
AI_CONCURRENT_LIMIT = 5          # Max concurrent API requests
AI_MAX_CONCURRENT_LIMIT = 10     # Hard cap on concurrency

# AI Model for validation.
# Opus 4.8 rather than 4.6: same $5/$25 per MTok, follows instructions more
# literally (the fix most likely to stop the validator rubber-stamping SR
# values), and it is where the project is heading anyway.
# Note for anyone editing the API call sites: `temperature` is REMOVED on
# Opus 4.7 and later — sending it returns a 400. Thinking is off unless
# explicitly set to adaptive, so max_tokens=4096 covers response text alone.
AI_MODEL = "claude-opus-4-8"

# AI Mock Mode (set to True for testing without real API calls)
AI_MOCK_MODE = os.environ.get("AI_MOCK_MODE", "false").lower() == "true"

# Billed Anthropic calls are opt-in. .env puts a real API key into the
# environment, so without an explicit gate any code path that reaches
# ai_validation spends money — which is how the test suite was silently billing
# on every run. Live calls now require either this variable or an in-process
# grant from ai_validation.permit_live_ai_calls() (main.py asks the user first).
ALLOW_LIVE_AI_CALLS = os.environ.get(
    "ALLOW_LIVE_AI_CALLS", ""
).strip().lower() in ("1", "true", "yes")

# PostgreSQL Database Configuration
DATABASE_HOST = os.environ.get("DATABASE_HOST", "localhost")
DATABASE_PORT = int(os.environ.get("DATABASE_PORT", "5432"))
DATABASE_NAME = os.environ.get("DATABASE_NAME", "cat_food_formulator")
DATABASE_USER = os.environ.get("DATABASE_USER", "postgres")
DATABASE_PASSWORD = os.environ.get("DATABASE_PASSWORD", "postgres")

DATABASE_URL = (
    f"postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}"
    f"@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
)

# Food ID sequence start (professional IDs, not starting from 1)
FOOD_ID_SEQUENCE_START = 10001

# File paths (data directory kept for legacy compatibility)
DATA_DIR = Path(__file__).parent / "data"

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)
