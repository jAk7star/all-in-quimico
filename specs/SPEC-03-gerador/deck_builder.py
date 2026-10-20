import re
from pathlib import Path

import jinja2
import yaml

ROOT = Path(__file__).parent
SPEC01_DIR = ROOT.parent / "SPEC-01-questoes"
SPEC02_DIR = ROOT.parent / "SPEC-02-mecanica"
OUT_DIR = ROOT.parent / "SPEC-04-impressao"

DOMAIN_NAMES = {
    "CHEM-SOL": "Soluções",
    "CHEM-STO": "Estequiometria",
    "CHEM-FND": "Fundamentos",
    "CHEM-ATO": "Estrutura Atômica",
    "CHEM-EQU": "Equilíbrio Químico",
    "CHEM-ENV": "Química Ambiental",
    "CHEM-TER": "Termoquímica",
    "CHEM-CIN": "Cinética Química",
}

# Alternativas binárias (A vs B) para questões numéricas e multi-step no Sistema Pari-Mutuel
BINARY_NUMERIC_OPTIONS = {
    "Q-SOL-001": {
        "correct": "A",
        "options": [
            {"key": "A", "text": "5,0 g/L", "rationale": "Correta; C = m / V = 10 g / 2 L = 5,0 g/L."},
            {"key": "B", "text": "20,0 g/L", "rationale": "Multiplicou a massa pelo volume (10 × 2) em vez de dividir."},
        ],
    },
    "Q-STO-001": {
        "correct": "B",
        "options": [
            {"key": "A", "text": "0,50 mol", "rationale": "Inverteu a razão dividindo a massa molar pela massa (58,5 / 117)."},
            {"key": "B", "text": "2,0 mol", "rationale": "Correta; n = m / M = 117 g / 58,5 g/mol = 2,0 mol."},
        ],
    },
    "Q-STO-002": {
        "correct": "A",
        "options": [
            {"key": "A", "text": "0,40 mol", "rationale": "Correta; n = 9,2 g / 23,0 g/mol = 0,40 mol."},
            {"key": "B", "text": "2,50 mol", "rationale": "Dividiu a massa molar pela massa da amostra (23,0 / 9,2)."},
        ],
    },
    "Q-STO-004": {
        "correct": "A",
        "options": [
            {"key": "A", "text": "18,0 g/mol", "rationale": "Correta; M(H2O) = 2 × 1,0 + 16,0 = 18,0 g/mol."},
            {"key": "B", "text": "17,0 g/mol", "rationale": "Somou apenas 1 átomo de hidrogênio, ignorando o índice 2 em H2O."},
        ],
    },
    "Q-STO-005": {
        "correct": "B",
        "options": [
            {"key": "A", "text": "6,0 g", "rationale": "Dividiu a massa molar pelo número de mols (18,0 / 3,0) em vez de multiplicar."},
            {"key": "B", "text": "54,0 g", "rationale": "Correta; m = n × M = 3,0 mol × 18,0 g/mol = 54,0 g."},
        ],
    },
    "Q-SOL-002": {
        "correct": "B",
        "options": [
            {"key": "A", "text": "0,008 g/L", "rationale": "Dividiu 4,0 g diretamente por 500 mL sem converter o volume para litros (0,500 L)."},
            {"key": "B", "text": "8,0 g/L", "rationale": "Correta; 500 mL = 0,500 L e C = 4,0 g / 0,500 L = 8,0 g/L."},
        ],
    },
    "Q-SOL-003": {
        "correct": "A",
        "options": [
            {"key": "A", "text": "2,0 mol/L", "rationale": "Correta; 250 mL = 0,250 L e c = 0,50 mol / 0,250 L = 2,0 mol/L."},
            {"key": "B", "text": "0,125 mol/L", "rationale": "Multiplicou a quantidade de matéria pelo volume (0,50 × 0,250) em vez de dividir."},
        ],
    },
    "Q-SOL-004": {
        "correct": "A",
        "options": [
            {"key": "A", "text": "0,50 mol/L", "rationale": "Correta; pela conservação do soluto (c1·V1 = c2·V2), c2 = (2,0 × 100) / 400 = 0,50 mol/L."},
            {"key": "B", "text": "8,0 mol/L", "rationale": "Multiplicou a concentração inicial por 4 em vez de dividir pelo aumento de volume."},
        ],
    },
    "Q-SOL-005": {
        "correct": "A",
        "options": [
            {"key": "A", "text": "200 mL", "rationale": "Correta; V2 = (c1 · V1) / c2 = (1,0 × 50) / 0,25 = 200 mL."},
            {"key": "B", "text": "12,5 mL", "rationale": "Multiplicou o volume inicial por 0,25 em vez de dividir pela concentração final."},
        ],
    },
    "Q-SOL-007": {
        "correct": "A",
        "options": [
            {"key": "A", "text": "M = 58,5 g/mol • n = 0,20 mol • c = 0,40 mol/L", "rationale": "Correta; converteu 500 mL para 0,500 L para achar c = 0,20 / 0,500 = 0,40 mol/L."},
            {"key": "B", "text": "M = 58,5 g/mol • n = 0,20 mol • c = 0,20 mol/L", "rationale": "Esqueceu de dividir a quantidade de matéria pelo volume de 0,500 L na última etapa."},
        ],
    },
    "Q-SOL-008": {
        "correct": "B",
        "options": [
            {"key": "A", "text": "M = 40,0 g/mol • n = 0,20 mol • c = 0,05 mol/L", "rationale": "Multiplicou 0,20 mol por 0,250 L em vez de dividir pelo volume em litros."},
            {"key": "B", "text": "M = 40,0 g/mol • n = 0,20 mol • c = 0,80 mol/L", "rationale": "Correta; M = 40,0 g/mol, n = 8,0 / 40,0 = 0,20 mol e c = 0,20 / 0,250 L = 0,80 mol/L."},
        ],
    },
}


