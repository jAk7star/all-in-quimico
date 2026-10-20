import argparse
import sys
from pathlib import Path

import yaml
from mechanics_models import AuctionRules
from pydantic import ValidationError

ROOT = Path(__file__).parent


def load_rules(file_path: Path) -> dict:
    with file_path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate_rules(rules_dict: dict) -> AuctionRules:
    return AuctionRules.model_validate(rules_dict)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validador das regras do leilão.")
    parser.add_argument("--rules", default=str(ROOT / "rules" / "base_rules.yaml"))
    args = parser.parse_args(argv)

    rules_path = Path(args.rules)
    if not rules_path.exists():
        print(f"Arquivo não encontrado: {rules_path}")
        return 1

    data = load_rules(rules_path)
    try:
        rules = validate_rules(data)
    except ValidationError as e:
        print("Erro de validação nas regras:")
        print(e)
        return 1
    
    print(f"Regras validadas com sucesso. Moeda: {rules.currency_name}, Blocos: {len(rules.blocks)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
