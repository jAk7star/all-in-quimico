"""
Suíte de Testes Automatizados para o Validador de Slides — All-In Químico
========================================================================
Testa de forma abrangente, modular e rigorosa o auditor programático:
  1. Testes Unitários de Regras Didáticas (R1):
     - Caso canônico válido (100% aprovação)
     - Adversariais: ausência de R$ 10.000, saldo incorreto, notas obsoletas, sem placas,
       teto R$ 200, multiplicador 2x, bônus unânime, empate técnico, Winner Takes All, repescagem.
  2. Testes Unitários de Sequência Q&A Monolítica (R2 Legado):
     - Caso canônico válido com 41 slides intercalados e 20 questões
     - Adversariais: contagem != 41, inversão de paridade, divergência de lote,
       ausência de N1/N2, vazamento de N3 (ID ou padrão textual).
  3. Testes Unitários do Deck de Teste Exclusivo (R2 Multi-Deck):
     - Caso canônico válido (7 slides, 3 questões N1 exclusivas)
     - Adversariais: contagem != 7, questão não-N1, vazamento de N2 ou N3, falha de paridade.
  4. Testes Unitários dos Desafios Individuais N3 (R3):
     - Caso canônico válido (3 slides, 1 questão N3)
     - Adversariais: contagem != 3, > 1 questão, questão não-N3, divergência de ID esperado.
  5. Testes Unitários dos Decks Regulares (R4):
     - Caso canônico válido (11 slides, 5 questões, zero N3)
     - Adversariais: contagem != 11, contagem de questões != 5, vazamento de N3 (ID ou texto).
  6. Testes Unitários do Deck de Desempate / Suplente:
     - Caso canônico válido (5 slides, 2 questões N2, zero N3)
     - Adversariais: contagem de questões != 2, vazamento de N3.
  7. Testes de Conformidade com o Design System Fintech Clean (R5):
     - Fundo #F8F9FA, cards #FFFFFF, tipografia Open Sans, anti-overflow (fontScale >= 0.90)
     - Adversariais: fundo dark/branco, fonte Arial/Roboto, compressão excessiva (fontScale < 0.90).
  8. Testes de Isolamento Cruzado e Zero-Reuse (Tier 3):
     - Partição perfeita das 25 questões canônicas
     - Adversariais: vazamento de questão de teste em regular/desafio, colisão pairwise entre regulares.
  9. Testes de Integração via Manifesto e CLI (E2E & Offline Batch):
     - Execução via manifesto JSON com mock/batch local
     - CLI subprocess com flags --manifest, --offline, --json
  10. Testes de Integração com Google Slides Real (quando credenciais ativas).
"""

import json
import subprocess
import sys
from pathlib import Path

# Adiciona o diretório do gerador ao sys.path para importar o validador
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
SPEC_DIR = REPO_ROOT / "specs" / "SPEC-03-gerador"
if str(SPEC_DIR) not in sys.path:
    sys.path.insert(0, str(SPEC_DIR))

from verificar_decks_slides import (
    DEFAULT_RULES_DECK_ID,
    EXPECTED_NIVEL_1_IDS,
    EXPECTED_NIVEL_2_IDS,
    LEGACY_NIVEL_1_IDS,
    LEGACY_NIVEL_2_IDS,
    PresentationInfo,
    SlideInfo,
    create_mock_challenge_deck,
    create_mock_multi_deck_manifest,
    create_mock_regular_deck,
    create_mock_test_deck,
    create_mock_tiebreaker_deck,
    parse_batch_operations,
    run_full_audit,
    run_manifest_audit,
    verify_challenge_deck,
    verify_cross_deck_isolation,
    verify_design_system,
    verify_qa_deck,
    verify_regular_deck,
    verify_rules_deck,
    verify_test_deck,
    verify_tiebreaker_deck,
)

# ==============================================================================
# FIXTURES E MOCKS DE DADOS DE TESTE (LEGADO & MULTI-DECK)
# ==============================================================================