def load_yaml(path: Path):
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_all_questions():
    q_dir = SPEC01_DIR / "questions"
    questions = []
    if q_dir.exists():
        for f in sorted(q_dir.rglob("*.yaml")):
            data = load_yaml(f)
            if data and "questions" in data:
                questions.extend(data["questions"])

    # Ordena por dificuldade/nível e depois por ID
    questions.sort(key=lambda q: (q.get("difficulty", 1), q.get("id", "")))
    return questions


def format_chemical_text(text: str) -> str:
    """Aprimora a tipografia de fórmulas químicas, setas e subscritos."""
    if not text:
        return ""

    s = str(text)

    # Substitui setas simples de reação química por setas elegantes
    s = s.replace("->", "→").replace("<->", "⇄")

    # Formata fórmulas químicas comuns se ainda não contiverem tags <sub>
    if "<sub>" not in s:
        replacements = [
            (r"\bH2O\b", "H<sub>2</sub>O"),
            (r"\bH2\b", "H<sub>2</sub>"),
            (r"\bO2\b", "O<sub>2</sub>"),
            (r"\bN2\b", "N<sub>2</sub>"),
            (r"\bCO2\b", "CO<sub>2</sub>"),
            (r"\bCO\b", "CO"),
            (r"\bCH4\b", "CH<sub>4</sub>"),
            (r"\bC6H12O6\b", "C<sub>6</sub>H<sub>12</sub>O<sub>6</sub>"),
            (r"\bC2H6O\b", "C<sub>2</sub>H<sub>6</sub>O"),
            (r"\bC2H5OH\b", "C<sub>2</sub>H<sub>5</sub>OH"),
            (r"\bCaCO3\b", "CaCO<sub>3</sub>"),
            (r"\bCaO\b", "CaO"),
            (r"\bH2SO4\b", "H<sub>2</sub>SO<sub>4</sub>"),
            (r"\bHCl\b", "HCl"),
            (r"\bNaOH\b", "NaOH"),
            (r"\bNaCl\b", "NaCl"),
            (r"\bNH3\b", "NH<sub>3</sub>"),
            (r"\bNO2\b", "NO<sub>2</sub>"),
            (r"\bSO2\b", "SO<sub>2</sub>"),
            (r"\bSO3\b", "SO<sub>3</sub>"),
            (r"\bFe2O3\b", "Fe<sub>2</sub>O<sub>3</sub>"),
            (r"\bAl2O3\b", "Al<sub>2</sub>O<sub>3</sub>"),
        ]
        for pattern, repl in replacements:
            s = re.sub(pattern, repl, s)

    return s


