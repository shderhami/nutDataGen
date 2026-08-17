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


# Derivation code to full description mapping.
# Generated from data/USDA data/FoodData_Central_sr_legacy_food_csv_2018-04/
# food_nutrient_derivation.csv (64 codes) — regenerate from that CSV
# rather than hand-editing; the previous hand-written table had inverted
# meanings (e.g. NC) and invented codes.
DERIVATION_CODES = {
    "A": "Analytical",
    "AI": "Analytical data; from the literature or  government;  incomplete documentation",
    "AR": "Analytical data; derived by linear regression",
    "AS": "Summed",
    "BD": "Based on same food; Drained solids from solids and liquids or vice versa (canned fruits and vegetables)",
    "BFAN": "Based on another form of the food or similar food; Concentration adjustment; Ash; Retention factors not used",
    "BFCN": "Based on another form of the food or similar food; Concentration adjustment; Carbohydrate; Retention factors not used",
    "BFFN": "Based on another form of the food or similar food; Concentration adjustment; Fat; Retention factors not used",
    "BFFY": "Based on another form of the food or similar food; Concentration adjustment; Fat; Retention factors used",
    "BFNN": "Based on another form of the food or similar food; Concentration adjustment; Non-fat solids; Retention factors not used",
    "BFNY": "Based on another form of the food or similar food; Concentration adjustment; Non-fat solids; Retentions factors used",
    "BFPN": "Based on another form of the food or similar food; Concentration adjustment; Protein; Retention factors not used",
    "BFPY": "Based on another form of the food or similar food; Concentration adjustment; Protein; Retention factors used",
    "BFSN": "Based on another form of the food or similar food; Concentration adjustment; Solids; Retention factors not used",
    "BFSY": "Based on another form of the food or similar food; Concentration adjustment; Solids; Retention factors used",
    "BFYN": "Based on another form of the food or similar food; Concentration adjustment; Yield; Retention factors not used",
    "BFYY": "Based on another form of the food or similar food; Concentration adjustment; Yield; Retention factors used",
    "BFZN": "Based on another form of the food or similar food; Concentration adjustment; No adjustment; Retention factors not used",
    "BFZY": "Based on another form of the food or similar food; Concentration adjustment; No adjustment; Retention factors used",
    "BNA": "Based on another form of the same food or similar food: constituents normalized to total; vitamin A",
    "CAAN": "Calculated from different food; From average values for food category; Ash; Retention factors not used",
    "CAFN": "Calculated from different food; From average values for food category; Fat; Retention factors not used",
    "CASN": "Calculated from different food; From average values for food category; Solids; Retention factors not used",
    "CAZN": "Calculated from different food; From average values for food category; No adjustment; Retention factors not used",
    "DA": "Concentration adjustment using factor; derived from analytical data",
    "DI": "Concentration adjustment using factor; derived from imputed data",
    "FLA": "Estimated formulation based on ingredient list; Linear program used to estimate ingredients; Analytical data",
    "FLC": "Estimated formulation based on ingredient list; Linear program used to estimate ingredients; Claim on label/serving",
    "FLM": "Estimated formulation based on ingredient list; Linear program used to estimate ingredients; Manuf. Calc. data/100",
    "JA": "Aggregated data involving combinations of data with only source codes 1 and 12 and/or 13",
    "JO": "Aggregated data involving combinations of data with different source codes when at least one code is not 1, 6, 12, or 13",
    "LC": "Label claim (back calculated from label by NDL staff; Calculated from label claim/serving (g or %RDI)",
    "LCCD": "Calculated from a daily value percentage per serving size measure",
    "LCCS": "Calculated from value per serving size measure",
    "LCGA": "Given by information provider as an approximate value per 100 unit measure",
    "LCGE": "Given by information provider as an exact value per 100 unit measure",
    "LCGL": "Given by information provider as a less than value per 100 unit measure",
    "LCSA": "Calculated from an approximate value per serving size measure",
    "LCSE": "Calculated from an exact value per serving size measure",
    "LCSG": "Calculated from a greater than value per serving size measure",
    "LCSL": "Calculated from a less than value per serving size measure",
    "MA": "Manufacturer supplied(industry or trade association), Analytical data, incomplete documentation",
    "MC": "Manufacturer supplied; Calculated by manufacturer or unknown if analytical or calculated",
    "ML": "Manufacturer supplied; Value upon which manufacturer based label claim for fortified/enriched nutrient",
    "NC": "Calculated",
    "NP": "Nutrient that is based on other nutrient/s; calculated by difference or summed (with or without activity factors) Ex. Proximate component other than CHO by difference. Vitamin A calculated from components when one of the component values is not source code 1 or 7",
    "NR": "Nutrient that is based on other nutrient/s; value used directly, ex. Nut.#204 from Nut.#298",
    "O": "Other procedure used from imputing",
    "PAE": "Based on physical composition; Derived from analytical data; Estimated physical composition",
    "PAK": "Based on physical composition; Derived from analytical data; Known physical composition",
    "PIE": "Based on physical composition; Derived from imputed data; Estimated physical composition",
    "PIK": "Based on physical composition; Derived from imputed data; Known physical composition",
    "RA": "Recipe; Approximate ingredient proportions (ex. combination of several recipes)",
    "RC": "Recipe; Cookbook",
    "RF": "Recipe; Formulary of standard products (formulary or standards of identity)",
    "RK": "Recipe; Known formulation (dissection data or proprietary formulation)",
    "RKA": "Recipe; Known formulation; No adjustments applied, combination of source codes 1, 12, and/or 6.",
    "RKI": "Recipe;Known formulation;No adjustments applied, combination of source codes which includes codes other than 1,12,or 6",
    "RP": "Recipe; Per package directions (ex. refrigerated dough, toast, cake mix)",
    "RPA": "Recipe; Per package directions; No adjustments applied, combination of source codes 1, 12, and/or 6.",
    "RPI": "Recipe;Per package directions;No adjustments applied, combination of source codes which incl codes other than 1,12,or 6",
    "S": "Product standard, such as enrichment level specified in CFR or AMS commodity standard",
    "T": "Taken from another source--other tables of food composition",
    "Z": "Assumed zero (Insignificant amount or not naturally occurring in a food, such as fiber in meat)",
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


def get_derivation_fields(food_nutrient: dict) -> dict:
    """
    Derivation evidence for a nutrient row, from either API payload shape.

    The /food/{id} full format nests it under "foodNutrientDerivation", while
    /foods/search and the abridged format flatten it to top-level derivationCode
    and derivationDescription. Reading only the nested key on a flattened payload
    makes every derivation look absent, which would demote USDA's explicit
    "Assumed Zero" values as though they were never measured.
    """
    nested = food_nutrient.get("foodNutrientDerivation")
    if nested:
        return nested

    code = food_nutrient.get("derivationCode")
    description = food_nutrient.get("derivationDescription")
    if code or description:
        return {"code": code or "", "description": description or ""}

    return {}


def missing_nutrient_entry(unpopulated_zero: bool = False) -> dict:
    """
    The canonical "nutrient not available" entry.

    Note: standard_error and footnote are omitted - USDA API does not provide them.
    """
    return {
        "name": None,
        "value": None,
        "unit": None,
        "num_samples": None,
        "min_value": None,
        "max_value": None,
        "median_value": None,
        "year_acquired": None,
        "derivation_description": None,
        "unpopulated_zero": unpopulated_zero,
    }


def is_unpopulated_zero(
    amount: object,
    data_points: Optional[int],
    derivation_data: Optional[dict],
) -> bool:
    """
    Detect a USDA row that carries no measurement rather than a real zero.

    USDA emits a row for every nutrient in a food's profile, so one that was never
    analysed still shows up with amount 0. Those rows have no data points and no
    derivation code at all, whereas a zero USDA stands behind carries evidence: an
    explicit "Z" (Assumed Zero), a calculated derivation, or a data point count.

    This is a PROVENANCE signal only — callers keep the zero and surface the flag
    to the reviewer. It is NOT evidence the value is wrong: against Foundation
    re-analyses, bare zeros turn out to be genuinely ~0 about 86% of the time,
    slightly more often than "Z"-coded zeros. Treating them as missing and sending
    them to a literature search was measured to be net harmful and was reverted.

    Example: FDC 174326 (lamb shoulder, lean, raw) publishes EPA, DHA and DPA as
    0 with no data points and no derivation, while carbohydrate and fiber carry
    derivation "Z" — only the former three are unpopulated.
    """
    if amount is None:
        return False
    try:
        if float(amount) != 0.0:
            return False
    except (TypeError, ValueError):
        return False

    # Any non-zero count means an actual analysis backs the zero.
    if data_points:
        return False

    if derivation_data and (
        derivation_data.get("code") or derivation_data.get("description")
    ):
        return False

    return True


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


VITAMIN_A_RAE_ID = 1106
RETINOL_ID = 1105
RETINOL_NUMBER = "319"      # FDC nutrient number for Retinol (abridged payloads)


def _retinol_note(desc: str) -> str:
    """Provenance marker for a Vitamin A value taken from the Retinol row."""
    note = "RAE from Retinol (1105); cats derive vitamin A from retinol only"
    return f"{desc}; {note}" if desc else note


def _retinol_fallback(result: dict, food_nutrients: list, abridged: bool) -> None:
    """Fill Vitamin A RAE (1106) from Retinol (1105) when the payload has no RAE row.

    Foundation Foods often publish Retinol without a Vitamin A RAE row (e.g. FDC
    2684441 farmed salmon: retinol 2.15 analytical, no 1106), which made vitamin A
    look SR-only and silently dropped the modern measurement — caught during the
    2026-08-17 DB validation. For this cat-specific database RAE := retinol (cats
    cannot convert carotenoids; matches the plant-vitamin-A-is-zero convention).
    A published RAE row — including a zero — always wins; the fallback fires only
    when 1106 is entirely absent from the payload.
    """
    entry = result.get(VITAMIN_A_RAE_ID)
    if entry is None or entry.get("value") is not None:
        return
    for fn in food_nutrients:
        if abridged:
            if str(fn.get("number", "")) != RETINOL_NUMBER:
                continue
            derivation = get_derivation_fields(fn)
            value = fn.get("amount")
            result[VITAMIN_A_RAE_ID] = {
                "name": fn.get("name"),
                "value": value,
                "unit": fn.get("unitName"),
                "num_samples": None,
                "min_value": None,
                "max_value": None,
                "median_value": None,
                "year_acquired": None,
                "derivation_description": _retinol_note(fn.get("derivationDescription", "")),
                "unpopulated_zero": is_unpopulated_zero(value, None, derivation),
            }
            return
        nid = fn["nutrient"].get("id") if "nutrient" in fn else fn.get("nutrientId")
        if nid != RETINOL_ID:
            continue
        if "nutrient" in fn:
            name, unit, value = fn["nutrient"].get("name"), fn["nutrient"].get("unitName"), fn.get("amount")
        else:
            name, unit, value = fn.get("nutrientName"), fn.get("unitName"), fn.get("value")
        derivation = get_derivation_fields(fn)
        data_points = fn.get("dataPoints") or fn.get("numberOfDataPoints")
        year = str(fn.get("minYearAcquired")) if fn.get("minYearAcquired") else None
        result[VITAMIN_A_RAE_ID] = {
            "name": name,
            "value": value,
            "unit": unit,
            "num_samples": data_points,
            "min_value": fn.get("min"),
            "max_value": fn.get("max"),
            "median_value": fn.get("median"),
            "year_acquired": year,
            "derivation_description": _retinol_note(get_derivation_description(derivation)),
            "unpopulated_zero": is_unpopulated_zero(value, data_points, derivation),
        }
        return


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

        Missing nutrients have value = None.

        Nutrients USDA published as an unpopulated zero (see is_unpopulated_zero)
        KEEP their zero and are flagged unpopulated_zero = True. The flag is
        advisory: it tells the reviewer USDA never measured the value, without
        substituting a judgement about what the value should be.
    """
    result = {}

    # Initialize all requested nutrients as missing with full metadata structure
    for nid in nutrient_ids:
        result[nid] = missing_nutrient_entry()

    # Get nutrients from the response
    food_nutrients = food_data.get("foodNutrients", [])

    # Abridged format uses flat structure with "number" field instead of nested "nutrient.id".
    # It carries no dataPoints but does carry flattened derivation fields, so the
    # unpopulated-zero flag is computed here too and the same food is flagged the same
    # way whichever format the API served.
    if food_data.get("_abridged"):
        for fn in food_nutrients:
            number = str(fn.get("number", ""))
            nid = NUTRIENT_NUMBER_TO_ID.get(number)
            if nid and nid in nutrient_ids:
                derivation = get_derivation_fields(fn)
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
                    "unpopulated_zero": is_unpopulated_zero(
                        fn.get("amount"), None, derivation
                    ),
                }
        _retinol_fallback(result, food_nutrients, abridged=True)
        return result

    for fn in food_nutrients:
        # Handle different response structures
        if "nutrient" in fn:
            # Standard structure (Foundation Foods typically)
            nutrient = fn["nutrient"]
            nid = nutrient.get("id")
            if nid in nutrient_ids:
                # Get derivation description
                derivation = get_derivation_fields(fn)
                derivation_desc = get_derivation_description(derivation)

                data_points = fn.get("dataPoints") or fn.get("numberOfDataPoints")
                unpopulated = is_unpopulated_zero(
                    fn.get("amount"), data_points, derivation
                )

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
                    "derivation_description": derivation_desc,
                    "unpopulated_zero": unpopulated
                }

        elif "nutrientId" in fn:
            # Alternative structure (some API response formats)
            nid = fn.get("nutrientId")
            if nid in nutrient_ids:
                # Get derivation description — this payload shape flattens it
                derivation = get_derivation_fields(fn)
                derivation_desc = get_derivation_description(derivation)

                data_points = fn.get("dataPoints") or fn.get("numberOfDataPoints")
                unpopulated = is_unpopulated_zero(
                    fn.get("value"), data_points, derivation
                )

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
                    "derivation_description": derivation_desc,
                    "unpopulated_zero": unpopulated
                }

    _retinol_fallback(result, food_nutrients, abridged=False)
    return result


def get_unpopulated_zero_ids(nutrients: dict) -> list[int]:
    """Nutrient IDs USDA published as an unpopulated zero (value kept, flagged)."""
    return [nid for nid, n in nutrients.items() if n.get("unpopulated_zero")]


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
            "nutrients": {nutrient_id: {name, value, unit, ...}, ...},
            "unpopulated_zeros": [nutrient_id, ...]  # kept at 0; USDA never measured them
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
        "nutrients": nutrients,
        "unpopulated_zeros": get_unpopulated_zero_ids(nutrients)
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
            "nutrients": {nutrient_id: {name, value, unit, ...}, ...},
            "unpopulated_zeros": [nutrient_id, ...]  # kept at 0; USDA never measured them
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
        "nutrients": nutrients,
        "unpopulated_zeros": get_unpopulated_zero_ids(nutrients)
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
