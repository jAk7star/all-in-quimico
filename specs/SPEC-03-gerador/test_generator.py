import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
OUT_DIR = ROOT.parent / "SPEC-04-impressao"


def test_generator_execution():
    """Garante que o deck_builder executa sem falhas e gera os materiais."""
    res = subprocess.run([sys.executable, str(ROOT / "deck_builder.py")], capture_output=True, text=True)
    assert res.returncode == 0, f"deck_builder falhou com erro: {res.stderr}"


def test_all_expected_output_files_exist():
    """Garante que todos os arquivos do ecossistema de impressão foram gerados com organização de 3 dígitos."""
    expected_files = [
        "cards.css",
        "001_manual_do_professor_v001.html",
        "002_guia_do_mestre_cheat_sheet_v001.html",
        "003_ficha_controle_leilao_v001.html",
        "004_regras_do_aluno_v001.html",
        "005_cartoes_regras_mesa_v001.html",
        "006_dinheiro_para_imprimir_v001.html",
        "007_duplex_intercalado_para_imprimir_v001.html",
        "008_perguntas_para_imprimir_v001.html",
        "009_verso_perguntas_para_imprimir_v001.html",
        "010_respostas_para_imprimir_v001.html",
        "011_verso_respostas_para_imprimir_v001.html",
        "012_perguntas_nivel_1_v001.html",
        "013_verso_perguntas_nivel_1_v001.html",
        "014_respostas_nivel_1_v001.html",
        "015_verso_respostas_nivel_1_v001.html",
        "016_perguntas_nivel_2_v001.html",
        "017_verso_perguntas_nivel_2_v001.html",
        "018_respostas_nivel_2_v001.html",
        "019_verso_respostas_nivel_2_v001.html",
        "020_perguntas_nivel_3_v001.html",
        "021_verso_perguntas_nivel_3_v001.html",
        "022_respostas_nivel_3_v001.html",
        "023_verso_respostas_nivel_3_v001.html",
    ]
    for filename in expected_files:
        file_path = OUT_DIR / filename
        assert file_path.exists(), f"Arquivo esperado não encontrado: {filename}"
        assert file_path.stat().st_size > 0, f"Arquivo gerado está vazio: {filename}"


def test_pari_mutuel_binary_options_and_rules_content():
    """Garante que todas as questões geram exatamente 2 opções (A e B) e que as regras pari-mutuel estão nos HTMLs."""
    import deck_builder

    questions = deck_builder.load_all_questions()
    assert len(questions) > 0
    for q in questions:
        correct_key, opts, distractors = deck_builder.build_binary_ab_options(q)
        assert correct_key in ("A", "B")
        assert [o["key"] for o in opts] == ["A", "B"]
        assert len(distractors) == 1

    training = deck_builder.build_training_round_context()
    assert training["total_pool"] == 450
    assert training["winner_pool"] == 250
    assert training["odd_str"] == "1,8"
    assert training["total_paid"] == 400
    assert training["breakage"] == 50

    rules_html = (OUT_DIR / "005_cartoes_regras_mesa_v001.html").read_text(encoding="utf-8")
    assert "Pari-Mutuel" in rules_html
    assert "Texas Hold'em" in rules_html
    assert "Sem Comissão" in rules_html

    tracker_html = (OUT_DIR / "003_ficha_controle_leilao_v001.html").read_text(encoding="utf-8")
    assert "POTE TOTAL" in tracker_html
    assert "MULTIPLICADOR" in tracker_html

    student_html = (OUT_DIR / "004_regras_do_aluno_v001.html").read_text(encoding="utf-8")
    assert "Alfa" in student_html and "Beta" in student_html and "Gama" in student_html
    assert "Texas Hold'em" in student_html

    teacher_html = (OUT_DIR / "001_manual_do_professor_v001.html").read_text(encoding="utf-8")
    assert "Roteiro Falado da Rodada-Treino" in teacher_html
    assert "Duelo Oral Relâmpago" in teacher_html


def test_duplex_mirroring_integrity():
    """Valida a lógica de espelhamento horizontal no duplex."""
    import deck_builder

    # 9 cartas simuladas com IDs 1..9
    dummy_cards = [{"number": f"{i:03d}"} for i in range(1, 10)]
    mirrored = deck_builder.mirror_grid_for_back(dummy_cards, grid_cols=3, grid_rows=3)

    # Linha 1: [001, 002, 003] -> [003, 002, 001]
    assert mirrored[0]["number"] == "003"
    assert mirrored[1]["number"] == "002"
    assert mirrored[2]["number"] == "001"

    # Linha 2: [004, 005, 006] -> [006, 005, 004]
    assert mirrored[3]["number"] == "006"
    assert mirrored[4]["number"] == "005"
    assert mirrored[5]["number"] == "004"

    # Linha 3: [007, 008, 009] -> [009, 008, 007]
    assert mirrored[6]["number"] == "009"
    assert mirrored[7]["number"] == "008"
    assert mirrored[8]["number"] == "007"
