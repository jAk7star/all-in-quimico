"""
gerar_slides_regras.py — Gerador Reprodutível do Deck de Regras do All-In Químico.

Gera o arquivo batch_regras_all_in.json contendo todas as operações batch
necessárias para renderizar no Google Slides a apresentação didática oficial (6 slides):
1. Capa Principal (Identidade Visual Dark Navy / Gold / Cyan / Emerald)
2. Kit Inicial de Cédulas & Limite de Aposta (R$ 1.000 por grupo, economia R$ 10.000)
3. Regras de Bonificação por Rodada (Dobro x2 para 1-4 acertos, +R$ 100 unânime)
4. Tabela Oficial de Pagamentos e Cédulas (Matriz de pagamentos 6x4)
5. Desafio da Mesa — Tudo ou Nada Final (Empate técnico <= R$ 100 e Winner Takes All)
6. Roteiro Rápido de Aplicação em Sala (Passo a passo operacional das 5 rodadas)
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

# Paleta oficial (Dark Navy / Slate / Ouro / Ciano / Esmeralda / Roxo)
BG_DARK = "#0F172A"  # Slate 900
BG_CARD = "#1E293B"  # Slate 800
BG_LIGHT = "#F8FAFC"  # Slate 50
TEXT_WHITE = "#FFFFFF"
TEXT_DARK = "#0F172A"
TEXT_MUTED = "#94A3B8"
TEXT_SLATE = "#475569"
TEXT_CARD = "#1E293B"

GOLD = "#F59E0B"  # Amber 500
CYAN = "#38BDF8"  # Sky 400
GREEN = "#22C55E"  # Green 500
PURPLE = "#D8B4FE"  # Purple 300
PURPLE_DEEP = "#7E22CE"  # Purple 700
RED = "#EF4444"  # Red 500
RED_DEEP = "#7F1D1D"  # Red 900

DEFAULT_RULES_PRESENTATION_ID = "1KpfettWa9KkvbmBmhNAkyWRlTPPzahCeTVCuNlA3VU0"


def build_rules_batch() -> list[dict]:
    """Constrói a lista de operações batch para os 6 slides de regras oficiais."""
    ops = []

    # =========================================================================
    # SLIDE 1: CAPA PRINCIPAL (Slide existente 'p')
    # =========================================================================
    ops.append({"op": "delete-element", "element": "i0"})
    ops.append({"op": "delete-element", "element": "i1"})
    ops.append({"op": "set-background", "slide": "p", "color": BG_DARK})

    # Barra de destaque superior
    ops.append(
        {
            "op": "add-shape",
            "slide": "p",
            "shape_type": "RECTANGLE",
            "x": 0,
            "y": 0,
            "width": 720,
            "height": 8,
            "background_color": GOLD,
        }
    )

    # Badge de categoria
    ops.append(
        {
            "op": "add-textbox",
            "slide": "p",
            "text": "DINÂMICA COMPETITIVA DE QUÍMICA • 5 EQUIPES",
            "x": 60,
            "y": 65,
            "width": 600,
            "height": 28,
            "font_size": 13,
            "bold": True,
            "color": CYAN,
            "font_family": "Montserrat",
            "alignment": "center",
            "content_alignment": "TOP",
        }
    )

    # Título principal
    ops.append(
        {
            "op": "add-textbox",
            "slide": "p",
            "text": "ALL-IN QUÍMICO",
            "x": 40,
            "y": 100,
            "width": 640,
            "height": 75,
            "font_size": 52,
            "bold": True,
            "color": GOLD,
            "font_family": "Montserrat",
            "alignment": "center",
            "content_alignment": "TOP",
        }
    )

    # Subtítulo
    ops.append(
        {
            "op": "add-textbox",
            "slide": "p",
            "text": "Sistema Oficial de Apostas, Multiplicador ×2 e Desafio da Mesa",
            "x": 60,
            "y": 178,
            "width": 600,
            "height": 36,
            "font_size": 18,
            "bold": True,
            "color": BG_LIGHT,
            "font_family": "Roboto",
            "alignment": "center",
            "content_alignment": "TOP",
        }
    )

    # Linha divisória
    ops.append(
        {
            "op": "add-shape",
            "slide": "p",
            "shape_type": "RECTANGLE",
            "x": 260,
            "y": 225,
            "width": 200,
            "height": 4,
            "background_color": CYAN,
        }
    )

    # 4 Stat Cards
    cards_s1 = [
        ("R$ 1.000\nSaldo Inicial / Equipe", TEXT_WHITE, 16),
        ("Máx. R$ 200\nTeto por Rodada", GOLD, 16),
        ("Dobro (×2)\n1 a 4 Grupos Acertando", GREEN, 15),
        ("+R$ 100 Fixo\nTodos os 5 Acertando", PURPLE, 15),
    ]
    for i, (txt, col, fsz) in enumerate(cards_s1):
        cx = 45 + i * 160
        ops.append(
            {
                "op": "add-textbox",
                "slide": "p",
                "text": txt,
                "x": cx,
                "y": 255,
                "width": 145 if i < 3 else 150,
                "height": 75,
                "font_size": fsz,
                "bold": True,
                "color": col,
                "background_color": BG_CARD,
                "font_family": "Roboto",
                "alignment": "center",
                "content_alignment": "MIDDLE",
            }
        )

    # Rodapé institucional
    ops.append(
        {
            "op": "add-textbox",
            "slide": "p",
            "text": "5 Perguntas Regulares  •  Economia R$ 10.000  •  Apostas em Papel (Sem Placas)  •  Desafio Final Tudo ou Nada",
            "x": 40,
            "y": 355,
            "width": 640,
            "height": 28,
            "font_size": 12,
            "color": TEXT_MUTED,
            "font_family": "Roboto",
            "alignment": "center",
            "content_alignment": "TOP",
        }
    )

    ops.append(
        {
            "op": "set-notes",
            "slide": "p",
            "text": "Slide de abertura: apresente a dinâmica All-In Químico. São 5 grupos competindo ao longo de 5 perguntas regulares de Química (Soluções, Estequiometria e Química Ambiental), usando cédulas físicas de R$ 10, R$ 50 e R$ 100.",
        }
    )

    # =========================================================================
    # SLIDE 2: KIT INICIAL DE CÉDULAS & LIMITE DE APOSTA
    # =========================================================================
    ops.append({"op": "add-slide", "layout": "BLANK", "id": "SLIDE_2"})
    ops.append({"op": "set-background", "slide": "SLIDE_2", "color": BG_LIGHT})
    ops.append(
        {
            "op": "add-shape",
            "slide": "SLIDE_2",
            "shape_type": "RECTANGLE",
            "x": 0,
            "y": 0,
            "width": 720,
            "height": 6,
            "background_color": BG_DARK,
        }
    )
    ops.append(
        {
            "op": "add-textbox",
            "slide": "SLIDE_2",
            "text": "1. Kit Inicial de Cédulas & Limite de Aposta",
            "x": 35,
            "y": 18,
            "width": 650,
            "height": 38,
            "font_size": 26,
            "bold": True,
            "color": BG_DARK,
            "font_family": "Montserrat",
            "alignment": "left",
            "content_alignment": "TOP",
        }
    )
    ops.append(
        {
            "op": "add-textbox",
            "slide": "SLIDE_2",
            "text": "Economia Total de R$ 10.000 (R$ 5.000 nos grupos + R$ 5.000 no Banco). Cada equipe começa com R$ 1.000 (aposta máx. R$ 200).",
            "x": 35,
            "y": 54,
            "width": 650,
            "height": 24,
            "font_size": 13,
            "color": TEXT_SLATE,
            "font_family": "Roboto",
            "alignment": "left",
            "content_alignment": "TOP",
        }
    )

    # 3 Colunas de Cédulas
    cedulas = [
        (
            "R$ 100",
            "#1E3A8A",
            "#DBEAFE",
            "6 notas por grupo\n(Total = R$ 600)\n\nIdeal para apostas altas (R$ 100 a R$ 200) e pagamento do Bônus Unânime.",
            35,
        ),
        (
            "R$ 50",
            "#B45309",
            "#FEF3C7",
            "6 notas por grupo\n(Total = R$ 300)\n\nPermite compor apostas intermediárias (R$ 50, R$ 150) com agilidade.",
            257,
        ),
        (
            "R$ 10",
            "#065F46",
            "#D1FAE5",
            "10 notas por grupo\n(Total = R$ 100)\n\nPermite apostas estratégicas de qualquer múltiplo de R$ 10 sem moedas quebradas!",
            480,
        ),
    ]
    for val_txt, hdr_bg, body_bg, desc_txt, x_pos in cedulas:
        ops.append(
            {
                "op": "add-textbox",
                "slide": "SLIDE_2",
                "text": val_txt,
                "x": x_pos,
                "y": 90,
                "width": 205,
                "height": 42,
                "font_size": 22,
                "bold": True,
                "color": TEXT_WHITE,
                "background_color": hdr_bg,
                "font_family": "Montserrat",
                "alignment": "center",
                "content_alignment": "MIDDLE",
            }
        )
        ops.append(
            {
                "op": "add-textbox",
                "slide": "SLIDE_2",
                "text": desc_txt,
                "x": x_pos,
                "y": 132,
                "width": 205,
                "height": 110,
                "font_size": 12,
                "color": TEXT_CARD,
                "background_color": body_bg,
                "font_family": "Roboto",
                "alignment": "center",
                "content_alignment": "MIDDLE",
            }
        )

    # Regras de Ouro do Caixa
    ops.append(
        {
            "op": "add-textbox",
            "slide": "SLIDE_2",
            "text": "REGRAS DE OURO DO CAIXA (SEM MOEDAS QUEBRADAS)",
            "x": 35,
            "y": 258,
            "width": 650,
            "height": 28,
            "font_size": 14,
            "bold": True,
            "color": TEXT_WHITE,
            "background_color": BG_DARK,
            "font_family": "Montserrat",
            "alignment": "center",
            "content_alignment": "MIDDLE",
        }
    )
    ops.append(
        {
            "op": "add-textbox",
            "slide": "SLIDE_2",
            "text": "• Economia de R$ 10.000: 5 grupos com R$ 1.000 (R$ 5.000) e Caixa do Professor com R$ 5.000 de reserva.\n• Sem Placas: Equipes utilizam papel/folha de aposta para anotar a alternativa e o valor apostado.\n• Teto Estrito por Pergunta: R$ 200 (mantém a sustentabilidade e competitividade nas 5 rodadas).\n• Reserva do Banco da Casa: 30 notas de R$ 100 (R$ 3.000), 30 notas de R$ 50 (R$ 1.500) e 50 notas de R$ 10 (R$ 500).",
            "x": 35,
            "y": 286,
            "width": 650,
            "height": 95,
            "font_size": 12,
            "color": TEXT_CARD,
            "background_color": "#E2E8F0",
            "font_family": "Roboto",
            "alignment": "left",
            "content_alignment": "TOP",
        }
    )
    ops.append(
        {
            "op": "set-notes",
            "slide": "SLIDE_2",
            "text": "Explique o kit inicial entregue a cada grupo (R$ 1.000 = 6x100 + 6x50 + 10x10) e por que o limite de R$ 200 impede que um grupo quebre na primeira pergunta. Destaque que com a regra do Multiplicador x2 puro para 1 a 4 grupos, nunca há troco quebrado.",
        }
    )

    # =========================================================================
    # SLIDE 3: REGRAS DE BONIFICAÇÃO POR RODADA
    # =========================================================================
    ops.append({"op": "add-slide", "layout": "BLANK", "id": "SLIDE_3"})
    ops.append({"op": "set-background", "slide": "SLIDE_3", "color": BG_DARK})
    ops.append(
        {
            "op": "add-shape",
            "slide": "SLIDE_3",
            "shape_type": "RECTANGLE",
            "x": 0,
            "y": 0,
            "width": 720,
            "height": 6,
            "background_color": GREEN,
        }
    )
    ops.append(
        {
            "op": "add-textbox",
            "slide": "SLIDE_3",
            "text": "2. Regras de Bonificação por Rodada",
            "x": 35,
            "y": 18,
            "width": 650,
            "height": 38,
            "font_size": 26,
            "bold": True,
            "color": GOLD,
            "font_family": "Montserrat",
            "alignment": "left",
            "content_alignment": "TOP",
        }
    )
    ops.append(
        {
            "op": "add-textbox",
            "slide": "SLIDE_3",
            "text": "O pagamento depende de quantos grupos acertarem a resposta na rodada:",
            "x": 35,
            "y": 54,
            "width": 650,
            "height": 24,
            "font_size": 13,
            "color": CYAN,
            "font_family": "Roboto",
            "alignment": "left",
            "content_alignment": "TOP",
        }
    )

    # Card Esquerdo: 1 a 4 grupos
    ops.append(
        {
            "op": "add-textbox",
            "slide": "SLIDE_3",
            "text": "1, 2, 3 OU 4 GRUPOS ACERTARAM",
            "x": 35,
            "y": 88,
            "width": 310,
            "height": 40,
            "font_size": 15,
            "bold": True,
            "color": BG_DARK,
            "background_color": GREEN,
            "font_family": "Montserrat",
            "alignment": "center",
            "content_alignment": "MIDDLE",
        }
    )
    ops.append(
        {
            "op": "add-textbox",
            "slide": "SLIDE_3",
            "text": "DOBRO DA APOSTA (×2)\nLucro Líquido de +100%\n\n• A equipe mantém as notas que apostou na mesa e recebe do Banco o mesmo valor em lucro!\n• Ex.: Apostou R$ 150 → Recebe +R$ 150 de lucro (volta com R$ 300 para a mão).\n• Ex.: Apostou R$ 200 → Recebe +R$ 200 de lucro!",
            "x": 35,
            "y": 128,
            "width": 310,
            "height": 185,
            "font_size": 12,
            "color": BG_LIGHT,
            "background_color": BG_CARD,
            "font_family": "Roboto",
            "alignment": "left",
            "content_alignment": "TOP",
        }
    )

    # Card Direito: Todos os 5 grupos
    ops.append(
        {
            "op": "add-textbox",
            "slide": "SLIDE_3",
            "text": "TODOS OS 5 GRUPOS ACERTARAM",
            "x": 375,
            "y": 88,
            "width": 310,
            "height": 40,
            "font_size": 15,
            "bold": True,
            "color": TEXT_WHITE,
            "background_color": PURPLE_DEEP,
            "font_family": "Montserrat",
            "alignment": "center",
            "content_alignment": "MIDDLE",
        }
    )
    ops.append(
        {
            "op": "add-textbox",
            "slide": "SLIDE_3",
            "text": "BÔNUS UNÂNIME (+R$ 100 FIXO)\nIndependente do valor apostado!\n\n• Quando as 5 equipes acertam juntas, o multiplicador ×2 é desativado.\n• Cada equipe recupera sua aposta e ganha exatamente 1 nota de R$ 100!\n• Equilibra a partida: quem apostou R$ 50 e quem apostou R$ 200 ganham os mesmos +R$ 100!",
            "x": 375,
            "y": 128,
            "width": 310,
            "height": 185,
            "font_size": 12,
            "color": BG_LIGHT,
            "background_color": BG_CARD,
            "font_family": "Roboto",
            "alignment": "left",
            "content_alignment": "TOP",
        }
    )

    # Alerta Inferior: Erro
    ops.append(
        {
            "op": "add-textbox",
            "slide": "SLIDE_3",
            "text": "❌ SE A EQUIPE ERRAR A PERGUNTA: Perde exatamente o valor que apostou na rodada (recolhido pelo Banco da Casa).",
            "x": 35,
            "y": 330,
            "width": 650,
            "height": 42,
            "font_size": 12,
            "bold": True,
            "color": TEXT_WHITE,
            "background_color": RED_DEEP,
            "font_family": "Roboto",
            "alignment": "center",
            "content_alignment": "MIDDLE",
        }
    )
    ops.append(
        {
            "op": "set-notes",
            "slide": "SLIDE_3",
            "text": "Apresente os três cenários de forma direta: 1 a 4 grupos acertando = Dobro do valor apostado (+100% de lucro líquido). Todos os 5 grupos acertando = Bônus fixo de +R$ 100 para cada equipe. Errou = perde o valor apostado.",
        }
    )

    # =========================================================================
    # SLIDE 4: TABELA OFICIAL DE PAGAMENTOS E CÉDULAS
    # =========================================================================
    ops.append({"op": "add-slide", "layout": "BLANK", "id": "SLIDE_4"})
    ops.append({"op": "set-background", "slide": "SLIDE_4", "color": BG_LIGHT})
    ops.append(
        {
            "op": "add-shape",
            "slide": "SLIDE_4",
            "shape_type": "RECTANGLE",
            "x": 0,
            "y": 0,
            "width": 720,
            "height": 6,
            "background_color": GOLD,
        }
    )
    ops.append(
        {
            "op": "add-textbox",
            "slide": "SLIDE_4",
            "text": "3. Tabela Oficial de Pagamentos e Cédulas",
            "x": 35,
            "y": 15,
            "width": 650,
            "height": 35,
            "font_size": 25,
            "bold": True,
            "color": BG_DARK,
            "font_family": "Montserrat",
            "alignment": "left",
            "content_alignment": "TOP",
        }
    )
    ops.append(
        {
            "op": "add-textbox",
            "slide": "SLIDE_4",
            "text": "Consulta rápida para o Banco da Casa pagar cada rodada usando apenas notas de R$ 10, R$ 50 e R$ 100:",
            "x": 35,
            "y": 48,
            "width": 650,
            "height": 22,
            "font_size": 12,
            "color": TEXT_SLATE,
            "font_family": "Roboto",
            "alignment": "left",
            "content_alignment": "TOP",
        }
    )

    # Tabela 6x4
    ops.append(
        {
            "op": "add-table",
            "slide": "SLIDE_4",
            "rows": 6,
            "cols": 4,
            "x": 35,
            "y": 76,
            "width": 650,
            "height": 240,
            "id": "TAB_REGRAS",
        }
    )

    table_data = [
        # Linha 0: Cabeçalhos
        [
            ("Valor Apostado", True, 10, TEXT_WHITE, BG_DARK),
            (
                "1 a 4 Grupos Acertaram\n(Dobro: +100% Lucro)",
                True,
                10,
                TEXT_WHITE,
                "#15803D",
            ),
            (
                "Todos os 5 Acertaram\n(Bônus Unânime Fixo)",
                True,
                10,
                TEXT_WHITE,
                PURPLE_DEEP,
            ),
            ("Se Errar a Resposta\n(Perde a Aposta)", True, 10, TEXT_WHITE, "#B91C1C"),
        ],
        # Linha 1: R$ 10 a R$ 40
        [
            ("R$ 10 a R$ 40", True, 9.5, BG_DARK, "#E2E8F0"),
            ("+R$ 10 a +R$ 40 (1 a 4 notas de 10)", False, 9.5, "#14532D", "#DCFCE7"),
            ("+R$ 100 (1 nota de 100)", False, 9.5, "#581C87", "#F3E8FF"),
            ("-R$ 10 a -R$ 40", False, 9.5, RED_DEEP, "#FEE2E2"),
        ],
        # Linha 2: R$ 50
        [
            ("R$ 50", True, 9.5, BG_DARK, "#F1F5F9"),
            ("+R$ 50 (1 nota de 50)", False, 9.5, "#14532D", "#F0FDF4"),
            ("+R$ 100 (1 nota de 100)", False, 9.5, "#581C87", "#FAF5FF"),
            ("-R$ 50", False, 9.5, RED_DEEP, "#FEF2F2"),
        ],
        # Linha 3: R$ 100
        [
            ("R$ 100", True, 9.5, BG_DARK, "#E2E8F0"),
            ("+R$ 100 (1 nota de 100)", False, 9.5, "#14532D", "#DCFCE7"),
            ("+R$ 100 (1 nota de 100)", False, 9.5, "#581C87", "#F3E8FF"),
            ("-R$ 100", False, 9.5, RED_DEEP, "#FEE2E2"),
        ],
        # Linha 4: R$ 150
        [
            ("R$ 150", True, 9.5, BG_DARK, "#F1F5F9"),
            ("+R$ 150 (1x100 + 1x50)", False, 9.5, "#14532D", "#F0FDF4"),
            ("+R$ 100 (1 nota de 100)", False, 9.5, "#581C87", "#FAF5FF"),
            ("-R$ 150", False, 9.5, RED_DEEP, "#FEF2F2"),
        ],
        # Linha 5: R$ 200 (Máx.)
        [
            ("R$ 200 (Máx.)", True, 9.5, BG_DARK, "#E2E8F0"),
            ("+R$ 200 (2 notas de 100)", False, 9.5, "#14532D", "#DCFCE7"),
            ("+R$ 100 (1 nota de 100)", False, 9.5, "#581C87", "#F3E8FF"),
            ("-R$ 200", False, 9.5, RED_DEEP, "#FEE2E2"),
        ],
    ]

    for r_idx, row in enumerate(table_data):
        for c_idx, (ctxt, is_bold, fsz, tcol, bgcol) in enumerate(row):
            ops.append(
                {
                    "op": "set-table-cell",
                    "table": "TAB_REGRAS",
                    "row": r_idx,
                    "col": c_idx,
                    "text": ctxt,
                    "bold": is_bold,
                    "font_size": fsz,
                    "color": tcol,
                    "background_color": bgcol,
                    "font_family": "Roboto",
                }
            )
            ops.append(
                {
                    "op": "style-table-cell",
                    "table": "TAB_REGRAS",
                    "row": r_idx,
                    "col": c_idx,
                    "alignment": "CENTER" if r_idx == 0 else "START",
                }
            )

    ops.append(
        {
            "op": "add-textbox",
            "slide": "SLIDE_4",
            "text": "💡 EFEITO ESTRATÉGICO: Se uma pergunta for fácil e todos os 5 grupos acertarem, quem arriscou R$ 200 ganha apenas +R$ 100 (metade do que ganharia no dobro), enquanto quem apostou R$ 50 ganha os mesmos +R$ 100!",
            "x": 35,
            "y": 335,
            "width": 650,
            "height": 42,
            "font_size": 11,
            "bold": True,
            "color": TEXT_CARD,
            "background_color": "#FEF3C7",
            "font_family": "Roboto",
            "alignment": "center",
            "content_alignment": "MIDDLE",
        }
    )
    ops.append(
        {
            "op": "set-notes",
            "slide": "SLIDE_4",
            "text": "Deixe este slide projetado durante as 5 rodadas para os alunos e o caixa consultarem rapidamente quanto cada aposta paga.",
        }
    )

    # =========================================================================
    # SLIDE 5: DESAFIO DA MESA — TUDO OU NADA FINAL!
    # =========================================================================
    ops.append({"op": "add-slide", "layout": "BLANK", "id": "SLIDE_5"})
    ops.append({"op": "set-background", "slide": "SLIDE_5", "color": BG_DARK})
    ops.append(
        {
            "op": "add-shape",
            "slide": "SLIDE_5",
            "shape_type": "RECTANGLE",
            "x": 0,
            "y": 0,
            "width": 720,
            "height": 6,
            "background_color": "#A855F7",
        }
    )
    ops.append(
        {
            "op": "add-textbox",
            "slide": "SLIDE_5",
            "text": "4. Desafio da Mesa — Tudo ou Nada Final!",
            "x": 35,
            "y": 16,
            "width": 650,
            "height": 36,
            "font_size": 26,
            "bold": True,
            "color": GOLD,
            "font_family": "Montserrat",
            "alignment": "left",
            "content_alignment": "TOP",
        }
    )
    ops.append(
        {
            "op": "add-textbox",
            "slide": "SLIDE_5",
            "text": "O grande clímax após a 5ª pergunta regular: juntar os saldos na mesa — quem acertar leva tudo e o outro zera!",
            "x": 35,
            "y": 50,
            "width": 650,
            "height": 22,
            "font_size": 12,
            "color": PURPLE,
            "font_family": "Roboto",
            "alignment": "left",
            "content_alignment": "TOP",
        }
    )

    # 3 Etapas Estruturadas
    etapas = [
        (
            "1. GATILHO\nEMPATE TÉCNICO (≤ R$ 100)",
            PURPLE_DEEP,
            TEXT_WHITE,
            "Ao fim da 5ª pergunta, toda equipe que estiver empatada na liderança OU a até R$ 100 de distância do 1º colocado (apenas 1 nota de 100 de diferença) entra automaticamente no Desafio da Mesa!",
            35,
        ),
        (
            "2. POTE UNIFICADO\nTODOS OS SALDOS NA MESA",
            GOLD,
            TEXT_DARK,
            "As equipes convocadas são obrigadas a colocar 100% de suas cédulas acumuladas no centro da mesa, formando um Pote Único Gigante!\n(Ex.: R$ 900 + R$ 850 = R$ 1.750 na mesa).",
            257,
        ),
        (
            "3. WINNER TAKES ALL\nQUEM GANHAR LEVA TUDO!",
            GREEN,
            TEXT_DARK,
            "Uma Pergunta Aleatória de Desempate é sorteada. Quem levantar a mão primeiro e acertar leva 100% do Pote da Mesa e os adversários saem ZERADOS! (Se errar, a vez passa ao rival).",
            480,
        ),
    ]
    for hdr_txt, hdr_bg, hdr_col, body_txt, x_pos in etapas:
        ops.append(
            {
                "op": "add-textbox",
                "slide": "SLIDE_5",
                "text": hdr_txt,
                "x": x_pos,
                "y": 82,
                "width": 205,
                "height": 42,
                "font_size": 12,
                "bold": True,
                "color": hdr_col,
                "background_color": hdr_bg,
                "font_family": "Montserrat",
                "alignment": "center",
                "content_alignment": "MIDDLE",
            }
        )
        ops.append(
            {
                "op": "add-textbox",
                "slide": "SLIDE_5",
                "text": body_txt,
                "x": x_pos,
                "y": 124,
                "width": 205,
                "height": 135,
                "font_size": 11,
                "color": BG_LIGHT,
                "background_color": BG_CARD,
                "font_family": "Roboto",
                "alignment": "center",
                "content_alignment": "MIDDLE",
            }
        )

    # Box Inferior Monte Carlo
    ops.append(
        {
            "op": "add-textbox",
            "slide": "SLIDE_5",
            "text": "📊 VALIDAÇÃO POR SIMULAÇÃO DE MONTE CARLO (10.000 PARTIDAS)",
            "x": 35,
            "y": 274,
            "width": 650,
            "height": 26,
            "font_size": 13,
            "bold": True,
            "color": CYAN,
            "background_color": BG_CARD,
            "font_family": "Montserrat",
            "alignment": "center",
            "content_alignment": "MIDDLE",
        }
    )
    ops.append(
        {
            "op": "add-textbox",
            "slide": "SLIDE_5",
            "text": "• Empate Exato Puro ocorre em apenas ~10,7% das partidas (com apostas de R$ 50) ou ~2,6% (com apostas livres de R$ 10).\n• Com a Regra do Empate Técnico (Margem ≤ R$ 100 do Líder), o Desafio da Mesa acontece em ~46,4% das partidas — mantendo a tensão até o último segundo sem tirar o mérito de quem abrir grande vantagem (> R$ 100)!",
            "x": 35,
            "y": 300,
            "width": 650,
            "height": 78,
            "font_size": 11,
            "color": "#E2E8F0",
            "background_color": "#0B1120",
            "font_family": "Roboto",
            "alignment": "left",
            "content_alignment": "TOP",
        }
    )
    ops.append(
        {
            "op": "set-notes",
            "slide": "SLIDE_5",
            "text": "Explique o Desafio da Mesa e como a regra do Empate Técnico (diferença de até R$ 100 para o líder após a 5ª pergunta) garante que quase metade das partidas termine no Tudo ou Nada na mesa, onde quem ganha leva a soma dos saldos e quem perde zera.",
        }
    )

    # =========================================================================
    # SLIDE 6: ROTEIRO RÁPIDO DE APLICAÇÃO EM SALA
    # =========================================================================
    ops.append({"op": "add-slide", "layout": "BLANK", "id": "SLIDE_6"})
    ops.append({"op": "set-background", "slide": "SLIDE_6", "color": BG_LIGHT})
    ops.append(
        {
            "op": "add-shape",
            "slide": "SLIDE_6",
            "shape_type": "RECTANGLE",
            "x": 0,
            "y": 0,
            "width": 720,
            "height": 6,
            "background_color": CYAN,
        }
    )
    ops.append(
        {
            "op": "add-textbox",
            "slide": "SLIDE_6",
            "text": "5. Roteiro Rápido de Aplicação em Sala",
            "x": 35,
            "y": 16,
            "width": 650,
            "height": 36,
            "font_size": 25,
            "bold": True,
            "color": BG_DARK,
            "font_family": "Montserrat",
            "alignment": "left",
            "content_alignment": "TOP",
        }
    )
    ops.append(
        {
            "op": "add-textbox",
            "slide": "SLIDE_6",
            "text": "Fluxo passo a passo para cada uma das 5 rodadas + encerramento:",
            "x": 35,
            "y": 50,
            "width": 650,
            "height": 22,
            "font_size": 12,
            "color": TEXT_SLATE,
            "font_family": "Roboto",
            "alignment": "left",
            "content_alignment": "TOP",
        }
    )

    # 4 Passos Horizontais
    passos = [
        (
            "PASSO 1 — Revelação do Tema, Aposta em Papel & Cédulas (30s)\nO professor anuncia o tema. Cada equipe anota no papel de aposta o valor (mín. R$ 10, máx. R$ 200) e separa as cédulas físicas.",
            80,
            58,
            "#E0F2FE",
            TEXT_DARK,
        ),
        (
            "PASSO 2 — Resolução & Entrega / Revelação do Papel (60s a 90s)\nA questão é projetada. Cada grupo registra por escrito no papel a alternativa escolhida (sem uso de placas) junto ao valor apostado.",
            146,
            58,
            "#FEF3C7",
            TEXT_DARK,
        ),
        (
            "PASSO 3 — Pagamento do Banco da Casa\n• 1 a 4 grupos acertaram? Dobram a aposta (+100% de lucro).\n• Todos os 5 acertaram? Cada equipe ganha +R$ 100 fixo (1 nota de R$ 100).\n• Errou? O Banco recolhe as notas apostadas.",
            212,
            74,
            "#DCFCE7",
            TEXT_DARK,
        ),
        (
            "PASSO 4 — Contagem Após a 5ª Pergunta & Desafio da Mesa\nContam-se os saldos. Há equipes a ≤ R$ 100 do 1º colocado? Todas colocam seus saldos no centro da mesa para a Pergunta Final Aleatória: quem acertar leva tudo e o outro zera!",
            294,
            68,
            "#581C87",
            TEXT_WHITE,
        ),
    ]
    for ptxt, y_pos, p_h, bgcol, tcol in passos:
        ops.append(
            {
                "op": "add-textbox",
                "slide": "SLIDE_6",
                "text": ptxt,
                "x": 35,
                "y": y_pos,
                "width": 650,
                "height": p_h,
                "font_size": 12,
                "bold": True,
                "color": tcol,
                "background_color": bgcol,
                "font_family": "Roboto",
                "alignment": "left",
                "content_alignment": "MIDDLE",
            }
        )

    ops.append(
        {
            "op": "set-notes",
            "slide": "SLIDE_6",
            "text": "Slide final com o passo a passo operacional da dinâmica para os estudantes acompanharem o ritmo da aula.",
        }
    )

    return ops


def verify_batch_rules(ops: list[dict]) -> dict[str, bool]:
    """Valida se o lote de operações do batch cumpre os 6 critérios de R1."""
    texts = []
    for op in ops:
        if "text" in op:
            texts.append(op["text"])

    corpus = " ".join(texts).lower()

    results = {
        "C1_Economia_10k": (
            "10.000" in corpus and "5.000" in corpus and "banco" in corpus
        ),
        "C2_Saldo_Inicial_1000": (
            "1.000" in corpus and "100" in corpus and "50" in corpus and "10" in corpus
        ),
        "C3_Mecanica_Papel_Sem_Placas": ("papel" in corpus and "sem placas" in corpus),
        "C4_Teto_200_Min_10": ("200" in corpus and "10" in corpus),
        "C5_Bonificacao_Dobro_Unanime": (
            "dobro" in corpus and "100" in corpus and "unânime" in corpus
        ),
        "C6_Desafio_Mesa_Empate_Tecnico": (
            "desafio da mesa" in corpus
            and "100" in corpus
            and "winner takes all" in corpus
        ),
    }
    return results


def verify_online_presentation(pres_id: str) -> dict[str, bool]:
    """Audita a apresentação online no Google Slides via gslides CLI."""
    cmd = f"gslides readonly read-all {pres_id}"
    res = subprocess.run(
        cmd, shell=True, capture_output=True, text=True, encoding="utf-8", check=False
    )
    if res.returncode != 0:
        raise RuntimeError(f"Erro ao ler apresentação {pres_id}: {res.stderr}")

    corpus = res.stdout.lower()

    results = {
        "C1_Economia_10k": (
            "10.000" in corpus and "5.000" in corpus and "banco" in corpus
        ),
        "C2_Saldo_Inicial_1000": (
            "1.000" in corpus and "100" in corpus and "50" in corpus and "10" in corpus
        ),
        "C3_Mecanica_Papel_Sem_Placas": ("papel" in corpus and "sem placas" in corpus),
        "C4_Teto_200_Min_10": ("200" in corpus and "10" in corpus),
        "C5_Bonificacao_Dobro_Unanime": (
            "dobro" in corpus and "100" in corpus and "unânime" in corpus
        ),
        "C6_Desafio_Mesa_Empate_Tecnico": (
            "desafio da mesa" in corpus
            and "100" in corpus
            and "winner takes all" in corpus
        ),
    }
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Gera o lote batch de slides das regras oficiais do All-In Químico."
    )
    parser.add_argument(
        "--output", "-o", default=None, help="Caminho do arquivo JSON de saída"
    )
    parser.add_argument(
        "--apply",
        "-a",
        metavar="PRES_ID",
        nargs="?",
        const=DEFAULT_RULES_PRESENTATION_ID,
        help="Aplica o batch gerado diretamente na apresentação do Google Slides via CLI gslides",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Valida os 6 critérios de R1 sobre o batch gerado",
    )
    parser.add_argument(
        "--verify-online",
        metavar="PRES_ID",
        nargs="?",
        const=DEFAULT_RULES_PRESENTATION_ID,
        help="Valida os 6 critérios de R1 diretamente na apresentação do Google Slides",
    )
    args = parser.parse_args()

    # Define caminho de saída padrão se não fornecido
    if args.output:
        out_path = Path(args.output)
    else:
        out_path = Path(__file__).parent / "batch_regras_all_in.json"

    ops = build_rules_batch()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(ops, f, ensure_ascii=False, indent=2)

    print(f"Sucesso: geradas {len(ops)} operações batch em {out_path.resolve()}")

    if args.verify:
        print("=== VERIFICAÇÃO LOCAL DO BATCH (CRITÉRIOS R1) ===")
        res = verify_batch_rules(ops)
        all_ok = True
        for k, v in res.items():
            status = "PASS" if v else "FAIL"
            print(f"[{status}] {k}")
            if not v:
                all_ok = False
        if not all_ok:
            print("Erro: Batch não atende a todos os critérios de R1!")
            sys.exit(1)
        print("Todos os critérios locais de R1 foram verificados com sucesso!")

    if args.verify_online:
        pres_id = args.verify_online
        print(f"=== VERIFICAÇÃO ONLINE GOOGLE SLIDES ({pres_id}) ===")
        res = verify_online_presentation(pres_id)
        all_ok = True
        for k, v in res.items():
            status = "PASS" if v else "FAIL"
            print(f"[{status}] {k}")
            if not v:
                all_ok = False
        if not all_ok:
            print("Erro: Apresentação online não atende a todos os critérios de R1!")
            sys.exit(1)
        print("Todos os critérios online de R1 foram verificados com sucesso!")

    if args.apply:
        pres_id = args.apply
        print(f"Aplicando batch na apresentação {pres_id} via gslides mutate batch...")
        cmd = f'gslides mutate batch {pres_id} -f "{out_path.resolve()}" --json'
        res = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        if res.returncode == 0:
            print("Batch aplicado com sucesso no Google Slides!")
            print(res.stdout)
        else:
            print(f"Erro ao aplicar batch (código {res.returncode}):")
            print(res.stderr)
            sys.exit(res.returncode)


if __name__ == "__main__":
    main()
