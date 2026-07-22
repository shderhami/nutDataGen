"""
USDA FoodData Central API Integration.

Fetches nutrition data from USDA FoodData Central databases
(SR Legacy and Foundation Foods).
"""
import requests
from typing import Optional

from config import BASE_URL, API_KEY
from fediaf_nutrients import get_usda_nutrient_ids


class USDAAPIError(Exception):
    """Exception raised for USDA API errors."""
    pass


# Mapping from USDA nutrient number (abridged format) to nutrient ID (full format).
# Some FDC IDs only return data in abridged format, which uses "number" (str)
# instead of "nutrient.id" (int). This mapping covers 48 tracked nutrients
# (excludes Chloride, Iodine, Biotin, Taurine which have no USDA data).
NUTRIENT_NUMBER_TO_ID: dict[str, int] = {
    "203": 1003, "204": 1004, "205": 1005, "207": 1007, "208": 1008,
    "255": 1051, "291": 1079, "301": 1087, "303": 1089, "304": 1090,
    "305": 1091, "306": 1092, "307": 1093, "309": 1095, "312": 1098,
    "315": 1101, "317": 1103, "320": 1106, "323": 1109, "324": 1110,
    "404": 1165, "405": 1166, "406": 1167, "410": 1170, "415": 1175,
    "417": 1177, "418": 1178, "421": 1180, "430": 1185,
    "501": 1210, "502": 1211, "503": 1212, "504": 1213, "505": 1214,
    "506": 1215, "507": 1216, "508": 1217, "509": 1218, "510": 1219,
    "511": 1220, "512": 1221,
    "618": 1269, "619": 1270, "620": 1271, "621": 1272, "629": 1278,
    "631": 1280, "646": 1293,
}


# Derivation code to full description mapping
# Based on USDA FoodData Central derivation codes
DERIVATION_CODES = {
    "A": "Analytical",
    "AR": "Analytical, Assumed Zero",
    "AS": "Analytical, Aggregated from Sample",
    "C": "Calculated",
    "CA": "Calculated by Addition",
    "CC": "Calculated from Composition",
    "CD": "Calculated from Difference",
    "CF": "Calculated from Formula",
    "CI": "Calculated from Imputation",
    "CM": "Calculated from Manufacturer Data",
    "CP": "Calculated from Percent Daily Value",
    "CR": "Calculated from Recipe",
    "CS": "Calculated from Similar",
    "E": "Estimated",
    "EC": "Estimated from Composition",
    "ER": "Estimated from Recipe",
    "ES": "Estimated from Similar",
    "I": "Imputed",
    "M": "Manufacturer's Data",
    "MA": "Manufacturer's Analytical",
    "MC": "Manufacturer's Calculated",
    "NC": "Not Calculated",
    "NR": "Not Reported",
    "NS": "Not Specified",
    "R": "Assumed or Rounded",
    "S": "Summed",
    "T": "Taken from Another Source",
    "U": "Unknown",
    "Z": "Assumed Zero",
}


def get_derivation_description(derivation_data: Optional[dict]) -> str:
    """
    Get full derivation description from derivation data.

    Args:
        derivation_data: Derivation object from API response

    Returns:
        Full description string, or empty string if not available
    """
    if not derivation_data:
        return ""

    # Try to get description directly from API response
    description = derivation_data.get("description", "")
    if description:
        return description

    # Fall back to code lookup
    code = derivation_data.get("code", "")
    if code and code in DERIVATION_CODES:
        return DERIVATION_CODES[code]

    return code if code else ""


def fetch_food_data(fdc_id: int, api_key: Optional[str] = None) -> dict:
    """
    Fetch raw food data from USDA API.

    Args:
        fdc_id: FoodData Central ID
        api_key: USDA API key (uses config if not provided)

    Returns:
        Complete JSON response as dict

    Raises:
        USDAAPIError: On API error or invalid FDC ID
    """
    key = api_key if api_key is not None else API_KEY
    if not key:
        raise USDAAPIError("No API key provided. Set USDA_API_KEY environment variable.")

    url = f"{BASE_URL}/food/{fdc_id}"
    params = {"api_key": key}

    try:
        response = requests.get(url, params=params, timeout=30)

        if response.status_code == 404:
            # Some FDC IDs (e.g., newer Foundation entries) only work with
            # abridged format. Retry before giving up.
            params["format"] = "abridged"
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 404:
                raise USDAAPIError(f"Food with FDC ID {fdc_id} not found")
            elif response.status_code != 200:
                raise USDAAPIError(f"API error: HTTP {response.status_code}")
            data = response.json()
            data["_abridged"] = True
            return data

        if response.status_code == 403:
            raise USDAAPIError("Invalid or expired API key")
        elif response.status_code == 429:
            raise USDAAPIError("Rate limit exceeded. Please wait and try again.")
        elif response.status_code != 200:
            raise USDAAPIError(f"API error: HTTP {response.status_code}")

        return response.json()

    except requests.exceptions.Timeout:
        raise USDAAPIError("Request timed out")
    except requests.exceptions.ConnectionError:
        raise USDAAPIError("Network connection error")
    except requests.exceptions.RequestException as e:
        raise USDAAPIError(f"Request failed: {str(e)}")


