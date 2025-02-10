function update_device_list() {
    document.querySelectorAll('#notifications_devices > div > div > div').forEach(function (element) {
        let device_info;
        try {
            device_info = JSON.parse(element.dataset.deviceInfo);
        } catch (e) {
            console.error('Failed to parse device info:', e);
            console.warn('Assuming the device contains only name.');
            element.querySelector('.card-content .media .media-content .title').textContent = element.dataset.deviceInfo;
            element.querySelector('.card-content > div > div > figure > img').src = 'https://eproba.zhr.pl/static/images/logo-background-200x200.png';
            element.querySelector('.card-content > div > div > figure > img').style.borderRadius = '8px';
            element.querySelector('.card-image figure img').src = `https://faisalman.github.io/ua-parser-js/images/types/mobile.png`;
            return;
        }
        const os_version = (device_info['os'].version !== '10') ? device_info['os'].version : '10/11';
        const browser = device_info['browser']['name'] ? device_info['browser']['name'].toLowerCase() : device_info['browser'].toLowerCase();
        const browserImageMap = {
            'chrome': 'chrome.png',
            'edge': 'edge.png',
            'safari': 'safari.png',
            'mobile safari': 'mobile%20safari.png',
            'opera': 'opera.png',
            'firefox': 'firefox.png'
        };

        if (browser in browserImageMap) {
            element.querySelector('.card-content > div > div > figure > img').src = `https://faisalman.github.io/ua-parser-js/images/browsers/${browserImageMap[browser]}`;
        } else {
            if (browser === 'app') {
                element.querySelector('.card-content > div > div > figure > img').src = 'https://eproba.zhr.pl/static/images/logo-background-200x200.png';
                element.querySelector('.card-content > div > div > figure > img').style.borderRadius = '8px';
            }
        }

        if (device_info['device'].vendor !== undefined) {
            element.querySelector('.card-content .media .media-content .title').innerHTML += `${device_info['device'].vendor}<br>`;
        }

        element.querySelector('.card-content .media .media-content .title').innerHTML += `${device_info['os'].name} ${os_version}`;
        element.querySelector('.card-content .media .media-content .subtitle').textContent = device_info['browser']['name'] ? device_info['browser']['name'] : device_info['browser'];

        if (device_info['device'].type !== undefined) {
            element.querySelector('.card-image figure img').src = `https://faisalman.github.io/ua-parser-js/images/types/${device_info['device'].type}.png`;
        }
    });

}

function mark_current_device() {
    let attempts = 0;
    const maxAttempts = 10;

    function checkToken() {
        if (window.firebaseToken) {
            document.querySelectorAll('#notifications_devices > div > div > div').forEach(function (element) {
                const device_token = element.dataset.registration_id;
                if (device_token === window.firebaseToken) {
                    element.querySelector('.card-content .media .media-content #that-device').innerHTML += '<span class="tag is-info">To urządzenie</span>';
                }
            });
        } else if (attempts < maxAttempts) {
            attempts++;
            setTimeout(checkToken, 1000);
        } else {
            console.log('window.firebaseToken not found within 10 seconds.');
        }
    }

    checkToken();
}

function getCookie(name) {
    let cookieArr = document.cookie.split(';');
    for (let i = 0; i < cookieArr.length; i++) {
        let cookiePair = cookieArr[i].split('=');
        if (name === cookiePair[0].trim()) {
            return decodeURIComponent(cookiePair[1]);
        }
    }
    return null;
}

function setCookie(name, value, days) {
    let expires = '';
    if (days) {
        let date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        expires = '; expires=' + date.toUTCString();
    }
    document.cookie = name + '=' + (value || '') + expires + '; path=/';
}

document.addEventListener('DOMContentLoaded', function () {
    update_device_list();


    document.querySelectorAll('.button').forEach(button => {
        button.addEventListener('click', function () {
            const deviceId = this.dataset.deviceId;
            const action = this.id.split('-')[0];

            if (action === 'active') {
                fetch(`/api/fcm/devices/${deviceId}/`, {
                    method: 'PATCH',
                    headers: {
                        'X-CSRFToken': csrfToken,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        active: this.dataset.active !== 'True'
                    })
                })
                    .then(response => response.json())
                    .then(data => {
                        alert('Urządzenie zostało wyrejestrowane.');
                        document.getElementById('notifications_devices').innerHTML = '';
                        location.reload();
                    });
            } else if (action === 'delete') {
                fetch(`/api/fcm/devices/${deviceId}/`, {
                    method: 'DELETE',
                    headers: {
                        'X-CSRFToken': csrfToken
                    }
                })
                    .then(response => {
                        alert('Urządzenie zostało usunięte.');
                        if (getCookie('fcm_token') === deviceId) {
                            setCookie('disable_notifications', true, 365);
                        }
                        document.getElementById('notifications_devices').innerHTML = '';
                        location.reload();
                    });
            }
        });
    });

    mark_current_device();
});