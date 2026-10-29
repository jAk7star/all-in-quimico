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
  2. Apresentação de Teste Exclusiva (R2):
     - Total de slides exatamente 7 (1 capa + 3 pares Q&A)
     - Exatamente 3 questões de Nível 1 exclusivas (zero N3, zero N2)
     - Regra de Zero-Reuse: questões não podem aparecer em outros decks
  3. Apresentações Individuais de Desafio — Nível 3 (R3):
     - Total de slides exatamente 3 (1 capa + 1 par Q&A)
     - Exatamente 1 questão de Nível 3 (Morte Súbita)
  4. Apresentações Regulares de 5 Perguntas e Respostas (R4):
     - Total de slides exatamente 11 por deck (1 capa + 5 pares Q&A)
     - Exatamente 5 questões (zero N3)
     - Decks regulares mutuamente disjuntos entre si (Reg_a ∩ Reg_b = ∅)
  5. Deck Suplente / Desempate Técnico (Nível 2):
     - Total de slides exatamente 5 (1 capa + 2 pares Q&A)
     - Exatamente 2 questões de Nível 2 (zero N3)
  6. Design System Fintech Clean & Anti-Overflow (R5):
     - Canvas background `#F8F9FA` (rgb(0.9725, 0.9765, 0.9804))
     - Cards elevados brancos `#FFFFFF`
     - Tipografia estrita `Open Sans` em 100% dos textos
     - Sem compressão severa de texto (`fontScale >= 0.90`)
  7. Modo Monolítico Legado (R2 Legado):
     - Total de 41 slides (1 capa + 20 pares Q&A) para compatibilidade retroativa.

Retorna código de saída 0 se todos os testes passarem, ou 1 se houver qualquer falha.

Uso CLI:
  # Auditoria via manifesto multi-deck:
  python verificar_decks_slides.py --manifest specs/SPEC-03-gerador/decks_manifest.json

  # Auditoria em modo offline (batch JSON):
  python verificar_decks_slides.py --manifest decks_manifest.json --offline

  # Auditoria de deck individual:
  python verificar_decks_slides.py --test-deck <ID_OU_ARQUIVO>
  python verificar_decks_slides.py --regular-deck <ID_OU_ARQUIVO>
  python verificar_decks_slides.py --challenge-deck <ID_OU_ARQUIVO> --expected-n3-id Q-SOL-005

  # Legado monolítico:
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

# Constantes e Defaults (IDs canônicos originais atualizados in-place)
DEFAULT_RULES_DECK_ID = "1KpfettWa9KkvbmBmhNAkyWRlTPPzahCeTVCuNlA3VU0"
DEFAULT_QA_DECK_ID = "10HrhJkrYDnxwhCP6HEo75DWvU9NS2RHXmp2wcx8XZUk"

EXPECTED_NIVEL_1_IDS = [
    "Q-ATO-001",
    "Q-ATO-002",
    "Q-ATO-003",
    "Q-ATO-004",
    "Q-ENV-001",
    "Q-ENV-002",
    "Q-ENV-003",
    "Q-ENV-004",
    "Q-ENV-007",
    "Q-ENV-008",
    "Q-SOL-001",
    "Q-SOL-006",
    "Q-SOL-010",
    "Q-SOL-011",
    "Q-STO-001",
    "Q-STO-002",
    "Q-STO-003",
    "Q-STO-004",
    "Q-STO-005",
    "Q-STO-009",
    "Q-STO-010",
]

EXPECTED_NIVEL_2_IDS = [
    "Q-ENV-005",
    "Q-ENV-009",
    "Q-ENV-010",
    "Q-SOL-002",
    "Q-SOL-003",
    "Q-SOL-004",
    "Q-SOL-009",
    "Q-SOL-012",
    "Q-STO-006",
    "Q-STO-007",
    "Q-STO-011",
    "Q-STO-012",
]

