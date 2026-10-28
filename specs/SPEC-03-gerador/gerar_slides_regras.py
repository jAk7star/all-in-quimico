"""
gerar_slides_regras.py — Gerador Reprodutível do Deck de Regras do All-In Químico.

Design System: Itaú Private / Fintech Clean / CrewDeck Anti-Vibe
- Fundo Off-White (#F8F9FA) de alta acessibilidade visual (WCAG AAA)
- Tipografia sem serifa Open Sans (abertura ampla de olho)
- Respiro matemático de 8px e contenção da carga cognitiva (max-w-prose)
- Psicologia das cores: Azul Cobalto (Institucional), Âmbar (Destaques), Verde Esmeralda (Pagamentos)

Gera o arquivo batch_regras_all_in.json contendo todas as operações batch
necessárias para renderizar no Google Slides a apresentação didática oficial (6 slides):
1. Capa Principal
2. Kit Inicial de Cédulas & Limite de Aposta (R$ 1.000 por grupo, economia R$ 10.000)
3. Regras de Bonificação por Rodada (Dobro x2 para 1-4 acertos, +R$ 100 unânime)
4. Tabela Oficial de Pagamentos e Cédulas (Matriz de pagamentos 6x4)
5. Desafio da Mesa — Tudo ou Nada Final (Empate técnico <= R$ 100 e Winner Takes All)
6. Roteiro Rápido de Aplicação em Sala (Passo a passo operacional das 5 rodadas)
"""

import argparse
import json
import shutil
import subprocess
from pathlib import Path

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

# Psicologia das Cores — Semântica Pedagógica e Financeira
COLOR_BRAND = "#0284C7"       # Azul Cobalto Institucional
COLOR_BRAND_BG = "#E0F2FE"    # Fundo azul suave
COLOR_AMBER = "#D97706"       # Âmbar / Laranja Queimado Institucional (Teto R$ 200)
COLOR_AMBER_BG = "#FEF3C7"    # Fundo âmbar suave

COLOR_GREEN = "#16A34A"       # Verde Fintech Esmeralda (Dobro x2 / Lucro)
COLOR_GREEN_BG = "#DCFCE7"    # Fundo verde suave
COLOR_GREEN_BORDER = "#BBF7D0"
COLOR_GREEN_TEXT = "#14532D"

COLOR_PURPLE = "#7C3AED"      # Roxo Ametista (Bônus Unânime / Desafio da Mesa)
COLOR_PURPLE_BG = "#F3E8FF"   # Fundo roxo suave
COLOR_PURPLE_TEXT = "#581C87"

COLOR_RED = "#DC2626"         # Vermelho Terracota (Erro / Caixa)
COLOR_RED_BG = "#FEE2E2"      # Fundo vermelho suave

DEFAULT_RULES_PRESENTATION_ID = "1KpfettWa9KkvbmBmhNAkyWRlTPPzahCeTVCuNlA3VU0"


