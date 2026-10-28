#!/usr/bin/env python3
"""
Validador e Auditor Automatizado de Apresentações Google Slides — All-In Químico
==============================================================================
Inspeciona programaticamente as apresentações no Google Slides:
  1. Deck de Regras Didáticas (R1):
     - Economia Total de R$ 10.000 (R$ 5.000 nos grupos + R$ 5.000 no Banco)
     - Saldo Inicial por grupo de R$ 1.000 (cédulas de 100, 50, 10; notas de orador sem menção de R$ 400)
     - Mecânica de aposta e resposta no papel (sem placas)
     - Teto estrito de R$ 200 por pergunta (mínimo de R$ 10)
     - Bonificação: x2 para 1-4 acertos (+100% de lucro líquido), +R$ 100 fixo unânime para 5 acertos, perda ao errar
     - Desafio da Mesa pós-rodada 5: empate técnico (<= R$ 100 de distância do 1º colocado) e pote central 100% Winner Takes All
  2. Deck Sequencial Intercalado de Perguntas e Respostas (R2):
     - Total de slides exatamente 41 (1 capa + 20 pares Q&A)
     - Alternância estrita: para todo i in [1..20], slide 2i é Pergunta i e slide 2i+1 é Resposta i (com paridade de identificador)
     - Escopo fechado: todas as 13 questões de Nível 1 e todas as 7 questões de Nível 2 presentes
     - Exclusão categórica de Nível 3: nenhum dos 5 IDs (Q-SOL-005, Q-SOL-007, Q-SOL-008, Q-STO-008, Q-ENV-006) ou menção a "Nível 3" / "🔥 [APOSTA NO TEMA"

Retorna código de saída 0 se todos os testes passarem, ou 1 se houver qualquer falha.

Uso CLI:
  python verificar_decks_slides.py [--rules-deck <ID>] [--qa-deck <ID>] [--rules-only] [--qa-only] [--json] [--verbose]
"""

import argparse
import io
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Constantes e Defaults
DEFAULT_RULES_DECK_ID = "1-iuM4hRqyPBK4Xs_Kwvkf02xU8i_QsYwlkip_Q06m4k"
DEFAULT_QA_DECK_ID = "1sxQyIjsI11wq5IYZ4JuKmEhenvo52kwywcx1wcv5dQQ"

EXPECTED_NIVEL_1_IDS = [
    "Q-ATO-001",
    "Q-ATO-002",
    "Q-ENV-001",
    "Q-ENV-002",
    "Q-ENV-003",
    "Q-ENV-004",
    "Q-SOL-001",
    "Q-SOL-006",
    "Q-STO-001",
    "Q-STO-002",
    "Q-STO-003",
    "Q-STO-004",
    "Q-STO-005",
]

EXPECTED_NIVEL_2_IDS = [
    "Q-ENV-005",
    "Q-SOL-002",
    "Q-SOL-003",
    "Q-SOL-004",
    "Q-SOL-009",
    "Q-STO-006",
    "Q-STO-007",
]

FORBIDDEN_NIVEL_3_IDS = [
    "Q-SOL-005",
    "Q-SOL-007",
    "Q-SOL-008",
    "Q-STO-008",
    "Q-ENV-006",
]

FORBIDDEN_N3_PATTERNS = [
    r"N[ií]vel\s*3",
    r"🔥\s*\[APOSTA NO TEMA",
    r"APOSTA NO TEMA",
    r"Morte\s+S[uú]bita",
    r"Texas\s+Hold'?em",
]


@dataclass
class SlideInfo:
    """Informações agregadas de um slide individual."""

    index: int  # 1-indexed
    object_id: str
    text_content: str
    speaker_notes: str
    element_count: int


@dataclass
class PresentationInfo:
    """Metadados e slides de uma apresentação inspecionada."""

    presentation_id: str
    title: str
    slides: list[SlideInfo] = field(default_factory=list)


@dataclass
class CheckResult:
    """Resultado de uma asserção de auditoria."""

    check_id: str
    category: str
    title: str
    passed: bool
    details: str
    evidence: str | None = None


