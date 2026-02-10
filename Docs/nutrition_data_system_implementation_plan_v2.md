# USDA Nutrition Data Extraction and Comparison System

## Implementation Plan v2.0 - Multi-Step with Testing

---

## Overview

This system extracts nutritional data from USDA FoodData Central databases (SR Legacy and Foundation Foods), compares them, and allows user-guided resolution of discrepancies. The goal is to build a validated nutrition database for cat food formulation following FEDIAF 2025 guidelines.

---

## System Goals

1. Extract nutrition data from SR Legacy database via API for FEDIAF-required nutrients
2. Extract matching data from Foundation Foods database via API
3. Compare the two datasets and identify discrepancies
4. Present discrepancies to user for decision-making
5. Store finalized, validated nutrition data to CSV database

---

## Part 1: Complete FEDIAF 2024/2025 Nutrient Requirements for Cats

Based on FEDIAF Nutritional Guidelines (July 2024), the following nutrients are required for complete cat food formulation.

### 1.1 Protein & Amino Acids (15 nutrients)

| # | Nutrient | USDA ID | Unit | USDA Available | Notes |
|---|----------|---------|------|----------------|-------|
| 1 | Crude Protein | 1003 | g | Yes | |
| 2 | Arginine | 1217 | g | Yes | Requirement increases with protein content |
| 3 | Histidine | 1218 | g | Yes | |
| 4 | Isoleucine | 1220 | g | Yes | |
| 5 | Leucine | 1221 | g | Yes | |
| 6 | Lysine | 1222 | g | Yes | |
| 7 | Methionine | 1223 | g | Yes | |
| 8 | Cystine | 1213 | g | Yes | Analyzed as cysteic acid |
| 9 | Methionine + Cystine | - | g | Calculated | Sum of 1223 + 1213 |
| 10 | Phenylalanine | 1214 | g | Yes | |
| 11 | Tyrosine | 1215 | g | Yes | Important for black coat color |
| 12 | Phenylalanine + Tyrosine | - | g | Calculated | Sum of 1214 + 1215 |
| 13 | Threonine | 1224 | g | Yes | |
| 14 | Tryptophan | 1210 | g | Yes | |
| 15 | Valine | 1227 | g | Yes | |

### 1.2 Taurine (CRITICAL - Not in USDA)

| # | Nutrient | USDA ID | Unit | USDA Available | Notes |
|---|----------|---------|------|----------------|-------|
| 16 | Taurine (canned/wet food) | - | g | **NO** | Requires literature source (Spitze et al. 2003) |
| 17 | Taurine (dry food) | - | g | **NO** | Lower requirement than wet food |

### 1.3 Fats & Fatty Acids (6 nutrients)

| # | Nutrient | USDA ID | Unit | USDA Available | Notes |
|---|----------|---------|------|----------------|-------|
| 18 | Total Fat (Crude Fat) | 1004 | g | Yes | |
| 19 | Linoleic acid (18:2 ω-6) | 1269 | g | Yes | |
| 20 | Arachidonic acid (20:4 ω-6) | 1271 | mg | Sparse | Critical for cats - cannot synthesize |
| 21 | Alpha-linolenic acid (18:3 ω-3) | 1270 | g | Yes | Required for growth/reproduction |
| 22 | EPA (20:5 ω-3) | 1278 | g | Yes | Mainly in fish |
| 23 | DHA (22:6 ω-3) | 1279 | g | Yes | Mainly in fish |

### 1.4 Minerals (12 nutrients)

| # | Nutrient | USDA ID | Unit | USDA Available | Notes |
|---|----------|---------|------|----------------|-------|
| 24 | Calcium | 1087 | g | Yes | Critical Ca:P ratio |
| 25 | Phosphorus | 1091 | g | Yes | Watch inorganic P in wet food |
| 26 | Potassium | 1092 | g | Yes | |
| 27 | Sodium | 1093 | g | Yes | |
| 28 | Chloride | 1088 | mg | **Sparse** | Often missing |
| 29 | Magnesium | 1090 | g | Yes | |
| 30 | Iron | 1089 | mg | Yes | Oxide/carbonate forms not bioavailable |
| 31 | Copper | 1098 | mg | Yes | Copper oxide not bioavailable |
| 32 | Manganese | 1101 | mg | Yes | |
| 33 | Zinc | 1095 | mg | Yes | |
| 34 | Iodine | 1100 | µg | **Sparse** | Often missing |
| 35 | Selenium | 1103 | µg | Yes | Different requirements for wet vs dry |

