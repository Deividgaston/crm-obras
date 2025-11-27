// app.js
// =======================
// CRM Obras 2N - Panel
// =======================
"use strict";

// 1) CONFIGURACIÓN FIREBASE (tus datos)
const firebaseConfig = {
  apiKey: "AIzaSyB51403DF43zxqq4K3Ex65i5-Sqm-EkiTY",
  authDomain: "crm-obras-2n.firebaseapp.com",
  projectId: "crm-obras-2n",
  storageBucket: "crm-obras-2n.firebasestorage.app",
  messagingSenderId: "545667121262",
  appId: "1:545667121262:web:9dd55a09bc7a7bb3e9a67f",
};

// 2) INICIALIZAR FIREBASE (compat)
firebase.initializeApp(firebaseConfig);
const db = firebase.firestore();

// 3) UTILIDADES BÁSICAS
const $ = (sel) => document.querySelector(sel);

function formatDate(value) {
  if (!value) return "";
  let d = value;
  if (value.toDate) d = value.toDate(); // Firestore Timestamp
  if (!(d instanceof Date)) d = new Date(d);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleDateString("es-ES", { day: "2-digit", month: "2-digit", year: "numeric" });
}

function showToast(msg, type = "error") {
  const toast = $("#toast");
  if (!toast) {
    console[type === "error" ? "error" : "log"](msg);
    return;
  }
  toast.textContent = msg;
  toast.className = `toast toast--${type}`;
  toast.style.opacity = "1";
  setTimeout(() => {
    toast.style.opacity = "0";
  }, 3500);
}

function setLoading(isLoading) {
  const loader = $("#panel-loading");
  if (loader) loader.style.display = isLoading ? "flex" : "none";
}

// 4) CARGA PRINCIPAL DEL PANEL
async function loadPanelData() {
  setLoading(true);
  try {
    // UNA sola lectura de la colección
    const snap = await db.collection("proyectos").get();

    const proyectos = snap.docs.map((doc) => ({
      id: doc.id,
      ...doc.data(),
    }));

    renderSummary(proyectos);
    renderTable(proyectos);
  } catch (err) {
    console.error(err);
    showToast("Error al cargar los datos del panel", "error");
  } finally {
    setLoading(false);
  }
}

// 5) CALCULAR ACCIONES (tareas + seguimientos)
function getAccionesFromProyecto(p) {
  const acciones = [];
  const {
    Proyecto,
    ciudad,
    seguimiento_fecha,
    seguimiento_comentario,
    tarea_fecha,
    tarea_comentario,
  } = p;

  if (tarea_fecha) {
    acciones.push({
      tipo: "Tarea",
      proyecto: Proyecto || "(Sin nombre)",
      fecha: tarea_fecha,
      comentario: tarea_comentario || "",
    });
  }

  if (seguimiento_fecha) {
    acciones.push({
      tipo: "Seguimiento",
      proyecto: Proyecto || "(Sin nombre)",
      fecha: seguimiento_fecha,
      comentario: seguimiento_comentario || "",
    });
  }

  return acciones;
}

// 6) RESUMEN (tarjetas + listas)
function renderSummary(proyectos) {
  const hoy = new Date();
  hoy.setHours(0, 0, 0, 0);
  const hoyEnd = new Date(hoy);
  hoyEnd.setHours(23, 59, 59, 999);

  const in7 = new Date(hoy);
  in7.setDate(in7.getDate() + 7);
  in7.setHours(23, 59, 59, 999);

  const todasAcciones = proyectos.flatMap(getAccionesFromProyecto);

  const retrasadas = [];
  const hoyAcciones = [];
  const proximas = [];

  todasAcciones.forEach((a) => {
    let fecha = a.fecha;
    if (fecha?.toDate) fecha = fecha.toDate();
    fecha = new Date(fecha);
    if (Number.isNaN(fecha.getTime())) return;

    if (fecha < hoy) {
      retrasadas.push({ ...a, fecha });
    } else if (fecha >= hoy && fecha <= hoyEnd) {
      hoyAcciones.push({ ...a, fecha });
    } else if (fecha > hoyEnd && fecha <= in7) {
      proximas.push({ ...a, fecha });
    }
  });

  // Tarjetas
  const total = todasAcciones.length;
  if ($("#stat-total")) $("#stat-total").textContent = total.toString();
  if ($("#stat-retrasadas")) $("#stat-retrasadas").textContent = retrasadas.length.toString();
  if ($("#stat-hoy")) $("#stat-hoy").textContent = hoyAcciones.length.toString();
  if ($("#stat-prox7")) $("#stat-prox7").textContent = proximas.length.toString();

  // Listas
  renderAccionList("#list-retrasadas", retrasadas);
  renderAccionList("#list-hoy", hoyAcciones);
  renderAccionList("#list-prox7", proximas);
}