@dataclass
class AuditReport:
    """Relatório consolidado de auditoria."""

    rules_deck_id: str | None = None
    qa_deck_id: str | None = None
    results: list[CheckResult] = field(default_factory=list)

    @property
    def total_checks(self) -> int:
        return len(self.results)

    @property
    def passed_checks(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def failed_checks(self) -> int:
        return sum(1 for r in self.results if not r.passed)

    @property
    def success(self) -> bool:
        return self.failed_checks == 0 and self.total_checks > 0


def find_gslides_executable() -> str | None:
    """Localiza o binário do CLI gslides no sistema (compatível com Windows .cmd)."""
    cmd = shutil.which("gslides")
    if cmd:
        return cmd
    for candidate in ["gslides.cmd", "gslides.exe", "gslides"]:
        cmd = shutil.which(candidate)
        if cmd:
            return cmd
    return None


def extract_text_from_page_element(el: dict[str, Any]) -> list[str]:
    """Extrai recursivamente todos os textRuns de shapes, tabelas e grupos."""
    texts: list[str] = []
    # 1. Shapes / Text Boxes
    if "shape" in el and "text" in el["shape"]:
        for te in el["shape"]["text"].get("textElements", []):
            tr = te.get("textRun", {})
            if "content" in tr:
                texts.append(tr["content"])
    # 2. Tabelas
    if "table" in el:
        for row in el["table"].get("tableRows", []):
            for cell in row.get("tableCells", []):
                for te in cell.get("text", {}).get("textElements", []):
                    tr = te.get("textRun", {})
                    if "content" in tr:
                        texts.append(tr["content"])
    # 3. Grupos de elementos
    if "elementGroup" in el:
        for child in el["elementGroup"].get("children", []):
            texts.extend(extract_text_from_page_element(child))
    return texts


def extract_notes_from_slide_dict(slide_dict: dict[str, Any]) -> str:
    """Extrai texto das notas do orador (speaker notes) a partir da estrutura de slide."""
    notes_page = slide_dict.get("slideProperties", {}).get("notesPage", {})
    notes_text: list[str] = []
    for el in notes_page.get("pageElements", []):
        shape = el.get("shape", {})
        if shape.get("placeholder", {}).get("type") == "BODY":
            for te in shape.get("text", {}).get("textElements", []):
                tr = te.get("textRun", {})
                if "content" in tr:
                    notes_text.append(tr["content"])
    return "".join(notes_text).strip()


def parse_presentation_json(
    data: dict[str, Any], presentation_id: str
) -> PresentationInfo:
    """Converte o payload JSON retornado pela API/CLI em PresentationInfo estruturado."""
    title = data.get("title", "")
    slides_raw = data.get("slides", [])
    slide_infos: list[SlideInfo] = []

    for idx, s in enumerate(slides_raw, start=1):
        obj_id = s.get("objectId", f"slide_{idx}")
        page_elements = s.get("pageElements", [])
        extracted_texts: list[str] = []
        for el in page_elements:
            extracted_texts.extend(extract_text_from_page_element(el))
        combined_text = " ".join(extracted_texts).strip()
        notes = extract_notes_from_slide_dict(s)
        slide_infos.append(
            SlideInfo(
                index=idx,
                object_id=obj_id,
                text_content=combined_text,
                speaker_notes=notes,
                element_count=len(page_elements),
            )
        )

    return PresentationInfo(
        presentation_id=presentation_id, title=title, slides=slide_infos
    )


def fetch_presentation_from_cli(presentation_id: str) -> PresentationInfo:
    """Obtém os dados da apresentação usando o CLI gslides readonly info --json."""
    exe = find_gslides_executable()
    if not exe:
        raise RuntimeError("CLI 'gslides' não foi encontrado no PATH do sistema.")

    cmd = [exe, "readonly", "info", presentation_id, "--json"]
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    if proc.returncode != 0:
        raise RuntimeError(
            f"Falha ao executar 'gslides readonly info {presentation_id}':\n"
            f"Código: {proc.returncode}\nStderr: {proc.stderr.strip()}"
        )

    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"Falha ao decodificar JSON retornado pelo gslides: {e}"
        ) from e

    return parse_presentation_json(data, presentation_id)