def create_mock_rules_deck() -> PresentationInfo:
    """Cria uma representação mock perfeitamente em conformidade com R1."""
    slides = [
        SlideInfo(
            index=1,
            object_id="p1",
            text_content=(
                "DINÂMICA COMPETITIVA DE QUÍMICA • 5 EQUIPES\n"
                "ALL-IN QUÍMICO\n"
                "Sistema Oficial de Apostas, Multiplicador ×2 e Desafio da Mesa\n"
                "R$ 1.000 Saldo Inicial / Equipe | Máx. R$ 200 Teto por Rodada | Dobro (×2) 1 a 4 Grupos Acertando | +R$ 100 Fixo Todos os 5 Acertando\n"
                "5 Perguntas Regulares • Economia R$ 10.000 • Apostas em Papel (Sem Placas) • Desafio Final Tudo ou Nada"
            ),
            speaker_notes="Slide de abertura oficial.",
            element_count=5,
            background_color="#F8F9FA",
            shapes=[{"shape_type": "ROUND_RECTANGLE", "background_color": "#FFFFFF"}],
            text_runs=[{"content": "ALL-IN QUÍMICO", "font_family": "Open Sans"}],
        ),
        SlideInfo(
            index=2,
            object_id="p2",
            text_content=(
                "1. Kit Inicial de Cédulas & Limite de Aposta\n"
                "Economia Total de R$ 10.000 (R$ 5.000 nos grupos + R$ 5.000 no Banco). Cada equipe começa com R$ 1.000 (aposta máx. R$ 200).\n"
                "R$ 100: 6 notas por grupo (Total = R$ 600)\n"
                "R$ 50: 6 notas por grupo (Total = R$ 300)\n"
                "R$ 10: 10 notas por grupo (Total = R$ 100)\n"
                "Sem Placas: Equipes utilizam papel/folha de aposta para registrar por escrito o valor e a alternativa.\n"
                "Teto Estrito por Pergunta: R$ 200 (mínimo de R$ 10 por rodada).\n"
                "Repescagem na Última Rodada (+R$ 200): Na 5ª rodada, equipe zerada ou no limite (saldo ≤ R$ 200) recebe +R$ 200 do Banco."
            ),
            speaker_notes="Explique o kit inicial entregue a cada grupo (R$ 1.000 = 6x100 + 6x50 + 10x10).",
            element_count=6,
            background_color="#F8F9FA",
            shapes=[{"shape_type": "ROUND_RECTANGLE", "background_color": "#FFFFFF"}],
            text_runs=[{"content": "Kit Inicial", "font_family": "Open Sans"}],
        ),
        SlideInfo(
            index=3,
            object_id="p3",
            text_content=(
                "2. Regras de Bonificação por Rodada\n"
                "1, 2, 3 OU 4 GRUPOS ACERTARAM: DOBRO DA APOSTA (×2) -> Lucro Líquido de +100%!\n"
                "TODOS OS 5 GRUPOS ACERTARAM: BÔNUS UNÂNIME (+R$ 100 FIXO) independente do valor apostado!\n"
                "SE A EQUIPE ERRAR A PERGUNTA: Perde exatamente o valor que apostou na rodada para o Banco da Casa."
            ),
            speaker_notes="Apresente as bonificações.",
            element_count=4,
            background_color="#F8F9FA",
            shapes=[{"shape_type": "ROUND_RECTANGLE", "background_color": "#FFFFFF"}],
            text_runs=[{"content": "Bonificações", "font_family": "Open Sans"}],
        ),
        SlideInfo(
            index=4,
            object_id="p4",
            text_content=(
                "3. Tabela Oficial de Pagamentos e Cédulas\n"
                "R$ 10 a R$ 40 -> Dobro: +100% Lucro | Todos 5: +R$ 100 | Erro: Perde a Aposta\n"
                "R$ 200 (Máx.) -> Dobro: +R$ 200 | Todos 5: +R$ 100 | Erro: -R$ 200"
            ),
            speaker_notes="Tabela de consulta rápida.",
            element_count=3,
            background_color="#F8F9FA",
            shapes=[{"shape_type": "ROUND_RECTANGLE", "background_color": "#FFFFFF"}],
            text_runs=[{"content": "Tabela", "font_family": "Open Sans"}],
        ),
        SlideInfo(
            index=5,
            object_id="p5",
            text_content=(
                "4. Desafio da Mesa — Tudo ou Nada Final!\n"
                "1. GATILHO - EMPATE TÉCNICO (≤ R$ 100): distância de até R$ 100 do 1º colocado pós-rodada 5.\n"
                "2. POTE UNIFICADO: 100% dos saldos das equipes na mesa.\n"
                "3. WINNER TAKES ALL: quem acertar leva tudo e o outro zera!"
            ),
            speaker_notes="Explique o grande clímax final.",
            element_count=5,
            background_color="#F8F9FA",
            shapes=[{"shape_type": "ROUND_RECTANGLE", "background_color": "#FFFFFF"}],
            text_runs=[{"content": "Desafio", "font_family": "Open Sans"}],
        ),
        SlideInfo(
            index=6,
            object_id="p6",
            text_content=(
                "5. Roteiro Rápido de Aplicação em Sala\n"
                "Passo 1: Aposta no papel (mín. R$ 10, máx. R$ 200).\n"
                "Passo 2: Resolução sem placas por escrito.\n"
                "Passo 3: Pagamento pelo Banco (dobro ou unânime +R$ 100).\n"
                "Passo 4: Desafio da mesa para empate técnico ≤ R$ 100 (Winner Takes All)."
            ),
            speaker_notes="Roteiro em 4 passos.",
            element_count=4,
            background_color="#F8F9FA",
            shapes=[{"shape_type": "ROUND_RECTANGLE", "background_color": "#FFFFFF"}],
            text_runs=[{"content": "Roteiro", "font_family": "Open Sans"}],
        ),
    ]
    return PresentationInfo(
        presentation_id="MOCK_RULES", title="All-In Químico — Regras", slides=slides
    )


def create_mock_qa_deck() -> PresentationInfo:
    """Cria uma representação mock perfeitamente em conformidade com R2 Legado (41 slides, 20 pares intercalados)."""
    slides = [
        SlideInfo(
            index=1,
            object_id="cover",
            text_content="ALL-IN QUÍMICO — Cards de Perguntas e Respostas (Níveis 1 e 2)",
            speaker_notes="Capa oficial do deck sequencial.",
            element_count=3,
            background_color="#F8F9FA",
            shapes=[{"shape_type": "ROUND_RECTANGLE", "background_color": "#FFFFFF"}],
            text_runs=[{"content": "ALL-IN QUÍMICO", "font_family": "Open Sans"}],
        )
    ]

    all_ids = LEGACY_NIVEL_1_IDS + LEGACY_NIVEL_2_IDS
    for idx, qid in enumerate(all_ids, start=1):
        diff = 1 if idx <= 13 else 2
        nivel_label = "Nível 1 - Aquecimento" if diff == 1 else "Nível 2 - Finais"

        q_slide = SlideInfo(
            index=2 * idx,
            object_id=f"q_{idx}",
            text_content=(
                f"LOTE {idx:03d} • {nivel_label} • {qid}\n"
                f"Enunciado químico completo da questão de teste número {idx}.\n"
                "Opção A) Alternativa A explicada detalhadamente.\n"
                "Opção B) Alternativa B explicada detalhadamente.\n"
                "Teto de R$ 200 • Aposta no Papel"
            ),
            speaker_notes=f"Notas do orador para a pergunta {idx} ({qid}).",
            element_count=6,
            background_color="#F8F9FA",
            shapes=[{"shape_type": "ROUND_RECTANGLE", "background_color": "#FFFFFF"}],
            text_runs=[{"content": f"Pergunta {qid}", "font_family": "Open Sans"}],
        )

        a_slide = SlideInfo(
            index=2 * idx + 1,
            object_id=f"a_{idx}",
            text_content=(
                f"LOTE {idx:03d} • GABARITO OFICIAL: ALTERNATIVA A\n"
                f"Questão {qid}\n"
                "Resolução Passo a Passo:\n"
                "1. Identificação dos dados fornecidos e estequiometria.\n"
                "2. Cálculo das grandezas molares.\n"
                "Justificativa Científica Pedagógica:\n"
                "Explicação físico-química formal da alternativa vencedora.\n"
                "Regras de Pagamento: Dobro (×2) para 1-4 acertos ou +R$ 100 para unânime."
            ),
            speaker_notes=f"Notas do orador para o gabarito {idx} ({qid}).",
            element_count=7,
            background_color="#F8F9FA",
            shapes=[{"shape_type": "ROUND_RECTANGLE", "background_color": "#FFFFFF"}],
            text_runs=[{"content": f"Gabarito {qid}", "font_family": "Open Sans"}],
        )

        slides.append(q_slide)
        slides.append(a_slide)

    return PresentationInfo(
        presentation_id="MOCK_QA", title="All-In Químico — Q&A", slides=slides
    )


# ==============================================================================
# 1. TESTES DE REGRAS DIDÁTICAS (R1)
# ==============================================================================


