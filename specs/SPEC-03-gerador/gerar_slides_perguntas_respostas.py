"""
Gerador Automatizado de Slides de Perguntas e Respostas — All-In Químico
======================================================================
Compila os cards didáticos das questões oficiais de Química em apresentações
independentes do Google Slides com arquitetura Multi-Deck, auto-scaling
tipográfico anti-overflow e formatação química aderente à norma IUPAC.

Decks Suportados (Total 25 Questões, 10 Decks, 60 Slides):
  1. Apresentação de Teste Exclusiva (R2): exatamente 3 N1 (7 slides)
  2. Apresentações Individuais de Desafio N3 (R3): 5 decks de 1 N3 (3 slides cada = 15 slides)
  3. Apresentações Regulares de 5 Questões (R4): 3 decks de 5 Q&A (11 slides cada = 33 slides)
  4. Deck Suplente / Desempate Técnico (SPEC-02 §4.4): 2 N2 (5 slides)

Design System: Itaú Private / Fintech Clean / CrewDeck Anti-Vibe
- Fundo Off-White (#F8F9FA) de alta acessibilidade visual (WCAG AAA)
- Superfícies/Cards #FFFFFF com contorno 1px #E2E8F0
- Tipografia humanista Open Sans sem serifa
- Dynamic Typography Auto-scaling Anti-Overflow (compute_typography_params)
- Notação química IUPAC para massas molares parentéticas M(X)

Uso:
  python gerar_slides_perguntas_respostas.py [--batch-only] [--execute] [--deck <ID>]
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, NamedTuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import yaml

# Diretórios base
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
QUESTIONS_DIR = PROJECT_ROOT / "specs" / "SPEC-01-questoes" / "questions"
BATCH_FILES_DIR = SCRIPT_DIR / "batch_files"
MANIFEST_PATH = SCRIPT_DIR / "decks_manifest.json"
DEFAULT_OUTPUT_JSON = SCRIPT_DIR / "batch_questoes_n1_n2.json"

# =============================================================================
# DESIGN SYSTEM: FINTECH CLEAN / ITAÚ PRIVATE / CREWDECK A11Y
# =============================================================================
BG_MAIN = "#F8F9FA"        # Off-white quente e limpo (conforto visual em projetores)
BG_CARD = "#FFFFFF"        # Superfície branca pura elevada
BG_CARD_SUBTLE = "#F1F5F9" # Slate 100 sutil para metadados e opções neutras
BORDER_SUBTLE = "#E2E8F0"  # Borda de 1px suave
TEXT_PRIMARY = "#0F172A"   # Slate 900 (legibilidade máxima WCAG AAA)
TEXT_SECONDARY = "#475569" # Slate 600
TEXT_MUTED = "#64748B"     # Slate 500
FONT_FAMILY = "Open Sans"  # Tipografia humanista com alta abertura de olho

# Psicologia das Cores — Dificuldades e Semântica Pedagógica
COLOR_N1 = "#0284C7"       # Azul Cobalto / Petróleo (Nível 1 - Aquecimento)
COLOR_N1_BG = "#E0F2FE"    # Fundo azul suave
COLOR_N2 = "#D97706"       # Âmbar / Laranja Queimado Institucional (Nível 2 - Finais)
COLOR_N2_BG = "#FEF3C7"    # Fundo âmbar suave
COLOR_N3 = "#7C3AED"       # Roxo Ametista (Nível 3 - Morte Súbita)
COLOR_N3_BG = "#F3E8FF"    # Fundo roxo suave
COLOR_N3_TEXT = "#581C87"  # Roxo escuro para contraste no badge

COLOR_GREEN = "#16A34A"    # Verde Fintech Esmeralda (Gabarito / Lucro)
COLOR_GREEN_BG = "#DCFCE7" # Fundo verde suave
COLOR_GREEN_BORDER = "#BBF7D0"
COLOR_GREEN_TEXT = "#14532D"

COLOR_RED = "#DC2626"      # Vermelho Terracota (Distrator / Caixa)
COLOR_RED_BG = "#FEE2E2"    # Fundo vermelho suave

# Mapeamento de domínios químicos para nomes pedagógicos e cores semânticas (Duplo Destaque)
DOMAIN_NAMES = {
    "CHEM-ATO": "Estrutura Atômica & Tabela Periódica",
    "CHEM-ENV": "Química Ambiental & Sustentabilidade",
    "CHEM-SOL": "Soluções & Concentrações Químicas",
    "CHEM-STO": "Estequiometria & Quantidade de Matéria",
}

DOMAIN_STYLES = {
    "CHEM-SOL": ("#0284C7", "#E0F2FE"),  # Azul Soluções
    "CHEM-STO": ("#4F46E5", "#E0E7FF"),  # Índigo/Roxo Estequiometria
    "CHEM-ENV": ("#059669", "#D1FAE5"),  # Verde Botânico Química Ambiental
    "CHEM-ATO": ("#0D9488", "#CCFBF1"),  # Petróleo/Teal Estrutura Atômica
}

# Mapeamento de níveis cognitivos
COGNITIVE_LABELS = {
    "recognition": "Reconhecimento",
    "understanding": "Compreensão",
    "application": "Aplicação",
    "analysis": "Análise",
}

# Dicionários de subscrito e sobrescrito Unicode para renderização química
SUBSCRIPTS = {
    "0": "₀", "1": "₁", "2": "₂", "3": "₃", "4": "₄",
    "5": "₅", "6": "₆", "7": "₇", "8": "₈", "9": "₉",
    "+": "₊", "-": "₋", "=": "₌", "(": "₍", ")": "₎",
    "a": "ₐ", "e": "ₑ", "o": "ₒ", "x": "ₓ", "i": "ᵢ",
}

SUPERSCRIPTS = {
    "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴",
    "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹",
    "+": "⁺", "-": "⁻", "=": "⁼", "(": "⁽", ")": "⁾",
    "n": "ⁿ",
}

COMMON_FORMULA_REPLACEMENTS = [
    (r"(?<![A-Za-z0-9])H2O(?![A-Za-z0-9])", "H₂O"),
    (r"(?<![A-Za-z0-9])SO3(?![A-Za-z0-9])", "SO₃"),
    (r"(?<![A-Za-z0-9])SO2(?![A-Za-z0-9])", "SO₂"),
    (r"(?<![A-Za-z0-9])CO2(?![A-Za-z0-9])", "CO₂"),
    (r"(?<![A-Za-z0-9])H2(?![A-Za-z0-9])", "H₂"),
    (r"(?<![A-Za-z0-9])O2(?![A-Za-z0-9])", "O₂"),
    (r"(?<![A-Za-z0-9])V2(?![A-Za-z0-9])", "V₂"),
    (r"(?<![A-Za-z0-9])V1(?![A-Za-z0-9])", "V₁"),
    (r"(?<![A-Za-z0-9])c1(?![A-Za-z0-9])", "c₁"),
    (r"(?<![A-Za-z0-9])c2(?![A-Za-z0-9])", "c₂"),
]


class TypographyParams(NamedTuple):
    stmt_font_size: float
    stmt_line_spacing: int
    opt_font_size: float
    opt_line_spacing: int
    ans2_font_size: float
    ans2_line_spacing: int


def compute_typography_params(
    statement: str | int,
    options: list[dict[str, Any]] | int | str,
    answer_data: dict[str, Any] | int | str,
) -> TypographyParams:
    """
    Computa dinamicamente tamanhos de fonte e line spacing em pontos
    para eliminar qualquer risco de overflow nos cards Fintech Clean.
    Conforme especificado em relatorio_auditoria_questoes.md §4.

    Retorna TypographyParams (NamedTuple):
        (stmt_font_size, stmt_line_spacing,
         opt_font_size, opt_line_spacing,
         ans2_font_size, ans2_line_spacing)
    """
    # 1. Enunciado da Questão (Card Esquerdo: w=296, h=196 pt)
    if isinstance(statement, int):
        stmt_len = statement
    else:
        stmt_len = len(str(statement or "").strip())

    if stmt_len > 240:
        stmt_font_size = 10.5
        stmt_line_spacing = 125
    elif stmt_len > 180:
        stmt_font_size = 11.0
        stmt_line_spacing = 130
    else:
        stmt_font_size = 12.0
        stmt_line_spacing = 135

    # 2. Alternativas A e B (Cards Direitos: w=288, h=68 pt)
    if isinstance(options, int):
        max_opt_len = options
    elif isinstance(options, (list, tuple)):
        max_opt_len = 0
        for opt in options:
            if isinstance(opt, dict):
                opt_text = clean_chemical_typography(opt.get("text", ""))
                max_opt_len = max(max_opt_len, len(opt_text))
            else:
                max_opt_len = max(max_opt_len, len(str(opt or "").strip()))
    else:
        max_opt_len = len(str(options or "").strip())

    if max_opt_len > 110:
        opt_font_size = 9.8
        opt_line_spacing = 120
    elif max_opt_len > 80:
        opt_font_size = 10.5
        opt_line_spacing = 125
    else:
        opt_font_size = 11.5
        opt_line_spacing = 130

    # 3. Justificativa Científica + Distrator (Gabarito Direito: w=288, h=196 pt)
    if isinstance(answer_data, int):
        col2_len = answer_data
    elif isinstance(answer_data, dict):
        justif = clean_chemical_typography(answer_data.get("scientific_justification", ""))
        rationale = clean_chemical_typography(
            answer_data.get("distractor_rationale", "")
            or answer_data.get("rationale", "")
            or answer_data.get("wrong_rationale", "")
        )
        wrong_key = answer_data.get("wrong_key", "B")
        col2_text = (
            f"✦ FUNDAMENTO FÍSICO-QUÍMICO:\n{justif}\n\n"
            f"✦ POR QUE A ALTERNATIVA {wrong_key} É UM ERRO TÍPICO?\n{rationale}"
        )
        col2_len = len(col2_text)
    else:
        col2_len = len(str(answer_data or "").strip())

    if col2_len > 260:
        ans2_font_size = 9.5
        ans2_line_spacing = 120
    elif col2_len > 200:
        ans2_font_size = 10.0
        ans2_line_spacing = 125
    else:
        ans2_font_size = 10.5
        ans2_line_spacing = 130

    return TypographyParams(
        stmt_font_size=stmt_font_size,
        stmt_line_spacing=stmt_line_spacing,
        opt_font_size=opt_font_size,
        opt_line_spacing=opt_line_spacing,
        ans2_font_size=ans2_font_size,
        ans2_line_spacing=ans2_line_spacing,
    )


def clean_chemical_typography(text: Any) -> str:
    """
    Converte tags HTML e fórmulas em caracteres Unicode limpos e elegantes,
    aderente à norma IUPAC para massas molares M(X) e subscritos químicos.
    """
    if text is None:
        return ""
    s = str(text).strip()

    # Pre-processa subscritos numéricos internos para lidar com tags aninhadas como M<sub>H<sub>2</sub>O</sub>
    s = re.sub(r"<sub>(\d+)</sub>", lambda m: "".join(SUBSCRIPTS.get(c, c) for c in m.group(1)), s, flags=re.IGNORECASE)

    # 1. Normalização IUPAC para massas molares com subscritos maiúsculos: M<sub>Na</sub> -> M(Na)
    # e massas de amostra com subscritos minúsculos: m<sub>Na</sub> -> m(Na) sem colisão de caso
    def _sub_molar_mass(m: re.Match) -> str:
        inner = m.group(1)
        inner_sub = "".join(SUBSCRIPTS.get(c, c) if c.isdigit() else c for c in inner)
        return f"M({inner_sub})"

    def _sub_sample_mass(m: re.Match) -> str:
        inner = m.group(1)
        inner_sub = "".join(SUBSCRIPTS.get(c, c) if c.isdigit() else c for c in inner)
        return f"m({inner_sub})"

    s = re.sub(r"M(?:<sub>|<SUB>)([^<]+)(?:</sub>|</SUB>)", _sub_molar_mass, s)
    s = re.sub(r"m(?:<sub>|<SUB>)([^<]+)(?:</sub>|</SUB>)", _sub_sample_mass, s)

    # 2. Converte tags <sub> numéricas e permitidas restantes
    def _sub(m: re.Match) -> str:
        return "".join(SUBSCRIPTS.get(c, c) for c in m.group(1))

    s = re.sub(r"<sub>(.*?)</sub>", _sub, s, flags=re.IGNORECASE)

    # 3. Converte tags <sup> sobrescritas
    def _sup(m: re.Match) -> str:
        return "".join(SUPERSCRIPTS.get(c, c) for c in m.group(1))

    s = re.sub(r"<sup>(.*?)</sup>", _sup, s, flags=re.IGNORECASE)

    # 4. Normalização de fórmulas comuns sem tags em resoluções e enunciados
    for pattern, replacement in COMMON_FORMULA_REPLACEMENTS:
        s = re.sub(pattern, replacement, s)

    # 5. Símbolos e conectores de reação
    s = s.replace("<->", "⇄").replace("->", "→")
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()


# =============================================================================
# MODELO DE CONFIGURAÇÃO DE DECKS E CARGA DO BANCO
# =============================================================================
@dataclass
class DeckConfig:
    deck_id: str
    deck_type: str  # "test" | "regular" | "challenge" | "tiebreaker"
    title: str
    subtitle: str
    question_ids: list[str]
    batch_filename: str
    presentation_id: str | None = None


# Matriz canônica de partição de todos os 10 decks (25 questões, 60 slides)
DECK_CONFIGS: list[DeckConfig] = [
    # 1. Apresentação de Teste Exclusiva (R2) — 7 slides
    DeckConfig(
        deck_id="deck_teste_nivel_1",
        deck_type="test",
        title="All-In Químico — Rodada de Aquecimento e Teste (Nível 1)",
        subtitle="Calibração Pedagógica Sem Risco Financeiro • 3 Questões Didáticas Iniciais",
        question_ids=["Q-ATO-001", "Q-SOL-001", "Q-STO-001"],
        batch_filename="batch_deck_teste_nivel_1.json",
        presentation_id="15Ydyk8N1awGpVvBESo-e0ZwBj3BLt81vlIL6wRJm-Eg",
    ),
    # 2. Apresentações Individuais de Desafio N3 (R3) — 3 slides cada
    DeckConfig(
        deck_id="desafio_01_morte_subita_diluicao",
        deck_type="challenge",
        title="All-In Químico — Desafio Final: Morte Súbita [Q-SOL-005]",
        subtitle="Tema: DILUIÇÃO • Aposta no Escuro • Winner Takes All",
        question_ids=["Q-SOL-005"],
        batch_filename="batch_desafio_01_morte_subita_diluicao.json",
        presentation_id="1wUKcIy3knGukQzh1xYboc8XZ0WunVxa5LtLi_UMqlYM",
    ),
    DeckConfig(
        deck_id="desafio_02_morte_subita_molaridade_sal",
        deck_type="challenge",
        title="All-In Químico — Desafio Final: Morte Súbita [Q-SOL-007]",
        subtitle="Tema: MOLARIDADE A PARTIR DA MASSA • Aposta no Escuro • Winner Takes All",
        question_ids=["Q-SOL-007"],
        batch_filename="batch_desafio_02_morte_subita_molaridade_sal.json",
        presentation_id="1nE5alcVwy5AKfgfBWZi27lnlIBH7VTdtCO7ZHxAMOMk",
    ),
    DeckConfig(
        deck_id="desafio_03_morte_subita_soda_caustica",
        deck_type="challenge",
        title="All-In Químico — Desafio Final: Morte Súbita [Q-SOL-008]",
        subtitle="Tema: SODA CÁUSTICA EM SOLUÇÃO • Aposta no Escuro • Winner Takes All",
        question_ids=["Q-SOL-008"],
        batch_filename="batch_desafio_03_morte_subita_soda_caustica.json",
        presentation_id="1kb50y0R9C_tSUYsxmmxdtrNVnygDVfOYH4nw1WXogms",
    ),
    DeckConfig(
        deck_id="desafio_04_morte_subita_estequiometria_agua",
        deck_type="challenge",
        title="All-In Químico — Desafio Final: Morte Súbita [Q-STO-008]",
        subtitle="Tema: LIMITANTE + RENDIMENTO • Aposta no Escuro • Winner Takes All",
        question_ids=["Q-STO-008"],
        batch_filename="batch_desafio_04_morte_subita_estequiometria_agua.json",
        presentation_id="1fnETGpSU4DghG_CTutZTSbwdXHeBa1qNh3vxH4gvMoE",
    ),
    DeckConfig(
        deck_id="desafio_05_morte_subita_chuva_acida",
        deck_type="challenge",
        title="All-In Químico — Desafio Final: Morte Súbita [Q-ENV-006]",
        subtitle="Tema: GEOQUÍMICA DA CHUVA ÁCIDA • Aposta no Escuro • Winner Takes All",
        question_ids=["Q-ENV-006"],
        batch_filename="batch_desafio_05_morte_subita_chuva_acida.json",
        presentation_id="1WALnYCMcEeWFyFXV1UMSCwHGt4NWBynNp3h9YPTU4uI",
    ),
    # 3. Apresentações Regulares de 5 Questões (R4) — 11 slides cada
    DeckConfig(
        deck_id="deck_regular_01",
        deck_type="regular",
        title="All-In Químico — Perguntas e Respostas — Deck Regular 01",
        subtitle="Fase 1: Aquecimento Geral • Lotes 001 a 005 (10 Slides Didáticos)",
        question_ids=["Q-ATO-002", "Q-SOL-006", "Q-STO-002", "Q-STO-003", "Q-STO-004"],
        batch_filename="batch_deck_regular_01.json",
        presentation_id="1_f1Cn6DMpMBOF_wNlpWWFGukc0Gl87shIonRmBdWbNg",
    ),
    DeckConfig(
        deck_id="deck_regular_02",
        deck_type="regular",
        title="All-In Químico — Perguntas e Respostas — Deck Regular 02",
        subtitle="Fase 1: Aquecimento & Meio Ambiente • Lotes 006 a 010 (10 Slides Didáticos)",
        question_ids=["Q-STO-005", "Q-ENV-001", "Q-ENV-002", "Q-ENV-003", "Q-ENV-004"],
        batch_filename="batch_deck_regular_02.json",
        presentation_id="15136PklF9Vh4BqLD-vhgn1pBidfFktWQqyffAtNmUNo",
    ),
    DeckConfig(
        deck_id="deck_regular_03",
        deck_type="regular",
        title="All-In Químico — Perguntas e Respostas — Deck Regular 03",
        subtitle="Fase 2: Finais de Alta Complexidade • Lotes 011 a 015 (10 Slides Didáticos)",
        question_ids=["Q-SOL-002", "Q-SOL-003", "Q-SOL-004", "Q-SOL-009", "Q-STO-006"],
        batch_filename="batch_deck_regular_03.json",
        presentation_id="1BOZyZih5pIoGHqMyzwCgD2mXmUJzgs3us2jAijoQdbY",
    ),
    # 4. Deck Suplente / Desempate Técnico (SPEC-02 §4.4) — 5 slides
    DeckConfig(
        deck_id="deck_suplente_desempate",
        deck_type="tiebreaker",
        title="All-In Químico — Deck Suplente / Desempate (Nível 2)",
        subtitle="Rodada Extra de Desempate Técnico • 2 Lotes Suplentes (SPEC-02 §4.4)",
        question_ids=["Q-ENV-005", "Q-STO-007"],
        batch_filename="batch_deck_suplente_desempate.json",
        presentation_id="1tQ3zzj06DZpS5AnwanIprVXEW98iQ3NRxV8pLY1Z1uY",
    ),
]


def load_all_questions() -> dict[str, dict[str, Any]]:
    """
    Carrega todas as 25 questões oficiais dos 3 arquivos YAML canônicos
    e retorna um dicionário mapeado por question_id.
    """
    f_n1 = QUESTIONS_DIR / "nivel_1_aquecimento" / "questoes_nivel_1.yaml"
    f_n2 = QUESTIONS_DIR / "nivel_2_finais" / "questoes_nivel_2.yaml"
    f_n3 = QUESTIONS_DIR / "nivel_3_desafio_morte_subita" / "questoes_nivel_3.yaml"

    for f_path in (f_n1, f_n2, f_n3):
        if not f_path.exists():
            raise FileNotFoundError(f"Arquivo de questões não encontrado: {f_path}")

    with f_n1.open(encoding="utf-8") as f:
        data_n1 = yaml.safe_load(f).get("questions", [])
    with f_n2.open(encoding="utf-8") as f:
        data_n2 = yaml.safe_load(f).get("questions", [])
    with f_n3.open(encoding="utf-8") as f:
        data_n3 = yaml.safe_load(f).get("questions", [])

    if len(data_n1) != 13:
        raise ValueError(f"Esperava-se 13 questões em Nível 1, obteve {len(data_n1)}")
    if len(data_n2) != 7:
        raise ValueError(f"Esperava-se 7 questões em Nível 2, obteve {len(data_n2)}")
    if len(data_n3) != 5:
        raise ValueError(f"Esperava-se 5 questões em Nível 3, obteve {len(data_n3)}")

    questions_by_id: dict[str, dict[str, Any]] = {}
    for q in data_n1:
        q["_source_level"] = 1
        questions_by_id[q["id"]] = q
    for q in data_n2:
        q["_source_level"] = 2
        questions_by_id[q["id"]] = q
    for q in data_n3:
        q["_source_level"] = 3
        questions_by_id[q["id"]] = q

    if len(questions_by_id) != 25:
        raise ValueError(f"Total de questões deve ser 25, obteve {len(questions_by_id)}")

    return questions_by_id


def load_questions_n1_n2() -> list[dict[str, Any]]:
    """
    Função mantida para compatibilidade retroativa: carrega exclusivamente
    as 20 questões de Nível 1 e 2 ordenadas canonicamente por (difficulty, id).
    """
    all_qs = load_all_questions()
    combined = [
        q for q in all_qs.values()
        if q.get("difficulty") in (1, 2)
    ]
    combined.sort(key=lambda q: (q.get("difficulty", 1), q.get("id", "")))
    if len(combined) != 20:
        raise ValueError(f"Esperava-se 20 questões combinadas N1+N2, obteve {len(combined)}")
    return combined


def validate_partition_matrix(
    deck_configs: list[DeckConfig],
    all_questions: dict[str, dict[str, Any]]
) -> None:
    """
    Valida rigorosamente a Teoria dos Conjuntos da partição:
    1. Zero-Reuse: decks mutuamente disjuntos.
    2. Completude: união cobre 100% das 25 questões.
    3. Requisitos de negócio: R2 (3 N1), R3 (5 N3 individuais), R4 (3x5), Tiebreaker (2 N2).
    """
    seen_ids: set[str] = set()
    total_q_count = 0

    test_deck = next((d for d in deck_configs if d.deck_type == "test"), None)
    if not test_deck:
        raise ValueError("Deck de teste não encontrado na configuração.")
    if len(test_deck.question_ids) != 3:
        raise ValueError(f"Deck de teste deve ter exatamente 3 questões, obteve {len(test_deck.question_ids)}")
    for qid in test_deck.question_ids:
        q = all_questions.get(qid)
        if not q or q.get("difficulty") != 1:
            raise ValueError(f"Questão {qid} do deck de teste deve ser de Nível 1.")

    challenges = [d for d in deck_configs if d.deck_type == "challenge"]
    if len(challenges) != 5:
        raise ValueError(f"Esperava-se exatamente 5 decks de desafio, obteve {len(challenges)}")
    for c in challenges:
        if len(c.question_ids) != 1:
            raise ValueError(f"Deck de desafio {c.deck_id} deve conter exatamente 1 questão.")
        qid = c.question_ids[0]
        q = all_questions.get(qid)
        if not q or q.get("difficulty") != 3:
            raise ValueError(f"Questão {qid} do desafio deve ser de Nível 3.")

    regulars = [d for d in deck_configs if d.deck_type == "regular"]
    if len(regulars) != 3:
        raise ValueError(f"Esperava-se exatamente 3 decks regulares, obteve {len(regulars)}")
    for r in regulars:
        if len(r.question_ids) != 5:
            raise ValueError(f"Deck regular {r.deck_id} deve ter exatamente 5 questões.")

    tiebreaker = next((d for d in deck_configs if d.deck_type == "tiebreaker"), None)
    if not tiebreaker:
        raise ValueError("Deck de desempate/suplente não encontrado na configuração.")
    if len(tiebreaker.question_ids) != 2:
        raise ValueError(f"Deck de desempate deve ter exatamente 2 questões, obteve {len(tiebreaker.question_ids)}")
    for qid in tiebreaker.question_ids:
        q = all_questions.get(qid)
        if not q or q.get("difficulty") != 2:
            raise ValueError(f"Questão {qid} do desempate deve ser de Nível 2.")

    for d in deck_configs:
        for qid in d.question_ids:
            if qid in seen_ids:
                raise ValueError(f"Violação de Zero-Reuse: Questão {qid} duplicada no deck {d.deck_id}!")
            seen_ids.add(qid)
            total_q_count += 1

    if total_q_count != 25 or len(seen_ids) != 25:
        raise ValueError(f"A partição não cobre exatamente as 25 questões do banco (encontradas {len(seen_ids)}).")

    all_bank_ids = set(all_questions.keys())
    if seen_ids != all_bank_ids:
        diff = all_bank_ids.symmetric_difference(seen_ids)
        raise ValueError(f"Divergência entre questões do banco e a partição: {diff}")


# =============================================================================
# OPERAÇÕES DE SLIDE: CAPAS ESPECIALIZADAS
# =============================================================================
def build_cover_operations(
    deck_config: DeckConfig | None = None,
    questions: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """
    Roteia a geração do Slide 1 (Capa Oficial) de acordo com o tipo de deck.
    Se deck_config for None, gera a capa clássica de 20 lotes (legada).
    """
    if deck_config is None:
        return _build_legacy_cover_operations()

    if deck_config.deck_type == "test":
        return _build_test_cover_operations(deck_config)
    elif deck_config.deck_type == "challenge":
        q = questions[0] if questions else {}
        return _build_challenge_cover_operations(q, deck_config)
    elif deck_config.deck_type == "regular":
        return _build_regular_cover_operations(deck_config)
    elif deck_config.deck_type == "tiebreaker":
        return _build_tiebreaker_cover_operations(deck_config)
    else:
        return _build_legacy_cover_operations()


def _build_legacy_cover_operations() -> list[dict[str, Any]]:
    """Capa monolítica clássica (41 slides / 20 lotes)."""
    ops: list[dict[str, Any]] = [
        {"op": "delete-element", "element": "i0"},
        {"op": "delete-element", "element": "i1"},
        {"op": "set-background", "slide": "p", "color": BG_MAIN},
        {
            "op": "add-shape", "slide": "p", "shape_type": "RECTANGLE",
            "x": 0, "y": 0, "width": 720, "height": 6, "background_color": COLOR_N1,
        },
        {
            "op": "add-textbox", "slide": "p",
            "text": "ALL-IN QUÍMICO • DUELO PEDAGÓGICO DE APOSTAS A OU B",
            "x": 35, "y": 20, "width": 650, "height": 24,
            "font_size": 11, "bold": True, "color": COLOR_N1,
            "font_family": FONT_FAMILY, "alignment": "center", "content_alignment": "MIDDLE",
        },
        {
            "op": "add-textbox", "slide": "p",
            "text": "CARDS DE PERGUNTAS & RESPOSTAS",
            "x": 35, "y": 44, "width": 650, "height": 48,
            "font_size": 28, "bold": True, "color": TEXT_PRIMARY,
            "font_family": FONT_FAMILY, "alignment": "center", "content_alignment": "MIDDLE",
        },
        {
            "op": "add-textbox", "slide": "p",
            "text": "Níveis 1 e 2 — 20 Lotes Oficiais Intercalados (40 Slides de Q&A Didático)",
            "x": 35, "y": 94, "width": 650, "height": 26,
            "font_size": 13, "bold": False, "color": TEXT_SECONDARY,
            "font_family": FONT_FAMILY, "alignment": "center", "content_alignment": "MIDDLE",
        },
        {
            "op": "add-shape", "slide": "p", "shape_type": "RECTANGLE",
            "x": 260, "y": 124, "width": 200, "height": 3, "background_color": COLOR_N1,
        },
    ]

    cards = [
        {
            "header": "FASE 1: AQUECIMENTO",
            "stat": "13 Questões",
            "desc": "Lotes 001 a 013\n• Estrutura Atômica\n• Soluções & Concentrações\n• Química Ambiental & Estequiometria\n• Teto de Aposta: R$ 200",
            "header_color": COLOR_N1, "header_bg": COLOR_N1_BG, "stat_color": COLOR_N1, "x": 35,
        },
        {
            "header": "FASE 2: FINAIS",
            "stat": "7 Questões",
            "desc": "Lotes 014 a 020\n• Cálculos Estequiométricos\n• Mistura de Soluções & Diluição\n• Rendimento & Catalisadores\n• Teto de Aposta: R$ 200",
            "header_color": COLOR_N2, "header_bg": COLOR_N2_BG, "stat_color": COLOR_N2, "x": 258,
        },
        {
            "header": "ESTRUTURA DIDÁTICA",
            "stat": "Pergunta ➔ Resposta",
            "desc": "Sequência Contínua de 41 Slides\n• Slide 2i: Pergunta e Opções A / B\n• Slide 2i+1: Gabarito e Resolução\n• Regras oficiais de liquidação\n• Notas completas de orador",
            "header_color": COLOR_GREEN_TEXT, "header_bg": COLOR_GREEN_BG, "stat_color": COLOR_GREEN, "x": 481,
        },
    ]

    for c in cards:
        cx = c["x"]
        ops.extend([
            {
                "op": "add-shape", "slide": "p", "shape_type": "ROUND_RECTANGLE",
                "x": cx, "y": 140, "width": 204, "height": 166,
                "background_color": BG_CARD, "outline_color": BORDER_SUBTLE, "outline_weight": 1.0,
            },
            {
                "op": "add-textbox", "slide": "p", "text": c["header"],
                "x": cx + 8, "y": 148, "width": 188, "height": 26,
                "font_size": 10.5, "bold": True, "color": c["header_color"],
                "background_color": c["header_bg"], "font_family": FONT_FAMILY,
                "alignment": "center", "content_alignment": "MIDDLE",
            },
            {
                "op": "add-textbox", "slide": "p", "text": c["stat"],
                "x": cx + 8, "y": 178, "width": 188, "height": 34,
                "font_size": 16, "bold": True, "color": c["stat_color"],
                "font_family": FONT_FAMILY, "alignment": "center", "content_alignment": "MIDDLE",
            },
            {
                "op": "add-textbox", "slide": "p", "text": c["desc"],
                "x": cx + 8, "y": 214, "width": 188, "height": 84,
                "font_size": 9.5, "color": TEXT_SECONDARY, "font_family": FONT_FAMILY,
                "line_spacing": 125, "alignment": "center", "content_alignment": "MIDDLE",
            },
        ])

    footer_text = (
        "REGRAS OFICIAIS DE APOSTA: Aposta mín. R$ 10 e máx. R$ 200 por rodada (sem placas, no papel)  |  "
        "1 a 4 acertos: Dobro (×2 / +100% lucro)  |  "
        "5 acertos: Bônus Unânime (+R$ 100 fixo)  |  "
        "Repescagem (5ª Rodada): Equipe zerada/≤ R$ 200 recebe +R$ 200 do Banco  |  "
        "Erros: Valor vai para a Banca."
    )
    ops.extend([
        {
            "op": "add-shape", "slide": "p", "shape_type": "ROUND_RECTANGLE",
            "x": 35, "y": 318, "width": 650, "height": 68,
            "background_color": BG_CARD, "outline_color": BORDER_SUBTLE, "outline_weight": 1.0,
        },
        {
            "op": "add-textbox", "slide": "p", "text": footer_text,
            "x": 48, "y": 326, "width": 624, "height": 52,
            "font_size": 10, "bold": True, "color": TEXT_PRIMARY,
            "font_family": FONT_FAMILY, "alignment": "center", "content_alignment": "MIDDLE",
        },
        {
            "op": "set-notes", "slide": "p",
            "text": (
                "SLIDE DE ABERTURA — ALL-IN QUÍMICO: CARDS DE PERGUNTAS E RESPOSTAS\n\n"
                "Apresentação oficial contendo exatamente os 20 lotes de questões dos Níveis 1 (Aquecimento) e 2 (Finais).\n"
                "Organização em pares estritos: cada slide de pergunta N é sucedido imediatamente pelo gabarito e resolução comentada N correspondente.\n"
                "Deck restrito e delimitado exclusivamente aos Níveis 1 e 2, conforme regulamento oficial de aplicação em sala."
            ),
        },
    ])
    return ops


def _build_test_cover_operations(cfg: DeckConfig) -> list[dict[str, Any]]:
    """Slide 1 da Apresentação de Teste Exclusiva (R2 — 7 slides)."""
    ops: list[dict[str, Any]] = [
        {"op": "delete-element", "element": "i0"},
        {"op": "delete-element", "element": "i1"},
        {"op": "set-background", "slide": "p", "color": BG_MAIN},
        {
            "op": "add-shape", "slide": "p", "shape_type": "RECTANGLE",
            "x": 0, "y": 0, "width": 720, "height": 6, "background_color": COLOR_N1,
        },
        {
            "op": "add-textbox", "slide": "p",
            "text": "ALL-IN QUÍMICO • CALIBRAÇÃO PEDAGÓGICA SEM RISCO",
            "x": 35, "y": 20, "width": 650, "height": 24,
            "font_size": 11, "bold": True, "color": COLOR_N1,
            "font_family": FONT_FAMILY, "alignment": "center", "content_alignment": "MIDDLE",
        },
        {
            "op": "add-textbox", "slide": "p",
            "text": "RODADA DE AQUECIMENTO E TESTE",
            "x": 35, "y": 44, "width": 650, "height": 48,
            "font_size": 28, "bold": True, "color": TEXT_PRIMARY,
            "font_family": FONT_FAMILY, "alignment": "center", "content_alignment": "MIDDLE",
        },
        {
            "op": "add-textbox", "slide": "p",
            "text": cfg.subtitle,
            "x": 35, "y": 94, "width": 650, "height": 26,
            "font_size": 13, "bold": False, "color": TEXT_SECONDARY,
            "font_family": FONT_FAMILY, "alignment": "center", "content_alignment": "MIDDLE",
        },
        {
            "op": "add-shape", "slide": "p", "shape_type": "RECTANGLE",
            "x": 260, "y": 124, "width": 200, "height": 3, "background_color": COLOR_N1,
        },
    ]

    cards = [
        {
            "header": "FASE DE TESTE",
            "stat": "3 Questões Didáticas",
            "desc": "Lotes T-01 a T-03\n• Q-ATO-001 (Tabela Periódica)\n• Q-SOL-001 (Concentração Comum)\n• Q-STO-001 (Mol & NaCl)\n• Treino de Dinâmica de Apostas",
            "header_color": COLOR_N1, "header_bg": COLOR_N1_BG, "stat_color": COLOR_N1, "x": 35,
        },
        {
            "header": "CALIBRAÇÃO DIDÁTICA",
            "stat": "Sem Risco Financeiro",
            "desc": "• Fixação das regras de aposta\n• Treino do registro em papel\n• Calibração do tempo de equipe\n• Sem débito real no saldo",
            "header_color": COLOR_N2, "header_bg": COLOR_N2_BG, "stat_color": COLOR_N2, "x": 258,
        },
        {
            "header": "ESTRUTURA DO DECK",
            "stat": "7 Slides Total",
            "desc": "Sequência de Calibração\n• 1 Slide de Abertura\n• 3 Slides de Pergunta e Opções\n• 3 Slides de Gabarito & Resolução\n• Paridade estrita Q&A",
            "header_color": COLOR_GREEN_TEXT, "header_bg": COLOR_GREEN_BG, "stat_color": COLOR_GREEN, "x": 481,
        },
    ]

    for c in cards:
        cx = c["x"]
        ops.extend([
            {
                "op": "add-shape", "slide": "p", "shape_type": "ROUND_RECTANGLE",
                "x": cx, "y": 140, "width": 204, "height": 166,
                "background_color": BG_CARD, "outline_color": BORDER_SUBTLE, "outline_weight": 1.0,
            },
            {
                "op": "add-textbox", "slide": "p", "text": c["header"],
                "x": cx + 8, "y": 148, "width": 188, "height": 26,
                "font_size": 10.5, "bold": True, "color": c["header_color"],
                "background_color": c["header_bg"], "font_family": FONT_FAMILY,
                "alignment": "center", "content_alignment": "MIDDLE",
            },
            {
                "op": "add-textbox", "slide": "p", "text": c["stat"],
                "x": cx + 8, "y": 178, "width": 188, "height": 34,
                "font_size": 14, "bold": True, "color": c["stat_color"],
                "font_family": FONT_FAMILY, "alignment": "center", "content_alignment": "MIDDLE",
            },
            {
                "op": "add-textbox", "slide": "p", "text": c["desc"],
                "x": cx + 8, "y": 214, "width": 188, "height": 84,
                "font_size": 9.5, "color": TEXT_SECONDARY, "font_family": FONT_FAMILY,
                "line_spacing": 125, "alignment": "center", "content_alignment": "MIDDLE",
            },
        ])

    footer_text = (
        "RODADA DE TESTE EXCLUSIVA (NÍVEL 1): Treino didático para ambientação das equipes com as regras do jogo.  |  "
        "As apostas e resoluções desta rodada não alteram os saldos oficiais da partida principal."
    )
    ops.extend([
        {
            "op": "add-shape", "slide": "p", "shape_type": "ROUND_RECTANGLE",
            "x": 35, "y": 318, "width": 650, "height": 68,
            "background_color": BG_CARD, "outline_color": BORDER_SUBTLE, "outline_weight": 1.0,
        },
        {
            "op": "add-textbox", "slide": "p", "text": footer_text,
            "x": 48, "y": 326, "width": 624, "height": 52,
            "font_size": 10, "bold": True, "color": TEXT_PRIMARY,
            "font_family": FONT_FAMILY, "alignment": "center", "content_alignment": "MIDDLE",
        },
        {
            "op": "set-notes", "slide": "p",
            "text": (
                "SLIDE DE ABERTURA — APRESENTAÇÃO DE TESTE EXCLUSIVA (NÍVEL 1)\n\n"
                "Deck reservado exclusivamente para calibração didática das regras de aposta.\n"
                "Total de 3 questões: Q-ATO-001, Q-SOL-001 e Q-STO-001.\n"
                "Regra de Isolamento: nenhuma destas 3 questões pode ser reutilizada em partidas oficiais."
            ),
        },
    ])
    return ops


def _build_challenge_cover_operations(q: dict[str, Any], cfg: DeckConfig) -> list[dict[str, Any]]:
    """Slide 1 das Apresentações Individuais de Desafio N3 (R3 — Texas Hold'em / Morte Súbita)."""
    raw_statement = q.get("statement", "")
    match = re.search(r"🔥\s*\[APOSTA NO TEMA:\s*(.*?)\]", raw_statement)
    theme = match.group(1).strip() if match else "DESAFIO FINAL"
    qid = q.get("id", "")
    domain = q.get("domain", "")
    domain_name = DOMAIN_NAMES.get(domain, domain)

    ops: list[dict[str, Any]] = [
        {"op": "delete-element", "element": "i0"},
        {"op": "delete-element", "element": "i1"},
        {"op": "set-background", "slide": "p", "color": BG_MAIN},
        {
            "op": "add-shape", "slide": "p", "shape_type": "RECTANGLE",
            "x": 0, "y": 0, "width": 720, "height": 6, "background_color": COLOR_N3,
        },
        {
            "op": "add-textbox", "slide": "p",
            "text": "ALL-IN QUÍMICO • MORTE SÚBITA (NÍVEL 3) • TEXAS HOLD'EM",
            "x": 35, "y": 20, "width": 650, "height": 24,
            "font_size": 11, "bold": True, "color": COLOR_N3,
            "font_family": FONT_FAMILY, "alignment": "center", "content_alignment": "MIDDLE",
        },
        {
            "op": "add-textbox", "slide": "p",
            "text": f"DESAFIO FINAL: {theme.upper()}",
            "x": 35, "y": 44, "width": 650, "height": 48,
            "font_size": 25, "bold": True, "color": TEXT_PRIMARY,
            "font_family": FONT_FAMILY, "alignment": "center", "content_alignment": "MIDDLE",
        },
        {
            "op": "add-textbox", "slide": "p",
            "text": f"Fase 1: Aposta no Escuro • Teto Desbloqueado • Mecânica All-In ({qid})",
            "x": 35, "y": 94, "width": 650, "height": 26,
            "font_size": 13, "bold": False, "color": TEXT_SECONDARY,
            "font_family": FONT_FAMILY, "alignment": "center", "content_alignment": "MIDDLE",
        },
        {
            "op": "add-shape", "slide": "p", "shape_type": "RECTANGLE",
            "x": 260, "y": 124, "width": 200, "height": 3, "background_color": COLOR_N3,
        },
    ]

    cards = [
        {
            "header": "TEMA DO DESAFIO",
            "stat": theme.upper(),
            "desc": f"• Domínio: {domain_name}\n• Análise multietapa de alta complexidade\n• Enunciado revelado na Fase 2\n• Aposta mínima: 100 T$",
            "header_color": COLOR_N3_TEXT, "header_bg": COLOR_N3_BG, "stat_color": COLOR_N3, "x": 35,
        },
        {
            "header": "MECÂNICA NO ESCURO",
            "stat": "Aposta no Tema",
            "desc": "• Apostem apenas pelo tema!\n• Permissão de All-In de todo o saldo\n• Equipes sem saldo estão fora\n• Registro obrigatório em folha",
            "header_color": COLOR_N2, "header_bg": COLOR_N2_BG, "stat_color": COLOR_N2, "x": 258,
        },
        {
            "header": "LIQUIDAÇÃO FINAL",
            "stat": "Winner Takes All",
            "desc": "• Maior lance correto leva o pote!\n• Pote central disputado na mesa\n• Empate: divisão proporcional\n• Erros: fichas vão para a Banca",
            "header_color": COLOR_GREEN_TEXT, "header_bg": COLOR_GREEN_BG, "stat_color": COLOR_GREEN, "x": 481,
        },
    ]

    for c in cards:
        cx = c["x"]
        ops.extend([
            {
                "op": "add-shape", "slide": "p", "shape_type": "ROUND_RECTANGLE",
                "x": cx, "y": 140, "width": 204, "height": 166,
                "background_color": BG_CARD, "outline_color": BORDER_SUBTLE, "outline_weight": 1.0,
            },
            {
                "op": "add-textbox", "slide": "p", "text": c["header"],
                "x": cx + 8, "y": 148, "width": 188, "height": 26,
                "font_size": 10.5, "bold": True, "color": c["header_color"],
                "background_color": c["header_bg"], "font_family": FONT_FAMILY,
                "alignment": "center", "content_alignment": "MIDDLE",
            },
            {
                "op": "add-textbox", "slide": "p", "text": c["stat"],
                "x": cx + 8, "y": 178, "width": 188, "height": 34,
                "font_size": 13 if len(c["stat"]) > 18 else 15, "bold": True, "color": c["stat_color"],
                "font_family": FONT_FAMILY, "alignment": "center", "content_alignment": "MIDDLE",
            },
            {
                "op": "add-textbox", "slide": "p", "text": c["desc"],
                "x": cx + 8, "y": 214, "width": 188, "height": 84,
                "font_size": 9.5, "color": TEXT_SECONDARY, "font_family": FONT_FAMILY,
                "line_spacing": 125, "alignment": "center", "content_alignment": "MIDDLE",
            },
        ])

    footer_text = (
        "REGRAS DA MORTE SÚBITA: Aposta mínima de 100 T$  |  All-In autorizado  |  "
        "Winner Takes All (o grupo com a maior aposta entre os que acertarem recolhe todo o pote da mesa)  |  "
        "Erros: 100% recolhido para a Banca."
    )
    ops.extend([
        {
            "op": "add-shape", "slide": "p", "shape_type": "ROUND_RECTANGLE",
            "x": 35, "y": 318, "width": 650, "height": 68,
            "background_color": BG_CARD, "outline_color": BORDER_SUBTLE, "outline_weight": 1.0,
        },
        {
            "op": "add-textbox", "slide": "p", "text": footer_text,
            "x": 48, "y": 326, "width": 624, "height": 52,
            "font_size": 10, "bold": True, "color": TEXT_PRIMARY,
            "font_family": FONT_FAMILY, "alignment": "center", "content_alignment": "MIDDLE",
        },
        {
            "op": "set-notes", "slide": "p",
            "text": (
                f"SLIDE DE ABERTURA — MORTE SÚBITA: {theme.upper()} ({qid})\n\n"
                "FASE 1: APOSTA NO ESCURO\n"
                "1. Projete apenas este slide para a turma. O enunciado e as opções ainda estão ocultos.\n"
                f"2. Anuncie o tema da rodada decisiva: {theme.upper()}.\n"
                "3. Explique que as equipes devem avaliar seu domínio sobre este tema e definir sua aposta no escuro.\n"
                "4. Aposta mínima de 100 T$. All-In autorizado (apostar todo o saldo restante).\n"
                "5. Recolha ou confira as apostas antes de avançar para o slide 2 (enunciado)."
            ),
        },
    ])
    return ops


def _build_regular_cover_operations(cfg: DeckConfig) -> list[dict[str, Any]]:
    """Slide 1 dos Decks Regulares (R4 — 11 slides / 5 Q&A)."""
    ops: list[dict[str, Any]] = [
        {"op": "delete-element", "element": "i0"},
        {"op": "delete-element", "element": "i1"},
        {"op": "set-background", "slide": "p", "color": BG_MAIN},
        {
            "op": "add-shape", "slide": "p", "shape_type": "RECTANGLE",
            "x": 0, "y": 0, "width": 720, "height": 6, "background_color": COLOR_N1,
        },
        {
            "op": "add-textbox", "slide": "p",
            "text": "ALL-IN QUÍMICO • DUELO PEDAGÓGICO DE APOSTAS A OU B",
            "x": 35, "y": 20, "width": 650, "height": 24,
            "font_size": 11, "bold": True, "color": COLOR_N1,
            "font_family": FONT_FAMILY, "alignment": "center", "content_alignment": "MIDDLE",
        },
        {
            "op": "add-textbox", "slide": "p",
            "text": "CARDS DE PERGUNTAS & RESPOSTAS",
            "x": 35, "y": 44, "width": 650, "height": 48,
            "font_size": 28, "bold": True, "color": TEXT_PRIMARY,
            "font_family": FONT_FAMILY, "alignment": "center", "content_alignment": "MIDDLE",
        },
        {
            "op": "add-textbox", "slide": "p",
            "text": cfg.subtitle,
            "x": 35, "y": 94, "width": 650, "height": 26,
            "font_size": 13, "bold": False, "color": TEXT_SECONDARY,
            "font_family": FONT_FAMILY, "alignment": "center", "content_alignment": "MIDDLE",
        },
        {
            "op": "add-shape", "slide": "p", "shape_type": "RECTANGLE",
            "x": 260, "y": 124, "width": 200, "height": 3, "background_color": COLOR_N1,
        },
    ]

    cards = [
        {
            "header": "PARTIDA REGULAR",
            "stat": "5 Questões Oficiais",
            "desc": "Lotes Intercalados do Deck\n• Domínios Químicos Oficiais\n• 1 a 4 acertos: Dobro (×2)\n• 5 acertos: Bônus Unânime (+R$ 100)",
            "header_color": COLOR_N1, "header_bg": COLOR_N1_BG, "stat_color": COLOR_N1, "x": 35,
        },
        {
            "header": "LIMITES DE APOSTA",
            "stat": "R$ 10 a R$ 200",
            "desc": "• Aposta mín. R$ 10 por rodada\n• Teto máx. R$ 200 por questão\n• Repescagem 5ª Rodada: +R$ 200\n• Apostas em folha (sem placas)",
            "header_color": COLOR_N2, "header_bg": COLOR_N2_BG, "stat_color": COLOR_N2, "x": 258,
        },
        {
            "header": "ESTRUTURA DIDÁTICA",
            "stat": "11 Slides Total",
            "desc": "Sequência Q&A Fechada\n• 1 Slide de Abertura\n• 5 Slides de Pergunta e Opções\n• 5 Slides de Gabarito & Resolução\n• Paridade estrita intercalada",
            "header_color": COLOR_GREEN_TEXT, "header_bg": COLOR_GREEN_BG, "stat_color": COLOR_GREEN, "x": 481,
        },
    ]

    for c in cards:
        cx = c["x"]
        ops.extend([
            {
                "op": "add-shape", "slide": "p", "shape_type": "ROUND_RECTANGLE",
                "x": cx, "y": 140, "width": 204, "height": 166,
                "background_color": BG_CARD, "outline_color": BORDER_SUBTLE, "outline_weight": 1.0,
            },
            {
                "op": "add-textbox", "slide": "p", "text": c["header"],
                "x": cx + 8, "y": 148, "width": 188, "height": 26,
                "font_size": 10.5, "bold": True, "color": c["header_color"],
                "background_color": c["header_bg"], "font_family": FONT_FAMILY,
                "alignment": "center", "content_alignment": "MIDDLE",
            },
            {
                "op": "add-textbox", "slide": "p", "text": c["stat"],
                "x": cx + 8, "y": 178, "width": 188, "height": 34,
                "font_size": 14, "bold": True, "color": c["stat_color"],
                "font_family": FONT_FAMILY, "alignment": "center", "content_alignment": "MIDDLE",
            },
            {
                "op": "add-textbox", "slide": "p", "text": c["desc"],
                "x": cx + 8, "y": 214, "width": 188, "height": 84,
                "font_size": 9.5, "color": TEXT_SECONDARY, "font_family": FONT_FAMILY,
                "line_spacing": 125, "alignment": "center", "content_alignment": "MIDDLE",
            },
        ])

    footer_text = (
        "REGRAS OFICIAIS DE APOSTA: Aposta mín. R$ 10 e máx. R$ 200 por rodada (sem placas, no papel)  |  "
        "1 a 4 acertos: Dobro (×2 / +100% lucro)  |  "
        "5 acertos: Bônus Unânime (+R$ 100 fixo)  |  "
        "Repescagem (5ª Rodada): Equipe com saldo ≤ R$ 200 recebe +R$ 200 do Banco."
    )
    ops.extend([
        {
            "op": "add-shape", "slide": "p", "shape_type": "ROUND_RECTANGLE",
            "x": 35, "y": 318, "width": 650, "height": 68,
            "background_color": BG_CARD, "outline_color": BORDER_SUBTLE, "outline_weight": 1.0,
        },
        {
            "op": "add-textbox", "slide": "p", "text": footer_text,
            "x": 48, "y": 326, "width": 624, "height": 52,
            "font_size": 10, "bold": True, "color": TEXT_PRIMARY,
            "font_family": FONT_FAMILY, "alignment": "center", "content_alignment": "MIDDLE",
        },
        {
            "op": "set-notes", "slide": "p",
            "text": (
                f"SLIDE DE ABERTURA — {cfg.title}\n\n"
                f"Apresentação regular independente contendo exatamente 5 questões fechadas.\n"
                f"Questões alocadas: {', '.join(cfg.question_ids)}.\n"
                "Paridade estrita: 1 slide de pergunta seguido imediatamente pelo gabarito correspondente."
            ),
        },
    ])
    return ops


def _build_tiebreaker_cover_operations(cfg: DeckConfig) -> list[dict[str, Any]]:
    """Slide 1 do Deck Suplente / Desempate Técnico (SPEC-02 §4.4 — 5 slides)."""
    ops: list[dict[str, Any]] = [
        {"op": "delete-element", "element": "i0"},
        {"op": "delete-element", "element": "i1"},
        {"op": "set-background", "slide": "p", "color": BG_MAIN},
        {
            "op": "add-shape", "slide": "p", "shape_type": "RECTANGLE",
            "x": 0, "y": 0, "width": 720, "height": 6, "background_color": COLOR_N2,
        },
        {
            "op": "add-textbox", "slide": "p",
            "text": "ALL-IN QUÍMICO • DESEMPATE TÉCNICO (SPEC-02 §4.4)",
            "x": 35, "y": 20, "width": 650, "height": 24,
            "font_size": 11, "bold": True, "color": COLOR_N2,
            "font_family": FONT_FAMILY, "alignment": "center", "content_alignment": "MIDDLE",
        },
        {
            "op": "add-textbox", "slide": "p",
            "text": "RODADA EXTRA DE DESEMPATE TÉCNICO",
            "x": 35, "y": 44, "width": 650, "height": 48,
            "font_size": 26, "bold": True, "color": TEXT_PRIMARY,
            "font_family": FONT_FAMILY, "alignment": "center", "content_alignment": "MIDDLE",
        },
        {
            "op": "add-textbox", "slide": "p",
            "text": cfg.subtitle,
            "x": 35, "y": 94, "width": 650, "height": 26,
            "font_size": 13, "bold": False, "color": TEXT_SECONDARY,
            "font_family": FONT_FAMILY, "alignment": "center", "content_alignment": "MIDDLE",
        },
        {
            "op": "add-shape", "slide": "p", "shape_type": "RECTANGLE",
            "x": 260, "y": 124, "width": 200, "height": 3, "background_color": COLOR_N2,
        },
    ]

    cards = [
        {
            "header": "CRITÉRIO DE ATIVAÇÃO",
            "stat": "Empate ≤ 100 T$",
            "desc": "• Acionado se a diferença entre 1º e 2º for ≤ 100 T$\n• 2 Lotes de alta complexidade (Nível 2)\n• Decisão prévia antes da Morte Súbita",
            "header_color": COLOR_N2, "header_bg": COLOR_N2_BG, "stat_color": COLOR_N2, "x": 35,
        },
        {
            "header": "REGRAS DA DISPUTA",
            "stat": "Teto R$ 200",
            "desc": "• Apenas equipes empatadas apostam na rodada\n• Demais equipes assistem e analisam\n• Multiplicador ×2 padrão",
            "header_color": COLOR_N1, "header_bg": COLOR_N1_BG, "stat_color": COLOR_N1, "x": 258,
        },
        {
            "header": "ESTRUTURA DO DECK",
            "stat": "5 Slides Total",
            "desc": "Sequência Suplente\n• 1 Slide de Abertura\n• 2 Slides de Pergunta [A] / [B]\n• 2 Slides de Gabarito & Resolução\n• Paridade intercalada Q&A",
            "header_color": COLOR_GREEN_TEXT, "header_bg": COLOR_GREEN_BG, "stat_color": COLOR_GREEN, "x": 481,
        },
    ]

    for c in cards:
        cx = c["x"]
        ops.extend([
            {
                "op": "add-shape", "slide": "p", "shape_type": "ROUND_RECTANGLE",
                "x": cx, "y": 140, "width": 204, "height": 166,
                "background_color": BG_CARD, "outline_color": BORDER_SUBTLE, "outline_weight": 1.0,
            },
            {
                "op": "add-textbox", "slide": "p", "text": c["header"],
                "x": cx + 8, "y": 148, "width": 188, "height": 26,
                "font_size": 10.5, "bold": True, "color": c["header_color"],
                "background_color": c["header_bg"], "font_family": FONT_FAMILY,
                "alignment": "center", "content_alignment": "MIDDLE",
            },
            {
                "op": "add-textbox", "slide": "p", "text": c["stat"],
                "x": cx + 8, "y": 178, "width": 188, "height": 34,
                "font_size": 14, "bold": True, "color": c["stat_color"],
                "font_family": FONT_FAMILY, "alignment": "center", "content_alignment": "MIDDLE",
            },
            {
                "op": "add-textbox", "slide": "p", "text": c["desc"],
                "x": cx + 8, "y": 214, "width": 188, "height": 84,
                "font_size": 9.5, "color": TEXT_SECONDARY, "font_family": FONT_FAMILY,
                "line_spacing": 125, "alignment": "center", "content_alignment": "MIDDLE",
            },
        ])

    footer_text = (
        "DECK SUPLENTE / DESEMPATE (NÍVEL 2): Acionado pelo professor caso haja empate técnico de primeiro lugar "
        "antes da Morte Súbita, conforme SPEC-02 §4.4."
    )
    ops.extend([
        {
            "op": "add-shape", "slide": "p", "shape_type": "ROUND_RECTANGLE",
            "x": 35, "y": 318, "width": 650, "height": 68,
            "background_color": BG_CARD, "outline_color": BORDER_SUBTLE, "outline_weight": 1.0,
        },
        {
            "op": "add-textbox", "slide": "p", "text": footer_text,
            "x": 48, "y": 326, "width": 624, "height": 52,
            "font_size": 10, "bold": True, "color": TEXT_PRIMARY,
            "font_family": FONT_FAMILY, "alignment": "center", "content_alignment": "MIDDLE",
        },
        {
            "op": "set-notes", "slide": "p",
            "text": (
                "SLIDE DE ABERTURA — DECK SUPLENTE E DESEMPATE TÉCNICO (NÍVEL 2)\n\n"
                "Utilizado exclusivamente se a diferença entre equipes líderes for <= 100 T$.\n"
                "Questões alocadas: Q-ENV-005 e Q-STO-007."
            ),
        },
    ])
    return ops


# =============================================================================
# OPERAÇÕES DE SLIDE: PERGUNTA (SLIDE 2i) E RESPOSTA (SLIDE 2i+1)
# =============================================================================
def build_question_operations(
    q: dict[str, Any],
    lote_num: int | str,
    deck_type: str = "regular",
    slide_idx: int | None = None,
) -> list[dict[str, Any]]:
    """Gera as operações do Slide de Pergunta (Slide 2i — Grid 2 Colunas Fintech Clean)."""
    if slide_idx is None:
        idx_val = int(lote_num) if isinstance(lote_num, int) or (isinstance(lote_num, str) and lote_num.isdigit()) else 1
    else:
        idx_val = slide_idx
    slide_id = f"SLIDE_Q_{idx_val:03d}"

    qid = q.get("id", "")
    difficulty = q.get("difficulty", 1)
    domain = q.get("domain", "")
    domain_name = DOMAIN_NAMES.get(domain, domain)
    cog_level = COGNITIVE_LABELS.get(q.get("cognitive_level", ""), q.get("cognitive_level", ""))

    # Trata tema e prefixo de fogo em Nível 3
    raw_statement = q.get("statement", "")
    theme = ""
    if difficulty == 3 or deck_type == "challenge":
        match = re.search(r"🔥\s*\[APOSTA NO TEMA:\s*(.*?)\]", raw_statement)
        if match:
            theme = match.group(1).strip()
        clean_raw_stmt = re.sub(r"🔥\s*\[APOSTA NO TEMA:\s*.*?\]\s*", "", raw_statement).strip()
        statement = clean_chemical_typography(clean_raw_stmt)
    else:
        statement = clean_chemical_typography(raw_statement)

    options = q.get("options", [])
    opt_a = next((o for o in options if o.get("key") == "A"), {"text": ""})
    opt_b = next((o for o in options if o.get("key") == "B"), {"text": ""})

    text_a = clean_chemical_typography(opt_a.get("text", ""))
    text_b = clean_chemical_typography(opt_b.get("text", ""))

    # Auto-scaling tipográfico anti-overflow
    typography = compute_typography_params(statement, options, q)

    if difficulty == 1:
        level_color = COLOR_N1
        level_bg = COLOR_N1_BG
        level_name = "NÍVEL 1 (AQUECIMENTO)"
    elif difficulty == 2:
        level_color = COLOR_N2
        level_bg = COLOR_N2_BG
        level_name = "NÍVEL 2 (FINAIS)"
    else:
        level_color = COLOR_N3
        level_bg = COLOR_N3_BG
        level_name = "NÍVEL 3 (MORTE SÚBITA)"

    dom_color, dom_bg = DOMAIN_STYLES.get(domain, (TEXT_PRIMARY, BG_CARD_SUBTLE))

    # Formatação do rótulo do Lote
    if isinstance(lote_num, int):
        lote_str = f"{lote_num:03d}"
        badge1_text = f"LOTE {lote_str}  •  {level_name}"
    else:
        lote_str = str(lote_num)
        if deck_type == "challenge":
            badge1_text = "DESAFIO DA MESA • MORTE SÚBITA"
        elif deck_type == "test":
            badge1_text = f"RODADA TESTE • {lote_str}"
        elif deck_type == "tiebreaker":
            badge1_text = f"DESEMPATE • {lote_str}"
        else:
            badge1_text = f"LOTE {lote_str}  •  {level_name}"

    badge2_text = f"TEMA: {theme.upper()}" if (difficulty == 3 and theme) else domain_name
    badge2_color = COLOR_N3_TEXT if difficulty == 3 else dom_color
    badge2_bg = COLOR_N3_BG if difficulty == 3 else dom_bg

    ops: list[dict[str, Any]] = [
        {"op": "add-slide", "layout": "BLANK", "id": slide_id},
        {"op": "set-background", "slide": slide_id, "color": BG_MAIN},
        # Barra superior institucional colorida pelo nível (6px)
        {
            "op": "add-shape", "slide": slide_id, "shape_type": "RECTANGLE",
            "x": 0, "y": 0, "width": 720, "height": 6, "background_color": level_color,
        },
        # --- HEADER / METADATA (Duplo Destaque Semântico) ---
        {
            "op": "add-textbox", "slide": slide_id,
            "text": badge1_text,
            "x": 32, "y": 16, "width": 240, "height": 28,
            "font_size": 10.5, "bold": True, "color": level_color, "background_color": level_bg,
            "font_family": FONT_FAMILY, "alignment": "center", "content_alignment": "MIDDLE",
        },
        {
            "op": "add-textbox", "slide": slide_id,
            "text": badge2_text,
            "x": 280, "y": 16, "width": 280, "height": 28,
            "font_size": 10.5, "bold": True, "color": badge2_color, "background_color": badge2_bg,
            "font_family": FONT_FAMILY, "alignment": "center", "content_alignment": "MIDDLE",
        },
        {
            "op": "add-textbox", "slide": slide_id,
            "text": f"{qid} | {cog_level}",
            "x": 568, "y": 16, "width": 120, "height": 28,
            "font_size": 9.5, "bold": True, "color": TEXT_MUTED, "background_color": BG_CARD_SUBTLE,
            "font_family": FONT_FAMILY, "alignment": "center", "content_alignment": "MIDDLE",
        },

        # --- COLUNA DA ESQUERDA: CARD DO ENUNCIADO (max-w-prose) ---
        {
            "op": "add-shape", "slide": slide_id, "shape_type": "ROUND_RECTANGLE",
            "x": 32, "y": 56, "width": 328, "height": 248,
            "background_color": BG_CARD, "outline_color": BORDER_SUBTLE, "outline_weight": 1.0,
        },
        {
            "op": "add-textbox", "slide": slide_id,
            "text": "DESAFIO DE MORTE SÚBITA" if difficulty == 3 else "QUESTÃO DIDÁTICA",
            "x": 48, "y": 68, "width": 296, "height": 20,
            "font_size": 9.5, "bold": True, "color": level_color, "font_family": FONT_FAMILY,
            "alignment": "left", "content_alignment": "TOP",
        },
        {
            "op": "add-textbox", "slide": slide_id,
            "text": statement,
            "x": 48, "y": 92, "width": 296, "height": 196,
            "font_size": typography.stmt_font_size, "color": TEXT_PRIMARY, "font_family": FONT_FAMILY,
            "line_spacing": typography.stmt_line_spacing, "alignment": "left", "content_alignment": "TOP",
        },

        # --- COLUNA DA DIREITA: CARDS DE ALTERNATIVAS A e B ---
        {
            "op": "add-shape", "slide": slide_id, "shape_type": "ROUND_RECTANGLE",
            "x": 368, "y": 56, "width": 320, "height": 118,
            "background_color": BG_CARD, "outline_color": BORDER_SUBTLE, "outline_weight": 1.0,
        },
        {
            "op": "add-textbox", "slide": slide_id,
            "text": "ALTERNATIVA [A]",
            "x": 384, "y": 68, "width": 130, "height": 22,
            "font_size": 10, "bold": True, "color": level_color, "background_color": level_bg,
            "font_family": FONT_FAMILY, "alignment": "center", "content_alignment": "MIDDLE",
        },
        {
            "op": "add-textbox", "slide": slide_id,
            "text": text_a,
            "x": 384, "y": 96, "width": 288, "height": 68,
            "font_size": typography.opt_font_size, "bold": True, "color": TEXT_PRIMARY, "font_family": FONT_FAMILY,
            "line_spacing": typography.opt_line_spacing, "alignment": "left", "content_alignment": "TOP",
        },

        {
            "op": "add-shape", "slide": slide_id, "shape_type": "ROUND_RECTANGLE",
            "x": 368, "y": 186, "width": 320, "height": 118,
            "background_color": BG_CARD, "outline_color": BORDER_SUBTLE, "outline_weight": 1.0,
        },
        {
            "op": "add-textbox", "slide": slide_id,
            "text": "ALTERNATIVA [B]",
            "x": 384, "y": 198, "width": 130, "height": 22,
            "font_size": 10, "bold": True, "color": level_color, "background_color": level_bg,
            "font_family": FONT_FAMILY, "alignment": "center", "content_alignment": "MIDDLE",
        },
        {
            "op": "add-textbox", "slide": slide_id,
            "text": text_b,
            "x": 384, "y": 226, "width": 288, "height": 68,
            "font_size": typography.opt_font_size, "bold": True, "color": TEXT_PRIMARY, "font_family": FONT_FAMILY,
            "line_spacing": typography.opt_line_spacing, "alignment": "left", "content_alignment": "TOP",
        },

        # --- BARRA DE GOVERNANÇA / APOSTAS NO RODAPÉ ---
        {
            "op": "add-shape", "slide": slide_id, "shape_type": "ROUND_RECTANGLE",
            "x": 32, "y": 318, "width": 656, "height": 68,
            "background_color": BG_CARD, "outline_color": BORDER_SUBTLE, "outline_weight": 1.0,
        },
        {
            "op": "add-textbox", "slide": slide_id,
            "text": (
                "🔥 FASE 2: ENUNCIADO REVELADO  •  CONFIRMAÇÃO DE APOSTAS  •  ALL-IN DISPONÍVEL"
                if difficulty == 3 else
                "💰 FAÇAM SUAS APOSTAS!  •  TETO MÁXIMO: R$ 200 (MÍN. R$ 10)  •  REPESCAGEM 5ª RODADA: +R$ 200 (SALDO ≤ R$ 200)"
            ),
            "x": 48, "y": 326, "width": 624, "height": 20,
            "font_size": 9.8, "bold": True, "color": COLOR_N3 if difficulty == 3 else COLOR_N2,
            "font_family": FONT_FAMILY, "alignment": "center", "content_alignment": "MIDDLE",
        },
        {
            "op": "add-textbox", "slide": slide_id,
            "text": (
                "Conferência final das apostas da mesa antes do encerramento do cronômetro. Vitória por maior lance correto (WTA)."
                if difficulty == 3 else
                "Registrem na folha de aposta a alternativa escolhida (A ou B) e o valor em dinheiro antes do encerramento do cronômetro."
            ),
            "x": 48, "y": 348, "width": 624, "height": 28,
            "font_size": 10, "color": TEXT_MUTED, "font_family": FONT_FAMILY,
            "alignment": "center", "content_alignment": "MIDDLE",
        },
    ]

    skill = q.get("skill", "Não especificada")
    concepts = ", ".join(q.get("concept_refs", [])) or "Gerais"
    formulas = ", ".join(q.get("formula_refs", [])) or "Sem fórmula específica"

    notes = (
        f"CARD DE PERGUNTA — {badge1_text} ({qid})\n\n"
        f"• Nível: {level_name} (Dificuldade {difficulty})\n"
        f"• Domínio: {domain_name} ({domain})\n"
        f"• Habilidade Pedagógica: {skill}\n"
        f"• Nível Cognitivo: {cog_level}\n"
        f"• Conceitos da Base: {concepts}\n"
        f"• Fórmulas de Referência: {formulas}\n\n"
        f"INSTRUÇÕES DE APLICAÇÃO PARA O PROFESSOR:\n"
        f"1. Projete este slide e faça a leitura clara do enunciado e das duas opções.\n"
        f"2. Conceda de 60 a 90 segundos para debate interno em cada equipe de estudantes.\n"
        f"3. Lembre a turma das regras de aposta e da obrigatoriedade do registro por escrito.\n"
        f"4. Recolha ou confira visualmente todas as folhas de resposta antes de avançar para o gabarito."
    )
    ops.append({"op": "set-notes", "slide": slide_id, "text": notes})

    return ops


def build_answer_operations(
    q: dict[str, Any],
    lote_num: int | str,
    deck_type: str = "regular",
    slide_idx: int | None = None,
) -> list[dict[str, Any]]:
    """Gera as operações do Slide de Resposta (Slide 2i+1 — Gabarito & Resolução Fintech Clean)."""
    if slide_idx is None:
        idx_val = int(lote_num) if isinstance(lote_num, int) or (isinstance(lote_num, str) and lote_num.isdigit()) else 1
    else:
        idx_val = slide_idx
    slide_id = f"SLIDE_A_{idx_val:03d}"

    qid = q.get("id", "")
    correct = q.get("correct", "A").upper()
    domain = q.get("domain", "")
    difficulty = q.get("difficulty", 1)

    worked_solution = clean_chemical_typography(q.get("worked_solution", ""))
    scientific_justification = clean_chemical_typography(q.get("scientific_justification", ""))

    options = q.get("options", [])
    wrong_key = "B" if correct == "A" else "A"
    wrong_opt = next((o for o in options if o.get("key") == wrong_key), {})
    wrong_rationale = clean_chemical_typography(wrong_opt.get("rationale", "Alternativa incorreta."))

    # Auto-scaling tipográfico anti-overflow
    typography = compute_typography_params(
        q.get("statement", ""),
        options,
        {
            "scientific_justification": scientific_justification,
            "distractor_rationale": wrong_rationale,
            "wrong_key": wrong_key,
        },
    )

    if isinstance(lote_num, int):
        lote_str = f"{lote_num:03d}"
        badge1_text = f"GABARITO OFICIAL  •  LOTE {lote_str}"
    else:
        lote_str = str(lote_num)
        if deck_type == "challenge":
            badge1_text = "GABARITO OFICIAL • MORTE SÚBITA"
        else:
            badge1_text = f"GABARITO OFICIAL • {lote_str}"

    ops: list[dict[str, Any]] = [
        {"op": "add-slide", "layout": "BLANK", "id": slide_id},
        {"op": "set-background", "slide": slide_id, "color": BG_MAIN},
        # Barra superior verde esmeralda (6px)
        {
            "op": "add-shape", "slide": slide_id, "shape_type": "RECTANGLE",
            "x": 0, "y": 0, "width": 720, "height": 6, "background_color": COLOR_GREEN,
        },
        # --- HEADER / GABARITO ---
        {
            "op": "add-textbox", "slide": slide_id,
            "text": badge1_text,
            "x": 32, "y": 16, "width": 240, "height": 28,
            "font_size": 10.5, "bold": True, "color": COLOR_GREEN, "background_color": COLOR_GREEN_BG,
            "font_family": FONT_FAMILY, "alignment": "center", "content_alignment": "MIDDLE",
        },
        {
            "op": "add-textbox", "slide": slide_id,
            "text": f"ALTERNATIVA CORRETA:  {correct}",
            "x": 280, "y": 16, "width": 280, "height": 28,
            "font_size": 12, "bold": True, "color": COLOR_GREEN, "background_color": COLOR_GREEN_BG,
            "font_family": FONT_FAMILY, "alignment": "center", "content_alignment": "MIDDLE",
        },
        {
            "op": "add-textbox", "slide": slide_id,
            "text": f"{qid} | {domain}",
            "x": 568, "y": 16, "width": 120, "height": 28,
            "font_size": 9.5, "bold": True, "color": TEXT_MUTED, "background_color": BG_CARD_SUBTLE,
            "font_family": FONT_FAMILY, "alignment": "center", "content_alignment": "MIDDLE",
        },

        # --- COLUNA ESQUERDA: RESOLUÇÃO PASSO A PASSO ---
        {
            "op": "add-shape", "slide": slide_id, "shape_type": "ROUND_RECTANGLE",
            "x": 32, "y": 56, "width": 328, "height": 248,
            "background_color": BG_CARD, "outline_color": BORDER_SUBTLE, "outline_weight": 1.0,
        },
        {
            "op": "add-textbox", "slide": slide_id,
            "text": "RESOLUÇÃO PASSO A PASSO",
            "x": 48, "y": 68, "width": 296, "height": 20,
            "font_size": 10, "bold": True, "color": COLOR_N1, "font_family": FONT_FAMILY,
            "alignment": "left", "content_alignment": "TOP",
        },
        {
            "op": "add-textbox", "slide": slide_id,
            "text": worked_solution,
            "x": 48, "y": 92, "width": 296, "height": 196,
            "font_size": 11, "color": TEXT_PRIMARY, "font_family": FONT_FAMILY,
            "line_spacing": 130, "alignment": "left", "content_alignment": "TOP",
        },

        # --- COLUNA DIREITA: JUSTIFICATIVA & ANÁLISE DE DISTRATOR ---
        {
            "op": "add-shape", "slide": slide_id, "shape_type": "ROUND_RECTANGLE",
            "x": 368, "y": 56, "width": 320, "height": 248,
            "background_color": BG_CARD, "outline_color": BORDER_SUBTLE, "outline_weight": 1.0,
        },
        {
            "op": "add-textbox", "slide": slide_id,
            "text": "JUSTIFICATIVA & DIAGNÓSTICO DE ERRO",
            "x": 384, "y": 68, "width": 288, "height": 20,
            "font_size": 10, "bold": True, "color": COLOR_N2, "font_family": FONT_FAMILY,
            "alignment": "left", "content_alignment": "TOP",
        },
        {
            "op": "add-textbox", "slide": slide_id,
            "text": (
                f"✦ FUNDAMENTO FÍSICO-QUÍMICO:\n{scientific_justification}\n\n"
                f"✦ POR QUE A ALTERNATIVA {wrong_key} É UM ERRO TÍPICO?\n{wrong_rationale}"
            ),
            "x": 384, "y": 92, "width": 288, "height": 196,
            "font_size": typography.ans2_font_size, "color": TEXT_SECONDARY, "font_family": FONT_FAMILY,
            "line_spacing": typography.ans2_line_spacing, "alignment": "left", "content_alignment": "TOP",
        },

        # --- BANNER DE PAGAMENTO NO RODAPÉ ---
        {
            "op": "add-shape", "slide": slide_id, "shape_type": "ROUND_RECTANGLE",
            "x": 32, "y": 318, "width": 656, "height": 68,
            "background_color": COLOR_GREEN_BG, "outline_color": COLOR_GREEN_BORDER, "outline_weight": 1.0,
        },
        {
            "op": "add-textbox", "slide": slide_id,
            "text": (
                "🏆 LIQUIDAÇÃO WINNER TAKES ALL (DESAFIO DE MORTE SÚBITA)"
                if difficulty == 3 else
                "💵 REGRAS DE LIQUIDAÇÃO E PAGAMENTO DA BANCA (RODADA REGULAR)"
            ),
            "x": 48, "y": 324, "width": 624, "height": 20,
            "font_size": 10, "bold": True, "color": COLOR_GREEN_TEXT, "font_family": FONT_FAMILY,
            "alignment": "center", "content_alignment": "MIDDLE",
        },
        {
            "op": "add-textbox", "slide": slide_id,
            "text": (
                "• O grupo com a MAIOR APOSTA entre os que acertaram recolhe TODO O POTE da mesa!\n"
                "• Em caso de empate no maior valor correto: O pote é dividido igualmente  |  Erros: A aposta vai para o Caixa"
                if difficulty == 3 else
                "• 1 a 4 equipes acertaram: Pagamento em DOBRO (×2 / +100% de lucro líquido sobre a aposta)\n"
                "• Todas as 5 equipes acertaram: BÔNUS UNÂNIME de +R$ 100 fixo por equipe  |  Erros: A aposta vai para o Caixa"
            ),
            "x": 48, "y": 344, "width": 624, "height": 36,
            "font_size": 10, "color": "#166534", "font_family": FONT_FAMILY,
            "alignment": "center", "content_alignment": "MIDDLE",
        },
    ]

    notes = (
        f"GABARITO COMENTADO — {badge1_text} ({qid})\n\n"
        f"• Alternativa Correta: {correct}\n"
        f"• Resolução Passo a Passo: {worked_solution}\n"
        f"• Justificativa Físico-Química: {scientific_justification}\n"
        f"• Raciocínio do Distrator ({wrong_key}): {wrong_rationale}\n\n"
        f"DIRETRIZES DE MEDIAÇÃO E PAGAMENTO:\n"
        f"1. Revele a alternativa correta ({correct}) e discuta o erro comum contido na alternativa {wrong_key}.\n"
        f"2. Proceda com a liquidação conforme o regulamento oficial (Dobro, Bônus Unânime ou Winner Takes All).\n"
        f"3. Equipes que escolheram {wrong_key}: Recolha 100% da aposta para a Banca da Casa."
    )
    ops.append({"op": "set-notes", "slide": slide_id, "text": notes})

    return ops


# =============================================================================
# COMPILAÇÃO DE BATCHES E GERADOR MULTI-DECK
# =============================================================================
def generate_deck_batch_operations(
    deck_config: DeckConfig,
    questions_by_id: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    """Compila as operações batch de um deck específico conforme sua configuração."""
    deck_qs = [questions_by_id[qid] for qid in deck_config.question_ids]
    all_ops: list[dict[str, Any]] = []

    # Slide 1: Capa Oficial do Deck
    all_ops.extend(build_cover_operations(deck_config=deck_config, questions=deck_qs))

    # Slides 2i e 2i+1: Pares Q&A intercalados
    for idx, q in enumerate(deck_qs, start=1):
        if deck_config.deck_type == "test":
            lote_label = f"T-{idx:02d}"
        elif deck_config.deck_type == "tiebreaker":
            lote_label = f"S-{idx:02d}"
        elif deck_config.deck_type == "challenge":
            lote_label = "MORTE SÚBITA"
        else:
            # Lotes regulares numerados continuamente se possível
            lote_map = {
                "Q-ATO-002": 1, "Q-SOL-006": 2, "Q-STO-002": 3, "Q-STO-003": 4, "Q-STO-004": 5,
                "Q-STO-005": 6, "Q-ENV-001": 7, "Q-ENV-002": 8, "Q-ENV-003": 9, "Q-ENV-004": 10,
                "Q-SOL-002": 11, "Q-SOL-003": 12, "Q-SOL-004": 13, "Q-SOL-009": 14, "Q-STO-006": 15,
            }
            lote_label = lote_map.get(q["id"], idx)

        all_ops.extend(
            build_question_operations(
                q, lote_num=lote_label, deck_type=deck_config.deck_type, slide_idx=idx
            )
        )
        all_ops.extend(
            build_answer_operations(
                q, lote_num=lote_label, deck_type=deck_config.deck_type, slide_idx=idx
            )
        )

    return all_ops


def generate_batch_operations(
    questions: list[dict[str, Any]],
    deck_config: DeckConfig | None = None,
) -> list[dict[str, Any]]:
    """
    Função de compatibilidade: se deck_config for fornecido, compila o lote do deck;
    se for None, compila a sequência intercalada clássica (41 slides para 20 questões).
    """
    if deck_config is not None:
        qs_by_id = {q["id"]: q for q in questions}
        return generate_deck_batch_operations(deck_config, qs_by_id)

    all_ops: list[dict[str, Any]] = []
    all_ops.extend(build_cover_operations(None))
    for idx, q in enumerate(questions, start=1):
        all_ops.extend(build_question_operations(q, lote_num=idx, slide_idx=idx))
        all_ops.extend(build_answer_operations(q, lote_num=idx, slide_idx=idx))
    return all_ops


def build_manifest(
    deck_configs: list[DeckConfig],
    generated_batches: dict[str, Path]
) -> dict[str, Any]:
    """Constrói o manifesto JSON conforme especificação de contrato do PROJECT.md."""
    manifest = {
        "manifest_version": "2.0",
        "generated_at": datetime.now(UTC).isoformat(),
        "design_system": {
            "background_color": BG_MAIN,
            "card_background": BG_CARD,
            "font_family": FONT_FAMILY,
        },
        "decks": {
            "test_deck": None,
            "challenges": [],
            "regular_decks": [],
            "tiebreaker_deck": None,
        },
    }

    for cfg in deck_configs:
        batch_path = generated_batches.get(cfg.deck_id)
        batch_rel = (
            str(batch_path.relative_to(SCRIPT_DIR)).replace("\\", "/")
            if batch_path
            else f"batch_files/{cfg.batch_filename}"
        )
        total_slides = 1 + len(cfg.question_ids) * 2
        entry = {
            "deck_id": cfg.deck_id,
            "type": cfg.deck_type,
            "presentation_id": cfg.presentation_id or "",
            "title": cfg.title,
            "total_slides": total_slides,
            "question_ids": cfg.question_ids,
            "batch_file": batch_rel,
        }

        if cfg.deck_type == "test":
            manifest["decks"]["test_deck"] = entry
        elif cfg.deck_type == "challenge":
            manifest["decks"]["challenges"].append(entry)
        elif cfg.deck_type == "regular":
            manifest["decks"]["regular_decks"].append(entry)
        elif cfg.deck_type == "tiebreaker":
            manifest["decks"]["tiebreaker_deck"] = entry

    return manifest


def generate_all_decks(
    batch_files_dir: Path = BATCH_FILES_DIR,
    manifest_path: Path = MANIFEST_PATH,
    dry_run: bool = True,
    execute: bool = False,
    selected_deck_id: str | None = None,
) -> dict[str, Any]:
    """
    Executa o pipeline completo:
    1. Carrega todas as 25 questões e valida a partição formal.
    2. Gera os arquivos de batch JSON para cada deck configurado.
    3. Emite o decks_manifest.json estruturado.
    4. Gera o batch legado batch_questoes_n1_n2.json para manter compatibilidade.
    5. Se execute=True, aplica mutações via gslides CLI nas apresentações configuradas.
    """
    all_questions = load_all_questions()
    validate_partition_matrix(DECK_CONFIGS, all_questions)

    batch_files_dir.mkdir(parents=True, exist_ok=True)
    generated_batches: dict[str, Path] = {}

    configs_to_process = (
        [d for d in DECK_CONFIGS if d.deck_id == selected_deck_id]
        if selected_deck_id
        else DECK_CONFIGS
    )

    if not configs_to_process:
        raise ValueError(f"Nenhum deck encontrado com o ID: {selected_deck_id}")

    print(f"\n{'='*75}")
    print(f"GERAÇÃO MULTI-DECK ALL-IN QUÍMICO — MODO: {'EXECUTE' if execute else 'BATCH-ONLY (DRY RUN)'}")
    print(f"{'='*75}")

    for cfg in configs_to_process:
        ops = generate_deck_batch_operations(cfg, all_questions)
        batch_out = batch_files_dir / cfg.batch_filename
        with batch_out.open("w", encoding="utf-8") as f:
            json.dump(ops, f, ensure_ascii=False, indent=2)

        generated_batches[cfg.deck_id] = batch_out
        total_slides = 1 + len(cfg.question_ids) * 2
        print(f"[OK] Deck [{cfg.deck_id}] -> {batch_out.name} ({len(ops)} ops, {total_slides} slides, {len(cfg.question_ids)} Qs)")

        if execute and cfg.presentation_id:
            print(f"  -> Aplicando batch no Google Slides ({cfg.presentation_id})...")
            apply_batch_to_deck(cfg.presentation_id, batch_out)

    manifest_data = build_manifest(DECK_CONFIGS, generated_batches)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest_data, f, ensure_ascii=False, indent=2)
    print(f"\n[OK] Manifesto unificado gerado com sucesso em: {manifest_path}")

    # Gera também o batch legado para compatibilidade contínua de ferramentas
    legacy_qs = load_questions_n1_n2()
    legacy_ops = generate_batch_operations(legacy_qs)
    with DEFAULT_OUTPUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(legacy_ops, f, ensure_ascii=False, indent=2)
    print(f"[OK] Batch legado preservado em: {DEFAULT_OUTPUT_JSON.name} ({len(legacy_ops)} ops)")
    print(f"{'='*75}\n")

    return manifest_data


# =============================================================================
# COMUNICAÇÃO COM O GOOGLE SLIDES API VIA GSLIDES CLI
# =============================================================================
def run_gslides(args: list[str]) -> subprocess.CompletedProcess:
    """Executa comando gslides de forma portável (compatível com Windows .CMD e UTF-8)."""
    gslides_bin = shutil.which("gslides") or "gslides"
    cmd = [gslides_bin] + args
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        shell=True,
        check=False,
    )


