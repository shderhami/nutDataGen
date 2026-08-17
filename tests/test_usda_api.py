"""
Tests for usda_api.py

Uses mock API responses for offline testing.
Live API tests are marked with @pytest.mark.live and skip if no API key.
"""
import sys
import os
from pathlib import Path
from unittest.mock import patch, Mock

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from usda_api import (
    USDAAPIError,
    NUTRIENT_NUMBER_TO_ID,
    fetch_food_data,
    extract_nutrients,
    fetch_sr_legacy,
    fetch_foundation,
    get_food_description,
    search_foods,
    get_derivation_description,
    get_derivation_fields,
    missing_nutrient_entry,
    is_unpopulated_zero,
    get_unpopulated_zero_ids,
    DERIVATION_CODES,
)


# Sample mock responses
MOCK_FOOD_RESPONSE = {
    "fdcId": 171116,
    "description": "Chicken, broiler or fryers, thigh, meat only, raw",
    "dataType": "SR Legacy",
    "foodNutrients": [
        {
            "nutrient": {
                "id": 1003,
                "name": "Protein",
                "unitName": "g"
            },
            "amount": 19.6,
            "numberOfDataPoints": 10,
            "min": 18.0,
            "max": 21.0,
            "median": 19.5,
            "standardError": 0.3,
            "foodNutrientDerivation": {
                "code": "A",
                "description": "Analytical"
            },
            "footnote": "Test footnote"
        },
        {
            "nutrient": {
                "id": 1004,
                "name": "Total lipid (fat)",
                "unitName": "g"
            },
            "amount": 6.99,
            "foodNutrientDerivation": {
                "code": "C",
                "description": "Calculated"
            }
        },
        {
            "nutrient": {
                "id": 1008,
                "name": "Energy",
                "unitName": "kcal"
            },
            "amount": 142
        },
        {
            "nutrient": {
                "id": 1087,
                "name": "Calcium, Ca",
                "unitName": "mg"
            },
            "amount": 8
        },
        {
            "nutrient": {
                "id": 1089,
                "name": "Iron, Fe",
                "unitName": "mg"
            },
            "amount": 1.3
        },
    ]
}

MOCK_ABRIDGED_RESPONSE = {
    "fdcId": 748967,
    "description": "Eggs, Grade A, Large, egg whole",
    "dataType": "Foundation",
    "foodNutrients": [
        {
            "number": "203",
            "name": "Protein",
            "amount": 12.4,
            "unitName": "G",
            "derivationCode": "NC",
            "derivationDescription": "Calculated",
        },
        {
            "number": "204",
            "name": "Total lipid (fat)",
            "amount": 9.96,
            "unitName": "G",
            "derivationCode": "A",
            "derivationDescription": "Analytical",
        },
        {
            "number": "208",
            "name": "Energy",
            "amount": 148,
            "unitName": "KCAL",
            "derivationCode": "NC",
            "derivationDescription": "Calculated",
        },
        {
            "number": "301",
            "name": "Calcium, Ca",
            "amount": 48.0,
            "unitName": "MG",
            "derivationCode": "A",
            "derivationDescription": "Analytical",
        },
        {
            "number": "999",
            "name": "Unknown Nutrient",
            "amount": 1.0,
            "unitName": "MG",
        },
    ],
}

MOCK_SEARCH_RESPONSE = {
    "foods": [
        {"fdcId": 171116, "description": "Chicken thigh, raw"},
        {"fdcId": 171117, "description": "Chicken breast, raw"},
    ],
    "totalHits": 2
}