class TestRulesVerification:
    """Testes unitários para o verificador do Deck de Regras (R1)."""

    def test_mock_rules_deck_all_pass(self):
        """O mock canônico de regras deve passar em 100% dos checks."""
        deck = create_mock_rules_deck()
        results = verify_rules_deck(deck)
        failed = [r for r in results if not r.passed]
        assert len(failed) == 0, f"Checks que falharam: {[r.check_id for r in failed]}"
        assert len(results) == 12

    def test_missing_total_economy_fails(self):
        """Ausência do valor de R$ 10.000 deve falhar no check R1_TOTAL_ECONOMY."""
        deck = create_mock_rules_deck()
        for s in deck.slides:
            s.text_content = s.text_content.replace("10.000", "2.000").replace(
                "10000", "2000"
            )
        results = verify_rules_deck(deck)
        r = next(res for res in results if res.check_id == "R1_TOTAL_ECONOMY")
        assert not r.passed

    def test_missing_initial_balance_fails(self):
        """Saldo inicial divergente de R$ 1.000 deve falhar no check R1_INITIAL_BALANCE."""
        deck = create_mock_rules_deck()
        for s in deck.slides:
            s.text_content = s.text_content.replace("1.000", "400").replace(
                "1000", "400"
            )
        results = verify_rules_deck(deck)
        r = next(res for res in results if res.check_id == "R1_INITIAL_BALANCE")
        assert not r.passed

    def test_outdated_speaker_note_fails(self):
        """Nota de orador no Slide 2 contendo 'R$ 400 = 2x100 + 3x50 + 5x10' deve falhar."""
        deck = create_mock_rules_deck()
        deck.slides[1].speaker_notes = (
            "Explique o kit inicial entregue a cada grupo (R$ 400 = 2x100 + 3x50 + 5x10)..."
        )
        results = verify_rules_deck(deck)
        r = next(res for res in results if res.check_id == "R1_SPEAKER_NOTE_SLIDE_2")
        assert not r.passed

    def test_missing_no_paddles_fails(self):
        """Ausência da especificação 'sem placas' deve falhar no check R1_BETTING_MECHANIC_NO_PADDLES."""
        deck = create_mock_rules_deck()
        for s in deck.slides:
            s.text_content = s.text_content.replace("Sem Placas", "Com Placas").replace(
                "sem placas", "com placas"
            )
        results = verify_rules_deck(deck)
        r = next(
            res for res in results if res.check_id == "R1_BETTING_MECHANIC_NO_PADDLES"
        )
        assert not r.passed

    def test_missing_bet_cap_200_fails(self):
        """Ausência do teto estrito de R$ 200 deve falhar no check R1_BET_LIMITS."""
        deck = create_mock_rules_deck()
        for s in deck.slides:
            s.text_content = s.text_content.replace("200", "500")
        results = verify_rules_deck(deck)
        r = next(res for res in results if res.check_id == "R1_BET_LIMITS")
        assert not r.passed

    def test_missing_bonus_multiplier_fails(self):
        """Ausência de menção ao dobro (×2) para 1-4 acertos deve falhar no check R1_BONUS_MULTIPLIER_2X."""
        deck = create_mock_rules_deck()
        for s in deck.slides:
            s.text_content = (
                s.text_content.replace("×2", "")
                .replace("x2", "")
                .replace("Dobro", "Triplo")
                .replace("DOBRO", "TRIPLO")
                .replace("dobro", "triplo")
                .replace("100%", "300%")
            )
        results = verify_rules_deck(deck)
        r = next(res for res in results if res.check_id == "R1_BONUS_MULTIPLIER_2X")
        assert not r.passed

    def test_missing_unanimous_bonus_fails(self):
        """Ausência do bônus unânime de +R$ 100 para todos os 5 grupos deve falhar."""
        deck = create_mock_rules_deck()
        for s in deck.slides:
            s.text_content = s.text_content.replace("BÔNUS UNÂNIME", "BÔNUS").replace(
                "unânime", "geral"
            )
        results = verify_rules_deck(deck)
        r = next(res for res in results if res.check_id == "R1_UNANIMOUS_BONUS")
        assert not r.passed

    def test_missing_desafio_mesa_trigger_fails(self):
        """Ausência do gatilho de empate técnico (≤ R$ 100) deve falhar no check R1_DESAFIO_MESA_GATILHO."""
        deck = create_mock_rules_deck()
        for s in deck.slides:
            s.text_content = s.text_content.replace(
                "EMPATE TÉCNICO", "DISPUTA"
            ).replace("empate técnico", "disputa")
        results = verify_rules_deck(deck)
        r = next(res for res in results if res.check_id == "R1_DESAFIO_MESA_GATILHO")
        assert not r.passed

    def test_missing_winner_takes_all_fails(self):
        """Ausência de Winner Takes All / 100% no pote deve falhar no check R1_DESAFIO_MESA_WTA."""
        deck = create_mock_rules_deck()
        for s in deck.slides:
            s.text_content = (
                s.text_content.replace("WINNER TAKES ALL", "DIVISÃO")
                .replace("Winner Takes All", "Divisão")
                .replace("quem acertar leva tudo", "quem acertar divide")
                .replace("leva tudo", "divide")
            )
        results = verify_rules_deck(deck)
        r = next(res for res in results if res.check_id == "R1_DESAFIO_MESA_WTA")
        assert not r.passed

    def test_missing_repescagem_fails(self):
        """Ausência da mecânica de Repescagem (+R$ 200 na última rodada) deve falhar no check R1_REPESCAGEM_MECHANIC."""
        deck = create_mock_rules_deck()
        for s in deck.slides:
            s.text_content = s.text_content.replace("Repescagem", "Rodada").replace(
                "repescagem", "rodada"
            )
        results = verify_rules_deck(deck)
        r = next(res for res in results if res.check_id == "R1_REPESCAGEM_MECHANIC")
        assert not r.passed


# ==============================================================================
# 2. TESTES DE SEQUÊNCIA INTERCALADA Q&A (R2 LEGADO)
# ==============================================================================


