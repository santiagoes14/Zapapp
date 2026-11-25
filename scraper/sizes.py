"""Normalización y coincidencia estricta de talles (47.5 AR / 14 US / 32 cm)."""

from __future__ import annotations

import re
from typing import Iterable


TARGET_PATTERNS = [
    # 47.5 / 47,5 (AR / EU)
    re.compile(r"(?<!\d)47[.,]5(?!\d)", re.IGNORECASE),
    # 14 US / US 14 / 14M / M14
    re.compile(r"(?<!\d)(?:us\s*14(?:[.,]0)?|14(?:[.,]0)?\s*us|m\s*14(?:[.,]0)?)(?!\d)", re.IGNORECASE),
    # Exact standalone "14" or "14.0" (used by Nike AR & New Balance)
    re.compile(r"^\s*14(?:[.,]0)?\s*$", re.IGNORECASE),
    # 32 cm / 32cm / 32.0 cm
    re.compile(r"(?<!\d)32(?:[.,]0)?\s*cm\b", re.IGNORECASE),
]


def normalize_token(value: str) -> str:
    """Limpia espacios y normaliza comas/mayúsculas."""
    cleaned = re.sub(r"\s+", " ", (value or "").strip()).lower()
    return cleaned.replace(",", ".")


def matches_target_size(raw_size: str, store_expected_size: str | None = None) -> bool:
    """
    Devuelve True si `raw_size` corresponde al talle buscado:
    - Coincidencia exacta con el talle configurado para la tienda
    - Equivalentes genéricos: 47.5 / 47,5 AR, 14 US, 32 cm
    """
    if not raw_size:
        return False

    norm_raw = normalize_token(raw_size)

    if store_expected_size:
        norm_expected = normalize_token(store_expected_size)
        if norm_raw == norm_expected:
            return True

    for pattern in TARGET_PATTERNS:
        if pattern.search(raw_size):
            return True

    return False


def matches_target_brand(
    product_brand: str | None,
    product_name: str | None,
    allowed_brands: Iterable[str],
) -> bool:
    """Verifica si la marca o el nombre del producto coincide con las marcas deseadas."""
    allowed = [b.strip().lower() for b in allowed_brands if b and b.strip()]
    if not allowed:
        return True

    brand_text = (product_brand or "").strip().lower()
    name_text = (product_name or "").strip().lower()
    combined = f"{brand_text} {name_text}"

    for target in allowed:
        # Handle "nike sb" specifically so it doesn't match generic non-SB if only Nike SB is requested
        if target == "nike sb":
            if "nike sb" in combined or ("nike" in combined and "sb" in name_text.split()):
                return True
        elif target == "nike sportswear":
            if "nike" in combined:
                return True
        elif target in brand_text or re.search(rf"\b{re.escape(target)}\b", combined):
            return True

    return False


def is_footwear_sneaker(product_name: str, category_text: str = "") -> bool:
    """Filtra ojotas, chinelas, medias, botines de fútbol y accesorios no deseados si se cuelan."""
    text = f"{product_name} {category_text}".lower()
    excluded = (
        "ojota",
        "chinela",
        "sandalia",
        "slide",
        "victori one",
        "offcourt",
        "media ",
        "medias ",
        "plantilla",
        "cordones",
        "bolso",
        "mochila",
    )
    return not any(word in text for word in excluded)
