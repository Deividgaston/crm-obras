// Modo Desarrollador Eficiente: código directo, sin florituras

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

function formatDate(iso) {
  if (!iso) return "—";
  try {
    const d = typeof iso === "string" ? new Date(iso) : iso.toDate?.() ?? iso;
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return `${day}/${month}/${year}`;
  } catch {
    return "—";
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

// ======= RENDER TABLA =======
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

// ======= PANEL =======
function actualizarPanel() {
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

  const tbody = document.getElementById("panel-last-projects-body");
  if (!proyectos.length) {
    tbody.innerHTML =
      '<tr><td colspan="5" class="muted">Sin proyectos todavía.</td></tr>';
    return;
  }

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
        ? formatDateForInput(proyecto.fecha_seguimiento)
        : ""
    );
    setVal("field-notas_seguimiento", proyecto.notas_seguimiento || "");
    setVal(
      "field-tarea_fecha",
      proyecto.tarea_fecha ? formatDateForInput(proyecto.tarea_fecha) : ""
    );
    setVal("field-tarea_comentario", proyecto.tarea_comentario || "");
  } else {
    const today = new Date().toISOString().slice(0, 10);
    document.getElementById("field-fecha_seguimiento").value = today;
  }

  modal.classList.remove("hidden");
}

function formatDateForInput(value) {
  try {
    const d =
      typeof value === "string"
        ? new Date(value)
        : value.toDate?.() ?? new Date(value);
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
    tarea_fecha:
      document.getElementById("field-tarea_fecha").value || null,
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

  if (!confirm(`¿Borrar ${cbs.length} proyecto(s)? Esta acción no se puede deshacer.`)) {
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
