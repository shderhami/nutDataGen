"""Golden-value pins for the intake source adapters, against the pinned repo
datasets. Values were hand-verified during the adapter build (2026-08-17) on
foods also validated in the 23-food sweep. If a pin breaks, either the data
file changed (it must not — see data/README.md SHAs) or an adapter regressed.
"""
import math

import pytest

from intake.model import (
    FEDIAF_BY_ID,
    Q_ANALYSED,
    Q_BORROWED,
    Q_CENSORED,
    Q_COMPUTED,
)


def _by_id(values, nid):
    hits = [sv for sv in values if sv.nutrient_id == nid]
    assert hits, f"no value for nutrient {nid}"
    return hits[0]


def _assert_fediaf_units(values):
    for sv in values:
        assert sv.nutrient_id in FEDIAF_BY_ID
        assert sv.unit == FEDIAF_BY_ID[sv.nutrient_id]["unit"]


class TestFCDB:
    @pytest.fixture(scope="class")
    def chicken_flesh(self):
        from intake.sources import fcdb
        return fcdb.extract(795)

    def test_units_and_coverage(self, chicken_flesh):
        _assert_fediaf_units(chicken_flesh)
        assert len(chicken_flesh) > 40

    def test_danish_analytical_protein_with_stats(self, chicken_flesh):
        sv = _by_id(chicken_flesh, 1003)
        assert math.isclose(sv.value, 19.2986, rel_tol=1e-4)
        assert sv.n == 30 and sv.quality == Q_ANALYSED

    def test_retinol_decoded_as_usda_1976_borrow(self, chicken_flesh):
        sv = _by_id(chicken_flesh, 1106)
        assert math.isclose(sv.value, 16 * 3.33)          # µg -> IU
        assert sv.quality == Q_BORROWED and "1976" in sv.note

    def test_choline_decoded_as_fdc_borrow(self, chicken_flesh):
        # Refines the sweep doctrine "choline: FCDB only": THIS food's choline
        # is itself FoodData Central lineage — not independent.
        sv = _by_id(chicken_flesh, 1180)
        assert sv.quality == Q_BORROWED and "FoodData Central" in sv.note

    def test_amino_acids_rescaled_to_grams(self, chicken_flesh):
        assert math.isclose(_by_id(chicken_flesh, 1213).value, 1.4124, rel_tol=1e-4)


class TestBLS:
    @pytest.fixture(scope="class")
    def chicken_flesh(self):
        from intake.sources import bls
        return bls.extract("V413000")

    def test_units(self, chicken_flesh):
        _assert_fediaf_units(chicken_flesh)

    def test_aggregation_rows_are_borrowed(self, chicken_flesh):
        sv = _by_id(chicken_flesh, 1003)
        assert sv.quality == Q_BORROWED and "Aggregation" in sv.note

    def test_chloride_and_b6_unit_rescale(self, chicken_flesh):
        assert _by_id(chicken_flesh, 1088).value == 85.0          # mg stays mg
        assert math.isclose(_by_id(chicken_flesh, 1175).value, 0.42)  # µg -> mg

    def test_vitamin_k_note_carries_forms(self, chicken_flesh):
        sv = _by_id(chicken_flesh, 1185)
        assert "VITK2=5.83" in sv.note

    def test_label_declaration_origin_is_borrowed(self):
        # round-2 audit: 'Labelangabe' (manufacturer package figure) fell to
        # unknown and counted as independent evidence
        from intake.sources.bls import _origin_quality
        assert _origin_quality("Labelangabe") == Q_BORROWED
        assert _origin_quality("Logische Null") == "computed"


