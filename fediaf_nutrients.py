"""
FEDIAF 2024/2025 Nutrient Requirements Reference Data.

Complete reference data for all 50 nutrients required for cat food formulation
following FEDIAF Nutritional Guidelines.

Note: Taurine (USDA nutrient ID 1234) is defined in the USDA nutrient schema
but has no data in SR Legacy or Foundation datasets. Requires literature source.
"""
from typing import Optional

# Complete list of FEDIAF-required nutrients (50 total)
FEDIAF_NUTRIENTS = [
    # ========== Protein & Amino Acids (15 nutrients) ==========
    {
        "nutrient_id": 1003,
        "nutrient_name": "Crude Protein",
        "usda_name": "Protein",
        "unit": "g",
        "fediaf_required": True,
        "category": "Protein",
        "notes": ""
    },
    {
        "nutrient_id": 1220,
        "nutrient_name": "Arginine",
        "usda_name": "Arginine",
        "unit": "g",
        "fediaf_required": True,
        "category": "Amino Acid",
        "notes": "Requirement increases with protein content"
    },
    {
        "nutrient_id": 1221,
        "nutrient_name": "Histidine",
        "usda_name": "Histidine",
        "unit": "g",
        "fediaf_required": True,
        "category": "Amino Acid",
        "notes": ""
    },
    {
        "nutrient_id": 1212,
        "nutrient_name": "Isoleucine",
        "usda_name": "Isoleucine",
        "unit": "g",
        "fediaf_required": True,
        "category": "Amino Acid",
        "notes": ""
    },
    {
        "nutrient_id": 1213,
        "nutrient_name": "Leucine",
        "usda_name": "Leucine",
        "unit": "g",
        "fediaf_required": True,
        "category": "Amino Acid",
        "notes": ""
    },
    {
        "nutrient_id": 1214,
        "nutrient_name": "Lysine",
        "usda_name": "Lysine",
        "unit": "g",
        "fediaf_required": True,
        "category": "Amino Acid",
        "notes": ""
    },
    {
        "nutrient_id": 1215,
        "nutrient_name": "Methionine",
        "usda_name": "Methionine",
        "unit": "g",
        "fediaf_required": True,
        "category": "Amino Acid",
        "notes": ""
    },
    {
        "nutrient_id": 1216,
        "nutrient_name": "Cystine",
        "usda_name": "Cystine",
        "unit": "g",
        "fediaf_required": True,
        "category": "Amino Acid",
        "notes": "Analyzed as cysteic acid"
    },
    {
        "nutrient_id": 1217,
        "nutrient_name": "Phenylalanine",
        "usda_name": "Phenylalanine",
        "unit": "g",
        "fediaf_required": True,
        "category": "Amino Acid",
        "notes": ""
    },
    {
        "nutrient_id": 1218,
        "nutrient_name": "Tyrosine",
        "usda_name": "Tyrosine",
        "unit": "g",
        "fediaf_required": True,
        "category": "Amino Acid",
        "notes": "Important for black coat color"
    },
    {
        "nutrient_id": 1211,
        "nutrient_name": "Threonine",
        "usda_name": "Threonine",
        "unit": "g",
        "fediaf_required": True,
        "category": "Amino Acid",
        "notes": ""
    },
    {
        "nutrient_id": 1210,
        "nutrient_name": "Tryptophan",
        "usda_name": "Tryptophan",
        "unit": "g",
        "fediaf_required": True,
        "category": "Amino Acid",
        "notes": ""
    },
    {
        "nutrient_id": 1219,
        "nutrient_name": "Valine",
        "usda_name": "Valine",
        "unit": "g",
        "fediaf_required": True,
        "category": "Amino Acid",
        "notes": ""
    },

    # ========== Taurine (USDA ID 1234, no data in SR Legacy/Foundation) ==========
    {
        "nutrient_id": 1234,
        "nutrient_name": "Taurine",
        "usda_name": "Taurine",
        "unit": "mg",
        "fediaf_required": True,
        "category": "Amino Acid",
        "notes": "Critical for cats; Requires literature source (Spitze et al. 2003)"
    },

    # ========== Fats & Fatty Acids (6 nutrients) ==========
    {
        "nutrient_id": 1004,
        "nutrient_name": "Total Fat",
        "usda_name": "Total lipid (fat)",
        "unit": "g",
        "fediaf_required": True,
        "category": "Fat",
        "notes": "Crude Fat"
    },
    {
        "nutrient_id": 1269,
        "nutrient_name": "Linoleic acid",
        "usda_name": "PUFA 18:2",
        "unit": "g",
        "fediaf_required": True,
        "category": "Fatty Acid",
        "notes": "18:2 omega-6"
    },
    {
        "nutrient_id": 1271,
        "nutrient_name": "Arachidonic acid",
        "usda_name": "PUFA 20:4",
        "unit": "g",
        "fediaf_required": True,
        "category": "Fatty Acid",
        "notes": "20:4 omega-6 (PUFA 20:4); Critical for cats - cannot synthesize"
    },
    {
        "nutrient_id": 1270,
        "nutrient_name": "Alpha-linolenic acid",
        "usda_name": "PUFA 18:3",
        "unit": "g",
        "fediaf_required": True,
        "category": "Fatty Acid",
        "notes": "18:3 omega-3; Required for growth/reproduction"
    },
    {
        "nutrient_id": 1278,
        "nutrient_name": "EPA",
        "usda_name": "PUFA 20:5 n-3 (EPA)",
        "unit": "g",
        "fediaf_required": True,
        "category": "Fatty Acid",
        "notes": "20:5 omega-3; Mainly in fish"
    },
    {
        "nutrient_id": 1272,
        "nutrient_name": "DHA",
        "usda_name": "PUFA 22:6 n-3 (DHA)",
        "unit": "g",
        "fediaf_required": True,
        "category": "Fatty Acid",
        "notes": "22:6 omega-3 (PUFA 22:6 n-3); Mainly in fish"
    },

    # ========== Minerals (12 nutrients) ==========
    {
        "nutrient_id": 1087,
        "nutrient_name": "Calcium",
        "usda_name": "Calcium, Ca",
        "unit": "mg",
        "fediaf_required": True,
        "category": "Mineral",
        "notes": "Critical Ca:P ratio"
    },
    {
        "nutrient_id": 1091,
        "nutrient_name": "Phosphorus",
        "usda_name": "Phosphorus, P",
        "unit": "mg",
        "fediaf_required": True,
        "category": "Mineral",
        "notes": "Watch inorganic P in wet food"
    },
    {
        "nutrient_id": 1092,
        "nutrient_name": "Potassium",
        "usda_name": "Potassium, K",
        "unit": "mg",
        "fediaf_required": True,
        "category": "Mineral",
        "notes": ""
    },
    {
        "nutrient_id": 1093,
        "nutrient_name": "Sodium",
        "usda_name": "Sodium, Na",
        "unit": "mg",
        "fediaf_required": True,
        "category": "Mineral",
        "notes": ""
    },
    {
        "nutrient_id": 1088,
        "nutrient_name": "Chloride",
        "usda_name": "Chloride",
        "unit": "mg",
        "fediaf_required": True,
        "category": "Mineral",
        "notes": "Sparse/often missing in USDA"
    },
    {
        "nutrient_id": 1090,
        "nutrient_name": "Magnesium",
        "usda_name": "Magnesium, Mg",
        "unit": "mg",
        "fediaf_required": True,
        "category": "Mineral",
        "notes": ""
    },
    {
        "nutrient_id": 1089,
        "nutrient_name": "Iron",
        "usda_name": "Iron, Fe",
        "unit": "mg",
        "fediaf_required": True,
        "category": "Mineral",
        "notes": "Oxide/carbonate forms not bioavailable"
    },
    {
        "nutrient_id": 1098,
        "nutrient_name": "Copper",
        "usda_name": "Copper, Cu",
        "unit": "mg",
        "fediaf_required": True,
        "category": "Mineral",
        "notes": "Copper oxide not bioavailable"
    },
    {
        "nutrient_id": 1101,
        "nutrient_name": "Manganese",
        "usda_name": "Manganese, Mn",
        "unit": "mg",
        "fediaf_required": True,
        "category": "Mineral",
        "notes": ""
    },
    {
        "nutrient_id": 1095,
        "nutrient_name": "Zinc",
        "usda_name": "Zinc, Zn",
        "unit": "mg",
        "fediaf_required": True,
        "category": "Mineral",
        "notes": ""
    },
    {
        "nutrient_id": 1100,
        "nutrient_name": "Iodine",
        "usda_name": "Iodine",
        "unit": "µg",
        "fediaf_required": True,
        "category": "Mineral",
        "notes": "Sparse/often missing in USDA"
    },
    {
        "nutrient_id": 1103,
        "nutrient_name": "Selenium",
        "usda_name": "Selenium, Se",
        "unit": "µg",
        "fediaf_required": True,
        "category": "Mineral",
        "notes": "Different requirements for wet vs dry"
    },

    # ========== Vitamins (13 nutrients) ==========
    {
        "nutrient_id": 1106,
        "nutrient_name": "Vitamin A",
        "usda_name": "Vitamin A, RAE",
        "unit": "IU",
        "fediaf_required": True,
        "category": "Vitamin",
        "notes": "As RAE, convert to IU"
    },
    {
        "nutrient_id": 1110,
        "nutrient_name": "Vitamin D",
        "usda_name": "Vitamin D (D2 + D3), International Units",
        "unit": "IU",
        "fediaf_required": True,
        "category": "Vitamin",
        "notes": "As µg, convert to IU"
    },
    {
        "nutrient_id": 1109,
        "nutrient_name": "Vitamin E",
        "usda_name": "Vitamin E (alpha-tocopherol)",
        "unit": "IU",
        "fediaf_required": True,
        "category": "Vitamin",
        "notes": "As mg, convert to IU"
    },
    {
        "nutrient_id": 1185,
        "nutrient_name": "Vitamin K",
        "usda_name": "Vitamin K (phylloquinone)",
        "unit": "µg",
        "fediaf_required": True,
        "category": "Vitamin",
        "notes": "Sparse; Usually not needed unless high fish diet"
    },
    {
        "nutrient_id": 1165,
        "nutrient_name": "Thiamin",
        "usda_name": "Thiamin",
        "unit": "mg",
        "fediaf_required": True,
        "category": "Vitamin",
        "notes": "B1"
    },
    {
        "nutrient_id": 1166,
        "nutrient_name": "Riboflavin",
        "usda_name": "Riboflavin",
        "unit": "mg",
        "fediaf_required": True,
        "category": "Vitamin",
        "notes": "B2"
    },
    {
        "nutrient_id": 1167,
        "nutrient_name": "Niacin",
        "usda_name": "Niacin",
        "unit": "mg",
        "fediaf_required": True,
        "category": "Vitamin",
        "notes": "B3"
    },
    {
        "nutrient_id": 1170,
        "nutrient_name": "Pantothenic acid",
        "usda_name": "Pantothenic acid",
        "unit": "mg",
        "fediaf_required": True,
        "category": "Vitamin",
        "notes": "B5"
    },
    {
        "nutrient_id": 1175,
        "nutrient_name": "Pyridoxine",
        "usda_name": "Vitamin B-6",
        "unit": "mg",
        "fediaf_required": True,
        "category": "Vitamin",
        "notes": "B6; Requirement increases with protein"
    },
    {
        "nutrient_id": 1177,
        "nutrient_name": "Folic acid",
        "usda_name": "Folate, total",
        "unit": "µg",
        "fediaf_required": True,
        "category": "Vitamin",
        "notes": "B9"
    },
    {
        "nutrient_id": 1178,
        "nutrient_name": "Cobalamin",
        "usda_name": "Vitamin B-12",
        "unit": "µg",
        "fediaf_required": True,
        "category": "Vitamin",
        "notes": "B12"
    },
    {
        "nutrient_id": 1176,
        "nutrient_name": "Biotin",
        "usda_name": "Biotin",
        "unit": "µg",
        "fediaf_required": True,
        "category": "Vitamin",
        "notes": "B7; Sparse/often missing in USDA"
    },
    {
        "nutrient_id": 1180,
        "nutrient_name": "Choline",
        "usda_name": "Choline, total",
        "unit": "mg",
        "fediaf_required": True,
        "category": "Vitamin",
        "notes": "Often missing in USDA"
    },

    # ========== Other Essential Data (5 nutrients) ==========
    {
        "nutrient_id": 1008,
        "nutrient_name": "Energy",
        "usda_name": "Energy",
        "unit": "kcal",
        "fediaf_required": True,
        "category": "Other",
        "notes": "For calculating per-1000kcal values"
    },
    {
        "nutrient_id": 1051,
        "nutrient_name": "Water",
        "usda_name": "Water",
        "unit": "g",
        "fediaf_required": True,
        "category": "Other",
        "notes": "Moisture; For dry matter calculations"
    },
    {
        "nutrient_id": 1007,
        "nutrient_name": "Ash",
        "usda_name": "Ash",
        "unit": "g",
        "fediaf_required": True,
        "category": "Other",
        "notes": "Useful for mineral estimation"
    },
    {
        "nutrient_id": 1079,
        "nutrient_name": "Crude Fiber",
        "usda_name": "Fiber, total dietary",
        "unit": "g",
        "fediaf_required": True,
        "category": "Other",
        "notes": "Fiber, total dietary"
    },
    {
        "nutrient_id": 1005,
        "nutrient_name": "Carbohydrate",
        "usda_name": "Carbohydrate, by difference",
        "unit": "g",
        "fediaf_required": True,
        "category": "Other",
        "notes": "Carbohydrate, by difference"
    },
]