class TestQASequenceVerification:
    """Testes unitários para o verificador do Deck Sequencial Monolítico de Perguntas e Respostas (R2 Legado)."""

    def test_mock_qa_deck_all_pass(self):
        """O mock canônico com 41 slides deve passar em 100% dos checks de R2."""
        deck = create_mock_qa_deck()
        results = verify_qa_deck(deck)
        failed = [r for r in results if not r.passed]
        assert len(failed) == 0, f"Checks que falharam: {[r.check_id for r in failed]}"
        assert len(results) == 7

    def test_slide_count_not_41_fails(self):
        """Deck com contagem diferente de 41 slides (ex: 40 slides) deve falhar."""
        deck = create_mock_qa_deck()
        deck.slides.pop()
        results = verify_qa_deck(deck)
        r = next(res for res in results if res.check_id == "R2_TOTAL_SLIDES_COUNT")
        assert not r.passed

    def test_parity_inversion_fails(self):
        """Inversão da ordem (slide de resposta no índice 2i e pergunta no 2i+1) deve falhar na paridade."""
        deck = create_mock_qa_deck()
        deck.slides[1], deck.slides[2] = deck.slides[2], deck.slides[1]
        results = verify_qa_deck(deck)
        r = next(res for res in results if res.check_id == "R2_INTERLEAVED_PARITY")
        assert not r.passed

    def test_lote_mismatch_fails_parity(self):
        """Divergência entre o lote anunciado na pergunta e na resposta subsequente deve falhar."""
        deck = create_mock_qa_deck()
        deck.slides[2].text_content = deck.slides[2].text_content.replace(
            "LOTE 001", "LOTE 005"
        )
        results = verify_qa_deck(deck)
        r = next(res for res in results if res.check_id == "R2_INTERLEAVED_PARITY")
        assert not r.passed

    def test_missing_nivel_1_question_fails(self):
        """Ausência de uma questão obrigatória de Nível 1 deve falhar no check R2_SCOPE_NIVEL_1."""
        deck = create_mock_qa_deck()
        for s in deck.slides:
            s.text_content = s.text_content.replace("Q-ATO-001", "Q-MOCK-999")
            s.speaker_notes = s.speaker_notes.replace("Q-ATO-001", "Q-MOCK-999")
        results = verify_qa_deck(deck)
        r = next(res for res in results if res.check_id == "R2_SCOPE_NIVEL_1")
        assert not r.passed
        assert "Q-ATO-001" in r.details

    def test_missing_nivel_2_question_fails(self):
        """Ausência de uma questão obrigatória de Nível 2 deve falhar no check R2_SCOPE_NIVEL_2."""
        deck = create_mock_qa_deck()
        for s in deck.slides:
            s.text_content = s.text_content.replace("Q-SOL-002", "Q-MOCK-999")
            s.speaker_notes = s.speaker_notes.replace("Q-SOL-002", "Q-MOCK-999")
        results = verify_qa_deck(deck)
        r = next(res for res in results if res.check_id == "R2_SCOPE_NIVEL_2")
        assert not r.passed
        assert "Q-SOL-002" in r.details

    def test_presence_of_nivel_3_id_fails(self):
        """Vazamento de um ID de Nível 3 (ex: Q-SOL-005) em qualquer slide deve reprovar imediatamente."""
        deck = create_mock_qa_deck()
        deck.slides[10].text_content += " Menção a Q-SOL-005 no enunciado."
        results = verify_qa_deck(deck)
        r = next(res for res in results if res.check_id == "R2_EXCLUSION_N3_IDS")
        assert not r.passed
        assert "Q-SOL-005" in r.details

    def test_presence_of_nivel_3_pattern_fails(self):
        """Vazamento de padrão proibido como '🔥 [APOSTA NO TEMA' ou 'Nível 3' deve reprovar."""
        deck = create_mock_qa_deck()
        deck.slides[15].speaker_notes += " Esta pergunta veio do Nível 3 Morte Súbita."
        results = verify_qa_deck(deck)
        r = next(res for res in results if res.check_id == "R2_EXCLUSION_N3_PATTERNS")
        assert not r.passed


# ==============================================================================
# 3. TESTES DA APRESENTAÇÃO DE TESTE EXCLUSIVA (R2 MULTI-DECK)
# ==============================================================================


class TestTestDeckVerification:
    """Testes unitários especializados para o Deck de Teste Exclusivo (R2)."""

    def test_valid_test_deck_all_pass(self):
        """Deck de teste com 7 slides e exatamente 3 questões N1 deve passar em 100% dos checks."""
        deck = create_mock_test_deck()
        results = verify_test_deck(deck)
        failed = [r for r in results if not r.passed]
        assert len(failed) == 0, f"Falhas no deck de teste: {[r.check_id for r in failed]}"
        check_ids = {r.check_id for r in results}
        assert "TEST_SLIDES_COUNT" in check_ids
        assert "TEST_N1_EXACT_3" in check_ids
        assert "TEST_EXCLUDE_N2" in check_ids
        assert "TEST_EXCLUDE_N3" in check_ids
        assert "TEST_INTERLEAVED_PARITY" in check_ids
        assert "TEST_DS_BG_COLOR" in check_ids
        assert "TEST_DS_CARD_FILL" in check_ids
        assert "TEST_DS_FONT_FAMILY" in check_ids
        assert "TEST_DS_FONT_SCALE" in check_ids

    def test_test_deck_wrong_slide_count_fails(self):
        """Deck de teste com 6 ou 8 slides deve falhar em TEST_SLIDES_COUNT."""
        deck = create_mock_test_deck()
        deck.slides.pop()  # 6 slides
        results = verify_test_deck(deck)
        r = next(res for res in results if res.check_id == "TEST_SLIDES_COUNT")
        assert not r.passed

    def test_test_deck_wrong_number_of_questions_fails(self):
        """Deck de teste com apenas 2 questões N1 (em vez de 3) deve falhar."""
        deck = create_mock_test_deck(question_ids=["Q-ATO-001", "Q-SOL-001"])
        results = verify_test_deck(deck)
        r = next(res for res in results if res.check_id == "TEST_N1_EXACT_3")
        assert not r.passed
        assert "2 questões detectadas" in r.details

    def test_test_deck_non_n1_question_fails(self):
        """Deck de teste contendo questão de Nível 2 (ex: Q-SOL-002) deve falhar."""
        deck = create_mock_test_deck(
            question_ids=["Q-ATO-001", "Q-SOL-001", "Q-SOL-002"]
        )
        results = verify_test_deck(deck)
        r_n1 = next(res for res in results if res.check_id == "TEST_N1_EXACT_3")
        assert not r_n1.passed
        r_n2 = next(res for res in results if res.check_id == "TEST_EXCLUDE_N2")
        assert not r_n2.passed

    def test_test_deck_n3_question_leaked_fails(self):
        """Vazamento de questão N3 (ex: Q-SOL-005) no deck de teste deve falhar categoricamente."""
        deck = create_mock_test_deck(
            question_ids=["Q-ATO-001", "Q-SOL-001", "Q-SOL-005"]
        )
        results = verify_test_deck(deck)
        r = next(res for res in results if res.check_id == "TEST_EXCLUDE_N3")
        assert not r.passed

    def test_test_deck_parity_inversion_fails(self):
        """Inversão de paridade em um dos pares Q&A do deck de teste deve falhar."""
        deck = create_mock_test_deck()
        deck.slides[1], deck.slides[2] = deck.slides[2], deck.slides[1]
        results = verify_test_deck(deck)
        r = next(res for res in results if res.check_id == "TEST_INTERLEAVED_PARITY")
        assert not r.passed


# ==============================================================================
# 4. TESTES DAS APRESENTAÇÕES DE DESAFIO INDIVIDUAL N3 (R3)
# ==============================================================================


