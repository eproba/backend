import {initializeApp} from "https://www.gstatic.com/firebasejs/9.14.0/firebase-app.js";
import {getAnalytics} from "https://www.gstatic.com/firebasejs/9.14.0/firebase-analytics.js";
import {getMessaging, getToken, onMessage} from "https://www.gstatic.com/firebasejs/9.14.0/firebase-messaging.js";

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

document.addEventListener('DOMContentLoaded', () => {
    const app = initializeApp(firebaseConfig);
    const analytics = getAnalytics(app);
    const messaging = getMessaging();

    const getCookie = (name) => {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
    };

    const setCookie = (name, value, days) => {
        let expires = "";
        if (days) {
            const date = new Date();
            date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
            expires = `; expires=${date.toUTCString()}`;
        }
        document.cookie = `${name}=${value || ""}${expires}; path=/`;
    };

    if (getCookie("disable_notifications") === undefined && getCookie("disable_notifications") !== "true") {
        getToken(messaging, {vapidKey: "BJDPUgOL1f1s5051JlJVqiO_Ik_aj-brMltYdg8FuHa3MS45g06M_ae2yDvUDm99TI4-5myoFVluitL9AUay4mA"}).then((currentToken) => {
            if (currentToken) {
                window.firebaseToken = currentToken;
                fetch('/api/fcm/devices/', {
                    method: 'GET',
                    headers: {'X-CSRFToken': csrfToken}
                })
                    .then(response => response.json())
                    .then(data => {
                        if (data.filter(e => e.registration_id === currentToken).length === 0) {
                            const uap = new UAParser();
                            const ua = uap.getResult();
                            fetch('/api/fcm/devices/', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                    'X-CSRFToken': csrfToken
                                },
                                body: JSON.stringify({
                                    "registration_id": currentToken,
                                    "name": JSON.stringify({
                                        "os": ua.os,
                                        "device": ua.device,
                                        "browser": ua.browser.name,
                                    }),
                                    "type": "web"
                                })
                            })
                                .then(response => response.json())
                                .then(data => {
                                    console.info("Zarejestrowano urządzenie dla FCM");
                                });
                        }
                    });
                setCookie('fcm_token', currentToken, 365);
            } else {
                console.log('No registration token available. Request permission to generate one.');
            }
        }).catch((err) => {
            console.log('An error occurred while retrieving token. ', err);
        });

        onMessage(messaging, (payload) => {
            const notificationsContainer = document.getElementById('notifications');

            const notificationDiv = document.createElement('div');
            notificationDiv.className = 'notification';

            const deleteButton = document.createElement('button');
            deleteButton.className = 'delete';
            deleteButton.onclick = function () {
                notificationDiv.remove();
            };

            const notificationLink = document.createElement('a');
            notificationLink.href = payload.fcmOptions.link;
            notificationLink.innerHTML = `<strong>${payload.notification.title}</strong><br>`;

            const notificationBody = document.createTextNode(payload.notification.body);

            notificationDiv.appendChild(deleteButton);
            notificationDiv.appendChild(notificationLink);
            notificationDiv.appendChild(notificationBody);

            notificationsContainer.appendChild(notificationDiv);

            setTimeout(() => {
                notificationDiv.remove();
            }, 10000);
        });
    }
});