def build_binary_ab_options(q: dict) -> tuple[str, list[dict], list[dict]]:
    """
    Garante que toda questão apresente exatamente duas respostas possíveis (A e B)
    para o Sistema de Apostas Pari-Mutuel.
    Retorna (correct_key, formatted_options, distractors).
    """
    qid = q.get("id", "")
    if q["type"] == "multiple_choice":
        raw_options = q.get("options", [])
        correct_opt = next((o for o in raw_options if o["key"] == q["correct"]), raw_options[0])
        wrong_options = [o for o in raw_options if o["key"] != q["correct"]]
        # Prioriza o distrator com mistake_ref documentado na base científica
        primary_wrong = next((o for o in wrong_options if o.get("mistake_ref")), wrong_options[0])

        if q["correct"] == "A":
            pair = [
                {"key": "A", "text": correct_opt["text"], "rationale": correct_opt.get("rationale", "")},
                {"key": "B", "text": primary_wrong["text"], "rationale": primary_wrong.get("rationale", "")},
            ]
            correct_key = "A"
        else:
            pair = [
                {"key": "A", "text": primary_wrong["text"], "rationale": primary_wrong.get("rationale", "")},
                {"key": "B", "text": correct_opt["text"], "rationale": correct_opt.get("rationale", "")},
            ]
            correct_key = "B"
    elif qid in BINARY_NUMERIC_OPTIONS:
        spec = BINARY_NUMERIC_OPTIONS[qid]
        correct_key = spec["correct"]
        pair = spec["options"]
    else:
        # Fallback automático para qualquer questão numérica futura
        exp = q.get("calc", {}).get("expected", {})
        val_num = float(exp.get("value", 1.0))
        unit = exp.get("unit", "")
        val_str = str(exp.get("value", "")).replace(".", ",")
        wrong_str = str(round(val_num * 2, 2)).replace(".", ",")
        correct_key = "A"
        pair = [
            {"key": "A", "text": f"{val_str} {unit}".strip(), "rationale": "Correta pelo cálculo estequiométrico."},
            {"key": "B", "text": f"{wrong_str} {unit}".strip(), "rationale": "Erro de fator 2 na operação matemática."},
        ]

    formatted_options = []
    distractors = []
    for o in pair:
        formatted_options.append({
            "key": o["key"],
            "text": o["text"],
            "text_html": format_chemical_text(o["text"]),
        })
        if o["key"] != correct_key and o.get("rationale"):
            distractors.append({
                "key": o["key"],
                "rationale": format_chemical_text(o["rationale"]),
            })

    return correct_key, formatted_options, distractors


def format_given_data(given_dict: dict) -> list:
    """Formata os dados fornecidos com notação físico-química padrão."""
    result = []
    for k, v in given_dict.items():
        label = v.get("description")
        if not label:
            key_clean = (
                k.replace("massa_", "m(")
                .replace("volume_", "V(")
                .replace("quantidade_", "n(")
                .replace("massa_molar_", "M(")
                .replace("c_", "c(")
                .replace("v_", "V(")
            )
            if "(" in key_clean:
                parts = key_clean.split("(")
                symbol = parts[0]
                sub = parts[1].upper() if symbol in ["m", "n", "M", "V", "c"] else parts[1]
                sub_map = {
                    "SOLUTO": "soluto",
                    "SOLUCAO": "solução",
                    "INICIAL": "inicial",
                    "FINAL": "final",
                    "AMOSTRA": "amostra",
                    "NACL": "NaCl",
                    "NAOH": "NaOH",
                    "NA": "Na",
                    "CL": "Cl",
                    "H2O": "H<sub>2</sub>O",
                }
                sub = sub_map.get(sub, sub)
                label = f"<em>{symbol}</em>({sub})"
            else:
                label = k.replace("_", " ")

        val_str = str(v["value"]).replace(".", ",")
        unit_str = v.get("unit", "")
        unit_formatted = unit_str.replace("mol/L", "mol/L").replace("g/L", "g/L")
        result.append({"label": label, "value": val_str, "unit": unit_formatted})
    return result


