"""
Gerador Automatizado de Slides de Perguntas e Respostas — All-In Químico
======================================================================
Compila os cards didáticos das questões oficiais de Nível 1 (Aquecimento) e Nível 2 (Finais)
em uma apresentação do Google Slides rigorosamente intercalada:
  Slide 1: Capa Oficial
  Slide 2i: Pergunta i (Lote 001 a 020)
  Slide 2i+1: Resposta i (Gabarito, Resolução, Justificativa e Regras de Pagamento)
Total: exatamente 41 slides (1 capa + 20 pares Q&A).
Questões de Nível 3 (Morte Súbita / Texas Hold'em) são rigorosamente excluídas.

Design System: Itaú Private / Fintech Clean / CrewDeck Anti-Vibe
- Fundo Off-White (#F8F9FA) de alta acessibilidade visual (WCAG AAA)
- Tipografia sem serifa Open Sans (abertura ampla de olho)
- Respiro matemático de 8px e contenção da carga cognitiva (max-w-prose)
- Psicologia das cores: Azul Cobalto (N1), Laranja Queimado (N2), Verde Esmeralda (Gabarito)
- Duplo Destaque Semântico nos Domínios Químicos e Hierarquia Idêntica para Alternativas [A] e [B]

Uso:
  python gerar_slides_perguntas_respostas.py [--apply] [--presentation-id <ID>] [--output <FILE>]
"""

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

import yaml

# Diretórios base
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
QUESTIONS_DIR = PROJECT_ROOT / "specs" / "SPEC-01-questoes" / "questions"
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

# Dicionários de subscrito e sobrescrito Unicode para renderização química perfeita
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


def clean_chemical_typography(text: Any) -> str:
    """Converte tags HTML e fórmulas em caracteres Unicode limpos e elegantes."""
    if text is None:
        return ""
    s = str(text).strip()

    def _sub(m):
        return "".join(SUBSCRIPTS.get(c, c) for c in m.group(1))

    s = re.sub(r"<sub>(.*?)</sub>", _sub, s, flags=re.IGNORECASE)

    def _sup(m):
        return "".join(SUPERSCRIPTS.get(c, c) for c in m.group(1))

    s = re.sub(r"<sup>(.*?)</sup>", _sup, s, flags=re.IGNORECASE)

    s = s.replace("<->", "⇄").replace("->", "→")
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()


def load_questions_n1_n2() -> list[dict[str, Any]]:
    """
    Carrega estritamente as questões de Nível 1 e Nível 2 dos YAMLs oficiais.
    Garante que o Nível 3 seja estritamente excluído.
    Ordena canonicamente (difficulty, id) para formar os Lotes 001 a 020.
    """
    f_n1 = QUESTIONS_DIR / "nivel_1_aquecimento" / "questoes_nivel_1.yaml"
    f_n2 = QUESTIONS_DIR / "nivel_2_finais" / "questoes_nivel_2.yaml"
    f_n3 = QUESTIONS_DIR / "nivel_3_desafio_morte_subita" / "questoes_nivel_3.yaml"

    if not f_n1.exists():
        raise FileNotFoundError(f"Arquivo de Nível 1 não encontrado: {f_n1}")
    if not f_n2.exists():
        raise FileNotFoundError(f"Arquivo de Nível 2 não encontrado: {f_n2}")

    with f_n1.open(encoding="utf-8") as f:
        data_n1 = yaml.safe_load(f).get("questions", [])

    with f_n2.open(encoding="utf-8") as f:
        data_n2 = yaml.safe_load(f).get("questions", [])

    if len(data_n1) != 13:
        raise ValueError(f"Esperava-se exatamente 13 questões em Nível 1, obteve {len(data_n1)}")
    if len(data_n2) != 7:
        raise ValueError(f"Esperava-se exatamente 7 questões em Nível 2, obteve {len(data_n2)}")

    banned_n3_ids = set()
    if f_n3.exists():
        with f_n3.open(encoding="utf-8") as f:
            data_n3 = yaml.safe_load(f).get("questions", [])
            banned_n3_ids = {q["id"] for q in data_n3}

    combined = []
    for q in data_n1:
        if q["id"] in banned_n3_ids or q.get("difficulty") == 3:
            raise ValueError(f"Violação de integridade: Questão de Nível 3 detectada: {q['id']}")
        q["_source_level"] = 1
        combined.append(q)

    for q in data_n2:
        if q["id"] in banned_n3_ids or q.get("difficulty") == 3:
            raise ValueError(f"Violação de integridade: Questão de Nível 3 detectada: {q['id']}")
        q["_source_level"] = 2
        combined.append(q)

    combined.sort(key=lambda q: (q.get("difficulty", 1), q.get("id", "")))

    if len(combined) != 20:
        raise ValueError(f"Esperava-se exatamente 20 questões combinadas (N1+N2), obteve {len(combined)}")

    return combined