class TestFetchFoodData:
    """Tests for fetch_food_data function."""

    def test_raises_error_without_api_key(self):
        """Test that fetch_food_data raises error without API key."""
        with patch.dict(os.environ, {"USDA_API_KEY": ""}, clear=False):
            # Force reload to get empty API key
            with pytest.raises(USDAAPIError) as exc_info:
                fetch_food_data(171116, api_key="")
            assert "API key" in str(exc_info.value)

    @patch('usda_api.requests.get')
    def test_successful_fetch(self, mock_get):
        """Test successful API fetch."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_FOOD_RESPONSE
        mock_get.return_value = mock_response

        result = fetch_food_data(171116, api_key="test_key")

        assert result["fdcId"] == 171116
        assert "Chicken" in result["description"]

    @patch('usda_api.requests.get')
    def test_404_both_formats_raises_error(self, mock_get):
        """Test that 404 on both full and abridged raises error."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        with pytest.raises(USDAAPIError) as exc_info:
            fetch_food_data(999999, api_key="test_key")
        assert "not found" in str(exc_info.value)
        # Should have been called twice: full format then abridged
        assert mock_get.call_count == 2

    @patch('usda_api.requests.get')
    def test_404_falls_back_to_abridged(self, mock_get):
        """Test that 404 on full format retries with abridged."""
        full_response = Mock()
        full_response.status_code = 404
        abridged_response = Mock()
        abridged_response.status_code = 200
        abridged_response.json.return_value = dict(MOCK_ABRIDGED_RESPONSE)
        mock_get.side_effect = [full_response, abridged_response]

        result = fetch_food_data(748967, api_key="test_key")

        assert result["fdcId"] == 748967
        assert result["_abridged"] is True
        assert mock_get.call_count == 2
        # Second call should include format=abridged
        second_call_params = mock_get.call_args_list[1].kwargs.get(
            "params", mock_get.call_args_list[1][1].get("params", {})
        )
        assert second_call_params.get("format") == "abridged"

    @patch('usda_api.requests.get')
    def test_403_raises_error(self, mock_get):
        """Test that 403 response raises error for invalid API key."""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_get.return_value = mock_response

        with pytest.raises(USDAAPIError) as exc_info:
            fetch_food_data(171116, api_key="invalid_key")
        assert "Invalid" in str(exc_info.value) or "API key" in str(exc_info.value)

    @patch('usda_api.requests.get')
    def test_429_raises_rate_limit_error(self, mock_get):
        """Test that 429 response raises rate limit error."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_get.return_value = mock_response

        with pytest.raises(USDAAPIError) as exc_info:
            fetch_food_data(171116, api_key="test_key")
        assert "Rate limit" in str(exc_info.value)

    @patch('usda_api.requests.get')
    def test_timeout_raises_error(self, mock_get):
        """Test that timeout raises error."""
        import requests
        mock_get.side_effect = requests.exceptions.Timeout()

        with pytest.raises(USDAAPIError) as exc_info:
            fetch_food_data(171116, api_key="test_key")
        assert "timed out" in str(exc_info.value)

    @patch('usda_api.requests.get')
    def test_connection_error_raises_error(self, mock_get):
        """Test that connection error raises error."""
        import requests
        mock_get.side_effect = requests.exceptions.ConnectionError()

        with pytest.raises(USDAAPIError) as exc_info:
            fetch_food_data(171116, api_key="test_key")
        assert "connection" in str(exc_info.value).lower()


class TestExtractNutrients:
    """Tests for extract_nutrients function."""

    def test_returns_correct_structure(self):
        """Test extract_nutrients returns correct structure."""
        result = extract_nutrients(MOCK_FOOD_RESPONSE, [1003, 1004])

        assert 1003 in result
        assert 1004 in result
        assert "name" in result[1003]
        assert "value" in result[1003]
        assert "unit" in result[1003]

    def test_extracts_correct_values(self):
        """Test that correct values are extracted."""
        result = extract_nutrients(MOCK_FOOD_RESPONSE, [1003, 1004, 1008])

        assert result[1003]["value"] == 19.6
        assert result[1004]["value"] == 6.99
        assert result[1008]["value"] == 142

    def test_handles_missing_nutrients(self):
        """Test extract_nutrients returns None for missing nutrients."""
        result = extract_nutrients(MOCK_FOOD_RESPONSE, [1003, 9999])

        assert result[1003]["value"] == 19.6
        assert result[9999]["value"] is None
        assert result[9999]["name"] is None

    def test_handles_empty_nutrient_list(self):
        """Test extract_nutrients with empty nutrient list."""
        result = extract_nutrients(MOCK_FOOD_RESPONSE, [])
        assert result == {}

    def test_handles_empty_food_data(self):
        """Test extract_nutrients with empty food data."""
        result = extract_nutrients({}, [1003])
        assert 1003 in result
        assert result[1003]["value"] is None

    def test_extracts_metadata_fields(self):
        """Test extract_nutrients extracts metadata fields."""
        result = extract_nutrients(MOCK_FOOD_RESPONSE, [1003])

        assert result[1003]["num_samples"] == 10
        assert result[1003]["min_value"] == 18.0
        assert result[1003]["max_value"] == 21.0
        assert result[1003]["median_value"] == 19.5
        assert result[1003]["derivation_description"] == "Analytical"
        # Note: standard_error and footnote removed - USDA API does not provide these

    def test_extracts_derivation_from_code(self):
        """Test extract_nutrients gets derivation description from code."""
        result = extract_nutrients(MOCK_FOOD_RESPONSE, [1004])

        assert result[1004]["derivation_description"] == "Calculated"

    def test_handles_missing_metadata(self):
        """Test extract_nutrients handles missing metadata gracefully."""
        result = extract_nutrients(MOCK_FOOD_RESPONSE, [1008])

        # Metadata should be None for nutrients without it
        assert result[1008]["num_samples"] is None
        assert result[1008]["min_value"] is None
        assert result[1008]["max_value"] is None


# Mirrors the shape of FDC 174326 (lamb shoulder, lean, raw): EPA/DHA/DPA are
# published as 0 with no data points and no derivation, carbohydrate carries an
# explicit "Assumed Zero" derivation, and Vitamin A a calculated one.
MOCK_UNPOPULATED_ZERO_RESPONSE = {
    "fdcId": 174326,
    "description": "Lamb, shoulder, separable lean only, raw",
    "dataType": "SR Legacy",
    "foodNutrients": [
        {
            "nutrient": {"id": 1003, "name": "Protein", "unitName": "G"},
            "amount": 19.55,
            "dataPoints": 32,
        },
        {   # never analysed -> must be demoted to missing
            "nutrient": {"id": 1278, "name": "PUFA 20:5 n-3 (EPA)", "unitName": "G"},
            "amount": 0.0,
            "dataPoints": 0,
        },
        {   # never analysed -> must be demoted to missing
            "nutrient": {"id": 1272, "name": "PUFA 22:6 n-3 (DHA)", "unitName": "G"},
            "amount": 0.0,
            "dataPoints": 0,
        },
        {   # USDA asserts the zero -> must be kept
            "nutrient": {"id": 1005, "name": "Carbohydrate, by difference", "unitName": "G"},
            "amount": 0.0,
            "dataPoints": 0,
            "foodNutrientDerivation": {"code": "Z", "description": "Assumed zero"},
        },
        {   # USDA calculated the zero -> must be kept
            "nutrient": {"id": 1106, "name": "Vitamin A, RAE", "unitName": "UG"},
            "amount": 0.0,
            "dataPoints": 0,
            "foodNutrientDerivation": {"code": "NC", "description": "Calculated"},
        },
        {   # non-zero without data points (calculated amino acid) -> must be kept
            "nutrient": {"id": 1220, "name": "Arginine", "unitName": "G"},
            "amount": 1.161,
            "dataPoints": 0,
        },
    ],
}


class TestIsUnpopulatedZero:
    """Tests for the unpopulated-zero predicate."""

    def test_bare_zero_is_unpopulated(self):
        """Zero with no data points and no derivation is a placeholder."""
        assert is_unpopulated_zero(0.0, 0, {}) is True

    def test_none_data_points_is_unpopulated(self):
        """A missing dataPoints field counts the same as zero."""
        assert is_unpopulated_zero(0.0, None, None) is True

    def test_assumed_zero_derivation_is_kept(self):
        """An explicit 'Z' derivation means USDA asserts the zero."""
        assert is_unpopulated_zero(0.0, 0, {"code": "Z"}) is False

    def test_calculated_derivation_is_kept(self):
        """A calculated zero is still an affirmative USDA value."""
        assert is_unpopulated_zero(0.0, 0, {"code": "NC"}) is False

    def test_description_only_derivation_is_kept(self):
        """Derivation evidence may arrive as a description without a code."""
        assert is_unpopulated_zero(0.0, 0, {"description": "Assumed zero"}) is False

    def test_measured_zero_is_kept(self):
        """A zero backed by data points was actually analysed."""
        assert is_unpopulated_zero(0.0, 12, {}) is False

    def test_non_zero_is_kept(self):
        """Only zeros can be placeholders; calculated values stay."""
        assert is_unpopulated_zero(1.161, 0, {}) is False

    def test_absent_amount_is_not_flagged(self):
        """A nutrient with no amount is already missing, not a placeholder."""
        assert is_unpopulated_zero(None, 0, {}) is False

    def test_non_numeric_amount_is_not_flagged(self):
        """A malformed amount must not be misread as a zero."""
        assert is_unpopulated_zero("n/a", 0, {}) is False


class TestExtractNutrientsUnpopulatedZeros:
    """extract_nutrients flags unpopulated zeros without changing their value."""

    def test_unpopulated_zero_is_flagged_but_kept(self):
        """EPA/DHA published as bare zeros keep the 0 and are flagged for review."""
        result = extract_nutrients(MOCK_UNPOPULATED_ZERO_RESPONSE, [1278, 1272])

        assert result[1278]["value"] == 0.0
        assert result[1272]["value"] == 0.0
        assert result[1278]["unpopulated_zero"] is True
        assert result[1272]["unpopulated_zero"] is True

    def test_assumed_zero_is_preserved(self):
        """Carbohydrate's asserted zero stays a real value."""
        result = extract_nutrients(MOCK_UNPOPULATED_ZERO_RESPONSE, [1005])

        assert result[1005]["value"] == 0.0
        assert result[1005]["unpopulated_zero"] is False

    def test_calculated_zero_is_preserved(self):
        """Vitamin A's calculated zero stays a real value."""
        result = extract_nutrients(MOCK_UNPOPULATED_ZERO_RESPONSE, [1106])

        assert result[1106]["value"] == 0.0
        assert result[1106]["unpopulated_zero"] is False

    def test_calculated_non_zero_is_preserved(self):
        """Amino acids carry no data points but are not zeros."""
        result = extract_nutrients(MOCK_UNPOPULATED_ZERO_RESPONSE, [1220])

        assert result[1220]["value"] == 1.161
        assert result[1220]["unpopulated_zero"] is False

    def test_measured_nutrient_is_preserved(self):
        """A normal analysed nutrient is untouched."""
        result = extract_nutrients(MOCK_UNPOPULATED_ZERO_RESPONSE, [1003])

        assert result[1003]["value"] == 19.55
        assert result[1003]["unpopulated_zero"] is False

    def test_get_unpopulated_zero_ids(self):
        """Helper collects exactly the demoted nutrients."""
        result = extract_nutrients(
            MOCK_UNPOPULATED_ZERO_RESPONSE, [1003, 1005, 1106, 1220, 1272, 1278]
        )

        assert sorted(get_unpopulated_zero_ids(result)) == [1272, 1278]

    @patch('usda_api.fetch_food_data')
    def test_fetch_sr_legacy_reports_unpopulated_zeros(self, mock_fetch):
        """fetch_sr_legacy surfaces the flagged nutrient ids to callers."""
        mock_fetch.return_value = MOCK_UNPOPULATED_ZERO_RESPONSE

        result = fetch_sr_legacy(174326, api_key="test_key")

        assert sorted(result["unpopulated_zeros"]) == [1272, 1278]
        assert result["nutrients"][1278]["value"] == 0.0
        assert result["nutrients"][1003]["value"] == 19.55