### 1.5 Vitamins (13 nutrients)

| # | Nutrient | USDA ID | Unit | USDA Available | Notes |
|---|----------|---------|------|----------------|-------|
| 36 | Vitamin A | 1106 | IU | Yes | As RAE, convert to IU |
| 37 | Vitamin D | 1110 | IU | Yes | As µg, convert to IU |
| 38 | Vitamin E | 1109 | IU | Yes | As mg, convert to IU |
| 39 | Vitamin K | 1185 | µg | **Sparse** | Usually not needed unless high fish |
| 40 | Thiamin (B1) | 1165 | mg | Yes | |
| 41 | Riboflavin (B2) | 1166 | mg | Yes | |
| 42 | Niacin (B3) | 1167 | mg | Yes | |
| 43 | Pantothenic acid (B5) | 1170 | mg | Yes | |
| 44 | Pyridoxine (B6) | 1175 | mg | Yes | Requirement increases with protein |
| 45 | Folic acid (B9) | 1177 | µg | Yes | |
| 46 | Cobalamin (B12) | 1178 | µg | Yes | |
| 47 | Biotin (B7) | 1176 | µg | **Sparse** | Often missing |
| 48 | Choline | 1180 | mg | Yes | Often missing in USDA |

### 1.6 Other Essential Data

| # | Nutrient | USDA ID | Unit | USDA Available | Notes |
|---|----------|---------|------|----------------|-------|
| 49 | Energy | 1008 | kcal | Yes | For calculating per-1000kcal values |
| 50 | Water/Moisture | 1051 | g | Yes | For dry matter calculations |
| 51 | Ash | 1007 | g | Yes | Useful for mineral estimation |

### 1.7 Summary: Nutrients Requiring External Sources

| Nutrient | Reason | Recommended Source |
|----------|--------|-------------------|
| **Taurine** | Not in USDA | Spitze et al. 2003; literature |
| **Iodine** | Sparse/missing | INRAE tables; literature |
| **Chloride** | Sparse/missing | INRAE tables; literature |
| **Biotin** | Sparse/missing | Literature |
| **Vitamin K** | Sparse/missing | Literature (if high fish diet) |
| **Arachidonic acid** | Sparse | May need literature supplement |

---

## Part 2: Data Schema

### 2.1 Final Schema (CSV format)

```
food_id              - string  - Your internal identifier
food_name            - string  - Standardized food name
sr_legacy_fdc_id     - integer - SR Legacy FDC ID
foundation_fdc_id    - integer - Foundation FDC ID (nullable)
life_stage           - enum    - Life stage: adult | growth | reproduction
nutrient_id          - integer - USDA nutrient ID (null for non-USDA nutrients)
nutrient_name        - string  - Nutrient name
unit                 - string  - Unit of measure (g, mg, µg, IU, kcal)
value                - float   - The working/final value
source               - string  - Data source (default: sr_legacy)
fediaf_required      - boolean - Is this required by FEDIAF
last_updated         - date    - When row was last modified
comment              - string  - Appended notes on changes (nullable)
```

### 2.2 Life Stage Values

| Value | Description | FEDIAF Reference |
|-------|-------------|------------------|
| `adult` | Adult maintenance (typical 75-100 kcal/kg^0.67) | Table III-4a column: Adult |
| `growth` | Kittens, growing cats | Table III-4a column: Growth |
| `reproduction` | Gestation and lactation | Table III-4a column: Reproduction |

**Note:** FEDIAF specifies different minimum requirements for each life stage. The `life_stage` field determines which FEDIAF thresholds apply when validating nutrient adequacy.

### 2.3 Source Field Values

| Value | Description |
|-------|-------------|
| `sr_legacy` | Default, from USDA SR Legacy database |
| `foundation` | Changed to USDA Foundation Foods |
| `literature` | From published scientific paper |
| `manual` | Manually entered by user |
| `calculated` | Derived value (e.g., Met+Cys sum) |

