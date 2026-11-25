# Monitor de Zapatillas — Talle 47.5 AR / 14 US / 32 cm

Aplicación web consolidada que monitorea diariamente a las **12:00 hs (Argentina)** las 15 tiendas de tu Google Sheet **Lista de sitios web Zapatillas**, muestra únicamente los modelos disponibles en tus marcas y talles, marca automáticamente los ingresos como **NUEVO HOY** o **REINGRESO**, y te envía una notificación diaria con las novedades.

## Cómo ponerla online gratis (recomendado — sin instalar nada en tu Mac)

La forma más simple y 100% gratuita es usar **GitHub Pages + GitHub Actions**: la app queda accesible desde tu Mac y celular con una URL propia y se actualiza sola todos los días a las 12:00 hs Argentina.

1. **Creá un repositorio en GitHub** (puede ser privado o público; para GitHub Pages gratis en cuenta free conviene público) y subí el contenido de esta carpeta.
2. **Habilitá GitHub Pages:** en el repositorio andá a **Settings → Pages → Build and deployment → Source: GitHub Actions**.
3. **Conectá tu Google Sheet para futuras tiendas:** en tu planilla **Lista de sitios web Zapatillas**, hacé clic en **Compartir → Cualquier persona con el enlace (Lector)**. Cada vez que agregues una fila nueva en la planilla, la app la incorpora automáticamente en la próxima corrida de las 12:00 hs.
4. **Activá las notificaciones diarias (elegí la opción que prefieras):**
   - **Opción más simple (push al celular y Mac con ntfy.sh — 0 cuentas):** instalá la app gratuita **ntfy** en tu celular, suscribite a un canal privado con un nombre difícil de adivinar (por ejemplo `zapas-475-santi-9283`), y en GitHub andá a **Settings → Secrets and variables → Actions → New repository secret**:
     - `NTFY_TOPIC` = `zapas-475-santi-9283`
   - **Opción Telegram:** cargá los secrets `TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID`.
   - *(Opcional)* En **Variables**, agregá `APP_URL` con la URL de tu GitHub Pages para que al tocar la notificación se abra directo el catálogo.
5. **Ejecutá la primera corrida manual:** andá a la pestaña **Actions → Actualización diaria de zapatillas (12:00 ART) → Run workflow**. En ~1 minuto tu catálogo ya estará online.

## Cómo probarla en tu Mac (opcional)

Si también querés correr el scraper en local:

```bash
# 1. Instalar herramientas de Python (si aún no las tenés)
xcode-select --install

# 2. Instalar dependencias y correr el scraper
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m scraper.run

# 3. Abrir la app web local
python -m http.server 8000 --directory web
# Abrí http://localhost:8000 en tu navegador
```

## Estructura del proyecto

- `scraper/sheets_sync.py`: sincroniza automáticamente las tiendas desde tu Google Sheet (con respaldo local en `scraper/stores_defaults.py`).
- `scraper/sizes.py`: normaliza talles (`47,5`, `47.5`, `14`, `14 US`, `32 cm`, `47.5(14us-32cm)`) y marcas por tienda.
- `scraper/adapters/`: adaptadores modulares para **VTEX** (8 tiendas), **Digital Sport** (3 tiendas), **SFCC/Demandware** (2 tiendas), **Magento** (Solo Urbano) y **TiendaNube** (Drifters).
- `scraper/run.py`: ejecuta el barrido diario, compara con `web/data/history.json`, etiqueta `NUEVO_HOY` / `REINGRESO` / `BAJÓ DE PRECIO` y genera `web/data/catalog.json`.
- `scraper/notify.py`: envía la notificación diaria con los modelos nuevos del día.
- `web/`: aplicación web estática (HTML/CSS/JS) con tarjetas de producto, filtros y CTA directo a cada tienda.
- `.github/workflows/daily-update.yml`: automatización diaria a las 12:00 hs ART (15:00 UTC) + publicación en GitHub Pages.
