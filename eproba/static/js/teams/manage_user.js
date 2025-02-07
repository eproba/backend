function rankDisplay(scoutRank, instructorRank) {
    if (instructorRank !== 0) {
        return `${scoutRanks[scoutRank]} ${instructorRanks[instructorRank]}`;
    } else {
        return scoutRanks[scoutRank];
    }
}

async function deactivateUser() {
    try {
        const response = await fetch(`/api/users/${user.id}/`, {
            method: 'PATCH',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({'is_active': false})
        });
        if (response.ok) {
            alert('Użytkownik został dezaktywowany');
            location.replace("/team/");
        } else {
            alert(`Nie udało się dezaktywować użytkownika: \n${response.statusText}`);
        }
    } catch (error) {
        alert(`Nie udało się dezaktywować użytkownika: \n${error.message}`);
    }
}

async function reactivateUser() {
    try {
        const response = await fetch(`/api/users/${user.id}/`, {
            method: 'PATCH',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({'is_active': true})
        });
        if (response.ok) {
            alert('Użytkownik został aktywowany');
            location.reload();
        } else {
            alert(`Nie udało się aktywować użytkownika: \n${response.statusText}`);
        }
    } catch (error) {
        alert(`Nie udało się aktywować użytkownika: \n${error.message}`);
    }
}

async function transferUser(targetPatrolId) {
    try {
        const response = await fetch(`/api/users/${user.id}/`, {
            method: 'PATCH',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({'patrol': targetPatrolId, 'function': 0})
        });
        if (response.ok) {
            alert('Użytkownik został przeniesiony do nowej drużyny');
            location.replace("/team/");
        } else {
            alert(`Nie udało się przenieść użytkownika: \n${response.statusText}`);
        }
    } catch (error) {
        alert(`Nie udało się przenieść użytkownika: \n${error.message}`);
    }
}

async function changePatrol(targetPatrolId) {
    try {
        const response = await fetch(`/api/users/${user.id}/`, {
            method: 'PATCH',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({'patrol': targetPatrolId})
        });
        if (response.ok) {
            const data = await response.json();
            document.getElementById('patrol').innerHTML = `${data.patrol_name} <i class="fa-solid fa-pen fa-xs"></i></p>`;
            alert('Użytkownik został przeniesiony do innego zastępu');
        } else {
            alert(`Nie udało się przenieść użytkownika: \n${response.statusText}`);
        }
    } catch (error) {
        alert(`Nie udało się przenieść użytkownika: \n${error.message}`);
    }
}

async function changeFunction(newFunction) {
    try {
        const response = await fetch(`/api/users/${user.id}/`, {
            method: 'PATCH',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({'function': newFunction})
        });
        if (response.ok) {
            const data = await response.json();
            document.getElementById('function').innerHTML = `${functions[data.function]} <i class="fa-solid fa-pen fa-xs"></i></p>`;
            alert('Funkcja użytkownika została zmieniona');
        } else {
            alert(`Nie udało się zmienić funkcji: \n${response.statusText}`);
        }
    } catch (error) {
        alert(`Nie udało się zmienić funkcji: \n${error.message}`);
    }
}

async function changeRanks(newScoutRank, newInstructorRank) {
    try {
        const response = await fetch(`/api/users/${user.id}/`, {
            method: 'PATCH',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({'scout_rank': newScoutRank, 'instructor_rank': newInstructorRank})
        });
        if (response.ok) {
            const data = await response.json();
            document.getElementById('rank').innerHTML = `${rankDisplay(data.scout_rank, data.instructor_rank)} <i class="fa-solid fa-pen fa-xs"></i></p>`;
            alert('Stopień użytkownika został zmieniony');
        } else {
            alert(`Nie udało się zmienić stopnia: \n${response.statusText}`);
        }
    } catch (error) {
        alert(`Nie udało się zmienić stopnia: \n${error.message}`);
    }
}