function renderAccionList(selector, acciones) {
  const container = $(selector);
  if (!container) return;

  if (!acciones.length) {
    container.innerHTML = `<div class="crm-empty">Sin acciones.</div>`;
    return;
  }

  acciones
    .sort((a, b) => a.fecha - b.fecha)
    .slice(0, 20)
    .forEach((a) => {
      const div = document.createElement("div");
      div.className = "crm-card crm-card--action";
      div.innerHTML = `
        <div class="crm-card__header">
          <span class="crm-chip">${a.tipo}</span>
          <span class="crm-card__date">${formatDate(a.fecha)}</span>
        </div>
        <div class="crm-card__title">${a.proyecto}</div>
        <div class="crm-card__body">${a.comentario || "Sin comentario"}</div>
      `;
      container.appendChild(div);
    });
}

// 7) TABLA PRINCIPAL DEL PANEL
function renderTable(proyectos) {
  const tbody = $("#panel-table-body");
  if (!tbody) return;

  tbody.innerHTML = "";

  // Ordenar por fecha de próxima acción (tarea o seguimiento)
  const withNextDate = proyectos.map((p) => {
    let fechas = [];
    if (p.tarea_fecha) fechas.push(p.tarea_fecha);
    if (p.seguimiento_fecha) fechas.push(p.seguimiento_fecha);
    let nextDate = null;
    if (fechas.length) {
      fechas = fechas.map((f) => (f.toDate ? f.toDate() : new Date(f)));
      nextDate = fechas.sort((a, b) => a - b)[0];
    }
    return { ...p, nextDate };
  });

  withNextDate
    .sort((a, b) => {
      if (!a.nextDate && !b.nextDate) return 0;
      if (!a.nextDate) return 1;
      if (!b.nextDate) return -1;
      return a.nextDate - b.nextDate;
    })
    .forEach((p) => {
      const tr = document.createElement("tr");
      tr.dataset.id = p.id;

      tr.innerHTML = `
        <td class="col-proyecto">${p.Proyecto || "(Sin nombre)"}</td>
        <td>${p.ciudad || ""}</td>
        <td>${p.provincia || ""}</td>
        <td>${p.fase_proyecto || ""}</td>
        <td>${formatDate(p.tarea_fecha)}</td>
        <td>${p.tarea_comentario || ""}</td>
        <td>${formatDate(p.seguimiento_fecha)}</td>
        <td>${p.seguimiento_comentario || ""}</td>
      `;

      tbody.appendChild(tr);
    });

  // (Opcional) click en fila para mostrar detalles rápidos en consola
  tbody.addEventListener("click", (ev) => {
    const row = ev.target.closest("tr");
    if (!row) return;
    const id = row.dataset.id;
    if (!id) return;
    console.log("Fila seleccionada (solo lectura por ahora):", id);
  });
}

// 8) EVENTOS INICIALES
document.addEventListener("DOMContentLoaded", () => {
  // Botón refrescar (si existe)
  const btnRefresh = $("#btn-panel-refresh");
  if (btnRefresh) {
    btnRefresh.addEventListener("click", () => loadPanelData());
  }

  // Cargar al entrar en la página
  loadPanelData();
});