class TestGetDerivationFields:
    """Derivation evidence must be found in either payload shape."""

    def test_reads_nested_shape(self):
        """The /food/{id} full format nests derivation."""
        fn = {"foodNutrientDerivation": {"code": "Z", "description": "Assumed zero"}}
        assert get_derivation_fields(fn)["code"] == "Z"

    def test_reads_flattened_shape(self):
        """/foods/search and abridged flatten derivation to top level."""
        fn = {"derivationCode": "Z", "derivationDescription": "Assumed zero"}

        result = get_derivation_fields(fn)

        assert result["code"] == "Z"
        assert result["description"] == "Assumed zero"

    def test_absent_derivation_is_empty(self):
        """A row with no derivation at all yields no evidence."""
        assert get_derivation_fields({"amount": 0.0}) == {}


class TestExtractNutrientsFlattenedShape:
    """The nutrientId payload shape flattens derivation; zeros must survive it."""

    FLAT = {
        "foodNutrients": [
            {"nutrientId": 1005, "nutrientName": "Carbohydrate", "unitName": "G",
             "value": 0.0, "dataPoints": 0,
             "derivationCode": "Z", "derivationDescription": "Assumed zero"},
            {"nutrientId": 1278, "nutrientName": "EPA", "unitName": "G",
             "value": 0.0, "dataPoints": 0},
        ]
    }

    def test_flattened_assumed_zero_is_preserved(self):
        """A 'Z' in the flattened shape must not be read as absent derivation."""
        result = extract_nutrients(self.FLAT, [1005])

        assert result[1005]["value"] == 0.0
        assert result[1005]["unpopulated_zero"] is False

    def test_flattened_bare_zero_is_flagged(self):
        """A genuinely bare zero in the flattened shape is flagged, not removed."""
        result = extract_nutrients(self.FLAT, [1278])

        assert result[1278]["value"] == 0.0
        assert result[1278]["unpopulated_zero"] is True


