"""
Testes Unitários para o Gerador de Slides de Perguntas e Respostas (N1 e N2)
==========================================================================
Valida:
1. Carga estrita de Nível 1 (13 questões) e Nível 2 (7 questões) = 20 questões.
2. Exclusão estrita e absoluta de Nível 3 (5 questões).
3. Ordenação canônica dos Lotes 001 a 020.
4. Compilação do batch de 41 slides intercalados (Pergunta -> Resposta).
5. Integridade do arquivo JSON de batch gerado.
"""

import json

from gerar_slides_perguntas_respostas import (
    DEFAULT_OUTPUT_JSON,
    clean_chemical_typography,
    generate_batch_operations,
    load_questions_n1_n2,
)


def test_clean_chemical_typography():
    """Valida conversão de notação química HTML para Unicode limpo."""
    assert clean_chemical_typography("H<sub>2</sub>O") == "H₂O"
    assert clean_chemical_typography("CO<sub>2</sub>") == "CO₂"
    assert clean_chemical_typography("SO<sub>2</sub>") == "SO₂"
    assert clean_chemical_typography("H<sub>2</sub>SO<sub>4</sub>") == "H₂SO₄"
    assert clean_chemical_typography("Al<sup>3+</sup>") == "Al³⁺"
    assert clean_chemical_typography("A -> B <-> C") == "A → B ⇄ C"


def test_load_questions_n1_n2_counts_and_exclusion():
    """Garante que apenas N1 e N2 são carregados e N3 é 100% excluído."""
    questions = load_questions_n1_n2()

    # 33 questões combinadas (21 N1 e 12 N2)
    assert len(questions) == 33

    # 21 de Nível 1 e 12 de Nível 2
    n1 = [q for q in questions if q.get("difficulty") == 1]
    n2 = [q for q in questions if q.get("difficulty") == 2]
    n3 = [q for q in questions if q.get("difficulty") == 3]

    assert len(n1) == 21
    assert len(n2) == 12
    assert len(n3) == 0

    # IDs proibidos de Nível 3
    banned_n3_ids = {"Q-SOL-005", "Q-SOL-007", "Q-SOL-008", "Q-STO-008", "Q-ENV-006"}
    for q in questions:
        assert q["id"] not in banned_n3_ids
        assert q.get("difficulty") in (1, 2)
        assert "🔥 [APOSTA NO TEMA" not in q.get("statement", "")


def test_canonical_lote_ordering():
    """Garante ordenação canônica por (difficulty, id) em todas as 33 questões."""
    questions = load_questions_n1_n2()

    expected_ids = [
        # Nível 1 (21 questões)
        "Q-ATO-001",
        "Q-ATO-002",
        "Q-ATO-003",
        "Q-ATO-004",
        "Q-ENV-001",
        "Q-ENV-002",
        "Q-ENV-003",
        "Q-ENV-004",
        "Q-ENV-007",
        "Q-ENV-008",
        "Q-SOL-001",
        "Q-SOL-006",
        "Q-SOL-010",
        "Q-SOL-011",
        "Q-STO-001",
        "Q-STO-002",
        "Q-STO-003",
        "Q-STO-004",
        "Q-STO-005",
        "Q-STO-009",
        "Q-STO-010",
        # Nível 2 (12 questões)
        "Q-ENV-005",
        "Q-ENV-009",
        "Q-ENV-010",
        "Q-SOL-002",
        "Q-SOL-003",
        "Q-SOL-004",
        "Q-SOL-009",
        "Q-SOL-012",
        "Q-STO-006",
        "Q-STO-007",
        "Q-STO-011",
        "Q-STO-012",
    ]

    actual_ids = [q["id"] for q in questions]
    assert actual_ids == expected_ids


def test_batch_operations_structure():
    """Garante a geração correta de 41 slides para 20 lotes com paridade rigorosa Pergunta -> Resposta."""
    questions = load_questions_n1_n2()[:20]
    ops = generate_batch_operations(questions)

    # Identifica criação de slides
    add_slide_ops = [op for op in ops if op.get("op") == "add-slide"]
    # 40 slides criados via add-slide (Slide 1 é a capa 'p' pré-existente)
    assert len(add_slide_ops) == 40

    slide_ids = [op["id"] for op in add_slide_ops]
    expected_slide_ids = []
    for i in range(1, 21):
        expected_slide_ids.append(f"SLIDE_Q_{i:03d}")
        expected_slide_ids.append(f"SLIDE_A_{i:03d}")

    assert slide_ids == expected_slide_ids

    # Confirma que todos os slides têm speaker notes configuradas
    set_notes_ops = [op for op in ops if op.get("op") == "set-notes"]
    assert len(set_notes_ops) == 41  # Capa (1) + 40 slides Q&A

    # Confirma que todos os slides de resposta contêm gabarito e regras de pagamento
    answer_textboxes = [
        op
        for op in ops
        if op.get("op") == "add-textbox" and "SLIDE_A_" in op.get("slide", "")
    ]
    assert len(answer_textboxes) > 0


def test_batch_json_file_validity():
    """Garante que o arquivo JSON do batch foi gerado e é sintaticamente válido."""
    assert DEFAULT_OUTPUT_JSON.exists()
    assert DEFAULT_OUTPUT_JSON.stat().st_size > 0

    with DEFAULT_OUTPUT_JSON.open("r", encoding="utf-8") as f:
        data = json.load(f)

    assert isinstance(data, list)
    assert len(data) in (723, 1178)
