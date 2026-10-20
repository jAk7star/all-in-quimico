"""Testes de aceitação da SPEC-00 v0.1.0 (§14)."""

import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import validate_knowledge as vk

TAX = vk.load_taxonomy()


def codes(report, kind="errors"):
    return {i.code for i in getattr(report, kind)}


@pytest.fixture
def concept():
    return {
        "id": "CHEM-SOL-001", "type": "concept", "version": 1, "status": "approved",
        "name": "Concentração comum", "domain": "CHEM-SOL", "topics": ["concentracao"],
        "definition": "Relação entre massa de soluto e volume final da solução.",
        "sources": ["Fonte X"],
    }


@pytest.fixture
def records():
    return copy.deepcopy(vk.load_records())


def test_1_valid_base_loads_and_validates():
    report = vk.validate_directory()
    assert report.ok, [str(e) for e in report.errors]


def test_2_missing_required_field_rejected(concept):
    del concept["definition"]
    assert "SCHEMA" in codes(vk.validate_records([concept], TAX))


def test_3_duplicate_id_detected(concept):
    assert "DUPLICATE_ID" in codes(vk.validate_records([concept, dict(concept)], TAX))


def test_4_missing_reference_detected(concept):
    concept["prerequisites"] = ["CHEM-QTY-MASS"]
    assert "MISSING_REF" in codes(vk.validate_records([concept], TAX))


def test_4b_prerequisite_cycle_detected(concept):
    b = {**concept, "id": "CHEM-SOL-002", "prerequisites": ["CHEM-SOL-001"]}
    concept["prerequisites"] = ["CHEM-SOL-002"]
    assert "CYCLE" in codes(vk.validate_records([concept, b], TAX))


def test_5_invalid_status_rejected(concept):
    concept["status"] = "ok"
    assert "SCHEMA" in codes(vk.validate_records([concept], TAX))


def test_6_quantity_without_unit_rejected(records):
    el = next(r for r in records if r["type"] == "element")
    del el["atomic_mass_reference"]["unit"]
    assert "SCHEMA" in codes(vk.validate_records([el], TAX))
    f = next(r for r in records if r["type"] == "formula")
    del f["variables"]["m_soluto"]["unit"]
    assert "SCHEMA" in codes(vk.validate_records([f], TAX))


def test_6b_unit_incompatible_with_quantity_rejected(records):
    el = next(r for r in records if r["type"] == "element")
    el["atomic_mass_reference"]["unit"] = "mol/L"
    assert "UNIT_MISMATCH" in codes(vk.validate_records([el], TAX))


def test_6c_dimensional_inconsistency_rejected(records):
    f = next(r for r in records if r["id"] == "CHEM-FRM-001")
    f["variables"]["C"]["unit"] = "g"
    f["variables"]["C"]["quantity"] = "mass"
    assert "DIMENSION" in codes(vk.validate_records([f], TAX))


def test_7_formula_can_declare_molar_mass_dependency(records):
    f = next(r for r in records if r["id"] == "CHEM-FRM-003")
    assert f["data_dependencies"] == ["molar_mass"]
    assert vk.validate_records([f], TAX).ok
    f["variables"].pop("M")
    f["relation"]["right"] = "m"
    assert "DEPENDENCY_MISSING" in codes(vk.validate_records([f], TAX))


def test_8_structural_error_distinct_from_review_pending(concept):
    draft = {**concept, "status": "review"}
    r = vk.validate_records([draft], TAX)
    assert r.ok and "NOT_APPROVED" in codes(r, "pending")
    bad = {**concept, "status": "approved", "sources": []}
    r = vk.validate_records([bad], TAX)
    assert r.ok and "SOURCES_MISSING" in codes(r, "pending")


def test_9_approved_records_consumable_standalone(concept):
    draft = {**concept, "id": "CHEM-SOL-002", "status": "draft"}
    assert vk.approved_records([concept, draft]) == [concept]


def test_10_base_expands_without_touching_others(concept, records):
    new_domain = {"id": "CHEM-XYZ", "name": "Novo", "topics": ["t"]}
    tax = {**TAX, "domains": [*TAX["domains"], new_domain]}
    extra = {**concept, "id": "CHEM-XYZ-001", "domain": "CHEM-XYZ", "topics": ["t"]}
    assert vk.validate_records([*records, extra], tax).ok


def test_unknown_field_and_unknown_domain_rejected(concept):
    r = vk.validate_records([{**concept, "card_color": "red"}], TAX)
    assert "SCHEMA" in codes(r)
    r = vk.validate_records([{**concept, "domain": "CHEM-ZZZ"}], TAX)
    assert "UNKNOWN_DOMAIN" in codes(r)


def test_invalid_atomic_mass_rejected(records):
    el = next(r for r in records if r["type"] == "element")
    el["atomic_mass_reference"]["value"] = -1
    assert "INVALID_VALUE" in codes(vk.validate_records([el], TAX))


def test_pydantic_and_json_schema_agree(concept, records):
    import json

    from jsonschema import Draft202012Validator

    from models import validate_record

    schema = json.loads(vk.SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    el = next(r for r in records if r["type"] == "element")
    fm = next(r for r in records if r["type"] == "formula")
    samples = [concept, el, fm, {**concept, "card_color": "red"}, {**concept, "status": "ok"},
               {k: v for k, v in concept.items() if k != "definition"}]
    bad_el = copy.deepcopy(el)
    del bad_el["atomic_mass_reference"]["unit"]
    samples.append(bad_el)
    for s in samples:
        assert (not validate_record(s)) == validator.is_valid(s), s


def test_json_schema_file_is_up_to_date():
    import generate_schema

    assert vk.SCHEMA_PATH.read_text(encoding="utf-8") == generate_schema.build(), "rode: python generate_schema.py"
