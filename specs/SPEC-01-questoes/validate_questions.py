"""Validação de questões (SPEC-01 v0.1.0) contra a Knowledge Base (SPEC-00).

Camadas: estrutural (Pydantic) -> referencial -> dados completos e unidades ->
recálculo do gabarito. Separa ERROS de PENDÊNCIAS de revisão humana.
Uso: python validate_questions.py [diretório_questions]
"""

from __future__ import annotations

import sys
from pathlib import Path

import sympy
import yaml
from sympy.parsing.sympy_parser import parse_expr

ROOT = Path(__file__).parent
SPEC00 = ROOT.parent / "SPEC-00-fundamentos"
sys.path.insert(0, str(SPEC00))

import validate_knowledge as vk

from question_models import validate_question

QUESTIONS_DIR = ROOT / "questions"
Report = vk.Report
CONSUMABLE = "approved"


# ---------------------------------------------------------------- Knowledge Base
def load_kb() -> tuple[dict[str, dict], dict]:
    records = vk.load_records(vk.KNOWLEDGE_DIR) + vk.load_records(SPEC00 / "examples")
    return {r["id"]: r for r in records}, vk.load_taxonomy()


def load_questions(directory: Path = QUESTIONS_DIR) -> list[dict]:
    out: list[dict] = []
    for path in sorted(directory.rglob("*.yaml")):
        out.extend((yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("questions") or [])
    return out



# ---------------------------------------------------------------------- Unidades
class UnitError(ValueError):
    pass


class Units:
    """Fatores e dimensões vindos dos registros `unit` e `quantity` da base."""

    def __init__(self, kb: dict[str, dict]):
        self.table: dict[str, tuple[float, str]] = {}
        for r in kb.values():
            if r["type"] == "unit":
                q = kb.get(r["quantity_ref"])
                self.table[r["symbol"]] = (float(r["factor"]), q["quantity_key"] if q else r["quantity_ref"])

    def parse(self, unit: str) -> tuple[float, dict[str, int]]:
        parts = unit.split("/")
        if len(parts) > 2 or any(p not in self.table for p in parts):
            raise UnitError(f"unidade não reconhecida: '{unit}'")
        f0, d0 = self.table[parts[0]]
        dims = {d0: 1}
        factor = f0
        if len(parts) == 2:
            f1, d1 = self.table[parts[1]]
            factor /= f1
            dims[d1] = dims.get(d1, 0) - 1
        return factor, {k: v for k, v in dims.items() if v}

    def convert(self, value: float, src: str, dst: str) -> float:
        fs, ds = self.parse(src)
        fd, dd = self.parse(dst)
        if ds != dd:
            raise UnitError(f"unidades incompatíveis: '{src}' -> '{dst}'")
        return value * fs / fd


# ------------------------------------------------------------------------ Cálculo
def _solve_formula(formula: dict, target: str, known: dict[str, float]) -> float:
    names = list(formula["variables"])
    symbols = {n: sympy.Symbol(n) for n in names}
    lhs, rhs = formula["expression"].split("=")
    eq = parse_expr(lhs, local_dict=symbols) - parse_expr(rhs, local_dict=symbols)
    eq = eq.subs({symbols[k]: v for k, v in known.items()})
    sols = sympy.solve(eq, symbols[target])
    if len(sols) != 1:
        raise ValueError(f"equação sem solução única para {target}")
    return float(sols[0])


def _check_step(q: dict, step: dict, ctx: dict[str, tuple[float, str]], kb, units: Units, rep: Report) -> None:
    qid, sid = q["id"], step["id"]
    exp = step["expected"]
    try:
        if step["kind"] == "molar_mass":
            total = 0.0
            for eid, count in step["composition"].items():
                el = kb.get(eid)
                if not el or el["type"] != "element":
                    rep.error("MISSING_REF", qid, f"etapa {sid}: elemento inexistente {eid}")
                    return
                given = next((g for g in q.get("given_data", {}).values() if g.get("element_ref") == eid), None)
                if given is None:
                    rep.error("MISSING_DATA", qid, f"etapa {sid}: massa atômica de {el['symbol']} não fornecida (§9.2)")
                    return
                total += count * units.convert(given["value"], given["unit"], "g/mol")
            computed, cunit = total, "g/mol"
        else:
            formula = kb.get(step["formula_ref"])
            if not formula or formula["type"] != "formula":
                rep.error("MISSING_REF", qid, f"etapa {sid}: fórmula inexistente {step['formula_ref']}")
                return
            if step["formula_ref"] not in q.get("formula_refs", []):
                rep.error("FORMULA_UNDECLARED", qid, f"etapa {sid}: {step['formula_ref']} ausente de formula_refs")
            variables = formula["variables"]
            target = step["target"]
            if target not in variables:
                rep.error("BAD_VARIABLE", qid, f"etapa {sid}: variável '{target}' não existe na fórmula")
                return
            missing = [v for v in variables if v != target and v not in step["inputs"]]
            if missing:
                rep.error("MISSING_DATA", qid, f"etapa {sid}: dados não fornecidos para {missing} (§9.1)")
                return
            known = {}
            for var, name in step["inputs"].items():
                if var not in variables or var == target:
                    rep.error("BAD_VARIABLE", qid, f"etapa {sid}: entrada '{var}' inválida")
                    return
                if name not in ctx:
                    rep.error("UNDEFINED_DATA", qid, f"etapa {sid}: '{name}' não é dado nem etapa anterior")
                    return
                value, unit = ctx[name]
                known[var] = units.convert(value, unit, variables[var]["unit"])
            computed, cunit = _solve_formula(formula, target, known), variables[target]["unit"]
        answer = units.convert(computed, cunit, exp["unit"])
    except UnitError as e:
        rep.error("UNIT_MISMATCH", qid, f"etapa {sid}: {e}")
        return
    except ValueError as e:
        rep.error("CALC", qid, f"etapa {sid}: {e}")
        return

    ctx[sid] = (computed, cunit)
    rel = abs(answer - exp["value"]) / abs(answer) if answer else abs(exp["value"])
    if rel > exp["tolerance"]:
        rep.error("ANSWER_MISMATCH", qid, f"etapa {sid}: gabarito {exp['value']} {exp['unit']}, recalculado {answer:.6g}")
    elif rel > 1e-9 and not exp.get("rounding"):
        rep.pend("ROUNDING_UNDECLARED", qid, f"etapa {sid}: resposta arredondada sem regra declarada (§9.4)")


# --------------------------------------------------------------------- Validação
def validate_questions(questions: list[dict], kb: dict[str, dict], taxonomy: dict) -> Report:
    rep = Report()
    units = Units(kb)
    domains = {d["id"] for d in taxonomy["domains"]}
    valid = []
    for q in questions:
        qid = q.get("id") if isinstance(q, dict) else None
        errs = validate_question(q)
        for m in errs:
            rep.error("SCHEMA", qid, m)
        if not errs:
            valid.append(q)

    seen: set[str] = set()
    for q in valid:
        qid = q["id"]
        if qid in seen:
            rep.error("DUPLICATE_ID", qid, "identificador duplicado")
        seen.add(qid)
        if q["domain"] not in domains:
            rep.error("UNKNOWN_DOMAIN", qid, f"domínio inexistente: {q['domain']}")
        if qid[2:5] != q["domain"][5:8]:
            rep.error("ID_DOMAIN_MISMATCH", qid, f"ID não corresponde ao domínio {q['domain']}")

        for field, kinds in (("concept_refs", ("concept", "skill")), ("formula_refs", ("formula",))):
            for ref in q.get(field, []):
                rec = kb.get(ref)
                if rec is None or rec["type"] not in kinds:
                    rep.error("MISSING_REF", qid, f"{field}: {ref} inexistente ou não é um de {kinds}")
                elif rec["status"] != CONSUMABLE:
                    rep.pend("DEPENDS_ON_UNAPPROVED", qid, f"{ref} não aprovado ({rec['status']})")

        for name, item in q.get("given_data", {}).items():
            ref = item.get("element_ref")
            if ref is None:
                continue
            el = kb.get(ref)
            if not el or el["type"] != "element":
                rep.error("MISSING_REF", qid, f"given_data.{name}: elemento inexistente {ref}")
                continue
            adopted = el["atomic_mass_reference"]
            try:
                same = abs(units.convert(item["value"], item["unit"], adopted["unit"]) - adopted["value"]) < 1e-9
            except UnitError as e:
                rep.error("UNIT_MISMATCH", qid, f"given_data.{name}: {e}")
                continue
            if not same:
                rep.error("ATOMIC_MASS_MISMATCH", qid, f"given_data.{name} difere da massa adotada na base ({adopted['value']})")

        ctx = {n: (g["value"], g["unit"]) for n, g in q.get("given_data", {}).items()}
        if q["type"] == "numeric":
            _check_step(q, q["calc"], ctx, kb, units, rep)
        elif q["type"] == "multi_step":
            ids = [s["id"] for s in q["steps"]]
            if len(set(ids)) != len(ids):
                rep.error("DUPLICATE_STEP", qid, "ids de etapa repetidos")
            for step in q["steps"]:
                _check_step(q, step, ctx, kb, units, rep)
        else:
            _check_multiple_choice(q, kb, rep)

        if q["status"] != CONSUMABLE:
            rep.pend("NOT_APPROVED", qid, f"status '{q['status']}': aguarda revisão humana")
        elif not q.get("sources"):
            rep.pend("SOURCES_MISSING", qid, "aprovada sem fontes documentadas")
    return rep


def _check_multiple_choice(q: dict, kb: dict, rep: Report) -> None:
    qid = q["id"]
    keys = [o["key"] for o in q["options"]]
    if len(set(keys)) != len(keys):
        rep.error("DUPLICATE_OPTION", qid, "chaves de alternativa repetidas")
    if q["correct"] not in keys:
        rep.error("BAD_CORRECT", qid, f"alternativa correta '{q['correct']}' inexistente")
    for o in q["options"]:
        ref = o.get("mistake_ref")
        if o["key"] == q["correct"]:
            if ref:
                rep.error("CORRECT_HAS_MISTAKE", qid, f"alternativa correta {o['key']} não pode ser um erro comum")
            continue
        if not ref:
            rep.pend("DISTRACTOR_UNJUSTIFIED", qid, f"distrator {o['key']} sem ligação a um erro comum da base")
            continue
        concept = kb.get(ref["concept"])
        mistakes = (concept or {}).get("common_mistakes", [])
        if ref["index"] >= len(mistakes):
            rep.error("MISSING_REF", qid, f"distrator {o['key']}: erro comum inexistente em {ref['concept']}")


def approved_questions(questions: list[dict]) -> list[dict]:
    return [q for q in questions if q.get("status") == CONSUMABLE]


def main(argv: list[str]) -> int:
    kb, tax = load_kb()
    directory = Path(argv[1]) if len(argv) > 1 else QUESTIONS_DIR
    rep = validate_questions(load_questions(directory), kb, tax)
    for i in rep.errors:
        print("ERRO     ", i)
    for i in rep.pending:
        print("PENDÊNCIA", i)
    print(f"\n{len(rep.errors)} erro(s), {len(rep.pending)} pendência(s) de revisão.")
    return 0 if rep.ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
