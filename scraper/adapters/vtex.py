"""Adaptador VTEX (API pública de catálogo): cubre 8 de las 15 tiendas."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

import httpx

from scraper.sizes import is_footwear_sneaker, matches_target_brand, matches_target_size

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Sec-Ch-Ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"macOS"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
}


def _extract_sku_size(item: dict[str, Any]) -> str:
    """Extrae el talle de un SKU VTEX leyendo variations y claves comunes."""
    # 1. Revisar los nombres de variación declarados por la tienda
    for var_key in item.get("variations") or []:
        if any(k in var_key.lower() for k in ("talle", "talla", "size", "nro", "numero", "tamaño")):
            val = item.get(var_key)
            if isinstance(val, list) and val:
                return str(val[0]).strip()
            if isinstance(val, str) and val.strip():
                return val.strip()

    # 2. Claves habituales en VTEX Argentina
    for key in ("Talle", "talle", "Talla", "talla", "Tamaño", "Size", "Talle Arg", "Talle AR", "Talle US"):
        val = item.get(key)
        if isinstance(val, list) and val:
            return str(val[0]).strip()
        if isinstance(val, str) and val.strip():
            return val.strip()

    return str(item.get("name") or item.get("nameComplete") or "")


def _extract_offer(item: dict[str, Any]) -> tuple[bool, float | None, float | None, int | None]:
    """Devuelve (available, price, list_price, stock_qty) de los sellers VTEX."""
    for seller in item.get("sellers") or []:
        offer = seller.get("commertialOffer") or {}
        qty = offer.get("AvailableQuantity")
        is_avail = offer.get("IsAvailable")
        price = offer.get("Price")
        list_price = offer.get("ListPrice")
        if (is_avail is True or (isinstance(qty, (int, float)) and qty > 0)) and price:
            stock_int = int(qty) if isinstance(qty, (int, float)) and qty > 0 else None
            return True, float(price), float(list_price) if list_price else None, stock_int
    return False, None, None, None


def scrape_vtex(store: dict[str, Any], max_pages: int = 10) -> list[dict[str, Any]]:
    parsed = urlparse(store["url"])
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    brands = store.get("brands") or ["Nike"]
    expected_size = store.get("size")

    seen_ids: set[str] = set()
    results: list[dict[str, Any]] = []
    page_size = 50
    raw_total = 0

    req_headers = {
        **HEADERS,
        "Referer": f"{base_url}/",
        "Origin": base_url,
    }

    with httpx.Client(headers=req_headers, timeout=25.0, follow_redirects=True) as client:
        # Calentar la sesión para obtener cookies iniciales del WAF/VTEX
        try:
            client.get(
                base_url,
                headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                },
            )
        except httpx.HTTPError:
            pass

        for brand in brands:
            search_term = brand.strip()
            for page in range(max_pages):
                start = page * page_size
                end = start + page_size - 1
                endpoint = f"{base_url}/api/catalog_system/pub/products/search"
                params = {
                    "ft": search_term,
                    "_from": start,
                    "_to": end,
                }
                resp = client.get(endpoint, params=params)
                if resp.status_code not in (200, 206):
                    if page == 0 and raw_total == 0:
                        raise RuntimeError(f"HTTP {resp.status_code} al consultar API VTEX")
                    break

                products = resp.json()
                if not isinstance(products, list) or not products:
                    break

                raw_total += len(products)

                for prod in products:
                    prod_id = str(prod.get("productId") or prod.get("productReference") or "")
                    if not prod_id or prod_id in seen_ids:
                        continue

                    name = str(prod.get("productName") or "").strip()
                    prod_brand = str(prod.get("brand") or "").strip()
                    categories = " ".join(prod.get("categories") or [])

                    if not matches_target_brand(prod_brand, name, brands):
                        continue
                    if not is_footwear_sneaker(name, categories):
                        continue

                    matched_offer = None
                    matched_size_label = None
                    matched_image = None

                    for item in prod.get("items") or []:
                        raw_size = _extract_sku_size(item)
                        if not matches_target_size(raw_size, expected_size):
                            continue
                        avail, price, list_price, stock_qty = _extract_offer(item)
                        if not avail or price is None:
                            continue

                        images = item.get("images") or []
                        img_url = images[0].get("imageUrl") if images else ""
                        matched_offer = (price, list_price, stock_qty)
                        matched_size_label = raw_size
                        matched_image = img_url
                        break

                    if not matched_offer:
                        continue

                    price, list_price, stock_qty = matched_offer
                    link = str(prod.get("link") or "").strip()
                    if link and not link.startswith("http"):
                        link = f"{base_url}/{link.lstrip('/')}"

                    seen_ids.add(prod_id)
                    results.append(
                        {
                            "id": f"{store['id']}::{prod_id}",
                            "store_id": store["id"],
                            "store_name": store["name"],
                            "name": name,
                            "brand": prod_brand or search_term,
                            "price": price,
                            "list_price": list_price if (list_price and list_price > price) else None,
                            "currency": "ARS",
                            "size_label": matched_size_label or expected_size or "47.5",
                            "stock": stock_qty,
                            "stock_text": f"{stock_qty} u. disponibles" if stock_qty else "En stock",
                            "image": matched_image or "",
                            "url": link or store["url"],
                        }
                    )

                if len(products) < page_size:
                    break

    return results
