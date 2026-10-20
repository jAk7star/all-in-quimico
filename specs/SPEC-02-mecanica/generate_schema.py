import json
from pathlib import Path

from mechanics_models import AuctionRules

ROOT = Path(__file__).parent


def main():
    schema = AuctionRules.model_json_schema()
    schema_path = ROOT / "schema" / "mechanics.schema.json"
    schema_path.write_text(json.dumps(schema, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Schema gerado em: {schema_path}")


if __name__ == "__main__":
    main()
