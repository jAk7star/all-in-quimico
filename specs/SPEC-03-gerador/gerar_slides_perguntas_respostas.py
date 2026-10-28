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

Uso:
  python gerar_slides_perguntas_respostas.py [--create] [--presentation-id <ID>] [--output <FILE>]
"""

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

import yaml

# Diretórios base
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
QUESTIONS_DIR = PROJECT_ROOT / "specs" / "SPEC-01-questoes" / "questions"
DEFAULT_OUTPUT_JSON = SCRIPT_DIR / "batch_questoes_n1_n2.json"

# Paleta Visual Oficial (Dark Navy / Slate / Gold / Cyan / Emerald / Red)
BG_DARK = "#0F172A"  # Slate 900 (fundo principal)
BG_CARD = "#1E293B"  # Slate 800 (card de conteúdo)
BG_CARD_ALT = "#172554"  # Blue 950 (card de opções e destaques)
BG_HEADER = "#090D16"  # Slate 950 (cabeçalhos)
GOLD = "#F59E0B"  # Amber 500 (ouro, Nível 2 e destaques)
CYAN = "#38BDF8"  # Sky 400 (ciano, Nível 1 e títulos secundários)
GREEN = "#22C55E"  # Emerald 500 (acerto, gabarito e lucro)
GREEN_BG = "#064E3B"  # Emerald 900 (fundo do gabarito e pagamento)
RED = "#EF4444"  # Red 500 (distrator e erros)
RED_BG = "#7F1D1D"  # Red 900 (fundo de aviso de erro)
WHITE = "#FFFFFF"  # Branco (texto principal)
MUTED = "#CBD5E1"  # Slate 300 (texto secundário/explicações)

# Mapeamento de domínios químicos para nomes pedagógicos
DOMAIN_NAMES = {
    "CHEM-ATO": "Estrutura Atômica & Tabela Periódica",
    "CHEM-ENV": "Química Ambiental & Sustentabilidade",
    "CHEM-SOL": "Soluções & Concentrações Químicas",
    "CHEM-STO": "Estequiometria & Quantidade de Matéria",
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
    "0": "₀",
    "1": "₁",
    "2": "₂",
    "3": "₃",
    "4": "₄",
    "5": "₅",
    "6": "₆",
    "7": "₇",
    "8": "₈",
    "9": "₉",
    "+": "₊",
    "-": "₋",
    "=": "₌",
    "(": "₍",
    ")": "₎",
    "a": "ₐ",
    "e": "ₑ",
    "o": "ₒ",
    "x": "ₓ",
    "i": "ᵢ",
}

SUPERSCRIPTS = {
    "0": "⁰",
    "1": "¹",
    "2": "²",
    "3": "³",
    "4": "⁴",
    "5": "⁵",
    "6": "⁶",
    "7": "⁷",
    "8": "⁸",
    "9": "⁹",
    "+": "⁺",
    "-": "⁻",
    "=": "⁼",
    "(": "⁽",
    ")": "⁾",
    "n": "ⁿ",
}


def clean_chemical_typography(text: Any) -> str:
    """Converte tags HTML e fórmulas em caracteres Unicode limpos e elegantes."""
    if text is None:
        return ""
    s = str(text).strip()

    # Substitui tags <sub>...</sub> por caracteres subscritos Unicode
    def _sub(m):
        return "".join(SUBSCRIPTS.get(c, c) for c in m.group(1))

    s = re.sub(r"<sub>(.*?)</sub>", _sub, s, flags=re.IGNORECASE)

    # Substitui tags <sup>...</sup> por caracteres sobrescritos Unicode
    def _sup(m):
        return "".join(SUPERSCRIPTS.get(c, c) for c in m.group(1))

    s = re.sub(r"<sup>(.*?)</sup>", _sup, s, flags=re.IGNORECASE)

    # Substitui setas simples por caracteres Unicode (ordena pelo mais longo primeiro)
    s = s.replace("<->", "⇄").replace("->", "→")

    # Remove quaisquer tags HTML residuais
    s = re.sub(r"<[^>]+>", "", s)

    # Normaliza espaços múltiplos
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

    # Verificação defensiva de integridade
    if len(data_n1) != 13:
        raise ValueError(
            f"Esperava-se exatamente 13 questões em Nível 1, obteve {len(data_n1)}"
        )
    if len(data_n2) != 7:
        raise ValueError(
            f"Esperava-se exatamente 7 questões em Nível 2, obteve {len(data_n2)}"
        )

    # Carrega IDs proibidos de Nível 3 para validação estrita
    banned_n3_ids = set()
    if f_n3.exists():
        with f_n3.open(encoding="utf-8") as f:
            data_n3 = yaml.safe_load(f).get("questions", [])
            banned_n3_ids = {q["id"] for q in data_n3}

    combined = []
    for q in data_n1:
        if q["id"] in banned_n3_ids or q.get("difficulty") == 3:
            raise ValueError(
                f"Violação de integridade: Questão de Nível 3 detectada: {q['id']}"
            )
        q["_source_level"] = 1
        combined.append(q)

    for q in data_n2:
        if q["id"] in banned_n3_ids or q.get("difficulty") == 3:
            raise ValueError(
                f"Violação de integridade: Questão de Nível 3 detectada: {q['id']}"
            )
        q["_source_level"] = 2
        combined.append(q)

    # Ordenação canônica idêntica à do gerador oficial (difficulty, id)
    combined.sort(key=lambda q: (q.get("difficulty", 1), q.get("id", "")))

    if len(combined) != 20:
        raise ValueError(
            f"Esperava-se exatamente 20 questões combinadas (N1+N2), obteve {len(combined)}"
        )

    return combined


def build_cover_operations() -> list[dict[str, Any]]:
    """Gera as operações do Slide 1 (Capa Oficial do Deck de Q&A)."""
    ops: list[dict[str, Any]] = [
        {"op": "delete-element", "element": "i0"},
        {"op": "delete-element", "element": "i1"},
        {"op": "set-background", "slide": "p", "color": BG_DARK},
        {
            "op": "add-shape",
            "slide": "p",
            "shape_type": "RECTANGLE",
            "x": 0,
            "y": 0,
            "width": 720,
            "height": 8,
            "background_color": GOLD,
        },
        # Header Badge
        {
            "op": "add-textbox",
            "slide": "p",
            "text": "ALL-IN QUÍMICO • DUELO DE APOSTAS A OU B",
            "x": 35,
            "y": 24,
            "width": 650,
            "height": 22,
            "font_size": 11,
            "bold": True,
            "color": CYAN,
            "font_family": "Montserrat",
            "alignment": "center",
        },
        # Título Principal
        {
            "op": "add-textbox",
            "slide": "p",
            "text": "CARDS DE PERGUNTAS & RESPOSTAS",
            "x": 35,
            "y": 48,
            "width": 650,
            "height": 52,
            "font_size": 28,
            "bold": True,
            "color": WHITE,
            "font_family": "Montserrat",
            "alignment": "center",
        },
        # Subtítulo com escopo
        {
            "op": "add-textbox",
            "slide": "p",
            "text": "Níveis 1 e 2 — 20 Lotes Oficiais Intercalados (40 Slides de Q&A Didático)",
            "x": 35,
            "y": 102,
            "width": 650,
            "height": 26,
            "font_size": 13,
            "bold": False,
            "color": GOLD,
            "font_family": "Roboto",
            "alignment": "center",
        },
        # Linha decorativa
        {
            "op": "add-shape",
            "slide": "p",
            "shape_type": "RECTANGLE",
            "x": 260,
            "y": 134,
            "width": 200,
            "height": 3,
            "background_color": CYAN,
        },
    ]

    # 3 Cards de Visão Geral
    cards = [
        {
            "header": "FASE 1: AQUECIMENTO",
            "stat": "13 Questões",
            "desc": "Lotes 001 a 013\n• Estrutura Atômica\n• Soluções & Concentrações\n• Química Ambiental & Estequiometria\n• Teto de Aposta: R$ 200",
            "color": CYAN,
            "stat_bg": BG_CARD_ALT,
            "x": 35,
        },
        {
            "header": "FASE 2: FINAIS",
            "stat": "7 Questões",
            "desc": "Lotes 014 a 020\n• Cálculos Estequiométricos\n• Mistura de Soluções & Diluição\n• Rendimento & Catalisadores\n• Teto de Aposta: R$ 200",
            "color": GOLD,
            "stat_bg": BG_CARD_ALT,
            "x": 258,
        },
        {
            "header": "ESTRUTURA DIDÁTICA",
            "stat": "Pergunta ➔ Resposta",
            "desc": "Sequência Contínua de 41 Slides\n• Slide 2i: Pergunta e Opções A / B\n• Slide 2i+1: Gabarito e Resolução\n• Regras oficiais de pagamento\n• Notas completas de orador",
            "color": GREEN,
            "stat_bg": GREEN_BG,
            "x": 481,
        },
    ]

    for c in cards:
        cx = c["x"]
        ops.extend(
            [
                {
                    "op": "add-textbox",
                    "slide": "p",
                    "text": c["header"],
                    "x": cx,
                    "y": 150,
                    "width": 204,
                    "height": 28,
                    "font_size": 10.5,
                    "bold": True,
                    "color": c["color"],
                    "background_color": BG_CARD,
                    "font_family": "Montserrat",
                    "alignment": "center",
                    "content_alignment": "MIDDLE",
                },
                {
                    "op": "add-textbox",
                    "slide": "p",
                    "text": c["stat"],
                    "x": cx,
                    "y": 178,
                    "width": 204,
                    "height": 40,
                    "font_size": 17,
                    "bold": True,
                    "color": WHITE,
                    "background_color": c["stat_bg"],
                    "font_family": "Montserrat",
                    "alignment": "center",
                    "content_alignment": "MIDDLE",
                },
                {
                    "op": "add-textbox",
                    "slide": "p",
                    "text": c["desc"],
                    "x": cx,
                    "y": 218,
                    "width": 204,
                    "height": 88,
                    "font_size": 9.5,
                    "color": MUTED,
                    "background_color": BG_CARD,
                    "font_family": "Roboto",
                    "alignment": "center",
                    "content_alignment": "MIDDLE",
                },
            ]
        )

    # Banner de regras oficiais de rodada no rodapé da capa
    footer_text = (
        "REGRAS OFICIAIS DE APOSTA: Aposta mínima de R$ 10 e máxima de R$ 200 por rodada nas 5 equipes  |  "
        "Sem placas: decisões registradas em papel  |  "
        "1 a 4 acertos: Lucro de 100% (recebe o dobro ×2)  |  "
        "5 acertos: Bônus Unânime de +R$ 100 fixo  |  "
        "Erros: Valor vai para a Banca da Casa."
    )
    ops.extend(
        [
            {
                "op": "add-textbox",
                "slide": "p",
                "text": footer_text,
                "x": 35,
                "y": 320,
                "width": 650,
                "height": 65,
                "font_size": 9.5,
                "bold": True,
                "color": WHITE,
                "background_color": "#0B132B",
                "font_family": "Roboto",
                "alignment": "center",
                "content_alignment": "MIDDLE",
            },
            {
                "op": "set-notes",
                "slide": "p",
                "text": (
                    "SLIDE DE ABERTURA — ALL-IN QUÍMICO: CARDS DE PERGUNTAS E RESPOSTAS\n\n"
                    "Apresentação oficial contendo exatamente os 20 lotes de questões dos Níveis 1 (Aquecimento) e 2 (Finais).\n"
                    "Organização em pares estritos: cada slide de pergunta N é sucedido imediatamente pelo gabarito e resolução comentada N correspondente.\n"
                    "Deck restrito e delimitado exclusivamente aos Níveis 1 e 2, conforme regulamento oficial de aplicação em sala."
                ),
            },
        ]
    )

    return ops


def build_question_operations(q: dict[str, Any], lote_num: int) -> list[dict[str, Any]]:
    """Gera as operações do Slide de Pergunta (Slide 2i)."""
    lote_str = f"{lote_num:03d}"
    slide_id = f"SLIDE_Q_{lote_str}"
    qid = q.get("id", "")
    difficulty = q.get("difficulty", 1)
    domain = q.get("domain", "")
    domain_name = DOMAIN_NAMES.get(domain, domain)
    cog_level = COGNITIVE_LABELS.get(
        q.get("cognitive_level", ""), q.get("cognitive_level", "")
    )

    level_color = CYAN if difficulty == 1 else GOLD
    level_name = "NÍVEL 1 — AQUECIMENTO" if difficulty == 1 else "NÍVEL 2 — FINAIS"

    statement = clean_chemical_typography(q.get("statement", ""))

    # Extrai opções A e B
    options = q.get("options", [])
    opt_a = next((o for o in options if o.get("key") == "A"), {"text": ""})
    opt_b = next((o for o in options if o.get("key") == "B"), {"text": ""})

    text_a = clean_chemical_typography(opt_a.get("text", ""))
    text_b = clean_chemical_typography(opt_b.get("text", ""))

    ops: list[dict[str, Any]] = [
        {"op": "add-slide", "layout": "BLANK", "id": slide_id},
        {"op": "set-background", "slide": slide_id, "color": BG_DARK},
        # Barra superior colorida pelo nível
        {
            "op": "add-shape",
            "slide": slide_id,
            "shape_type": "RECTANGLE",
            "x": 0,
            "y": 0,
            "width": 720,
            "height": 6,
            "background_color": level_color,
        },
        # Topo - Badge de Lote & Nível
        {
            "op": "add-textbox",
            "slide": slide_id,
            "text": f"LOTE {lote_str}  •  {level_name}",
            "x": 30,
            "y": 12,
            "width": 220,
            "height": 30,
            "font_size": 11,
            "bold": True,
            "color": level_color,
            "background_color": BG_CARD,
            "font_family": "Montserrat",
            "alignment": "center",
            "content_alignment": "MIDDLE",
        },
        # Topo - Domínio Temático
        {
            "op": "add-textbox",
            "slide": slide_id,
            "text": f"DOMÍNIO: {domain_name}",
            "x": 260,
            "y": 12,
            "width": 300,
            "height": 30,
            "font_size": 10.5,
            "bold": True,
            "color": WHITE,
            "background_color": BG_CARD,
            "font_family": "Roboto",
            "alignment": "left",
            "content_alignment": "MIDDLE",
        },
        # Topo - ID da Questão e Nível Cognitivo
        {
            "op": "add-textbox",
            "slide": slide_id,
            "text": f"{qid}  |  {cog_level}",
            "x": 570,
            "y": 12,
            "width": 120,
            "height": 30,
            "font_size": 9.5,
            "bold": True,
            "color": CYAN,
            "background_color": BG_CARD_ALT,
            "font_family": "Roboto",
            "alignment": "center",
            "content_alignment": "MIDDLE",
        },
        # Card do Enunciado
        {
            "op": "add-textbox",
            "slide": slide_id,
            "text": "ENUNCIADO DA QUESTÃO:",
            "x": 30,
            "y": 48,
            "width": 660,
            "height": 20,
            "font_size": 9.5,
            "bold": True,
            "color": GOLD,
            "background_color": BG_CARD,
            "font_family": "Montserrat",
            "alignment": "left",
            "content_alignment": "MIDDLE",
        },
        {
            "op": "add-textbox",
            "slide": slide_id,
            "text": statement,
            "x": 30,
            "y": 68,
            "width": 660,
            "height": 104,
            "font_size": 12.5,
            "color": WHITE,
            "background_color": BG_CARD,
            "font_family": "Roboto",
            "alignment": "left",
            "content_alignment": "TOP",
        },
        # Card da Alternativa A
        {
            "op": "add-textbox",
            "slide": slide_id,
            "text": "ALTERNATIVA A",
            "x": 30,
            "y": 180,
            "width": 320,
            "height": 26,
            "font_size": 11.5,
            "bold": True,
            "color": CYAN,
            "background_color": "#1E3A8A",
            "font_family": "Montserrat",
            "alignment": "center",
            "content_alignment": "MIDDLE",
        },
        {
            "op": "add-textbox",
            "slide": slide_id,
            "text": text_a,
            "x": 30,
            "y": 206,
            "width": 320,
            "height": 106,
            "font_size": 11,
            "color": WHITE,
            "background_color": BG_CARD_ALT,
            "font_family": "Roboto",
            "alignment": "left",
            "content_alignment": "TOP",
        },
        # Card da Alternativa B
        {
            "op": "add-textbox",
            "slide": slide_id,
            "text": "ALTERNATIVA B",
            "x": 370,
            "y": 180,
            "width": 320,
            "height": 26,
            "font_size": 11.5,
            "bold": True,
            "color": CYAN,
            "background_color": "#1E3A8A",
            "font_family": "Montserrat",
            "alignment": "center",
            "content_alignment": "MIDDLE",
        },
        {
            "op": "add-textbox",
            "slide": slide_id,
            "text": text_b,
            "x": 370,
            "y": 206,
            "width": 320,
            "height": 106,
            "font_size": 11,
            "color": WHITE,
            "background_color": BG_CARD_ALT,
            "font_family": "Roboto",
            "alignment": "left",
            "content_alignment": "TOP",
        },
        # Banner de Aposta no Rodapé
        {
            "op": "add-textbox",
            "slide": slide_id,
            "text": (
                "💰 FAÇAM SUAS APOSTAS!  |  MÍNIMO: R$ 10  •  TETO MÁXIMO POR RODADA: R$ 200\n"
                "Preencham a folha de aposta com a alternativa escolhida (A ou B) e o valor em dinheiro antes do tempo esgotar!"
            ),
            "x": 30,
            "y": 322,
            "width": 660,
            "height": 65,
            "font_size": 10,
            "bold": True,
            "color": GOLD,
            "background_color": "#0B132B",
            "font_family": "Roboto",
            "alignment": "center",
            "content_alignment": "MIDDLE",
        },
    ]

    # Notas de Orador Pedagógicas
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
    """Gera as operações do Slide de Resposta (Slide 2i+1)."""
    lote_str = f"{lote_num:03d}"
    slide_id = f"SLIDE_A_{lote_str}"
    qid = q.get("id", "")
    correct = q.get("correct", "A").upper()
    domain = q.get("domain", "")

    worked_solution = clean_chemical_typography(q.get("worked_solution", ""))
    scientific_justification = clean_chemical_typography(
        q.get("scientific_justification", "")
    )

    # Análise da alternativa errada (distrator)
    options = q.get("options", [])
    wrong_key = "B" if correct == "A" else "A"
    wrong_opt = next((o for o in options if o.get("key") == wrong_key), {})
    wrong_rationale = clean_chemical_typography(
        wrong_opt.get("rationale", "Alternativa incorreta.")
    )

    ops: list[dict[str, Any]] = [
        {"op": "add-slide", "layout": "BLANK", "id": slide_id},
        {"op": "set-background", "slide": slide_id, "color": BG_DARK},
        # Barra superior verde esmeralda
        {
            "op": "add-shape",
            "slide": slide_id,
            "shape_type": "RECTANGLE",
            "x": 0,
            "y": 0,
            "width": 720,
            "height": 6,
            "background_color": GREEN,
        },
        # Topo - Badge de Gabarito
        {
            "op": "add-textbox",
            "slide": slide_id,
            "text": f"GABARITO OFICIAL  •  LOTE {lote_str}",
            "x": 30,
            "y": 12,
            "width": 220,
            "height": 30,
            "font_size": 11,
            "bold": True,
            "color": GREEN,
            "background_color": GREEN_BG,
            "font_family": "Montserrat",
            "alignment": "center",
            "content_alignment": "MIDDLE",
        },
        # Topo - Destaque da Alternativa Correta
        {
            "op": "add-textbox",
            "slide": slide_id,
            "text": f"ALTERNATIVA CORRETA:  {correct}",
            "x": 260,
            "y": 12,
            "width": 300,
            "height": 30,
            "font_size": 13,
            "bold": True,
            "color": "#4ADE80",
            "background_color": GREEN_BG,
            "font_family": "Montserrat",
            "alignment": "center",
            "content_alignment": "MIDDLE",
        },
        # Topo - ID da Questão
        {
            "op": "add-textbox",
            "slide": slide_id,
            "text": f"{qid}  |  {domain}",
            "x": 570,
            "y": 12,
            "width": 120,
            "height": 30,
            "font_size": 9.5,
            "bold": True,
            "color": MUTED,
            "background_color": BG_CARD,
            "font_family": "Roboto",
            "alignment": "center",
            "content_alignment": "MIDDLE",
        },
        # Coluna Esquerda: Resolução Passo a Passo
        {
            "op": "add-textbox",
            "slide": slide_id,
            "text": "RESOLUÇÃO PASSO A PASSO",
            "x": 30,
            "y": 48,
            "width": 320,
            "height": 26,
            "font_size": 11,
            "bold": True,
            "color": GOLD,
            "background_color": "#0F172A",
            "font_family": "Montserrat",
            "alignment": "center",
            "content_alignment": "MIDDLE",
        },
        {
            "op": "add-textbox",
            "slide": slide_id,
            "text": worked_solution,
            "x": 30,
            "y": 74,
            "width": 320,
            "height": 238,
            "font_size": 11,
            "color": WHITE,
            "background_color": BG_CARD,
            "font_family": "Roboto",
            "alignment": "left",
            "content_alignment": "TOP",
        },
        # Coluna Direita: Justificativa Científica e Análise de Distrator
        {
            "op": "add-textbox",
            "slide": slide_id,
            "text": "JUSTIFICATIVA & ANÁLISE DE ERROS",
            "x": 370,
            "y": 48,
            "width": 320,
            "height": 26,
            "font_size": 11,
            "bold": True,
            "color": CYAN,
            "background_color": "#0F172A",
            "font_family": "Montserrat",
            "alignment": "center",
            "content_alignment": "MIDDLE",
        },
        {
            "op": "add-textbox",
            "slide": slide_id,
            "text": (
                f"✦ JUSTIFICATIVA FÍSICO-QUÍMICA:\n{scientific_justification}\n\n"
                f"✦ POR QUE A ALTERNATIVA {wrong_key} É UM ERRO TÍPICO?\n{wrong_rationale}"
            ),
            "x": 370,
            "y": 74,
            "width": 320,
            "height": 238,
            "font_size": 10.5,
            "color": WHITE,
            "background_color": BG_CARD,
            "font_family": "Roboto",
            "alignment": "left",
            "content_alignment": "TOP",
        },
        # Banner de Pagamento no Rodapé
        {
            "op": "add-textbox",
            "slide": slide_id,
            "text": (
                "💵 REGRAS DE PAGAMENTO DA BANCA PARA ESTA RODADA:\n"
                "• 1 a 4 equipes acertaram: Pagamento em DOBRO (×2 / +100% de lucro líquido sobre a aposta)\n"
                "• Todas as 5 equipes acertaram: BÔNUS UNÂNIME de +R$ 100 fixo por equipe  |  Erros: Aposta vai para o Caixa"
            ),
            "x": 30,
            "y": 322,
            "width": 660,
            "height": 65,
            "font_size": 9.5,
            "bold": True,
            "color": WHITE,
            "background_color": GREEN_BG,
            "font_family": "Roboto",
            "alignment": "center",
            "content_alignment": "MIDDLE",
        },
    ]

    # Notas de Orador Pedagógicas
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

    # Slide 1: Capa Oficial
    all_ops.extend(build_cover_operations())

    # Slides 2 a 41: Pares intercalados Pergunta / Resposta
    for idx, q in enumerate(questions, start=1):
        # Slide 2i: Pergunta
        all_ops.extend(build_question_operations(q, lote_num=idx))
        # Slide 2i+1: Resposta
        all_ops.extend(build_answer_operations(q, lote_num=idx))

    return all_ops


import shutil


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
        check=True,
        shell=True,
    )


def create_google_slides_deck(
    title: str = "All-In Químico — Cards de Perguntas e Respostas (Níveis 1 e 2)",
) -> str:
    """Cria uma nova apresentação no Google Slides via gslides CLI e retorna o ID."""
    print(f"Criando apresentação: {title}")
    res = run_gslides(["mutate", "create", "--title", title, "--json"])
    stdout = res.stdout.strip()
    print(f"Saída create: {stdout}")

    # 1. Tenta extrair ID via Regex "(ID: ...)"
    m = re.search(r"\(ID:\s*([a-zA-Z0-9_-]+)\)", stdout)
    if m:
        pres_id = m.group(1)
        print(f"Apresentação criada com sucesso! ID: {pres_id}")
        return pres_id

    # 2. Tenta extrair caso o output seja JSON
    try:
        out = json.loads(stdout)
        pres_id = out.get("presentationId") or out.get("id")
        if pres_id:
            print(f"Apresentação criada com sucesso! ID: {pres_id}")
            return pres_id
    except (json.JSONDecodeError, KeyError, AttributeError):
        pass

    # 3. Fallback: qualquer padrão de ID alfanumérico longo
    m2 = re.search(r"ID:\s*([a-zA-Z0-9_-]{20,})", stdout)
    if m2:
        pres_id = m2.group(1)
        print(f"Apresentação criada com sucesso! ID: {pres_id}")
        return pres_id

    raise RuntimeError(
        f"Não foi possível obter o ID da apresentação criada. Saída: {stdout}"
    )


def apply_batch_operations(
    presentation_id: str, batch_file: Path, chunk_size: int = 150
) -> None:
    """
    Aplica as operações de batch no Google Slides.
    Se a lista for muito longa, subdivide em chunks mantendo a integridade referencial.
    Nota: no nosso caso, as referências 'add-slide' criam IDs que são usados nos slides subsequentes.
    Como os IDs são definidos no momento de criação de cada slide, agrupamos slides inteiros por chunk!
    """
    with batch_file.open("r", encoding="utf-8") as f:
        ops = json.load(f)

    print(f"Total de operações no batch: {len(ops)}")

    # Agrupa operações por slide para garantir que add-slide e seus elementos fiquem juntos
    slide_groups: list[list[dict[str, Any]]] = []
    current_group: list[dict[str, Any]] = []

    for op in ops:
        if op.get("op") == "add-slide" and current_group:
            slide_groups.append(current_group)
            current_group = [op]
        else:
            current_group.append(op)
    if current_group:
        slide_groups.append(current_group)

    print(f"Total de slides agrupados: {len(slide_groups)}")

    # O CLI gslides mutate batch processou 881 operações de uma vez no teste de cenários.
    # Tentamos primeiro enviar o batch completo. Caso haja erro de timeout, particionamos.
    try:
        print(
            f"Enviando batch completo ({len(ops)} operações) para {presentation_id}..."
        )
        run_gslides(
            ["mutate", "batch", presentation_id, "-f", str(batch_file), "--json"]
        )
        print("Batch completo aplicado com sucesso!")
        return
    except subprocess.CalledProcessError as err:
        print(
            f"Aviso: Erro ao aplicar batch completo ({err}). Tentando envio particionado por grupos de slides..."
        )
        print(f"Stderr: {err.stderr}")

    # Envio particionado: agrupa em lotes de ~10 slides por chamada
    temp_dir = batch_file.parent / "temp_batches"
    temp_dir.mkdir(exist_ok=True)

    chunk_slides = 10
    for chunk_idx in range(0, len(slide_groups), chunk_slides):
        chunk_group = slide_groups[chunk_idx : chunk_idx + chunk_slides]
        flattened_ops = [op for group in chunk_group for op in group]
        temp_file = temp_dir / f"batch_chunk_{chunk_idx // chunk_slides:02d}.json"
        with temp_file.open("w", encoding="utf-8") as f:
            json.dump(flattened_ops, f, indent=2, ensure_ascii=False)

        print(
            f"Aplicando chunk {chunk_idx // chunk_slides + 1} ({len(flattened_ops)} operações)..."
        )
        run_gslides(
            ["mutate", "batch", presentation_id, "-f", str(temp_file), "--json"]
        )

    print("Todos os chunks foram aplicados com sucesso!")


def verify_presentation(presentation_id: str) -> None:
    """Valida programaticamente o deck criado via gslides CLI."""
    print(f"\nAuditando apresentação {presentation_id}...")
    res = run_gslides(["readonly", "info", presentation_id, "--json"])
    info = json.loads(res.stdout)

    slides = info.get("slides", [])
    num_slides = len(slides)
    print(f"Total de slides detectados: {num_slides}")

    if num_slides != 41:
        raise ValueError(
            f"Auditoria falhou: esperava-se exatamente 41 slides, encontrou {num_slides}"
        )

    print("Auditoria estrutural concluída: 41 slides presentes!")
    print(
        f"URL de edição: https://docs.google.com/presentation/d/{presentation_id}/edit"
    )


def main():
    parser = argparse.ArgumentParser(
        description="Gerador de Slides de Perguntas e Respostas — All-In Químico"
    )
    parser.add_argument(
        "--create",
        action="store_true",
        help="Cria automaticamente nova apresentação no Google Slides",
    )
    parser.add_argument(
        "--presentation-id",
        type=str,
        default=None,
        help="ID de uma apresentação existente para aplicar o batch",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_JSON,
        help="Caminho do arquivo JSON de batch a ser gerado",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Apenas gera o arquivo JSON sem enviar para a API",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("ALL-IN QUÍMICO — GERADOR DE SLIDES DE PERGUNTAS E RESPOSTAS (N1 E N2)")
    print("=" * 70)

    # 1. Carrega e valida questões
    questions = load_questions_n1_n2()
    print(f"Questões carregadas com sucesso: {len(questions)}")
    for i, q in enumerate(questions, start=1):
        diff = q.get("difficulty", 1)
        qid = q.get("id", "")
        corr = q.get("correct", "")
        print(f"  Lote {i:03d} -> Nível {diff} | ID {qid} | Gabarito {corr}")

    # 2. Gera operações de batch
    ops = generate_batch_operations(questions)
    print(f"\nOperações de batch geradas: {len(ops)}")

    # Salva arquivo JSON
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        json.dump(ops, f, indent=2, ensure_ascii=False)
    print(f"Arquivo JSON salvo em: {args.output}")

    if args.dry_run:
        print(
            "\nModo dry-run ativado. Nenhuma alteração foi enviada para o Google Slides."
        )
        return

    # 3. Criação ou atualização do Google Slides
    pres_id = args.presentation_id
    if args.create or not pres_id:
        pres_id = create_google_slides_deck()

    # 4. Aplicação do batch
    apply_batch_operations(pres_id, args.output)

    # 5. Auditoria de integridade
    verify_presentation(pres_id)

    print("\n" + "=" * 70)
    print("CONCLUÍDO COM SUCESSO!")
    print(f"Presentation ID: {pres_id}")
    print(f"Edit URL: https://docs.google.com/presentation/d/{pres_id}/edit")
    print("=" * 70)


if __name__ == "__main__":
    main()