def extract_nutrients(food_data: dict, nutrient_ids: list[int]) -> dict:
    """
    Extract specific nutrients from API response with full metadata.

    Args:
        food_data: Raw API response dict
        nutrient_ids: List of USDA nutrient IDs to extract

    Note:
        SR Legacy API doesn't provide per-nutrient year_acquired dates.
        Only Foundation Foods has minYearAcquired and nutrientAnalysisDetails.

    Returns:
        Dict mapping nutrient_id to nutrient data including:
        - name: Nutrient name
        - value: Amount/value
        - unit: Unit of measurement
        - num_samples: Number of data points/samples
        - min_value: Minimum value
        - max_value: Maximum value
        - median_value: Median value
        - year_acquired: Year data was acquired
        - derivation_description: Full derivation description

        Note: standard_error and footnote are NOT provided by USDA API.

        Missing nutrients have value = None
    """
    result = {}

    # Initialize all requested nutrients as missing with full metadata structure
    # Note: standard_error and footnote removed - USDA API does not provide these fields
    for nid in nutrient_ids:
        result[nid] = {
            "name": None,
            "value": None,
            "unit": None,
            "num_samples": None,
            "min_value": None,
            "max_value": None,
            "median_value": None,
            "year_acquired": None,
            "derivation_description": None
        }

    # Get nutrients from the response
    food_nutrients = food_data.get("foodNutrients", [])

    # Abridged format uses flat structure with "number" field instead of nested "nutrient.id"
    if food_data.get("_abridged"):
        for fn in food_nutrients:
            number = str(fn.get("number", ""))
            nid = NUTRIENT_NUMBER_TO_ID.get(number)
            if nid and nid in nutrient_ids:
                result[nid] = {
                    "name": fn.get("name"),
                    "value": fn.get("amount"),
                    "unit": fn.get("unitName"),
                    "num_samples": None,
                    "min_value": None,
                    "max_value": None,
                    "median_value": None,
                    "year_acquired": None,
                    "derivation_description": fn.get("derivationDescription", ""),
                }
        return result

    for fn in food_nutrients:
        # Handle different response structures
        if "nutrient" in fn:
            # Standard structure (Foundation Foods typically)
            nutrient = fn["nutrient"]
            nid = nutrient.get("id")
            if nid in nutrient_ids:
                # Get derivation description
                derivation = fn.get("foodNutrientDerivation", {})
                derivation_desc = get_derivation_description(derivation)

                # Extract year - check minYearAcquired first (Foundation), then nutrientAnalysisDetails
                # Note: SR Legacy API doesn't provide per-nutrient dates (only website shows them)
                year_acquired = None
                if fn.get("minYearAcquired"):
                    year_acquired = str(fn.get("minYearAcquired"))
                else:
                    analysis_details = fn.get("nutrientAnalysisDetails", [])
                    if analysis_details and len(analysis_details) > 0:
                        acq_date = analysis_details[0].get("acquisitionDate", "")
                        if acq_date:
                            # Extract just the year from date string
                            year_acquired = acq_date[:4] if len(acq_date) >= 4 else acq_date

                result[nid] = {
                    "name": nutrient.get("name"),
                    "value": fn.get("amount"),
                    "unit": nutrient.get("unitName"),
                    # dataPoints is used by both SR Legacy and Foundation; numberOfDataPoints is fallback
                    "num_samples": fn.get("dataPoints") or fn.get("numberOfDataPoints"),
                    "min_value": fn.get("min"),
                    "max_value": fn.get("max"),
                    # median is only available in Foundation, not SR Legacy
                    "median_value": fn.get("median"),
                    "year_acquired": year_acquired,
                    "derivation_description": derivation_desc
                }

        elif "nutrientId" in fn:
            # Alternative structure (some API response formats)
            nid = fn.get("nutrientId")
            if nid in nutrient_ids:
                # Get derivation description
                derivation = fn.get("foodNutrientDerivation", {})
                derivation_desc = get_derivation_description(derivation)

                # Extract year - SR Legacy API doesn't provide per-nutrient dates
                year_acquired = None
                if fn.get("minYearAcquired"):
                    year_acquired = str(fn.get("minYearAcquired"))
                elif fn.get("acquisitionDate"):
                    acq_date = fn.get("acquisitionDate", "")
                    year_acquired = acq_date[:4] if len(acq_date) >= 4 else acq_date

                result[nid] = {
                    "name": fn.get("nutrientName"),
                    "value": fn.get("value"),
                    "unit": fn.get("unitName"),
                    # dataPoints is used by both SR Legacy and Foundation
                    "num_samples": fn.get("dataPoints") or fn.get("numberOfDataPoints"),
                    "min_value": fn.get("min"),
                    "max_value": fn.get("max"),
                    # median may not be available in SR Legacy
                    "median_value": fn.get("median"),
                    "year_acquired": year_acquired,
                    "derivation_description": derivation_desc
                }

    return result