class TestChallengeDeckVerification:
    """Testes unitários especializados para Apresentações de Desafio N3 (R3)."""

    def test_valid_challenge_deck_passes(self):
        """Apresentação de desafio com exatamente 3 slides e 1 questão N3 deve passar."""
        deck = create_mock_challenge_deck(question_id="Q-SOL-005")
        results = verify_challenge_deck(deck, expected_question_id="Q-SOL-005")
        failed = [r for r in results if not r.passed]
        assert len(failed) == 0, f"Falhas no desafio: {[r.check_id for r in failed]}"
        check_ids = {r.check_id for r in results}
        assert "CHALLENGE_SLIDES_COUNT" in check_ids
        assert "CHALLENGE_N3_EXACT_1" in check_ids
        assert "CHALLENGE_EXCLUDE_N1_N2" in check_ids
        assert "CHALLENGE_INTERLEAVED_PARITY" in check_ids

    def test_challenge_deck_wrong_slide_count_fails(self):
        """Desafio com 2 slides (sem capa) deve falhar na contagem de slides."""
        deck = create_mock_challenge_deck(question_id="Q-SOL-005", total_slides=2)
        results = verify_challenge_deck(deck)
        r = next(res for res in results if res.check_id == "CHALLENGE_SLIDES_COUNT")
        assert not r.passed

    def test_challenge_deck_more_than_one_question_fails(self):
        """Apresentação de desafio contendo mais de 1 questão deve falhar categoricamente."""
        deck = create_mock_challenge_deck(question_id="Q-SOL-005")
        deck.slides[1].text_content += " Menção à questão secundária Q-SOL-007."
        results = verify_challenge_deck(deck)
        r = next(res for res in results if res.check_id == "CHALLENGE_N3_EXACT_1")
        assert not r.passed

    def test_challenge_deck_non_n3_question_fails(self):
        """Desafio contendo questão de Nível 1 (ex: Q-ATO-001) deve falhar."""
        deck = create_mock_challenge_deck(question_id="Q-ATO-001")
        results = verify_challenge_deck(deck)
        r = next(res for res in results if res.check_id == "CHALLENGE_N3_EXACT_1")
        assert not r.passed
        r_n1 = next(res for res in results if res.check_id == "CHALLENGE_EXCLUDE_N1_N2")
        assert not r_n1.passed

    def test_challenge_deck_mismatched_expected_id_fails(self):
        """Desafio configurado para Q-SOL-007 contendo Q-SOL-005 deve falhar."""
        deck = create_mock_challenge_deck(question_id="Q-SOL-005")
        results = verify_challenge_deck(deck, expected_question_id="Q-SOL-007")
        r = next(res for res in results if res.check_id == "CHALLENGE_N3_EXACT_1")
        assert not r.passed


# ==============================================================================
# 5. TESTES DAS APRESENTAÇÕES REGULARES (R4)
# ==============================================================================


class TestRegularDeckVerification:
    """Testes unitários especializados para Decks Regulares de 5 Questões (R4)."""

    def test_valid_regular_deck_passes(self):
        """Deck regular com 11 slides e 5 questões N1/N2 deve passar com 100% de sucesso."""
        deck = create_mock_regular_deck()
        results = verify_regular_deck(deck)
        failed = [r for r in results if not r.passed]
        assert len(failed) == 0, f"Falhas no deck regular: {[r.check_id for r in failed]}"
        check_ids = {r.check_id for r in results}
        assert "REGULAR_SLIDES_COUNT" in check_ids
        assert "REGULAR_EXACT_5_QUESTIONS" in check_ids
        assert "REGULAR_EXCLUDE_N3" in check_ids
        assert "REGULAR_INTERLEAVED_PARITY" in check_ids

    def test_regular_deck_wrong_slide_count_fails(self):
        """Deck regular com 10 ou 12 slides deve falhar em REGULAR_SLIDES_COUNT."""
        deck = create_mock_regular_deck(total_slides=10)
        results = verify_regular_deck(deck)
        r = next(res for res in results if res.check_id == "REGULAR_SLIDES_COUNT")
        assert not r.passed

    def test_regular_deck_wrong_question_count_fails(self):
        """Deck regular com 4 questões em vez de 5 deve falhar em REGULAR_EXACT_5_QUESTIONS."""
        deck = create_mock_regular_deck(
            question_ids=["Q-ATO-002", "Q-SOL-006", "Q-STO-002", "Q-STO-003"]
        )
        results = verify_regular_deck(deck)
        r = next(res for res in results if res.check_id == "REGULAR_EXACT_5_QUESTIONS")
        assert not r.passed

    def test_regular_deck_n3_question_leaked_fails(self):
        """Vazamento de questão N3 (ex: Q-SOL-005) em deck regular deve falhar em REGULAR_EXCLUDE_N3."""
        deck = create_mock_regular_deck(
            question_ids=["Q-ATO-002", "Q-SOL-006", "Q-STO-002", "Q-STO-003", "Q-SOL-005"]
        )
        results = verify_regular_deck(deck)
        r = next(res for res in results if res.check_id == "REGULAR_EXCLUDE_N3")
        assert not r.passed

    def test_regular_deck_n3_pattern_leaked_fails(self):
        """Vazamento do termo 'Nível 3' ou 'Morte Súbita' em deck regular deve falhar."""
        deck = create_mock_regular_deck()
        deck.slides[4].text_content += " 🔥 [APOSTA NO TEMA: Nível 3 Morte Súbita]"
        results = verify_regular_deck(deck)
        r = next(res for res in results if res.check_id == "REGULAR_EXCLUDE_N3")
        assert not r.passed


# ==============================================================================
# 6. TESTES DO DECK DE DESEMPATE / SUPLENTE (NÍVEL 2)
# ==============================================================================


class TestTiebreakerDeckVerification:
    """Testes unitários para o Deck Suplente / Desempate Técnico."""

    def test_valid_tiebreaker_deck_passes(self):
        """Deck de desempate com 5 slides e 2 questões N2 deve passar."""
        deck = create_mock_tiebreaker_deck()
        results = verify_tiebreaker_deck(deck)
        failed = [r for r in results if not r.passed]
        assert len(failed) == 0, f"Falhas no desempate: {[r.check_id for r in failed]}"
        check_ids = {r.check_id for r in results}
        assert "TIEBREAKER_SLIDES_COUNT" in check_ids
        assert "TIEBREAKER_EXACT_2_QUESTIONS" in check_ids
        assert "TIEBREAKER_EXCLUDE_N3" in check_ids

    def test_tiebreaker_wrong_question_count_fails(self):
        """Deck de desempate com 3 questões em vez de 2 deve falhar."""
        deck = create_mock_tiebreaker_deck(
            question_ids=["Q-ENV-005", "Q-STO-007", "Q-SOL-009"]
        )
        results = verify_tiebreaker_deck(deck)
        r = next(res for res in results if res.check_id == "TIEBREAKER_EXACT_2_QUESTIONS")
        assert not r.passed

    def test_tiebreaker_n3_leaked_fails(self):
        """Vazamento de questão N3 no deck de desempate deve falhar."""
        deck = create_mock_tiebreaker_deck(
            question_ids=["Q-ENV-005", "Q-SOL-005"]
        )
        results = verify_tiebreaker_deck(deck)
        r = next(res for res in results if res.check_id == "TIEBREAKER_EXCLUDE_N3")
        assert not r.passed


