"""
Suíte de Testes Adversariais e Empíricos — Challenger M5
Projeto: All-In Químico — Reestruturação Multi-Deck de Slides
============================================================
Executa testes empíricos de estresse sem confiar em logs ou mocks:
1. Zero-Reuse & Cross-Deck Isolation Stress Test
2. Anti-Overflow & Typography Stress Test (Geometria e Auto-Scaling)
3. IUPAC Chemical Notation Stress Test (Massa Molar e Subscritos)
4. Verificação de Integridade dos Batch JSONs Gerados em Disco
"""

from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path
from typing import ClassVar

import pytest
import yaml

# Adiciona gerador ao path
REPO_ROOT = Path(__file__).resolve().parent.parent
SPEC_GEN_DIR = REPO_ROOT / "specs" / "SPEC-03-gerador"
QUESTIONS_DIR = REPO_ROOT / "specs" / "SPEC-01-questoes" / "questions"
BATCH_DIR = SPEC_GEN_DIR / "batch_files"
MANIFEST_PATH = SPEC_GEN_DIR / "decks_manifest.json"

if str(SPEC_GEN_DIR) not in sys.path:
    sys.path.insert(0, str(SPEC_GEN_DIR))

from gerar_slides_perguntas_respostas import (
    clean_chemical_typography,
    compute_typography_params,
)

# ==============================================================================
# FIXTURES E CARREGAMENTO EMPÍRICO DIRETO DOS ARQUIVOS FONTE
# ==============================================================================

@pytest.fixture(scope="session")
def question_bank():
    """Carrega diretamente as 25 questões dos arquivos YAML originais."""
    questions = {}
    yaml_files = [
        QUESTIONS_DIR / "nivel_1_aquecimento" / "questoes_nivel_1.yaml",
        QUESTIONS_DIR / "nivel_2_finais" / "questoes_nivel_2.yaml",
        QUESTIONS_DIR / "nivel_3_desafio_morte_subita" / "questoes_nivel_3.yaml",
    ]
    for filepath in yaml_files:
        assert filepath.is_file(), f"Arquivo YAML não encontrado: {filepath}"
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            q_list = data.get("questions", [])
            for q in q_list:
                qid = q["id"]
                assert qid not in questions, f"ID duplicado no banco: {qid}"
                questions[qid] = q
    return questions


@pytest.fixture(scope="session")
def manifest():
    """Carrega o manifesto de decks oficial."""
    assert MANIFEST_PATH.is_file(), f"Manifesto não encontrado: {MANIFEST_PATH}"
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def batch_files():
    """Carrega todos os arquivos batch JSON gerados em batch_files/."""
    assert BATCH_DIR.is_dir(), f"Diretório batch_files não encontrado: {BATCH_DIR}"
    batches = {}
    for f in BATCH_DIR.glob("*.json"):
        with open(f, "r", encoding="utf-8") as fp:
            batches[f.name] = json.load(fp)
    return batches


# ==============================================================================
# 1. ZERO-REUSE & CROSS-DECK ISOLATION STRESS TEST
# ==============================================================================