def apply_batch_to_deck(presentation_id: str, batch_file: Path) -> None:
    """Aplica o arquivo de batch JSON in-place na apresentação do Google Slides."""
    info_res = run_gslides(["readonly", "info", presentation_id, "--json"])
    if info_res.returncode != 0:
        raise RuntimeError(f"Falha ao inspecionar apresentação {presentation_id}:\n{info_res.stderr}")

    pres_data = json.loads(info_res.stdout)
    slides = pres_data.get("slides", [])
    cleanup_ops: list[dict[str, Any]] = []

    if slides:
        first_slide_elements = [
            el["objectId"]
            for el in slides[0].get("pageElements", [])
            if "objectId" in el
        ]
        for el_id in first_slide_elements:
            cleanup_ops.append({"op": "delete-element", "element": el_id})

        for sl in slides[1:]:
            sl_id = sl.get("objectId")
            if sl_id:
                cleanup_ops.append({"op": "delete-element", "element": sl_id})

    with batch_file.open("r", encoding="utf-8") as f:
        raw_ops = json.load(f)

    filtered_ops = [
        op for op in raw_ops
        if not (op.get("op") == "delete-element" and op.get("element") in ("i0", "i1"))
    ]
    effective_ops = cleanup_ops + filtered_ops

    temp_batch = batch_file.parent / f"_tmp_apply_{batch_file.name}"
    try:
        with temp_batch.open("w", encoding="utf-8") as f:
            json.dump(effective_ops, f, ensure_ascii=False, indent=2)
        res = run_gslides(["mutate", "batch", presentation_id, "-f", str(temp_batch)])
        if res.returncode != 0:
            raise RuntimeError(f"Falha ao executar batchUpdate no Google Slides:\n{res.stderr}")
        print(f"Sucesso: batch aplicado in-place à apresentação {presentation_id}.")
    finally:
        if temp_batch.exists():
            temp_batch.unlink()