class TestExtractNutrientsDuplicateRows:
    """Later rows overwrite earlier ones; value and flag must stay consistent."""

    def test_duplicate_row_keeps_value_and_flag_consistent(self):
        """The flag must describe the value actually retained."""
        payload = {"foodNutrients": [
            {"nutrient": {"id": 1106, "name": "Vitamin A", "unitName": "UG"},
             "amount": 2.61, "dataPoints": 6,
             "foodNutrientDerivation": {"code": "NC", "description": "Calculated"}},
            {"nutrient": {"id": 1106, "name": "Vitamin A", "unitName": "UG"},
             "amount": 0.0, "dataPoints": 0},
        ]}

        result = extract_nutrients(payload, [1106])

        # The last row wins; its bare zero is flagged and its value retained.
        assert result[1106]["value"] == 0.0
        assert result[1106]["unpopulated_zero"] is True

    def test_missing_entry_helper_shape(self):
        """The helper is the single definition of an absent nutrient."""
        entry = missing_nutrient_entry(unpopulated_zero=True)

        assert entry["value"] is None
        assert entry["name"] is None
        assert entry["unpopulated_zero"] is True


class TestExtractNutrientsAbridged:
    """Tests for extract_nutrients with abridged format responses."""

    def test_extracts_values_from_abridged(self):
        """Test extract_nutrients correctly maps abridged number to nutrient ID."""
        abridged_data = dict(MOCK_ABRIDGED_RESPONSE)
        abridged_data["_abridged"] = True

        result = extract_nutrients(abridged_data, [1003, 1004, 1008, 1087])

        assert result[1003]["value"] == 12.4
        assert result[1003]["name"] == "Protein"
        assert result[1004]["value"] == 9.96
        assert result[1008]["value"] == 148
        assert result[1087]["value"] == 48.0

    def test_abridged_unit_preserved(self):
        """Test that unit from abridged format is preserved."""
        abridged_data = dict(MOCK_ABRIDGED_RESPONSE)
        abridged_data["_abridged"] = True

        result = extract_nutrients(abridged_data, [1003, 1087])

        assert result[1003]["unit"] == "G"
        assert result[1087]["unit"] == "MG"

    def test_abridged_metadata_is_none(self):
        """Test that metadata not in abridged format is None."""
        abridged_data = dict(MOCK_ABRIDGED_RESPONSE)
        abridged_data["_abridged"] = True

        result = extract_nutrients(abridged_data, [1003])

        assert result[1003]["num_samples"] is None
        assert result[1003]["min_value"] is None
        assert result[1003]["max_value"] is None
        assert result[1003]["median_value"] is None
        assert result[1003]["year_acquired"] is None

    def test_abridged_derivation_description(self):
        """Test that derivation description is extracted from abridged."""
        abridged_data = dict(MOCK_ABRIDGED_RESPONSE)
        abridged_data["_abridged"] = True

        result = extract_nutrients(abridged_data, [1003, 1004])

        assert result[1003]["derivation_description"] == "Calculated"
        assert result[1004]["derivation_description"] == "Analytical"

    def test_abridged_missing_nutrients_are_none(self):
        """Test that requested nutrients not in abridged data have None values."""
        abridged_data = dict(MOCK_ABRIDGED_RESPONSE)
        abridged_data["_abridged"] = True

        result = extract_nutrients(abridged_data, [1003, 1234])  # 1234 = Taurine

        assert result[1003]["value"] == 12.4
        assert result[1234]["value"] is None

    def test_abridged_ignores_unmapped_numbers(self):
        """Test that nutrients with unknown numbers are ignored."""
        abridged_data = dict(MOCK_ABRIDGED_RESPONSE)
        abridged_data["_abridged"] = True

        # number "999" is in mock data but not in NUTRIENT_NUMBER_TO_ID
        result = extract_nutrients(abridged_data, [1003])

        assert 1003 in result
        assert result[1003]["value"] == 12.4


