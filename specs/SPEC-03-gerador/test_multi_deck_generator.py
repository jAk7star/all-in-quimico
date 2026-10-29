"""
Testes Automatizados para a Arquitetura Multi-Deck, Auto-Scaling e IUPAC
======================================================================
Valida:
1. Resolução do defeito de subscrito maiúsculo com norma IUPAC parentética M(X).
2. Auto-scaling tipográfico anti-overflow (compute_typography_params).
3. Matriz disjunta e completa dos 10 decks (25 questões, 60 slides).
4. Integridade do decks_manifest.json gerado conforme o contrato do PROJECT.md.
5. Conformidade com o Design System Fintech Clean (cores, fontes Open Sans, cards).
6. Extração e limpeza da mecânica de Aposta no Tema (Morte Súbita N3).
"""

import json

from gerar_slides_perguntas_respostas import (
    BATCH_FILES_DIR,
    BG_CARD,
    BG_MAIN,
    BORDER_SUBTLE,
    DECK_CONFIGS,
    FONT_FAMILY,
    MANIFEST_PATH,
    clean_chemical_typography,
    compute_typography_params,
    generate_all_decks,
    load_all_questions,
    validate_partition_matrix,
)


def test_iupac_chemical_molar_mass_typography():
    """Valida a conversão mandatória para notação parentética IUPAC M(X)."""
    assert clean_chemical_typography("M<sub>Na</sub> = 23,0 g/mol") == "M(Na) = 23,0 g/mol"
    assert clean_chemical_typography("M<sub>Cl</sub> = 35,5 g/mol") == "M(Cl) = 35,5 g/mol"
    assert clean_chemical_typography("M<sub>H</sub> = 1,0 g/mol") == "M(H) = 1,0 g/mol"
    assert clean_chemical_typography("M<sub>O</sub> = 16,0 g/mol") == "M(O) = 16,0 g/mol"
    assert clean_chemical_typography("M<sub>H2O</sub> = 18,0 g/mol") == "M(H₂O) = 18,0 g/mol"
    assert clean_chemical_typography("M<sub>H₂O</sub> = 18,0 g/mol") == "M(H₂O) = 18,0 g/mol"
    # Tag aninhada como no YAML de Q-STO-005
    assert clean_chemical_typography("M<sub>H<sub>2</sub>O</sub> = 18,0 g/mol") == "M(H₂O) = 18,0 g/mol"
    # Validação de distinção de caso (M maiúsculo molar mass vs m minúsculo sample mass)
    assert clean_chemical_typography("m<sub>Na</sub> = 10 g") == "m(Na) = 10 g"
    assert clean_chemical_typography("m<sub>amostra</sub> = 5 g") == "m(amostra) = 5 g"


def test_clean_chemical_typography_auto_subscripts():
    """Valida auto-subscrição de fórmulas comuns sem tags HTML."""
    assert clean_chemical_typography("2 H2 + O2 -> 2 H2O") == "2 H₂ + O₂ → 2 H₂O"
    assert clean_chemical_typography("c1·V1 = c2·V2") == "c₁·V₁ = c₂·V₂"
    assert clean_chemical_typography("SO2 e SO3") == "SO₂ e SO₃"
    assert clean_chemical_typography("CO2") == "CO₂"