---

## Part 3: Multi-Step Implementation Plan

### Phase 1: Foundation Setup
**Goal:** Create project structure and configuration

#### Step 1.1: Project Structure
Create the following directory and file structure:

```
nutrition_data_system/
├── config.py
├── fediaf_nutrients.py
├── usda_api.py
├── comparison.py
├── user_interaction.py
├── database.py
├── main.py
├── tests/
│   ├── test_config.py
│   ├── test_fediaf_nutrients.py
│   ├── test_usda_api.py
│   ├── test_comparison.py
│   ├── test_database.py
│   └── test_integration.py
└── data/
    └── .gitkeep
```

#### Step 1.2: config.py
**Contents:**
- `API_KEY`: USDA FoodData Central API key (read from environment variable)
- `BASE_URL`: `https://api.nal.usda.gov/fdc/v1`
- `DISCREPANCY_THRESHOLDS`: Dictionary
  - `trivial`: 5
  - `moderate`: 15
  - `significant`: 30
- `DATA_DIR`: Path to data directory
- `DATABASE_FILE`: `data/nutrition_database.csv`

**Testing (test_config.py):**
```
- Test that all required config values exist
- Test that thresholds are positive numbers
- Test that paths are valid strings
```

---

### Phase 2: FEDIAF Nutrients Reference
**Goal:** Create complete reference data for all 51 required nutrients

#### Step 2.1: fediaf_nutrients.py
**Contents:**

Define `FEDIAF_NUTRIENTS` as a list of dictionaries:

```python
{
    "nutrient_id": int or None,      # USDA ID, None if not in USDA
    "nutrient_name": str,            # Standard name
    "unit": str,                     # g, mg, µg, IU, kcal
    "fediaf_required": True,
    "usda_available": bool,          # Is this in USDA?
    "category": str,                 # Protein, Amino Acid, Fat, Fatty Acid, Mineral, Vitamin, Other
    "is_calculated": bool,           # True for Met+Cys, Phe+Tyr
    "calculation_components": list,  # nutrient_ids to sum, if calculated
    "notes": str                     # Any special notes
}
```

**Functions:**
- `get_all_nutrients() -> list[dict]`: Returns complete FEDIAF nutrient list
- `get_usda_nutrient_ids() -> list[int]`: Returns list of USDA nutrient IDs to fetch
- `get_nutrient_by_id(nutrient_id: int) -> dict`: Returns nutrient info by USDA ID
- `get_nutrient_by_name(name: str) -> dict`: Returns nutrient info by name
- `get_missing_from_usda() -> list[dict]`: Returns nutrients not in USDA
- `get_calculated_nutrients() -> list[dict]`: Returns nutrients that need calculation

**Testing (test_fediaf_nutrients.py):**
```
- Test that FEDIAF_NUTRIENTS contains exactly 51 entries
- Test that all required fields are present in each entry
- Test get_usda_nutrient_ids() returns only non-None IDs
- Test get_nutrient_by_id() returns correct nutrient
- Test get_nutrient_by_id() returns None for invalid ID
- Test get_missing_from_usda() includes Taurine
- Test get_calculated_nutrients() includes Met+Cys and Phe+Tyr
- Test that calculated nutrients have valid component IDs
```

---

### Phase 3: USDA API Integration
**Goal:** Fetch nutrition data from USDA FoodData Central

#### Step 3.1: usda_api.py
**Functions:**

```python
def fetch_food_data(fdc_id: int, api_key: str) -> dict:
    """
    Fetch raw food data from USDA API.
    Returns complete JSON response.
    Raises exception on API error.
    """

def extract_nutrients(food_data: dict, nutrient_ids: list[int]) -> dict:
    """
    Extract specific nutrients from API response.
    Returns dict: {nutrient_id: {"name": str, "value": float, "unit": str}}
    Missing nutrients have value = None
    """

def fetch_sr_legacy(fdc_id: int, api_key: str) -> dict:
    """
    Fetch SR Legacy food and extract FEDIAF-required nutrients.
    Returns dict with food metadata and nutrients.
    """

def fetch_foundation(fdc_id: int, api_key: str) -> dict:
    """
    Fetch Foundation Foods and extract FEDIAF-required nutrients.
    Returns dict with food metadata and nutrients.
    """

def get_food_description(fdc_id: int, api_key: str) -> str:
    """
    Quick lookup of food description by FDC ID.
    """
```