class TestZeroReuseAndCrossDeckIsolation:
    """Validação adversarial de isolamento absoluto e não-reutilização."""

    TEST_EXCLUSIVE_IDS: ClassVar[set[str]] = {"Q-ATO-001", "Q-SOL-001", "Q-STO-001"}
    CHALLENGE_N3_IDS: ClassVar[set[str]] = {"Q-SOL-005", "Q-SOL-007", "Q-SOL-008", "Q-STO-008", "Q-ENV-006"}
    TIEBREAKER_N2_IDS: ClassVar[set[str]] = {"Q-ENV-005", "Q-STO-007"}

    def test_question_bank_total_count_and_tier_distribution(self, question_bank):
        """Verifica se o banco tem exatamente 38 questões com 21 N1, 12 N2, 5 N3."""
        assert len(question_bank) == 38
        n1 = [q for q in question_bank.values() if q.get("difficulty") == 1 or q.get("tier") == 1]
        n2 = [q for q in question_bank.values() if q.get("difficulty") == 2 or q.get("tier") == 2]
        n3 = [q for q in question_bank.values() if q.get("difficulty") == 3 or q.get("tier") == 3]
        assert len(n1) == 21, f"Esperado 21 N1, obteve {len(n1)}"
        assert len(n2) == 12, f"Esperado 12 N2, obteve {len(n2)}"
        assert len(n3) == 5, f"Esperado 5 N3, obteve {len(n3)}"

    def test_test_deck_exclusive_three_n1(self, manifest):
        """Verifica se o deck de teste tem exatamente as 3 questões N1 exclusivas."""
        test_deck = manifest["decks"]["test_deck"]
        q_ids = set(test_deck["question_ids"])
        assert q_ids == self.TEST_EXCLUSIVE_IDS
        assert test_deck["total_slides"] == 7

    def test_zero_reuse_test_questions_in_regular_decks(self, manifest):
        """Assegura que nenhuma das 3 questões do teste aparece em decks regulares."""
        regular_decks = manifest["decks"]["regular_decks"]
        for reg in regular_decks:
            reg_ids = set(reg["question_ids"])
            collision = reg_ids & self.TEST_EXCLUSIVE_IDS
            assert not collision, f"Vazamento de questão de teste {collision} no deck {reg['deck_id']}"

    def test_zero_reuse_test_questions_in_challenge_decks(self, manifest):
        """Assegura que nenhuma questão do teste aparece em decks de desafio."""
        challenges = manifest["decks"]["challenges"]
        for chal in challenges:
            chal_ids = set(chal["question_ids"])
            collision = chal_ids & self.TEST_EXCLUSIVE_IDS
            assert not collision, f"Vazamento de questão de teste {collision} no desafio {chal['deck_id']}"

    def test_zero_reuse_test_questions_in_tiebreaker_deck(self, manifest):
        """Assegura que nenhuma questão do teste aparece no deck de desempate."""
        tb_deck = manifest["decks"].get("tiebreaker_deck")
        if tb_deck:
            tb_ids = set(tb_deck["question_ids"])
            collision = tb_ids & self.TEST_EXCLUSIVE_IDS
            assert not collision, f"Vazamento de questão de teste {collision} no deck suplente"

    def test_regular_decks_mutually_disjoint(self, manifest):
        """Verifica que todos os 3 decks regulares são mutuamente disjuntos (Reg_a ∩ Reg_b = ∅)."""
        regular_decks = manifest["decks"]["regular_decks"]
        assert len(regular_decks) == 3
        reg_sets = [set(reg["question_ids"]) for reg in regular_decks]
        
        # Cada deck regular deve ter 5 ou 10 questões
        for i, r_set in enumerate(reg_sets):
            assert len(r_set) in (5, 10), f"Deck regular {i+1} possui {len(r_set)} questões"

        # Disjunção pairwise
        assert reg_sets[0].isdisjoint(reg_sets[1]), f"Colisão entre Regular 1 e 2: {reg_sets[0] & reg_sets[1]}"
        assert reg_sets[0].isdisjoint(reg_sets[2]), f"Colisão entre Regular 1 e 3: {reg_sets[0] & reg_sets[2]}"
        assert reg_sets[1].isdisjoint(reg_sets[2]), f"Colisão entre Regular 2 e 3: {reg_sets[1] & reg_sets[2]}"

    def test_challenge_decks_exact_one_distinct_n3(self, manifest):
        """Verifica se os 5 desafios contêm exatamente 1 questão N3 distinta cada."""
        challenges = manifest["decks"]["challenges"]
        assert len(challenges) == 5
        seen_n3 = set()
        for chal in challenges:
            q_ids = chal["question_ids"]
            assert len(q_ids) == 1, f"Desafio {chal['deck_id']} possui {len(q_ids)} questões"
            qid = q_ids[0]
            assert qid in self.CHALLENGE_N3_IDS, f"Questão {qid} não é N3 válida"
            assert qid not in seen_n3, f"Questão N3 {qid} duplicada entre desafios"
            seen_n3.add(qid)
            assert chal["total_slides"] == 3

        assert seen_n3 == self.CHALLENGE_N3_IDS

    def test_tiebreaker_deck_composition(self, manifest):
        """Verifica se o deck de desempate possui exatamente as 2 questões N2 suplentes quando configurado."""
        tb = manifest["decks"].get("tiebreaker_deck")
        if tb:
            tb_ids = set(tb["question_ids"])
            assert tb_ids == self.TIEBREAKER_N2_IDS
            assert tb["total_slides"] == 5

    def test_sum_of_all_questions_equals_25_and_partition_is_exact(self, manifest, question_bank):
        """Verifica se a soma das questões em todos os decks é exatamente 38 e cobre 100% do banco."""
        all_deck_qids = []
        
        # Test deck
        all_deck_qids.extend(manifest["decks"]["test_deck"]["question_ids"])
        # Challenges
        for chal in manifest["decks"]["challenges"]:
            all_deck_qids.extend(chal["question_ids"])
        # Regular decks
        for reg in manifest["decks"]["regular_decks"]:
            all_deck_qids.extend(reg["question_ids"])
        # Tiebreaker
        if manifest["decks"].get("tiebreaker_deck"):
            all_deck_qids.extend(manifest["decks"]["tiebreaker_deck"]["question_ids"])

        expected_count = len(question_bank)
        assert len(all_deck_qids) == expected_count, f"Contagem total de questões alocadas é {len(all_deck_qids)}, esperado {expected_count}"
        assert len(set(all_deck_qids)) == expected_count, "Há questões duplicadas entre decks!"
        assert set(all_deck_qids) == set(question_bank.keys()), "A partição não cobre exatamente o banco de questões!"

    def test_batch_json_files_literal_zero_reuse(self, batch_files):
        """Varre textualmente os arquivos batch JSON em disco garantindo ausência de Q-ATO-001, Q-SOL-001, Q-STO-001 fora do teste."""
        forbidden = ["Q-ATO-001", "Q-SOL-001", "Q-STO-001"]
        for fname, batch_content in batch_files.items():
            content_str = json.dumps(batch_content, ensure_ascii=False)
            if fname == "batch_deck_teste_nivel_1.json":
                # No teste, todas as 3 devem aparecer
                for f_id in forbidden:
                    assert f_id in content_str, f"{f_id} esperado no deck de teste mas não encontrado"
            else:
                # Em nenhum outro deck nenhuma das 3 pode aparecer
                for f_id in forbidden:
                    assert f_id not in content_str, f"Vazamento literal de {f_id} no arquivo batch {fname}!"