class TestNutrientNumberToId:
    """Tests for NUTRIENT_NUMBER_TO_ID mapping."""

    def test_mapping_covers_fediaf_nutrients(self):
        """Test that mapping covers all FEDIAF nutrients with USDA IDs."""
        from fediaf_nutrients import FEDIAF_NUTRIENTS

        # 4 nutrients have no USDA data: Chloride, Iodine, Biotin, Taurine
        unmapped_ids = {1088, 1100, 1176, 1234}
        fediaf_ids = {
            n["nutrient_id"]
            for n in FEDIAF_NUTRIENTS
            if n["nutrient_id"] is not None and n["nutrient_id"] not in unmapped_ids
        }
        mapped_ids = set(NUTRIENT_NUMBER_TO_ID.values())

        assert fediaf_ids.issubset(mapped_ids)

    def test_mapping_values_are_unique(self):
        """Test that all mapped nutrient IDs are unique."""
        ids = list(NUTRIENT_NUMBER_TO_ID.values())
        assert len(ids) == len(set(ids))

    def test_protein_mapping(self):
        """Test Protein number-to-ID mapping."""
        assert NUTRIENT_NUMBER_TO_ID["203"] == 1003

    def test_fat_mapping(self):
        """Test Fat number-to-ID mapping."""
        assert NUTRIENT_NUMBER_TO_ID["204"] == 1004


