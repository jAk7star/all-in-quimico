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

    questions.sort(key=lambda q: (q.get("difficulty", 1), q.get("id", "")))
    return questions


def format_chemical_text(text: str) -> str:
    """Aprimora a tipografia de fórmulas químicas, setas e subscritos."""
    if not text:
        return ""

    s = str(text)
    s = s.replace("->", "→").replace("<->", "⇄")

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
    """Garante que toda questão apresente exatamente duas respostas possíveis (A e B)."""
    qid = q.get("id", "")
    if q["type"] == "multiple_choice":
        raw_options = q.get("options", [])
        correct_opt = next((o for o in raw_options if o["key"] == q["correct"]), raw_options[0])
        wrong_options = [o for o in raw_options if o["key"] != q["correct"]]
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


def mirror_grid_for_back(cards_chunk: list, grid_cols: int = 3, grid_rows: int = 3) -> list:
    """Espelha horizontalmente as colunas de um grid 3x3 para impressão duplex."""
    mirrored = []
    for r in range(grid_rows):
        row_items = []
        for c in range(grid_cols):
            idx = r * grid_cols + c
            if idx < len(cards_chunk):
                row_items.append(cards_chunk[idx])
            else:
                row_items.append(None)

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


def build_training_round_context(breakage_unit: int = 50) -> dict:
    """Mantido para retrocompatibilidade de testes unitários."""
    raw_teams = [
        {"name": "Alfa", "choice": "A", "bet": 200},
        {"name": "Beta", "choice": "B", "bet": 100},
        {"name": "Gama", "choice": "B", "bet": 150},
    ]
    correct_option = "B"
    total_pool = sum(t["bet"] for t in raw_teams)
    winner_pool = sum(t["bet"] for t in raw_teams if t["choice"] == correct_option)
    odd = total_pool / winner_pool
    odd_str = f"{odd:.1f}".replace(".", ",")

    teams_out = []
    total_paid = 0
    for t in raw_teams:
        won = t["choice"] == correct_option
        if won:
            raw_val = t["bet"] * odd
            payout = int(raw_val // breakage_unit) * breakage_unit
            total_paid += payout
            profit = payout - t["bet"]
            raw_str = f"{int(round(raw_val))} T$"
            net_str = f"+{profit} T$ (lucro)"
        else:
            payout = 0
            raw_str = "0 T$ (errou)"
            net_str = f"−{t['bet']} T$ (perdeu)"
        teams_out.append({
            **t,
            "won": won,
            "raw_str": raw_str,
            "payout": payout,
            "net_str": net_str,
        })

    breakage = total_pool - total_paid
    return {
        "correct_option": correct_option,
        "total_pool": total_pool,
        "winner_pool": winner_pool,
        "odd": odd,
        "odd_str": odd_str,
        "total_paid": total_paid,
        "breakage": breakage,
        "teams": teams_out,
    }


def build_10_kits_money_pages() -> tuple[list[dict], dict]:
    """
    Gera exatamente os 10 Kits de R$ 1.000 (Economia Total = R$ 10.000):
      - 5 Kits para as 5 Equipes (R$ 5.000)
      - 5 Kits para o Banco da Casa / Reserva do Professor (R$ 5.000)
    Composição de cada Kit de R$ 1.000:
      - 6 notas de R$ 100 (R$ 600)
      - 6 notas de R$ 50  (R$ 300)
      - 10 notas de R$ 10 (R$ 100)
    Total geral de 10 Kits:
      - 60 notas de R$ 100 = R$ 6.000
      - 60 notas de R$ 50  = R$ 3.000
      - 100 notas de R$ 10 = R$ 1.000
      - Total: 220 cédulas = R$ 10.000,00
    """
    notes_100 = []
    for i in range(1, 61):
        kit_num = ((i - 1) // 6) + 1
        kit_role = f"KIT {kit_num:02d} • EQUIPE {kit_num:02d}" if kit_num <= 5 else f"KIT {kit_num:02d} • BANCO DA CASA"
        notes_100.append({"value": 100, "serial": i, "kit_num": kit_num, "kit_label": kit_role})

    notes_50 = []
    for i in range(1, 61):
        kit_num = ((i - 1) // 6) + 1
        kit_role = f"KIT {kit_num:02d} • EQUIPE {kit_num:02d}" if kit_num <= 5 else f"KIT {kit_num:02d} • BANCO DA CASA"
        notes_50.append({"value": 50, "serial": i, "kit_num": kit_num, "kit_label": kit_role})

    notes_10 = []
    for i in range(1, 101):
        kit_num = ((i - 1) // 10) + 1
        kit_role = f"KIT {kit_num:02d} • EQUIPE {kit_num:02d}" if kit_num <= 5 else f"KIT {kit_num:02d} • BANCO DA CASA"
        notes_10.append({"value": 10, "serial": i, "kit_num": kit_num, "kit_label": kit_role})

    all_notes = notes_100 + notes_50 + notes_10
    money_pages = []
    for i in range(0, len(all_notes), 12):
        chunk = all_notes[i : i + 12]
        vals = sorted({n["value"] for n in chunk}, reverse=True)
        val_str = ", ".join(f"R$ {v}" for v in vals)
        page_sum = sum(n["value"] for n in chunk)
        money_pages.append({
            "page_num": (i // 12) + 1,
            "notes": chunk,
            "denomination_summary": f"{len(chunk)} Cédulas de {val_str} • Subtotal da Folha: R$ {page_sum:,}".replace(",", "."),
        })

    stats = {
        "kits_count": 10,
        "count_100": len(notes_100),
        "count_50": len(notes_50),
        "count_10": len(notes_10),
        "total_notes": len(all_notes),
        "total_value": sum(n["value"] for n in all_notes),
    }
    return money_pages, stats


def build_group_bet_cards() -> tuple[list[dict], list[dict]]:
    """
    Gera os exemplares de Ficha de Controle das Apostas dos Grupos no formato
    de card 63mm x 88mm (grade 3x3 = 9 cards por folha A4):
      - Folha 1: 9 Fichas Consolidadas de Controle de Apostas da Equipe (5 Rodadas + Desafio da Mesa)
      - Folha 2: 9 Bilhetes Individuais de Aposta Secreta por Rodada
    """
    team_tracker_cards = [
        {"badge": "EQUIPE 01", "team_num": 1},
        {"badge": "EQUIPE 02", "team_num": 2},
        {"badge": "EQUIPE 03", "team_num": 3},
        {"badge": "EQUIPE 04", "team_num": 4},
        {"badge": "EQUIPE 05", "team_num": 5},
        {"badge": "EQUIPE 01 (2ª)", "team_num": 1},
        {"badge": "EQUIPE 02 (2ª)", "team_num": 2},
        {"badge": "EQUIPE 03 (2ª)", "team_num": 3},
        {"badge": "EQUIPE ___", "team_num": 0},
    ]
    round_slip_cards = [{"slip_num": i} for i in range(1, 10)]
    return team_tracker_cards, round_slip_cards


def main():
    OUT_DIR.mkdir(exist_ok=True)
    ver_tag = "v001"

    # Remove arquivos .html antigos para manter apenas os 2 arquivos solicitados
    for old_html in OUT_DIR.glob("*.html"):
        old_html.unlink()

    env = jinja2.Environment(loader=jinja2.FileSystemLoader(ROOT / "templates"))
    bet_cards_template = env.get_template("group_bet_cards_template.html")
    money_template = env.get_template("money_template.html")

    # 1. Exemplares de Ficha de Controle das Apostas dos Grupos (Cards 63mm x 88mm)
    team_tracker_cards, round_slip_cards = build_group_bet_cards()
    bet_cards_html = bet_cards_template.render(
        team_tracker_cards=team_tracker_cards,
        round_slip_cards=round_slip_cards,
    )
    f_bet_cards = OUT_DIR / f"001_fichas_controle_apostas_grupos_{ver_tag}.html"
    f_bet_cards.write_text(bet_cards_html, encoding="utf-8")

    # 2. Arquivo de Cédulas de Dinheiro (10 Kits de R$ 1.000 = R$ 10.000)
    money_pages, stats = build_10_kits_money_pages()
    money_html = money_template.render(
        money_pages=money_pages,
        stats=stats,
    )
    f_money = OUT_DIR / f"002_cedulas_dinheiro_10_kits_{ver_tag}.html"
    f_money.write_text(money_html, encoding="utf-8")

    print(f"Sucesso! Materiais gerados em {OUT_DIR.resolve()}:")
    print(f" - {f_bet_cards.name}: Exemplares de Ficha de Controle das Apostas dos Grupos (Cards 63x88mm)")
    print(
        f" - {f_money.name}: {stats['kits_count']} Kits de R$ 1.000 = R$ {stats['total_value']:,} "
        f"({stats['count_100']}x R$ 100 + {stats['count_50']}x R$ 50 + {stats['count_10']}x R$ 10 = {stats['total_notes']} cédulas)"
    )


if __name__ == "__main__":
    main()
