const state = {
  products: [],
  stores: [],
  brand: "ALL",
  store: "ALL",
  search: "",
  onlyNew: false,
  sort: "new",
};

const fmtARS = (value) =>
  new Intl.NumberFormat("es-AR", {
    style: "currency",
    currency: "ARS",
    maximumFractionDigits: 0,
  }).format(value);

const escapeHtml = (str = "") =>
  str
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");

function renderBadges(p) {
  const list = [];
  if (p.badge === "NUEVO_HOY") {
    list.push('<span class="badge badge-new">NUEVO HOY</span>');
  } else if (p.badge === "REINGRESO") {
    list.push('<span class="badge badge-restock">REINGRESO</span>');
  }
  if (p.price_drop) {
    list.push('<span class="badge badge-drop">BAJÓ DE PRECIO</span>');
  }
  if (p.list_price && p.list_price > p.price) {
    const pct = Math.round(((p.list_price - p.price) / p.list_price) * 100);
    if (pct >= 5) {
      list.push(`<span class="badge badge-off">-${pct}%</span>`);
    }
  }
  return list.join("");
}

function getFilteredProducts() {
  const q = state.search.trim().toLowerCase();
  const filtered = state.products.filter((p) => {
    if (state.onlyNew && !p.badge) return false;
    if (state.store !== "ALL" && p.store_id !== state.store) return false;
    if (state.brand !== "ALL") {
      const b = (p.brand || "").toLowerCase();
      const n = (p.name || "").toLowerCase();
      const target = state.brand.toLowerCase();
      if (target === "nike sb") {
        if (!b.includes("sb") && !n.includes(" sb")) return false;
      } else if (!b.includes(target) && !n.includes(target)) {
        return false;
      }
    }
    if (q && !`${p.name} ${p.brand} ${p.store_name}`.toLowerCase().includes(q)) {
      return false;
    }
    return true;
  });

  const badgeOrder = { NUEVO_HOY: 0, REINGRESO: 1 };
  filtered.sort((a, b) => {
    if (state.sort === "price_asc") return a.price - b.price;
    if (state.sort === "price_desc") return b.price - a.price;
    if (state.sort === "name_asc") return a.name.localeCompare(b.name, "es");
    const ra = badgeOrder[a.badge] ?? 2;
    const rb = badgeOrder[b.badge] ?? 2;
    if (ra !== rb) return ra - rb;
    return a.price - b.price;
  });

  return filtered;
}

function renderCatalog() {
  const grid = document.getElementById("product-grid");
  const empty = document.getElementById("empty-state");
  const countEl = document.getElementById("results-count");
  const resetBtn = document.getElementById("btn-reset");

  const items = getFilteredProducts();
  const hasFilters =
    state.brand !== "ALL" || state.store !== "ALL" || state.search.trim() !== "" || state.onlyNew;

  resetBtn.classList.toggle("hidden", !hasFilters);
  countEl.textContent = `Mostrando ${items.length} de ${state.products.length} modelos disponibles en talle 47.5 AR / 14 US`;

  if (items.length === 0) {
    grid.innerHTML = "";
    empty.classList.remove("hidden");
    return;
  }

  empty.classList.add("hidden");
  grid.innerHTML = items
    .map((p) => {
      const imgSrc = p.image || "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='320' height='240'%3E%3Crect width='100%25' height='100%25' fill='%23f3f4f6'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' fill='%239ca3af' font-family='sans-serif' font-size='14'%3ESin imagen%3C/text%3E%3C/svg%3E";
      const listPriceHtml =
        p.list_price && p.list_price > p.price
          ? `<span class="price-list">${fmtARS(p.list_price)}</span>`
          : "";

      return `
        <article class="card">
          <div class="card-media">
            <div class="badges">${renderBadges(p)}</div>
            <img src="${escapeHtml(imgSrc)}" alt="${escapeHtml(p.name)}" loading="lazy" />
          </div>
          <div class="card-body">
            <div class="card-meta">
              <span class="store-pill">${escapeHtml(p.store_name)}</span>
              <span>${escapeHtml(p.brand)}</span>
            </div>
            <h2 class="card-title">${escapeHtml(p.name)}</h2>
            <div class="price-row">
              <span class="price-main">${fmtARS(p.price)}</span>
              ${listPriceHtml}
            </div>
            <div class="stock-row">
              <span class="size-tag">Talle: ${escapeHtml(p.size_label)}</span>
              <span>${escapeHtml(p.stock_text || "En stock")}</span>
            </div>
            <a class="cta-btn" href="${escapeHtml(p.url)}" target="_blank" rel="noopener noreferrer">
              Ver en ${escapeHtml(p.store_name)} ↗
            </a>
          </div>
        </article>
      `;
    })
    .join("");
}

