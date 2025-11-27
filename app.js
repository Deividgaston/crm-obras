// Modo Desarrollador Eficiente: código directo, una sola lectura inicial a Firestore

// ======= ESTADO EN MEMORIA =======
let proyectos = [];          // lista completa desde Firestore
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

// ======= CARGA INICIAL (ÚNICA LECTURA A FIRESTORE) =======
async function cargarProyectosInicial() {
  const tbody = document.getElementById("projects-table-body");
  if (tbody) {
    tbody.innerHTML =
      '<tr><td colspan="10" class="muted">Cargando...</td></tr>';
  }

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
    if (tbody) {
      tbody.innerHTML =
        '<tr><td colspan="10" class="muted error">Error cargando datos</td></tr>';
    }
  }
}

// ======= FILTROS =======
function aplicarFiltros() {
  const search = (document.getElementById("filter-search")?.value || "")
    .toLowerCase()
    .trim();
  const estado = document.getElementById("filter-estado")?.value || "";
  const prioridad = document.getElementById("filter-prioridad")?.value || "";

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

  if (!tbody) return;

  if (selectAll) selectAll.checked = false;

  if (!proyectosFiltrados.length) {
    tbody.innerHTML =
      '<tr><td colspan="10" class="muted">No hay proyectos con estos filtros.</td></tr>';
    if (countLabel) countLabel.textContent = "0 proyectos";
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
  if (countLabel) {
    countLabel.textContent = `${proyectosFiltrados.length} proyecto(s)`;
  }

  // Doble click en fila: editar
  tbody.querySelectorAll("tr").forEach((tr) => {
    tr.addEventListener("dblclick", () => {
      const id = tr.dataset.id;
      const proyecto = proyectos.find((p) => p.id === id);
      if (proyecto) abrirModalProyecto(proyecto);
    });
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

  const kpiTotal = document.getElementById("kpi-total");
  const kpiSeg = document.getElementById("kpi-seguimiento");
  const kpiGan = document.getElementById("kpi-ganados");
  const kpiPot = document.getElementById("kpi-potencial");
  const kpiSub = document.getElementById("kpi-total-sub");

  if (kpiTotal) kpiTotal.textContent = total;
  if (kpiSeg) kpiSeg.textContent = seguimiento;
  if (kpiGan) kpiGan.textContent = ganados;
  if (kpiPot) kpiPot.textContent = formatNumber(potencialTotal);
  if (kpiSub) {
    kpiSub.textContent = `${ganados} ganados · ${seguimiento} en seguimiento`;
  }

  // Últimos proyectos
  const tbody = document.getElementById("panel-last-projects-body");
  if (tbody) {
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
  }

  // Acciones (seguimientos + tareas)
  const acciones = buildAccionesFromProyectos(proyectos);
  const { atras, hoyArr, prox } = particionarAcciones(acciones);
  renderAccionesPanel(acciones, atras, hoyArr, prox);
}

// Construye lista de acciones desde los proyectos
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

    // Tareas (si existe lista "tareas")
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

// Pinta bloque de acciones en el panel
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
        const desc = a.descripcion
          ? `<div class="accion-desc">${a.descripcion}</div>`
          : "";
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

// ======= GUARDAR PROYECTO (SIN RECARGAR FIRESTORE) =======
async function guardarProyectoDesdeFormulario() {
  const id = document.getElementById("project-id").value || null;
  const nombre_obra = document
    .getElementById("field-nombre_obra")
    .value.trim();

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
      // UPDATE EN FIRESTORE
      await db.collection("proyectos").doc(id).update(payload);
      // UPDATE EN MEMORIA
      const idx = proyectos.findIndex((p) => p.id === id);
      if (idx !== -1) {
        proyectos[idx] = { ...proyectos[idx], ...payload };
      }
    } else {
      // CREATE EN FIRESTORE
      const docRef = await db.collection("proyectos").add({
        ...payload,
        created_at: firebase.firestore.FieldValue.serverTimestamp(),
      });
      // AÑADIR AL ARRAY LOCAL (sin nueva lectura)
      proyectos.push({
        id: docRef.id,
        ...payload,
        created_at: new Date(),
      });
    }

    document.getElementById("project-modal").classList.add("hidden");

    // Recalcular filtros y panel sin volver a leer de Firestore
    aplicarFiltros();
    actualizarPanel();
  } catch (err) {
    console.error("Error guardando proyecto:", err);
    alert("Error guardando el proyecto. Revisa la consola.");
  }
}

// ======= BORRADO (SIN RECARGAR FIRESTORE) =======
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
    const ids = [];
    cbs.forEach((cb) => {
      const id = cb.dataset.id;
      ids.push(id);
      const ref = db.collection("proyectos").doc(id);
      batch.delete(ref);
    });
    await batch.commit();

    // Eliminar del array local SIN recargar
    const idSet = new Set(ids);
    proyectos = proyectos.filter((p) => !idSet.has(p.id));

    aplicarFiltros();
    actualizarPanel();
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
  const search = document.getElementById("filter-search");
  const estado = document.getElementById("filter-estado");
  const prioridad = document.getElementById("filter-prioridad");

  if (search) search.addEventListener("input", aplicarFiltros);
  if (estado) estado.addEventListener("change", aplicarFiltros);
  if (prioridad) prioridad.addEventListener("change", aplicarFiltros);

  // Botones
  const btnAdd = document.getElementById("btn-add-project");
  const btnDel = document.getElementById("btn-delete-selected");
  const btnEdit = document.getElementById("btn-edit-selected");

  if (btnAdd) btnAdd.addEventListener("click", () => abrirModalProyecto(null));
  if (btnDel) btnDel.addEventListener("click", borrarSeleccionados);
  if (btnEdit) btnEdit.addEventListener("click", editarSeleccionado);

  // Seleccionar todo
  const selectAll = document.getElementById("select-all-projects");
  if (selectAll) {
    selectAll.addEventListener("change", () => {
      const checked = selectAll.checked;
      document
        .querySelectorAll(".project-checkbox")
        .forEach((cb) => (cb.checked = checked));
    });
  }
}

// ======= INIT =======
document.addEventListener("DOMContentLoaded", () => {
  setupNavigation();
  setupModalProyecto();
  setupEventos();
  cargarProyectosInicial(); // única lectura global a Firestore
});
