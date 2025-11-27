"use strict";

let proyectos = [];
let proyectoSeleccionado = null;

// -------------- Utils --------------
const $ = (sel) => document.querySelector(sel);

function toast(msg, ok = false) {
  const el = $("#toast");
  el.textContent = msg;
  el.style.background = ok ? "#0e9f6e" : "#c23934";
  el.style.opacity = "1";
  setTimeout(() => (el.style.opacity = "0"), 3000);
}

function formatDate(val) {
  if (!val) return "";
  let d = val.toDate ? val.toDate() : new Date(val);
  return d.toLocaleDateString("es-ES");
}

// -------------- Cargar datos --------------
async function cargarProyectos() {
  try {
    const snap = await db.collection("proyectos").get();
    proyectos = snap.docs.map((d) => ({ id: d.id, ...d.data() }));
    renderTabla();
  } catch (e) {
    console.error(e);
    toast("Error al cargar proyectos");
  }
}

// -------------- Render tabla --------------
function renderTabla() {
  const texto = $("#filtroTexto").value.toLowerCase();
  const fase = $("#filtroFase").value;
  const segmento = $("#filtroSegmento").value;

  const filtrados = proyectos.filter((p) => {
    const t =
      (p.Proyecto || "") +
      (p.Promotora_Fondo || "") +
      (p.Ciudad || "") +
      (p.Provincia || "");
    if (!t.toLowerCase().includes(texto)) return false;
    if (fase && p.Fase_proyecto !== fase) return false;
    if (segmento && p.Segmento !== segmento) return false;
    return true;
  });

  filtrados.sort((a, b) =>
    (a.Fase_proyecto || "").localeCompare(b.Fase_proyecto || "")
  );

  const tbody = $("#tabla-proyectos");
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
      <td>${formatDate(p.Fecha_Inicio_Estimada)}</td>
      <td>${p.Potencial_2N || ""}</td>
      <td>${p.Promotora_Fondo || ""}</td>
    `;
    tr.addEventListener("dblclick", () => abrirModal(p.id));
    tbody.appendChild(tr);
  });

  actualizarBotones();
}

// -------------- Botones según selección --------------
function actualizarBotones() {
  const seleccionados = document.querySelectorAll(".chk-proyecto:checked");
  $("#btnEditar").disabled = seleccionados.length !== 1;
  $("#btnBorrar").disabled = seleccionados.length === 0;
}

// -------------- Modal --------------
function abrirModal(id = null) {
  proyectoSeleccionado = id;
  $("#modal-titulo").textContent = id ? "Editar proyecto" : "Nuevo proyecto";

  const p = id ? proyectos.find((x) => x.id === id) : {};

  $("#modalContenido").innerHTML = `
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
      <input id="mPotencial" class="crm-input" value="${p.Potencial_2N || ""}">
    </div>

    <div class="crm-field-group">
      <label class="crm-label">Notas</label>
      <textarea id="mNotas" class="crm-textarea">${p.Notas || ""}</textarea>
    </div>
  `;

  $("#modal-proyecto").style.display = "flex";
}

function cerrarModal() {
  $("#modal-proyecto").style.display = "none";
  proyectoSeleccionado = null;
}

// -------------- Guardar --------------
$("#btnGuardar").onclick = async () => {
  const datos = {
    Proyecto: $("#mProyecto").value,
    Ciudad: $("#mCiudad").value,
    Provincia: $("#mProvincia").value,
    Segmento: $("#mSegmento").value,
    Fase_proyecto: $("#mFase").value,
    Promotora_Fondo: $("#mPromotora").value,
    Potencial_2N: Number($("#mPotencial").value),
    Notas: $("#mNotas").value,
  };

  try {
    if (proyectoSeleccionado) {
      await db.collection("proyectos").doc(proyectoSeleccionado).update(datos);
      toast("Proyecto actualizado", true);
    } else {
      await db.collection("proyectos").add(datos);
      toast("Proyecto creado", true);
    }

    cerrarModal();
    cargarProyectos();
  } catch (err) {
    console.error(err);
    toast("Error guardando");
  }
};

// -------------- Borrar --------------
$("#btnBorrar").onclick = async () => {
  const seleccionados = [...document.querySelectorAll(".chk-proyecto:checked")];
  if (!seleccionados.length) return;

  if (!confirm("¿Borrar los proyectos seleccionados?")) return;

  try {
    const batch = db.batch();
    seleccionados.forEach((chk) => {
      batch.delete(db.collection("proyectos").doc(chk.dataset.id));
    });
    await batch.commit();

    toast("Proyectos eliminados", true);
    cargarProyectos();
  } catch (err) {
    console.error(err);
    toast("Error borrando");
  }
};

// -------------- Editar --------------
$("#btnEditar").onclick = () => {
  const chk = document.querySelector(".chk-proyecto:checked");
  if (chk) abrirModal(chk.dataset.id);
};

// -------------- Eventos filtros --------------
$("#filtroTexto").oninput = renderTabla;
$("#filtroFase").onchange = renderTabla;
$("#filtroSegmento").onchange = renderTabla;

// -------------- Eventos selección --------------
document.addEventListener("change", (e) => {
  if (e.target.classList.contains("chk-proyecto")) {
    actualizarBotones();
  }
});

// -------------- Botón nuevo --------------
$("#btnNuevo").onclick = () => abrirModal(null);

// -------------- Inicial --------------
document.addEventListener("DOMContentLoaded", cargarProyectos);