def fetch_sr_legacy(fdc_id: int, api_key: Optional[str] = None) -> dict:
    """
    Fetch SR Legacy food and extract FEDIAF-required nutrients.

    Args:
        fdc_id: FoodData Central ID for SR Legacy food
        api_key: USDA API key (uses config if not provided)

    Returns:
        Dict with food metadata and nutrients:
        {
            "fdc_id": int,
            "description": str,
            "data_type": str,
            "publication_date": str,
            "portion_size": str (always "100g" for USDA data),
            "nutrients": {nutrient_id: {name, value, unit, ...}, ...}
        }
    """
    food_data = fetch_food_data(fdc_id, api_key)
    nutrient_ids = get_usda_nutrient_ids()
    nutrients = extract_nutrients(food_data, nutrient_ids)

    return {
        "fdc_id": fdc_id,
        "description": food_data.get("description", ""),
        "data_type": food_data.get("dataType", ""),
        "publication_date": food_data.get("publicationDate", ""),
        "portion_size": "100g",  # USDA data is always per 100g
        "nutrients": nutrients
    }


def fetch_foundation(fdc_id: int, api_key: Optional[str] = None) -> dict:
    """
    Fetch Foundation Foods and extract FEDIAF-required nutrients.

    Args:
        fdc_id: FoodData Central ID for Foundation food
        api_key: USDA API key (uses config if not provided)

    Returns:
        Dict with food metadata and nutrients:
        {
            "fdc_id": int,
            "description": str,
            "data_type": str,
            "publication_date": str,
            "portion_size": str (always "100g" for USDA data),
            "nutrients": {nutrient_id: {name, value, unit, ...}, ...}
        }
    """
    food_data = fetch_food_data(fdc_id, api_key)
    nutrient_ids = get_usda_nutrient_ids()
    nutrients = extract_nutrients(food_data, nutrient_ids)

    return {
        "fdc_id": fdc_id,
        "description": food_data.get("description", ""),
        "data_type": food_data.get("dataType", ""),
        "publication_date": food_data.get("publicationDate", ""),
        "portion_size": "100g",  # USDA data is always per 100g
        "nutrients": nutrients
    }


def get_food_description(fdc_id: int, api_key: Optional[str] = None) -> str:
    """
    Quick lookup of food description by FDC ID.

    Args:
        fdc_id: FoodData Central ID
        api_key: USDA API key (uses config if not provided)

    Returns:
        Food description string
    """
    food_data = fetch_food_data(fdc_id, api_key)
    return food_data.get("description", "")


def search_foods(query: str, data_type: Optional[str] = None,
                 api_key: Optional[str] = None, page_size: int = 25) -> list[dict]:
    """
    Search for foods in USDA database.

    Args:
        query: Search query string
        data_type: Filter by data type (e.g., "SR Legacy", "Foundation")
        api_key: USDA API key (uses config if not provided)
        page_size: Number of results per page

    Returns:
        List of food items matching the query
    """
    key = api_key if api_key is not None else API_KEY
    if not key:
        raise USDAAPIError("No API key provided. Set USDA_API_KEY environment variable.")

    url = f"{BASE_URL}/foods/search"
    params = {
        "api_key": key,
        "query": query,
        "pageSize": page_size
    }

    if data_type:
        params["dataType"] = data_type

    try:
        response = requests.get(url, params=params, timeout=30)

        if response.status_code != 200:
            raise USDAAPIError(f"Search API error: HTTP {response.status_code}")

        data = response.json()
        return data.get("foods", [])

    except requests.exceptions.RequestException as e:
        raise USDAAPIError(f"Search request failed: {str(e)}")
