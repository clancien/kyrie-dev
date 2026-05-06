const DATA_FILES = {
  selector: "./data/selector_productos_server_latest.json",
  saldos: "./data/saldos_server_latest.json",
  tarjetas: "./data/tarjetas_server_latest.json",
  movimientos: "./data/movimientos_server_latest.json",
  movimientosApi: "./data/movimientos_api_server_latest.json",
};

const metricsEl = document.getElementById("metrics");
const accountsEl = document.getElementById("accounts");
const movementsByAccountEl = document.getElementById("movementsByAccount");
const cardsEl = document.getElementById("cards");
const rawJsonEl = document.getElementById("rawJson");
const reloadBtn = document.getElementById("reloadBtn");
const movementsSearchEl = document.getElementById("movementsSearch");
const movementsMonthEl = document.getElementById("movementsMonth");
const movementsTypeEl = document.getElementById("movementsType");
let selectedKey = null;
let currentMovementsContext = null;

const toMoney = (n) => {
  const num = Number(n);
  if (Number.isNaN(num)) return String(n ?? "-");
  return new Intl.NumberFormat("es-CL", { style: "currency", currency: "CLP", maximumFractionDigits: 0 }).format(num);
};

const el = (tag, className, text) => {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
};

const clear = (...nodes) => nodes.forEach((n) => (n.innerHTML = ""));

const formatDateISO = (raw) => {
  const txt = String(raw || "").trim();
  const m = txt.match(/^(\d{4})(\d{2})(\d{2})/);
  if (m) return `${m[1]}-${m[2]}-${m[3]}`;
  const m2 = txt.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (m2) return `${m2[1]}-${m2[2]}-${m2[3]}`;
  return txt || "-";
};

const formatTimeHHMM = (raw) => {
  const txt = String(raw || "").trim();
  const m = txt.match(/^\d{8}\s+(\d{2}):(\d{2})/);
  if (m) return `${m[1]}:${m[2]}`;
  const m2 = txt.match(/^\d{4}-\d{2}-\d{2}[T\s](\d{2}):(\d{2})/);
  if (m2) return `${m2[1]}:${m2[2]}`;
  return "-";
};

const movementDate = (m) => m.fecha || m.fechaMovimiento || m.fechaContable || "";
const movementMonth = (m) => {
  const iso = formatDateISO(movementDate(m));
  return /^\d{4}-\d{2}-\d{2}$/.test(iso) ? iso.slice(0, 7) : "";
};
const toNumberSafe = (v) => {
  if (v === undefined || v === null || v === "") return 0;
  if (typeof v === "number") return Number.isFinite(v) ? v : 0;
  const s = String(v).trim();
  if (!s) return 0;
  const normalized = s.replace(/[^\d,-]/g, "").replace(/\./g, "").replace(",", ".");
  const n = Number(normalized);
  return Number.isFinite(n) ? n : 0;
};

function renderMetrics(data) {
  const cardsCount = Array.isArray(data?.api_raw?.tarjetas)
    ? data.api_raw.tarjetas.length
    : Array.isArray(data?.api_raw?.selector_productos?.productos)
      ? data.api_raw.selector_productos.productos.filter((p) => p?.tipo === "tarjeta").length
      : 0;

  const items = [
    ["Cuentas detectadas", data.accounts_count ?? 0],
    ["Cuentas consultadas", data.accounts_queried_count ?? 0],
    ["Movimientos totales", data?.derived?.movimientos_total ?? 0],
    ["Tarjetas", cardsCount],
  ];

  clear(metricsEl);
  items.forEach(([label, value]) => {
    const card = el("article", "metric");
    card.append(el("div", "label", label));
    card.append(el("div", "value", String(value)));
    metricsEl.append(card);
  });
}

function table(headers, rows, opts = {}) {
  if (!rows?.length) return el("div", "empty", "Sin datos para mostrar.");

  const wrap = el("div", "table-wrap");
  const t = el("table");
  const thead = el("thead");
  const trh = el("tr");
  const numericColumns = new Set(opts.numericColumns || []);
  headers.forEach((h, idx) => {
    const th = el("th", "", h);
    if (numericColumns.has(idx)) th.classList.add("ta-right");
    trh.append(th);
  });
  thead.append(trh);

  const tbody = el("tbody");
  rows.forEach((row, idx) => {
    const tr = el("tr");
    if (opts.isRowSelected?.(row, idx)) tr.classList.add("row-selected");
    if (opts.onRowClick) {
      tr.classList.add("row-clickable");
      tr.addEventListener("click", () => opts.onRowClick(row, idx));
    }
    row.forEach((cell, colIdx) => {
      const td = el("td", "", cell ?? "-");
      if (numericColumns.has(colIdx)) td.classList.add("ta-right");
      tr.append(td);
    });
    tbody.append(tr);
  });

  t.append(thead, tbody);
  wrap.append(t);
  return wrap;
}

