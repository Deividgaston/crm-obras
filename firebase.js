// firebase.js
// Configuración centralizada de Firebase (App, Firestore y Auth)
// Se usa en TODO el CRM (index, proyectos, clientes, tareas, reportes, etc.)

import { initializeApp } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-app.js";
import {
  getFirestore,
  enableIndexedDbPersistence
} from "https://www.gstatic.com/firebasejs/10.8.0/firebase-firestore.js";
import {
  getAuth,
  setPersistence,
  browserLocalPersistence
} from "https://www.gstatic.com/firebasejs/10.8.0/firebase-auth.js";

const firebaseConfig = {
  apiKey: "AIzaSyB51403DF43zxqq4K3Ex65i5-Sqm-EkiTY",
  authDomain: "crm-obras-2n.firebaseapp.com",
  projectId: "crm-obras-2n",
  storageBucket: "crm-obras-2n.firebasestorage.app",
  messagingSenderId: "545667121262",
  appId: "1:545667121262:web:9dd55a09bc7a7bb3e9a67f"
};

// Inicializar app
const app = initializeApp(firebaseConfig);

// Firestore
const db = getFirestore(app);

// Persistencia offline / cache local (optimiza lecturas)
enableIndexedDbPersistence(db).catch((err) => {
  console.warn("No se pudo activar la persistencia de Firestore:", err.code || err);
});

// Auth
const auth = getAuth(app);

// Persistencia de sesión en el navegador
setPersistence(auth, browserLocalPersistence).catch((err) => {
  console.warn("No se pudo establecer persistencia de sesión:", err.code || err);
});

export { app, db, auth };
