#!/usr/bin/env python3
"""
publicar_decks_google_slides.py — Criação e Publicação Online dos 10 Decks no Google Slides.
=============================================================================================
1. Itera por todos os 10 decks configurados no All-In Químico.
2. Cria cada apresentação no Google Slides via `gslides mutate create --title <título>`.
3. Aplica o batch JSON correspondente via `apply_batch_to_deck(pres_id, batch_file)`.
4. Atualiza o decks_manifest.json com os IDs oficiais gerados.
5. Emite a tabela consolidada com os links diretos para cada apresentação.
"""

import json
import re
import subprocess
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

import gerar_slides_perguntas_respostas as g


def create_presentation(title: str) -> str:
    """Cria uma nova apresentação no Google Slides e retorna seu ID."""
    cmd = ["gslides", "mutate", "create", "--title", title]
    res = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        shell=True,
    )
    if res.returncode != 0:
        raise RuntimeError(f"Erro ao criar apresentação '{title}':\n{res.stderr}")

    m = re.search(r"\(ID:\s*([a-zA-Z0-9_-]+)\)", res.stdout)
    if not m:
        m = re.search(r"\b([a-zA-Z0-9_-]{25,})\b", res.stdout)
    if not m:
        raise RuntimeError(f"Não foi possível extrair o ID da apresentação. Saída:\n{res.stdout}")

    return m.group(1).strip()


def main():
    print("\n" + "=" * 80)
    print("PUBLICADOR AUTOMATIZADO DE DECKS NO GOOGLE SLIDES — ALL-IN QUÍMICO")
    print("=" * 80 + "\n")

    manifest_path = g.MANIFEST_PATH
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifesto não encontrado em: {manifest_path}")

    with manifest_path.open("r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    batch_dir = g.BATCH_FILES_DIR
    results = []

    total_decks = len(g.DECK_CONFIGS)
    for idx, cfg in enumerate(g.DECK_CONFIGS, start=1):
        batch_file = batch_dir / cfg.batch_filename
        if not batch_file.exists():
            raise FileNotFoundError(f"Arquivo de lote não encontrado: {batch_file}")

        if cfg.presentation_id:
            pres_id = cfg.presentation_id
            edit_url = f"https://docs.google.com/presentation/d/{pres_id}/edit"
            print(f"[{idx}/{total_decks}] Usando apresentação já configurada: '{cfg.title}' ({pres_id})")
        else:
            print(f"[{idx}/{total_decks}] Criando apresentação no Google Slides: '{cfg.title}'...")
            pres_id = create_presentation(cfg.title)
            edit_url = f"https://docs.google.com/presentation/d/{pres_id}/edit"
            print(f"       ID gerado: {pres_id}")

            print(f"       Aplicando batch '{batch_file.name}' in-place...")
            g.apply_batch_to_deck(pres_id, batch_file)
            print(f"       [OK] Apresentação pronta: {edit_url}\n")
            time.sleep(1)

        results.append({
            "deck_id": cfg.deck_id,
            "type": cfg.deck_type,
            "title": cfg.title,
            "presentation_id": pres_id,
            "edit_url": edit_url,
            "batch_file": cfg.batch_filename,
            "question_ids": cfg.question_ids,
        })

    # Atualiza o decks_manifest.json
    id_map = {r["deck_id"]: r["presentation_id"] for r in results}

    if manifest_data.get("decks", {}).get("test_deck"):
        t_id = manifest_data["decks"]["test_deck"]["deck_id"]
        manifest_data["decks"]["test_deck"]["presentation_id"] = id_map.get(t_id, "")

    for item in manifest_data.get("decks", {}).get("challenges", []):
        c_id = item["deck_id"]
        item["presentation_id"] = id_map.get(c_id, "")

    for item in manifest_data.get("decks", {}).get("regular_decks", []):
        r_id = item["deck_id"]
        item["presentation_id"] = id_map.get(r_id, "")

    if manifest_data.get("decks", {}).get("tiebreaker_deck"):
        tb_id = manifest_data["decks"]["tiebreaker_deck"]["deck_id"]
        manifest_data["decks"]["tiebreaker_deck"]["presentation_id"] = id_map.get(tb_id, "")

    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest_data, f, ensure_ascii=False, indent=2)

    print("=" * 80)
    print("MANIFESTO ATUALIZADO COM SUCESSO!")
    print(f"Arquivo salvo em: {manifest_path}")
    print("=" * 80 + "\n")

    print("RESUMO DE PUBLICAÇÃO:")
    for r in results:
        print(f"• {r['title']}")
        print(f"  ID: {r['presentation_id']}")
        print(f"  Link: {r['edit_url']}\n")


if __name__ == "__main__":
    main()