class TestGetDerivationDescription:
    """Tests for get_derivation_description function."""

    def test_returns_description_from_api(self):
        """Test returns description directly from API response."""
        derivation = {"code": "A", "description": "Analytical"}
        result = get_derivation_description(derivation)
        assert result == "Analytical"

    def test_falls_back_to_code_lookup(self):
        """Test falls back to code lookup when no description."""
        derivation = {"code": "NC"}
        result = get_derivation_description(derivation)
        assert result == "Calculated"

    def test_returns_code_for_unknown(self):
        """Test returns code if not in lookup table."""
        derivation = {"code": "XYZ"}
        result = get_derivation_description(derivation)
        assert result == "XYZ"

    def test_returns_empty_for_none(self):
        """Test returns empty string for None input."""
        result = get_derivation_description(None)
        assert result == ""

    def test_returns_empty_for_empty_dict(self):
        """Test returns empty string for empty dict."""
        result = get_derivation_description({})
        assert result == ""


class TestDerivationCodes:
    """Tests for DERIVATION_CODES constant."""

    def test_contains_common_codes(self):
        """Common real codes are present (the old table asserted invented ones)."""
        assert "A" in DERIVATION_CODES
        assert "NC" in DERIVATION_CODES
        assert "Z" in DERIVATION_CODES

    def test_analytical_is_correct(self):
        """Test Analytical derivation is correct."""
        assert DERIVATION_CODES["A"] == "Analytical"

    def test_calculated_is_correct(self):
        """NC is USDA's 'Calculated' — the old table inverted it to 'Not Calculated'."""
        assert DERIVATION_CODES["NC"] == "Calculated"

    def test_ar_is_linear_regression_not_assumed_zero(self):
        """AR meant 'Analytical, Assumed Zero' in the old table — wrong."""
        assert DERIVATION_CODES["AR"] == "Analytical data; derived by linear regression"

    def test_table_matches_usda_csv_exactly(self):
        """The table is generated from USDA's own derivation CSV — keep it that way.

        The bulk datasets are gitignored, so skip when they aren't present.
        """
        import csv

        import cv_config

        csv_path = cv_config.FDC_SRL_DIR / "food_nutrient_derivation.csv"
        if not csv_path.exists():
            pytest.skip(f"USDA bulk dataset not present at {csv_path}")

        expected = {
            row["code"]: row["description"].strip()
            for row in csv.DictReader(open(csv_path))
        }
        assert DERIVATION_CODES == expected