# ==============================================================================
# 2. ANTI-OVERFLOW & TYPOGRAPHY STRESS TEST
# ==============================================================================

class TestAntiOverflowAndTypography:
    """Validação adversarial das equações de auto-scaling e geometria de cards."""

    def test_extreme_case_longest_statement_q_sto_008(self, question_bank):
        """Testa o caso extremo de maior enunciado (Q-STO-008: 307c raw, 241c clean, 198c display)."""
        q = question_bank["Q-STO-008"]
        raw_stmt = q["statement"]
        assert len(raw_stmt) == 307
        clean_stmt = clean_chemical_typography(raw_stmt)
        assert len(clean_stmt) == 241

        # Teste com raw (307c > 240)
        params_raw = compute_typography_params(raw_stmt, 50, 100)
        assert params_raw.stmt_font_size == 10.5
        assert params_raw.stmt_line_spacing == 125

        # Teste com clean (241c > 240)
        params_clean = compute_typography_params(clean_stmt, 50, 100)
        assert params_clean.stmt_font_size == 10.5
        assert params_clean.stmt_line_spacing == 125

        # Teste com display limpo sem o tema N3 (198c: 180 < len <= 240)
        display_stmt = re.sub(r"^🔥\s*\[APOSTA NO TEMA:[^\]]+\]\s*", "", clean_stmt)
        assert len(display_stmt) == 198
        params_display = compute_typography_params(display_stmt, 50, 100)
        assert params_display.stmt_font_size == 11.0
        assert params_display.stmt_line_spacing == 130

    def test_extreme_cases_longest_options(self, question_bank):
        """Testa as opções mais longas do banco (> 110c) garantindo opt_font_size = 9.8 pt."""
        extreme_options = [
            ("Q-ENV-004", "A", 159, 137),  # 159 raw, 137 clean
            ("Q-ENV-002", "B", 144, 122),  # 144 raw, 122 clean
            ("Q-ENV-006", "B", 139, 117),  # 139 raw, 117 clean
            ("Q-ENV-005", "A", 134, 123),  # 134 raw, 123 clean
            ("Q-ENV-003", "A", 127, 127),  # 127 clean
        ]
        for qid, opt_key, raw_len, clean_len in extreme_options:
            q = question_bank[qid]
            opt_obj = next(o for o in q["options"] if o["key"] == opt_key)
            assert len(opt_obj["text"]) == raw_len
            cleaned_opt = clean_chemical_typography(opt_obj["text"])
            assert len(cleaned_opt) == clean_len

            # Passando lista de opções com dicionários
            params = compute_typography_params("Enunciado padrão", q["options"], 100)
            assert params.opt_font_size == 9.8, f"Falha para {qid} opção {opt_key}: esperava 9.8, obteve {params.opt_font_size}"
            assert params.opt_line_spacing == 120

            # Passando comprimento diretamente
            params_direct = compute_typography_params(100, clean_len, 100)
            assert params_direct.opt_font_size == 9.8
            assert params_direct.opt_line_spacing == 120

    def test_extreme_cases_longest_solution_justification(self, question_bank):
        """Testa as justificativas mais longas do banco (> 260c) garantindo ans2_font_size = 9.5 pt."""
        extreme_solutions = ["Q-STO-008", "Q-STO-006", "Q-SOL-009", "Q-ENV-006"]
        for qid in extreme_solutions:
            q = question_bank[qid]
            correct = q.get("correct", "A").upper()
            wrong_key = "B" if correct == "A" else "A"
            wrong_opt = next((o for o in q.get("options", []) if o.get("key") == wrong_key), {})
            ans_data = {
                "scientific_justification": clean_chemical_typography(q.get("scientific_justification", "")),
                "distractor_rationale": clean_chemical_typography(wrong_opt.get("rationale", "")),
                "wrong_key": wrong_key,
            }
            params = compute_typography_params("Enunciado", 50, ans_data)
            assert params.ans2_font_size == 9.5, f"Falha para {qid}: esperava 9.5, obteve {params.ans2_font_size}"
            assert params.ans2_line_spacing == 120

    def test_card_geometry_mathematical_clearance_all_25_questions(self, question_bank):
        """Modela geometricamente todas as 25 questões contra os limites físicos dos cards."""
        # Dimensões nominais dos cards Fintech Clean (em pontos):
        # Enunciado: w=296, h=196
        # Alternativas: w=288, h=68
        # Gabarito Coluna 2: w=288, h=196
        
        for qid, q in question_bank.items():
            cleaned_stmt = clean_chemical_typography(q["statement"])
            # Remove tema N3 para cálculo real de exibição
            display_stmt = re.sub(r"^🔥\s*\[APOSTA NO TEMA:[^\]]+\]\s*", "", cleaned_stmt)
            
            opts = [clean_chemical_typography(o["text"]) for o in q["options"]]
            max_opt_len = max(len(o) for o in opts)
            
            correct = q.get("correct", "A").upper()
            wrong_key = "B" if correct == "A" else "A"
            wrong_opt = next((o for o in q.get("options", []) if o.get("key") == wrong_key), {})
            justif = clean_chemical_typography(q.get("scientific_justification", ""))
            rationale = clean_chemical_typography(wrong_opt.get("rationale", ""))
            ans_data = {
                "scientific_justification": justif,
                "distractor_rationale": rationale,
                "wrong_key": wrong_key,
            }
            
            params = compute_typography_params(display_stmt, q["options"], ans_data)
            
            # 1. Enunciado
            stmt_char_per_line = 296 / (params.stmt_font_size * 0.55)
            stmt_lines = math.ceil(len(display_stmt) / stmt_char_per_line)
            stmt_height = stmt_lines * (params.stmt_font_size * (params.stmt_line_spacing / 100))
            assert stmt_height <= 196, f"Overflow no enunciado de {qid}: {stmt_height:.1f} pt > 196 pt"
            
            # 2. Alternativas (max opt)
            opt_char_per_line = 288 / (params.opt_font_size * 0.62)
            opt_lines = math.ceil(max_opt_len / opt_char_per_line)
            opt_height = opt_lines * (params.opt_font_size * (params.opt_line_spacing / 100))
            assert opt_height <= 68, f"Overflow na alternativa de {qid}: {opt_height:.1f} pt > 68 pt"
            assert (68 - opt_height) >= 15, f"Folga insuficiente na alternativa de {qid}: {68 - opt_height:.1f} pt"
            
            # 3. Gabarito Coluna 2
            col2_char_per_line = 288 / (params.ans2_font_size * 0.55)
            # Soma linhas dos títulos + linhas dos parágrafos
            col2_lines = 4 + math.ceil(len(justif) / col2_char_per_line) + math.ceil(len(rationale) / col2_char_per_line)
            col2_height = col2_lines * (params.ans2_font_size * (params.ans2_line_spacing / 100))
            assert col2_height <= 196, f"Overflow na coluna 2 de {qid}: {col2_height:.1f} pt > 196 pt"


