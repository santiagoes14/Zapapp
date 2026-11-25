"""Adaptador Salesforce Commerce Cloud / Demandware (New Balance y Stock Center)."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from scraper.sizes import is_footwear_sneaker, matches_target_brand

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-AR,es;q=0.9",
}


def _parse_ars_price(text: str) -> float | None:
    if not text:
        return None
    cleaned = re.sub(r"[^\d,.]", "", text)
    if not cleaned:
        return None
    # Formato argentino: $289.999 o $289.999,00
    if "," in cleaned and "." in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    elif cleaned.count(".") >= 1 and len(cleaned.split(".")[-1]) == 3:
        cleaned = cleaned.replace(".", "")
    else:
        cleaned = cleaned.replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


def scrape_sfcc(store: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Consulta el listado SFCC filtrado por talle (y marca cuando aplica).
    Funciona tanto para Stock Center como para New Balance Argentina.
    """
    parsed = urlparse(store["url"])
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    size = store.get("size") or "47.5"
    brands = store.get("brands") or []

    # Parámetros estándar de refinamiento en Demandware / SFCC
    candidate_urls: list[str] = []
    if "stockcenter.com.ar" in parsed.netloc:
        candidate_urls.append(
            f"{base_url}/on/demandware.store/Sites-StockCenter-Site/default/Search-UpdateGrid"
            f"?cgid=hombre-calzado&prefn1=size&prefv1={size}&prefn2=brand&prefv2=Nike&start=0&sz=72"
        )
    elif "newbalance.com.ar" in parsed.netloc:
        candidate_urls.append(
            f"{store['url'].rstrip('/')}?prefn1=size&prefv1={size}&start=0&sz=72"
        )
    else:
        candidate_urls.append(f"{store['url']}?prefn1=size&prefv1={size}&sz=72")

    results: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    with httpx.Client(headers=HEADERS, timeout=25.0, follow_redirects=True) as client:
        for url in candidate_urls:
            try:
                resp = client.get(url)
                if resp.status_code != 200:
                    continue
                soup = BeautifulSoup(resp.text, "lxml")
            except Exception:
                continue

            tiles = soup.select(".product-tile, .product, [data-pid]")
            for tile in tiles:
                pid = tile.get("data-pid") or ""
                link_el = tile.select_one("a.link, .pdp-link a, a[href*='.html'], a[href*='/']")
                if not link_el or not link_el.get("href"):
                    continue
                prod_url = urljoin(base_url, link_el["href"])
                if prod_url in seen_urls:
                    continue

                name_el = tile.select_one(".pdp-link a, .product-name, .tile-body .link, h2, h3")
                name = name_el.get_text(" ", strip=True) if name_el else link_el.get_text(" ", strip=True)
                if not name or not is_footwear_sneaker(name):
                    continue
                if not matches_target_brand("", name, brands):
                    # En New Balance el nombre a veces es solo el código/modelo ("9060 X", "1080v15")
                    if "newbalance.com.ar" not in parsed.netloc:
                        continue

                price_el = tile.select_one(".sales .value, .price .sales, .value[content], .price")
                price = None
                if price_el:
                    price = _parse_ars_price(price_el.get("content") or price_el.get_text(" ", strip=True))
                if not price:
                    continue

                list_el = tile.select_one(".strike-through .value, .list .value")
                list_price = _parse_ars_price(list_el.get("content") or list_el.get_text(" ", strip=True)) if list_el else None

                img_el = tile.select_one("img.tile-image, img")
                image = ""
                if img_el:
                    image = img_el.get("data-src") or img_el.get("src") or ""
                    if image.startswith("//"):
                        image = f"https:{image}"
                    elif image and not image.startswith("http"):
                        image = urljoin(base_url, image)

                seen_urls.add(prod_url)
                results.append(
                    {
                        "id": f"{store['id']}::{pid or prod_url.split('/')[-1]}",
                        "store_id": store["id"],
                        "store_name": store["name"],
                        "name": name,
                        "brand": brands[0] if brands else store["name"],
                        "price": price,
                        "list_price": list_price if (list_price and list_price > price) else None,
                        "currency": "ARS",
                        "size_label": size,
                        "stock": None,
                        "stock_text": "En stock",
                        "image": image,
                        "url": prod_url,
                    }
                )

    return results