**Testing (test_usda_api.py):**
```
- Test fetch_food_data() with valid FDC ID (use known chicken thigh ID: 171116)
- Test fetch_food_data() raises exception for invalid FDC ID
- Test extract_nutrients() returns correct structure
- Test extract_nutrients() handles missing nutrients (returns None)
- Test fetch_sr_legacy() returns expected nutrients for chicken thigh
- Test fetch_foundation() returns expected nutrients (if Foundation ID available)
- Test that protein value for chicken thigh is in reasonable range (15-25g)
```

**Mock Testing:**
- Create mock API responses for offline testing
- Test error handling for network failures
- Test rate limit handling

---

### Phase 4: Comparison Engine
**Goal:** Compare SR Legacy and Foundation Foods data, identify discrepancies

#### Step 4.1: comparison.py
**Functions:**

```python
def calculate_discrepancy(sr_value: float, foundation_value: float) -> dict:
    """
    Calculate percentage difference between two values.
    Returns: {
        "sr_value": float,
        "foundation_value": float,
        "percentage": float,
        "tier": str  # trivial/moderate/significant/major
    }
    """

def classify_tier(percentage: float) -> str:
    """
    Classify discrepancy into tier based on thresholds.
    """

def compare_nutrients(sr_data: dict, foundation_data: dict) -> dict:
    """
    Compare nutrients from both sources.
    Returns: {
        "matches": [...],           # < 5% difference
        "discrepancies": [...],     # >= 5% difference, both have values
        "sr_only": [...],           # Only in SR Legacy
        "foundation_only": [...],   # Only in Foundation
        "missing_both": [...]       # Missing from both sources
    }
    """

def generate_comparison_report(food_name: str, sr_fdc_id: int, 
                                foundation_fdc_id: int, comparison: dict) -> str:
    """
    Generate human-readable comparison report.
    """
```

**Testing (test_comparison.py):**
```
- Test calculate_discrepancy() with identical values (0%)
- Test calculate_discrepancy() with 10% difference
- Test calculate_discrepancy() with 50% difference
- Test classify_tier() returns correct tier for each threshold boundary
- Test compare_nutrients() correctly categorizes matching nutrients
- Test compare_nutrients() correctly identifies discrepancies
- Test compare_nutrients() handles sr_only nutrients
- Test compare_nutrients() handles missing_both nutrients
- Test generate_comparison_report() produces readable output
```

---

### Phase 5: Database Operations
**Goal:** CSV read/write operations for persistent storage

#### Step 5.1: database.py
**Functions:**

```python
def initialize_database(filepath: str) -> None:
    """
    Create empty database file with headers if not exists.
    """

def load_database(filepath: str) -> list[dict]:
    """
    Load database from CSV file.
    Returns list of row dictionaries.
    """

def save_database(data: list[dict], filepath: str) -> None:
    """
    Save complete database to CSV file.
    """

def add_food_nutrients(food_nutrients: list[dict], filepath: str) -> None:
    """
    Add new food nutrient rows to database.
    Checks for duplicates (food_id + nutrient_id).
    """

def get_food_by_id(food_id: str, filepath: str) -> list[dict]:
    """
    Get all nutrient rows for a specific food.
    """

def update_nutrient(food_id: str, nutrient_id: int, 
                    updates: dict, filepath: str) -> bool:
    """
    Update specific nutrient for a food.
    Appends to comment field rather than replacing.
    """

def food_exists(food_id: str, filepath: str) -> bool:
    """
    Check if food_id already exists in database.
    """

def get_all_food_ids(filepath: str) -> list[str]:
    """
    Get list of all unique food_ids in database.
    """
```