# ==============================================================================
# 7. TESTES DE DESIGN SYSTEM E ANTI-OVERFLOW (R5)
# ==============================================================================


class TestDesignSystemVerification:
    """Testes unitários para conformidade visual Fintech Clean e prevenção de overflow."""

    def test_design_system_valid_deck_passes(self):
        """Deck com atributos visuais canônicos (#F8F9FA, #FFFFFF, Open Sans, fontScale=1.0) passa."""
        deck = create_mock_regular_deck()
        results = verify_design_system(deck)
        failed = [r for r in results if not r.passed]
        assert len(failed) == 0, f"Falhas no Design System: {[r.check_id for r in failed]}"

    def test_design_system_wrong_background_fails(self):
        """Slide com fundo escuro (#0F172A) ou branco (#FFFFFF) deve falhar em DS_BG_COLOR."""
        deck = create_mock_regular_deck()
        deck.slides[2].background_color = "#0F172A"  # Fundo escuro não autorizado
        results = verify_design_system(deck)
        r = next(res for res in results if res.check_id == "DS_BG_COLOR")
        assert not r.passed
        assert "Slides com fundo divergente" in r.details

    def test_design_system_wrong_font_family_fails(self):
        """Elemento de texto utilizando fonte Arial ou Roboto deve falhar em DS_FONT_FAMILY."""
        deck = create_mock_regular_deck()
        deck.slides[3].text_runs.append(
            {"content": "Texto em Arial", "font_family": "Arial"}
        )
        results = verify_design_system(deck)
        r = next(res for res in results if res.check_id == "DS_FONT_FAMILY")
        assert not r.passed
        assert "Arial" in r.details

    def test_design_system_severe_font_scale_shrinkage_fails(self):
        """Slide com fontScale < 0.90 (compressão severa de texto) deve falhar em DS_FONT_SCALE."""
        deck = create_mock_regular_deck()
        deck.slides[4].min_font_scale = 0.85  # Compressão excessiva (>10%)
        results = verify_design_system(deck)
        r = next(res for res in results if res.check_id == "DS_FONT_SCALE")
        assert not r.passed
        assert "fontScale < 0.90" in r.details

    def test_design_system_missing_white_card_fails(self):
        """Slide de conteúdo sem card branco (#FFFFFF) deve falhar em DS_CARD_FILL."""
        deck = create_mock_regular_deck(add_white_cards=False)
        results = verify_design_system(deck)
        r = next(res for res in results if res.check_id == "DS_CARD_FILL")
        assert not r.passed


# ==============================================================================
# 8. TESTES DE ISOLAMENTO CRUZADO E ZERO-REUSE (TIER 3)
# ==============================================================================


class TestCrossDeckZeroReuseAudit:
    """Testes unitários para auditoria de disjunção mútua e Zero-Reuse entre decks."""

    def test_valid_partition_all_pass(self):
        """Partição canônica completa das 25 questões deve passar com 100% de sucesso."""
        test_deck = ["Q-ATO-001", "Q-SOL-001", "Q-STO-001"]
        reg_decks = [
            ["Q-ATO-002", "Q-SOL-006", "Q-STO-002", "Q-STO-003", "Q-STO-004"],
            ["Q-STO-005", "Q-ENV-001", "Q-ENV-002", "Q-ENV-003", "Q-ENV-004"],
            ["Q-SOL-002", "Q-SOL-003", "Q-SOL-004", "Q-SOL-009", "Q-STO-006"],
        ]
        chal_decks = [
            ["Q-SOL-005"],
            ["Q-SOL-007"],
            ["Q-SOL-008"],
            ["Q-STO-008"],
            ["Q-ENV-006"],
        ]
        tiebreaker = ["Q-ENV-005", "Q-STO-007"]

        results = verify_cross_deck_isolation(
            test_deck=test_deck,
            regular_decks=reg_decks,
            challenge_decks=chal_decks,
            tiebreaker_deck=tiebreaker,
        )
        failed = [r for r in results if not r.passed]
        assert len(failed) == 0, f"Falhas no isolamento cruzado: {[r.check_id for r in failed]}"
        assert len(results) == 5

    def test_zero_reuse_test_question_leaked_into_regular_fails(self):
        """Vazamento de questão de teste (ex: Q-ATO-001) em deck regular deve falhar categoricamente."""
        test_deck = ["Q-ATO-001", "Q-SOL-001", "Q-STO-001"]
        reg_decks = [
            ["Q-ATO-001", "Q-SOL-006", "Q-STO-002", "Q-STO-003", "Q-STO-004"],  # Q-ATO-001 vazou!
            ["Q-STO-005", "Q-ENV-001", "Q-ENV-002", "Q-ENV-003", "Q-ENV-004"],
        ]
        results = verify_cross_deck_isolation(
            test_deck=test_deck,
            regular_decks=reg_decks,
            challenge_decks=[["Q-SOL-005"]],
        )
        r = next(
            res for res in results if res.check_id == "CROSS_TEST_REGULAR_DISJOINT"
        )
        assert not r.passed
        assert "Q-ATO-001" in r.details

    def test_test_question_leaked_into_challenge_fails(self):
        """Vazamento de questão de teste (ex: Q-SOL-001) em desafio deve falhar."""
        test_deck = ["Q-ATO-001", "Q-SOL-001", "Q-STO-001"]
        reg_decks = [["Q-ATO-002", "Q-SOL-006", "Q-STO-002", "Q-STO-003", "Q-STO-004"]]
        chal_decks = [["Q-SOL-001"]]  # Q-SOL-001 vazou no desafio!

        results = verify_cross_deck_isolation(
            test_deck=test_deck, regular_decks=reg_decks, challenge_decks=chal_decks
        )
        r = next(
            res for res in results if res.check_id == "CROSS_TEST_CHALLENGE_DISJOINT"
        )
        assert not r.passed
        assert "Q-SOL-001" in r.details

    def test_regular_decks_pairwise_collision_fails(self):
        """Questão duplicada entre dois decks regulares (ex: Q-STO-002) deve falhar."""
        test_deck = ["Q-ATO-001", "Q-SOL-001", "Q-STO-001"]
        reg_decks = [
            ["Q-ATO-002", "Q-SOL-006", "Q-STO-002", "Q-STO-003", "Q-STO-004"],
            ["Q-STO-002", "Q-ENV-001", "Q-ENV-002", "Q-ENV-003", "Q-ENV-004"],  # Q-STO-002 repetida!
        ]
        results = verify_cross_deck_isolation(
            test_deck=test_deck, regular_decks=reg_decks, challenge_decks=[["Q-SOL-005"]]
        )
        r = next(
            res for res in results if res.check_id == "CROSS_REGULAR_PAIRWISE_DISJOINT"
        )
        assert not r.passed
        assert "Q-STO-002" in r.details

    def test_challenge_decks_pairwise_collision_fails(self):
        """Dois decks de desafio contendo a mesma questão N3 devem falhar."""
        test_deck = ["Q-ATO-001", "Q-SOL-001", "Q-STO-001"]
        reg_decks = [["Q-ATO-002", "Q-SOL-006", "Q-STO-002", "Q-STO-003", "Q-STO-004"]]
        chal_decks = [["Q-SOL-005"], ["Q-SOL-005"]]  # Duplicado!

        results = verify_cross_deck_isolation(
            test_deck=test_deck, regular_decks=reg_decks, challenge_decks=chal_decks
        )
        r = next(
            res
            for res in results
            if res.check_id == "CROSS_CHALLENGE_PAIRWISE_DISJOINT"
        )
        assert not r.passed
        assert "Q-SOL-005" in r.details


