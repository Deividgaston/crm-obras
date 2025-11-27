// firebase.js — configuración global del proyecto CRM Obras 2N

// SDKs Firebase (COMPAT)
document.write(`<script src="https://www.gstatic.com/firebasejs/9.23.0/firebase-app-compat.js"></script>`);
document.write(`<script src="https://www.gstatic.com/firebasejs/9.23.0/firebase-firestore-compat.js"></script>`);

// Esperamos a que Firebase cargue y luego inicializamos
window.addEventListener("DOMContentLoaded", () => {
  const firebaseConfig = {
    apiKey: "AIzaSyB51403DF43zxqq4K3Ex65i5-Sqm-EkiTY",
    authDomain: "crm-obras-2n.firebaseapp.com",
    projectId: "crm-obras-2n",
    storageBucket: "crm-obras-2n.firebasestorage.app",
    messagingSenderId: "545667121262",
    appId: "1:545667121262:web:9dd55a09bc7a7bb3e9a67f"
  };

  // Inicialización
  firebase.initializeApp(firebaseConfig);
  window.db = firebase.firestore();

  console.log("🔥 Firebase listo — Firestore conectado");
});