**Testing (test_database.py):**
```
- Test initialize_database() creates file with correct headers
- Test load_database() returns empty list for empty file
- Test save_database() and load_database() round-trip
- Test add_food_nutrients() adds new rows
- Test add_food_nutrients() rejects duplicates
- Test get_food_by_id() returns correct rows
- Test get_food_by_id() returns empty list for unknown food
- Test update_nutrient() modifies correct row
- Test update_nutrient() appends to comment
- Test food_exists() returns correct boolean
```

---

### Phase 6: User Interaction
**Goal:** Command-line interface for user decisions

#### Step 6.1: user_interaction.py
**Functions:**

```python
def display_comparison_report(report: str) -> None:
    """
    Print formatted comparison report to console.
    """

def prompt_food_info() -> dict:
    """
    Prompt user for food_id, food_name, sr_fdc_id, foundation_fdc_id.
    Returns dict with user inputs.
    """

def prompt_discrepancy_decision(discrepancy: dict) -> dict:
    """
    Display discrepancy details and prompt for decision.
    Options:
        1. Keep SR Legacy
        2. Use Foundation
        3. Enter manual value
        4. Skip (flag for later)
    Returns: {
        "nutrient_id": int,
        "chosen_value": float,
        "chosen_source": str,
        "comment": str
    }
    """

def prompt_missing_nutrient(nutrient: dict) -> dict:
    """
    Prompt user for value of nutrient missing from USDA.
    Options:
        1. Enter value from literature
        2. Skip for now
    Returns decision dict.
    """

def prompt_confirmation(message: str) -> bool:
    """
    Generic yes/no confirmation prompt.
    """

def display_final_summary(food_data: list[dict]) -> None:
    """
    Display final nutrient table before saving.
    """

def display_progress(current: int, total: int, item_name: str) -> None:
    """
    Display progress indicator.
    """
```

**Testing (test_user_interaction.py):**
```
- Test prompt functions with mocked input
- Test input validation (reject invalid choices)
- Test display functions produce expected output format
- Test confirmation prompt handles y/n/yes/no
```

---

### Phase 7: Main Application & Integration
**Goal:** Orchestrate complete workflow

#### Step 7.1: main.py
**Main Workflow:**

```python
def main():
    """
    Main entry point.
    1. Display welcome message
    2. Loop:
        a. Prompt for food info
        b. Check if food exists
        c. Fetch SR Legacy data
        d. Fetch Foundation data (if provided)
        e. Compare and display discrepancies
        f. Process user decisions
        g. Handle missing nutrients
        h. Calculate derived nutrients (Met+Cys, Phe+Tyr)
        i. Display final summary
        j. Confirm and save
        k. Ask to continue
    """

def process_single_food(food_info: dict) -> list[dict]:
    """
    Process one food item through complete workflow.
    Returns list of nutrient records ready for saving.
    """

def build_nutrient_record(food_id, food_name, sr_fdc_id, foundation_fdc_id,
                          nutrient_id, nutrient_name, unit, value, 
                          source, fediaf_required, comment) -> dict:
    """
    Create single nutrient record matching schema.
    """

def calculate_derived_nutrients(nutrients: dict) -> dict:
    """
    Calculate Met+Cys, Phe+Tyr from component values.
    """
```

**Testing (test_integration.py):**
```
- Test complete workflow with mocked API and user input
- Test that all 51 nutrients are processed
- Test that calculated nutrients are computed correctly
- Test that final output matches schema
- Test error recovery (API failure mid-process)
```

---

## Part 4: Implementation Steps with Testing Checkpoints

### Step-by-Step Implementation Order

| Step | Module | Description | Testing Checkpoint |
|------|--------|-------------|-------------------|
| 1 | config.py | Basic configuration | Run test_config.py - all pass |
| 2 | fediaf_nutrients.py | Nutrient reference data | Run test_fediaf_nutrients.py - all pass |
| 3 | usda_api.py (fetch only) | Basic API fetch | Test with single FDC ID manually |
| 4 | usda_api.py (complete) | Extract nutrients | Run test_usda_api.py - all pass |
| 5 | comparison.py | Comparison logic | Run test_comparison.py - all pass |
| 6 | database.py | CSV operations | Run test_database.py - all pass |
| 7 | user_interaction.py | CLI prompts | Run test_user_interaction.py - all pass |
| 8 | main.py | Integration | Run test_integration.py - all pass |
| 9 | End-to-end test | Full workflow | Process chicken thigh successfully |