async function changeFirstName(newFirstName) {
    try {
        const response = await fetch(`/api/users/${user.id}/`, {
            method: 'PATCH',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({'first_name': newFirstName})
        });
        if (response.ok) {
            const data = await response.json();
            document.getElementById('first-name').innerHTML = `${data.first_name}`;
            document.getElementById('first-name-edit-icon').style.display = 'inline';
            document.getElementById('first-name-loading-icon').style.display = 'none';
            alert('Imię użytkownika zostało zmienione');
        } else {
            alert(`Nie udało się zmienić imienia: \n${response.statusText}`);
        }
    } catch (error) {
        alert(`Nie udało się zmienić imienia: \n${error.message}`);
    }
}

async function changeLastName(newLastName) {
    try {
        const response = await fetch(`/api/users/${user.id}/`, {
            method: 'PATCH',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({'last_name': newLastName})
        });
        if (response.ok) {
            const data = await response.json();
            document.getElementById('last-name').innerHTML = `${data.last_name}`;
            document.getElementById('last-name-edit-icon').style.display = 'inline';
            document.getElementById('last-name-loading-icon').style.display = 'none';
            alert('Nazwisko użytkownika zostało zmienione');
        } else {
            alert(`Nie udało się zmienić nazwiska: \n${response.statusText}`);
        }
    } catch (error) {
        alert(`Nie udało się zmienić nazwiska: \n${error.message}`);
    }
}