class TestFetchSrLegacy:
    """Tests for fetch_sr_legacy function."""

    @patch('usda_api.fetch_food_data')
    def test_returns_expected_structure(self, mock_fetch):
        """Test fetch_sr_legacy returns expected structure."""
        mock_fetch.return_value = MOCK_FOOD_RESPONSE

        result = fetch_sr_legacy(171116, api_key="test_key")

        assert "fdc_id" in result
        assert "description" in result
        assert "data_type" in result
        assert "nutrients" in result

    @patch('usda_api.fetch_food_data')
    def test_returns_correct_fdc_id(self, mock_fetch):
        """Test fetch_sr_legacy returns correct FDC ID."""
        mock_fetch.return_value = MOCK_FOOD_RESPONSE

        result = fetch_sr_legacy(171116, api_key="test_key")

        assert result["fdc_id"] == 171116

    @patch('usda_api.fetch_food_data')
    def test_extracts_all_fediaf_nutrients(self, mock_fetch):
        """Test that all FEDIAF nutrients are attempted to be extracted."""
        mock_fetch.return_value = MOCK_FOOD_RESPONSE

        result = fetch_sr_legacy(171116, api_key="test_key")

        # Should have nutrients dict
        assert isinstance(result["nutrients"], dict)
        # Should include common nutrients
        assert 1003 in result["nutrients"]  # Protein


class TestFetchFoundation:
    """Tests for fetch_foundation function."""

    @patch('usda_api.fetch_food_data')
    def test_returns_expected_structure(self, mock_fetch):
        """Test fetch_foundation returns expected structure."""
        mock_fetch.return_value = MOCK_FOOD_RESPONSE

        result = fetch_foundation(746784, api_key="test_key")

        assert "fdc_id" in result
        assert "description" in result
        assert "nutrients" in result


class TestGetFoodDescription:
    """Tests for get_food_description function."""

    @patch('usda_api.fetch_food_data')
    def test_returns_description(self, mock_fetch):
        """Test get_food_description returns description."""
        mock_fetch.return_value = MOCK_FOOD_RESPONSE

        result = get_food_description(171116, api_key="test_key")

        assert "Chicken" in result

    @patch('usda_api.fetch_food_data')
    def test_returns_empty_for_missing_description(self, mock_fetch):
        """Test returns empty string if description missing."""
        mock_fetch.return_value = {"fdcId": 123}

        result = get_food_description(123, api_key="test_key")

        assert result == ""


class TestSearchFoods:
    """Tests for search_foods function."""

    @patch('usda_api.requests.get')
    def test_successful_search(self, mock_get):
        """Test successful food search."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_SEARCH_RESPONSE
        mock_get.return_value = mock_response

        result = search_foods("chicken", api_key="test_key")

        assert len(result) == 2
        assert result[0]["fdcId"] == 171116

    @patch('usda_api.requests.get')
    def test_search_with_data_type_filter(self, mock_get):
        """Test search with data type filter."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_SEARCH_RESPONSE
        mock_get.return_value = mock_response

        search_foods("chicken", data_type="SR Legacy", api_key="test_key")

        # Verify data type was passed to API
        call_args = mock_get.call_args
        assert "dataType" in call_args.kwargs.get("params", call_args[1].get("params", {}))

    def test_search_raises_error_without_api_key(self):
        """Test that search raises error without API key."""
        with pytest.raises(USDAAPIError) as exc_info:
            search_foods("chicken", api_key="")
        assert "API key" in str(exc_info.value)