def auto_discover_qa_deck_id() -> str | None:
    """Busca automaticamente o ID do Deck Q&A em variáveis de ambiente, arquivos de configuração ou metadados de workers."""
    # 0. Default configurado
    if DEFAULT_QA_DECK_ID:
        return DEFAULT_QA_DECK_ID

    # 1. Variável de ambiente
    for env_var in ["QA_DECK_ID", "ALL_IN_QA_DECK_ID", "GOOGLE_SLIDES_QA_DECK_ID"]:
        val = os.getenv(env_var)
        if val and len(val.strip()) > 15:
            return val.strip()

    # 2. Arquivos de configuração no repositório ou diretórios conhecidos
    base_dirs = [
        Path(__file__).resolve().parent,
        Path(__file__).resolve().parent.parent.parent,
        Path(r"c:\Users\Vaio\Desktop\Trabalhar DOCS"),
        Path(r"c:\Users\Vaio\Desktop\Trabalhar DOCS\.agents\teamwork\worker_m2"),
        Path(r"c:\Users\Vaio\Desktop\Trabalhar DOCS\.agents\teamwork\sub_orch_m2"),
    ]

    candidate_files = [
        "qa_deck_id.txt",
        "qa_deck.json",
        "deck_config.json",
        "handoff.md",
        "progress.md",
        "context.md",
        "BRIEFING.md",
    ]

    for d in base_dirs:
        for fname in candidate_files:
            p = d / fname
            if p.is_file():
                try:
                    content = p.read_text(encoding="utf-8", errors="replace")
                    # Procura por URLs do Google Slides: docs.google.com/presentation/d/([a-zA-Z0-9_-]+)
                    matches = re.findall(
                        r"presentation/d/([a-zA-Z0-9_-]{25,})", content
                    )
                    for m in matches:
                        if m != DEFAULT_RULES_DECK_ID:
                            return m
                    # Procura por chaves JSON ou referências como "presentation_id": "..."
                    json_matches = re.findall(
                        r'["\'](?:qa_deck_id|presentation_id|deck_id)["\']\s*:\s*["\']([a-zA-Z0-9_-]{25,})["\']',
                        content,
                    )
                    for m in json_matches:
                        if m != DEFAULT_RULES_DECK_ID:
                            return m
                except (OSError, UnicodeDecodeError):
                    continue

    return None