def build_rules_batch() -> list[dict]:
    """Constrói a lista de operações batch para os 6 slides de regras oficiais em Design System Clean."""
    ops = []

    # =========================================================================
    # SLIDE 1: CAPA PRINCIPAL (Slide existente 'p')
    # =========================================================================
    ops.append({"op": "delete-element", "element": "i0"})
    ops.append({"op": "delete-element", "element": "i1"})
    ops.append({"op": "set-background", "slide": "p", "color": BG_MAIN})

    # Barra superior institucional (8px)
    ops.append({
        "op": "add-shape", "slide": "p", "shape_type": "RECTANGLE",
        "x": 0, "y": 0, "width": 720, "height": 6, "background_color": COLOR_BRAND,
    })

    # Badge de categoria
    ops.append({
        "op": "add-textbox", "slide": "p",
        "text": "DINÂMICA COMPETITIVA DE QUÍMICA • 5 EQUIPES",
        "x": 60, "y": 55, "width": 600, "height": 28,
        "font_size": 11.5, "bold": True, "color": COLOR_BRAND,
        "font_family": FONT_FAMILY, "alignment": "center", "content_alignment": "MIDDLE",
    })

    # Título principal
    ops.append({
        "op": "add-textbox", "slide": "p",
        "text": "ALL-IN QUÍMICO",
        "x": 40, "y": 85, "width": 640, "height": 72,
        "font_size": 48, "bold": True, "color": TEXT_PRIMARY,
        "font_family": FONT_FAMILY, "alignment": "center", "content_alignment": "MIDDLE",
    })

    # Subtítulo
    ops.append({
        "op": "add-textbox", "slide": "p",
        "text": "Sistema Oficial de Apostas, Multiplicador ×2 e Desafio da Mesa",
        "x": 60, "y": 158, "width": 600, "height": 32,
        "font_size": 16, "bold": True, "color": TEXT_SECONDARY,
        "font_family": FONT_FAMILY, "alignment": "center", "content_alignment": "MIDDLE",
    })

    # Linha divisória suave
    ops.append({
        "op": "add-shape", "slide": "p", "shape_type": "RECTANGLE",
        "x": 260, "y": 200, "width": 200, "height": 3, "background_color": COLOR_BRAND,
    })

    # 4 Stat Cards Elevados (Estilo Dashboard Fintech)
    cards_s1 = [
        ("R$ 1.000", "Saldo Inicial / Equipe", COLOR_BRAND, COLOR_BRAND_BG),
        ("Máx. R$ 200", "Teto por Rodada", COLOR_AMBER, COLOR_AMBER_BG),
        ("Dobro (×2)", "1 a 4 Grupos Acertando", COLOR_GREEN, COLOR_GREEN_BG),
        ("+R$ 100 Fixo", "Todos os 5 Acertando", COLOR_PURPLE, COLOR_PURPLE_BG),
    ]
    for i, (val, label, col, _col_bg) in enumerate(cards_s1):
        cx = 40 + i * 162
        ops.append({
            "op": "add-shape", "slide": "p", "shape_type": "ROUND_RECTANGLE",
            "x": cx, "y": 222, "width": 152, "height": 92,
            "background_color": BG_CARD, "outline_color": BORDER_SUBTLE, "outline_weight": 1.0,
        })
        ops.append({
            "op": "add-textbox", "slide": "p", "text": val,
            "x": cx + 6, "y": 230, "width": 140, "height": 36,
            "font_size": 18, "bold": True, "color": col,
            "font_family": FONT_FAMILY, "alignment": "center", "content_alignment": "MIDDLE",
        })
        ops.append({
            "op": "add-textbox", "slide": "p", "text": label,
            "x": cx + 6, "y": 268, "width": 140, "height": 38,
            "font_size": 10.5, "bold": True, "color": TEXT_SECONDARY,
            "font_family": FONT_FAMILY, "alignment": "center", "content_alignment": "TOP",
        })

    # Footer Banner
    ops.append({
        "op": "add-shape", "slide": "p", "shape_type": "ROUND_RECTANGLE",
        "x": 40, "y": 328, "width": 640, "height": 52,
        "background_color": BG_CARD, "outline_color": BORDER_SUBTLE, "outline_weight": 1.0,
    })
    ops.append({
        "op": "add-textbox", "slide": "p",
        "text": "5 Perguntas Regulares  •  Economia R$ 10.000  •  Apostas em Papel (Sem Placas)  •  Repescagem (+R$ 200 na 5ª Rodada)  •  Desafio da Mesa",
        "x": 48, "y": 336, "width": 624, "height": 36,
        "font_size": 10.5, "bold": True, "color": TEXT_MUTED,
        "font_family": FONT_FAMILY, "alignment": "center", "content_alignment": "MIDDLE",
    })

    ops.append({
        "op": "set-notes", "slide": "p",
        "text": (
            "SLIDE DE ABERTURA — APRESENTAÇÃO DIDÁTICA DO ALL-IN QUÍMICO\n\n"
            "Apresente aos estudantes a dinâmica competitiva de Química.\n"
            "5 equipes competem com saldo inicial de R$ 1.000 cada, com economia total de R$ 10.000.\n"
            "Apostas registradas exclusivamente em papel/folhas de aposta (sem placas).\n"
            "Teto máximo de aposta por pergunta: R$ 200.\n"
            "Inclui mecânica de Repescagem na 5ª rodada (+R$ 200 do Banco para equipe zerada ou com saldo <= R$ 200)."
        ),
    })

    # =========================================================================
    # SLIDE 2: KIT INICIAL DE CÉDULAS & LIMITE DE APOSTA
    # =========================================================================
    ops.append({"op": "add-slide", "layout": "BLANK", "id": "SLIDE_1"})
    ops.append({"op": "set-background", "slide": "SLIDE_1", "color": BG_MAIN})
    ops.append({
        "op": "add-shape", "slide": "SLIDE_1", "shape_type": "RECTANGLE",
        "x": 0, "y": 0, "width": 720, "height": 6, "background_color": COLOR_BRAND,
    })

    ops.append({
        "op": "add-textbox", "slide": "SLIDE_1",
        "text": "1. Kit Inicial de Cédulas & Limite de Aposta",
        "x": 35, "y": 16, "width": 650, "height": 34,
        "font_size": 24, "bold": True, "color": TEXT_PRIMARY,
        "font_family": FONT_FAMILY, "alignment": "left", "content_alignment": "MIDDLE",
    })
    ops.append({
        "op": "add-textbox", "slide": "SLIDE_1",
        "text": "Economia Total de R$ 10.000 (R$ 5.000 nos grupos + R$ 5.000 no Banco). Cada equipe começa com R$ 1.000 (aposta máx. R$ 200).",
        "x": 35, "y": 50, "width": 650, "height": 24,
        "font_size": 11.5, "color": TEXT_SECONDARY,
        "font_family": FONT_FAMILY, "alignment": "left", "content_alignment": "MIDDLE",
    })

    # 3 Cards de Cédulas
    bills = [
        ("R$ 100", "6 notas por grupo\n(Total = R$ 600)", "Ideal para apostas altas (R$ 100 a R$ 200) e pagamento do Bônus Unânime.", COLOR_BRAND, COLOR_BRAND_BG),
        ("R$ 50", "6 notas por grupo\n(Total = R$ 300)", "Permite compor apostas intermediárias (R$ 50, R$ 150) com agilidade.", COLOR_AMBER, COLOR_AMBER_BG),
        ("R$ 10", "10 notas por grupo\n(Total = R$ 100)", "Permite apostas estratégicas de qualquer múltiplo de R$ 10 sem moedas quebradas!", COLOR_GREEN, COLOR_GREEN_BG),
    ]
    for i, (b_val, b_tot, b_desc, b_col, b_bg) in enumerate(bills):
        bx = 35 + i * 222
        ops.append({
            "op": "add-shape", "slide": "SLIDE_1", "shape_type": "ROUND_RECTANGLE",
            "x": bx, "y": 80, "width": 208, "height": 164,
            "background_color": BG_CARD, "outline_color": BORDER_SUBTLE, "outline_weight": 1.0,
        })
        ops.append({
            "op": "add-textbox", "slide": "SLIDE_1", "text": b_val,
            "x": bx + 10, "y": 88, "width": 188, "height": 38,
            "font_size": 20, "bold": True, "color": b_col, "background_color": b_bg,
            "font_family": FONT_FAMILY, "alignment": "center", "content_alignment": "MIDDLE",
        })
        ops.append({
            "op": "add-textbox", "slide": "SLIDE_1", "text": b_tot,
            "x": bx + 10, "y": 130, "width": 188, "height": 38,
            "font_size": 11, "bold": True, "color": TEXT_PRIMARY,
            "font_family": FONT_FAMILY, "alignment": "center", "content_alignment": "MIDDLE",
        })
        ops.append({
            "op": "add-textbox", "slide": "SLIDE_1", "text": b_desc,
            "x": bx + 10, "y": 170, "width": 188, "height": 66,
            "font_size": 9.5, "color": TEXT_SECONDARY,
            "font_family": FONT_FAMILY, "line_spacing": 125, "alignment": "center", "content_alignment": "TOP",
        })

    # Banner Regras de Ouro
    ops.append({
        "op": "add-shape", "slide": "SLIDE_1", "shape_type": "ROUND_RECTANGLE",
        "x": 35, "y": 254, "width": 650, "height": 126,
        "background_color": BG_CARD, "outline_color": BORDER_SUBTLE, "outline_weight": 1.0,
    })
    ops.append({
        "op": "add-textbox", "slide": "SLIDE_1",
        "text": "REGRAS DE OURO DO CAIXA, GOVERNANÇA & REPESCAGEM",
        "x": 48, "y": 258, "width": 624, "height": 20,
        "font_size": 10.5, "bold": True, "color": COLOR_BRAND,
        "font_family": FONT_FAMILY, "alignment": "left", "content_alignment": "MIDDLE",
    })
    rules_text = (
        "• Economia de R$ 10.000: 5 grupos com R$ 1.000 (R$ 5.000) e Caixa do Professor com R$ 5.000 de reserva.\n"
        "• Sem Placas: Equipes utilizam papel/folha de aposta para anotar a alternativa e o valor apostado.\n"
        "• Teto Estrito por Pergunta: R$ 200 (mínimo de R$ 10 por rodada; mantém a competitividade nas 5 rodadas).\n"
        "• Repescagem na Última Rodada (+R$ 200): Na 5ª rodada, equipe zerada ou no limite (saldo ≤ R$ 200) recebe +R$ 200 do Banco (a fundo perdido) para jogar!\n"
        "• Reserva do Banco da Casa: 30 notas de R$ 100 (R$ 3.000), 30 notas de R$ 50 (R$ 1.500) e 50 notas de R$ 10 (R$ 500)."
    )
    ops.append({
        "op": "add-textbox", "slide": "SLIDE_1", "text": rules_text,
        "x": 48, "y": 278, "width": 624, "height": 98,
        "font_size": 9.5, "color": TEXT_PRIMARY,
        "font_family": FONT_FAMILY, "line_spacing": 122, "alignment": "left", "content_alignment": "TOP",
    })
    ops.append({
        "op": "set-notes", "slide": "SLIDE_1",
        "text": (
            "SLIDE 2 — KIT INICIAL E BANCA DA CASA\n\n"
            "Explique a composição exata das cédulas entregues a cada grupo:\n"
            "6 notas de R$ 100 (R$ 600) + 6 notas de R$ 50 (R$ 300) + 10 notas de R$ 10 (R$ 100) = R$ 1.000.\n"
            "A economia total do jogo é de R$ 10.000, dividida meio a meio entre estudantes e professor.\n"
            "As equipes devem utilizar a folha de aposta em papel (sem placas).\n"
            "Destaque a Repescagem na 5ª rodada: equipe zerada ou com saldo <= R$ 200 recebe +R$ 200 do Banco da Casa."
        ),
    })

    # =========================================================================
    # SLIDE 3: REGRAS DE BONIFICAÇÃO POR RODADA
    # =========================================================================
    ops.append({"op": "add-slide", "layout": "BLANK", "id": "SLIDE_2"})
    ops.append({"op": "set-background", "slide": "SLIDE_2", "color": BG_MAIN})
    ops.append({
        "op": "add-shape", "slide": "SLIDE_2", "shape_type": "RECTANGLE",
        "x": 0, "y": 0, "width": 720, "height": 6, "background_color": COLOR_GREEN,
    })

    ops.append({
        "op": "add-textbox", "slide": "SLIDE_2",
        "text": "2. Regras de Bonificação por Rodada",
        "x": 35, "y": 16, "width": 650, "height": 34,
        "font_size": 24, "bold": True, "color": TEXT_PRIMARY,
        "font_family": FONT_FAMILY, "alignment": "left", "content_alignment": "MIDDLE",
    })
    ops.append({
        "op": "add-textbox", "slide": "SLIDE_2",
        "text": "O pagamento depende de quantos grupos acertarem a resposta na rodada:",
        "x": 35, "y": 50, "width": 650, "height": 24,
        "font_size": 11.5, "color": TEXT_SECONDARY,
        "font_family": FONT_FAMILY, "alignment": "left", "content_alignment": "MIDDLE",
    })

    # Card 1 a 4 Grupos Acertando
    ops.append({
        "op": "add-shape", "slide": "SLIDE_2", "shape_type": "ROUND_RECTANGLE",
        "x": 35, "y": 80, "width": 315, "height": 224,
        "background_color": BG_CARD, "outline_color": BORDER_SUBTLE, "outline_weight": 1.0,
    })
    ops.append({
        "op": "add-textbox", "slide": "SLIDE_2",
        "text": "1, 2, 3 OU 4 GRUPOS ACERTARAM",
        "x": 45, "y": 88, "width": 295, "height": 32,
        "font_size": 11, "bold": True, "color": COLOR_GREEN_TEXT, "background_color": COLOR_GREEN_BG,
        "font_family": FONT_FAMILY, "alignment": "center", "content_alignment": "MIDDLE",
    })
    text_c1 = (
        "DOBRO DA APOSTA (×2)\n"
        "Lucro Líquido de +100%\n\n"
        "• A equipe mantém as notas que apostou e recebe do Banco o mesmo valor em lucro líquido!\n"
        "• Ex.: Apostou R$ 150 ➔ Recebe +R$ 150 (volta com R$ 300 para o caixa da equipe).\n"
        "• Ex.: Apostou R$ 200 ➔ Recebe +R$ 200 de lucro!"
    )
    ops.append({
        "op": "add-textbox", "slide": "SLIDE_2", "text": text_c1,
        "x": 48, "y": 126, "width": 289, "height": 170,
        "font_size": 11, "color": TEXT_PRIMARY,
        "font_family": FONT_FAMILY, "line_spacing": 130, "alignment": "left", "content_alignment": "TOP",
    })

    # Card Todos os 5 Grupos Acertando
    ops.append({
        "op": "add-shape", "slide": "SLIDE_2", "shape_type": "ROUND_RECTANGLE",
        "x": 370, "y": 80, "width": 315, "height": 224,
        "background_color": BG_CARD, "outline_color": BORDER_SUBTLE, "outline_weight": 1.0,
    })
    ops.append({
        "op": "add-textbox", "slide": "SLIDE_2",
        "text": "TODOS OS 5 GRUPOS ACERTARAM",
        "x": 380, "y": 88, "width": 295, "height": 32,
        "font_size": 11, "bold": True, "color": COLOR_PURPLE_TEXT, "background_color": COLOR_PURPLE_BG,
        "font_family": FONT_FAMILY, "alignment": "center", "content_alignment": "MIDDLE",
    })
    text_c2 = (
        "BÔNUS UNÂNIME (+R$ 100 FIXO)\n"
        "Independente do valor apostado!\n\n"
        "• Quando todas as 5 equipes acertam juntas, o multiplicador ×2 é neutralizado.\n"
        "• Cada equipe recupera sua aposta e ganha exatamente 1 nota de R$ 100!\n"
        "• Equilibra o jogo: quem apostou R$ 50 ou R$ 200 ganham os mesmos +R$ 100!"
    )
    ops.append({
        "op": "add-textbox", "slide": "SLIDE_2", "text": text_c2,
        "x": 383, "y": 126, "width": 289, "height": 170,
        "font_size": 11, "color": TEXT_PRIMARY,
        "font_family": FONT_FAMILY, "line_spacing": 130, "alignment": "left", "content_alignment": "TOP",
    })

    # Banner de Erro
    ops.append({
        "op": "add-shape", "slide": "SLIDE_2", "shape_type": "ROUND_RECTANGLE",
        "x": 35, "y": 316, "width": 650, "height": 64,
        "background_color": COLOR_RED_BG, "outline_color": "#FECACA", "outline_weight": 1.0,
    })
    ops.append({
        "op": "add-textbox", "slide": "SLIDE_2",
        "text": "❌ SE A EQUIPE ERRAR A PERGUNTA: Perde integralmente o valor apostado na rodada, recolhido pelo Banco da Casa.",
        "x": 48, "y": 326, "width": 624, "height": 44,
        "font_size": 11.5, "bold": True, "color": COLOR_RED,
        "font_family": FONT_FAMILY, "alignment": "center", "content_alignment": "MIDDLE",
    })

    ops.append({
        "op": "set-notes", "slide": "SLIDE_2",
        "text": (
            "SLIDE 3 — MECÂNICA DE LIQUIDAÇÃO\n\n"
            "Enfatize a diferença entre os cenários:\n"
            "1 a 4 acertos: Pagamento dobrado (+100% de lucro líquido).\n"
            "5 acertos: Bônus unânime fixo (+R$ 100), reduzindo a disparidade entre estratégias conservadoras e agressivas.\n"
            "Erros: O montante apostado vai para o Caixa da Casa."
        ),
    })

    # =========================================================================
    # SLIDE 4: TABELA OFICIAL DE PAGAMENTOS E CÉDULAS
    # =========================================================================
    ops.append({"op": "add-slide", "layout": "BLANK", "id": "SLIDE_3"})
    ops.append({"op": "set-background", "slide": "SLIDE_3", "color": BG_MAIN})
    ops.append({
        "op": "add-shape", "slide": "SLIDE_3", "shape_type": "RECTANGLE",
        "x": 0, "y": 0, "width": 720, "height": 6, "background_color": COLOR_AMBER,
    })

    ops.append({
        "op": "add-textbox", "slide": "SLIDE_3",
        "text": "3. Tabela Oficial de Pagamentos e Cédulas",
        "x": 35, "y": 14, "width": 650, "height": 32,
        "font_size": 24, "bold": True, "color": TEXT_PRIMARY,
        "font_family": FONT_FAMILY, "alignment": "left", "content_alignment": "MIDDLE",
    })
    ops.append({
        "op": "add-textbox", "slide": "SLIDE_3",
        "text": "Consulta rápida para o Banco da Casa liquidar cada rodada usando cédulas de R$ 10, R$ 50 e R$ 100:",
        "x": 35, "y": 46, "width": 650, "height": 22,
        "font_size": 11.5, "color": TEXT_SECONDARY,
        "font_family": FONT_FAMILY, "alignment": "left", "content_alignment": "MIDDLE",
    })

    # Tabela 6x4
    ops.append({
        "op": "add-table", "slide": "SLIDE_3", "rows": 6, "cols": 4, "id": "TABLE_PAG",
        "x": 35, "y": 74, "width": 650, "height": 236,
    })

    headers = [
        ("Valor Apostado", BG_CARD_SUBTLE, TEXT_PRIMARY),
        ("1 a 4 Acertos (Dobro: +100%)", COLOR_GREEN_BG, COLOR_GREEN_TEXT),
        ("Todos os 5 Acertos (+R$ 100)", COLOR_PURPLE_BG, COLOR_PURPLE_TEXT),
        ("Se Errar (Perde Aposta)", COLOR_RED_BG, COLOR_RED),
    ]
    for c, (h_txt, h_bg, h_col) in enumerate(headers):
        ops.append({
            "op": "set-table-cell", "table": "TABLE_PAG", "row": 0, "col": c,
            "text": h_txt, "bold": True, "font_size": 11, "color": h_col,
            "background_color": h_bg, "font_family": FONT_FAMILY,
        })

    row_data = [
        ("R$ 10 a R$ 40", "+R$ 10 a +R$ 40 (1 a 4 notas de 10)", "+R$ 100 (1 nota de 100)", "-R$ 10 a -R$ 40"),
        ("R$ 50", "+R$ 50 (1 nota de 50)", "+R$ 100 (1 nota de 100)", "-R$ 50"),
        ("R$ 100", "+R$ 100 (1 nota de 100)", "+R$ 100 (1 nota de 100)", "-R$ 100"),
        ("R$ 150", "+R$ 150 (1x100 + 1x50)", "+R$ 100 (1 nota de 100)", "-R$ 150"),
        ("R$ 200 (Máx.)", "+R$ 200 (2 notas de 100)", "+R$ 100 (1 nota de 100)", "-R$ 200"),
    ]
    for r, r_vals in enumerate(row_data, start=1):
        bg_row = BG_CARD if r % 2 == 1 else BG_CARD_SUBTLE
        for c, val in enumerate(r_vals):
            col_txt = TEXT_PRIMARY if c == 0 else (COLOR_GREEN_TEXT if c == 1 else (COLOR_PURPLE_TEXT if c == 2 else COLOR_RED))
            ops.append({
                "op": "set-table-cell", "table": "TABLE_PAG", "row": r, "col": c,
                "text": val, "bold": (c == 0 or r == 5), "font_size": 10.5, "color": col_txt,
                "background_color": bg_row, "font_family": FONT_FAMILY,
            })

    # Callout Educacional & Repescagem
    ops.append({
        "op": "add-shape", "slide": "SLIDE_3", "shape_type": "ROUND_RECTANGLE",
        "x": 35, "y": 320, "width": 650, "height": 60,
        "background_color": COLOR_AMBER_BG, "outline_color": "#FDE68A", "outline_weight": 1.0,
    })
    ops.append({
        "op": "add-textbox", "slide": "SLIDE_3",
        "text": "💡 EFEITO ESTRATÉGICO & REPESCAGEM (5ª RODADA): Se todos os 5 acertarem, qualquer aposta rende +R$ 100 fixos. Na última rodada (5ª), equipe zerada ou no limite (saldo ≤ R$ 200) recebe +R$ 200 do Banco (fundo perdido) para apostar até R$ 200 e dobrar normalmente (×2 ➔ R$ 400)!",
        "x": 48, "y": 324, "width": 624, "height": 52,
        "font_size": 10, "bold": True, "color": "#78350F",
        "font_family": FONT_FAMILY, "alignment": "center", "content_alignment": "MIDDLE",
    })

    ops.append({
        "op": "set-notes", "slide": "SLIDE_3",
        "text": (
            "SLIDE 4 — TABELA DE LIQUIDAÇÃO\n\n"
            "Deixe este slide projetado durante a resolução para orientar as apostas das equipes.\n"
            "A tabela elimina dúvidas operacionais de troco no Caixa da Casa."
        ),
    })

    # =========================================================================
    # SLIDE 5: DESAFIO DA MESA — TUDO OU NADA FINAL
    # =========================================================================
    ops.append({"op": "add-slide", "layout": "BLANK", "id": "SLIDE_4"})
    ops.append({"op": "set-background", "slide": "SLIDE_4", "color": BG_MAIN})
    ops.append({
        "op": "add-shape", "slide": "SLIDE_4", "shape_type": "RECTANGLE",
        "x": 0, "y": 0, "width": 720, "height": 6, "background_color": COLOR_PURPLE,
    })

    ops.append({
        "op": "add-textbox", "slide": "SLIDE_4",
        "text": "4. Desafio da Mesa — Tudo ou Nada Final!",
        "x": 35, "y": 14, "width": 650, "height": 32,
        "font_size": 24, "bold": True, "color": TEXT_PRIMARY,
        "font_family": FONT_FAMILY, "alignment": "left", "content_alignment": "MIDDLE",
    })
    ops.append({
        "op": "add-textbox", "slide": "SLIDE_4",
        "text": "O clímax após a 5ª rodada: saldos unificados na mesa — quem acertar leva tudo e o outro zera!",
        "x": 35, "y": 46, "width": 650, "height": 22,
        "font_size": 11.5, "color": TEXT_SECONDARY,
        "font_family": FONT_FAMILY, "alignment": "left", "content_alignment": "MIDDLE",
    })

    mesa_steps = [
        ("1. GATILHO: EMPATE TÉCNICO", "Diferença ≤ R$ 100 do Líder", "Ao fim da 5ª pergunta, qualquer equipe empatada ou a até R$ 100 do 1º colocado (apenas 1 nota de 100) entra automaticamente no Desafio da Mesa!", COLOR_PURPLE, COLOR_PURPLE_BG),
        ("2. POTE UNIFICADO NA MESA", "100% dos Saldos no Centro", "As equipes convocadas colocam todo o dinheiro acumulado no centro da mesa, formando um Pote Único Gigante (ex.: R$ 1.200 + R$ 1.150 = R$ 2.350)!", COLOR_AMBER, COLOR_AMBER_BG),
        ("3. WINNER TAKES ALL", "Quem Ganhar Leva Tudo!", "Pergunta decisiva sorteada. Quem levantar a mão primeiro e acertar leva 100% do pote e os rivais saem zerados (se errar, a vez passa ao adversário).", COLOR_GREEN, COLOR_GREEN_BG),
    ]
    for i, (m_title, m_sub, m_desc, m_col, m_bg) in enumerate(mesa_steps):
        mx = 35 + i * 222
        ops.append({
            "op": "add-shape", "slide": "SLIDE_4", "shape_type": "ROUND_RECTANGLE",
            "x": mx, "y": 76, "width": 208, "height": 194,
            "background_color": BG_CARD, "outline_color": BORDER_SUBTLE, "outline_weight": 1.0,
        })
        ops.append({
            "op": "add-textbox", "slide": "SLIDE_4", "text": m_title,
            "x": mx + 8, "y": 84, "width": 192, "height": 28,
            "font_size": 10, "bold": True, "color": m_col, "background_color": m_bg,
            "font_family": FONT_FAMILY, "alignment": "center", "content_alignment": "MIDDLE",
        })
        ops.append({
            "op": "add-textbox", "slide": "SLIDE_4", "text": m_sub,
            "x": mx + 8, "y": 116, "width": 192, "height": 26,
            "font_size": 11, "bold": True, "color": TEXT_PRIMARY,
            "font_family": FONT_FAMILY, "alignment": "center", "content_alignment": "MIDDLE",
        })
        ops.append({
            "op": "add-textbox", "slide": "SLIDE_4", "text": m_desc,
            "x": mx + 8, "y": 146, "width": 192, "height": 116,
            "font_size": 10, "color": TEXT_SECONDARY,
            "font_family": FONT_FAMILY, "line_spacing": 130, "alignment": "center", "content_alignment": "TOP",
        })

    # Validação Monte Carlo Banner
    ops.append({
        "op": "add-shape", "slide": "SLIDE_4", "shape_type": "ROUND_RECTANGLE",
        "x": 35, "y": 280, "width": 650, "height": 100,
        "background_color": BG_CARD, "outline_color": BORDER_SUBTLE, "outline_weight": 1.0,
    })
    ops.append({
        "op": "add-textbox", "slide": "SLIDE_4",
        "text": "📊 VALIDAÇÃO ESTATÍSTICA — MONTE CARLO (100.000 PARTIDAS)",
        "x": 48, "y": 286, "width": 624, "height": 20,
        "font_size": 10, "bold": True, "color": COLOR_BRAND,
        "font_family": FONT_FAMILY, "alignment": "left", "content_alignment": "MIDDLE",
    })
    mc_text = (
        "• Empate Matemático Exato: Ocorre em apenas ~2,6% a ~10,7% das partidas devido às múltiplas combinações de apostas.\n"
        "• Regra do Empate Técnico (Margem ≤ R$ 100): Eleva a ativação do Desafio da Mesa para ~44,3% a ~46,4% das aulas!\n"
        "• Resultado Pedagógico: Mantém a adrenalina e a disputa viva até o último minuto sem retirar o mérito de quem abrir grande vantagem (> R$ 100)."
    )
    ops.append({
        "op": "add-textbox", "slide": "SLIDE_4", "text": mc_text,
        "x": 48, "y": 308, "width": 624, "height": 66,
        "font_size": 10, "color": TEXT_PRIMARY,
        "font_family": FONT_FAMILY, "line_spacing": 130, "alignment": "left", "content_alignment": "TOP",
    })

    ops.append({
        "op": "set-notes", "slide": "SLIDE_4",
        "text": (
            "SLIDE 5 — DESAFIO DA MESA (TUDO OU NADA)\n\n"
            "Explique as três fases do clímax final:\n"
            "1. Convocação das equipes na margem de até R$ 100 do líder.\n"
            "2. Formação do pote unificado no centro da mesa.\n"
            "3. Pergunta decisiva onde quem acerta leva tudo e o adversário zera."
        ),
    })

    # =========================================================================
    # SLIDE 6: ROTEIRO RÁPIDO DE APLICAÇÃO EM SALA
    # =========================================================================
    ops.append({"op": "add-slide", "layout": "BLANK", "id": "SLIDE_5"})
    ops.append({"op": "set-background", "slide": "SLIDE_5", "color": BG_MAIN})
    ops.append({
        "op": "add-shape", "slide": "SLIDE_5", "shape_type": "RECTANGLE",
        "x": 0, "y": 0, "width": 720, "height": 6, "background_color": COLOR_BRAND,
    })

    ops.append({
        "op": "add-textbox", "slide": "SLIDE_5",
        "text": "5. Roteiro Rápido de Aplicação em Sala",
        "x": 35, "y": 14, "width": 650, "height": 32,
        "font_size": 24, "bold": True, "color": TEXT_PRIMARY,
        "font_family": FONT_FAMILY, "alignment": "left", "content_alignment": "MIDDLE",
    })
    ops.append({
        "op": "add-textbox", "slide": "SLIDE_5",
        "text": "Fluxo operacional passo a passo para cada uma das 5 rodadas + encerramento:",
        "x": 35, "y": 46, "width": 650, "height": 22,
        "font_size": 11.5, "color": TEXT_SECONDARY,
        "font_family": FONT_FAMILY, "alignment": "left", "content_alignment": "MIDDLE",
    })

    steps = [
        ("PASSO 1 — Revelação do Tema, Aposta em Papel & Cédulas (30s)", "O professor anuncia o tema da questão (ex.: Estequiometria). Cada equipe anota na folha de aposta o valor (mín. R$ 10, máx. R$ 200) e separa as cédulas físicas na mesa.", COLOR_BRAND_BG, COLOR_BRAND),
        ("PASSO 2 — Resolução & Entrega / Revelação do Papel (60s a 90s)", "A questão é projetada. Cada grupo registra por escrito na folha de aposta a alternativa escolhida (A ou B) junto ao valor apostado, sem o uso de placas.", COLOR_AMBER_BG, COLOR_AMBER),
        ("PASSO 3 — Pagamento do Banco da Casa", "• 1 a 4 grupos acertaram? Dobram a aposta (+100% de lucro líquido).\n• Todos os 5 acertaram? Bônus unânime fixo de +R$ 100 para cada grupo  |  Erros: A aposta vai para o Caixa.", COLOR_GREEN_BG, COLOR_GREEN_TEXT),
        ("PASSO 4 — Repescagem na 5ª Rodada (+R$ 200) & Desafio da Mesa", "Antes da 5ª pergunta, equipes zeradas ou no limite (≤ R$ 200) recebem +R$ 200 do Banco (fundo perdido; se acertar, dobra ×2). Após a 5ª pergunta, equipes a ≤ R$ 100 do 1º colocado disputam o Desafio da Mesa (Winner Takes All)!", COLOR_PURPLE_BG, COLOR_PURPLE_TEXT),
    ]
    for i, (s_title, s_desc, _s_bg, s_col) in enumerate(steps):
        sy = 74 + i * 76
        ops.append({
            "op": "add-shape", "slide": "SLIDE_5", "shape_type": "ROUND_RECTANGLE",
            "x": 35, "y": sy, "width": 650, "height": 70,
            "background_color": BG_CARD, "outline_color": BORDER_SUBTLE, "outline_weight": 1.0,
        })
        ops.append({
            "op": "add-textbox", "slide": "SLIDE_5", "text": s_title,
            "x": 48, "y": sy + 6, "width": 624, "height": 22,
            "font_size": 11, "bold": True, "color": s_col,
            "font_family": FONT_FAMILY, "alignment": "left", "content_alignment": "MIDDLE",
        })
        ops.append({
            "op": "add-textbox", "slide": "SLIDE_5", "text": s_desc,
            "x": 48, "y": sy + 28, "width": 624, "height": 36,
            "font_size": 10, "color": TEXT_PRIMARY,
            "font_family": FONT_FAMILY, "line_spacing": 125, "alignment": "left", "content_alignment": "TOP",
        })

    ops.append({
        "op": "set-notes", "slide": "SLIDE_5",
        "text": (
            "SLIDE 6 — ROTEIRO OPERACIONAL DE SALA\n\n"
            "Guia de condução dinâmica para o professor sincronizar o tempo das equipes.\n"
            "Controle rigoroso dos 30s de aposta e 60-90s de resolução."
        ),
    })

    return ops


