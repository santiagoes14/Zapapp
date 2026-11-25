"""Adaptadores para Digital Sport (Sport 78, Fluid, Dionysos), Magento (Solo Urbano) y TiendaNube (Drifters)."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote, urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from scraper.sizes import is_footwear_sneaker, matches_target_brand, matches_target_size

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
    m = re.search(r"\$\s*([\d.,]+)", text)
    raw = m.group(1) if m else re.sub(r"[^\d.,]", "", text)
    if not raw:
        return None
    if "," in raw and "." in raw:
        raw = raw.replace(".", "").replace(",", ".")
    elif raw.count(".") >= 1 and len(raw.split(".")[-1]) == 3:
        raw = raw.replace(".", "")
    else:
        raw = raw.replace(",", ".")
    try:
        return float(raw)
    except ValueError:
        return None


def scrape_digitalsport(store: dict[str, Any]) -> list[dict[str, Any]]:
    """Cubre Digital Sport 78, Fluid y Dionysos filtrando por marca y talle 47.5."""
    parsed = urlparse(store["url"])
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    store_path = parsed.path.strip("/")  # sport78, fluid, dionysos
    size = store.get("size") or "47.5"
    brands = store.get("brands") or ["Nike"]

    results: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    with httpx.Client(headers=HEADERS, timeout=25.0, follow_redirects=True) as client:
        for brand in brands:
            search_url = (
                f"{base_url}/{store_path}/search/"
                f"?category=calzado&brand={quote(brand.lower())}&size={quote(size)}"
            )
            try:
                resp = client.get(search_url)
                if resp.status_code != 200:
                    continue
                soup = BeautifulSoup(resp.text, "lxml")
            except Exception:
                continue

            cards = soup.select(".product, .product-card, article.product-item, a[href*='/prods/']")
            for card in cards:
                link_el = card if card.name == "a" else card.select_one("a[href*='/prods/'], a[href]")
                if not link_el or not link_el.get("href"):
                    continue
                prod_url = urljoin(base_url, link_el["href"])
                if prod_url in seen_urls or "/prods/" not in prod_url:
                    continue

                name_el = card.select_one("h2, h3, .product-name, .title, .name")
                name = name_el.get_text(" ", strip=True) if name_el else link_el.get_text(" ", strip=True)
                if not name or not is_footwear_sneaker(name):
                    continue
                if not matches_target_brand("", name, brands):
                    continue

                price_el = card.select_one(".price, .product-price, [class*='price']")
                price = _parse_ars_price(price_el.get_text(" ", strip=True) if price_el else card.get_text(" ", strip=True))
                if not price:
                    continue

                img_el = card.select_one("img")
                image = ""
                if img_el:
                    image = img_el.get("data-src") or img_el.get("src") or ""
                    if image and not image.startswith("http"):
                        image = urljoin(base_url, image)

                seen_urls.add(prod_url)
                results.append(
                    {
                        "id": f"{store['id']}::{prod_url.rstrip('/').split('/')[-1]}",
                        "store_id": store["id"],
                        "store_name": store["name"],
                        "name": name,
                        "brand": brand,
                        "price": price,
                        "list_price": None,
                        "currency": "ARS",
                        "size_label": size,
                        "stock": None,
                        "stock_text": "En stock",
                        "image": image,
                        "url": prod_url,
                    }
                )

    return results


def scrape_magento(store: dict[str, Any]) -> list[dict[str, Any]]:
    """Cubre Solo Urbano (Magento 2) leyendo productos y talles directamente desde el listado."""
    parsed = urlparse(store["url"])
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    size = store.get("size") or "47.5"
    brands = store.get("brands") or ["Nike"]

    results: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    with httpx.Client(headers=HEADERS, timeout=25.0, follow_redirects=True) as client:
        for page in range(1, 6):
            url = f"{store['url']}?p={page}&product_list_limit=24"
            try:
                resp = client.get(url)
                if resp.status_code != 200:
                    break
                soup = BeautifulSoup(resp.text, "lxml")
            except Exception:
                break

            items = soup.select("li.product-item, .product-item-info")
            if not items:
                break

            for item in items:
                link_el = item.select_one("a.product-item-link, a.product-item-photo")
                if not link_el or not link_el.get("href"):
                    continue
                prod_url = urljoin(base_url, link_el["href"])
                if prod_url in seen_urls:
                    continue

                name_el = item.select_one(".product-item-link")
                name = name_el.get_text(" ", strip=True) if name_el else ""
                if not name or not matches_target_brand("", name, brands) or not is_footwear_sneaker(name):
                    continue

                # Solo Urbano expone los talles disponibles directamente en la tarjeta del listado
                size_els = item.select(".swatch-option, [option-label], .talles span, .size-item")
                available_sizes = [
                    (el.get("option-label") or el.get_text(" ", strip=True))
                    for el in size_els
                ]
                if available_sizes and not any(matches_target_size(s, size) for s in available_sizes):
                    continue

                price_el = item.select_one(".special-price .price, .price-final_price .price, .price")
                price = _parse_ars_price(price_el.get_text(" ", strip=True)) if price_el else None
                if not price:
                    continue

                old_el = item.select_one(".old-price .price")
                list_price = _parse_ars_price(old_el.get_text(" ", strip=True)) if old_el else None

                img_el = item.select_one("img.product-image-photo, img")
                image = (img_el.get("data-src") or img_el.get("src") or "") if img_el else ""

                seen_urls.add(prod_url)
                results.append(
                    {
                        "id": f"{store['id']}::{prod_url.rstrip('/').split('/')[-1]}",
                        "store_id": store["id"],
                        "store_name": store["name"],
                        "name": name,
                        "brand": brands[0],
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


def scrape_tiendanube(store: dict[str, Any]) -> list[dict[str, Any]]:
    """Cubre Drifters (TiendaNube) filtrando por marca (Nike SB) y talle 47.5 / 14 US / 32 cm."""
    parsed = urlparse(store["url"])
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    expected_size = store.get("size") or "47.5(14us-32cm)"
    brands = store.get("brands") or ["Nike Sb"]

    results: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    with httpx.Client(headers=HEADERS, timeout=25.0, follow_redirects=True) as client:
        for page in range(1, 6):
            url = f"{store['url'].rstrip('/')}/?mpage={page}"
            try:
                resp = client.get(url)
                if resp.status_code != 200:
                    break
                soup = BeautifulSoup(resp.text, "lxml")
            except Exception:
                break

            cards = soup.select(".js-item-product, .item-product")
            if not cards:
                break

            for card in cards:
                link_el = card.select_one("a.item-link, a[href*='/productos/']")
                if not link_el or not link_el.get("href"):
                    continue
                prod_url = urljoin(base_url, link_el["href"])
                if prod_url in seen_urls:
                    continue

                name_el = card.select_one(".js-item-name, .item-name")
                name = name_el.get_text(" ", strip=True) if name_el else ""
                if not name or not matches_target_brand("", name, brands) or not is_footwear_sneaker(name):
                    continue

                # TiendaNube incluye variantes en el atributo data-variants JSON del card o botones de talle
                variants_raw = card.get("data-variants") or ""
                size_buttons = [el.get_text(" ", strip=True) for el in card.select(".js-insta-variant, [data-option]")]
                has_size = matches_target_size(variants_raw, expected_size) or any(
                    matches_target_size(s, expected_size) for s in size_buttons
                )
                if not has_size:
                    continue

                price_el = card.select_one(".js-price-display, .item-price")
                price = _parse_ars_price(price_el.get_text(" ", strip=True)) if price_el else None
                if not price:
                    continue

                old_el = card.select_one(".js-compare-price-display")
                list_price = _parse_ars_price(old_el.get_text(" ", strip=True)) if old_el else None

                img_el = card.select_one("img")
                image = ""
                if img_el:
                    image = img_el.get("data-srcset") or img_el.get("data-src") or img_el.get("src") or ""
                    image = image.split(",")[0].strip().split(" ")[0]
                    if image.startswith("//"):
                        image = f"https:{image}"

                seen_urls.add(prod_url)
                results.append(
                    {
                        "id": f"{store['id']}::{prod_url.rstrip('/').split('/')[-1]}",
                        "store_id": store["id"],
                        "store_name": store["name"],
                        "name": name,
                        "brand": brands[0],
                        "price": price,
                        "list_price": list_price if (list_price and list_price > price) else None,
                        "currency": "ARS",
                        "size_label": expected_size,
                        "stock": None,
                        "stock_text": "En stock",
                        "image": image,
                        "url": prod_url,
                    }
                )

    return results