function renderMovementsPlaceholder() {
  currentMovementsContext = null;
  if (movementsSearchEl) movementsSearchEl.value = "";
  if (movementsMonthEl) movementsMonthEl.value = "";
  if (movementsTypeEl) movementsTypeEl.value = "";
  clear(movementsByAccountEl);
  movementsByAccountEl.append(el("div", "empty", "Selecciona una cuenta o tarjeta para ver los últimos movimientos."));
}

function renderMovementsRows(title, movimientos) {
  currentMovementsContext = { title, movimientos: Array.isArray(movimientos) ? movimientos : [] };
  if (movementsSearchEl) movementsSearchEl.value = "";
  if (movementsTypeEl) movementsTypeEl.value = "";
  if (movementsMonthEl) {
    const months = [...new Set(currentMovementsContext.movimientos.map(movementMonth).filter(Boolean))].sort().reverse();
    movementsMonthEl.innerHTML = "";
    const allOpt = document.createElement("option");
    allOpt.value = "";
    allOpt.textContent = "Todos los meses";
    movementsMonthEl.append(allOpt);
    months.forEach((month) => {
      const opt = document.createElement("option");
      opt.value = month;
      opt.textContent = month;
      movementsMonthEl.append(opt);
    });
    movementsMonthEl.value = "";
  }
  renderMovementsFromCurrent();
}

function renderMovementsFromCurrent() {
  if (!currentMovementsContext) {
    renderMovementsPlaceholder();
    return;
  }

  clear(movementsByAccountEl);
  const block = el("section", "account-block");
  block.append(el("h3", "account-title", currentMovementsContext.title));
  const searchText = (movementsSearchEl?.value || "").trim().toLowerCase();
  const selectedMonth = (movementsMonthEl?.value || "").trim();
  const selectedType = (movementsTypeEl?.value || "").trim().toLowerCase();

  const filtered = currentMovementsContext.movimientos.filter((m) => {
    if (selectedMonth && movementMonth(m) !== selectedMonth) return false;
    if (selectedType) {
      const tipo = String(m?.tipo || "").toLowerCase();
      if (tipo !== selectedType) return false;
    }
    if (searchText) {
      const full = JSON.stringify(m ?? {}).toLowerCase();
      if (!full.includes(searchText)) return false;
    }
    return true;
  });

  if (!filtered.length) {
    block.append(el("div", "empty", "Sin movimientos para mostrar."));
    movementsByAccountEl.append(block);
    return;
  }

  const extractOrigen = (m) => {
    const detalle = Array.isArray(m?.detalleGlosa) ? m.detalleGlosa : [];
    let rut = "";
    for (const line of detalle) {
      if (typeof line !== "string") continue;
      const [rawKey, ...rest] = line.split(":");
      const key = (rawKey || "").trim().toLowerCase();
      const value = rest.join(":").trim();
      if (!value) continue;
      if (key === "rut origen") rut = value;
    }
    return rut || "-";
  };

  const extractComentario = (m) => {
    const detalle = Array.isArray(m?.detalleGlosa) ? m.detalleGlosa : [];
    for (const line of detalle) {
      if (typeof line !== "string") continue;
      const [rawKey, ...rest] = line.split(":");
      const key = (rawKey || "").trim().toLowerCase();
      const value = rest.join(":").trim();
      if (key === "comentario" && value) return value;
    }
    return "-";
  };

  let cargoTotal = 0;
  let abonoTotal = 0;
  const rows = filtered.slice(0, 100).map((m) => {
    const tipo = String(m?.tipo || "").toLowerCase();
    const montoRaw = m.monto !== undefined ? m.monto : m.importe;
    const montoFmt = montoRaw !== undefined ? toMoney(montoRaw) : "-";
    const esAbono = tipo === "abono";
    const esCargo = tipo === "cargo";
    const montoNum = toNumberSafe(montoRaw);
    if (esCargo) cargoTotal += montoNum;
    if (esAbono) abonoTotal += montoNum;
    const fechaRaw = movementDate(m);
    return [
      formatDateISO(fechaRaw),
      formatTimeHHMM(fechaRaw),
      m.descripcion || m.glosa || m.detalle || "-",
      esAbono ? extractOrigen(m) : "-",
      esAbono ? extractComentario(m) : "-",
      esCargo ? montoFmt : "-",
      esAbono ? montoFmt : "-",
      m.saldo !== undefined ? toMoney(m.saldo) : "-",
    ];
  });
  rows.push([
    "",
    "",
    "TOTAL",
    "",
    "",
    toMoney(cargoTotal),
    toMoney(abonoTotal),
    "",
  ]);
  block.append(table(["Fecha", "Hora", "Descripción", "Origen", "Comentario", "Cargo", "Abono", "Saldo"], rows, {
    numericColumns: [5, 6, 7],
  }));
  movementsByAccountEl.append(block);
}