def verify_rules_deck(presentation: PresentationInfo) -> list[CheckResult]:
    """Executa a bateria de auditoria de Regras Didáticas (R1) contra a apresentação."""
    results: list[CheckResult] = []
    all_slide_texts = [s.text_content for s in presentation.slides]
    full_text = "\n".join(all_slide_texts)
    full_text_lower = full_text.lower()

    # 1. Quantidade mínima de slides
    passed = len(presentation.slides) >= 6
    results.append(
        CheckResult(
            check_id="R1_SLIDES_COUNT",
            category="Regras Didáticas (R1)",
            title="Total de slides do deck de regras (mínimo 6)",
            passed=passed,
            details=f"Detectados {len(presentation.slides)} slides no deck de regras.",
            evidence=f"Slide count = {len(presentation.slides)}",
        )
    )

    # 2. Economia Total de R$ 10.000 (R$ 5.000 grupos + R$ 5.000 banco)
    has_10k = bool(re.search(r"10\.000|10000", full_text))
    has_5k_groups = bool(
        re.search(r"5\.000.*(?:grupos|equipes)", full_text_lower)
        or re.search(r"5\s*grupos.*(?:5\.000|1\.000)", full_text_lower)
    )
    has_5k_bank = bool(
        re.search(r"5\.000.*(?:banco|caixa)", full_text_lower)
        or re.search(r"(?:banco|caixa).*(?:5\.000)", full_text_lower)
    )
    passed = has_10k and (has_5k_groups or has_5k_bank)
    results.append(
        CheckResult(
            check_id="R1_TOTAL_ECONOMY",
            category="Regras Didáticas (R1)",
            title="Economia total de R$ 10.000 (R$ 5.000 equipes + R$ 5.000 banco)",
            passed=passed,
            details=f"Termos detectados: 10.000={has_10k}, 5.000 equipes={has_5k_groups}, 5.000 banco={has_5k_bank}.",
            evidence=next(
                (line.strip() for line in full_text.splitlines() if "10.000" in line),
                None,
            ),
        )
    )

    # 3. Saldo inicial de R$ 1.000 por equipe e cédulas (100, 50, 10)
    has_1k = bool(re.search(r"1\.000|1000", full_text))
    has_bills = bool(
        re.search(r"100", full_text)
        and re.search(r"50", full_text)
        and re.search(r"10", full_text)
    )
    passed = has_1k and has_bills
    results.append(
        CheckResult(
            check_id="R1_INITIAL_BALANCE",
            category="Regras Didáticas (R1)",
            title="Saldo inicial de R$ 1.000 por equipe com cédulas de 100, 50 e 10",
            passed=passed,
            details=f"Saldo R$ 1.000 detectado={has_1k}, cédulas de 100, 50 e 10 detectadas={has_bills}.",
            evidence=next(
                (line.strip() for line in full_text.splitlines() if "1.000" in line),
                None,
            ),
        )
    )

    # 4. Integridade da Speaker Note do Slide 2 (R$ 1.000 vs R$ 400 preliminar)
    s2_notes = (
        presentation.slides[1].speaker_notes if len(presentation.slides) > 1 else ""
    )
    has_outdated_400 = "400" in s2_notes and "2x100" in s2_notes
    has_correct_1k_note = "1.000" in s2_notes or "6x100" in s2_notes
    passed = (not has_outdated_400) and (has_correct_1k_note or len(s2_notes) == 0)
    results.append(
        CheckResult(
            check_id="R1_SPEAKER_NOTE_SLIDE_2",
            category="Regras Didáticas (R1)",
            title="Integridade da anotação do orador no Slide 2 (calibrada para R$ 1.000)",
            passed=passed,
            details=f"Nota do Slide 2: menção obsoleta de R$ 400={has_outdated_400}, menção correta de R$ 1.000={has_correct_1k_note}.",
            evidence=s2_notes[:120] + ("..." if len(s2_notes) > 120 else ""),
        )
    )

    # 5. Mecânica em papel/folha de resposta e ausência de placas
    has_paper = bool(re.search(r"papel|folha", full_text_lower))
    has_no_paddles = bool(
        re.search(r"sem\s*(?:o\s*uso\s*de\s*)?placas", full_text_lower)
    )
    passed = has_paper and has_no_paddles
    results.append(
        CheckResult(
            check_id="R1_BETTING_MECHANIC_NO_PADDLES",
            category="Regras Didáticas (R1)",
            title="Mecânica de aposta e resposta em papel/folhas (sem uso de placas)",
            passed=passed,
            details=f"Menção a papel/folha={has_paper}, menção explícita 'sem placas'={has_no_paddles}.",
            evidence=next(
                (
                    line.strip()
                    for line in full_text.splitlines()
                    if "placas" in line.lower() or "papel" in line.lower()
                ),
                None,
            ),
        )
    )

    # 6. Limite de aposta: teto estrito de R$ 200 e aposta mínima de R$ 10
    has_cap_200 = bool(
        re.search(r"200", full_text)
        and re.search(r"teto|m[aá]x|limite", full_text_lower)
    )
    has_min_10 = bool(
        re.search(r"10", full_text) and re.search(r"m[ií]n", full_text_lower)
    )
    passed = has_cap_200 and has_min_10
    results.append(
        CheckResult(
            check_id="R1_BET_LIMITS",
            category="Regras Didáticas (R1)",
            title="Teto estrito de R$ 200 por pergunta e aposta mínima de R$ 10",
            passed=passed,
            details=f"Teto R$ 200 detectado={has_cap_200}, mínimo R$ 10 detectado={has_min_10}.",
            evidence=next(
                (
                    line.strip()
                    for line in full_text.splitlines()
                    if "200" in line
                    and (
                        "teto" in line.lower()
                        or "máx" in line.lower()
                        or "max" in line.lower()
                    )
                ),
                None,
            ),
        )
    )

    # 7. Regras de bonificação: x2 para 1-4 acertos (+100% de lucro líquido)
    has_mult_2x = bool(re.search(r"[×x]2|dobro|100%", full_text_lower))
    has_1_to_4 = bool(re.search(r"1\s*(?:a|ou|e)\s*4", full_text_lower))
    passed = has_mult_2x and has_1_to_4
    results.append(
        CheckResult(
            check_id="R1_BONUS_MULTIPLIER_2X",
            category="Regras Didáticas (R1)",
            title="Multiplicador ×2 (+100% lucro líquido) para 1 a 4 grupos corretos",
            passed=passed,
            details=f"Multiplicador 2x/dobro detectado={has_mult_2x}, faixa 1 a 4 acertos detectada={has_1_to_4}.",
            evidence=next(
                (
                    line.strip()
                    for line in full_text.splitlines()
                    if "dobro" in line.lower() or "×2" in line or "x2" in line.lower()
                ),
                None,
            ),
        )
    )

    # 8. Bônus Unânime Fixo de +R$ 100 para todos os 5 grupos corretos
    has_unanimous_bonus = bool(
        re.search(r"un[aâ]nime", full_text_lower) and re.search(r"100", full_text)
    )
    has_all_5 = bool(re.search(r"5\s*(?:grupos|equipes)|todos", full_text_lower))
    passed = has_unanimous_bonus and has_all_5
    results.append(
        CheckResult(
            check_id="R1_UNANIMOUS_BONUS",
            category="Regras Didáticas (R1)",
            title="Bônus Unânime Fixo de +R$ 100 para todos os 5 grupos corretos",
            passed=passed,
            details=f"Bônus unânime +R$ 100 detectado={has_unanimous_bonus}, referência a todos os 5 grupos={has_all_5}.",
            evidence=next(
                (
                    line.strip()
                    for line in full_text.splitlines()
                    if "unânime" in line.lower() or "unanime" in line.lower()
                ),
                None,
            ),
        )
    )

    # 9. Penalidade de erro: grupos que erram perdem aposta para a banca
    has_error_loss = bool(
        re.search(r"errar.*(?:perde|banco|caixa)", full_text_lower)
        or re.search(r"perde.*(?:aposta|banco|caixa)", full_text_lower)
    )
    passed = has_error_loss
    results.append(
        CheckResult(
            check_id="R1_LOSER_PENALTY",
            category="Regras Didáticas (R1)",
            title="Penalidade de erro: grupos perdem valor apostado para o Banco da Casa",
            passed=passed,
            details=f"Regra de perda de aposta em caso de erro detectada={has_error_loss}.",
            evidence=next(
                (
                    line.strip()
                    for line in full_text.splitlines()
                    if "errar" in line.lower() and "perde" in line.lower()
                ),
                None,
            ),
        )
    )

    # 10. Desafio da Mesa pós-rodada 5: gatilho de empate técnico (<= R$ 100 do 1º colocado)
    has_technical_tie = bool(re.search(r"empate\s+t[eé]cnico", full_text_lower))
    has_tie_threshold = bool(
        re.search(r"(?:<=|≤|\bate\b|\baté\b)\s*R?\$?\s*100", full_text, re.IGNORECASE)
        or re.search(r"dist[aâ]ncia.*100", full_text_lower)
    )
    passed = has_technical_tie and has_tie_threshold
    results.append(
        CheckResult(
            check_id="R1_DESAFIO_MESA_GATILHO",
            category="Regras Didáticas (R1)",
            title="Desafio da Mesa: gatilho de empate técnico (distância ≤ R$ 100 do 1º colocado)",
            passed=passed,
            details=f"Termo 'empate técnico'={has_technical_tie}, margem de corte ≤ R$ 100={has_tie_threshold}.",
            evidence=next(
                (
                    line.strip()
                    for line in full_text.splitlines()
                    if "empate técnico" in line.lower()
                    or "empate tecnico" in line.lower()
                ),
                None,
            ),
        )
    )

    # 11. Desafio da Mesa: mecânica Winner Takes All (100% dos saldos no pote central)
    has_wta = bool(re.search(r"winner\s+takes\s+all|leva\s+tudo", full_text_lower))
    has_100pct_pot = bool(
        re.search(r"100%|pote\s*(?:[uú]nico|gigante|central)", full_text_lower)
    )
    passed = has_wta and has_100pct_pot
    results.append(
        CheckResult(
            check_id="R1_DESAFIO_MESA_WTA",
            category="Regras Didáticas (R1)",
            title="Desafio da Mesa: pote unificado e mecânica Winner Takes All (leva tudo)",
            passed=passed,
            details=f"Winner Takes All / leva tudo={has_wta}, 100% dos saldos no pote={has_100pct_pot}.",
            evidence=next(
                (
                    line.strip()
                    for line in full_text.splitlines()
                    if "winner takes all" in line.lower() or "leva tudo" in line.lower()
                ),
                None,
            ),
        )
    )

    return results


