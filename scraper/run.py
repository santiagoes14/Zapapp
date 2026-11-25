"""Orquestador diario: sincroniza Google Sheet, scrapea las 15 tiendas, etiqueta novedades y genera catalog.json."""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from scraper.adapters.others import scrape_digitalsport, scrape_magento, scrape_tiendanube
from scraper.adapters.sfcc import scrape_sfcc
from scraper.adapters.vtex import scrape_vtex
from scraper.notify import send_notifications
from scraper.sheets_sync import load_stores
from scraper.stores_defaults import GOOGLE_SHEET_ID, TIMEZONE

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "web" / "data"
CATALOG_PATH = DATA_DIR / "catalog.json"
HISTORY_PATH = DATA_DIR / "history.json"

ADAPTERS = {
    "vtex": scrape_vtex,
    "sfcc": scrape_sfcc,
    "digitalsport": scrape_digitalsport,
    "magento": scrape_magento,
    "tiendanube": scrape_tiendanube,
}


def load_json(path: Path, default: Any) -> Any:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default
    return default


def run() -> None:
    tz = ZoneInfo(TIMEZONE)
    now = datetime.now(tz)
    today = now.strftime("%Y-%m-%d")

    stores, sync_source = load_stores()
    history: dict[str, dict[str, Any]] = load_json(HISTORY_PATH, {})
    prev_catalog = load_json(CATALOG_PATH, {"products": []})
    prev_active_ids = {p["id"] for p in prev_catalog.get("products", [])}

    all_products: list[dict[str, Any]] = []
    store_statuses: list[dict[str, Any]] = []

    for store in stores:
        adapter = ADAPTERS.get(store["platform"], scrape_vtex)
        t0 = time.time()
        status = "ok"
        error_msg = None
        items: list[dict[str, Any]] = []

        try:
            items = adapter(store)
        except Exception as exc:
            status = "error"
            error_msg = str(exc)

        elapsed = round(time.time() - t0, 1)
        print(f"[{store['name']}] {len(items)} productos en talle {store['size']} ({elapsed}s) - {status}")

        store_statuses.append(
            {
                "id": store["id"],
                "name": store["name"],
                "url": store["url"],
                "platform": store["platform"],
                "size": store["size"],
                "brands": store["brands"],
                "count": len(items),
                "status": status,
                "error": error_msg,
                "elapsed_sec": elapsed,
            }
        )
        all_products.extend(items)

    # Deduplicar por id y calcular etiquetas: NUEVO_HOY, REINGRESO, BAJO_PRECIO
    deduped: dict[str, dict[str, Any]] = {}
    new_items: list[dict[str, Any]] = []
    restock_items: list[dict[str, Any]] = []

    for prod in all_products:
        pid = prod["id"]
        if pid in deduped:
            continue

        prev_record = history.get(pid)
        badge = None
        price_drop = False

        if not prev_record:
            # Primera vez visto en el historial
            first_seen = today
            if history:  # A partir del segundo día, todo ingreso nuevo lleva etiqueta NUEVO_HOY
                badge = "NUEVO_HOY"
        else:
            first_seen = prev_record.get("first_seen", today)
            if first_seen == today:
                badge = "NUEVO_HOY"
            elif pid not in prev_active_ids:
                badge = "REINGRESO"
            prev_price = prev_record.get("last_price")
            if prev_price and prod["price"] < prev_price:
                price_drop = True

        prod["first_seen"] = first_seen
        prod["last_seen"] = today
        prod["badge"] = badge
        prod["price_drop"] = price_drop

        history[pid] = {
            "first_seen": first_seen,
            "last_seen": today,
            "last_price": prod["price"],
            "name": prod["name"],
            "store_name": prod["store_name"],
        }

        if badge == "NUEVO_HOY":
            new_items.append(prod)
        elif badge == "REINGRESO":
            restock_items.append(prod)

        deduped[pid] = prod

    # Ordenar por defecto: Nuevos primero, luego Reingresos, luego menor precio
    badge_rank = {"NUEVO_HOY": 0, "REINGRESO": 1, None: 2}
    sorted_products = sorted(
        deduped.values(),
        key=lambda p: (badge_rank.get(p["badge"], 2), p["price"]),
    )

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    catalog_payload = {
        "updated_at": now.isoformat(),
        "updated_label": now.strftime("%d/%m/%Y %H:%M hs (ART)"),
        "target_size_summary": "47.5 AR / 14 US / 32 cm",
        "google_sheet_url": f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}",
        "sync_source": sync_source,
        "summary": {
            "total_products": len(sorted_products),
            "new_today": len(new_items),
            "restocks_today": len(restock_items),
            "stores_total": len(store_statuses),
            "stores_ok": sum(1 for s in store_statuses if s["status"] == "ok"),
        },
        "stores": store_statuses,
        "products": sorted_products,
    }

    CATALOG_PATH.write_text(json.dumps(catalog_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    HISTORY_PATH.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"[run] Catálogo guardado: {len(sorted_products)} modelos "
        f"({len(new_items)} nuevos hoy, {len(restock_items)} reingresos)."
    )

    send_notifications(new_items, restock_items, len(sorted_products))


if __name__ == "__main__":
    run()