# =============================================================================
# CLI ENTRYPOINT
# =============================================================================
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Gerador Multi-Deck de Slides de Perguntas e Respostas — All-In Químico."
    )
    parser.add_argument(
        "--batch-only",
        action="store_true",
        default=True,
        help="Gera exclusivamente os arquivos de batch JSON e o decks_manifest.json (padrão dry-run)",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Executa e aplica as mutações via gslides CLI nas apresentações configuradas",
    )
    parser.add_argument(
        "--deck",
        type=str,
        default=None,
        help="Gera ou executa apenas o deck com o ID especificado",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=MANIFEST_PATH,
        help="Caminho do decks_manifest.json a ser salvo",
    )
    parser.add_argument(
        "--batch-dir",
        type=Path,
        default=BATCH_FILES_DIR,
        help="Diretório onde salvar os arquivos de batch JSON",
    )
    # Argumentos legados preservados para compatibilidade
    parser.add_argument(
        "--presentation-id",
        type=str,
        default=None,
        help="ID de apresentação individual para aplicação legada",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_JSON,
        help="Caminho do arquivo batch JSON legado",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Aplica o batchUpdate diretamente na apresentação via gslides CLI (modo legado)",
    )
    args = parser.parse_args()

    execute_mode = args.execute or args.apply
    dry_run = not execute_mode

    # Se for modo legado com --apply e --presentation-id sem --deck
    if args.apply and args.presentation_id and not args.deck:
        print("Modo legado acionado: gerando batch N1+N2 e aplicando à apresentação informada...")
        questions = load_questions_n1_n2()
        ops = generate_batch_operations(questions)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", encoding="utf-8") as f:
            json.dump(ops, f, ensure_ascii=False, indent=2)
        apply_batch_to_deck(args.presentation_id, args.output)
        return

    generate_all_decks(
        batch_files_dir=args.batch_dir,
        manifest_path=args.manifest,
        dry_run=dry_run,
        execute=execute_mode,
        selected_deck_id=args.deck,
    )


if __name__ == "__main__":
    main()