def verify_qa_deck(presentation: PresentationInfo) -> list[CheckResult]:
    """Executa a bateria de auditoria da Apresentação Sequencial de Perguntas e Respostas (R2)."""
    results: list[CheckResult] = []
    slides = presentation.slides
    num_slides = len(slides)

    # 1. Total exato de 41 slides
    passed = num_slides == 41
    results.append(
        CheckResult(
            check_id="R2_TOTAL_SLIDES_COUNT",
            category="Sequência Q&A (R2)",
            title="Contagem total exata de 41 slides (1 capa + 20 pares Q&A)",
            passed=passed,
            details=f"Total de slides detectados: {num_slides} (esperado: exatamente 41).",
            evidence=f"Slide count = {num_slides}",
        )
    )

    # 2. Slide 1 é Capa
    cover_text = slides[0].text_content.lower() if num_slides > 0 else ""
    is_cover = bool(
        "all-in" in cover_text
        or "perguntas" in cover_text
        or "cards" in cover_text
        or "capa" in cover_text
    )
    results.append(
        CheckResult(
            check_id="R2_COVER_SLIDE",
            category="Sequência Q&A (R2)",
            title="Slide 1 é Capa da Apresentação de Perguntas e Respostas",
            passed=is_cover,
            details=f"Texto do Slide 1 avaliado como capa: {is_cover}.",
            evidence=slides[0].text_content[:100] if num_slides > 0 else None,
        )
    )

    # 3. Paridade estrita intercalada: para i em 1..20, slide 2i é Pergunta e slide 2i+1 é Resposta
    parity_errors: list[str] = []
    detected_pairs: list[tuple[int, str, str]] = []

    for i in range(1, 21):
        q_idx = 2 * i - 1  # 0-indexed para slide 2i
        a_idx = 2 * i  # 0-indexed para slide 2i+1

        if q_idx >= num_slides:
            parity_errors.append(
                f"Par {i}: Slide de pergunta {2 * i} não existe (deck possui apenas {num_slides} slides)."
            )
            continue
        if a_idx >= num_slides:
            parity_errors.append(
                f"Par {i}: Slide de resposta {2 * i + 1} não existe (deck possui apenas {num_slides} slides)."
            )
            continue

        q_slide = slides[q_idx]
        a_slide = slides[a_idx]
        q_text = q_slide.text_content
        a_text = a_slide.text_content

        # Verifica se o slide 2i possui características de pergunta
        is_question = bool(
            re.search(
                r"pergunta|lote\s*\d+|quest[aã]o|n[ií]vel\s*[12]", q_text, re.IGNORECASE
            )
            and (
                "a)" in q_text.lower()
                or "b)" in q_text.lower()
                or "[a]" in q_text.lower()
                or "[b]" in q_text.lower()
                or "opção a" in q_text.lower()
                or "opcao a" in q_text.lower()
            )
        )

        # Verifica se o slide 2i+1 possui características de resposta
        is_answer = bool(
            re.search(
                r"gabarito|resposta|resolu[cç][aã]o|justificativa",
                a_text,
                re.IGNORECASE,
            )
            and re.search(
                r"\b[AB]\b|gabarito\s*:\s*[AB]|alternativa\s*[AB]",
                a_text,
                re.IGNORECASE,
            )
        )

        if not is_question:
            parity_errors.append(
                f"Par {i} (Slide {2 * i}): Não foi identificado como card de Pergunta."
            )
        if not is_answer:
            parity_errors.append(
                f"Par {i} (Slide {2 * i + 1}): Não foi identificado como card de Resposta/Gabarito."
            )

        # Extrai Lote ou ID para checar correspondência de paridade
        lote_q = re.search(r"lote\s*0?(\d+)", q_text, re.IGNORECASE)
        lote_a = re.search(r"lote\s*0?(\d+)", a_text, re.IGNORECASE)
        if lote_q and lote_a:
            num_q = int(lote_q.group(1))
            num_a = int(lote_a.group(1))
            if num_q != num_a:
                parity_errors.append(
                    f"Par {i}: Divergência de lote entre pergunta (Lote {num_q}) e resposta (Lote {num_a})."
                )
            detected_pairs.append((i, f"Lote {num_q}", f"Lote {num_a}"))
        else:
            detected_pairs.append((i, "Questão detectada", "Resposta detectada"))

    passed_parity = len(parity_errors) == 0 and len(detected_pairs) == 20
    results.append(
        CheckResult(
            check_id="R2_INTERLEAVED_PARITY",
            category="Sequência Q&A (R2)",
            title="Paridade intercalada estrita: Slide 2i = Pergunta i, Slide 2i+1 = Resposta i (i=1..20)",
            passed=passed_parity,
            details="Todos os 20 pares de pergunta e resposta intercalados com sucesso."
            if passed_parity
            else f"Erros de paridade: {'; '.join(parity_errors[:3])}",
            evidence=f"Pares validados: {len(detected_pairs)}/20",
        )
    )

    # 4. Escopo fechado: Todas as 13 questões de Nível 1 presentes
    all_content_and_notes = "\n".join(
        [f"{s.text_content} {s.speaker_notes}" for s in slides]
    )

    missing_n1: list[str] = []
    for qid in EXPECTED_NIVEL_1_IDS:
        if qid not in all_content_and_notes:
            missing_n1.append(qid)

    passed_n1 = len(missing_n1) == 0
    results.append(
        CheckResult(
            check_id="R2_SCOPE_NIVEL_1",
            category="Sequência Q&A (R2)",
            title="Presença integral das 13 questões oficiais de Nível 1 (Aquecimento)",
            passed=passed_n1,
            details="Todas as 13 questões de Nível 1 foram encontradas no deck."
            if passed_n1
            else f"Questões ausentes de Nível 1: {', '.join(missing_n1)}",
            evidence=f"Presentes: {13 - len(missing_n1)}/13",
        )
    )

    # 5. Escopo fechado: Todas as 7 questões de Nível 2 presentes
    missing_n2: list[str] = []
    for qid in EXPECTED_NIVEL_2_IDS:
        if qid not in all_content_and_notes:
            missing_n2.append(qid)

    passed_n2 = len(missing_n2) == 0
    results.append(
        CheckResult(
            check_id="R2_SCOPE_NIVEL_2",
            category="Sequência Q&A (R2)",
            title="Presença integral das 7 questões oficiais de Nível 2 (Finais)",
            passed=passed_n2,
            details="Todas as 7 questões de Nível 2 foram encontradas no deck."
            if passed_n2
            else f"Questões ausentes de Nível 2: {', '.join(missing_n2)}",
            evidence=f"Presentes: {7 - len(missing_n2)}/7",
        )
    )

    # 6. Exclusão categórica de Nível 3 (Nenhum dos 5 IDs proibidos)
    found_forbidden_ids: list[str] = []
    for qid in FORBIDDEN_NIVEL_3_IDS:
        if qid in all_content_and_notes:
            found_forbidden_ids.append(qid)

    passed_no_n3_ids = len(found_forbidden_ids) == 0
    results.append(
        CheckResult(
            check_id="R2_EXCLUSION_N3_IDS",
            category="Sequência Q&A (R2)",
            title="Exclusão categórica dos IDs de Nível 3 (Morte Súbita)",
            passed=passed_no_n3_ids,
            details="Nenhum ID de Nível 3 foi detectado no deck."
            if passed_no_n3_ids
            else f"IDs proibidos detectados: {', '.join(found_forbidden_ids)}",
            evidence="0 IDs de Nível 3 detectados"
            if passed_no_n3_ids
            else f"Detectado: {found_forbidden_ids}",
        )
    )

    # 7. Exclusão categórica de marcadores e menções a "Nível 3" / "🔥 [APOSTA NO TEMA"
    found_forbidden_patterns: list[str] = []
    for pat in FORBIDDEN_N3_PATTERNS:
        match = re.search(pat, all_content_and_notes, re.IGNORECASE)
        if match:
            found_forbidden_patterns.append(match.group(0))

    passed_no_n3_patterns = len(found_forbidden_patterns) == 0
    results.append(
        CheckResult(
            check_id="R2_EXCLUSION_N3_PATTERNS",
            category="Sequência Q&A (R2)",
            title="Ausência total de marcadores de Nível 3 ('Nível 3', '🔥 [APOSTA NO TEMA', etc.)",
            passed=passed_no_n3_patterns,
            details="Nenhum marcador de Nível 3 detectado nos textos ou notas dos 41 slides."
            if passed_no_n3_patterns
            else f"Marcadores detectados: {', '.join(found_forbidden_patterns)}",
            evidence="0 marcadores detectados"
            if passed_no_n3_patterns
            else f"Detectado: {found_forbidden_patterns}",
        )
    )

    return results