def get_all_nutrients() -> list[dict]:
    """Returns complete FEDIAF nutrient list."""
    return FEDIAF_NUTRIENTS.copy()


def get_usda_nutrient_ids() -> list[int]:
    """Returns list of USDA nutrient IDs to fetch (non-None IDs only)."""
    return [
        n["nutrient_id"]
        for n in FEDIAF_NUTRIENTS
        if n["nutrient_id"] is not None
    ]


def get_nutrient_by_id(nutrient_id: int) -> Optional[dict]:
    """Returns nutrient info by USDA ID, or None if not found."""
    for nutrient in FEDIAF_NUTRIENTS:
        if nutrient["nutrient_id"] == nutrient_id:
            return nutrient.copy()
    return None


def get_nutrient_by_name(name: str) -> Optional[dict]:
    """Returns nutrient info by name (case-insensitive), or None if not found."""
    name_lower = name.lower()
    for nutrient in FEDIAF_NUTRIENTS:
        if nutrient["nutrient_name"].lower() == name_lower:
            return nutrient.copy()
    return None


# TAURINE_NUTRIENT_ID is used to identify taurine (USDA ID 1234, no data in datasets)
TAURINE_NUTRIENT_ID = 1234


def get_taurine_nutrient() -> Optional[dict]:
    """Returns the taurine nutrient info (always missing from USDA)."""
    return get_nutrient_by_id(TAURINE_NUTRIENT_ID)




def get_nutrients_by_category(category: str) -> list[dict]:
    """Returns nutrients in a specific category."""
    return [
        n.copy()
        for n in FEDIAF_NUTRIENTS
        if n["category"].lower() == category.lower()
    ]
