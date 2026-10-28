"""
Suíte de Testes Automatizados para o Validador de Slides — All-In Químico
========================================================================
Testa de forma abrangente e rigorosa o auditor programático:
  1. Testes Unitários de Regras Didáticas (R1):
     - Caso canônico válido (100% aprovação)
     - Adversarial: ausência de R$ 10.000 ou repartição 5k/5k
     - Adversarial: saldo inicial incorreto
     - Adversarial: notas do orador com texto obsoleto de R$ 400
     - Adversarial: ausência de especificação "sem placas"
     - Adversarial: ausência de teto R$ 200 ou mínimo R$ 10
     - Adversarial: falha no multiplicador 2x
     - Adversarial: ausência de bônus unânime +R$ 100
     - Adversarial: ausência de penalidade de erro
     - Adversarial: falha no gatilho de empate técnico (<= R$ 100)
     - Adversarial: falha na mecânica Winner Takes All
  2. Testes Unitários de Sequência Q&A (R2):
     - Caso canônico válido com 41 slides intercalados e 20 questões
     - Adversarial: contagem diferente de 41 slides
     - Adversarial: inversão de paridade (resposta antes de pergunta)
     - Adversarial: divergência de lote entre pergunta e resposta
     - Adversarial: ausência de questão de Nível 1
     - Adversarial: ausência de questão de Nível 2
     - Adversarial: vazamento de ID de Nível 3 (Q-SOL-005, etc.)
     - Adversarial: vazamento de texto proibido "Nível 3" ou "🔥 [APOSTA NO TEMA"
  3. Testes de Integração / E2E com Google Slides Real:
     - Auditoria do deck real de regras (ID 1KpfettWa9KkvbmBmhNAkyWRlTPPzahCeTVCuNlA3VU0)
     - Execução via CLI com flags --rules-only e --json
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
    PresentationInfo,
    SlideInfo,
    run_full_audit,
    verify_qa_deck,
    verify_rules_deck,
)

# ==============================================================================
# FIXTURES E MOCKS DE DADOS DE TESTE
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
        ),
    ]
    return PresentationInfo(
        presentation_id="MOCK_RULES", title="All-In Químico — Regras", slides=slides
    )


def create_mock_qa_deck() -> PresentationInfo:
    """Cria uma representação mock perfeitamente em conformidade com R2 (41 slides, 20 pares intercalados)."""
    slides = [
        SlideInfo(
            index=1,
            object_id="cover",
            text_content="ALL-IN QUÍMICO — Cards de Perguntas e Respostas (Níveis 1 e 2)",
            speaker_notes="Capa oficial do deck sequencial.",
            element_count=3,
        )
    ]

    all_ids = EXPECTED_NIVEL_1_IDS + EXPECTED_NIVEL_2_IDS  # 13 + 7 = 20
    for idx, qid in enumerate(all_ids, start=1):
        diff = 1 if idx <= 13 else 2
        nivel_label = "Nível 1 - Aquecimento" if diff == 1 else "Nível 2 - Finais"

        # Slide 2i: Pergunta
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
        )

        # Slide 2i+1: Resposta
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
        )

        slides.append(q_slide)
        slides.append(a_slide)

    return PresentationInfo(
        presentation_id="MOCK_QA", title="All-In Químico — Q&A", slides=slides
    )


# ==============================================================================
# TESTES DE REGRAS DIDÁTICAS (R1)
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
        deck.slides[
            1
        ].speaker_notes = "Explique o kit inicial entregue a cada grupo (R$ 400 = 2x100 + 3x50 + 5x10)..."
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
            s.text_content = s.text_content.replace("Repescagem", "Rodada").replace("repescagem", "rodada")
        results = verify_rules_deck(deck)
        r = next(res for res in results if res.check_id == "R1_REPESCAGEM_MECHANIC")
        assert not r.passed


# ==============================================================================
# TESTES DE SEQUÊNCIA INTERCALADA Q&A (R2)
# ==============================================================================


class TestQASequenceVerification:
    """Testes unitários para o verificador do Deck Sequencial de Perguntas e Respostas (R2)."""

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
        deck.slides.pop()  # 40 slides
        results = verify_qa_deck(deck)
        r = next(res for res in results if res.check_id == "R2_TOTAL_SLIDES_COUNT")
        assert not r.passed

    def test_parity_inversion_fails(self):
        """Inversão da ordem (slide de resposta no índice 2i e pergunta no 2i+1) deve falhar na paridade."""
        deck = create_mock_qa_deck()
        # Inverte o par 1 (slides 2 e 3)
        deck.slides[1], deck.slides[2] = deck.slides[2], deck.slides[1]
        results = verify_qa_deck(deck)
        r = next(res for res in results if res.check_id == "R2_INTERLEAVED_PARITY")
        assert not r.passed

    def test_lote_mismatch_fails_parity(self):
        """Divergência entre o lote anunciado na pergunta e na resposta subsequente deve falhar."""
        deck = create_mock_qa_deck()
        # Altera o lote da resposta do par 1 para Lote 005
        deck.slides[2].text_content = deck.slides[2].text_content.replace(
            "LOTE 001", "LOTE 005"
        )
        results = verify_qa_deck(deck)
        r = next(res for res in results if res.check_id == "R2_INTERLEAVED_PARITY")
        assert not r.passed

    def test_missing_nivel_1_question_fails(self):
        """Ausência de uma questão obrigatória de Nível 1 deve falhar no check R2_SCOPE_NIVEL_1."""
        deck = create_mock_qa_deck()
        # Remove a questão Q-ATO-001 de todos os slides
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
        # Remove a questão Q-SOL-002 de todos os slides
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
# TESTES DE INTEGRAÇÃO COM DECK DE REGRAS REAL
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
