"""Modelos Pydantic da Knowledge Base (SPEC-00 v0.1.0).

Validação em tempo de execução, por tipo de registro. O contrato interoperável
fica em schema/knowledge.schema.json (os testes verificam que ambos concordam).
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

ID_PATTERN = r"^CHEM-[A-Z]{3}-[A-Z0-9_]+$"
Id = Annotated[str, Field(pattern=ID_PATTERN)]
Text = Annotated[str, Field(min_length=1)]
Status = Literal["draft", "review", "approved", "deprecated"]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _Record(_Base):
    id: Id
    name: Text
    version: Annotated[int, Field(ge=1, strict=True)]
    status: Status
    domain: Annotated[str, Field(pattern=r"^CHEM-[A-Z]{3}$")] | None = None
    topics: list[str] = []
    prerequisites: list[Id] = []
    common_mistakes: list[Text] = []
    examples: list[Text] = []
    sources: list[str] = []
    notes: list[Text] = []


class QuantitativeValue(_Base):
    value: float
    unit: Text
    quantity: str
    context: Text


class Concept(_Record):
    type: Literal["concept"]
    domain: Annotated[str, Field(pattern=r"^CHEM-[A-Z]{3}$")]
    definition: Text
    formula_refs: list[Id] = []


class Element(_Record):
    type: Literal["element"]
    symbol: Annotated[str, Field(pattern=r"^[A-Z][a-z]{0,2}$")]
    atomic_number: Annotated[int, Field(ge=1, le=118, strict=True)]
    atomic_mass_reference: QuantitativeValue


class Variable(_Base):
    name: Text
    unit: Text
    quantity: str | None = None


class Relation(_Base):
    result: str
    op: Literal["divide", "multiply"]
    left: str
    right: str


class Formula(_Record):
    type: Literal["formula"]
    expression: Text
    variables: Annotated[dict[str, Variable], Field(min_length=1)]
    conditions: list[Text]
    limitations: list[Text]
    relation: Relation | None = None
    data_dependencies: list[Literal["atomic_mass", "molar_mass"]] = []


class OtherRecord(_Record):
    """Tipos ainda sem schema próprio na v0.1.0; exigem domínio."""

    model_config = ConfigDict(extra="allow")
    type: Literal["compound", "quantity", "unit", "constant", "skill"]
    domain: Annotated[str, Field(pattern=r"^CHEM-[A-Z]{3}$")]


Record = Annotated[
    Concept | Element | Formula | OtherRecord,
    Field(discriminator="type"),
]
_adapter = TypeAdapter(Record)


def validate_record(data: object) -> list[str]:
    """Retorna lista de mensagens de erro estrutural (vazia se válido)."""
    if not isinstance(data, dict):
        return ["(raiz): registro deve ser um objeto"]
    try:
        _adapter.validate_python(data)
    except Exception as exc:  # pydantic.ValidationError
        errors = getattr(exc, "errors", None)
        if errors is None:
            raise
        return [f"{'.'.join(str(p) for p in e['loc']) or '(raiz)'}: {e['msg']}" for e in errors()]
    return []
