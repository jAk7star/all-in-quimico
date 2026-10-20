"""Gera schema/knowledge.schema.json a partir dos modelos Pydantic (fonte única).

Uso: python generate_schema.py          # grava o arquivo
     python generate_schema.py --check  # falha se estiver desatualizado
"""

import json
import sys

from models import _adapter
from validate_knowledge import SCHEMA_PATH


def build() -> str:
    schema = _adapter.json_schema()
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "SPEC-00 Knowledge record",
        "$comment": "GERADO por generate_schema.py a partir de models.py. Não editar à mão.",
        **schema,
    }
    return json.dumps(schema, indent=2, ensure_ascii=False) + "\n"


if __name__ == "__main__":
    content = build()
    if "--check" in sys.argv:
        current = SCHEMA_PATH.read_text(encoding="utf-8") if SCHEMA_PATH.exists() else ""
        sys.exit(0 if current == content else 1)
    SCHEMA_PATH.write_text(content, encoding="utf-8")
    print(f"Escrito: {SCHEMA_PATH}")