# ==============================================================================
# 3. IUPAC CHEMICAL NOTATION STRESS TEST
# ==============================================================================

class TestIUPACChemicalNotation:
    """Validação adversarial estrita de clean_chemical_typography e norma IUPAC."""

    def test_molar_mass_uppercase_subscripts(self):
        """Testa se subscritos maiúsculos em M<sub>X</sub> viram rigorosamente M(X) e nunca MX."""
        test_cases = [
            ("M<sub>Na</sub> = 23,0 g/mol", "M(Na) = 23,0 g/mol"),
            ("M<sub>Cl</sub> = 35,5 g/mol", "M(Cl) = 35,5 g/mol"),
            ("M<sub>H</sub> = 1,0 g/mol", "M(H) = 1,0 g/mol"),
            ("M<sub>O</sub> = 16,0 g/mol", "M(O) = 16,0 g/mol"),
            ("M<sub>H₂O</sub> = 18,0 g/mol", "M(H₂O) = 18,0 g/mol"),
            ("M<sub>H2O</sub> = 18,0 g/mol", "M(H₂O) = 18,0 g/mol"),
            ("M<sub>H<sub>2</sub>O</sub> = 18,0 g/mol", "M(H₂O) = 18,0 g/mol"),
            ("M<sub>Fe</sub> = 56,0 g/mol", "M(Fe) = 56,0 g/mol"),
            ("M<sub>CaCO3</sub> = 100,0 g/mol", "M(CaCO₃) = 100,0 g/mol"),
        ]
        for raw_input, expected in test_cases:
            res = clean_chemical_typography(raw_input)
            assert res == expected, f"Falha: entrada '{raw_input}' produziu '{res}', esperado '{expected}'"
            # Garante que não gerou a forma deformada sem parênteses
            assert "MNa" not in res
            assert "MCl" not in res
            assert "MH " not in res
            assert "MO " not in res
            assert "MH₂O" not in res

    def test_yaml_molar_mass_questions(self, question_bank):
        """Testa a limpeza tipográfica nas questões específicas do banco que contêm M<sub>X</sub>."""
        # Q-STO-004
        stmt_sto4 = clean_chemical_typography(question_bank["Q-STO-004"]["statement"])
        assert "M(H) = 1,0 g/mol" in stmt_sto4
        assert "M(O) = 16,0 g/mol" in stmt_sto4
        assert "MH" not in stmt_sto4
        assert "MO" not in stmt_sto4

        # Q-STO-005
        stmt_sto5 = clean_chemical_typography(question_bank["Q-STO-005"]["statement"])
        assert "M(H₂O) = 18,0 g/mol" in stmt_sto5
        assert "MH₂O" not in stmt_sto5

        # Q-SOL-007
        stmt_sol7 = clean_chemical_typography(question_bank["Q-SOL-007"]["statement"])
        assert "M(Na) = 23,0 g/mol" in stmt_sol7
        assert "M(Cl) = 35,5 g/mol" in stmt_sol7
        assert "MNa" not in stmt_sol7
        assert "MCl" not in stmt_sol7

        # Q-SOL-008
        stmt_sol8 = clean_chemical_typography(question_bank["Q-SOL-008"]["statement"])
        assert "M(Na) = 23,0 g/mol" in stmt_sol8
        assert "M(O) = 16,0 g/mol" in stmt_sol8
        assert "M(H) = 1,0 g/mol" in stmt_sol8

    def test_chemical_subscripts_and_superscripts(self):
        """Testa conversão de tags <sub> e <sup> comuns."""
        cases = [
            ("H<sub>2</sub>O", "H₂O"),
            ("CO<sub>2</sub>", "CO₂"),
            ("SO<sub>2</sub>", "SO₂"),
            ("SO<sub>3</sub>", "SO₃"),
            ("H<sub>2</sub>SO<sub>4</sub>", "H₂SO₄"),
            ("Na<sub>2</sub>SO<sub>4</sub>", "Na₂SO₄"),
            ("CaCO<sub>3</sub>", "CaCO₃"),
            ("Al<sup>3+</sup>", "Al³⁺"),
            ("Al<sup>0</sup>", "Al⁰"),
            ("V<sub>2</sub>", "V₂"),
            ("V<sub>1</sub>", "V₁"),
        ]
        for raw_input, expected in cases:
            res = clean_chemical_typography(raw_input)
            assert res == expected

    def test_untagged_formula_and_symbol_replacements(self):
        """Testa fórmulas não marcadas em resoluções e setas de reação."""
        cases = [
            ("2 H2 + O2 -> 2 H2O", "2 H₂ + O₂ → 2 H₂O"),
            ("N2 + 3 H2 <-> 2 NH3", "N2 + 3 H₂ ⇄ 2 NH3"),
            ("c1·V1 = c2·V2", "c₁·V₁ = c₂·V₂"),
        ]
        for raw_input, expected in cases:
            res = clean_chemical_typography(raw_input)
            assert res == expected

    def test_adversarial_nil_and_empty_inputs(self):
        """Testa robustez contra entradas nulas, vazias ou whitespace."""
        assert clean_chemical_typography(None) == ""
        assert clean_chemical_typography("") == ""
        assert clean_chemical_typography("   ") == ""
        assert clean_chemical_typography(12345) == "12345"


