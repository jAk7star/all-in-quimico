"""Gera schema/question.schema.json a partir de question_models.py.

Uso: python generate_schema.py [--check]
"""

import json
import sys
from pathlib import Path

from question_models import _adapter

SCHEMA_PATH = Path(__file__).parent / "schema" / "question.schema.json"


def build() -> str:
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "SPEC-01 Question",
        "$comment": "GERADO por generate_schema.py a partir de question_models.py. Não editar à mão.",
        **_adapter.json_schema(),
    }
    return json.dumps(schema, indent=2, ensure_ascii=False) + "\n"


if __name__ == "__main__":
    content = build()
    if "--check" in sys.argv:
        current = SCHEMA_PATH.read_text(encoding="utf-8") if SCHEMA_PATH.exists() else ""
        sys.exit(0 if current == content else 1)
    SCHEMA_PATH.write_text(content, encoding="utf-8")
    print(f"Escrito: {SCHEMA_PATH}")