function showAccountMovements(data, account) {
  const groups = data?.derived?.movimientos_by_account ?? [];
  const group = groups.find((g) => {
    const acc = g?.account || {};
    if (acc.numero && account.numero && String(acc.numero) === String(account.numero)) return true;
    if (acc.mascara && account.mascara && String(acc.mascara) === String(account.mascara)) return true;
    return false;
  });
  const title = `Últimos movimientos · ${account.labelProducto || account.codigoProducto || "Cuenta"} ${account.numero || account.mascara || ""}`.trim();
  renderMovementsRows(title, group?.movimientos || []);
}

function showCardMovements(data, card) {
  const cardMovs = card?.movimientos || card?.ultimosMovimientos || [];
  const title = `Últimos movimientos · Tarjeta ${card.numero || card.mascara || ""}`.trim();
  renderMovementsRows(title, Array.isArray(cardMovs) ? cardMovs : []);
}

function renderAccounts(data) {
  const accounts = data.accounts_queried ?? [];
  const saldosRaw = Array.isArray(data?.api_raw?.saldos) ? data.api_raw.saldos : [];
  const saldoByKey = new Map(
    saldosRaw
      .filter((s) => s && (s.numero !== undefined || s.codProducto !== undefined))
      .map((s) => [`${String(s.codProducto || "")}:${String(s.numero || "")}`, s])
  );

  const rows = accounts.map((a, idx) => [
    a.numero,
    a.labelProducto || "-",
    a.codigoProducto,
    a.claseCuenta || "-",
    a.moneda,
    (() => {
      const saldo = saldoByKey.get(`${String(a.codigoProducto || "")}:${String(a.numero || "")}`);
      return saldo?.cupo !== undefined ? toMoney(saldo.cupo) : "-";
    })(),
    (() => {
      const saldo = saldoByKey.get(`${String(a.codigoProducto || "")}:${String(a.numero || "")}`);
      return saldo?.disponible !== undefined ? toMoney(saldo.disponible) : "-";
    })(),
  ]);
  clear(accountsEl);
  accountsEl.append(table(["Número", "Tipo", "Código", "Clase", "Moneda", "Saldo", "Disponible"], rows, {
    numericColumns: [5, 6],
    isRowSelected: (_, idx) => selectedKey === `account:${idx}`,
    onRowClick: (_, idx) => {
      selectedKey = `account:${idx}`;
      renderAccounts(data);
      renderCards(data);
      showAccountMovements(data, accounts[idx]);
    },
  }));
}

function renderCards(data) {
  const selector = data?.api_raw?.selector_productos?.productos ?? [];
  const selectorCards = selector.filter((p) => p?.tipo === "tarjeta");
  const selectorById = new Map(selectorCards.map((c) => [c.id, c]));
  const apiCards = Array.isArray(data?.api_raw?.tarjetas) ? data.api_raw.tarjetas : [];

  const pickFromCard = (card, keys) => {
    for (const k of keys) {
      if (card?.[k] !== undefined && card?.[k] !== null) return card[k];
    }
    const cupos = Array.isArray(card?.cupos) ? card.cupos : [];
    for (const cupo of cupos) {
      for (const k of keys) {
        if (cupo?.[k] !== undefined && cupo?.[k] !== null) return cupo[k];
      }
      const lineas = Array.isArray(cupo?.lineas) ? cupo.lineas : [];
      for (const linea of lineas) {
        for (const k of keys) {
          if (linea?.[k] !== undefined && linea?.[k] !== null) return linea[k];
        }
      }
    }
    return null;
  };

  const formatMoneyMaybe = (v) => (v === undefined || v === null || v === "" ? "-" : toMoney(v));

  const cardsData = (apiCards.length ? apiCards : selectorCards);
  const rows = cardsData.map((card) => {
    const sel = selectorById.get(card?.idProducto) || {};
    const saldo = pickFromCard(card, ["saldo", "saldoActual", "saldoFinal", "saldoTotal", "montoUtilizado"]);
    const disponible = pickFromCard(card, ["disponible", "montoDisponible", "saldoDisponible", "cupoDisponible"]);
    return [
      sel.codigo || card.codigo || "-",
      sel.mascara || card.numero || "-",
      sel.label || `${card.marca || ""} ${card.tipo || ""}`.trim() || "-",
      sel.detalleEstado || sel.estado || (card.titular === true ? "Titular" : card.titular === false ? "Adicional" : "-"),
      sel.tipoCliente || "-",
      formatMoneyMaybe(saldo),
      formatMoneyMaybe(disponible),
    ];
  });

  clear(cardsEl);
  cardsEl.append(table(["Código", "Máscara", "Tarjeta", "Estado", "Cliente", "Saldo", "Disponible"], rows, {
    numericColumns: [5, 6],
    isRowSelected: (_, idx) => selectedKey === `card:${idx}`,
    onRowClick: (_, idx) => {
      selectedKey = `card:${idx}`;
      renderAccounts(data);
      renderCards(data);
      showCardMovements(data, cardsData[idx]);
    },
  }));
}