# IDs canônicos originais da apresentação monolítica legada de 41 slides (20 questões)
LEGACY_NIVEL_1_IDS = [
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

LEGACY_NIVEL_2_IDS = [
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

# Parâmetros oficiais do Design System Fintech Clean
DS_EXPECTED_BG_HEX = "#F8F9FA"
DS_EXPECTED_BG_RGB = (0.9725, 0.9765, 0.9804)
DS_EXPECTED_CARD_FILL_HEX = "#FFFFFF"
DS_EXPECTED_FONT_FAMILY = "Open Sans"
DS_MIN_FONT_SCALE = 0.90


@dataclass
class SlideInfo:
    """Informações agregadas e visuais de um slide individual."""

    index: int  # 1-indexed
    object_id: str
    text_content: str
    speaker_notes: str
    element_count: int
    background_color: Any = None
    shapes: list[dict[str, Any]] = field(default_factory=list)
    text_runs: list[dict[str, Any]] = field(default_factory=list)
    min_font_scale: float = 1.0
    raw_dict: dict[str, Any] = field(default_factory=dict)


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
    manifest_path: str | None = None
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


# =============================================================================
# UTILITÁRIOS DE INSPEÇÃO, TEXTO E CORES
# =============================================================================


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


def is_fintech_clean_background(color: Any, tol: float = 0.02) -> bool:
    """Verifica se a cor de fundo corresponde a #F8F9FA dentro da tolerância."""
    if color is None:
        return False

    if isinstance(color, str):
        c = color.strip().lstrip("#")
        if len(c) == 6:
            try:
                r = int(c[0:2], 16) / 255.0
                g = int(c[2:4], 16) / 255.0
                b = int(c[4:6], 16) / 255.0
                return (
                    abs(r - DS_EXPECTED_BG_RGB[0]) <= tol
                    and abs(g - DS_EXPECTED_BG_RGB[1]) <= tol
                    and abs(b - DS_EXPECTED_BG_RGB[2]) <= tol
                )
            except ValueError:
                return False
        return False

    if isinstance(color, dict):
        r = float(color.get("red", 0.0))
        g = float(color.get("green", 0.0))
        b = float(color.get("blue", 0.0))
        return (
            abs(r - DS_EXPECTED_BG_RGB[0]) <= tol
            and abs(g - DS_EXPECTED_BG_RGB[1]) <= tol
            and abs(b - DS_EXPECTED_BG_RGB[2]) <= tol
        )

    if isinstance(color, (list, tuple)) and len(color) >= 3:
        r, g, b = float(color[0]), float(color[1]), float(color[2])
        return (
            abs(r - DS_EXPECTED_BG_RGB[0]) <= tol
            and abs(g - DS_EXPECTED_BG_RGB[1]) <= tol
            and abs(b - DS_EXPECTED_BG_RGB[2]) <= tol
        )

    return False


def is_white_card_color(color: Any, tol: float = 0.02) -> bool:
    """Verifica se a cor do card corresponde a #FFFFFF."""
    if color is None:
        return False

    if isinstance(color, str):
        c = color.strip().lstrip("#").upper()
        if c in ("FFFFFF", "FFF"):
            return True
        if len(c) == 6:
            try:
                r = int(c[0:2], 16) / 255.0
                g = int(c[2:4], 16) / 255.0
                b = int(c[4:6], 16) / 255.0
                return abs(r - 1.0) <= tol and abs(g - 1.0) <= tol and abs(b - 1.0) <= tol
            except ValueError:
                return False
        return False

    if isinstance(color, dict):
        r = float(color.get("red", 0.0))
        g = float(color.get("green", 0.0))
        b = float(color.get("blue", 0.0))
        return abs(r - 1.0) <= tol and abs(g - 1.0) <= tol and abs(b - 1.0) <= tol

    if isinstance(color, (list, tuple)) and len(color) >= 3:
        r, g, b = float(color[0]), float(color[1]), float(color[2])
        return abs(r - 1.0) <= tol and abs(g - 1.0) <= tol and abs(b - 1.0) <= tol

    return False


def is_open_sans_font(font_name: Any) -> bool:
    """Verifica se o nome da fonte é estritamente 'Open Sans'."""
    if not font_name:
        return True
    return str(font_name).strip().lower() == "open sans"


def extract_question_ids(presentation: PresentationInfo) -> list[str]:
    """Extrai todos os identificadores canônicos de questão (Q-XXX-NNN) de uma apresentação."""
    all_text = " ".join(
        [f"{s.text_content} {s.speaker_notes}" for s in presentation.slides]
    )
    raw_ids = re.findall(r"\bQ-[A-Z]{3}-\d{3}\b", all_text)
    # Preserva ordem de primeira aparição
    seen: set[str] = set()
    ordered_ids: list[str] = []
    for qid in raw_ids:
        if qid not in seen:
            seen.add(qid)
            ordered_ids.append(qid)
    return ordered_ids


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


def extract_visual_elements_from_slide_dict(
    slide_dict: dict[str, Any],
) -> tuple[Any, list[dict[str, Any]], list[dict[str, Any]], float]:
    """Extrai cor de fundo, shapes, text runs e menor fontScale de um slide da API."""
    bg_color = None
    page_bg = slide_dict.get("pageProperties", {}).get("pageBackgroundFill", {})
    solid_fill = page_bg.get("solidFill", {})
    if "color" in solid_fill:
        color_obj = solid_fill["color"]
        if "rgbColor" in color_obj:
            bg_color = color_obj["rgbColor"]
        elif "themeColor" in color_obj:
            bg_color = color_obj.get("themeColor")

    shapes: list[dict[str, Any]] = []
    text_runs: list[dict[str, Any]] = []
    min_font_scale = 1.0

    def inspect_element(el: dict[str, Any]) -> None:
        nonlocal min_font_scale
        if "shape" in el:
            sh = el["shape"]
            stype = sh.get("shapeType", "")
            sh_fill = (
                sh.get("shapeProperties", {})
                .get("shapeBackgroundFill", {})
                .get("solidFill", {})
                .get("color", {})
                .get("rgbColor")
            )
            shapes.append({"shape_type": stype, "background_color": sh_fill})

            # Autofit fontScale
            autofit = sh.get("text", {}).get("autofit", {})
            if "fontScale" in autofit and autofit["fontScale"] is not None:
                min_font_scale = min(min_font_scale, float(autofit["fontScale"]))

            # Text runs
            for te in sh.get("text", {}).get("textElements", []):
                tr = te.get("textRun", {})
                if "content" in tr:
                    style = tr.get("style", {})
                    font_fam = style.get("fontFamily") or style.get(
                        "weightedFontFamily", {}
                    ).get("fontFamily")
                    text_runs.append(
                        {
                            "content": tr["content"],
                            "font_family": font_fam,
                            "style": style,
                        }
                    )

        if "elementGroup" in el:
            for ch in el["elementGroup"].get("children", []):
                inspect_element(ch)

    for el in slide_dict.get("pageElements", []):
        inspect_element(el)

    return bg_color, shapes, text_runs, min_font_scale


def parse_presentation_json(
    data: dict[str, Any], presentation_id: str
) -> PresentationInfo:
    """Converte o payload JSON retornado pela API/CLI ou mock em PresentationInfo estruturado."""
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

        bg_color, shapes, text_runs, min_font_scale = (
            extract_visual_elements_from_slide_dict(s)
        )

        # Suporte a campos diretos em mocks
        if s.get("background_color") is not None:
            bg_color = s.get("background_color")
        if s.get("shapes"):
            shapes = s.get("shapes")
        if s.get("text_runs"):
            text_runs = s.get("text_runs")
        if s.get("min_font_scale") is not None:
            min_font_scale = float(s.get("min_font_scale"))

        slide_infos.append(
            SlideInfo(
                index=idx,
                object_id=obj_id,
                text_content=combined_text,
                speaker_notes=notes,
                element_count=len(page_elements) if page_elements else len(shapes),
                background_color=bg_color,
                shapes=shapes,
                text_runs=text_runs,
                min_font_scale=min_font_scale,
                raw_dict=s,
            )
        )

    return PresentationInfo(
        presentation_id=presentation_id, title=title, slides=slide_infos
    )


def parse_batch_operations(
    ops: list[dict[str, Any]], presentation_id: str = "BATCH_DECK", title: str = ""
) -> PresentationInfo:
    """Simula e converte uma lista de operações declarativas de mutação em PresentationInfo."""
    slide_order: list[str] = []
    slide_data: dict[str, dict[str, Any]] = {}

    def get_or_create_slide(slide_id: str) -> dict[str, Any]:
        if slide_id not in slide_data:
            slide_order.append(slide_id)
            slide_data[slide_id] = {
                "id": slide_id,
                "texts": [],
                "notes": "",
                "bg_color": None,
                "shapes": [],
                "text_runs": [],
                "min_font_scale": 1.0,
            }
        return slide_data[slide_id]

    get_or_create_slide("p")

    for op in ops:
        op_type = op.get("op", "")
        if op_type == "add-slide":
            sid = op.get("id") or f"slide_{len(slide_order) + 1}"
            get_or_create_slide(sid)
            continue

        target_slide = op.get("slide", slide_order[0] if slide_order else "p")
        sentry = get_or_create_slide(target_slide)

        if op_type == "set-background":
            sentry["bg_color"] = op.get("color")
        elif op_type == "add-shape":
            sentry["shapes"].append(
                {
                    "shape_type": op.get("shape_type", "ROUND_RECTANGLE"),
                    "background_color": op.get("background_color"),
                    "outline_color": op.get("outline_color"),
                }
            )
        elif op_type == "add-textbox":
            txt = op.get("text", "")
            sentry["texts"].append(txt)
            font_fam = op.get("font_family")
            font_scale = op.get("font_scale", op.get("fontScale", 1.0))
            if font_scale is not None:
                sentry["min_font_scale"] = min(
                    sentry["min_font_scale"], float(font_scale)
                )
            sentry["text_runs"].append(
                {
                    "content": txt,
                    "font_family": font_fam,
                    "font_size": op.get("font_size"),
                }
            )
        elif op_type == "set-notes":
            sentry["notes"] = op.get("notes", op.get("text", ""))

    slide_infos: list[SlideInfo] = []
    for idx, sid in enumerate(slide_order, start=1):
        sd = slide_data[sid]
        slide_infos.append(
            SlideInfo(
                index=idx,
                object_id=sid,
                text_content=" ".join(sd["texts"]).strip(),
                speaker_notes=sd["notes"].strip(),
                element_count=len(sd["shapes"]) + len(sd["text_runs"]),
                background_color=sd["bg_color"],
                shapes=sd["shapes"],
                text_runs=sd["text_runs"],
                min_font_scale=sd["min_font_scale"],
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
    if DEFAULT_QA_DECK_ID:
        return DEFAULT_QA_DECK_ID

    for env_var in ["QA_DECK_ID", "ALL_IN_QA_DECK_ID", "GOOGLE_SLIDES_QA_DECK_ID"]:
        val = os.getenv(env_var)
        if val and len(val.strip()) > 15:
            return val.strip()

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
                    matches = re.findall(
                        r"presentation/d/([a-zA-Z0-9_-]{25,})", content
                    )
                    for m in matches:
                        if m != DEFAULT_RULES_DECK_ID:
                            return m
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


# =============================================================================
# AUDITORIA DO DESIGN SYSTEM FINTECH CLEAN (R5)
# =============================================================================


def verify_design_system(
    presentation: PresentationInfo,
    deck_category_label: str = "Design System",
    prefix: str = "DS",
) -> list[CheckResult]:
    """Audita a conformidade com o Design System Fintech Clean: fundo #F8F9FA, cards #FFFFFF, Open Sans e fontScale >= 0.90."""
    results: list[CheckResult] = []
    slides = presentation.slides

    # 1. Canvas Background: #F8F9FA
    non_conforming_bg: list[int] = []
    for s in slides:
        if s.background_color is not None and not is_fintech_clean_background(
            s.background_color
        ):
            non_conforming_bg.append(s.index)

    passed_bg = len(non_conforming_bg) == 0
    results.append(
        CheckResult(
            check_id=f"{prefix}_BG_COLOR",
            category=deck_category_label,
            title="Cor de fundo do canvas estritamente #F8F9FA (Fintech Clean)",
            passed=passed_bg,
            details=f"Todos os {len(slides)} slides utilizam fundo #F8F9FA."
            if passed_bg
            else f"Slides com fundo divergente de #F8F9FA: {non_conforming_bg}",
            evidence=f"Slides validados: {len(slides) - len(non_conforming_bg)}/{len(slides)}",
        )
    )

    # 2. Card Shapes Fill: #FFFFFF (obrigatório em todos os slides de conteúdo index >= 2)
    missing_white_cards: list[int] = []
    for s in slides:
        if s.index >= 2:
            white_cards = [
                sh
                for sh in s.shapes
                if sh.get("shape_type") in ("ROUND_RECTANGLE", "RECTANGLE")
                and is_white_card_color(sh.get("background_color"))
            ]
            if len(white_cards) == 0:
                missing_white_cards.append(s.index)

    passed_cards = len(missing_white_cards) == 0
    results.append(
        CheckResult(
            check_id=f"{prefix}_CARD_FILL",
            category=deck_category_label,
            title="Cards elevados com preenchimento branco puro (#FFFFFF)",
            passed=passed_cards,
            details="Todos os slides de conteúdo utilizam superfície branca elevada #FFFFFF."
            if passed_cards
            else f"Slides de conteúdo sem card branco #FFFFFF detectado: {missing_white_cards}",
            evidence=f"Slides sem card branco: {len(missing_white_cards)}",
        )
    )

    # 3. Tipografia: Open Sans em 100% dos textos
    violating_fonts: list[tuple[int, str]] = []
    for s in slides:
        for tr in s.text_runs:
            ff = tr.get("font_family")
            if ff and not is_open_sans_font(ff):
                violating_fonts.append((s.index, str(ff)))

    passed_fonts = len(violating_fonts) == 0
    results.append(
        CheckResult(
            check_id=f"{prefix}_FONT_FAMILY",
            category=deck_category_label,
            title="Tipografia estrita Open Sans em 100% dos elementos de texto",
            passed=passed_fonts,
            details="100% dos elementos de texto utilizam a fonte Open Sans."
            if passed_fonts
            else f"Fontes não autorizadas detectadas: {violating_fonts[:3]}",
            evidence=f"Violações tipográficas: {len(violating_fonts)}",
        )
    )

    # 4. Anti-Overflow: fontScale >= 0.90
    overflow_slides: list[tuple[int, float]] = []
    for s in slides:
        if s.min_font_scale < DS_MIN_FONT_SCALE:
            overflow_slides.append((s.index, s.min_font_scale))

    passed_overflow = len(overflow_slides) == 0
    results.append(
        CheckResult(
            check_id=f"{prefix}_FONT_SCALE",
            category=deck_category_label,
            title="Ausência de transbordamento / compressão severa de texto (fontScale ≥ 0.90)",
            passed=passed_overflow,
            details="Nenhum transbordamento ou compressão excessiva de texto detectada (todos os fontScale ≥ 0.90)."
            if passed_overflow
            else f"Slides com compressão excessiva (fontScale < 0.90): {overflow_slides}",
            evidence=f"Slides com overflow: {len(overflow_slides)}",
        )
    )

    return results


# =============================================================================
# AUDITORIA DE REGRAS DIDÁTICAS (R1)
# =============================================================================


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

    # 4. Integridade da Speaker Note do Slide 2
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

    # 5. Mecânica em papel e ausência de placas
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

    # 6. Limite de aposta: teto R$ 200 e mínimo R$ 10
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

    # 7. Regras de bonificação: x2 para 1-4 acertos
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

    # 8. Bônus Unânime Fixo de +R$ 100
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

    # 9. Penalidade de erro
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

    # 10. Desafio da Mesa pós-rodada 5: gatilho de empate técnico
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

    # 11. Desafio da Mesa: Winner Takes All
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

    # 12. Mecânica de Repescagem na 5ª rodada
    has_repescagem = bool(re.search(r"repescagem", full_text_lower))
    has_repescagem_200 = bool(
        re.search(
            r"repescagem.*200|\+R\$\s*200.*(?:banco|repescagem|5ª|última)",
            full_text,
            re.IGNORECASE,
        )
    )
    passed = has_repescagem and has_repescagem_200
    results.append(
        CheckResult(
            check_id="R1_REPESCAGEM_MECHANIC",
            category="Regras Didáticas (R1)",
            title="Repescagem na 5ª/última rodada (+R$ 200 do Banco para equipe zerada ou saldo ≤ R$ 200)",
            passed=passed,
            details=f"Menção a 'Repescagem'={has_repescagem}, auxílio de +R$ 200 na última rodada={has_repescagem_200}.",
            evidence=next(
                (
                    line.strip()
                    for line in full_text.splitlines()
                    if "repescagem" in line.lower()
                ),
                None,
            ),
        )
    )

    return results


# =============================================================================
# AUDITORIA DO DECK DE TESTE EXCLUSIVO (R2)
# =============================================================================


def verify_test_deck(presentation: PresentationInfo) -> list[CheckResult]:
    """
    Audita a Apresentação de Teste Exclusiva (R2):
      - Exatamente 7 slides (1 capa + 3 pares Q&A intercalados).
      - Exatamente 3 questões de Nível 1.
      - Zero questões de Nível 3 e zero questões de Nível 2.
      - Paridade estrita Pergunta/Resposta.
      - Conformidade com Design System Fintech Clean.
    """
    results: list[CheckResult] = []
    slides = presentation.slides
    num_slides = len(slides)

    # 1. Total exato de 7 slides
    passed_count = num_slides == 7
    results.append(
        CheckResult(
            check_id="TEST_SLIDES_COUNT",
            category="Deck de Teste (R2)",
            title="Contagem total exata de 7 slides (1 capa + 3 pares Q&A)",
            passed=passed_count,
            details=f"Detectados {num_slides} slides no deck de teste (esperado: exatamente 7).",
            evidence=f"Slide count = {num_slides}",
        )
    )

    # 2. Slide 1 é Capa
    cover_text = slides[0].text_content.lower() if num_slides > 0 else ""
    is_cover = bool(
        "teste" in cover_text
        or "aquecimento" in cover_text
        or "all-in" in cover_text
        or "treino" in cover_text
    )
    results.append(
        CheckResult(
            check_id="TEST_COVER_SLIDE",
            category="Deck de Teste (R2)",
            title="Slide 1 é Capa oficial da Rodada de Teste/Aquecimento",
            passed=is_cover,
            details=f"Texto do Slide 1 avaliado como capa de teste: {is_cover}.",
            evidence=slides[0].text_content[:120] if num_slides > 0 else None,
        )
    )

    # 3. Paridade estrita intercalada nos 3 pares (Slides 2-3, 4-5, 6-7)
    parity_errors: list[str] = []
    for i in range(1, 4):
        q_idx = 2 * i - 1
        a_idx = 2 * i
        if q_idx >= num_slides or a_idx >= num_slides:
            parity_errors.append(f"Par {i} ausente")
            continue

        q_txt = slides[q_idx].text_content.lower()
        a_txt = slides[a_idx].text_content.lower()

        is_q = bool(
            (
                re.search(r"pergunta|lote|quest[aã]o|n[ií]vel\s*1", q_txt)
                or "opção" in q_txt
                or "alternativa" in q_txt
                or "a)" in q_txt
                or "[a]" in q_txt
            )
            and not re.search(r"gabarito\s*oficial|resolu[cç][aã]o\s+passo", q_txt)
        )
        is_a = bool(
            re.search(r"gabarito|resposta|resolu[cç][aã]o|justificativa", a_txt)
            and not (
                "opção b" in a_txt
                or "alternativa b explicada" in a_txt
                or "opção b)" in a_txt
            )
        )
        if not is_q:
            parity_errors.append(f"Par {i} (Slide {2*i}): não é pergunta")
        if not is_a:
            parity_errors.append(f"Par {i} (Slide {2*i+1}): não é resposta")

    passed_parity = len(parity_errors) == 0 and num_slides >= 7
    results.append(
        CheckResult(
            check_id="TEST_INTERLEAVED_PARITY",
            category="Deck de Teste (R2)",
            title="Paridade intercalada estrita: Slide 2i = Pergunta i, Slide 2i+1 = Resposta i (i=1..3)",
            passed=passed_parity,
            details="3 pares de pergunta e resposta intercalados com sucesso."
            if passed_parity
            else f"Erros de paridade: {'; '.join(parity_errors)}",
            evidence="3 pares Q&A intercalados",
        )
    )

    # 4. Exatamente 3 questões de Nível 1
    detected_ids = extract_question_ids(presentation)
    n1_ids = [qid for qid in detected_ids if qid in EXPECTED_NIVEL_1_IDS]
    non_n1_ids = [qid for qid in detected_ids if qid not in EXPECTED_NIVEL_1_IDS]

    passed_n1 = len(detected_ids) == 3 and len(n1_ids) == 3 and len(non_n1_ids) == 0
    results.append(
        CheckResult(
            check_id="TEST_N1_EXACT_3",
            category="Deck de Teste (R2)",
            title="Presença exclusiva de exatamente 3 questões de Nível 1",
            passed=passed_n1,
            details=f"Detectadas {len(n1_ids)} questões de Nível 1: {n1_ids}."
            if passed_n1
            else f"Divergência: {len(detected_ids)} questões detectadas ({detected_ids}), sendo {len(non_n1_ids)} não-N1 ({non_n1_ids}). Esperado: exatamente 3 N1.",
            evidence=f"IDs detectados: {detected_ids}",
        )
    )

    # 5. Exclusão categórica de Nível 3
    all_text = " ".join(
        [f"{s.text_content} {s.speaker_notes}" for s in presentation.slides]
    )
    n3_ids_found = [qid for qid in FORBIDDEN_NIVEL_3_IDS if qid in all_text]
    n3_patterns_found = [
        p for p in FORBIDDEN_N3_PATTERNS if re.search(p, all_text, re.IGNORECASE)
    ]
    passed_no_n3 = len(n3_ids_found) == 0 and len(n3_patterns_found) == 0
    results.append(
        CheckResult(
            check_id="TEST_EXCLUDE_N3",
            category="Deck de Teste (R2)",
            title="Exclusão categórica de Nível 3 (Morte Súbita)",
            passed=passed_no_n3,
            details="Zero IDs ou padrões de Nível 3 detectados no deck de teste."
            if passed_no_n3
            else f"Violação N3 detectada: IDs={n3_ids_found}, Padrões={n3_patterns_found}",
            evidence="0 itens N3 detectados"
            if passed_no_n3
            else f"Detectado: {n3_ids_found + n3_patterns_found}",
        )
    )

    # 6. Exclusão categórica de Nível 2
    n2_ids_found = [qid for qid in EXPECTED_NIVEL_2_IDS if qid in all_text]
    passed_no_n2 = len(n2_ids_found) == 0
    results.append(
        CheckResult(
            check_id="TEST_EXCLUDE_N2",
            category="Deck de Teste (R2)",
            title="Exclusão categórica de questões de Nível 2 no deck de teste",
            passed=passed_no_n2,
            details="Zero questões de Nível 2 detectadas no deck de teste."
            if passed_no_n2
            else f"Questões indevidas de Nível 2 no deck de teste: {n2_ids_found}",
            evidence=f"IDs N2 detectados: {n2_ids_found}",
        )
    )

    # 7. Design System Visual
    ds_results = verify_design_system(
        presentation, deck_category_label="Deck de Teste (R2)", prefix="TEST_DS"
    )
    results.extend(ds_results)

    return results


# =============================================================================
# AUDITORIA DAS APRESENTAÇÕES DE DESAFIO INDIVIDUAL NÍVEL 3 (R3)
# =============================================================================


def verify_challenge_deck(
    presentation: PresentationInfo, expected_question_id: str | None = None
) -> list[CheckResult]:
    """
    Audita uma Apresentação Individual de Desafio Nível 3 (R3):
      - Exatamente 3 slides (1 capa + 1 par Q&A) focada na questão.
      - Exatamente 1 questão de Nível 3.
      - Zero questões de Nível 1 ou Nível 2.
      - Paridade de pergunta e resposta com foco Texas Hold'em / Morte Súbita.
      - Conformidade com Design System Fintech Clean.
    """
    results: list[CheckResult] = []
    slides = presentation.slides
    num_slides = len(slides)

    # 1. Total exato de 3 slides (1 capa + 1 par Q&A)
    passed_count = num_slides == 3
    results.append(
        CheckResult(
            check_id="CHALLENGE_SLIDES_COUNT",
            category="Desafio Individual N3 (R3)",
            title="Contagem exata de 3 slides (1 capa + 1 par Q&A de foco extremo)",
            passed=passed_count,
            details=f"Detectados {num_slides} slides no deck de desafio (esperado: exatamente 3).",
            evidence=f"Slide count = {num_slides}",
        )
    )

    # 2. Slide 1 é Capa de Desafio
    cover_text = slides[0].text_content.lower() if num_slides > 0 else ""
    is_cover = bool(
        "desafio" in cover_text
        or "morte súbita" in cover_text
        or "morte subita" in cover_text
        or "all-in" in cover_text
        or "final" in cover_text
    )
    results.append(
        CheckResult(
            check_id="CHALLENGE_COVER_SLIDE",
            category="Desafio Individual N3 (R3)",
            title="Slide 1 é Capa temática de Desafio Final / Morte Súbita",
            passed=is_cover,
            details=f"Texto do Slide 1 avaliado como capa de desafio: {is_cover}.",
            evidence=slides[0].text_content[:120] if num_slides > 0 else None,
        )
    )

    # 3. Paridade estrita no par único (Slide 2 Pergunta, Slide 3 Resposta)
    if num_slides >= 3:
        q_txt = slides[1].text_content.lower()
        a_txt = slides[2].text_content.lower()
        is_q = bool(
            (
                re.search(
                    r"pergunta|lote|quest[aã]o|desafio|morte\s*s[uú]bita|n[ií]vel\s*3",
                    q_txt,
                )
                or "opção" in q_txt
                or "alternativa" in q_txt
                or "a)" in q_txt
                or "[a]" in q_txt
            )
            and not re.search(r"gabarito\s*oficial|resolu[cç][aã]o\s+multietapa", q_txt)
        )
        is_a = bool(
            re.search(r"gabarito|resposta|resolu[cç][aã]o|justificativa", a_txt)
            and not ("opção b" in a_txt or "alternativa b detalhada" in a_txt)
        )
        passed_parity = is_q and is_a
    else:
        passed_parity = False

    results.append(
        CheckResult(
            check_id="CHALLENGE_INTERLEAVED_PARITY",
            category="Desafio Individual N3 (R3)",
            title="Paridade estrita: Slide 2 = Pergunta de Desafio, Slide 3 = Gabarito Oficial",
            passed=passed_parity,
            details="Par de Pergunta e Gabarito de desafio identificado com sucesso."
            if passed_parity
            else "Falha na estrutura de Pergunta e Gabarito do desafio individual.",
            evidence="Par Q&A validado",
        )
    )

    # 4. Exatamente 1 questão de Nível 3 canônico
    detected_ids = extract_question_ids(presentation)
    n3_ids = [qid for qid in detected_ids if qid in FORBIDDEN_NIVEL_3_IDS]
    non_n3_ids = [qid for qid in detected_ids if qid not in FORBIDDEN_NIVEL_3_IDS]

    match_expected = True
    if expected_question_id:
        match_expected = expected_question_id in detected_ids

    passed_n3 = (
        len(detected_ids) == 1
        and len(n3_ids) == 1
        and len(non_n3_ids) == 0
        and match_expected
    )
    results.append(
        CheckResult(
            check_id="CHALLENGE_N3_EXACT_1",
            category="Desafio Individual N3 (R3)",
            title="Presença exclusiva de exatamente 1 questão de Nível 3 canônica",
            passed=passed_n3,
            details=f"Detectada exatamente 1 questão N3: {n3_ids} (esperada: {expected_question_id or 'qualquer N3'})."
            if passed_n3
            else f"Divergência: {len(detected_ids)} questões detectadas ({detected_ids}). Esperado: exatamente 1 questão N3 ({expected_question_id or 'N3 canônica'}).",
            evidence=f"IDs detectados: {detected_ids}",
        )
    )

    # 5. Exclusão de Nível 1 e Nível 2
    n1_or_n2_found = [
        qid
        for qid in detected_ids
        if qid in EXPECTED_NIVEL_1_IDS or qid in EXPECTED_NIVEL_2_IDS
    ]
    passed_no_n1_n2 = len(n1_or_n2_found) == 0
    results.append(
        CheckResult(
            check_id="CHALLENGE_EXCLUDE_N1_N2",
            category="Desafio Individual N3 (R3)",
            title="Exclusão categórica de questões de Nível 1 e Nível 2 no deck de desafio",
            passed=passed_no_n1_n2,
            details="Zero questões de Nível 1 ou Nível 2 detectadas no deck de desafio."
            if passed_no_n1_n2
            else f"Questões indevidas de N1/N2 detectadas no desafio: {n1_or_n2_found}",
            evidence=f"IDs N1/N2: {n1_or_n2_found}",
        )
    )

    # 6. Design System Visual
    ds_results = verify_design_system(
        presentation,
        deck_category_label="Desafio Individual N3 (R3)",
        prefix="CHALLENGE_DS",
    )
    results.extend(ds_results)

    return results


# =============================================================================
# AUDITORIA DAS APRESENTAÇÕES REGULARES (R4)
# =============================================================================


def verify_regular_deck(
    presentation: PresentationInfo, expected_question_ids: list[str] | None = None
) -> list[CheckResult]:
    """
    Audita uma Apresentação Regular de Perguntas e Respostas (R4 — 5 ou 10 rodadas):
      - Total de slides: 11 slides (5 Qs) ou 21 slides (10 Qs).
      - Questões de Nível 1 ou Nível 2.
      - Exclusão categórica de Nível 3.
      - Paridade estrita intercalada Pergunta -> Resposta.
      - Conformidade com Design System Fintech Clean.
    """
    results: list[CheckResult] = []
    slides = presentation.slides
    num_slides = len(slides)

    expected_q_count = (
        len(expected_question_ids)
        if expected_question_ids
        else (10 if num_slides == 21 else 5)
    )
    expected_slides_count = 1 + 2 * expected_q_count

    # 1. Total exato de slides (11 para 5 Qs, 21 para 10 Qs)
    passed_count = num_slides == expected_slides_count
    results.append(
        CheckResult(
            check_id="REGULAR_SLIDES_COUNT",
            category="Deck Regular (R4)",
            title=f"Contagem total exata de {expected_slides_count} slides (1 capa + {expected_q_count} pares Q&A)",
            passed=passed_count,
            details=f"Detectados {num_slides} slides no deck regular (esperado: exatamente {expected_slides_count}).",
            evidence=f"Slide count = {num_slides}",
        )
    )

    # 2. Slide 1 é Capa Regular
    cover_text = slides[0].text_content.lower() if num_slides > 0 else ""
    is_cover = bool(
        "all-in" in cover_text
        or "perguntas" in cover_text
        or "deck" in cover_text
        or "regular" in cover_text
        or "rodadas" in cover_text
    )
    results.append(
        CheckResult(
            check_id="REGULAR_COVER_SLIDE",
            category="Deck Regular (R4)",
            title="Slide 1 é Capa temática da Apresentação Regular",
            passed=is_cover,
            details=f"Texto do Slide 1 avaliado como capa: {is_cover}.",
            evidence=slides[0].text_content[:120] if num_slides > 0 else None,
        )
    )

    # 3. Paridade estrita intercalada nos pares
    parity_errors: list[str] = []
    for i in range(1, expected_q_count + 1):
        q_idx = 2 * i - 1
        a_idx = 2 * i
        if q_idx >= num_slides or a_idx >= num_slides:
            parity_errors.append(f"Par {i} ausente")
            continue

        q_txt = slides[q_idx].text_content.lower()
        a_txt = slides[a_idx].text_content.lower()

        is_q = bool(
            (
                re.search(r"pergunta|lote|quest[aã]o|n[ií]vel\s*[12]", q_txt)
                or "opção" in q_txt
                or "alternativa" in q_txt
                or "a)" in q_txt
                or "[a]" in q_txt
            )
            and not re.search(r"gabarito\s*oficial|resolu[cç][aã]o\s+e\s+justificativa", q_txt)
        )
        is_a = bool(
            re.search(r"gabarito|resposta|resolu[cç][aã]o|justificativa", a_txt)
            and not (
                "opção b" in a_txt
                or "segunda opção" in a_txt
                or "opção b)" in a_txt
            )
        )
        if not is_q:
            parity_errors.append(f"Par {i} (Slide {2*i}): não é pergunta")
        if not is_a:
            parity_errors.append(f"Par {i} (Slide {2*i+1}): não é resposta")

    passed_parity = len(parity_errors) == 0 and num_slides >= expected_slides_count
    results.append(
        CheckResult(
            check_id="REGULAR_INTERLEAVED_PARITY",
            category="Deck Regular (R4)",
            title=f"Paridade intercalada estrita: Slide 2i = Pergunta i, Slide 2i+1 = Resposta i (i=1..{expected_q_count})",
            passed=passed_parity,
            details=f"{expected_q_count} pares de pergunta e resposta intercalados com sucesso."
            if passed_parity
            else f"Erros de paridade: {'; '.join(parity_errors)}",
            evidence=f"{expected_q_count} pares Q&A intercalados",
        )
    )

    # 4. Exatamente expected_q_count questões
    detected_ids = extract_question_ids(presentation)
    match_expected = True
    if expected_question_ids:
        match_expected = set(detected_ids) == set(expected_question_ids)

    passed_count_q = len(detected_ids) == expected_q_count and match_expected
    results.append(
        CheckResult(
            check_id="REGULAR_EXACT_5_QUESTIONS",
            category="Deck Regular (R4)",
            title=f"Presença de exatamente {expected_q_count} questões didáticas no deck regular",
            passed=passed_count_q,
            details=f"Detectadas {expected_q_count} questões no deck regular: {detected_ids}."
            if passed_count_q
            else f"Divergência de questões detectadas: {len(detected_ids)} ({detected_ids}). Esperado: exatamente {expected_q_count} questões ({expected_question_ids or f'{expected_q_count} questões'}).",
            evidence=f"IDs detectados: {detected_ids}",
        )
    )

    # 5. Exclusão categórica de Nível 3
    all_text = " ".join(
        [f"{s.text_content} {s.speaker_notes}" for s in presentation.slides]
    )
    n3_ids_found = [qid for qid in FORBIDDEN_NIVEL_3_IDS if qid in all_text]
    n3_patterns_found = [
        p for p in FORBIDDEN_N3_PATTERNS if re.search(p, all_text, re.IGNORECASE)
    ]
    passed_no_n3 = len(n3_ids_found) == 0 and len(n3_patterns_found) == 0
    results.append(
        CheckResult(
            check_id="REGULAR_EXCLUDE_N3",
            category="Deck Regular (R4)",
            title="Exclusão categórica de questões e marcadores de Nível 3",
            passed=passed_no_n3,
            details="Nenhum item de Nível 3 detectado no deck regular."
            if passed_no_n3
            else f"Violações de Nível 3 no deck regular: IDs={n3_ids_found}, Padrões={n3_patterns_found}",
            evidence="0 itens N3 detectados"
            if passed_no_n3
            else f"Detectado: {n3_ids_found + n3_patterns_found}",
        )
    )

    # 6. Design System Visual
    ds_results = verify_design_system(
        presentation, deck_category_label="Deck Regular (R4)", prefix="REGULAR_DS"
    )
    results.extend(ds_results)

    return results


# =============================================================================
# AUDITORIA DO DECK DE DESEMPATE / SUPLENTE (NÍVEL 2)
# =============================================================================


def verify_tiebreaker_deck(
    presentation: PresentationInfo, expected_question_ids: list[str] | None = None
) -> list[CheckResult]:
    """
    Audita o Deck Suplente / Desempate Técnico (Nível 2):
      - Exatamente 5 slides (1 capa + 2 pares Q&A intercalados).
      - Exatamente 2 questões de Nível 2.
      - Exclusão categórica de Nível 3.
      - Conformidade com Design System Fintech Clean.
    """
    results: list[CheckResult] = []
    slides = presentation.slides
    num_slides = len(slides)

    # 1. Total exato de 5 slides
    passed_count = num_slides == 5
    results.append(
        CheckResult(
            check_id="TIEBREAKER_SLIDES_COUNT",
            category="Deck Desempate",
            title="Contagem total exata de 5 slides (1 capa + 2 pares Q&A)",
            passed=passed_count,
            details=f"Detectados {num_slides} slides no deck de desempate (esperado: exatamente 5).",
            evidence=f"Slide count = {num_slides}",
        )
    )

    # 2. Slide 1 é Capa
    cover_text = slides[0].text_content.lower() if num_slides > 0 else ""
    is_cover = bool(
        "desempate" in cover_text
        or "suplente" in cover_text
        or "all-in" in cover_text
    )
    results.append(
        CheckResult(
            check_id="TIEBREAKER_COVER_SLIDE",
            category="Deck Desempate",
            title="Slide 1 é Capa temática de Desempate / Suplente",
            passed=is_cover,
            details=f"Texto do Slide 1 avaliado como capa de desempate: {is_cover}.",
            evidence=slides[0].text_content[:120] if num_slides > 0 else None,
        )
    )

    # 3. Paridade nos 2 pares
    parity_errors: list[str] = []
    for i in range(1, 3):
        q_idx = 2 * i - 1
        a_idx = 2 * i
        if q_idx >= num_slides or a_idx >= num_slides:
            parity_errors.append(f"Par {i} ausente")
            continue
        q_txt = slides[q_idx].text_content.lower()
        a_txt = slides[a_idx].text_content.lower()
        is_q = bool(
            (
                re.search(r"pergunta|lote|quest[aã]o|n[ií]vel\s*2", q_txt)
                or "opção" in q_txt
                or "alternativa" in q_txt
                or "a)" in q_txt
                or "[a]" in q_txt
            )
            and not re.search(r"gabarito\s*oficial|resolu[cç][aã]o\s+detalhada", q_txt)
        )
        is_a = bool(
            re.search(r"gabarito|resposta|resolu[cç][aã]o|justificativa", a_txt)
            and not (
                "opção b" in a_txt
                or "segunda opção" in a_txt
                or "opção b)" in a_txt
            )
        )
        if not is_q:
            parity_errors.append(f"Par {i} (Slide {2*i}): não é pergunta")
        if not is_a:
            parity_errors.append(f"Par {i} (Slide {2*i+1}): não é resposta")

    passed_parity = len(parity_errors) == 0 and num_slides >= 5
    results.append(
        CheckResult(
            check_id="TIEBREAKER_INTERLEAVED_PARITY",
            category="Deck Desempate",
            title="Paridade intercalada: Slide 2i = Pergunta i, Slide 2i+1 = Resposta i (i=1..2)",
            passed=passed_parity,
            details="2 pares Q&A intercalados com sucesso."
            if passed_parity
            else f"Erros de paridade: {'; '.join(parity_errors)}",
            evidence="2 pares Q&A intercalados",
        )
    )

    # 4. Exatamente 2 questões
    detected_ids = extract_question_ids(presentation)
    match_expected = True
    if expected_question_ids:
        match_expected = set(detected_ids) == set(expected_question_ids)

    passed_count_q = len(detected_ids) == 2 and match_expected
    results.append(
        CheckResult(
            check_id="TIEBREAKER_EXACT_2_QUESTIONS",
            category="Deck Desempate",
            title="Presença de exatamente 2 questões didáticas de Nível 2",
            passed=passed_count_q,
            details=f"Detectadas 2 questões no deck de desempate: {detected_ids}."
            if passed_count_q
            else f"Divergência: {len(detected_ids)} questões detectadas ({detected_ids}). Esperado: exatamente 2 questões ({expected_question_ids or '2 questões'}).",
            evidence=f"IDs detectados: {detected_ids}",
        )
    )

    # 5. Exclusão de Nível 3
    all_text = " ".join(
        [f"{s.text_content} {s.speaker_notes}" for s in presentation.slides]
    )
    n3_ids_found = [qid for qid in FORBIDDEN_NIVEL_3_IDS if qid in all_text]
    passed_no_n3 = len(n3_ids_found) == 0
    results.append(
        CheckResult(
            check_id="TIEBREAKER_EXCLUDE_N3",
            category="Deck Desempate",
            title="Exclusão categórica de questões de Nível 3 no deck de desempate",
            passed=passed_no_n3,
            details="Nenhuma questão de Nível 3 detectada no deck de desempate."
            if passed_no_n3
            else f"Violação N3 detectada: {n3_ids_found}",
            evidence=f"IDs N3 detectados: {n3_ids_found}",
        )
    )

    # 6. Design System Visual
    ds_results = verify_design_system(
        presentation, deck_category_label="Deck Desempate", prefix="TIEBREAKER_DS"
    )
    results.extend(ds_results)

    return results


# =============================================================================
# AUDITORIA DE ISOLAMENTO CRUZADO E ZERO-REUSE (TIER 3)
# =============================================================================


def verify_cross_deck_isolation(
    test_deck: PresentationInfo | list[str],
    regular_decks: list[PresentationInfo | list[str]],
    challenge_decks: list[PresentationInfo | list[str]],
    tiebreaker_deck: PresentationInfo | list[str] | None = None,
) -> list[CheckResult]:
    """
    Executa a auditoria de disjunção mútua entre todos os decks gerados:
      - Test ∩ Regulares = ∅ (Zero-Reuse)
      - Test ∩ Desafios = ∅
      - Reg_a ∩ Reg_b = ∅ (Partição estrita entre decks regulares)
      - Desafio_a ∩ Desafio_b = ∅
      - Tiebreaker ∩ (Test ∪ Regulares ∪ Desafios) = ∅
    """
    results: list[CheckResult] = []

    def get_ids(target: PresentationInfo | list[str]) -> set[str]:
        if isinstance(target, list):
            return set(target)
        return set(extract_question_ids(target))

    test_ids = get_ids(test_deck)
    regular_sets = [get_ids(r) for r in regular_decks]
    challenge_sets = [get_ids(c) for c in challenge_decks]
    tiebreaker_ids = get_ids(tiebreaker_deck) if tiebreaker_deck else set()

    all_regular_ids: set[str] = set()
    for s in regular_sets:
        all_regular_ids.update(s)

    all_challenge_ids: set[str] = set()
    for s in challenge_sets:
        all_challenge_ids.update(s)

    # 1. Test ∩ Regulares = ∅
    leak_test_regular = test_ids & all_regular_ids
    passed_t_r = len(leak_test_regular) == 0
    results.append(
        CheckResult(
            check_id="CROSS_TEST_REGULAR_DISJOINT",
            category="Isolamento Cruzado (Zero-Reuse)",
            title="Isolamento absoluto: Teste ∩ Regulares = ∅ (Zero-Reuse de questões de teste)",
            passed=passed_t_r,
            details="Zero reutilização: nenhuma das questões de teste aparece nos decks regulares."
            if passed_t_r
            else f"Violação de Zero-Reuse: questão(ões) de teste vazada(s) nos decks regulares: {sorted(leak_test_regular)}",
            evidence="Disjunção confirmada"
            if passed_t_r
            else f"Vazamentos: {sorted(leak_test_regular)}",
        )
    )

    # 2. Test ∩ Desafios = ∅
    leak_test_challenge = test_ids & all_challenge_ids
    passed_t_c = len(leak_test_challenge) == 0
    results.append(
        CheckResult(
            check_id="CROSS_TEST_CHALLENGE_DISJOINT",
            category="Isolamento Cruzado (Zero-Reuse)",
            title="Isolamento absoluto: Teste ∩ Desafios = ∅",
            passed=passed_t_c,
            details="Zero reutilização: nenhuma questão de teste aparece nos desafios."
            if passed_t_c
            else f"Violação de isolamento: questão(ões) de teste presente(s) nos desafios: {sorted(leak_test_challenge)}",
            evidence="Disjunção confirmada"
            if passed_t_c
            else f"Vazamentos: {sorted(leak_test_challenge)}",
        )
    )

    # 3. Reg_a ∩ Reg_b = ∅ (disjunção pairwise entre decks regulares)
    regular_overlaps: list[str] = []
    for i in range(len(regular_sets)):
        for j in range(i + 1, len(regular_sets)):
            overlap = regular_sets[i] & regular_sets[j]
            if overlap:
                regular_overlaps.append(
                    f"Regular {i+1} ∩ Regular {j+1}: {sorted(overlap)}"
                )

    passed_r_r = len(regular_overlaps) == 0
    results.append(
        CheckResult(
            check_id="CROSS_REGULAR_PAIRWISE_DISJOINT",
            category="Isolamento Cruzado (Zero-Reuse)",
            title="Partição estrita: decks regulares mutuamente disjuntos entre si (Reg_a ∩ Reg_b = ∅)",
            passed=passed_r_r,
            details="Todos os decks regulares são mutuamente disjuntos."
            if passed_r_r
            else f"Questões duplicadas entre decks regulares: {'; '.join(regular_overlaps)}",
            evidence="Partição pairwise perfeita"
            if passed_r_r
            else f"Sobreposições: {regular_overlaps}",
        )
    )

    # 4. Desafio_a ∩ Desafio_b = ∅
    challenge_overlaps: list[str] = []
    for i in range(len(challenge_sets)):
        for j in range(i + 1, len(challenge_sets)):
            overlap = challenge_sets[i] & challenge_sets[j]
            if overlap:
                challenge_overlaps.append(
                    f"Desafio {i+1} ∩ Desafio {j+1}: {sorted(overlap)}"
                )

    passed_c_c = len(challenge_overlaps) == 0
    results.append(
        CheckResult(
            check_id="CROSS_CHALLENGE_PAIRWISE_DISJOINT",
            category="Isolamento Cruzado (Zero-Reuse)",
            title="Partição estrita: desafios individuais mutuamente disjuntos entre si",
            passed=passed_c_c,
            details="Todos os decks de desafio são mutuamente disjuntos."
            if passed_c_c
            else f"Desafios com mesma questão: {'; '.join(challenge_overlaps)}",
            evidence="Desafios disjuntos"
            if passed_c_c
            else f"Sobreposições: {challenge_overlaps}",
        )
    )

    # 5. Tiebreaker ∩ (Test ∪ Regulares ∪ Desafios) = ∅
    if tiebreaker_ids:
        tb_leak_test = tiebreaker_ids & test_ids
        tb_leak_reg = tiebreaker_ids & all_regular_ids
        tb_leak_chal = tiebreaker_ids & all_challenge_ids
        tb_leaks = tb_leak_test | tb_leak_reg | tb_leak_chal

        passed_tb = len(tb_leaks) == 0
        results.append(
            CheckResult(
                check_id="CROSS_TIEBREAKER_DISJOINT",
                category="Isolamento Cruzado (Zero-Reuse)",
                title="Isolamento absoluto: deck de desempate mutuamente disjunto de todos os demais decks",
                passed=passed_tb,
                details="Deck de desempate possui questões exclusivas não repetidas."
                if passed_tb
                else f"Questão(ões) de desempate duplicada(s) em outros decks: {sorted(tb_leaks)}",
                evidence="Desempate disjunto"
                if passed_tb
                else f"Vazamentos: {sorted(tb_leaks)}",
            )
        )

    return results


# =============================================================================
# RESOLUÇÃO DE APRESENTAÇÕES (ONLINE E OFFLINE BATCH)
# =============================================================================


def resolve_presentation(
    deck_entry: dict[str, Any] | str,
    mock_decks: dict[str, Any] | None = None,
    offline: bool = False,
    base_dir: Path | None = None,
) -> PresentationInfo:
    """Resolve uma apresentação a partir de mock, arquivo batch JSON local ou API do Google Slides."""
    pres_id = ""
    title = ""
    deck_type = ""
    batch_file = None

    if isinstance(deck_entry, str):
        pres_id = deck_entry
    elif isinstance(deck_entry, dict):
        pres_id = (
            deck_entry.get("presentation_id")
            or deck_entry.get("deck_id")
            or deck_entry.get("id")
            or ""
        )
        title = deck_entry.get("title", "")
        deck_type = deck_entry.get("type", "")
        batch_file = deck_entry.get("batch_file") or deck_entry.get("file_path")

    # 1. Verifica no dicionário de mocks
    if mock_decks:
        for lookup_key in [
            pres_id,
            title,
            deck_type,
            deck_entry.get("deck_id") if isinstance(deck_entry, dict) else None,
        ]:
            if lookup_key and lookup_key in mock_decks:
                val = mock_decks[lookup_key]
                if isinstance(val, PresentationInfo):
                    return val
                if isinstance(val, dict):
                    if "slides" in val:
                        return parse_presentation_json(val, pres_id)
                    if "ops" in val or "operations" in val:
                        return parse_batch_operations(
                            val.get("ops") or val.get("operations"), pres_id, title
                        )
                if isinstance(val, list):
                    return parse_batch_operations(val, pres_id, title)

    # 2. Verifica se o pres_id ou batch_file é um arquivo no sistema
    candidate_paths: list[Path] = []
    if batch_file:
        candidate_paths.append(Path(batch_file))
        if base_dir:
            candidate_paths.append(base_dir / batch_file)
    if pres_id and (pres_id.endswith(".json") or os.sep in pres_id):
        candidate_paths.append(Path(pres_id))
        if base_dir:
            candidate_paths.append(base_dir / pres_id)

    for p in candidate_paths:
        if p.is_file():
            content = p.read_text(encoding="utf-8", errors="replace")
            parsed = json.loads(content)
            if isinstance(parsed, list):
                return parse_batch_operations(parsed, pres_id, title)
            if isinstance(parsed, dict):
                if "slides" in parsed:
                    return parse_presentation_json(parsed, pres_id)
                if "ops" in parsed or "operations" in parsed:
                    return parse_batch_operations(
                        parsed.get("ops") or parsed.get("operations"), pres_id, title
                    )

    # 3. Chamada à API Google Slides via CLI gslides
    if not offline and pres_id and len(pres_id) >= 20:
        return fetch_presentation_from_cli(pres_id)

    if offline:
        raise RuntimeError(
            f"Modo offline ativado: a apresentação '{pres_id or title}' não foi encontrada nos mocks ou arquivos locais."
        )

    raise RuntimeError(
        f"Não foi possível obter a apresentação '{pres_id or title}'. ID não fornecido ou inválido."
    )


# =============================================================================
# RUNNERS PRINCIPAIS (MANIFESTO & FULL AUDIT)
# =============================================================================


def run_manifest_audit(
    manifest_path: str | Path | None = None,
    manifest_data: dict[str, Any] | None = None,
    mock_decks: dict[str, Any] | None = None,
    offline: bool = False,
    verbose: bool = False,
) -> AuditReport:
    """
    Executa a auditoria completa do ecossistema de apresentações a partir de um decks_manifest.json:
      - Validação de cada tipo de deck (Regras, Teste, Desafios, Regulares, Desempate).
      - Auditoria do Design System Fintech Clean (#F8F9FA, #FFFFFF, Open Sans, fontScale).
      - Auditoria de Isolamento Cruzado e Zero-Reuse entre todos os decks.
    """
    report = AuditReport(manifest_path=str(manifest_path) if manifest_path else None)

    if manifest_data is None:
        if not manifest_path:
            raise ValueError(
                "É necessário fornecer 'manifest_path' ou 'manifest_data'."
            )
        p = Path(manifest_path)
        if not p.is_file():
            report.results.append(
                CheckResult(
                    check_id="MANIFEST_NOT_FOUND",
                    category="Manifesto de Decks",
                    title="Acesso e leitura do manifesto de apresentações",
                    passed=False,
                    details=f"Arquivo de manifesto não encontrado no caminho: {p}",
                )
            )
            return report

        try:
            manifest_data = json.loads(p.read_text(encoding="utf-8", errors="replace"))
        except (json.JSONDecodeError, OSError) as e:
            report.results.append(
                CheckResult(
                    check_id="MANIFEST_PARSE_ERROR",
                    category="Manifesto de Decks",
                    title="Decodificação JSON do arquivo de manifesto",
                    passed=False,
                    details=f"Falha ao decodificar JSON do manifesto: {e}",
                )
            )
            return report

    base_dir = Path(manifest_path).parent if manifest_path else None
    decks_section = (
        manifest_data.get("decks")
        if isinstance(manifest_data.get("decks"), dict)
        else manifest_data
    )

    test_pres: PresentationInfo | None = None
    regular_pres_list: list[PresentationInfo] = []
    challenge_pres_list: list[PresentationInfo] = []
    tiebreaker_pres: PresentationInfo | None = None

    # 1. Deck de Regras (se presente)
    rules_entry = decks_section.get("rules_deck") or decks_section.get("rules")
    if rules_entry:
        if verbose:
            print("\n[MANIFESTO] Auditando Deck de Regras Didáticas...")
        try:
            rules_pres = resolve_presentation(
                rules_entry, mock_decks, offline, base_dir
            )
            report.results.extend(verify_rules_deck(rules_pres))
        except (
            RuntimeError,
            ValueError,
            OSError,
            json.JSONDecodeError,
            subprocess.SubprocessError,
            KeyError,
        ) as e:
            report.results.append(
                CheckResult(
                    check_id="RULES_DECK_ERROR",
                    category="Regras Didáticas (R1)",
                    title="Acesso e leitura do deck de regras",
                    passed=False,
                    details=f"Erro ao auditar deck de regras: {e}",
                )
            )

    # 2. Deck de Teste Exclusivo
    test_entry = decks_section.get("test_deck") or decks_section.get("test")
    if test_entry:
        if verbose:
            print("\n[MANIFESTO] Auditando Deck de Teste Exclusivo...")
        try:
            test_pres = resolve_presentation(test_entry, mock_decks, offline, base_dir)
            report.results.extend(verify_test_deck(test_pres))
        except (
            RuntimeError,
            ValueError,
            OSError,
            json.JSONDecodeError,
            subprocess.SubprocessError,
            KeyError,
        ) as e:
            report.results.append(
                CheckResult(
                    check_id="TEST_DECK_ERROR",
                    category="Deck de Teste (R2)",
                    title="Acesso e leitura do deck de teste exclusivo",
                    passed=False,
                    details=f"Erro ao auditar deck de teste: {e}",
                )
            )
    else:
        report.results.append(
            CheckResult(
                check_id="MANIFEST_MISSING_TEST_DECK",
                category="Manifesto de Decks",
                title="Presença da especificação do deck de teste no manifesto",
                passed=False,
                details="A chave 'test_deck' não foi encontrada no manifesto.",
            )
        )

    # 3. Decks Individuais de Desafio (Nível 3)
    chal_entries = (
        decks_section.get("challenges")
        or decks_section.get("challenge_decks")
        or []
    )
    if isinstance(chal_entries, list) and chal_entries:
        for idx, c_entry in enumerate(chal_entries, start=1):
            expected_qid = None
            if isinstance(c_entry, dict):
                expected_qid = (
                    c_entry.get("question_ids", [None])[0]
                    if c_entry.get("question_ids")
                    else c_entry.get("question_id")
                )
            if verbose:
                print(
                    f"\n[MANIFESTO] Auditando Deck de Desafio N3 #{idx} (esperado: {expected_qid})..."
                )
            try:
                cp = resolve_presentation(c_entry, mock_decks, offline, base_dir)
                challenge_pres_list.append(cp)
                report.results.extend(
                    verify_challenge_deck(cp, expected_question_id=expected_qid)
                )
            except (
            RuntimeError,
            ValueError,
            OSError,
            json.JSONDecodeError,
            subprocess.SubprocessError,
            KeyError,
        ) as e:
                report.results.append(
                    CheckResult(
                        check_id=f"CHALLENGE_DECK_{idx}_ERROR",
                        category="Desafio Individual N3 (R3)",
                        title=f"Acesso e leitura do desafio individual #{idx}",
                        passed=False,
                        details=f"Erro ao auditar desafio individual #{idx}: {e}",
                    )
                )
    else:
        report.results.append(
            CheckResult(
                check_id="MANIFEST_MISSING_CHALLENGES",
                category="Manifesto de Decks",
                title="Presença dos decks de desafio N3 no manifesto",
                passed=False,
                details="Nenhum deck de desafio listado no manifesto ('challenges').",
            )
        )

    # 4. Decks Regulares de 5 Perguntas
    reg_entries = decks_section.get("regular_decks") or []
    if isinstance(reg_entries, list) and reg_entries:
        for idx, r_entry in enumerate(reg_entries, start=1):
            expected_qids = (
                r_entry.get("question_ids") if isinstance(r_entry, dict) else None
            )
            if verbose:
                print(f"\n[MANIFESTO] Auditando Deck Regular #{idx}...")
            try:
                rp = resolve_presentation(r_entry, mock_decks, offline, base_dir)
                regular_pres_list.append(rp)
                report.results.extend(
                    verify_regular_deck(rp, expected_question_ids=expected_qids)
                )
            except (
            RuntimeError,
            ValueError,
            OSError,
            json.JSONDecodeError,
            subprocess.SubprocessError,
            KeyError,
        ) as e:
                report.results.append(
                    CheckResult(
                        check_id=f"REGULAR_DECK_{idx}_ERROR",
                        category="Deck Regular (R4)",
                        title=f"Acesso e leitura do deck regular #{idx}",
                        passed=False,
                        details=f"Erro ao auditar deck regular #{idx}: {e}",
                    )
                )
    else:
        report.results.append(
            CheckResult(
                check_id="MANIFEST_MISSING_REGULARS",
                category="Manifesto de Decks",
                title="Presença dos decks regulares no manifesto",
                passed=False,
                details="Nenhum deck regular listado no manifesto ('regular_decks').",
            )
        )

    # 5. Deck de Desempate / Suplente (se presente)
    tb_entry = decks_section.get("tiebreaker_deck") or decks_section.get("tiebreaker")
    if tb_entry:
        if verbose:
            print("\n[MANIFESTO] Auditando Deck de Desempate / Suplente...")
        expected_qids = (
            tb_entry.get("question_ids") if isinstance(tb_entry, dict) else None
        )
        try:
            tiebreaker_pres = resolve_presentation(
                tb_entry, mock_decks, offline, base_dir
            )
            report.results.extend(
                verify_tiebreaker_deck(
                    tiebreaker_pres, expected_question_ids=expected_qids
                )
            )
        except (
            RuntimeError,
            ValueError,
            OSError,
            json.JSONDecodeError,
            subprocess.SubprocessError,
            KeyError,
        ) as e:
            report.results.append(
                CheckResult(
                    check_id="TIEBREAKER_DECK_ERROR",
                    category="Deck Desempate",
                    title="Acesso e leitura do deck de desempate",
                    passed=False,
                    details=f"Erro ao auditar deck de desempate: {e}",
                )
            )

    # 6. Auditoria de Isolamento Cruzado (Zero-Reuse)
    if test_pres and regular_pres_list:
        if verbose:
            print(
                "\n[MANIFESTO] Executando Auditoria de Isolamento Cruzado e Zero-Reuse..."
            )
        cross_results = verify_cross_deck_isolation(
            test_deck=test_pres,
            regular_decks=regular_pres_list,
            challenge_decks=challenge_pres_list,
            tiebreaker_deck=tiebreaker_pres,
        )
        report.results.extend(cross_results)

    return report


def verify_qa_deck(presentation: PresentationInfo) -> list[CheckResult]:
    """Executa a bateria de auditoria da Apresentação Sequencial Monolítica de Perguntas e Respostas (R2 Legado)."""
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
        q_idx = 2 * i - 1
        a_idx = 2 * i

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
                or "alternativa a" in q_text.lower()
            )
        )

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
    for qid in LEGACY_NIVEL_1_IDS:
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
    for qid in LEGACY_NIVEL_2_IDS:
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
    """Executa a auditoria completa conforme os parâmetros fornecidos (retrocompatibilidade R1/R2)."""
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
            KeyError,
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
                    details="O ID da apresentação Q&A não foi especificado via --qa-deck e não foi encontrado automaticamente.",
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
            KeyError,
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


# =============================================================================
# FÁBRICAS DE MOCK PARA TESTES UNITÁRIOS E E2E
# =============================================================================


def create_mock_test_deck(
    question_ids: list[str] | None = None,
    total_slides: int | None = None,
    font_family: str = "Open Sans",
    bg_color: str = "#F8F9FA",
    font_scale: float = 1.0,
    add_white_cards: bool = True,
) -> PresentationInfo:
    """Cria apresentação mock em conformidade com o Deck de Teste Exclusivo (7 slides, 3 N1)."""
    default_ids = ["Q-ATO-001", "Q-SOL-001", "Q-STO-001"]
    qids = question_ids if question_ids is not None else default_ids
    max_slides = total_slides if total_slides is not None else (1 + 2 * len(qids))

    slides: list[SlideInfo] = [
        SlideInfo(
            index=1,
            object_id="cover",
            text_content="ALL-IN QUÍMICO • RODADA DE AQUECIMENTO E TESTE (NÍVEL 1) • 3 QUESTÕES",
            speaker_notes="Capa oficial da apresentação de teste exclusivo.",
            element_count=4,
            background_color=bg_color,
            shapes=[{"shape_type": "ROUND_RECTANGLE", "background_color": "#FFFFFF"}] if add_white_cards else [],
            text_runs=[{"content": "ALL-IN QUÍMICO", "font_family": font_family}],
            min_font_scale=font_scale,
        )
    ]

    for idx, qid in enumerate(qids, start=1):
        if len(slides) >= max_slides:
            break
        q_slide = SlideInfo(
            index=2 * idx,
            object_id=f"q_{idx}",
            text_content=f"LOTE 00{idx} • Nível 1 - Aquecimento • Questão {qid}\nEnunciado teste {qid} no card.\nOpção A) Alternativa correta.\nOpção B) Alternativa incorreta.\nAposta no papel • Teto R$ 200",
            speaker_notes=f"Notas para a pergunta {qid}.",
            element_count=5,
            background_color=bg_color,
            shapes=[{"shape_type": "ROUND_RECTANGLE", "background_color": "#FFFFFF"}] if add_white_cards else [],
            text_runs=[{"content": f"Pergunta {qid}", "font_family": font_family}],
            min_font_scale=font_scale,
        )
        slides.append(q_slide)

        if len(slides) >= max_slides:
            break
        a_slide = SlideInfo(
            index=2 * idx + 1,
            object_id=f"a_{idx}",
            text_content=f"LOTE 00{idx} • GABARITO OFICIAL: ALTERNATIVA A\nQuestão {qid}\nResolução explicada passo a passo.\nJustificativa científica formal.\nPagamento: Dobro (×2).",
            speaker_notes=f"Notas para o gabarito {qid}.",
            element_count=6,
            background_color=bg_color,
            shapes=[{"shape_type": "ROUND_RECTANGLE", "background_color": "#FFFFFF"}] if add_white_cards else [],
            text_runs=[{"content": f"Gabarito {qid}", "font_family": font_family}],
            min_font_scale=font_scale,
        )
        slides.append(a_slide)

    while len(slides) < max_slides:
        curr_idx = len(slides) + 1
        slides.append(
            SlideInfo(
                index=curr_idx,
                object_id=f"extra_{curr_idx}",
                text_content=f"Slide extra {curr_idx}",
                speaker_notes="",
                element_count=2,
                background_color=bg_color,
                shapes=[{"shape_type": "ROUND_RECTANGLE", "background_color": "#FFFFFF"}] if add_white_cards else [],
                text_runs=[{"content": "Extra", "font_family": font_family}],
                min_font_scale=font_scale,
            )
        )

    return PresentationInfo(
        presentation_id="MOCK_TEST_DECK",
        title="All-In Químico — Deck de Teste",
        slides=slides,
    )


def create_mock_challenge_deck(
    question_id: str = "Q-SOL-005",
    total_slides: int = 3,
    font_family: str = "Open Sans",
    bg_color: str = "#F8F9FA",
    font_scale: float = 1.0,
    add_white_cards: bool = True,
) -> PresentationInfo:
    """Cria apresentação mock em conformidade com o Desafio Individual N3 (3 slides, 1 N3)."""
    slides: list[SlideInfo] = [
        SlideInfo(
            index=1,
            object_id="cover",
            text_content=f"ALL-IN QUÍMICO • DESAFIO FINAL: MORTE SÚBITA • {question_id}",
            speaker_notes="Capa oficial do desafio individual Texas Hold'em.",
            element_count=4,
            background_color=bg_color,
            shapes=[{"shape_type": "ROUND_RECTANGLE", "background_color": "#FFFFFF"}] if add_white_cards else [],
            text_runs=[{"content": "DESAFIO FINAL", "font_family": font_family}],
            min_font_scale=font_scale,
        )
    ]

    if total_slides >= 2:
        slides.append(
            SlideInfo(
                index=2,
                object_id="q_1",
                text_content=f"DESAFIO FINAL • MORTE SÚBITA • Questão {question_id}\nEnunciado de alta complexidade de Nível 3.\nOpção A) Alternativa A detalhada.\nOpção B) Alternativa B detalhada.\nPote 100% Winner Takes All",
                speaker_notes=f"Notas para a pergunta de desafio {question_id}.",
                element_count=5,
                background_color=bg_color,
                shapes=[{"shape_type": "ROUND_RECTANGLE", "background_color": "#FFFFFF"}] if add_white_cards else [],
                text_runs=[{"content": f"Desafio {question_id}", "font_family": font_family}],
                min_font_scale=font_scale,
            )
        )

    if total_slides >= 3:
        slides.append(
            SlideInfo(
                index=3,
                object_id="a_1",
                text_content=f"DESAFIO FINAL • GABARITO OFICIAL: ALTERNATIVA A\nQuestão {question_id}\nResolução multietapa detalhada com cálculos estequiométricos.\nWinner Takes All: vencedor leva todo o pote!",
                speaker_notes=f"Notas do gabarito de desafio {question_id}.",
                element_count=6,
                background_color=bg_color,
                shapes=[{"shape_type": "ROUND_RECTANGLE", "background_color": "#FFFFFF"}] if add_white_cards else [],
                text_runs=[{"content": f"Gabarito {question_id}", "font_family": font_family}],
                min_font_scale=font_scale,
            )
        )

    while len(slides) < total_slides:
        curr_idx = len(slides) + 1
        slides.append(
            SlideInfo(
                index=curr_idx,
                object_id=f"extra_{curr_idx}",
                text_content=f"Slide extra {curr_idx}",
                speaker_notes="",
                element_count=2,
                background_color=bg_color,
                shapes=[{"shape_type": "ROUND_RECTANGLE", "background_color": "#FFFFFF"}] if add_white_cards else [],
                text_runs=[{"content": "Extra", "font_family": font_family}],
                min_font_scale=font_scale,
            )
        )

    return PresentationInfo(
        presentation_id=f"MOCK_CHALLENGE_{question_id}",
        title=f"All-In Químico — Desafio {question_id}",
        slides=slides,
    )


def create_mock_regular_deck(
    question_ids: list[str] | None = None,
    total_slides: int | None = None,
    font_family: str = "Open Sans",
    bg_color: str = "#F8F9FA",
    font_scale: float = 1.0,
    add_white_cards: bool = True,
) -> PresentationInfo:
    """Cria apresentação mock em conformidade com o Deck Regular (11 slides, 5 Qs)."""
    default_ids = ["Q-ATO-002", "Q-SOL-006", "Q-STO-002", "Q-STO-003", "Q-STO-004"]
    qids = question_ids if question_ids is not None else default_ids
    max_slides = total_slides if total_slides is not None else (1 + 2 * len(qids))

    slides: list[SlideInfo] = [
        SlideInfo(
            index=1,
            object_id="cover",
            text_content="ALL-IN QUÍMICO • CARDS DE PERGUNTAS E RESPOSTAS • DECK REGULAR",
            speaker_notes="Capa oficial da apresentação regular.",
            element_count=4,
            background_color=bg_color,
            shapes=[{"shape_type": "ROUND_RECTANGLE", "background_color": "#FFFFFF"}] if add_white_cards else [],
            text_runs=[{"content": "DECK REGULAR", "font_family": font_family}],
            min_font_scale=font_scale,
        )
    ]

    for idx, qid in enumerate(qids, start=1):
        if len(slides) >= max_slides:
            break
        q_slide = SlideInfo(
            index=2 * idx,
            object_id=f"q_{idx}",
            text_content=f"LOTE 00{idx} • Questão {qid}\nEnunciado químico completo da questão regular.\nOpção A) Primeira opção.\nOpção B) Segunda opção.\nTeto R$ 200 • Aposta em papel",
            speaker_notes=f"Notas para a questão {qid}.",
            element_count=5,
            background_color=bg_color,
            shapes=[{"shape_type": "ROUND_RECTANGLE", "background_color": "#FFFFFF"}] if add_white_cards else [],
            text_runs=[{"content": f"Pergunta {qid}", "font_family": font_family}],
            min_font_scale=font_scale,
        )
        slides.append(q_slide)

        if len(slides) >= max_slides:
            break
        a_slide = SlideInfo(
            index=2 * idx + 1,
            object_id=f"a_{idx}",
            text_content=f"LOTE 00{idx} • GABARITO OFICIAL: ALTERNATIVA A\nQuestão {qid}\nResolução e justificativa pedagógica.\nPagamento: Dobro (×2).",
            speaker_notes=f"Notas para o gabarito {qid}.",
            element_count=6,
            background_color=bg_color,
            shapes=[{"shape_type": "ROUND_RECTANGLE", "background_color": "#FFFFFF"}] if add_white_cards else [],
            text_runs=[{"content": f"Gabarito {qid}", "font_family": font_family}],
            min_font_scale=font_scale,
        )
        slides.append(a_slide)

    while len(slides) < max_slides:
        curr_idx = len(slides) + 1
        slides.append(
            SlideInfo(
                index=curr_idx,
                object_id=f"extra_{curr_idx}",
                text_content=f"Slide extra {curr_idx}",
                speaker_notes="",
                element_count=2,
                background_color=bg_color,
                shapes=[{"shape_type": "ROUND_RECTANGLE", "background_color": "#FFFFFF"}] if add_white_cards else [],
                text_runs=[{"content": "Extra", "font_family": font_family}],
                min_font_scale=font_scale,
            )
        )

    return PresentationInfo(
        presentation_id="MOCK_REGULAR_DECK",
        title="All-In Químico — Deck Regular",
        slides=slides,
    )


def create_mock_tiebreaker_deck(
    question_ids: list[str] | None = None,
    total_slides: int | None = None,
    font_family: str = "Open Sans",
    bg_color: str = "#F8F9FA",
    font_scale: float = 1.0,
    add_white_cards: bool = True,
) -> PresentationInfo:
    """Cria apresentação mock em conformidade com o Deck de Desempate (5 slides, 2 Qs N2)."""
    default_ids = ["Q-ENV-005", "Q-STO-007"]
    qids = question_ids if question_ids is not None else default_ids
    max_slides = total_slides if total_slides is not None else (1 + 2 * len(qids))

    slides: list[SlideInfo] = [
        SlideInfo(
            index=1,
            object_id="cover",
            text_content="ALL-IN QUÍMICO • DECK SUPLENTE / DESEMPATE TÉCNICO (NÍVEL 2)",
            speaker_notes="Capa oficial do deck de desempate.",
            element_count=4,
            background_color=bg_color,
            shapes=[{"shape_type": "ROUND_RECTANGLE", "background_color": "#FFFFFF"}] if add_white_cards else [],
            text_runs=[{"content": "DESEMPATE", "font_family": font_family}],
            min_font_scale=font_scale,
        )
    ]

    for idx, qid in enumerate(qids, start=1):
        if len(slides) >= max_slides:
            break
        q_slide = SlideInfo(
            index=2 * idx,
            object_id=f"q_{idx}",
            text_content=f"DESEMPATE • Nível 2 • Questão {qid}\nEnunciado da questão de desempate.\nOpção A) Primeira opção.\nOpção B) Segunda opção.\nAposta livre até saldo total",
            speaker_notes=f"Notas para a pergunta de desempate {qid}.",
            element_count=5,
            background_color=bg_color,
            shapes=[{"shape_type": "ROUND_RECTANGLE", "background_color": "#FFFFFF"}] if add_white_cards else [],
            text_runs=[{"content": f"Pergunta {qid}", "font_family": font_family}],
            min_font_scale=font_scale,
        )
        slides.append(q_slide)

        if len(slides) >= max_slides:
            break
        a_slide = SlideInfo(
            index=2 * idx + 1,
            object_id=f"a_{idx}",
            text_content=f"DESEMPATE • GABARITO OFICIAL: ALTERNATIVA A\nQuestão {qid}\nResolução detalhada do desempate.",
            speaker_notes=f"Notas para o gabarito {qid}.",
            element_count=6,
            background_color=bg_color,
            shapes=[{"shape_type": "ROUND_RECTANGLE", "background_color": "#FFFFFF"}] if add_white_cards else [],
            text_runs=[{"content": f"Gabarito {qid}", "font_family": font_family}],
            min_font_scale=font_scale,
        )
        slides.append(a_slide)

    while len(slides) < max_slides:
        curr_idx = len(slides) + 1
        slides.append(
            SlideInfo(
                index=curr_idx,
                object_id=f"extra_{curr_idx}",
                text_content=f"Slide extra {curr_idx}",
                speaker_notes="",
                element_count=2,
                background_color=bg_color,
                shapes=[{"shape_type": "ROUND_RECTANGLE", "background_color": "#FFFFFF"}] if add_white_cards else [],
                text_runs=[{"content": "Extra", "font_family": font_family}],
                min_font_scale=font_scale,
            )
        )

    return PresentationInfo(
        presentation_id="MOCK_TIEBREAKER_DECK",
        title="All-In Químico — Deck de Desempate",
        slides=slides,
    )


def create_mock_multi_deck_manifest(
    test_ids: list[str] | None = None,
    reg1_ids: list[str] | None = None,
    reg2_ids: list[str] | None = None,
    reg3_ids: list[str] | None = None,
    challenge_ids: list[str] | None = None,
    tiebreaker_ids: list[str] | None = None,
) -> tuple[dict[str, Any], dict[str, PresentationInfo]]:
    """Cria um manifesto e suas apresentações mock associadas perfeitamente disjuntas e em conformidade."""
    t_ids = test_ids or ["Q-ATO-001", "Q-SOL-001", "Q-STO-001"]
    r1_ids = reg1_ids or ["Q-ATO-002", "Q-SOL-006", "Q-STO-002", "Q-STO-003", "Q-STO-004"]
    r2_ids = reg2_ids or ["Q-STO-005", "Q-ENV-001", "Q-ENV-002", "Q-ENV-003", "Q-ENV-004"]
    r3_ids = reg3_ids or ["Q-SOL-002", "Q-SOL-003", "Q-SOL-004", "Q-SOL-009", "Q-STO-006"]
    c_ids = challenge_ids or ["Q-SOL-005", "Q-SOL-007", "Q-SOL-008", "Q-STO-008", "Q-ENV-006"]
    tb_ids = tiebreaker_ids or ["Q-ENV-005", "Q-STO-007"]

    mock_decks: dict[str, PresentationInfo] = {}

    test_pres = create_mock_test_deck(question_ids=t_ids, total_slides=7)
    mock_decks["TEST_DECK_ID"] = test_pres

    reg1_pres = create_mock_regular_deck(question_ids=r1_ids, total_slides=11)
    mock_decks["REG_01_ID"] = reg1_pres

    reg2_pres = create_mock_regular_deck(question_ids=r2_ids, total_slides=11)
    mock_decks["REG_02_ID"] = reg2_pres

    reg3_pres = create_mock_regular_deck(question_ids=r3_ids, total_slides=11)
    mock_decks["REG_03_ID"] = reg3_pres

    chal_entries: list[dict[str, Any]] = []
    for idx, cid in enumerate(c_ids, start=1):
        cp_id = f"CHAL_{idx}_ID"
        cp = create_mock_challenge_deck(question_id=cid, total_slides=3)
        mock_decks[cp_id] = cp
        chal_entries.append(
            {
                "type": "challenge",
                "presentation_id": cp_id,
                "title": f"Desafio Morte Súbita {cid}",
                "total_slides": 3,
                "question_ids": [cid],
            }
        )

    tb_pres = create_mock_tiebreaker_deck(question_ids=tb_ids, total_slides=5)
    mock_decks["TIEBREAKER_ID"] = tb_pres

    manifest_dict = {
        "manifest_version": "2.0",
        "generated_at": "2026-10-29T00:00:00Z",
        "design_system": {
            "background_color": DS_EXPECTED_BG_HEX,
            "card_background": DS_EXPECTED_CARD_FILL_HEX,
            "font_family": DS_EXPECTED_FONT_FAMILY,
        },
        "decks": {
            "test_deck": {
                "type": "test",
                "presentation_id": "TEST_DECK_ID",
                "title": "Deck de Teste Exclusivo (3 Questões N1)",
                "total_slides": 7,
                "question_ids": t_ids,
            },
            "challenges": chal_entries,
            "regular_decks": [
                {
                    "type": "regular",
                    "deck_id": "regular_01",
                    "presentation_id": "REG_01_ID",
                    "title": "Deck Regular 01",
                    "total_slides": 11,
                    "question_ids": r1_ids,
                },
                {
                    "type": "regular",
                    "deck_id": "regular_02",
                    "presentation_id": "REG_02_ID",
                    "title": "Deck Regular 02",
                    "total_slides": 11,
                    "question_ids": r2_ids,
                },
                {
                    "type": "regular",
                    "deck_id": "regular_03",
                    "presentation_id": "REG_03_ID",
                    "title": "Deck Regular 03",
                    "total_slides": 11,
                    "question_ids": r3_ids,
                },
            ],
            "tiebreaker_deck": {
                "type": "tiebreaker",
                "presentation_id": "TIEBREAKER_ID",
                "title": "Deck de Desempate (Nível 2)",
                "total_slides": 5,
                "question_ids": tb_ids,
            },
        },
    }

    return manifest_dict, mock_decks


# ==============================================================================
# FORMATAÇÃO E SAÍDA CLI
# ==============================================================================


def print_audit_report(report: AuditReport, verbose: bool = False) -> None:
    """Imprime relatório formatado e detalhado no terminal."""
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

    if report.manifest_path:
        print(f"Manifesto de Decks: {report.manifest_path}")
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
        print(f"  {tag:<7} {r.check_id:<32} {r.title}")
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
        "--manifest",
        type=str,
        default=None,
        help="Caminho para decks_manifest.json para auditoria multi-deck integrada",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Executa auditoria em modo offline inspecionando arquivos locais de batch mutation",
    )
    parser.add_argument(
        "--test-deck",
        type=str,
        default=None,
        help="ID ou caminho do deck de teste exclusivo para auditoria isolada",
    )
    parser.add_argument(
        "--challenge-deck",
        type=str,
        default=None,
        help="ID ou caminho do deck de desafio individual N3",
    )
    parser.add_argument(
        "--expected-n3-id",
        type=str,
        default=None,
        help="ID esperado de Nível 3 para validação de desafio individual",
    )
    parser.add_argument(
        "--regular-deck",
        type=str,
        default=None,
        help="ID ou caminho de uma apresentação regular de 5 perguntas",
    )
    parser.add_argument(
        "--tiebreaker-deck",
        type=str,
        default=None,
        help="ID ou caminho do deck suplente / desempate técnico",
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
        help="ID da apresentação sequencial monolítica de Perguntas e Respostas N1/N2",
    )
    parser.add_argument(
        "--rules-only",
        action="store_true",
        help="Executa apenas a auditoria do deck de regras (R1)",
    )
    parser.add_argument(
        "--qa-only",
        action="store_true",
        help="Executa apenas a auditoria do deck de perguntas e respostas monolítico (R2)",
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

    # 1. Modo Manifesto Multi-Deck
    if args.manifest:
        report = run_manifest_audit(
            manifest_path=args.manifest,
            offline=args.offline,
            verbose=args.verbose,
        )
    # 2. Deck de Teste Isolado
    elif args.test_deck:
        report = AuditReport()
        pres = resolve_presentation(args.test_deck, offline=args.offline)
        report.results.extend(verify_test_deck(pres))
    # 3. Deck de Desafio Isolado
    elif args.challenge_deck:
        report = AuditReport()
        pres = resolve_presentation(args.challenge_deck, offline=args.offline)
        report.results.extend(
            verify_challenge_deck(pres, expected_question_id=args.expected_n3_id)
        )
    # 4. Deck Regular Isolado
    elif args.regular_deck:
        report = AuditReport()
        pres = resolve_presentation(args.regular_deck, offline=args.offline)
        report.results.extend(verify_regular_deck(pres))
    # 5. Deck de Desempate Isolado
    elif args.tiebreaker_deck:
        report = AuditReport()
        pres = resolve_presentation(args.tiebreaker_deck, offline=args.offline)
        report.results.extend(verify_tiebreaker_deck(pres))
    # 6. Modo Legado (Full Audit ou Regras/QA)
    else:
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
            "manifest_path": report.manifest_path,
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
