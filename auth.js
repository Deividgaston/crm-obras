// auth.js
import { auth } from "./firebase.js";
import {
  onAuthStateChanged,
  signOut
} from "https://www.gstatic.com/firebasejs/10.8.0/firebase-auth.js";

// =============================
// REDIRECCIÓN A VERSIONES MÓVILES
// =============================

(function handleMobileRedirect() {
  const isMobile = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
  if (!isMobile) return;

  const path = window.location.pathname;
  const page = path.split("/").pop() || "index.html";

  // No redirigir desde login, admin ni si ya estás en una página móvil
  if (
    page === "login.html" ||
    page === "admin.html" ||
    page.startsWith("mobile-")
  ) {
    return;
  }

  const mobileMap = {
    "index.html": "mobile-index.html",
    "proyectos.html": "mobile-proyectos.html",
    "clientes.html": "mobile-clientes.html",
    "tareas.html": "mobile-tareas.html"
    // si en el futuro haces más: "reportes.html": "mobile-reportes.html", etc.
  };

  const target = mobileMap[page];
  if (target) {
    window.location.replace(target);
  }
})();

// =============================
// GUARDIA DE AUTENTICACIÓN
// =============================

const PUBLIC_PAGES = ["login.html"];

function getCurrentPage() {
  const path = window.location.pathname;
  return path.split("/").pop() || "index.html";
}

onAuthStateChanged(auth, (user) => {
  const page = getCurrentPage();

  // Si no está logueado y no es página pública → al login
  if (!user && !PUBLIC_PAGES.includes(page)) {
    window.location.replace("login.html");
    return;
  }

  // Si está logueado y está en login → al index (desktop; móvil ya redirige solo)
  if (user && PUBLIC_PAGES.includes(page)) {
    window.location.replace("index.html");
    return;
  }
});

// =============================
// LOGOUT (botón con id="btnLogout")
// =============================

const btnLogout = document.getElementById("btnLogout");
if (btnLogout) {
  btnLogout.addEventListener("click", async () => {
    try {
      await signOut(auth);
      window.location.replace("login.html");
    } catch (err) {
      console.error("Error al cerrar sesión:", err);
      alert("No se ha podido cerrar sesión. Inténtalo de nuevo.");
    }
  });
}