def test_compute_typography_params_scaling():
    """Valida as faixas exatas de auto-scaling anti-overflow (§4 do relatório de auditoria)."""
    # 1. Enunciado (<=180 -> 12pt, 181..240 -> 11pt, >240 -> 10.5pt)
    short_stmt = "A" * 150
    med_stmt = "B" * 200
    long_stmt = "C" * 250

    p_short = compute_typography_params(short_stmt, 50, 100)
    p_med = compute_typography_params(med_stmt, 50, 100)
    p_long = compute_typography_params(long_stmt, 50, 100)

    assert p_short.stmt_font_size == 12.0
    assert p_short.stmt_line_spacing == 135

    assert p_med.stmt_font_size == 11.0
    assert p_med.stmt_line_spacing == 130

    assert p_long.stmt_font_size == 10.5
    assert p_long.stmt_line_spacing == 125

    # 2. Alternativas (<=80 -> 11.5pt, 81..110 -> 10.5pt, >110 -> 9.8pt)
    opts_short = [{"text": "A" * 50}, {"text": "B" * 70}]
    opts_med = [{"text": "A" * 50}, {"text": "B" * 95}]
    opts_long = [{"text": "A" * 50}, {"text": "B" * 125}]

    p_opt_short = compute_typography_params("Enunciado", opts_short, 100)
    p_opt_med = compute_typography_params("Enunciado", opts_med, 100)
    p_opt_long = compute_typography_params("Enunciado", opts_long, 100)

    assert p_opt_short.opt_font_size == 11.5
    assert p_opt_short.opt_line_spacing == 130

    assert p_opt_med.opt_font_size == 10.5
    assert p_opt_med.opt_line_spacing == 125

    assert p_opt_long.opt_font_size == 9.8
    assert p_opt_long.opt_line_spacing == 120

    # 3. Gabarito Coluna 2 (<=200 -> 10.5pt, 201..260 -> 10.0pt, >260 -> 9.5pt)
    p_ans_short = compute_typography_params("Enunciado", 50, 180)
    p_ans_med = compute_typography_params("Enunciado", 50, 230)
    p_ans_long = compute_typography_params("Enunciado", 50, 300)

    assert p_ans_short.ans2_font_size == 10.5
    assert p_ans_short.ans2_line_spacing == 130

    assert p_ans_med.ans2_font_size == 10.0
    assert p_ans_med.ans2_line_spacing == 125

    assert p_ans_long.ans2_font_size == 9.5
    assert p_ans_long.ans2_line_spacing == 120


def test_partition_matrix_and_zero_reuse():
    """Valida Teoria dos Conjuntos: completude e disjunção mútua (Zero-Reuse)."""
    all_qs = load_all_questions()
    assert len(all_qs) == 25
    validate_partition_matrix(DECK_CONFIGS, all_qs)

    test_deck = next(d for d in DECK_CONFIGS if d.deck_type == "test")
    challenges = [d for d in DECK_CONFIGS if d.deck_type == "challenge"]
    regulars = [d for d in DECK_CONFIGS if d.deck_type == "regular"]
    tiebreaker = next(d for d in DECK_CONFIGS if d.deck_type == "tiebreaker")

    # Exatamente 3 questões de Nível 1 no teste
    assert len(test_deck.question_ids) == 3
    assert set(test_deck.question_ids) == {"Q-ATO-001", "Q-SOL-001", "Q-STO-001"}

    # Zero-Reuse: Teste x Outros = Vazio
    other_ids = set()
    for c in challenges:
        other_ids.update(c.question_ids)
    for r in regulars:
        other_ids.update(r.question_ids)
    other_ids.update(tiebreaker.question_ids)

    assert set(test_deck.question_ids).isdisjoint(other_ids)

    # 5 desafios individuais N3
    assert len(challenges) == 5
    challenge_ids = {c.question_ids[0] for c in challenges}
    assert challenge_ids == {"Q-SOL-005", "Q-SOL-007", "Q-SOL-008", "Q-STO-008", "Q-ENV-006"}

    # 3 regulares de 5 questões cada
    assert len(regulars) == 3
    reg_ids = set()
    for r in regulars:
        assert len(r.question_ids) == 5
        reg_ids.update(r.question_ids)
    assert len(reg_ids) == 15

    # 1 deck suplente com 2 questões N2
    assert len(tiebreaker.question_ids) == 2
    assert set(tiebreaker.question_ids) == {"Q-ENV-005", "Q-STO-007"}