async function loadData() {
  const ts = Date.now();
  const fetchJson = async (url, required = true) => {
    const res = await fetch(`${url}?ts=${ts}`);
    if (!res.ok) {
      if (!required) return null;
      throw new Error(`No se pudo cargar ${url}`);
    }
    return res.json();
  };

  const selectorResp = await fetchJson(DATA_FILES.selector, true);
  const saldosResp = await fetchJson(DATA_FILES.saldos, false);
  const tarjetasResp = await fetchJson(DATA_FILES.tarjetas, false);
  const movimientosResp = await fetchJson(DATA_FILES.movimientos, true);
  const movimientosApiResp = await fetchJson(DATA_FILES.movimientosApi, false);

  const selectorRaw = selectorResp?.raw || {};
  const saldosRaw = saldosResp?.raw ?? null;
  const tarjetasRaw = Array.isArray(tarjetasResp?.raw) ? tarjetasResp.raw : [];
  const productos = Array.isArray(selectorRaw?.productos) ? selectorRaw.productos : [];
  const rut = selectorRaw?.rut || "";
  const nombre = selectorRaw?.nombre || "";

  const accountsRaw = productos
    .filter((p) => {
      const numero = String(p?.numero || "").trim();
      const codigo = String(p?.codigo || "").trim();
      const tipo = String(p?.tipo || "").toLowerCase();
      return Boolean(numero) && (codigo === "CTD" || tipo.includes("cuenta") || tipo.includes("linea"));
    })
    .map((p) => ({
      nombreCliente: nombre,
      rutCliente: rut,
      numero: p.numero,
      mascara: p.mascara || (p.numero ? `****${String(p.numero).slice(-4)}` : ""),
      selected: p.codigo === "CTD",
      codigoProducto: p.codigo || "",
      claseCuenta: p.claseCuenta || (p.codigo === "CTD" ? "CCNMN1" : ""),
      moneda: p.codigoMoneda || "CLP",
      tipoProducto: p.tipo || "",
      labelProducto: p.label || "",
    }));

  // Duplicados de productos pueden venir con el mismo numero; conservar solo la primera ocurrencia.
  const seenAccountNumbers = new Set();
  const accounts = accountsRaw.filter((a) => {
    const n = String(a?.numero || "").trim();
    if (!n || seenAccountNumbers.has(n)) return false;
    seenAccountNumbers.add(n);
    return true;
  });

  return {
    ok: true,
    mode: movimientosResp?.mode || "web_joined",
    accounts_count: accounts.length,
    accounts_queried_count: accounts.length,
    accounts_queried: accounts,
    api_raw: {
      selector_productos: selectorRaw,
      saldos: saldosRaw,
      tarjetas: tarjetasRaw,
      movimientos_pages: movimientosApiResp?.raw_pages || movimientosResp?.movimientos_pages_raw || [],
    },
    derived: {
      movimientos_total: movimientosResp?.movimientos_total ?? 0,
      movimientos: movimientosResp?.movimientos || [],
      movimientos_by_account: movimientosResp?.movimientos_by_account || [],
    },
    source_files: DATA_FILES,
  };
}

async function render() {
  try {
    const data = await loadData();
    selectedKey = null;
    renderMetrics(data);
    renderAccounts(data);
    renderCards(data);
    renderMovementsPlaceholder();
    rawJsonEl.textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    clear(metricsEl, accountsEl, movementsByAccountEl, cardsEl);
    metricsEl.append(el("div", "empty", `Error cargando datos: ${err.message}. Ejecuta run.sh para regenerar JSON en output/.`));
    rawJsonEl.textContent = "";
  }
}

reloadBtn.addEventListener("click", render);
if (movementsSearchEl) {
  movementsSearchEl.addEventListener("input", () => {
    if (!currentMovementsContext) return;
    renderMovementsFromCurrent();
  });
}
if (movementsMonthEl) {
  movementsMonthEl.addEventListener("change", () => {
    if (!currentMovementsContext) return;
    renderMovementsFromCurrent();
  });
}
if (movementsTypeEl) {
  movementsTypeEl.addEventListener("change", () => {
    if (!currentMovementsContext) return;
    renderMovementsFromCurrent();
  });
}
render();