def build_cover_operations() -> list[dict[str, Any]]:
    """Gera as operações do Slide 1 (Capa Oficial do Deck de Q&A — Design Fintech Clean)."""
    ops: list[dict[str, Any]] = [
        {"op": "delete-element", "element": "i0"},
        {"op": "delete-element", "element": "i1"},
        {"op": "set-background", "slide": "p", "color": BG_MAIN},
        # Barra superior de acento institucional (8px)
        {
            "op": "add-shape", "slide": "p", "shape_type": "RECTANGLE",
            "x": 0, "y": 0, "width": 720, "height": 6, "background_color": COLOR_N1,
        },
        # Header Badge
        {
            "op": "add-textbox", "slide": "p",
            "text": "ALL-IN QUÍMICO • DUELO PEDAGÓGICO DE APOSTAS A OU B",
            "x": 35, "y": 20, "width": 650, "height": 24,
            "font_size": 11, "bold": True, "color": COLOR_N1,
            "font_family": FONT_FAMILY, "alignment": "center", "content_alignment": "MIDDLE",
        },
        # Título Principal
        {
            "op": "add-textbox", "slide": "p",
            "text": "CARDS DE PERGUNTAS & RESPOSTAS",
            "x": 35, "y": 44, "width": 650, "height": 48,
            "font_size": 28, "bold": True, "color": TEXT_PRIMARY,
            "font_family": FONT_FAMILY, "alignment": "center", "content_alignment": "MIDDLE",
        },
        # Subtítulo com escopo
        {
            "op": "add-textbox", "slide": "p",
            "text": "Níveis 1 e 2 — 20 Lotes Oficiais Intercalados (40 Slides de Q&A Didático)",
            "x": 35, "y": 94, "width": 650, "height": 26,
            "font_size": 13, "bold": False, "color": TEXT_SECONDARY,
            "font_family": FONT_FAMILY, "alignment": "center", "content_alignment": "MIDDLE",
        },
        # Linha decorativa suave
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
            "header_color": COLOR_N1,
            "header_bg": COLOR_N1_BG,
            "stat_color": COLOR_N1,
            "x": 35,
        },
        {
            "header": "FASE 2: FINAIS",
            "stat": "7 Questões",
            "desc": "Lotes 014 a 020\n• Cálculos Estequiométricos\n• Mistura de Soluções & Diluição\n• Rendimento & Catalisadores\n• Teto de Aposta: R$ 200",
            "header_color": COLOR_N2,
            "header_bg": COLOR_N2_BG,
            "stat_color": COLOR_N2,
            "x": 258,
        },
        {
            "header": "ESTRUTURA DIDÁTICA",
            "stat": "Pergunta ➔ Resposta",
            "desc": "Sequência Contínua de 41 Slides\n• Slide 2i: Pergunta e Opções A / B\n• Slide 2i+1: Gabarito e Resolução\n• Regras oficiais de liquidação\n• Notas completas de orador",
            "header_color": COLOR_GREEN_TEXT,
            "header_bg": COLOR_GREEN_BG,
            "stat_color": COLOR_GREEN,
            "x": 481,
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
        "REGRAS OFICIAIS DE APOSTA: Aposta mínima de R$ 10 e máxima de R$ 200 por rodada nas 5 equipes  |  "
        "Sem placas: decisões registradas em papel  |  "
        "1 a 4 acertos: Lucro de 100% (recebe o dobro ×2)  |  "
        "5 acertos: Bônus Unânime de +R$ 100 fixo  |  "
        "Erros: Valor vai para a Banca da Casa."
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


def build_question_operations(q: dict[str, Any], lote_num: int) -> list[dict[str, Any]]:
    """Gera as operações do Slide de Pergunta (Slide 2i — Grid 2 Colunas Fintech Clean)."""
    lote_str = f"{lote_num:03d}"
    slide_id = f"SLIDE_Q_{lote_str}"
    qid = q.get("id", "")
    difficulty = q.get("difficulty", 1)
    domain = q.get("domain", "")
    domain_name = DOMAIN_NAMES.get(domain, domain)
    cog_level = COGNITIVE_LABELS.get(q.get("cognitive_level", ""), q.get("cognitive_level", ""))

    level_color = COLOR_N1 if difficulty == 1 else COLOR_N2
    level_bg = COLOR_N1_BG if difficulty == 1 else COLOR_N2_BG
    level_name = "NÍVEL 1 (AQUECIMENTO)" if difficulty == 1 else "NÍVEL 2 (FINAIS)"
    dom_color, dom_bg = DOMAIN_STYLES.get(domain, (TEXT_PRIMARY, BG_CARD_SUBTLE))

    statement = clean_chemical_typography(q.get("statement", ""))

    options = q.get("options", [])
    opt_a = next((o for o in options if o.get("key") == "A"), {"text": ""})
    opt_b = next((o for o in options if o.get("key") == "B"), {"text": ""})

    text_a = clean_chemical_typography(opt_a.get("text", ""))
    text_b = clean_chemical_typography(opt_b.get("text", ""))

    ops: list[dict[str, Any]] = [
        {"op": "add-slide", "layout": "BLANK", "id": slide_id},
        {"op": "set-background", "slide": slide_id, "color": BG_MAIN},
        # Barra superior institucional colorida pelo nível (8px)
        {
            "op": "add-shape", "slide": slide_id, "shape_type": "RECTANGLE",
            "x": 0, "y": 0, "width": 720, "height": 6, "background_color": level_color,
        },
        # --- HEADER / METADATA (Duplo Destaque Semântico: Nível + Domínio Químico) ---
        {
            "op": "add-textbox", "slide": slide_id,
            "text": f"LOTE {lote_str}  •  {level_name}",
            "x": 32, "y": 16, "width": 240, "height": 28,
            "font_size": 10.5, "bold": True, "color": level_color, "background_color": level_bg,
            "font_family": FONT_FAMILY, "alignment": "center", "content_alignment": "MIDDLE",
        },
        {
            "op": "add-textbox", "slide": slide_id,
            "text": domain_name,
            "x": 280, "y": 16, "width": 280, "height": 28,
            "font_size": 10.5, "bold": True, "color": dom_color, "background_color": dom_bg,
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
            "text": "QUESTÃO DIDÁTICA",
            "x": 48, "y": 68, "width": 296, "height": 20,
            "font_size": 9.5, "bold": True, "color": level_color, "font_family": FONT_FAMILY,
            "alignment": "left", "content_alignment": "TOP",
        },
        {
            "op": "add-textbox", "slide": slide_id,
            "text": statement,
            "x": 48, "y": 92, "width": 296, "height": 196,
            "font_size": 12, "color": TEXT_PRIMARY, "font_family": FONT_FAMILY,
            "line_spacing": 135, "alignment": "left", "content_alignment": "TOP",
        },

        # --- COLUNA DA DIREITA: CARDS DE ALTERNATIVAS A e B (Hierarquia Visual Idêntica) ---
        # Card Alternativa A
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
            "font_size": 11.5, "bold": True, "color": TEXT_PRIMARY, "font_family": FONT_FAMILY,
            "line_spacing": 130, "alignment": "left", "content_alignment": "TOP",
        },

        # Card Alternativa B (mesma hierarquia tipográfica e cromática para não enviesar a aposta)
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
            "font_size": 11.5, "bold": True, "color": TEXT_PRIMARY, "font_family": FONT_FAMILY,
            "line_spacing": 130, "alignment": "left", "content_alignment": "TOP",
        },

        # --- BARRA DE GOVERNANÇA / APOSTAS NO RODAPÉ ---
        {
            "op": "add-shape", "slide": slide_id, "shape_type": "ROUND_RECTANGLE",
            "x": 32, "y": 318, "width": 656, "height": 68,
            "background_color": BG_CARD, "outline_color": BORDER_SUBTLE, "outline_weight": 1.0,
        },
        {
            "op": "add-textbox", "slide": slide_id,
            "text": "💰 FAÇAM SUAS APOSTAS!  •  TETO MÁXIMO POR RODADA: R$ 200 (MÍNIMO R$ 10)",
            "x": 48, "y": 326, "width": 624, "height": 20,
            "font_size": 10, "bold": True, "color": COLOR_N2, "font_family": FONT_FAMILY,
            "alignment": "center", "content_alignment": "MIDDLE",
        },
        {
            "op": "add-textbox", "slide": slide_id,
            "text": "Registrem na folha de aposta a alternativa escolhida (A ou B) e o valor em dinheiro antes do encerramento do cronômetro.",
            "x": 48, "y": 348, "width": 624, "height": 28,
            "font_size": 10, "color": TEXT_MUTED, "font_family": FONT_FAMILY,
            "alignment": "center", "content_alignment": "MIDDLE",
        },
    ]

    skill = q.get("skill", "Não especificada")
    concepts = ", ".join(q.get("concept_refs", [])) or "Gerais"
    formulas = ", ".join(q.get("formula_refs", [])) or "Sem fórmula específica"

    notes = (
        f"CARD DE PERGUNTA — LOTE {lote_str} ({qid})\n\n"
        f"• Nível: {level_name} (Dificuldade {difficulty})\n"
        f"• Domínio: {domain_name} ({domain})\n"
        f"• Habilidade Pedagógica: {skill}\n"
        f"• Nível Cognitivo: {cog_level}\n"
        f"• Conceitos da Base: {concepts}\n"
        f"• Fórmulas de Referência: {formulas}\n\n"
        f"INSTRUÇÕES DE APLICAÇÃO PARA O PROFESSOR:\n"
        f"1. Projete este slide e faça a leitura clara do enunciado e das duas opções.\n"
        f"2. Conceda de 60 a 90 segundos para debate interno em cada equipe de estudantes.\n"
        f"3. Lembre a turma do teto de aposta de R$ 200 e da obrigatoriedade do registro por escrito.\n"
        f"4. Recolha ou confira visualmente todas as folhas de resposta antes de avançar para o gabarito."
    )
    ops.append({"op": "set-notes", "slide": slide_id, "text": notes})

    return ops