def paginate_cards(cards: list, page_size: int = 9) -> list:
    """Divide a lista de cartas em páginas A4 com exatamente page_size cartas."""
    pages = []
    for i in range(0, len(cards), page_size):
        chunk = cards[i : i + page_size]
        pages.append({
            "page_num": (i // page_size) + 1,
            "cards": chunk,
            "first_num": chunk[0]["number"],
            "last_num": chunk[-1]["number"],
        })
    return pages


def mirror_grid_for_back(cards_chunk: list, grid_cols: int = 3, grid_rows: int = 3) -> list:
    """
    Espelha horizontalmente as colunas de um grid 3x3 para impressão duplex.
    Quando a folha é virada pela borda longa:
    A coluna 0 da frente vira a coluna 2 do verso;
    A coluna 1 da frente permanece na coluna 1 do verso;
    A coluna 2 da frente vira a coluna 0 do verso.
    """
    mirrored = []
    for r in range(grid_rows):
        row_items = []
        for c in range(grid_cols):
            idx = r * grid_cols + c
            if idx < len(cards_chunk):
                row_items.append(cards_chunk[idx])
            else:
                row_items.append(None)

        # Inverte as colunas desta linha
        row_reversed = list(reversed(row_items))
        mirrored.extend(row_reversed)

    clean_mirrored = []
    for item in mirrored:
        if item is not None:
            clean_mirrored.append(item)
        else:
            clean_mirrored.append({
                "css_class": "card-placeholder",
                "level": 1,
                "is_empty": True,
                "number": "---",
                "id": "",
                "is_question": False,
            })
    return clean_mirrored


def build_duplex_sheets(front_pages: list, back_cards_all: list) -> list:
    """Gera a estrutura de folhas duplex intercaladas (Frente Pág N, Verso Pág N espelhado)."""
    duplex_sheets = []
    for p_idx, f_page in enumerate(front_pages):
        f_cards = f_page["cards"]
        start_idx = p_idx * 9
        end_idx = start_idx + len(f_cards)
        b_chunk = back_cards_all[start_idx:end_idx]

        b_mirrored = mirror_grid_for_back(b_chunk, grid_cols=3, grid_rows=3)

        duplex_sheets.append({
            "sheet_num": p_idx + 1,
            "front_cards": f_cards,
            "back_cards_mirrored": b_mirrored,
            "first_num": f_cards[0]["number"],
            "last_num": f_cards[-1]["number"],
        })
    return duplex_sheets


def main():
    OUT_DIR.mkdir(exist_ok=True)
    questions = load_all_questions()
    rules = load_yaml(SPEC02_DIR / "rules" / "base_rules.yaml") or {}
    pari_mutuel = rules.get("pari_mutuel", {})
    house_cut_pct = int(round(float(pari_mutuel.get("house_cut", 0.10)) * 100))

    q_cards = []
    a_cards = []
    cheat_sheet_items = []

    for i, q in enumerate(questions, start=1):
        num_str = f"{i:03d}"
        lvl = q.get("difficulty", 1)
        domain_code = q.get("domain", "CHEM-FND")
        domain_clean = DOMAIN_NAMES.get(domain_code, domain_code)

        # Opções binárias A e B para o Sistema Pari-Mutuel
        correct_key, formatted_options, distractors = build_binary_ab_options(q)
        winning_opt = next((o for o in formatted_options if o["key"] == correct_key), formatted_options[0])
        correct_display = f"{correct_key}) {winning_opt['text_html']}"

        common_data = {
            "id": q["id"],
            "number": num_str,
            "level": lvl,
            "domain": domain_code,
            "domain_clean": domain_clean,
            "is_empty": False,
            "house_cut_pct": house_cut_pct,
        }

        given_formatted = format_given_data(q.get("given_data", {}))

        # Resumo para a folha do mestre (Cheat Sheet)
        quick_sol = q.get("worked_solution", "")
        if len(quick_sol) > 110:
            quick_sol = quick_sol[:107] + "..."
        cheat_sheet_items.append({
            "number": num_str,
            "level": lvl,
            "domain_clean": domain_clean,
            "correct_key": correct_key,
            "correct_answer_html": correct_display,
            "quick_summary": format_chemical_text(quick_sol or q.get("scientific_justification", "")),
        })

        # Carta de Pergunta
        q_cards.append({
            **common_data,
            "type_label": "Pergunta",
            "css_class": "question",
            "is_question": True,
            "statement": q["statement"],
            "statement_html": format_chemical_text(q["statement"]),
            "skill": q.get("skill", ""),
            "options": formatted_options,
            "given_data": given_formatted,
        })

        # Carta de Resposta
        a_cards.append({
            **common_data,
            "type_label": "Resposta",
            "css_class": "answer",
            "is_question": False,
            "correct_key": correct_key,
            "correct_answer_html": correct_display,
            "worked_solution": q.get("worked_solution", ""),
            "worked_solution_html": format_chemical_text(q.get("worked_solution", "")),
            "scientific_justification": q.get("scientific_justification", ""),
            "scientific_justification_html": format_chemical_text(q.get("scientific_justification", "")),
            "distractors": distractors,
        })

    # Jinja2 Environment
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(ROOT / "templates"))
    deck_template = env.get_template("deck_template.html")
    back_template = env.get_template("card_back_template.html")
    duplex_template = env.get_template("duplex_template.html")
    money_template = env.get_template("money_template.html")
    cheat_sheet_template = env.get_template("cheat_sheet_template.html")
    score_tracker_template = env.get_template("score_tracker_template.html")
    table_rules_template = env.get_template("table_rules_template.html")

    # Paginação 3x3 (9 cartas por página)
    q_pages = paginate_cards(q_cards, page_size=9)
    a_pages = paginate_cards(a_cards, page_size=9)

    total_lots = len(q_cards)

    # 1. Arquivo Duplex Intercalado Unificado (Frente + Verso Espelhado)
    q_duplex_sheets = build_duplex_sheets(q_pages, q_cards)
    duplex_html = duplex_template.render(duplex_sheets=q_duplex_sheets, house_cut_pct=house_cut_pct)
    (OUT_DIR / "duplex_intercalado_para_imprimir.html").write_text(duplex_html, encoding="utf-8")

    # 2. Arquivos de Frentes e Versos Separados
    q_html = deck_template.render(
        deck_title=f"Perguntas Pari-Mutuel (A ou B) - Lotes 001 a {total_lots:03d}",
        pages=q_pages,
        house_cut_pct=house_cut_pct,
    )
    a_html = deck_template.render(
        deck_title=f"Respostas / Gabarito (A ou B) - Lotes 001 a {total_lots:03d}",
        pages=a_pages,
        house_cut_pct=house_cut_pct,
    )
    q_back_html = back_template.render(deck_title="Verso das Cartas de Pergunta", pages=q_pages)
    a_back_html = back_template.render(deck_title="Verso das Cartas de Resposta", pages=a_pages)

    (OUT_DIR / "perguntas_para_imprimir.html").write_text(q_html, encoding="utf-8")
    (OUT_DIR / "respostas_para_imprimir.html").write_text(a_html, encoding="utf-8")
    (OUT_DIR / "verso_perguntas_para_imprimir.html").write_text(q_back_html, encoding="utf-8")
    (OUT_DIR / "verso_respostas_para_imprimir.html").write_text(a_back_html, encoding="utf-8")

    # 3. Arquivos Separados por Nível de Dificuldade
    for lvl, title in [
        (1, "Nível 1 - Aquecimento"),
        (2, "Nível 2 - Desenvolvimento"),
        (3, "Nível 3 - Desafio Morte Súbita"),
    ]:
        q_lvl = [c for c in q_cards if c["level"] == lvl]
        a_lvl = [c for c in a_cards if c["level"] == lvl]
        if q_lvl:
            q_lvl_pages = paginate_cards(q_lvl, page_size=9)
            a_lvl_pages = paginate_cards(a_lvl, page_size=9)

            (OUT_DIR / f"perguntas_nivel_{lvl}.html").write_text(
                deck_template.render(
                    deck_title=f"Perguntas - {title}", pages=q_lvl_pages, house_cut_pct=house_cut_pct
                ),
                encoding="utf-8",
            )
            (OUT_DIR / f"respostas_nivel_{lvl}.html").write_text(
                deck_template.render(
                    deck_title=f"Respostas - {title}", pages=a_lvl_pages, house_cut_pct=house_cut_pct
                ),
                encoding="utf-8",
            )
            (OUT_DIR / f"verso_perguntas_nivel_{lvl}.html").write_text(
                back_template.render(deck_title=f"Verso Perguntas - {title}", pages=q_lvl_pages),
                encoding="utf-8",
            )
            (OUT_DIR / f"verso_respostas_nivel_{lvl}.html").write_text(
                back_template.render(deck_title=f"Verso Respostas - {title}", pages=a_lvl_pages),
                encoding="utf-8",
            )

    # 4. Cédulas de Tokens (12 notas por folha A4 em grid 2x6)
    currency = rules.get("currency_name", "Tokens")
    all_notes = [{"value": 50}] * 48 + [{"value": 100}] * 48 + [{"value": 500}] * 24
    money_pages = []
    for i in range(0, len(all_notes), 12):
        chunk = all_notes[i : i + 12]
        money_pages.append({"page_num": (i // 12) + 1, "notes": chunk})

    m_html = money_template.render(currency=currency, money_pages=money_pages)
    (OUT_DIR / "dinheiro_para_imprimir.html").write_text(m_html, encoding="utf-8")

    # 5. Guia Rápido do Mestre (Cheat Sheet em folha única A4)
    cs_html = cheat_sheet_template.render(
        items=cheat_sheet_items,
        rules=rules,
        house_cut_pct=house_cut_pct,
    )
    (OUT_DIR / "guia_do_mestre_cheat_sheet.html").write_text(cs_html, encoding="utf-8")

    # 6. Ficha de Registro de Apostas Pari-Mutuel, Pool e Odds (Score Tracker)
    st_html = score_tracker_template.render(
        rules=rules,
        house_cut_pct=house_cut_pct,
    )
    (OUT_DIR / "ficha_controle_leilao.html").write_text(st_html, encoding="utf-8")

    # 7. Cartões de Regras Rápidas de Mesa para os Alunos (Pari-Mutuel Tokenizado)
    tr_html = table_rules_template.render(
        rules=rules,
        house_cut_pct=house_cut_pct,
    )
    (OUT_DIR / "cartoes_regras_mesa.html").write_text(tr_html, encoding="utf-8")

    print(f"Sucesso! Gerados todos os materiais pari-mutuel em {OUT_DIR.resolve()}:")
    print(f" - {len(q_cards)} pares de cartas (A vs B) em páginas A4 com marcas de corte")
    print(" - Arquivo duplex intercalado com espelhamento milimétrico de colunas")
    print(f" - {len(all_notes)} cédulas de {currency} com 4 numerais nos cantos")
    print(" - Guia Rápido do Mestre (Cheat Sheet Pari-Mutuel)")
    print(" - Ficha de Controle de Pool (T_A, T_B, P) e Odds (O_A, O_B)")
    print(" - Cartões de Regras Rápidas de Mesa (Sistema Pari-Mutuel Tokenizado)")


if __name__ == "__main__":
    main()