class TestMEXT:
    @pytest.fixture(scope="class")
    def thigh(self):
        from intake.sources import mext
        return mext.extract("11224")

    def test_units_and_panels(self, thigh):
        _assert_fediaf_units(thigh)
        ids = {sv.nutrient_id for sv in thigh}
        assert {1210, 1213, 1269, 1278, 1272, 1293} <= ids  # AA + FA volumes joined

    def test_thiamin_hcl_form_conversion(self, thigh):
        sv = _by_id(thigh, 1165)
        assert math.isclose(sv.value, 0.12 * 0.887)
        assert "HCl" in sv.note

    def test_vitamin_k_total_and_retinol_iu(self, thigh):
        from intake.model import FORM_TOTAL_K
        k = _by_id(thigh, 1185)
        assert k.value == 23.0 and k.form == FORM_TOTAL_K
        assert math.isclose(_by_id(thigh, 1106).value, 16 * 3.33)

    def test_energy_is_computed(self, thigh):
        assert _by_id(thigh, 1008).quality == Q_COMPUTED


class TestCIQUAL:
    def test_leg_meat_k_forms_summed(self):
        from intake.model import FORM_TOTAL_K
        from intake.sources import ciqual
        sv = _by_id(ciqual.extract(36024), 1185)
        assert math.isclose(sv.value, 2.53 + 34.3)
        assert "K2=34.3" in sv.note
        assert sv.form == FORM_TOTAL_K

    def test_k1_without_k2_not_marked_total(self):
        from intake.model import FORM_K1_ONLY
        from intake.sources import ciqual
        sv = _by_id(ciqual.extract(36019), 1185)   # K1=2.9, K2 not reported
        assert sv.form == FORM_K1_ONLY

    def test_k2_traces_does_not_fabricate_a_total(self):
        # round-2 audit: a 'traces' K2 was treated as a measured menaquinone,
        # letting K1-only values defeat the form-defect rule (47 foods)
        from intake.model import FORM_K1_ONLY
        from intake.sources import ciqual
        sv = _by_id(ciqual.extract(20016), 1185)   # chou-fleur: K1=3.31, K2=traces
        assert math.isclose(sv.value, 3.31)
        assert sv.form == FORM_K1_ONLY and "traces" in sv.note

    def test_censored_iodine_upper_bound(self):
        from intake.sources import ciqual
        sv = _by_id(ciqual.extract(36002), 1100)   # "< 20"
        assert sv.value == 20.0 and sv.quality == Q_CENSORED

    def test_comma_decimals(self):
        from intake.sources import ciqual
        assert math.isclose(_by_id(ciqual.extract(36024), 1004).value, 4.05)


class TestAFCD:
    @pytest.fixture(scope="class")
    def thigh(self):
        from intake.sources import afcd
        return afcd.extract("F002806")

    def test_units(self, thigh):
        _assert_fediaf_units(thigh)

    def test_sampling_scan_downgrades_imputed_vitamin_d(self, thigh):
        sv = _by_id(thigh, 1110)
        assert sv.quality == Q_BORROWED and "imput" in sv.note.lower()

    def test_fatty_acid_mass_columns_used(self, thigh):
        assert math.isclose(_by_id(thigh, 1271).value, 0.02268)  # ARA mg -> g

    def test_analysed_biotin(self, thigh):
        sv = _by_id(thigh, 1176)
        assert sv.value == 3.7 and sv.quality == Q_ANALYSED


class TestCoFID:
    def test_dark_meat_values_and_refs(self):
        from intake.sources import cofid
        values = cofid.extract("18-289")
        _assert_fediaf_units(values)
        assert _by_id(values, 1176).value == 3.0
        assert "LGC" in _by_id(values, 1088).note   # underlying survey cited

    def test_unknown_code_raises(self):
        from intake.sources import cofid
        with pytest.raises(KeyError):
            cofid.extract("99-999")


class TestIodineDB:
    def test_roasted_thigh_stats(self):
        from intake.sources import iodine_db
        sv = iodine_db.extract("05098")[0]
        assert (sv.value, sv.n, sv.vmin, sv.vmax) == (0.9, 35, 0.0, 9.5)
        assert sv.quality == Q_ANALYSED
        assert sv.usda_lineage is True   # never independent confirmation