async function changeNickname(newNickname) {
    try {
        const response = await fetch(`/api/users/${user.id}/`, {
            method: 'PATCH',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({'nickname': newNickname})
        });
        if (response.ok) {
            const data = await response.json();
            document.getElementById('nickname').innerHTML = `${data.nickname}`;
            document.getElementById('nickname-edit-icon').style.display = 'inline';
            document.getElementById('nickname-loading-icon').style.display = 'none';
            alert('Pseudonim użytkownika został zmieniony');
        } else {
            alert(`Nie udało się zmienić pseudonimu: \n${response.statusText}`);
        }
    } catch (error) {
        alert(`Nie udało się zmienić pseudonimu: \n${error.message}`);
    }
}
document.addEventListener('DOMContentLoaded', () => {
    // Set variables that will be used to discard changes
    let firstNameField = document.getElementById('first-name')
    let lastNameField = document.getElementById('last-name')
    let nicknameField = document.getElementById('nickname')

    document.getElementById('scout-rank-select').value = user.scout_rank;
    document.getElementById('instructor-rank-select').value = user.instructor_rank;
    document.getElementById('patrol-select').value = user.patrol;
    document.getElementById('function-select').value = user.function;
    if (user.scout_rank >= 5) {
        document.getElementById('instructor-rank-field').style.display = 'block';
    }

    document.querySelectorAll("#transfer-user-patrol-select option").forEach((patrol) => {
        patrol.style.display = "none";
    });
    document.getElementById('transfer-user-patrol-select').value = -1;
    document.getElementById('transfer-user-team-select').value = -1;

    function openModal(el) {
        el.classList.add('is-active');
    }

    function closeModal(el) {
        el.classList.remove('is-active');
    }

    function closeAllModals() {
        document.querySelectorAll('.modal').forEach((modal) => {
            closeModal(modal);
        });
    }

    // Add a click event on buttons to open a specific modal
    document.querySelectorAll('.js-modal-trigger').forEach(trigger => {
        const modalId = trigger.dataset.target;
        const modalElement = document.getElementById(modalId);

        trigger.addEventListener('click', () => {
            openModal(modalElement);
        });
    });

    // Add a click event on various child elements to close the parent modal
    (document.querySelectorAll('.modal-background, .modal-close, .modal-card-head .delete, .modal-card-foot .button') || []).forEach((close) => {
        const target = close.closest('.modal');

        close.addEventListener('click', () => {
            closeModal(target);
        });
    });

    // Add a keyboard event to close all modals
    document.addEventListener('keydown', (event) => {
        if (event.key === "Escape") {
            closeAllModals();
        }
    });

    const transferUserTeamSelect = document.getElementById('transfer-user-team-select');
    const transferUserPatrolSelect = document.getElementById('transfer-user-patrol-select');


    transferUserTeamSelect.addEventListener('change', () => {
        const teamId = transferUserTeamSelect.value;
        const patrols = transferUserPatrolSelect.querySelectorAll('option');
        let matchingForeignPatrols = [];
        patrols.forEach((patrol) => {
            if (patrol.getAttribute('data-team-id') === teamId) {
                patrol.style.display = 'block';
                matchingForeignPatrols.push(patrol);
            } else {
                patrol.style.display = 'none';
            }
        });
        if (matchingForeignPatrols.length > 0) {
            matchingForeignPatrols[0].selected = true;
        }
    });

    function handleFocusIn(field, editIcon, saveIcons) {
        editIcon.style.display = 'none';
        saveIcons.style.display = 'inline';
    }

    function handleFocusOut(field, editIcon, saveIcons, loadingIcon, previousValue, changeFunction) {
        return (event) => {
            if (event.relatedTarget && event.relatedTarget.id === `${field.id}-confirm-icon`) {
                previousValue = field.textContent;
                saveIcons.style.display = 'none';
                loadingIcon.style.display = 'inline';
                changeFunction(field.textContent);
                return;
            }
            editIcon.style.display = 'inline';
            saveIcons.style.display = 'none';
            field.textContent = previousValue;
        };
    }

    function handleKeyDown(field, previousValue, changeFunction, saveIcons, loadingIcon) {
        return (event) => {
            if (event.key === 'Enter') {
                event.preventDefault();
                previousValue = field.textContent;
                changeFunction(field.textContent);
                saveIcons.style.display = 'none';
                loadingIcon.style.display = 'inline';
                field.blur();
            }
        };
    }

    const firstNameEditIcon = document.getElementById('first-name-edit-icon');
    const firstNameSaveIcons = document.getElementById('first-name-save-icons');
    const firstNameLoadingIcon = document.getElementById('first-name-loading-icon');
    previousFirstName = firstNameField.textContent;

    firstNameField.addEventListener('focusin', () => handleFocusIn(firstNameField, firstNameEditIcon, firstNameSaveIcons));
    firstNameField.addEventListener('focusout', handleFocusOut(firstNameField, firstNameEditIcon, firstNameSaveIcons, firstNameLoadingIcon, previousFirstName, changeFirstName));
    firstNameField.addEventListener('keydown', handleKeyDown(firstNameField, previousFirstName, changeFirstName, firstNameSaveIcons, firstNameLoadingIcon));

    const lastNameEditIcon = document.getElementById('last-name-edit-icon');
    const lastNameSaveIcons = document.getElementById('last-name-save-icons');
    const lastNameLoadingIcon = document.getElementById('last-name-loading-icon');
    previousLastName = lastNameField.textContent;

    lastNameField.addEventListener('focusin', () => handleFocusIn(lastNameField, lastNameEditIcon, lastNameSaveIcons));
    lastNameField.addEventListener('focusout', handleFocusOut(lastNameField, lastNameEditIcon, lastNameSaveIcons, lastNameLoadingIcon, previousLastName, changeLastName));
    lastNameField.addEventListener('keydown', handleKeyDown(lastNameField, previousLastName, changeLastName, lastNameSaveIcons, lastNameLoadingIcon));

    const nicknameEditIcon = document.getElementById('nickname-edit-icon');
    const nicknameSaveIcons = document.getElementById('nickname-save-icons');
    const nicknameLoadingIcon = document.getElementById('nickname-loading-icon');
    previousNickname = nicknameField.textContent;

    nicknameField.addEventListener('focusin', () => handleFocusIn(nicknameField, nicknameEditIcon, nicknameSaveIcons));
    nicknameField.addEventListener('focusout', handleFocusOut(nicknameField, nicknameEditIcon, nicknameSaveIcons, nicknameLoadingIcon, previousNickname, changeNickname));
    nicknameField.addEventListener('keydown', handleKeyDown(nicknameField, previousNickname, changeNickname, nicknameSaveIcons, nicknameLoadingIcon));

});