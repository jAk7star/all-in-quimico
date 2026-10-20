import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import validate_questions as vq

KB, TAX = vq.load_kb()


@pytest.fixture
def questions():
    return copy.deepcopy(vq.load_questions())


def codes(report, kind="errors"):
    return {i.code for i in getattr(report, kind)}


def test_valid_questions_load_and_validate(questions):
    report = vq.validate_questions(questions, KB, TAX)
    assert report.ok, [str(e) for e in report.errors]


def test_missing_ref_detected(questions):
    q = questions[0]
    q["concept_refs"].append("CHEM-SOL-999")
    assert "MISSING_REF" in codes(vq.validate_questions([q], KB, TAX))


def test_undeclared_formula_in_step_detected(questions):
    q = next(q for q in questions if q["id"] == "Q-SOL-001")
    q["formula_refs"] = []
    assert "FORMULA_UNDECLARED" in codes(vq.validate_questions([q], KB, TAX))


def test_atomic_mass_mismatch_detected(questions):
    q = next(q for q in questions if q["id"] == "Q-SOL-008")
    q["given_data"]["massa_na"]["value"] = 24.0
    assert "ATOMIC_MASS_MISMATCH" in codes(vq.validate_questions([q], KB, TAX))


def test_unit_mismatch_detected_in_calc(questions):
    q = next(q for q in questions if q["id"] == "Q-SOL-001")
    q["given_data"]["volume_solucao"]["unit"] = "mol"
    assert "UNIT_MISMATCH" in codes(vq.validate_questions([q], KB, TAX))


def test_answer_mismatch_detected(questions):
    q = next(q for q in questions if q["id"] == "Q-SOL-001")
    q["calc"]["expected"]["value"] = 10.0
    assert "ANSWER_MISMATCH" in codes(vq.validate_questions([q], KB, TAX))


def test_missing_data_detected(questions):
    q = next(q for q in questions if q["id"] == "Q-SOL-001")
    del q["calc"]["inputs"]["V_solucao"]
    assert "MISSING_DATA" in codes(vq.validate_questions([q], KB, TAX))


def test_multiple_choice_duplicate_option(questions):
    q = next(q for q in questions if q["id"] == "Q-SOL-006")
    q["options"][1]["key"] = "A"
    assert "DUPLICATE_OPTION" in codes(vq.validate_questions([q], KB, TAX))


def test_multiple_choice_correct_has_mistake(questions):
    q = next(q for q in questions if q["id"] == "Q-SOL-006")
    q["options"][1]["mistake_ref"] = {"concept": "CHEM-SOL-001", "index": 0}
    assert "CORRECT_HAS_MISTAKE" in codes(vq.validate_questions([q], KB, TAX))


def test_multiple_choice_distractor_unjustified(questions):
    q = next(q for q in questions if q["id"] == "Q-SOL-006")
    del q["options"][0]["mistake_ref"]
    report = vq.validate_questions([q], KB, TAX)
    assert "DISTRACTOR_UNJUSTIFIED" in codes(report, "pending")


def test_duplicate_question_id(questions):
    q = questions[0]
    assert "DUPLICATE_ID" in codes(vq.validate_questions([q, dict(q)], KB, TAX))
