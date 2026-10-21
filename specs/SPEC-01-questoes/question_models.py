"""Modelos Pydantic de questão (SPEC-01 v0.1.0).

A questão REFERENCIA a Knowledge Base (SPEC-00) por ID e não duplica dados
científicos. Não há campos de pontuação, aposta ou layout (extra="forbid").
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, model_validator

Id = Annotated[str, Field(pattern=r"^CHEM-[A-Z]{3}-[A-Z0-9_]+$")]
Text = Annotated[str, Field(min_length=1)]
Slug = Annotated[str, Field(pattern=r"^[a-z][a-z0-9_]*$")]
Status = Literal["draft", "review", "approved", "deprecated"]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


class GivenItem(_Base):
    """Dado fornecido ao estudante. `element_ref` marca uma massa atômica da base."""

    value: float
    unit: Text
    description: Text | None = None
    element_ref: Id | None = None


class Expected(_Base):
    value: float
    unit: Text
    tolerance: Annotated[float, Field(gt=0, le=0.5)]  # tolerância relativa
    rounding: Text | None = None  # regra de arredondamento adotada


class Step(_Base):
    """Cálculo recalculável pelo validador: aplicação de fórmula ou massa molar."""

    id: Slug
    kind: Literal["formula", "molar_mass"]
    prompt: Text | None = None
    formula_ref: Id | None = None
    target: str | None = None  # variável a determinar (kind=formula)
    inputs: dict[str, str] = {}  # variável da fórmula -> nome de dado/etapa anterior
    composition: dict[Id, Annotated[int, Field(ge=1)]] | None = None  # kind=molar_mass
    expected: Expected

    @model_validator(mode="after")
    def _coherent(self) -> Step:
        if self.kind == "formula" and not (self.formula_ref and self.target):
            raise ValueError("kind=formula exige formula_ref e target")
        if self.kind == "molar_mass" and not self.composition:
            raise ValueError("kind=molar_mass exige composition")
        return self


class _Question(_Base):
    id: Annotated[str, Field(pattern=r"^Q-[A-Z]{3}-[0-9]{3}$")]
    version: Annotated[int, Field(ge=1, strict=True)]
    status: Status
    domain: Annotated[str, Field(pattern=r"^CHEM-[A-Z]{3}$")]
    statement: Text
    skill: Text
    cognitive_level: Literal["recognition", "understanding", "application", "analysis"]
    difficulty: Literal[1, 2, 3]
    concept_refs: Annotated[list[Id], Field(min_length=1)]
    formula_refs: list[Id] = []
    given_data: dict[Slug, GivenItem] = {}
    assumptions: list[Text] = []
    worked_solution: Text
    scientific_justification: Text
    sources: list[str] = []


class NumericQuestion(_Question):
    type: Literal["numeric"]
    calc: Step


class MultiStepQuestion(_Question):
    type: Literal["multi_step"]
    steps: Annotated[list[Step], Field(min_length=2)]


class MistakeRef(_Base):
    concept: Id
    index: Annotated[int, Field(ge=0)]  # posição em common_mistakes do conceito


class Option(_Base):
    key: Annotated[str, Field(pattern=r"^[AB]$")]
    text: Text
    rationale: Text
    mistake_ref: MistakeRef | None = None


class MultipleChoiceQuestion(_Question):
    type: Literal["multiple_choice"]
    options: Annotated[list[Option], Field(min_length=2, max_length=2)]
    correct: Annotated[str, Field(pattern=r"^[AB]$")]
    calc: Step | None = None
    steps: Annotated[list[Step], Field(min_length=2)] | None = None


Question = Annotated[
    MultipleChoiceQuestion,
    Field(discriminator="type"),
]
_adapter = TypeAdapter(Question)


def validate_question(data: object) -> list[str]:
    """Mensagens de erro estrutural (vazia se válido)."""
    if not isinstance(data, dict):
        return ["(raiz): questão deve ser um objeto"]
    try:
        _adapter.validate_python(data)
    except Exception as exc:
        errors = getattr(exc, "errors", None)
        if errors is None:
            raise
        return [f"{'.'.join(str(p) for p in e['loc']) or '(raiz)'}: {e['msg']}" for e in errors()]
    return []