# Live API tests - only run if a valid API key is available
def _has_valid_api_key():
    """Check if a valid-looking API key is set (not empty or placeholder)."""
    key = os.environ.get("USDA_API_KEY", "")
    return key and len(key) > 10 and key != "your_api_key_here"

@pytest.mark.skipif(
    not _has_valid_api_key(),
    reason="USDA_API_KEY not set or is placeholder"
)
class TestLiveAPI:
    """Live API tests - require USDA_API_KEY environment variable."""

    def test_fetch_chicken_thigh(self):
        """Test fetching known chicken thigh FDC ID."""
        result = fetch_food_data(171116)
        assert "Chicken" in result.get("description", "")

    def test_protein_value_reasonable_range(self):
        """Test that protein value for chicken thigh is in reasonable range."""
        result = fetch_sr_legacy(171116)
        protein = result["nutrients"].get(1003, {})
        value = protein.get("value")
        if value is not None:
            assert 15 <= value <= 30, f"Protein {value}g outside expected range"

    def test_fetch_invalid_id_raises_error(self):
        """Test that invalid FDC ID raises error."""
        with pytest.raises(USDAAPIError):
            fetch_food_data(999999999)


class TestRetinolFallback:
    """Vitamin A RAE (1106) falls back to Retinol (1105) when RAE is absent.

    Foundation Foods often publish retinol without an RAE row (FDC 2684441
    salmon), which made vitamin A look SR-only. RAE := retinol for cats.
    """

    _RETINOL_FULL = {
        "nutrient": {"id": 1105, "name": "Retinol", "unitName": "µg"},
        "amount": 2.15, "dataPoints": 8, "min": 1.09, "max": 3.0, "median": 2.0,
        "minYearAcquired": 2023,
        "foodNutrientDerivation": {"code": "A", "description": "Analytical"},
    }

    def test_foundation_retinol_only_fills_rae(self):
        result = extract_nutrients({"foodNutrients": [self._RETINOL_FULL]}, [1106])
        entry = result[1106]
        assert entry["value"] == 2.15
        assert entry["num_samples"] == 8
        assert entry["min_value"] == 1.09 and entry["max_value"] == 3.0
        assert "RAE from Retinol (1105)" in entry["derivation_description"]
        assert entry["unpopulated_zero"] is False

    def test_published_rae_row_wins_even_when_zero(self):
        rae = {"nutrient": {"id": 1106, "name": "Vitamin A, RAE", "unitName": "µg"},
               "amount": 0.0, "dataPoints": 3,
               "foodNutrientDerivation": {"code": "A", "description": "Analytical"}}
        result = extract_nutrients({"foodNutrients": [rae, self._RETINOL_FULL]}, [1106])
        assert result[1106]["value"] == 0.0
        assert "Retinol" not in (result[1106]["derivation_description"] or "")

    def test_abridged_payload_number_319(self):
        payload = {"_abridged": True, "foodNutrients": [
            {"number": "319", "name": "Retinol", "unitName": "µg", "amount": 5.2,
             "derivationCode": "A", "derivationDescription": "Analytical"}]}
        result = extract_nutrients(payload, [1106])
        assert result[1106]["value"] == 5.2
        assert "RAE from Retinol (1105)" in result[1106]["derivation_description"]

    def test_backfill_request_without_1106_is_untouched(self):
        """backfill_nutrients requests only [1293, 1280]; no 1106 key may appear."""
        result = extract_nutrients({"foodNutrients": [self._RETINOL_FULL]}, [1293, 1280])
        assert 1106 not in result
        assert set(result) == {1293, 1280}
