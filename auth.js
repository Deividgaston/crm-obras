// auth.js
// Guard de autenticación para todas las páginas del CRM

import { auth } from "./firebase.js";
import {
  onAuthStateChanged,
  signOut
} from "https://www.gstatic.com/firebasejs/10.8.0/firebase-auth.js";

const PUBLIC_PAGES = ["login.html", "login", ""]; // permitimos acceso directo al login

function getCurrentPageName() {
  const path = window.location.pathname;
  const file = path.split("/").pop() || "";
  return file.toLowerCase();
}

function isPublicPage() {
  const file = getCurrentPageName();
  return PUBLIC_PAGES.includes(file);
}

// Proteger páginas
onAuthStateChanged(auth, (user) => {
  if (!user && !isPublicPage()) {
    // No logueado → login
    window.location.href = "login.html";
    return;
  }

  // Ya logueado y está en login → mandarlo al dashboard
  if (user && getCurrentPageName() === "login.html") {
    window.location.href = "index.html";
  }
});

// Logout si existe el botón
document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("btnLogout");
  if (btn) {
    btn.addEventListener("click", async () => {
      try {
        await signOut(auth);
        window.location.href = "login.html";
      } catch (err) {
        console.error("Error al cerrar sesión:", err);
        alert("No se pudo cerrar sesión. Inténtalo de nuevo.");
      }
    });
  }
});