def run_gslides(args: list[str]) -> subprocess.CompletedProcess:
    """Executa o comando gslides de forma portável."""
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
    """Aplica operações batch in-place a uma apresentação Google Slides (limpando slides anteriores se existirem)."""
    info_res = run_gslides(["readonly", "info", presentation_id, "--json"])
    if info_res.returncode != 0:
        raise RuntimeError(f"Falha ao inspecionar apresentação {presentation_id}:\n{info_res.stderr}")

    pres_data = json.loads(info_res.stdout)
    slides = pres_data.get("slides", [])
    cleanup_ops = []

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
        print(f"Sucesso: batch de regras aplicado in-place à apresentação {presentation_id}.")
    finally:
        if temp_batch.exists():
            temp_batch.unlink()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Gera batch de regras do All-In Químico no Google Slides."
    )
    parser.add_argument(
        "--presentation-id",
        type=str,
        default=DEFAULT_RULES_PRESENTATION_ID,
        help="ID da apresentação no Google Slides",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parent / "batch_regras_all_in.json",
        help="Caminho do arquivo batch JSON de saída",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Aplica o batchUpdate diretamente na apresentação via gslides CLI",
    )
    args = parser.parse_args()

    print("Gerando operações batch para os 6 slides de regras (Design Fintech Clean)...")
    ops = build_rules_batch()
    print(f"Total de operações de regras geradas: {len(ops)}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        json.dump(ops, f, ensure_ascii=False, indent=2)
    print(f"Arquivo batch de regras salvo em: {args.output}")

    if args.apply:
        print(f"Aplicando à apresentação de regras no Google Slides: {args.presentation_id}")
        apply_batch_to_deck(args.presentation_id, args.output)


if __name__ == "__main__":
    main()