def build_answer_operations(q: dict[str, Any], lote_num: int) -> list[dict[str, Any]]:
    """Gera as operações do Slide de Resposta (Slide 2i+1 — Gabarito & Resolução Fintech Clean)."""
    lote_str = f"{lote_num:03d}"
    slide_id = f"SLIDE_A_{lote_str}"
    qid = q.get("id", "")
    correct = q.get("correct", "A").upper()
    domain = q.get("domain", "")

    worked_solution = clean_chemical_typography(q.get("worked_solution", ""))
    scientific_justification = clean_chemical_typography(q.get("scientific_justification", ""))

    options = q.get("options", [])
    wrong_key = "B" if correct == "A" else "A"
    wrong_opt = next((o for o in options if o.get("key") == wrong_key), {})
    wrong_rationale = clean_chemical_typography(wrong_opt.get("rationale", "Alternativa incorreta."))

    ops: list[dict[str, Any]] = [
        {"op": "add-slide", "layout": "BLANK", "id": slide_id},
        {"op": "set-background", "slide": slide_id, "color": BG_MAIN},
        # Barra superior verde esmeralda (8px)
        {
            "op": "add-shape", "slide": slide_id, "shape_type": "RECTANGLE",
            "x": 0, "y": 0, "width": 720, "height": 6, "background_color": COLOR_GREEN,
        },
        # --- HEADER / GABARITO ---
        {
            "op": "add-textbox", "slide": slide_id,
            "text": f"GABARITO OFICIAL  •  LOTE {lote_str}",
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
            "font_size": 10.5, "color": TEXT_SECONDARY, "font_family": FONT_FAMILY,
            "line_spacing": 130, "alignment": "left", "content_alignment": "TOP",
        },

        # --- BANNER DE PAGAMENTO NO RODAPÉ ---
        {
            "op": "add-shape", "slide": slide_id, "shape_type": "ROUND_RECTANGLE",
            "x": 32, "y": 318, "width": 656, "height": 68,
            "background_color": COLOR_GREEN_BG, "outline_color": COLOR_GREEN_BORDER, "outline_weight": 1.0,
        },
        {
            "op": "add-textbox", "slide": slide_id,
            "text": "💵 REGRAS DE LIQUIDAÇÃO E PAGAMENTO DA BANCA (RODADA REGULAR)",
            "x": 48, "y": 324, "width": 624, "height": 20,
            "font_size": 10, "bold": True, "color": COLOR_GREEN_TEXT, "font_family": FONT_FAMILY,
            "alignment": "center", "content_alignment": "MIDDLE",
        },
        {
            "op": "add-textbox", "slide": slide_id,
            "text": (
                "• 1 a 4 equipes acertaram: Pagamento em DOBRO (×2 / +100% de lucro líquido sobre a aposta)\n"
                "• Todas as 5 equipes acertaram: BÔNUS UNÂNIME de +R$ 100 fixo por equipe  |  Erros: A aposta vai para o Caixa"
            ),
            "x": 48, "y": 344, "width": 624, "height": 36,
            "font_size": 10, "color": "#166534", "font_family": FONT_FAMILY,
            "alignment": "center", "content_alignment": "MIDDLE",
        },
    ]

    notes = (
        f"GABARITO COMENTADO — LOTE {lote_str} ({qid})\n\n"
        f"• Alternativa Correta: {correct}\n"
        f"• Resolução Passo a Passo: {worked_solution}\n"
        f"• Justificativa Físico-Química: {scientific_justification}\n"
        f"• Raciocínio do Distrator ({wrong_key}): {wrong_rationale}\n\n"
        f"DIRETRIZES DE MEDIAÇÃO E PAGAMENTO:\n"
        f"1. Revele a alternativa correta ({correct}) e discuta o erro comum contido na alternativa {wrong_key}.\n"
        f"2. Se 1 a 4 grupos acertaram: Entregue o valor apostado em dobro (lucro de +100%).\n"
        f"3. Se todas as 5 equipes acertaram: Anuncie o Bônus Unânime (+R$ 100 fixo para cada grupo).\n"
        f"4. Grupos que escolheram {wrong_key}: Recolha 100% da quantia apostada para a Banca da Casa."
    )
    ops.append({"op": "set-notes", "slide": slide_id, "text": notes})

    return ops


