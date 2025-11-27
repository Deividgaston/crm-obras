// Estado global
let proyectos = [];
let proyectosFiltrados = [];

// Utils
function formatNumber(num) {
  if (num == null || isNaN(num)) return "0";
  return Number(num).toLocaleString("es-ES", { maximumFractionDigits: 0 });
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

function formatDate(value) {
  const d = parseDateField(value);
  if (!d) return "—";
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${day}/${m}/${y}`;
}

function formatDateInput(value) {
  const d = parseDateField(value);
  if (!d) return "";
  return d.toISOString().slice(0, 10);
}

// Navegación
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

// Carga inicial (una sola lectura)
async function cargarProyectosInicial() {
  const tbody = document.getElementById("projects-table-body");
  if (tbody) {
    tbody.innerHTML =
      '<tr><td colspan="8" class="muted">Cargando...</td></tr>';
  }

  try {
    const snapshot = await db
      .collection("proyectos")
      .orderBy("Fase_proyecto", "asc")
      .orderBy("Proyecto", "asc")
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
        '<tr><td colspan="8" class="muted error">Error cargando datos</td></tr>';
    }
  }
}

// Filtros
function aplicarFiltros() {
  const search = (document.getElementById("filter-search")?.value || "")
    .toLowerCase()
    .trim();
  const fase = document.getElementById("filter-fase")?.value || "";
  const segmento = document.getElementById("filter-segmento")?.value || "";

  proyectosFiltrados = proyectos.filter((p) => {
    if (fase && p.Fase_proyecto !== fase) return false;
    if (segmento && p.Segmento !== segmento) return false;

    if (search) {
      const txt = (
        (p.Proyecto || "") +
        " " +
        (p.Ciudad || "") +
        " " +
        (p.Promotora_Fondo || "") +
        " " +
        (p.Arquitectura || "") +
        " " +
        (p.Ingenieria || "")
      )
        .toLowerCase()
        .trim();
      if (!txt.includes(search)) return false;
    }

    return true;
  });

  renderProyectosTabla();
}

// Render tabla de proyectos
function renderProyectosTabla() {
  const tbody = document.getElementById("projects-table-body");
  const countLabel = document.getElementById("projects-count-label");
  const selectAll = document.getElementById("select-all-projects");

  if (!tbody) return;

  if (selectAll) selectAll.checked = false;

  if (!proyectosFiltrados.length) {
    tbody.innerHTML =
      '<tr><td colspan="8" class="muted">No hay proyectos con estos filtros.</td></tr>';
    if (countLabel) countLabel.textContent = "0 proyectos";
    return;
  }

  const rowsHtml = proyectosFiltrados
    .map((p) => {
      const fase = p.Fase_proyecto || p.estado || "—";
      const potencial = p.Potencial_2N ?? p.potencial_eur ?? 0;
      return `
        <tr data-id="${p.id}">
          <td class="checkbox-col">
            <input type="checkbox" class="project-checkbox" data-id="${p.id}" />
          </td>
          <td>${p.Proyecto || "—"}</td>
          <td>${p.Ciudad || "—"}</td>
          <td>${p.Segmento || "—"}</td>
          <td>${fase}</td>
          <td>${p.Promotora_Fondo || "—"}</td>
          <td>${formatDate(p.Fecha_Inicio_Estimada)}</td>
          <td class="numeric">${formatNumber(potencial)}</td>
        </tr>
      `;
    })
    .join("");

  tbody.innerHTML = rowsHtml;
  if (countLabel) {
    countLabel.textContent = `${proyectosFiltrados.length} proyecto(s)`;
  }

  // Doble click para editar
  tbody.querySelectorAll("tr").forEach((tr) => {
    tr.addEventListener("dblclick", () => {
      const id = tr.dataset.id;
      const proyecto = proyectos.find((p) => p.id === id);
      if (proyecto) abrirModalProyecto(proyecto);
    });
  });
}

// Panel (KPIs + últimos + acciones)
function actualizarPanel() {
  const total = proyectos.length;
  const seguimiento = proyectos.filter(
    (p) => (p.Fase_proyecto || p.estado || "") !== "Detectado"
  ).length;
  const avanzados = proyectos.filter((p) =>
    ["Construcción", "Entregado"].includes(p.Fase_proyecto || p.estado || "")
  ).length;
  const potencialTotal = proyectos.reduce((acc, p) => {
    const val = p.Potencial_2N ?? p.potencial_eur ?? 0;
    return acc + (Number(val) || 0);
  }, 0);

  const kpiTotal = document.getElementById("kpi-total");
  const kpiSeg = document.getElementById("kpi-seguimiento");
  const kpiGan = document.getElementById("kpi-ganados");
  const kpiPot = document.getElementById("kpi-potencial");
  const kpiSub = document.getElementById("kpi-total-sub");

  if (kpiTotal) kpiTotal.textContent = total;
  if (kpiSeg) kpiSeg.textContent = seguimiento;
  if (kpiGan) kpiGan.textContent = avanzados;
  if (kpiPot) kpiPot.textContent = formatNumber(potencialTotal);
  if (kpiSub) {
    kpiSub.textContent = `${avanzados} avanzados · ${seguimiento} en seguimiento`;
  }

  // Últimos proyectos (por created_at si existe)
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
        .map((p) => {
          const fase = p.Fase_proyecto || p.estado || "—";
          const potencial = p.Potencial_2N ?? p.potencial_eur ?? 0;
          return `
            <tr>
              <td>${p.Proyecto || "—"}</td>
              <td>${p.Ciudad || "—"}</td>
              <td>${p.Segmento || "—"}</td>
              <td>${fase}</td>
              <td class="numeric">${formatNumber(potencial)}</td>
            </tr>
          `;
        })
        .join("");
    }
  }

  const acciones = buildAccionesFromProyectos(proyectos);
  const { atras, hoyArr, prox } = particionarAcciones(acciones);
  renderAccionesPanel(acciones, atras, hoyArr, prox);
}

// Acciones próximas desde seguimiento + tarea
function buildAccionesFromProyectos(lista) {
  const acciones = [];

  lista.forEach((p) => {
    const nombre = p.Proyecto || "Sin nombre";
    const cliente = p.Promotora_Fondo || "—";
    const ciudad = p.Ciudad || "—";
    const fase = p.Fase_proyecto || p.estado || "Detectado";

    // Seguimiento
    const fSeg = parseDateField(p.seguimiento_fecha);
    if (fSeg) {
      acciones.push({
        tipo: "Seguimiento",
        fechaDate: fSeg,
        proyecto: nombre,
        cliente,
        ciudad,
        estado: fase,
        descripcion: p.seguimiento_comentario || "",
      });
    }

    // Tarea
    const fT = parseDateField(p.tarea_fecha);
    if (fT && p.tarea_comentario) {
      acciones.push({
        tipo: "Tarea",
        fechaDate: fT,
        proyecto: nombre,
        cliente,
        ciudad,
        estado: fase,
        descripcion: p.tarea_comentario || "",
      });
    }
  });

  acciones.sort((a, b) => a.fechaDate - b.fechaDate);
  return acciones;
}

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
        const fecha = formatDate(a.fechaDate);
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

// Modal proyecto
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
    if (el) el.value = value != null ? value : "";
  };

  if (proyecto) {
    setVal("field-Proyecto", proyecto.Proyecto);
    setVal("field-Ciudad", proyecto.Ciudad);
    setVal("field-Provincia", proyecto.Provincia);
    setVal("field-Tipo_Proyecto", proyecto.Tipo_Proyecto);
    setVal("field-Segmento", proyecto.Segmento);
    setVal(
      "field-Num_viviendas_aprox",
      proyecto.Num_viviendas_aprox ?? proyecto["Nº_viviendas_aprox"] ?? ""
    );
    setVal("field-Promotora_Fondo", proyecto.Promotora_Fondo);
    setVal("field-Arquitectura", proyecto.Arquitectura);
    setVal("field-Ingenieria", proyecto.Ingenieria);
    setVal(
      "field-Fase_proyecto",
      proyecto.Fase_proyecto || proyecto.estado || "Detectado"
    );
    setVal(
      "field-Fecha_Inicio_Estimada",
      formatDateInput(proyecto.Fecha_Inicio_Estimada)
    );
    setVal(
      "field-Fecha_Entrega_Estimada",
      formatDateInput(proyecto.Fecha_Entrega_Estimada)
    );
    setVal("field-Potencial_2N", proyecto.Potencial_2N ?? "");
    setVal("field-potencial_eur", proyecto.potencial_eur ?? "");
    setVal("field-Fuente_URL", proyecto.Fuente_URL);
    setVal("field-Notas", proyecto.Notas);
    setVal(
      "field-seguimiento_fecha",
      formatDateInput(proyecto.seguimiento_fecha)
    );
    setVal(
      "field-seguimiento_comentario",
      proyecto.seguimiento_comentario || ""
    );
    setVal("field-tarea_fecha", formatDateInput(proyecto.tarea_fecha));
    setVal("field-tarea_comentario", proyecto.tarea_comentario || "");
  } else {
    const today = new Date().toISOString().slice(0, 10);
    document.getElementById("field-Fecha_Inicio_Estimada").value = today;
  }

  modal.classList.remove("hidden");
}

// Guardar proyecto (sin recargar Firestore completo)
async function guardarProyectoDesdeFormulario() {
  const id = document.getElementById("project-id").value || null;

  const Proyecto = document.getElementById("field-Proyecto").value.trim();
  if (!Proyecto) {
    alert("El nombre del proyecto es obligatorio.");
    return;
  }

  const payload = {
    Proyecto,
    Ciudad: document.getElementById("field-Ciudad").value.trim() || null,
    Provincia:
      document.getElementById("field-Provincia").value.trim() || null,
    Tipo_Proyecto:
      document.getElementById("field-Tipo_Proyecto").value.trim() || null,
    Segmento: document.getElementById("field-Segmento").value || null,
    Num_viviendas_aprox: Number(
      document.getElementById("field-Num_viviendas_aprox").value || 0
    ),
    Promotora_Fondo:
      document.getElementById("field-Promotora_Fondo").value.trim() || null,
    Arquitectura:
      document.getElementById("field-Arquitectura").value.trim() || null,
    Ingenieria:
      document.getElementById("field-Ingenieria").value.trim() || null,
    Fase_proyecto:
      document.getElementById("field-Fase_proyecto").value || "Detectado",
    Fecha_Inicio_Estimada:
      document.getElementById("field-Fecha_Inicio_Estimada").value || null,
    Fecha_Entrega_Estimada:
      document.getElementById("field-Fecha_Entrega_Estimada").value || null,
    Potencial_2N: Number(
      document.getElementById("field-Potencial_2N").value || 0
    ),
    potencial_eur: Number(
      document.getElementById("field-potencial_eur").value || 0
    ),
    Fuente_URL:
      document.getElementById("field-Fuente_URL").value.trim() || null,
    Notas: document.getElementById("field-Notas").value.trim() || null,
    seguimiento_fecha:
      document.getElementById("field-seguimiento_fecha").value || null,
    seguimiento_comentario:
      document
        .getElementById("field-seguimiento_comentario")
        .value.trim() || null,
    tarea_fecha:
      document.getElementById("field-tarea_fecha").value || null,
    tarea_comentario:
      document.getElementById("field-tarea_comentario").value.trim() ||
      null,
  };

  // Mantener compatibilidad con panel (estado)
  payload.estado = payload.Fase_proyecto;

  try {
    if (id) {
      await db.collection("proyectos").doc(id).update(payload);
      const idx = proyectos.findIndex((p) => p.id === id);
      if (idx !== -1) {
        proyectos[idx] = { ...proyectos[idx], ...payload };
      }
    } else {
      const docRef = await db.collection("proyectos").add({
        ...payload,
        created_at: firebase.firestore.FieldValue.serverTimestamp(),
      });
      proyectos.push({
        id: docRef.id,
        ...payload,
        created_at: new Date(),
      });
    }

    document.getElementById("project-modal").classList.add("hidden");

    aplicarFiltros();
    actualizarPanel();
  } catch (err) {
    console.error("Error guardando proyecto:", err);
    alert("Error guardando el proyecto. Revisa la consola.");
  }
}

// Borrar seleccionados
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
      batch.delete(db.collection("proyectos").doc(id));
    });
    await batch.commit();

    const idSet = new Set(ids);
    proyectos = proyectos.filter((p) => !idSet.has(p.id));

    aplicarFiltros();
    actualizarPanel();
  } catch (err) {
    console.error("Error borrando proyectos:", err);
    alert("Error borrando proyectos. Revisa la consola.");
  }
}

// Editar seleccionado
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

// Listeners
function setupEventos() {
  const search = document.getElementById("filter-search");
  const fase = document.getElementById("filter-fase");
  const segmento = document.getElementById("filter-segmento");

  if (search) search.addEventListener("input", aplicarFiltros);
  if (fase) fase.addEventListener("change", aplicarFiltros);
  if (segmento) segmento.addEventListener("change", aplicarFiltros);

  const btnAdd = document.getElementById("btn-add-project");
  const btnDel = document.getElementById("btn-delete-selected");
  const btnEdit = document.getElementById("btn-edit-selected");

  if (btnAdd) btnAdd.addEventListener("click", () => abrirModalProyecto(null));
  if (btnDel) btnDel.addEventListener("click", borrarSeleccionados);
  if (btnEdit) btnEdit.addEventListener("click", editarSeleccionado);

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

// Init
document.addEventListener("DOMContentLoaded", () => {
  setupNavigation();
  setupModalProyecto();
  setupEventos();
  cargarProyectosInicial();
});
