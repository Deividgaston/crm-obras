"use strict";

let proyectos = [];
let proyectoSeleccionado = null;

// ------------------ Utils ------------------
const $ = (sel) => document.querySelector(sel);

function toast(msg, ok = false) {
  const el = $("#toast");
  if (!el) {
    console[ok ? "log" : "error"](msg);
    return;
  }
  el.textContent = msg;
  el.style.background = ok ? "#0e9f6e" : "#c23934";
  el.style.opacity = "1";
  setTimeout(() => (el.style.opacity = "0"), 3000);
}

function formatDateDisplay(val) {
  if (!val) return "";
  let d = val;
  if (val.toDate) d = val.toDate(); // Timestamp
  d = new Date(d);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleDateString("es-ES");
}

function formatDateInput(val) {
  if (!val) return "";
  let d = val;
  if (val.toDate) d = val.toDate();
  d = new Date(d);
  if (Number.isNaN(d.getTime())) return "";
  return d.toISOString().slice(0, 10);
}

// ------------------ Carga datos ------------------
async function cargarProyectos() {
  try {
    const snap = await window.db.collection("proyectos").get();
    proyectos = snap.docs.map((d) => ({ id: d.id, ...d.data() }));
    renderTabla();
  } catch (e) {
    console.error(e);
    toast("Error al cargar proyectos");
  }
}

