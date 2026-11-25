"""Notificaciones diarias con las zapatillas nuevas o reingresos del día."""

from __future__ import annotations

import os
import platform
import subprocess
from typing import Any

import httpx


def _format_ars(price: float) -> str:
    return f"${price:,.0f}".replace(",", ".")


def build_summary_text(
    new_items: list[dict[str, Any]],
    restock_items: list[dict[str, Any]],
    total_catalog: int,
    app_url: str,
) -> tuple[str, str]:
    """Construye título y cuerpo compacto para push/Telegram/macOS."""
    total_updates = len(new_items) + len(restock_items)
    if total_updates == 0:
        title = "Zapatillas 47.5 / 14 US — Sin novedades hoy"
        body = f"Catálogo actualizado: {total_catalog} modelos disponibles en tu talle."
        return title, body

    title = f"Zapatillas 47.5 / 14 US: {len(new_items)} nuevas y {len(restock_items)} reingresos"
    lines: list[str] = []
    for item in (new_items + restock_items)[:8]:
        tag = "NUEVA" if item.get("badge") == "NUEVO_HOY" else "REINGRESO"
        lines.append(
            f"• [{tag}] {item['name']} — {_format_ars(item['price'])} ({item['store_name']})"
        )
    if total_updates > 8:
        lines.append(f"... y {total_updates - 8} modelos más en la app.")
    if app_url:
        lines.append(f"\nVer catálogo completo: {app_url}")
    return title, "\n".join(lines)


def send_notifications(
    new_items: list[dict[str, Any]],
    restock_items: list[dict[str, Any]],
    total_catalog: int,
) -> None:
    """
    Envía notificación diaria por los canales configurados mediante variables de entorno:
    - NTFY_TOPIC (push gratis a celular y Mac vía ntfy.sh)
    - TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID
    - Notificación nativa de macOS (cuando corre en local)
    """
    app_url = os.getenv("APP_URL", "").strip()
    notify_even_if_empty = os.getenv("NOTIFY_IF_EMPTY", "false").lower() == "true"

    if not new_items and not restock_items and not notify_even_if_empty:
        print("[notify] Sin novedades hoy; no se dispara alerta push.")
        return

    title, body = build_summary_text(new_items, restock_items, total_catalog, app_url)

    # 1. Push instantáneo vía ntfy.sh (iOS, Android, Mac, Web — 100% gratis)
    ntfy_topic = os.getenv("NTFY_TOPIC", "").strip()
    if ntfy_topic:
        try:
            headers = {"Title": title.encode("utf-8"), "Priority": "default", "Tags": "shoe"}
            if app_url:
                headers["Click"] = app_url
            httpx.post(f"https://ntfy.sh/{ntfy_topic}", content=body.encode("utf-8"), headers=headers, timeout=15.0)
            print(f"[notify] Push enviado a ntfy.sh/{ntfy_topic}")
        except Exception as exc:
            print(f"[notify] Error enviando a ntfy.sh: {exc}")

    # 2. Telegram Bot
    tg_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    tg_chat = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if tg_token and tg_chat:
        try:
            httpx.post(
                f"https://api.telegram.org/bot{tg_token}/sendMessage",
                json={"chat_id": tg_chat, "text": f"{title}\n\n{body}", "disable_web_page_preview": True},
                timeout=15.0,
            )
            print("[notify] Mensaje enviado por Telegram.")
        except Exception as exc:
            print(f"[notify] Error enviando a Telegram: {exc}")

    # 3. Notificación nativa de macOS (solo en ejecución local)
    if platform.system() == "Darwin" and not os.getenv("CI"):
        try:
            safe_title = title.replace('"', "'")
            safe_body = body.splitlines()[0].replace('"', "'")
            subprocess.run(
                ["osascript", "-e", f'display notification "{safe_body}" with title "{safe_title}"'],
                check=False,
            )
        except Exception:
            pass