# ==============================================================================
# 9. TESTES DE INTEGRAÇÃO VIA MANIFESTO E CLI (OFFLINE & E2E)
# ==============================================================================


class TestManifestAuditIntegration:
    """Testes de integração do motor de auditoria multi-deck baseado em manifesto JSON."""

    def test_manifest_audit_valid_pass(self):
        """Auditoria via manifesto mock válido passa com 100% de sucesso."""
        manifest_dict, mock_decks = create_mock_multi_deck_manifest()
        report = run_manifest_audit(
            manifest_data=manifest_dict, mock_decks=mock_decks, verbose=False
        )
        failed = [r for r in report.results if not r.passed]
        assert len(failed) == 0, f"Falhas no manifesto: {[r.check_id for r in failed]}"
        assert report.success is True
        assert report.total_checks >= 50

    def test_manifest_missing_file_fails(self):
        """Tentativa de auditar manifesto inexistente deve gerar resultado de falha."""
        report = run_manifest_audit(manifest_path="caminho_inexistente_xyz.json")
        assert report.success is False
        r = next(res for res in report.results if res.check_id == "MANIFEST_NOT_FOUND")
        assert not r.passed

    def test_manifest_offline_batch_operations(self):
        """Validação offline simulada a partir de operações declarativas de mutação em lote."""
        ops = [
            {"op": "set-background", "slide": "p", "color": "#F8F9FA"},
            {
                "op": "add-shape",
                "slide": "p",
                "shape_type": "ROUND_RECTANGLE",
                "background_color": "#FFFFFF",
            },
            {
                "op": "add-textbox",
                "slide": "p",
                "text": "ALL-IN QUÍMICO • TESTE",
                "font_family": "Open Sans",
            },
            {"op": "add-slide", "id": "s2"},
            {"op": "set-background", "slide": "s2", "color": "#F8F9FA"},
            {
                "op": "add-shape",
                "slide": "s2",
                "shape_type": "ROUND_RECTANGLE",
                "background_color": "#FFFFFF",
            },
            {
                "op": "add-textbox",
                "slide": "s2",
                "text": "LOTE 001 • Q-ATO-001 • Pergunta Opção A / B",
                "font_family": "Open Sans",
                "font_scale": 1.0,
            },
        ]
        pres = parse_batch_operations(ops, presentation_id="BATCH_SAMPLE")
        assert len(pres.slides) == 2
        assert pres.slides[0].background_color == "#F8F9FA"
        assert pres.slides[1].min_font_scale == 1.0
        assert "Q-ATO-001" in pres.slides[1].text_content

    def test_cli_manifest_execution_pass(self, tmp_path):
        """Execução do script via CLI com --manifest, --offline e --json em caso de sucesso."""
        manifest_dict, mock_decks = create_mock_multi_deck_manifest()

        # Salva apresentações mock como arquivos JSON locais
        deck_files: dict[str, Path] = {}
        for deck_id, pres in mock_decks.items():
            fpath = tmp_path / f"{deck_id}.json"
            slides_data = [
                {
                    "objectId": s.object_id,
                    "background_color": s.background_color,
                    "shapes": s.shapes,
                    "text_runs": s.text_runs,
                    "min_font_scale": s.min_font_scale,
                    "pageElements": [
                        {
                            "shape": {
                                "shapeType": "ROUND_RECTANGLE",
                                "shapeProperties": {
                                    "shapeBackgroundFill": {
                                        "solidFill": {
                                            "color": {
                                                "rgbColor": {
                                                    "red": 1.0,
                                                    "green": 1.0,
                                                    "blue": 1.0,
                                                }
                                            }
                                        }
                                    }
                                },
                                "text": {
                                    "textElements": [
                                        {
                                            "textRun": {
                                                "content": s.text_content,
                                                "style": {
                                                    "fontFamily": "Open Sans"
                                                },
                                            }
                                        }
                                    ]
                                },
                            }
                        }
                    ],
                    "slideProperties": {
                        "notesPage": {
                            "pageElements": [
                                {
                                    "shape": {
                                        "placeholder": {"type": "BODY"},
                                        "text": {
                                            "textElements": [
                                                {
                                                    "textRun": {
                                                        "content": s.speaker_notes
                                                    }
                                                }
                                            ]
                                        },
                                    }
                                }
                            ]
                        }
                    },
                }
                for s in pres.slides
            ]
            fpath.write_text(
                json.dumps(
                    {"title": pres.title, "slides": slides_data}, ensure_ascii=False
                ),
                encoding="utf-8",
            )
            deck_files[deck_id] = fpath

        # Atualiza o manifesto para apontar para os arquivos locais
        manifest_dict["decks"]["test_deck"]["presentation_id"] = str(
            deck_files["TEST_DECK_ID"]
        )
        for chal in manifest_dict["decks"]["challenges"]:
            chal["presentation_id"] = str(deck_files[chal["presentation_id"]])
        for reg in manifest_dict["decks"]["regular_decks"]:
            reg["presentation_id"] = str(deck_files[reg["presentation_id"]])
        manifest_dict["decks"]["tiebreaker_deck"]["presentation_id"] = str(
            deck_files["TIEBREAKER_ID"]
        )

        manifest_file = tmp_path / "decks_manifest.json"
        manifest_file.write_text(
            json.dumps(manifest_dict, ensure_ascii=False), encoding="utf-8"
        )

        script_path = SPEC_DIR / "verificar_decks_slides.py"
        cmd = [
            sys.executable,
            str(script_path),
            "--manifest",
            str(manifest_file),
            "--offline",
            "--json",
        ]
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        assert proc.returncode == 0, (
            f"Script CLI falhou com código {proc.returncode}:\n{proc.stderr}\n{proc.stdout}"
        )
        data = json.loads(proc.stdout)
        assert data["success"] is True
        assert data["failed_checks"] == 0
        assert data["passed_checks"] >= 50

    def test_cli_manifest_execution_failure_exit_code_1(self, tmp_path):
        """Execução do CLI com violação proposital no manifesto deve retornar exit code 1."""
        manifest_dict, mock_decks = create_mock_multi_deck_manifest()

        # Injeta vazamento de Zero-Reuse (Q-ATO-001 do teste dentro do regular 01)
        mock_decks["REG_01_ID"].slides[1].text_content += " Q-ATO-001 vazou aqui!"

        deck_files: dict[str, Path] = {}
        for deck_id, pres in mock_decks.items():
            fpath = tmp_path / f"{deck_id}.json"
            slides_data = [
                {
                    "objectId": s.object_id,
                    "background_color": s.background_color,
                    "shapes": s.shapes,
                    "text_runs": s.text_runs,
                    "min_font_scale": s.min_font_scale,
                    "pageElements": [
                        {
                            "shape": {
                                "shapeType": "ROUND_RECTANGLE",
                                "shapeProperties": {
                                    "shapeBackgroundFill": {
                                        "solidFill": {
                                            "color": {
                                                "rgbColor": {
                                                    "red": 1.0,
                                                    "green": 1.0,
                                                    "blue": 1.0,
                                                }
                                            }
                                        }
                                    }
                                },
                                "text": {
                                    "textElements": [
                                        {
                                            "textRun": {
                                                "content": s.text_content,
                                                "style": {
                                                    "fontFamily": "Open Sans"
                                                },
                                            }
                                        }
                                    ]
                                },
                            }
                        }
                    ],
                }
                for s in pres.slides
            ]
            fpath.write_text(
                json.dumps(
                    {"title": pres.title, "slides": slides_data}, ensure_ascii=False
                ),
                encoding="utf-8",
            )
            deck_files[deck_id] = fpath

        manifest_dict["decks"]["test_deck"]["presentation_id"] = str(
            deck_files["TEST_DECK_ID"]
        )
        for chal in manifest_dict["decks"]["challenges"]:
            chal["presentation_id"] = str(deck_files[chal["presentation_id"]])
        for reg in manifest_dict["decks"]["regular_decks"]:
            reg["presentation_id"] = str(deck_files[reg["presentation_id"]])
        manifest_dict["decks"]["tiebreaker_deck"]["presentation_id"] = str(
            deck_files["TIEBREAKER_ID"]
        )

        manifest_file = tmp_path / "decks_manifest.json"
        manifest_file.write_text(
            json.dumps(manifest_dict, ensure_ascii=False), encoding="utf-8"
        )

        script_path = SPEC_DIR / "verificar_decks_slides.py"
        cmd = [
            sys.executable,
            str(script_path),
            "--manifest",
            str(manifest_file),
            "--offline",
            "--json",
        ]
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        assert proc.returncode == 1, (
            f"Esperava-se exit code 1 para falha de asserção, obteve {proc.returncode}"
        )
        data = json.loads(proc.stdout)
        assert data["success"] is False
        assert data["failed_checks"] >= 1

    def test_real_generated_manifest_offline_passes(self):
        """Audita o manifesto real gerado no repositório specs/SPEC-03-gerador/decks_manifest.json se presente."""
        manifest_path = SPEC_DIR / "decks_manifest.json"
        if manifest_path.is_file():
            report = run_manifest_audit(manifest_path=manifest_path, offline=True)
            failed = [r for r in report.results if not r.passed]
            assert len(failed) == 0, (
                f"Falhas no manifesto real gerado: {[(r.check_id, r.details) for r in failed]}"
            )
            assert report.success is True
            assert report.total_checks >= 80