def run_full_audit(
    rules_deck_id: str | None = None,
    qa_deck_id: str | None = None,
    rules_only: bool = False,
    qa_only: bool = False,
    mock_rules_data: dict[str, Any] | None = None,
    mock_qa_data: dict[str, Any] | None = None,
    verbose: bool = False,
) -> AuditReport:
    """Executa a auditoria completa conforme os parâmetros fornecidos."""
    report = AuditReport(rules_deck_id=rules_deck_id, qa_deck_id=qa_deck_id)

    # Auditoria de Regras (R1)
    if not qa_only:
        r_id = rules_deck_id or DEFAULT_RULES_DECK_ID
        report.rules_deck_id = r_id
        if verbose:
            print(
                f"\n[AUDITORIA] Inspecionando Deck de Regras Didáticas (ID: {r_id})..."
            )
        try:
            if mock_rules_data:
                rules_pres = parse_presentation_json(mock_rules_data, r_id)
            else:
                rules_pres = fetch_presentation_from_cli(r_id)
            rules_results = verify_rules_deck(rules_pres)
            report.results.extend(rules_results)
        except (
            RuntimeError,
            ValueError,
            OSError,
            json.JSONDecodeError,
            subprocess.SubprocessError,
        ) as e:
            report.results.append(
                CheckResult(
                    check_id="R1_INSPECTION_ERROR",
                    category="Regras Didáticas (R1)",
                    title="Acesso e leitura da apresentação de regras",
                    passed=False,
                    details=f"Erro ao inspecionar deck de regras: {e}",
                )
            )

    # Auditoria de Perguntas e Respostas (R2)
    if not rules_only:
        q_id = qa_deck_id or auto_discover_qa_deck_id()
        report.qa_deck_id = q_id
        if verbose:
            print(
                f"\n[AUDITORIA] Inspecionando Deck Sequencial Q&A Níveis 1 e 2 (ID: {q_id})..."
            )

        if not q_id and not mock_qa_data:
            report.results.append(
                CheckResult(
                    check_id="R2_QA_DECK_NOT_PROVIDED",
                    category="Sequência Q&A (R2)",
                    title="Fornecimento do ID da Apresentação Q&A",
                    passed=False,
                    details="O ID da apresentação Q&A não foi especificado via --qa-deck e não foi encontrado automaticamente nos arquivos de metadados.",
                )
            )
        else:
            try:
                target_id = q_id or "MOCK_QA_DECK"
                if mock_qa_data:
                    qa_pres = parse_presentation_json(mock_qa_data, target_id)
                else:
                    qa_pres = fetch_presentation_from_cli(target_id)
                qa_results = verify_qa_deck(qa_pres)
                report.results.extend(qa_results)
            except (
                RuntimeError,
                ValueError,
                OSError,
                json.JSONDecodeError,
                subprocess.SubprocessError,
            ) as e:
                report.results.append(
                    CheckResult(
                        check_id="R2_INSPECTION_ERROR",
                        category="Sequência Q&A (R2)",
                        title="Acesso e leitura da apresentação Q&A",
                        passed=False,
                        details=f"Erro ao inspecionar deck Q&A: {e}",
                    )
                )

    return report


