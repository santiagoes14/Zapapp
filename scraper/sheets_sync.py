"""Sincroniza la lista de tiendas desde el Google Sheet del usuario con fallback local."""

from __future__ import annotations

import csv
import io
import os
import re
from typing import Any
from urllib.parse import urlparse

import httpx

from scraper.stores_defaults import DEFAULT_STORES, GOOGLE_SHEET_CSV_URL


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "store"


def detect_platform(url: str) -> str:
    """Detecta automáticamente la plataforma del ecommerce según dominio/ruta."""
    host = urlparse(url).netloc.lower()
    path = urlparse(url).path.lower()

    if "digitalsport.com.ar" in host:
        return "digitalsport"
    if "stockcenter.com.ar" in host or "newbalance.com.ar" in host:
        return "sfcc"
    if "solourbano.com" in host or path.endswith(".html"):
        return "magento"
    if "drifters.com.ar" in host:
        return "tiendanube"
    return "vtex"


def parse_brands(raw: str) -> list[str]:
    return [b.strip() for b in re.split(r"[,;/]", raw or "") if b.strip()]


def load_stores() -> tuple[list[dict[str, Any]], str]:
    """
    Lee las tiendas desde el Google Sheet (si tiene acceso de lectura por enlace)
    y cae automáticamente en DEFAULT_STORES si el Sheet es privado o falla la red.
    """
    csv_url = os.getenv("GOOGLE_SHEET_CSV_URL", GOOGLE_SHEET_CSV_URL)

    try:
        with httpx.Client(timeout=15.0, follow_redirects=True) as client:
            resp = client.get(csv_url)
            resp.raise_for_status()
            body = resp.text

        if "<html" in body[:500].lower():
            print("[sheets_sync] Sheet privado; usando lista local (compartilo como lectura para sincronización automática).")
            return DEFAULT_STORES, "local_fallback"

        reader = csv.DictReader(io.StringIO(body))
        parsed: list[dict[str, Any]] = []
        known_by_url = {s["url"].rstrip("/").lower(): s for s in DEFAULT_STORES}

        for row in reader:
            name = (row.get("Sitio web") or row.get("Sitio") or "").strip()
            url = (row.get("URL") or "").strip()
            size = (row.get("Talle / Talla") or row.get("Talle") or "47.5").strip()
            brands = parse_brands(row.get("Marca") or row.get("Marcas") or "")
            if not name or not url:
                continue

            existing = known_by_url.get(url.rstrip("/").lower(), {})
            parsed.append(
                {
                    "id": existing.get("id") or slugify(name),
                    "name": name,
                    "url": url,
                    "platform": existing.get("platform") or detect_platform(url),
                    "size": size,
                    "brands": brands,
                }
            )

        if parsed:
            print(f"[sheets_sync] Sincronizadas {len(parsed)} tiendas desde Google Sheets.")
            return parsed, "google_sheet"
    except Exception as exc:
        print(f"[sheets_sync] Error leyendo Google Sheet ({exc}); usando lista local.")

    return DEFAULT_STORES, "local_fallback"