def test_multi_deck_manifest_and_batch_files_generation():
    """Gera todos os decks em batch-only e valida o manifesto estruturado."""
    manifest = generate_all_decks(dry_run=True, execute=False)

    assert manifest["manifest_version"] == "2.0"
    assert manifest["design_system"]["background_color"] == BG_MAIN
    assert manifest["design_system"]["card_background"] == BG_CARD
    assert manifest["design_system"]["font_family"] == FONT_FAMILY

    decks = manifest["decks"]
    assert decks["test_deck"]["total_slides"] == 7
    assert len(decks["challenges"]) == 5
    for c in decks["challenges"]:
        assert c["total_slides"] == 3
    assert len(decks["regular_decks"]) == 3
    for r in decks["regular_decks"]:
        assert r["total_slides"] == 11
    assert decks["tiebreaker_deck"]["total_slides"] == 5

    # Total de slides acumulado = 7 + 15 + 33 + 5 = 60
    total_slides = (
        decks["test_deck"]["total_slides"]
        + sum(c["total_slides"] for c in decks["challenges"])
        + sum(r["total_slides"] for r in decks["regular_decks"])
        + decks["tiebreaker_deck"]["total_slides"]
    )
    assert total_slides == 60

    # Confirma existência física de todos os 10 arquivos de batch
    assert MANIFEST_PATH.exists()
    assert (BATCH_FILES_DIR / "batch_deck_teste_nivel_1.json").exists()
    assert (BATCH_FILES_DIR / "batch_desafio_01_morte_subita_diluicao.json").exists()
    assert (BATCH_FILES_DIR / "batch_desafio_02_morte_subita_molaridade_sal.json").exists()
    assert (BATCH_FILES_DIR / "batch_desafio_03_morte_subita_soda_caustica.json").exists()
    assert (BATCH_FILES_DIR / "batch_desafio_04_morte_subita_estequiometria_agua.json").exists()
    assert (BATCH_FILES_DIR / "batch_desafio_05_morte_subita_chuva_acida.json").exists()
    assert (BATCH_FILES_DIR / "batch_deck_regular_01.json").exists()
    assert (BATCH_FILES_DIR / "batch_deck_regular_02.json").exists()
    assert (BATCH_FILES_DIR / "batch_deck_regular_03.json").exists()
    assert (BATCH_FILES_DIR / "batch_deck_suplente_desempate.json").exists()


def test_fintech_clean_design_system_compliance_in_batches():
    """Valida se as operações de batch respeitam estritamente as regras visuais Fintech Clean."""
    batch_file = BATCH_FILES_DIR / "batch_deck_teste_nivel_1.json"
    assert batch_file.exists()

    with batch_file.open("r", encoding="utf-8") as f:
        ops = json.load(f)

    # 1. Background de todos os slides deve ser #F8F9FA
    bg_ops = [op for op in ops if op.get("op") == "set-background"]
    assert len(bg_ops) == 7  # 1 capa + 3 perguntas + 3 respostas
    for bg_op in bg_ops:
        assert bg_op["color"] == BG_MAIN

    # 2. Todos os cards de conteúdo possuem fundo #FFFFFF e borda suave #E2E8F0
    card_ops = [
        op for op in ops
        if op.get("op") == "add-shape" and op.get("shape_type") == "ROUND_RECTANGLE"
    ]
    assert len(card_ops) > 0
    for c in card_ops:
        assert c["outline_color"] in (BORDER_SUBTLE, "#BBF7D0")

    # 3. Tipografia deve ser 100% Open Sans
    textbox_ops = [op for op in ops if op.get("op") == "add-textbox"]
    assert len(textbox_ops) > 0
    for tb in textbox_ops:
        assert tb.get("font_family") == FONT_FAMILY


def test_challenge_deck_flame_tag_extraction_and_cleaning():
    """Valida que em N3 a tag 🔥 [APOSTA NO TEMA] é extraída e limpa do enunciado."""
    batch_file = BATCH_FILES_DIR / "batch_desafio_01_morte_subita_diluicao.json"
    with batch_file.open("r", encoding="utf-8") as f:
        ops = json.load(f)

    # Verifica Slide 1 (Capa): título contém DILUIÇÃO
    cover_titles = [
        op for op in ops
        if op.get("op") == "add-textbox" and op.get("slide") == "p" and "DESAFIO FINAL: DILUIÇÃO" in op.get("text", "")
    ]
    assert len(cover_titles) == 1

    # Verifica Slide 2 (Pergunta): enunciado NÃO contém a tag 🔥 [APOSTA NO TEMA
    q_statements = [
        op for op in ops
        if op.get("op") == "add-textbox" and op.get("slide") == "SLIDE_Q_001" and "Você dispõe de 50 mL" in op.get("text", "")
    ]
    assert len(q_statements) == 1
    stmt_text = q_statements[0]["text"]
    assert "🔥 [APOSTA NO TEMA" not in stmt_text
    assert "Você dispõe de 50 mL" in stmt_text
    assert "(V₂)" in stmt_text  # V2 convertido para V₂