def print_audit_report(report: AuditReport, verbose: bool = False) -> None:
    """Imprime relatório formatado e colorido no terminal."""
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, io.UnsupportedOperation, OSError):
        pass

    print("=" * 78)
    print(
        "     ALL-IN QUIMICO -- AUDITORIA PROGRAMATICA DE APRESENTACOES GOOGLE SLIDES"
    )
    print("=" * 78)

    if report.rules_deck_id:
        print(f"Deck de Regras: {report.rules_deck_id}")
    if report.qa_deck_id:
        print(f"Deck Q&A N1/N2: {report.qa_deck_id}")
    print("-" * 78)

    current_cat = ""
    for r in report.results:
        if r.category != current_cat:
            current_cat = r.category
            print(f"\n>> {current_cat}:")

        tag = "[PASS]" if r.passed else "[FAIL]"
        print(f"  {tag:<7} {r.check_id:<30} {r.title}")
        if verbose or not r.passed:
            print(f"          Detalhes: {r.details}")
            if r.evidence:
                print(f"          Evidencia: {r.evidence}")

    print("\n" + "=" * 78)
    print(
        f"RESUMO: {report.passed_checks}/{report.total_checks} verificacoes aprovadas. "
        f"Falhas: {report.failed_checks}"
    )
    print("=" * 78)

    if report.success:
        print(">>> STATUS GERAL: APROVADO COM SUCESSO (Exit Code 0) <<<")
    else:
        print(">>> STATUS GERAL: FALHA DETECTADA (Exit Code 1) <<<")


