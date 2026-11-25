"""Configuración base de las 15 tiendas y vínculo con el Google Sheet consolidado."""

from __future__ import annotations

GOOGLE_SHEET_ID = "1N4dcWUyGMFaQoEc11MqkssHpMsRdoEbx-sAXgRcV7Es"
GOOGLE_SHEET_CSV_URL = (
    f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/export?format=csv"
)
TIMEZONE = "America/Argentina/Buenos_Aires"

GENERIC_SIZES = {
    "ar": ["47,5", "47.5"],
    "us": ["14", "14 US", "US 14", "14.0"],
    "cm": ["32", "32 cm", "32cm"],
}

DEFAULT_STORES = [
    {
        "id": "nike-ar",
        "name": "Nike Argentina",
        "url": "https://www.nike.com.ar/hombre/calzado",
        "platform": "vtex",
        "size": "14",
        "brands": ["Nike"],
    },
    {
        "id": "newsport",
        "name": "NewSport",
        "url": "https://www.newsport.com.ar/newsport/calzado/",
        "platform": "vtex",
        "size": "47,5",
        "brands": ["Nike", "Jordan"],
    },
    {
        "id": "new-balance",
        "name": "New Balance",
        "url": "https://www.newbalance.com.ar/hombre/zapatillas/ver-todo/",
        "platform": "sfcc",
        "size": "14",
        "brands": ["New Balance"],
    },
    {
        "id": "fuencarral",
        "name": "Fuencarral",
        "url": "https://www.tiendafuencarral.com.ar/tienda-fuencarral/calzado/",
        "platform": "vtex",
        "size": "47,5",
        "brands": ["Nike", "Jordan"],
    },
    {
        "id": "cero26",
        "name": "Cero 26",
        "url": "https://www.cero26.com.ar/cero26/calzado/",
        "platform": "vtex",
        "size": "47,5",
        "brands": ["Nike", "Jordan"],
    },
    {
        "id": "sport78",
        "name": "Digital Sport 78",
        "url": "https://www.digitalsport.com.ar/sport78/",
        "platform": "digitalsport",
        "size": "47.5",
        "brands": ["Nike"],
    },
    {
        "id": "fluid",
        "name": "Fluid",
        "url": "https://www.digitalsport.com.ar/fluid/",
        "platform": "digitalsport",
        "size": "47.5",
        "brands": ["Nike"],
    },
    {
        "id": "dionysos",
        "name": "Dionysos",
        "url": "https://www.digitalsport.com.ar/dionysos",
        "platform": "digitalsport",
        "size": "47.5",
        "brands": ["Nike"],
    },
    {
        "id": "dash",
        "name": "Dash",
        "url": "https://www.dashdeportes.com.ar/calzado/",
        "platform": "vtex",
        "size": "47.5",
        "brands": ["Nike", "Nike sportswear", "Jordan"],
    },
    {
        "id": "sporting",
        "name": "Sporting",
        "url": "https://www.sporting.com.ar/sporting/calzado/",
        "platform": "vtex",
        "size": "47.5",
        "brands": ["Nike"],
    },
    {
        "id": "solo-urbano",
        "name": "Solo Urbano",
        "url": "https://www.solourbano.com/hombre/calzado.html",
        "platform": "magento",
        "size": "47.5",
        "brands": ["Nike"],
    },
    {
        "id": "stock-center",
        "name": "Stock Center",
        "url": "https://www.stockcenter.com.ar/hombre/calzado",
        "platform": "sfcc",
        "size": "47.5",
        "brands": ["Nike"],
    },
    {
        "id": "on-sports",
        "name": "On Sports",
        "url": "https://www.onsports.com.ar/calzado",
        "platform": "vtex",
        "size": "47,5",
        "brands": ["Nike"],
    },
    {
        "id": "drifters",
        "name": "Drifters",
        "url": "https://drifters.com.ar/calzado/",
        "platform": "tiendanube",
        "size": "47.5(14us-32cm)",
        "brands": ["Nike Sb"],
    },
    {
        "id": "grid",
        "name": "Grid",
        "url": "https://www.grid.com.ar/calzado",
        "platform": "vtex",
        "size": "47.5",
        "brands": ["Nike"],
    },
]