// ------------------ Render tabla ------------------
function renderTabla() {
  const texto = ($("#filtroTexto")?.value || "").toLowerCase();
  const fase = $("#filtroFase")?.value || "";
  const segmento = $("#filtroSegmento")?.value || "";

  const filtrados = proyectos.filter((p) => {
    const t =
      (p.Proyecto || "") +
      (p.Promotora_Fondo || "") +
      (p.Ciudad || "") +
      (p.Provincia || "");
    if (!t.toLowerCase().includes(texto)) return false;
    if (fase && (p.Fase_proyecto || "") !== fase) return false;
    if (segmento && (p.Segmento || "") !== segmento) return false;
    return true;
  });

  filtrados.sort((a, b) =>
    (a.Fase_proyecto || "").localeCompare(b.Fase_proyecto || "")
  );

  const tbody = $("#tabla-proyectos");
  if (!tbody) return;
  tbody.innerHTML = "";

  filtrados.forEach((p) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td class="crm-col-checkbox">
        <input type="checkbox" data-id="${p.id}" class="chk-proyecto">
      </td>
      <td>${p.Proyecto || ""}</td>
      <td>${p.Ciudad || ""}</td>
      <td>${p.Segmento || ""}</td>
      <td>${p.Fase_proyecto || ""}</td>
      <td>${formatDateDisplay(p.Fecha_Inicio_Estimada)}</td>
      <td>${p.Potencial_2N || ""}</td>
      <td>${p.Promotora_Fondo || ""}</td>
    `;
    // doble click → editar
    tr.addEventListener("dblclick", () => abrirModal(p.id));
    tbody.appendChild(tr);
  });

  actualizarBotones();
}

// ------------------ Botones según selección ------------------
function actualizarBotones() {
  const seleccionados = document.querySelectorAll(".chk-proyecto:checked");
  const btnEditar = $("#btnEditar");
  const btnBorrar = $("#btnBorrar");
  if (btnEditar) btnEditar.disabled = seleccionados.length !== 1;
  if (btnBorrar) btnBorrar.disabled = seleccionados.length === 0;
}

// ------------------ Modal ------------------
function abrirModal(id = null) {
  proyectoSeleccionado = id;
  const modal = $("#modal-proyecto");
  const titulo = $("#modal-titulo");
  const cont = $("#modalContenido");
  if (!modal || !titulo || !cont) return;

  titulo.textContent = id ? "Editar proyecto" : "Nuevo proyecto";

  const p = id ? proyectos.find((x) => x.id === id) || {} : {};

  cont.innerHTML = `
    <div class="crm-field-group">
      <label class="crm-label">Proyecto</label>
      <input id="mProyecto" class="crm-input" value="${p.Proyecto || ""}">
    </div>

    <div class="crm-field-group">
      <label class="crm-label">Ciudad</label>
      <input id="mCiudad" class="crm-input" value="${p.Ciudad || ""}">
    </div>

    <div class="crm-field-group">
      <label class="crm-label">Provincia</label>
      <input id="mProvincia" class="crm-input" value="${p.Provincia || ""}">
    </div>

    <div class="crm-field-group">
      <label class="crm-label">Segmento</label>
      <select id="mSegmento" class="crm-select">
        <option ${p.Segmento === "Lujo" ? "selected" : ""}>Lujo</option>
        <option ${p.Segmento === "Estándar" ? "selected" : ""}>Estándar</option>
        <option ${p.Segmento === "BTR" ? "selected" : ""}>BTR</option>
      </select>
    </div>

    <div class="crm-field-group">
      <label class="crm-label">Fase</label>
      <select id="mFase" class="crm-select">
        <option ${p.Fase_proyecto === "Detectado" ? "selected" : ""}>Detectado</option>
        <option ${p.Fase_proyecto === "Conceptual" ? "selected" : ""}>Conceptual</option>
        <option ${p.Fase_proyecto === "Anteproyecto" ? "selected" : ""}>Anteproyecto</option>
        <option ${p.Fase_proyecto === "Básico" ? "selected" : ""}>Básico</option>
        <option ${p.Fase_proyecto === "Ejecución" ? "selected" : ""}>Ejecución</option>
        <option ${p.Fase_proyecto === "Licitación" ? "selected" : ""}>Licitación</option>
        <option ${p.Fase_proyecto === "Construcción" ? "selected" : ""}>Construcción</option>
        <option ${p.Fase_proyecto === "Entregado" ? "selected" : ""}>Entregado</option>
        <option ${p.Fase_proyecto === "Paralizado" ? "selected" : ""}>Paralizado</option>
        <option ${p.Fase_proyecto === "Cancelado" ? "selected" : ""}>Cancelado</option>
      </select>
    </div>

    <div class="crm-field-group">
      <label class="crm-label">Promotora / Fondo</label>
      <input id="mPromotora" class="crm-input" value="${p.Promotora_Fondo || ""}">
    </div>

    <div class="crm-field-group">
      <label class="crm-label">Potencial 2N (€)</label>
      <input id="mPotencial" type="number" class="crm-input" value="${p.Potencial_2N || ""}">
    </div>

    <div class="crm-field-group">
      <label class="crm-label">Fecha inicio estimada</label>
      <input id="mFechaInicio" type="date" class="crm-input"
             value="${formatDateInput(p.Fecha_Inicio_Estimada)}">
    </div>

    <hr style="margin:8px 0; border:none; border-top:1px solid #e5e7eb;">

    <div class="crm-field-group">
      <label class="crm-label">Tarea - Fecha</label>
      <input id="mTareaFecha" type="date" class="crm-input"
             value="${formatDateInput(p.tarea_fecha)}">
    </div>

    <div class="crm-field-group">
      <label class="crm-label">Tarea - Comentario</label>
      <textarea id="mTareaComentario" class="crm-textarea">${p.tarea_comentario || ""}</textarea>
    </div>

    <div class="crm-field-group">
      <label class="crm-label">Seguimiento - Fecha</label>
      <input id="mSegFecha" type="date" class="crm-input"
             value="${formatDateInput(p.seguimiento_fecha)}">
    </div>

    <div class="crm-field-group">
      <label class="crm-label">Seguimiento - Comentario</label>
      <textarea id="mSegComentario" class="crm-textarea">${p.seguimiento_comentario || ""}</textarea>
    </div>

    <div class="crm-field-group">
      <label class="crm-label">Notas</label>
      <textarea id="mNotas" class="crm-textarea">${p.Notas || ""}</textarea>
    </div>
  `;

  modal.style.display = "flex";
}

function cerrarModal() {
  const modal = $("#modal-proyecto");
  if (modal) modal.style.display = "none";
  proyectoSeleccionado = null;
}

// ------------------ Guardar ------------------
async function guardarProyecto() {
  const datos = {
    Proyecto: $("#mProyecto").value.trim(),
    Ciudad: $("#mCiudad").value.trim(),
    Provincia: $("#mProvincia").value.trim(),
    Segmento: $("#mSegmento").value,
    Fase_proyecto: $("#mFase").value,
    Promotora_Fondo: $("#mPromotora").value.trim(),
    Potencial_2N: Number($("#mPotencial").value || 0),
    Fecha_Inicio_Estimada: $("#mFechaInicio").value || null,
    tarea_fecha: $("#mTareaFecha").value || null,
    tarea_comentario: $("#mTareaComentario").value.trim() || "",
    seguimiento_fecha: $("#mSegFecha").value || null,
    seguimiento_comentario: $("#mSegComentario").value.trim() || "",
    Notas: $("#mNotas").value.trim() || "",
  };

  if (!datos.Proyecto) {
    toast("El nombre del proyecto es obligatorio");
    return;
  }

  try {
    if (proyectoSeleccionado) {
      await window.db.collection("proyectos").doc(proyectoSeleccionado).update(datos);
      toast("Proyecto actualizado", true);
    } else {
      await window.db.collection("proyectos").add(datos);
      toast("Proyecto creado", true);
    }
    cerrarModal();
    cargarProyectos();
  } catch (err) {
    console.error(err);
    toast("Error guardando proyecto");
  }
}

// ------------------ Borrar ------------------
async function borrarSeleccionados() {
  const seleccionados = [...document.querySelectorAll(".chk-proyecto:checked")];
  if (!seleccionados.length) return;

  if (!confirm("¿Borrar los proyectos seleccionados?")) return;

  try {
    const batch = window.db.batch();
    seleccionados.forEach((chk) => {
      batch.delete(window.db.collection("proyectos").doc(chk.dataset.id));
    });
    await batch.commit();
    toast("Proyectos eliminados", true);
    cargarProyectos();
  } catch (err) {
    console.error(err);
    toast("Error borrando proyectos");
  }
}

// ------------------ Editar ------------------
function editarSeleccionado() {
  const chk = document.querySelector(".chk-proyecto:checked");
  if (chk) abrirModal(chk.dataset.id);
}

// ------------------ Init (espera a db y DOM) ------------------
function initProyectosPage() {
  // Eventos filtros
  $("#filtroTexto")?.addEventListener("input", renderTabla);
  $("#filtroFase")?.addEventListener("change", renderTabla);
  $("#filtroSegmento")?.addEventListener("change", renderTabla);

  // Botones
  $("#btnNuevo")?.addEventListener("click", () => abrirModal(null));
  $("#btnEditar")?.addEventListener("click", editarSeleccionado);
  $("#btnBorrar")?.addEventListener("click", borrarSeleccionados);
  $("#btnGuardar")?.addEventListener("click", guardarProyecto);
  $(".crm-modal-close")?.addEventListener("click", cerrarModal);

  // Checkboxes
  document.addEventListener("change", (e) => {
    if (e.target.classList.contains("chk-proyecto")) {
      actualizarBotones();
    }
  });

  // Cargar datos
  cargarProyectos();
}

document.addEventListener("DOMContentLoaded", () => {
  // Esperar a que firebase.js haya creado window.db
  const checkDb = () => {
    if (window.db) {
      initProyectosPage();
    } else {
      setTimeout(checkDb, 50);
    }
  };
  checkDb();
});
