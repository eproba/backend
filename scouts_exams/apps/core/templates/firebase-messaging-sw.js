importScripts('https://www.gstatic.com/firebasejs/9.8.3/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/9.8.3/firebase-messaging-compat.js');
const firebaseConfig = {
    apiKey: "AIzaSyBKVP78_xDjRNNs9VBk2fEvLOvhxRL2kng",
    authDomain: "scouts-exams.firebaseapp.com",
    databaseURL: "https://scouts-exams-default-rtdb.europe-west1.firebasedatabase.app",
    projectId: "scouts-exams",
    storageBucket: "scouts-exams.appspot.com",
    messagingSenderId: "897419344971",
    appId: "1:897419344971:web:dd3325a492cc57756d61ce",
    measurementId: "G-YB1DB8G1WG"
};

// Initialize Firebase
const app = firebase.initializeApp(firebaseConfig);
const messaging = firebase.messaging();