function renderStoresPanel() {
  const select = document.getElementById("store-select");
  const wrap = document.getElementById("stores-table-wrap");

  select.innerHTML =
    `<option value="ALL">Todas las tiendas (${state.stores.length})</option>` +
    state.stores
      .map(
        (s) =>
          `<option value="${escapeHtml(s.id)}">${escapeHtml(s.name)} (${s.count})</option>`
      )
      .join("");

  wrap.innerHTML = state.stores
    .map(
      (s) => `
      <div class="store-status-card">
        <strong>${escapeHtml(s.name)}</strong>
        <div>Talle: ${escapeHtml(s.size)} · ${(s.brands || []).join(", ")}</div>
        <div class="${s.status === "ok" ? "status-ok" : "status-err"}">
          ${s.status === "ok" ? `OK · ${s.count} modelos` : `Error: ${escapeHtml(s.error || "revisar")}`}
        </div>
      </div>
    `
    )
    .join("");
}

function bindEvents() {
  document.getElementById("search-input").addEventListener("input", (e) => {
    state.search = e.target.value;
    renderCatalog();
  });

  document.querySelectorAll("#brand-chips .chip").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("#brand-chips .chip").forEach((c) => c.classList.remove("active"));
      btn.classList.add("active");
      state.brand = btn.dataset.brand;
      renderCatalog();
    });
  });

  document.getElementById("store-select").addEventListener("change", (e) => {
    state.store = e.target.value;
    renderCatalog();
  });

  document.getElementById("sort-select").addEventListener("change", (e) => {
    state.sort = e.target.value;
    renderCatalog();
  });

  const onlyNewCheckbox = document.getElementById("only-new-checkbox");
  onlyNewCheckbox.addEventListener("change", (e) => {
    state.onlyNew = e.target.checked;
    renderCatalog();
  });

  document.getElementById("btn-only-new").addEventListener("click", () => {
    state.onlyNew = !state.onlyNew;
    onlyNewCheckbox.checked = state.onlyNew;
    document.getElementById("btn-only-new").textContent = state.onlyNew
      ? "Ver todo el catálogo"
      : "Ver solo nuevas de hoy";
    renderCatalog();
  });

  document.getElementById("btn-reset").addEventListener("click", () => {
    state.brand = "ALL";
    state.store = "ALL";
    state.search = "";
    state.onlyNew = false;
    document.getElementById("search-input").value = "";
    document.getElementById("store-select").value = "ALL";
    onlyNewCheckbox.checked = false;
    document.querySelectorAll("#brand-chips .chip").forEach((c, idx) => {
      c.classList.toggle("active", idx === 0);
    });
    renderCatalog();
  });
}

async function init() {
  bindEvents();
  try {
    const resp = await fetch("data/catalog.json", { cache: "no-store" });
    if (!resp.ok) throw new Error("No se encontró data/catalog.json");
    const data = await resp.json();

    state.products = data.products || [];
    state.stores = data.stores || [];

    document.getElementById("updated-label").textContent = `Última actualización: ${data.updated_label || "Pendiente de primera corrida"}`;
    if (data.google_sheet_url) {
      document.getElementById("sheet-link").href = data.google_sheet_url;
    }

    const s = data.summary || {};
    document.getElementById("kpi-total").textContent = s.total_products ?? state.products.length;
    document.getElementById("kpi-new").textContent = s.new_today ?? 0;
    document.getElementById("kpi-restock").textContent = s.restocks_today ?? 0;
    document.getElementById("kpi-stores").textContent = `${s.stores_ok ?? 0}/${s.stores_total ?? state.stores.length}`;

    const updatesToday = (s.new_today ?? 0) + (s.restocks_today ?? 0);
    if (updatesToday > 0) {
      const banner = document.getElementById("new-banner");
      banner.classList.remove("hidden");
      document.getElementById("new-banner-title").textContent =
        `Hoy entraron ${s.new_today ?? 0} modelos nuevos y ${s.restocks_today ?? 0} reingresos en tu talle`;
    }

    renderStoresPanel();
    renderCatalog();
  } catch (err) {
    document.getElementById("updated-label").textContent =
      "Aún no se ejecutó la primera actualización de catálogo.";
    document.getElementById("empty-state").classList.remove("hidden");
    document.getElementById("empty-title").textContent = "Catálogo inicial pendiente";
    document.getElementById("empty-desc").textContent =
      "Ejecutá `python3 -m scraper.run` o activá el workflow diario en GitHub Actions para cargar los modelos en vivo.";
  }
}

init();