def generate_batch_operations(questions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Compila a lista completa de operações para os 41 slides do deck de Q&A."""
    all_ops: list[dict[str, Any]] = []

    all_ops.extend(build_cover_operations())

    for idx, q in enumerate(questions, start=1):
        all_ops.extend(build_question_operations(q, lote_num=idx))
        all_ops.extend(build_answer_operations(q, lote_num=idx))

    return all_ops


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
    )


def apply_batch_to_deck(presentation_id: str, batch_file: Path) -> None:
    """Aplica o arquivo de batch JSON in-place na apresentação do Google Slides (limpando slides anteriores se existirem)."""
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

    # Remove deleções hardcoded de placeholders iniciais (i0/i1) que já estão cobertas pelo cleanup dinâmico
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


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Gera apresentação sequencial de Perguntas e Respostas no Google Slides."
    )
    parser.add_argument(
        "--presentation-id",
        type=str,
        default="10HrhJkrYDnxwhCP6HEo75DWvU9NS2RHXmp2wcx8XZUk",
        help="ID da apresentação no Google Slides",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_JSON,
        help="Caminho do arquivo batch JSON a ser salvo",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Aplica o batchUpdate diretamente na apresentação via gslides CLI",
    )
    args = parser.parse_args()

    print("Carregando banco de questões de Nível 1 e Nível 2...")
    questions = load_questions_n1_n2()
    print(f"Carregadas {len(questions)} questões (13 N1 + 7 N2). Nível 3 excluído com sucesso.")

    print("Gerando operações batch no Design System Fintech Clean...")
    ops = generate_batch_operations(questions)
    print(f"Total de operações geradas: {len(ops)}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        json.dump(ops, f, ensure_ascii=False, indent=2)
    print(f"Arquivo batch salvo com sucesso em: {args.output}")

    if args.apply:
        print(f"Aplicando lote à apresentação no Google Slides: {args.presentation_id}")
        apply_batch_to_deck(args.presentation_id, args.output)


if __name__ == "__main__":
    main()
