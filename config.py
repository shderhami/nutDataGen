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

# Smart Skipping Thresholds
SKIP_VALIDATION_THRESHOLD = 5.0  # Skip AI validation if SR/Foundation differ by < 5%

# Async Concurrent Validation Settings
AI_CONCURRENT_LIMIT = 5          # Max concurrent API requests
AI_MAX_CONCURRENT_LIMIT = 10     # Hard cap on concurrency

# AI Model for validation
AI_MODEL = "claude-opus-4-6"

# AI Mock Mode (set to True for testing without real API calls)
AI_MOCK_MODE = os.environ.get("AI_MOCK_MODE", "false").lower() == "true"

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
