// Modo Desarrollador Eficiente: código directo

// ======= ESTADO EN MEMORIA =======
let proyectos = []; // lista completa desde Firestore
let proyectosFiltrados = []; // tras filtros

// ======= UTILIDADES =======
function formatNumber(num) {
  if (num == null || isNaN(num)) return "0";
  return num.toLocaleString("es-ES", {
    maximumFractionDigits: 0,
  });
}

function formatDate(value) {
  if (!value) return "—";
  try {
    let d;
    if (value instanceof Date) {
      d = value;
    } else if (value && typeof value.toDate === "function") {
      d = value.toDate();
    } else {
      d = new Date(value);
    }
    if (isNaN(d.getTime())) return "—";
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return `${day}/${month}/${year}`;
  } catch {
    return "—";
  }
}

function formatDateFromDate(d) {
  if (!(d instanceof Date) || isNaN(d.getTime())) return "—";
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${day}/${month}/${year}`;
}

function parseDateField(value) {
  if (!value) return null;
  try {
    if (value instanceof Date) return value;
    if (value && typeof value.toDate === "function") return value.toDate();
    const d = new Date(value);
    if (isNaN(d.getTime())) return null;
    return d;
  } catch {
    return null;
  }
}

// ======= NAVEGACIÓN =======
function setupNavigation() {
  const navButtons = document.querySelectorAll(".nav-btn");
  navButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      navButtons.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");

      const sectionName = btn.dataset.section;
      document
        .querySelectorAll(".section")
        .forEach((s) => s.classList.remove("active"));
      document
        .getElementById(`section-${sectionName}`)
        .classList.add("active");
    });
  });
}

// ======= CARGA INICIAL =======
async function cargarProyectos() {
  const tbody = document.getElementById("projects-table-body");
  tbody.innerHTML =
    '<tr><td colspan="10" class="muted">Cargando...</td></tr>';

  try {
    const snapshot = await db
      .collection("proyectos")
      .orderBy("nombre_obra", "asc")
      .get();

    proyectos = snapshot.docs.map((doc) => ({
      id: doc.id,
      ...doc.data(),
    }));

    aplicarFiltros();
    actualizarPanel();
  } catch (err) {
    console.error("Error cargando proyectos:", err);
    tbody.innerHTML =
      '<tr><td colspan="10" class="muted error">Error cargando datos</td></tr>';
  }
}

// ======= FILTROS =======
function aplicarFiltros() {
  const search = document
    .getElementById("filter-search")
    .value.toLowerCase()
    .trim();
  const estado = document.getElementById("filter-estado").value;
  const prioridad = document.getElementById("filter-prioridad").value;

  proyectosFiltrados = proyectos.filter((p) => {
    if (estado && p.estado !== estado) return false;
    if (prioridad && p.prioridad !== prioridad) return false;

    if (search) {
      const texto =
        `${p.nombre_obra || ""} ${p.cliente_principal || ""} ${
          p.ciudad || ""
        }`.toLowerCase();
      if (!texto.includes(search)) return false;
    }

    return true;
  });

  renderProyectosTabla();
}

// ======= RENDER TABLA PROYECTOS =======
function renderProyectosTabla() {
  const tbody = document.getElementById("projects-table-body");
  const countLabel = document.getElementById("projects-count-label");
  const selectAll = document.getElementById("select-all-projects");
  selectAll.checked = false;

  if (!proyectosFiltrados.length) {
    tbody.innerHTML =
      '<tr><td colspan="10" class="muted">No hay proyectos con estos filtros.</td></tr>';
    countLabel.textContent = "0 proyectos";
    return;
  }

  const rowsHtml = proyectosFiltrados
    .map((p) => {
      return `
      <tr data-id="${p.id}">
        <td class="checkbox-col">
          <input type="checkbox" class="project-checkbox" data-id="${p.id}" />
        </td>
        <td>${p.nombre_obra || "—"}</td>
        <td>${p.cliente_principal || "—"}</td>
        <td>${p.ciudad || "—"}</td>
        <td>${p.provincia || "—"}</td>
        <td>${p.estado || "—"}</td>
        <td>${p.prioridad || "—"}</td>
        <td>${p.tipo || "—"}</td>
        <td class="numeric">${formatNumber(p.potencial_eur)}</td>
        <td>${formatDate(p.fecha_seguimiento)}</td>
      </tr>
    `;
    })
    .join("");

  tbody.innerHTML = rowsHtml;
  countLabel.textContent = `${proyectosFiltrados.length} proyecto(s)`;

  // Doble click en fila: editar
  tbody.querySelectorAll("tr").forEach((tr) => {
    tr.addEventListener("dblclick", () => {
      const id = tr.dataset.id;
      const proyecto = proyectos.find((p) => p.id === id);
      if (proyecto) abrirModalProyecto(proyecto);
    });
  });

  // Seleccionar todo
  selectAll.addEventListener("change", () => {
    const checked = selectAll.checked;
    document
      .querySelectorAll(".project-checkbox")
      .forEach((cb) => (cb.checked = checked));
  });
}

// ======= PANEL: KPIs + ÚLTIMOS PROYECTOS + ACCIONES =======
function actualizarPanel() {
  // KPIs por proyectos
  const total = proyectos.length;
  const seguimiento = proyectos.filter((p) => p.estado !== "Detectado").length;
  const ganados = proyectos.filter((p) => p.estado === "Ganado").length;
  const potencialTotal = proyectos.reduce(
    (acc, p) => acc + (Number(p.potencial_eur) || 0),
    0
  );

  document.getElementById("kpi-total").textContent = total;
  document.getElementById("kpi-seguimiento").textContent = seguimiento;
  document.getElementById("kpi-ganados").textContent = ganados;
  document.getElementById("kpi-potencial").textContent =
    formatNumber(potencialTotal);
  document.getElementById(
    "kpi-total-sub"
  ).textContent = `${ganados} ganados · ${seguimiento} en seguimiento`;

  // Últimos proyectos
  const tbody = document.getElementById("panel-last-projects-body");
  if (!proyectos.length) {
    tbody.innerHTML =
      '<tr><td colspan="5" class="muted">Sin proyectos todavía.</td></tr>';
  } else {
    const ultimos = [...proyectos]
      .sort((a, b) => {
        const da = a.created_at?.toMillis?.() ?? 0;
        const db = b.created_at?.toMillis?.() ?? 0;
        return db - da;
      })
      .slice(0, 5);

    tbody.innerHTML = ultimos
      .map(
        (p) => `
      <tr>
        <td>${p.nombre_obra || "—"}</td>
        <td>${p.cliente_principal || "—"}</td>
        <td>${p.ciudad || "—"}</td>
        <td>${p.estado || "—"}</td>
        <td class="numeric">${formatNumber(p.potencial_eur)}</td>
      </tr>
    `
      )
      .join("");
  }

  // Acciones (como en el panel de Streamlit): Seguimientos + Tareas próximas
  const acciones = buildAccionesFromProyectos(proyectos);
  const { atras, hoyArr, prox } = particionarAcciones(acciones);
  renderAccionesPanel(acciones, atras, hoyArr, prox);
}

// Construye lista de acciones desde los proyectos
// - Seguimiento: fecha_seguimiento + notas_seguimiento
// - Tareas: array "tareas" con campos {completado, fecha_limite, tipo, titulo}
function buildAccionesFromProyectos(lista) {
  const acciones = [];

  lista.forEach((p) => {
    const nombre = p.nombre_obra || "Sin nombre";
    const cliente = p.cliente_principal || "—";
    const ciudad = p.ciudad || "—";
    const estado = p.estado || "Detectado";

    // Seguimiento
    const fSeg = parseDateField(p.fecha_seguimiento);
    if (fSeg) {
      acciones.push({
        tipo: "Seguimiento",
        fechaDate: fSeg,
        proyecto: nombre,
        cliente,
        ciudad,
        estado,
        descripcion: p.notas_seguimiento || "",
      });
    }

    // Tareas (si existe lista "tareas" como en la versión Python)
    const tareas = Array.isArray(p.tareas) ? p.tareas : [];
    tareas.forEach((t) => {
      if (!t || typeof t !== "object" || t.completado) return;
      const fT = parseDateField(t.fecha_limite);
      if (!fT) return;
      acciones.push({
        tipo: t.tipo || "Tarea",
        fechaDate: fT,
        proyecto: nombre,
        cliente,
        ciudad,
        estado,
        descripcion: t.titulo || "",
      });
    });
  });

  acciones.sort((a, b) => a.fechaDate - b.fechaDate);
  return acciones;
}

// Particiona acciones en retrasadas / hoy / próximos 7 días
function particionarAcciones(acciones) {
  const now = new Date();
  const hoy = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const en7 = new Date(hoy);
  en7.setDate(en7.getDate() + 7);

  const atras = [];
  const hoyArr = [];
  const prox = [];

  acciones.forEach((a) => {
    const d = a.fechaDate;
    if (!(d instanceof Date)) return;
    const d0 = new Date(d.getFullYear(), d.getMonth(), d.getDate());
    if (d0 < hoy) atras.push(a);
    else if (d0.getTime() === hoy.getTime()) hoyArr.push(a);
    else if (d0 <= en7) prox.push(a);
  });

  return { atras, hoyArr, prox };
}

// Pinta bloque de acciones en el panel usando solo DOM (sin tocar HTML base)
function renderAccionesPanel(acciones, atras, hoyArr, prox) {
  const panelSection = document.getElementById("section-panel");
  if (!panelSection) return;

  let card = document.getElementById("panel-actions-card");
  if (!card) {
    card = document.createElement("div");
    card.id = "panel-actions-card";
    card.className = "card";
    panelSection.appendChild(card);
  }

  const renderLista = (lista) => {
    if (!lista.length) {
      return `<div class="muted" style="font-size:0.75rem;margin-top:0.2rem;">Sin acciones.</div>`;
    }
    return lista
      .map((a) => {
        const fecha = formatDateFromDate(a.fechaDate);
        const desc = a.descripcion ? `<div class="accion-desc">${a.descripcion}</div>` : "";
        return `
        <div class="accion-card" style="margin-bottom:4px;padding:6px 8px;border-radius:0.35rem;border:1px solid #e5e7eb;background:#ffffff;">
          <div class="accion-meta" style="font-size:0.72rem;color:#6b7280;">
            ${fecha} · <strong>${a.tipo}</strong>
          </div>
          <div class="accion-title" style="font-size:0.82rem;font-weight:600;color:#032d60;">
            ${a.proyecto}
          </div>
          <div class="accion-sub" style="font-size:0.72rem;color:#6b7280;">
            ${a.cliente} · ${a.ciudad} · ${a.estado}
          </div>
          ${desc}
        </div>
      `;
      })
      .join("");
  };

  card.innerHTML = `
    <div class="card-header">
      <h2>Acciones próximas</h2>
    </div>
    <div style="display:flex;flex-wrap:wrap;gap:0.5rem;margin-top:0.2rem;margin-bottom:0.3rem;">
      <div style="min-width:90px;">
        <div style="font-size:0.75rem;color:#6b7280;">Acciones</div>
        <div style="font-size:1rem;font-weight:700;color:#111827;">${acciones.length}</div>
      </div>
      <div style="min-width:90px;">
        <div style="font-size:0.75rem;color:#6b7280;">Retrasadas</div>
        <div style="font-size:1rem;font-weight:700;color:#b91c1c;">${atras.length}</div>
      </div>
      <div style="min-width:90px;">
        <div style="font-size:0.75rem;color:#6b7280;">Hoy</div>
        <div style="font-size:1rem;font-weight:700;color:#065f46;">${hoyArr.length}</div>
      </div>
      <div style="min-width:110px;">
        <div style="font-size:0.75rem;color:#6b7280;">Próx. 7 días</div>
        <div style="font-size:1rem;font-weight:700;color:#0369a1;">${prox.length}</div>
      </div>
    </div>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:0.6rem;margin-top:0.2rem;">
      <div>
        <div style="font-size:0.78rem;font-weight:600;color:#032d60;margin-bottom:0.2rem;">📌 Retrasadas</div>
        ${renderLista(atras)}
      </div>
      <div>
        <div style="font-size:0.78rem;font-weight:600;color:#032d60;margin-bottom:0.2rem;">📅 Hoy</div>
        ${renderLista(hoyArr)}
      </div>
      <div>
        <div style="font-size:0.78rem;font-weight:600;color:#032d60;margin-bottom:0.2rem;">🔜 Próx. 7 días</div>
        ${renderLista(prox)}
      </div>
    </div>
  `;
}

// ======= MODAL PROYECTO =======
function setupModalProyecto() {
  const modal = document.getElementById("project-modal");
  const closeBtn = document.getElementById("project-modal-close");
  const cancelBtn = document.getElementById("project-modal-cancel");
  const backdrop = modal.querySelector(".modal-backdrop");
  const form = document.getElementById("project-form");

  function closeModal() {
    modal.classList.add("hidden");
    form.reset();
    document.getElementById("project-id").value = "";
  }

  closeBtn.addEventListener("click", closeModal);
  cancelBtn.addEventListener("click", closeModal);
  backdrop.addEventListener("click", closeModal);

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    await guardarProyectoDesdeFormulario();
  });
}

function abrirModalProyecto(proyecto = null) {
  const modal = document.getElementById("project-modal");
  const title = document.getElementById("project-modal-title");
  const form = document.getElementById("project-form");

  form.reset();
  document.getElementById("project-id").value = proyecto ? proyecto.id : "";
  title.textContent = proyecto ? "Editar proyecto" : "Nuevo proyecto";

  const setVal = (id, value) => {
    const el = document.getElementById(id);
    if (!el) return;
    el.value = value != null ? value : "";
  };

  if (proyecto) {
    setVal("field-nombre_obra", proyecto.nombre_obra);
    setVal("field-cliente_principal", proyecto.cliente_principal);
    setVal("field-ciudad", proyecto.ciudad);
    setVal("field-provincia", proyecto.provincia);
    setVal("field-tipo", proyecto.tipo || "Residencial lujo");
    setVal("field-estado", proyecto.estado || "Detectado");
    setVal("field-prioridad", proyecto.prioridad || "Media");
    setVal("field-potencial_eur", proyecto.potencial_eur || "");
    setVal(
      "field-fecha_seguimiento",
      proyecto.fecha_seguimiento
        ? formatDateInputValue(proyecto.fecha_seguimiento)
        : ""
    );
    setVal("field-notas_seguimiento", proyecto.notas_seguimiento || "");
    setVal(
      "field-tarea_fecha",
      proyecto.tarea_fecha ? formatDateInputValue(proyecto.tarea_fecha) : ""
    );
    setVal("field-tarea_comentario", proyecto.tarea_comentario || "");
  } else {
    const today = new Date().toISOString().slice(0, 10);
    document.getElementById("field-fecha_seguimiento").value = today;
  }

  modal.classList.remove("hidden");
}

function formatDateInputValue(value) {
  try {
    const d =
      value instanceof Date
        ? value
        : value && typeof value.toDate === "function"
        ? value.toDate()
        : new Date(value);
    if (isNaN(d.getTime())) return "";
    return d.toISOString().slice(0, 10);
  } catch {
    return "";
  }
}

async function guardarProyectoDesdeFormulario() {
  const id = document.getElementById("project-id").value || null;
  const nombre_obra = document.getElementById("field-nombre_obra").value.trim();

  if (!nombre_obra) {
    alert("El nombre del proyecto es obligatorio.");
    return;
  }

  const payload = {
    nombre_obra,
    cliente_principal:
      document.getElementById("field-cliente_principal").value.trim() || null,
    ciudad: document.getElementById("field-ciudad").value.trim() || null,
    provincia: document.getElementById("field-provincia").value.trim() || null,
    tipo: document.getElementById("field-tipo").value || "Residencial lujo",
    estado: document.getElementById("field-estado").value || "Detectado",
    prioridad: document.getElementById("field-prioridad").value || "Media",
    potencial_eur: Number(
      document.getElementById("field-potencial_eur").value || 0
    ),
    fecha_seguimiento:
      document.getElementById("field-fecha_seguimiento").value || null,
    notas_seguimiento:
      document.getElementById("field-notas_seguimiento").value.trim() || null,
    tarea_fecha: document.getElementById("field-tarea_fecha").value || null,
    tarea_comentario:
      document.getElementById("field-tarea_comentario").value.trim() || null,
  };

  try {
    if (id) {
      await db.collection("proyectos").doc(id).update(payload);
    } else {
      await db.collection("proyectos").add({
        ...payload,
        created_at: firebase.firestore.FieldValue.serverTimestamp(),
      });
    }
    document.getElementById("project-modal").classList.add("hidden");
    await cargarProyectos();
  } catch (err) {
    console.error("Error guardando proyecto:", err);
    alert("Error guardando el proyecto. Revisa la consola.");
  }
}

// ======= BORRADO =======
async function borrarSeleccionados() {
  const cbs = Array.from(
    document.querySelectorAll(".project-checkbox:checked")
  );
  if (!cbs.length) {
    alert("Selecciona al menos un proyecto.");
    return;
  }

  if (
    !confirm(
      `¿Borrar ${cbs.length} proyecto(s)? Esta acción no se puede deshacer.`
    )
  ) {
    return;
  }

  try {
    const batch = db.batch();
    cbs.forEach((cb) => {
      const id = cb.dataset.id;
      const ref = db.collection("proyectos").doc(id);
      batch.delete(ref);
    });
    await batch.commit();
    await cargarProyectos();
  } catch (err) {
    console.error("Error borrando proyectos:", err);
    alert("Error borrando proyectos. Revisa la consola.");
  }
}

// ======= EDICIÓN SELECCIONADO =======
function editarSeleccionado() {
  const cbs = Array.from(
    document.querySelectorAll(".project-checkbox:checked")
  );
  if (!cbs.length) {
    alert("Selecciona un proyecto.");
    return;
  }
  if (cbs.length > 1) {
    alert("Solo puedes editar un proyecto a la vez.");
    return;
  }
  const id = cbs[0].dataset.id;
  const proyecto = proyectos.find((p) => p.id === id);
  if (!proyecto) {
    alert("No se ha encontrado el proyecto.");
    return;
  }
  abrirModalProyecto(proyecto);
}

// ======= LISTENERS =======
function setupEventos() {
  // Filtros
  document
    .getElementById("filter-search")
    .addEventListener("input", aplicarFiltros);
  document
    .getElementById("filter-estado")
    .addEventListener("change", aplicarFiltros);
  document
    .getElementById("filter-prioridad")
    .addEventListener("change", aplicarFiltros);

  // Botones
  document
    .getElementById("btn-add-project")
    .addEventListener("click", () => abrirModalProyecto(null));
  document
    .getElementById("btn-delete-selected")
    .addEventListener("click", borrarSeleccionados);
  document
    .getElementById("btn-edit-selected")
    .addEventListener("click", editarSeleccionado);
}

// ======= INIT =======
document.addEventListener("DOMContentLoaded", () => {
  setupNavigation();
  setupModalProyecto();
  setupEventos();
  cargarProyectos();
});
