"""Validação da Knowledge Base (SPEC-00 v0.1.0).

Camadas: estrutural (JSON Schema) -> referencial -> científica parcial.
Separa ERROS (base inválida) de PENDÊNCIAS (revisão humana necessária).
A ausência de erros NÃO implica aprovação científica (SPEC-00 §13.3/§13.4).

Uso: python validate_knowledge.py [diretório_knowledge]
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from models import validate_record

ROOT = Path(__file__).parent
SCHEMA_PATH = ROOT / "schema" / "knowledge.schema.json"
KNOWLEDGE_DIR = ROOT / "knowledge"

# Grandeza -> unidades aceitas (compatibilidade grandeza x unidade, §8).
QUANTITY_UNITS: dict[str, set[str]] = {
    "mass": {"g", "kg", "mg"},
    "volume": {"L", "mL"},
    "amount_of_substance": {"mol", "mmol"},
    "molar_mass": {"g/mol", "kg/mol"},
    "common_concentration": {"g/L", "g/mL"},
    "molar_concentration": {"mol/L", "mmol/L"},
}
CONSUMABLE_STATUS = "approved"


@dataclass
class Issue:
    code: str
    record_id: str | None
    message: str

    def __str__(self) -> str:
        return f"[{self.code}] {self.record_id or '-'}: {self.message}"


@dataclass
class Report:
    errors: list[Issue] = field(default_factory=list)
    pending: list[Issue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def error(self, code, rid, msg):
        self.errors.append(Issue(code, rid, msg))

    def pend(self, code, rid, msg):
        self.pending.append(Issue(code, rid, msg))


def load_yaml(path: Path):
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_taxonomy(knowledge_dir: Path = KNOWLEDGE_DIR) -> dict:
    return load_yaml(knowledge_dir / "taxonomy.yaml")


def load_records(knowledge_dir: Path = KNOWLEDGE_DIR) -> list[dict]:
    records: list[dict] = []
    for path in sorted(knowledge_dir.glob("*.yaml")):
        if path.name == "taxonomy.yaml":
            continue
        data = load_yaml(path) or {}
        records.extend(data.get("records") or [])
    return records


def _divide_unit(left: str, right: str) -> str | None:
    """Unidade esperada de left/right; None se não reconhecida."""
    if "/" not in left and "/" not in right:
        return f"{left}/{right}"
    if "/" in right:
        num, den = right.split("/", 1)
        if num == left and "/" not in den:
            return den  # g / (g/mol) = mol
    return None


def _check_dimension(rec: dict, report: Report) -> None:
    rel = rec.get("relation")
    variables = rec["variables"]
    if not rel:
        report.pend("DIMENSION_UNVERIFIED", rec["id"], "sem 'relation': consistência dimensional exige revisão humana")
        return
    names = [rel["result"], rel["left"], rel["right"]]
    missing = [n for n in names if n not in variables]
    if missing:
        report.error("RELATION_VARIABLE", rec["id"], f"variáveis da relação não declaradas: {missing}")
        return
    if rel["op"] != "divide":
        report.pend("DIMENSION_UNVERIFIED", rec["id"], f"operação '{rel['op']}' não verificada automaticamente")
        return
    expected = _divide_unit(variables[rel["left"]]["unit"], variables[rel["right"]]["unit"])
    got = variables[rel["result"]]["unit"]
    if expected is None:
        report.pend("DIMENSION_UNVERIFIED", rec["id"], "unidades não reconhecidas para verificação dimensional")
    elif expected != got:
        report.error("DIMENSION", rec["id"], f"unidade esperada {expected}, declarada {got}")


def _check_units(rec: dict, quantity: str | None, unit: str, where: str, report: Report) -> None:
    if quantity is None:
        return
    allowed = QUANTITY_UNITS.get(quantity)
    if allowed is None:
        report.pend("QUANTITY_UNKNOWN", rec["id"], f"{where}: grandeza '{quantity}' sem unidades registradas")
    elif unit not in allowed:
        report.error("UNIT_MISMATCH", rec["id"], f"{where}: unidade '{unit}' incompatível com {quantity}")


def _check_science(rec: dict, report: Report) -> None:
    if rec["type"] == "element":
        ref = rec["atomic_mass_reference"]
        if ref["value"] <= 0:
            report.error("INVALID_VALUE", rec["id"], "massa atômica deve ser > 0")
        _check_units(rec, ref["quantity"], ref["unit"], "atomic_mass_reference", report)
    elif rec["type"] == "formula":
        for var, spec in rec["variables"].items():
            _check_units(rec, spec.get("quantity"), spec["unit"], f"variável {var}", report)
        _check_dimension(rec, report)
        quantities = {v.get("quantity") for v in rec["variables"].values()}
        for dep in rec.get("data_dependencies", []):
            if dep not in quantities:
                report.error("DEPENDENCY_MISSING", rec["id"], f"depende de '{dep}', mas nenhuma variável o fornece")


def _find_cycles(graph: dict[str, list[str]]) -> list[list[str]]:
    cycles, state = [], {}

    def visit(node, stack):
        state[node] = 1
        for nxt in graph.get(node, []):
            if state.get(nxt) == 1:
                cycles.append([*stack[stack.index(nxt):], nxt] if nxt in stack else [node, nxt])
            elif nxt not in state:
                visit(nxt, [*stack, nxt])
        state[node] = 2

    for n in graph:
        if n not in state:
            visit(n, [n])
    return cycles


def validate_records(records: list[dict], taxonomy: dict) -> Report:
    report = Report()

    # 1. Estrutural (modelos Pydantic em models.py)
    structurally_valid = []
    for rec in records:
        rid = rec.get("id") if isinstance(rec, dict) else None
        errs = validate_record(rec)
        for msg in errs:
            report.error("SCHEMA", rid, msg)
        if not errs:
            structurally_valid.append(rec)

    # 2. Referencial
    seen: dict[str, dict] = {}
    for rec in structurally_valid:
        if rec["id"] in seen:
            report.error("DUPLICATE_ID", rec["id"], "identificador duplicado")
        seen[rec["id"]] = rec
    domains = {d["id"]: set(d["topics"]) for d in taxonomy["domains"]}
    graph: dict[str, list[str]] = {}
    for rec in structurally_valid:
        rid = rec["id"]
        for field_name in ("prerequisites", "formula_refs"):
            for ref in rec.get(field_name, []):
                if ref not in seen:
                    report.error("MISSING_REF", rid, f"{field_name} referencia ID inexistente: {ref}")
        graph[rid] = [r for r in rec.get("prerequisites", []) if r in seen]
        dom = rec.get("domain")
        if dom is not None and dom not in domains:
            report.error("UNKNOWN_DOMAIN", rid, f"domínio inexistente: {dom}")
        for topic in rec.get("topics", []):
            if dom in domains and topic not in domains[dom]:
                report.error("UNKNOWN_TOPIC", rid, f"tópico '{topic}' inexistente em {dom}")
    for cyc in _find_cycles(graph):
        report.error("CYCLE", cyc[0], "pré-requisitos circulares: " + " -> ".join(cyc))

    # 3. Científica parcial + pendências de revisão
    for rec in structurally_valid:
        _check_science(rec, report)
        if rec["status"] != CONSUMABLE_STATUS:
            report.pend("NOT_APPROVED", rec["id"], f"status '{rec['status']}': aguarda revisão científica")
        elif not rec.get("sources"):
            report.pend("SOURCES_MISSING", rec["id"], "aprovado sem fontes documentadas")
        if rec["status"] == CONSUMABLE_STATUS:
            for ref in rec.get("prerequisites", []) + rec.get("formula_refs", []):
                if ref in seen and seen[ref]["status"] != CONSUMABLE_STATUS:
                    report.pend("DEPENDS_ON_UNAPPROVED", rec["id"], f"referencia {ref} não aprovado")
    return report


def validate_directory(knowledge_dir: Path = KNOWLEDGE_DIR) -> Report:
    """Valida knowledge/ junto com examples/ (registros-exemplo da SPEC, §10), se existir."""
    records = load_records(knowledge_dir)
    examples = knowledge_dir.parent / "examples"
    if examples.is_dir():
        records += load_records(examples)
    return validate_records(records, load_taxonomy(knowledge_dir))


def approved_records(records: list[dict]) -> list[dict]:
    """Registros consumíveis na produção de materiais (§6.2)."""
    return [r for r in records if r.get("status") == CONSUMABLE_STATUS]


def main(argv: list[str]) -> int:
    directory = Path(argv[1]) if len(argv) > 1 else KNOWLEDGE_DIR
    report = validate_directory(directory)
    for i in report.errors:
        print("ERRO     ", i)
    for i in report.pending:
        print("PENDÊNCIA", i)
    print(f"\n{len(report.errors)} erro(s), {len(report.pending)} pendência(s) de revisão.")
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