### Testing Commands

After each step, run:

```bash
# Run specific test file
python -m pytest tests/test_<module>.py -v

# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html
```

---

## Part 5: Example Session Output

```
========================================
USDA Nutrition Data Extraction System
========================================

Enter food_id: CHKN_THIGH_RAW_001
Enter food_name: Chicken thigh, meat only, raw
Enter SR Legacy FDC ID: 171116
Enter Foundation FDC ID (or press Enter to skip): 746784

Fetching SR Legacy data for FDC ID 171116...
✓ Retrieved 45 of 51 FEDIAF-required nutrients

Fetching Foundation data for FDC ID 746784...
✓ Retrieved 38 of 51 FEDIAF-required nutrients

========================================
COMPARISON REPORT
========================================
Food: Chicken thigh, meat only, raw
SR Legacy FDC: 171116 | Foundation FDC: 746784

Summary:
  - Matching (< 5% difference): 31 nutrients
  - Discrepancies (≥ 5%): 4 nutrients
  - SR Legacy only: 7 nutrients
  - Missing from both: 6 nutrients

----------------------------------------
DISCREPANCIES REQUIRING REVIEW
----------------------------------------

[1/4] Iron (ID: 1089)
      SR Legacy:  1.30 mg
      Foundation: 0.89 mg
      Difference: 31.5% [MAJOR]
      
      Action:
        [1] Keep SR Legacy (1.30 mg)
        [2] Use Foundation (0.89 mg)
        [3] Enter manual value
        [4] Skip for later
      
      Your choice: 2
      Reason (optional): Foundation n=12, better sampling
      
      ✓ Iron = 0.89 mg (source: foundation)

... (more discrepancies) ...

----------------------------------------
NUTRIENTS MISSING FROM USDA
----------------------------------------

[1/6] Taurine
      Not available in USDA databases.
      
      Action:
        [1] Enter value from literature
        [2] Skip for now
      
      Your choice: 1
      Enter value: 170
      Enter source: Spitze et al. 2003
      
      ✓ Taurine = 170 mg (source: literature)

... (more missing nutrients) ...

----------------------------------------
CALCULATED NUTRIENTS
----------------------------------------
  ✓ Methionine + Cystine = 0.68 g (0.44 + 0.24)
  ✓ Phenylalanine + Tyrosine = 1.23 g (0.65 + 0.58)

========================================
FINAL SUMMARY
========================================
Food: Chicken thigh, meat only, raw (CHKN_THIGH_RAW_001)

Total nutrients: 51
  - From SR Legacy: 38
  - From Foundation: 4
  - From Literature: 6
  - Calculated: 2
  - Skipped: 1

Save to database? [Y/n]: Y

✓ Saved 51 nutrient records to data/nutrition_database.csv

----------------------------------------
Process another food? [Y/n]: 
```

---

## Part 6: Dependencies

```
requests>=2.28.0    # API calls
pytest>=7.0.0       # Testing
pytest-cov>=4.0.0   # Coverage reporting
```

No database dependencies - using CSV for simplicity.

---

## Part 7: Getting Started

1. **Get API Key:**
   - Visit: https://fdc.nal.usda.gov/api-key-signup.html
   - Set environment variable: `export USDA_API_KEY=your_key_here`

2. **Install Dependencies:**
   ```bash
   pip install requests pytest pytest-cov
   ```

3. **Run Tests:**
   ```bash
   python -m pytest tests/ -v
   ```

4. **Run Application:**
   ```bash
   python main.py
   ```

---

## Part 8: Known FDC IDs for Testing

| Food | SR Legacy FDC ID | Foundation FDC ID |
|------|------------------|-------------------|
| Chicken thigh, raw | 171116 | 746784 |
| Chicken liver, raw | 171062 | 748967 |
| Salmon, Atlantic, raw | 175167 | 746764 |
| Egg yolk, raw | 172185 | 748626 |
| Beef, ground, raw | 174036 | 746760 |

Use these for testing during development.
