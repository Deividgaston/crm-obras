// firebase.js
// Configuración Firebase + export de Firestore como módulo ES6

import { initializeApp } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-app.js";
import { getFirestore } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-firestore.js";

const firebaseConfig = {
  apiKey: "AIzaSyB51403DF43zxqq4K3Ex65i5-Sqm-EkiTY",
  authDomain: "crm-obras-2n.firebaseapp.com",
  projectId: "crm-obras-2n",
  storageBucket: "crm-obras-2n.firebasestorage.app",
  messagingSenderId: "545667121262",
  appId: "1:545667121262:web:9dd55a09bc7a7bb3e9a67f"
};

// Inicializar Firebase
const app = initializeApp(firebaseConfig);

// Exportar instancia de Firestore
export const db = getFirestore(app);