def main() -> None:
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, io.UnsupportedOperation, OSError):
        pass

    parser = argparse.ArgumentParser(
        description="Auditor Programático de Apresentações Google Slides — All-In Químico"
    )
    parser.add_argument(
        "--rules-deck",
        type=str,
        default=DEFAULT_RULES_DECK_ID,
        help=f"ID da apresentação de regras (default: {DEFAULT_RULES_DECK_ID})",
    )
    parser.add_argument(
        "--qa-deck",
        type=str,
        default=None,
        help="ID da apresentação sequencial de Perguntas e Respostas N1/N2 (auto-descoberto se omitido)",
    )
    parser.add_argument(
        "--rules-only",
        action="store_true",
        help="Executa apenas a auditoria do deck de regras (R1)",
    )
    parser.add_argument(
        "--qa-only",
        action="store_true",
        help="Executa apenas a auditoria do deck de perguntas e respostas (R2)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Exibe resultado em formato JSON estruturado",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Exibe detalhes e evidências completas de cada verificação",
    )
    args = parser.parse_args()

    report = run_full_audit(
        rules_deck_id=args.rules_deck,
        qa_deck_id=args.qa_deck,
        rules_only=args.rules_only,
        qa_only=args.qa_only,
        verbose=args.verbose,
    )

    if args.json:
        payload = {
            "success": report.success,
            "total_checks": report.total_checks,
            "passed_checks": report.passed_checks,
            "failed_checks": report.failed_checks,
            "rules_deck_id": report.rules_deck_id,
            "qa_deck_id": report.qa_deck_id,
            "results": [
                {
                    "check_id": r.check_id,
                    "category": r.category,
                    "title": r.title,
                    "passed": r.passed,
                    "details": r.details,
                    "evidence": r.evidence,
                }
                for r in report.results
            ],
        }
        print(json.dumps(payload, indent=2, ensure_ascii=True))
    else:
        print_audit_report(report, verbose=args.verbose)

    sys.exit(0 if report.success else 1)


if __name__ == "__main__":
    main()