# ==============================================================================
# 10. TESTES DE INTEGRAÇÃO COM GOOGLE SLIDES REAL
# ==============================================================================


class TestRealGoogleSlidesIntegration:
    """Testes de integração executados contra a apresentação real no Google Slides."""

    def test_real_rules_deck_audit_passes(self):
        """Audita a apresentação real de regras 1KpfettWa9KkvbmBmhNAkyWRlTPPzahCeTVCuNlA3VU0."""
        report = run_full_audit(
            rules_deck_id=DEFAULT_RULES_DECK_ID, rules_only=True, verbose=False
        )
        failed = [r for r in report.results if not r.passed]
        assert len(failed) == 0, (
            f"Falhas no deck real de regras: {[(r.check_id, r.details) for r in failed]}"
        )
        assert report.success is True
        assert report.total_checks == 12

    def test_cli_rules_only_execution(self):
        """Executa o script de verificação via linha de comando com a flag --rules-only."""
        script_path = SPEC_DIR / "verificar_decks_slides.py"
        cmd = [sys.executable, str(script_path), "--rules-only", "--json"]
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        assert proc.returncode == 0, (
            f"Script CLI falhou com código {proc.returncode}:\n{proc.stderr}"
        )
        data = json.loads(proc.stdout)
        assert data["success"] is True
        assert data["failed_checks"] == 0
        assert data["passed_checks"] >= 11

    def test_real_qa_deck_audit_passes(self):
        """Audita a apresentação real de Perguntas e Respostas N1/N2 no Google Slides."""
        qa_deck_id = "10HrhJkrYDnxwhCP6HEo75DWvU9NS2RHXmp2wcx8XZUk"
        report = run_full_audit(qa_deck_id=qa_deck_id, qa_only=True, verbose=False)
        failed = [r for r in report.results if not r.passed]
        assert len(failed) == 0, (
            f"Falhas no deck real de Q&A: {[(r.check_id, r.details) for r in failed]}"
        )
        assert report.success is True
        assert report.total_checks == 7

    def test_cli_full_audit_execution(self):
        """Executa a auditoria completa de ambos os decks (R1 + R2) via CLI com saída JSON."""
        script_path = SPEC_DIR / "verificar_decks_slides.py"
        qa_deck_id = "10HrhJkrYDnxwhCP6HEo75DWvU9NS2RHXmp2wcx8XZUk"
        cmd = [
            sys.executable,
            str(script_path),
            "--rules-deck",
            DEFAULT_RULES_DECK_ID,
            "--qa-deck",
            qa_deck_id,
            "--json",
        ]
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        assert proc.returncode == 0, (
            f"Script CLI falhou com código {proc.returncode}:\n{proc.stderr}"
        )
        data = json.loads(proc.stdout)
        assert data["success"] is True
        assert data["failed_checks"] == 0
        assert data["passed_checks"] == 19