# ==============================================================================
# 4. AUDITORIA DOS BATCH JSONS GERADOS EM DISCO
# ==============================================================================

class TestDiskBatchJSONIntegrity:
    """Verifica a integridade estrutural e de Design System em cada batch JSON gerado."""

    def test_all_10_manifest_batches_exist(self, manifest):
        """Garante que todos os arquivos batch referenciados no manifesto existem fisicamente."""
        decks_info = []
        decks_info.append(manifest["decks"]["test_deck"])
        decks_info.extend(manifest["decks"]["challenges"])
        decks_info.extend(manifest["decks"]["regular_decks"])
        if manifest["decks"].get("tiebreaker_deck"):
            decks_info.append(manifest["decks"]["tiebreaker_deck"])
        assert len(decks_info) in (9, 10)

        for deck in decks_info:
            b_rel = deck["batch_file"]
            b_path = SPEC_GEN_DIR / b_rel
            assert b_path.is_file(), f"Arquivo batch {b_path} não existe no disco!"

    def test_batch_json_design_system_properties(self, batch_files):
        """Inspeciona as operações batch confirmando cor de fundo #F8F9FA, card #FFFFFF e Open Sans."""
        for fname, batch_content in batch_files.items():
            assert isinstance(batch_content, list), f"Arquivo batch {fname} deve ser uma lista de operações"
            assert len(batch_content) > 0, f"Arquivo batch {fname} está vazio!"

            # 1. Verifica operações set-background
            bg_ops = [op for op in batch_content if op.get("op") == "set-background"]
            assert len(bg_ops) > 0, f"Nenhuma operação set-background em {fname}"
            for bg in bg_ops:
                assert bg.get("color") == "#F8F9FA", f"Cor de fundo inválida {bg.get('color')} em {fname}"

            # 2. Verifica cards elevados brancos (#FFFFFF)
            card_ops = [
                op for op in batch_content 
                if op.get("op") == "add-shape" and op.get("background_color") == "#FFFFFF"
            ]
            assert len(card_ops) > 0, f"Nenhum card elevado #FFFFFF encontrado em {fname}"

            # 3. Verifica fontes Open Sans em add-textbox
            textbox_ops = [op for op in batch_content if op.get("op") == "add-textbox"]
            assert len(textbox_ops) > 0, f"Nenhum textbox encontrado em {fname}"
            for tb in textbox_ops:
                ff = tb.get("font_family")
                if ff:
                    assert ff == "Open Sans", f"Fonte não-conforme '{ff}' encontrada em {fname}"

    def test_batch_json_slide_counts_and_qa_parity(self, batch_files, manifest):
        """Verifica se cada arquivo batch gera a contagem exata de slides e alterna Q&A estritamente."""
        expected_counts = {
            "batch_deck_teste_nivel_1.json": 7,
            "batch_desafio_01_morte_subita_diluicao.json": 3,
            "batch_desafio_02_morte_subita_molaridade_sal.json": 3,
            "batch_desafio_03_morte_subita_soda_caustica.json": 3,
            "batch_desafio_04_morte_subita_estequiometria_agua.json": 3,
            "batch_desafio_05_morte_subita_chuva_acida.json": 3,
            "batch_deck_regular_01.json": 11,
            "batch_deck_regular_02.json": 11,
            "batch_deck_regular_03.json": 11,
            "batch_deck_suplente_desempate.json": 5,
        }

        total_slides_system = 0
        for fname, exp_count in expected_counts.items():
            ops = batch_files[fname]
            # O primeiro slide é o slide 'p' (existente/modificado), e os demais são 'add-slide'
            added_slides = [op for op in ops if op.get("op") == "add-slide"]
            total_slides = 1 + len(added_slides)
            assert total_slides == exp_count, f"{fname}: esperado {exp_count} slides, obteve {total_slides}"
            total_slides_system += total_slides

            # Verifica paridade estrita dos slides adicionados
            # Os slides adicionados devem alternar: Pergunta (SLIDE_Q_xxx), Resposta (SLIDE_A_xxx)
            slide_ids = [s["id"] for s in added_slides]
            for i, sid in enumerate(slide_ids):
                if i % 2 == 0:
                    assert sid.startswith("SLIDE_Q_"), f"{fname}: slide {i+2} deveria ser pergunta, obteve {sid}"
                else:
                    assert sid.startswith("SLIDE_A_"), f"{fname}: slide {i+2} deveria ser resposta, obteve {sid}"

            # Verifica notas de orador (cada slide deve ter um set-notes)
            notes_ops = [op for op in ops if op.get("op") == "set-notes"]
            assert len(notes_ops) == exp_count, (
                f"{fname}: esperado {exp_count} set-notes, obteve {len(notes_ops)}"
            )

        assert total_slides_system == 60, f"Total do sistema de slides deveria ser 60, obteve {total_slides_system}"


