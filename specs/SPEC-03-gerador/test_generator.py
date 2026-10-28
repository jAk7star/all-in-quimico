import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
OUT_DIR = ROOT.parent / "SPEC-04-impressao"


def test_generator_execution():
    """Garante que o deck_builder executa sem falhas e gera os materiais enxutos."""
    res = subprocess.run([sys.executable, str(ROOT / "deck_builder.py")], capture_output=True, text=True)
    assert res.returncode == 0, f"deck_builder falhou com erro: {res.stderr}"


def test_only_expected_output_files_exist():
    """Garante que apenas o arquivo de Fichas de Apostas dos Grupos (63x88mm) e o de Cédulas (10 Kits = R$ 10.000) existem."""
    expected_files = {
        "cards.css",
        "001_fichas_controle_apostas_grupos_v001.html",
        "002_cedulas_dinheiro_10_kits_v001.html",
    }
    actual_files = {p.name for p in OUT_DIR.iterdir() if p.is_file()}
    assert actual_files == expected_files, f"Arquivos divergentes em SPEC-04-impressao: {actual_files}"

    for filename in expected_files:
        file_path = OUT_DIR / filename
        assert file_path.exists(), f"Arquivo esperado não encontrado: {filename}"
        assert file_path.stat().st_size > 0, f"Arquivo gerado está vazio: {filename}"


def test_10_kits_money_totals_10000_reais():
    """Valida matematicamente que os 10 kits geram exatamente R$ 10.000 (60x100 + 60x50 + 100x10 = 220 cédulas)."""
    import deck_builder

    money_pages, stats = deck_builder.build_10_kits_money_pages()
    assert stats["kits_count"] == 10
    assert stats["count_100"] == 60
    assert stats["count_50"] == 60
    assert stats["count_10"] == 100
    assert stats["total_notes"] == 220
    assert stats["total_value"] == 10000
    assert len(money_pages) == 19  # 18 folhas de 12 notas (216) + 1 folha de 4 notas = 220 cédulas

    money_html = (OUT_DIR / "002_cedulas_dinheiro_10_kits_v001.html").read_text(encoding="utf-8")
    assert "CEM REAIS" in money_html
    assert "CINQUENTA REAIS" in money_html
    assert "DEZ REAIS" in money_html
    assert money_html.count('class="money-note note-100"') == 60
    assert money_html.count('class="money-note note-50"') == 60
    assert money_html.count('class="money-note note-10"') == 100


def test_group_bet_cards_format_and_rules():
    """Valida que as Fichas de Controle das Apostas dos Grupos usam o tamanho 63x88mm (grade 3x3) e as regras oficiais."""
    bet_cards_html = (OUT_DIR / "001_fichas_controle_apostas_grupos_v001.html").read_text(encoding="utf-8")
    assert 'class="cards-sheet"' in bet_cards_html
    assert "R$ 1.000" in bet_cards_html
    assert "6×100 | 6×50 | 10×10" in bet_cards_html
    assert "MÍN R$ 10" in bet_cards_html
    assert "MÁX R$ 200" in bet_cards_html
    assert "DESAFIO DA MESA" in bet_cards_html
    assert "SEM PLACAS" in bet_cards_html


def test_duplex_mirroring_integrity():
    """Valida a lógica de espelhamento horizontal no duplex."""
    import deck_builder

    dummy_cards = [{"number": f"{i:03d}"} for i in range(1, 10)]
    mirrored = deck_builder.mirror_grid_for_back(dummy_cards, grid_cols=3, grid_rows=3)

    assert mirrored[0]["number"] == "003"
    assert mirrored[1]["number"] == "002"
    assert mirrored[2]["number"] == "001"
    assert mirrored[3]["number"] == "006"
    assert mirrored[4]["number"] == "005"
    assert mirrored[5]["number"] == "004"
    assert mirrored[6]["number"] == "009"
    assert mirrored[7]["number"] == "008"
    assert mirrored[8]["number"] == "007"
