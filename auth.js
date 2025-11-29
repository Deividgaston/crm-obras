// auth.js – Guardia global de autenticación para CRM 2N
// -------------------------------------------------------

import { auth } from "./firebase.js";
import {
  onAuthStateChanged,
  signOut
} from "https://www.gstatic.com/firebasejs/10.8.0/firebase-auth.js";

// Páginas sin autenticación requerida
const PUBLIC_PAGES = ["login.html", "login", ""];

// Obtener el nombre del archivo actual
function getCurrentPageName() {
  const path = window.location.pathname;
  return (path.split("/").pop() || "").toLowerCase();
}

// ¿Es página pública?
function isPublicPage() {
  return PUBLIC_PAGES.includes(getCurrentPageName());
}

// Aplicar la guardia de autenticación
onAuthStateChanged(auth, (user) => {

  // 🚫 NO autenticado → cualquier página privada redirige a login
  if (!user && !isPublicPage()) {
    window.location.replace("login.html");
    return;
  }

  // 🔁 SI autenticado → evitar permanecer en login
  if (user && getCurrentPageName() === "login.html") {
    window.location.replace("index.html");
    return;
  }
});

// Logout global si existe el botón
document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("btnLogout");

  if (btn) {
    btn.addEventListener("click", async () => {
      try {
        await signOut(auth);

        // Evitar volver atrás al login
        window.location.replace("login.html");

        // Limpieza extra (por si algún navegador cachea)
        setTimeout(() => {
          window.location.href = "login.html";
        }, 50);

      } catch (err) {
        console.error("❌ Error al cerrar sesión:", err);
        alert("No se pudo cerrar sesión, inténtalo de nuevo.");
      }
    });
  }
});