# ==============================================================================
# 5. ADVERSARIAL BOUNDARY FUZZING
# ==============================================================================

class TestAdversarialBoundaryFuzzing:
    """Fuzzing de fronteira nas funções centrais de tipografia e notação."""

    def test_compute_typography_params_boundaries(self):
        """Testa valores limítrofes exatos de caracteres para corte de auto-scaling."""
        # Enunciado: cortes em 180 e 240
        assert compute_typography_params(180, 50, 100).stmt_font_size == 12.0
        assert compute_typography_params(181, 50, 100).stmt_font_size == 11.0
        assert compute_typography_params(240, 50, 100).stmt_font_size == 11.0
        assert compute_typography_params(241, 50, 100).stmt_font_size == 10.5
        assert compute_typography_params(1000, 50, 100).stmt_font_size == 10.5

        # Alternativas: cortes em 80 e 110
        assert compute_typography_params(100, 80, 100).opt_font_size == 11.5
        assert compute_typography_params(100, 81, 100).opt_font_size == 10.5
        assert compute_typography_params(100, 110, 100).opt_font_size == 10.5
        assert compute_typography_params(100, 111, 100).opt_font_size == 9.8
        assert compute_typography_params(100, 500, 100).opt_font_size == 9.8

        # Resposta Coluna 2: cortes em 200 e 260
        assert compute_typography_params(100, 50, 200).ans2_font_size == 10.5
        assert compute_typography_params(100, 50, 201).ans2_font_size == 10.0
        assert compute_typography_params(100, 50, 260).ans2_font_size == 10.0
        assert compute_typography_params(100, 50, 261).ans2_font_size == 9.5
        assert compute_typography_params(100, 50, 800).ans2_font_size == 9.5

    def test_clean_chemical_typography_adversarial_strings(self):
        """Testa sequências químicas adversariais e combinadas."""
        # Múltiplos M(X) na mesma frase
        multi = "Dados: M<sub>Na</sub> = 23,0 g/mol, M<sub>Cl</sub> = 35,5 g/mol e M<sub>H</sub> = 1,0 g/mol."
        cleaned = clean_chemical_typography(multi)
        assert cleaned == "Dados: M(Na) = 23,0 g/mol, M(Cl) = 35,5 g/mol e M(H) = 1,0 g/mol."
        assert "MNa" not in cleaned
        assert "MCl" not in cleaned
        assert "MH" not in cleaned

        # Variáveis físicas subscritas vs molar mass
        # V2 e V1 não devem virar V(2) ou V(1)
        v_test = "Calculando V<sub>2</sub> a partir de V<sub>1</sub> = 100 mL e c<sub>1</sub>."
        cleaned_v = clean_chemical_typography(v_test)
        assert "V₂" in cleaned_v
        assert "V₁" in cleaned_v
        assert "V(2)" not in cleaned_v

        # Fórmulas complexas com subscrito e sobrescrito simultâneos
        complex_chem = "Íons Al<sup>3+</sup> reagem com SO<sub>4</sub><sup>2-</sup> formando Al<sub>2</sub>(SO<sub>4</sub>)<sub>3</sub>."
        cleaned_comp = clean_chemical_typography(complex_chem)
        assert "Al³⁺" in cleaned_comp
        assert "SO₄²⁻" in cleaned_comp
        assert "Al₂(SO₄)₃" in cleaned_comp

