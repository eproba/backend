let teamNameField, teamShortNameField, previousTeamName, previousTeamShortName;

function changeTeamName(newName) {
    fetch(`/api/teams/${teamId}/`, {
        method: 'PATCH',
        headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({'name': newName})
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            document.getElementById(`team-name-${teamId}-loading-icon`).style.display = 'none';
            document.getElementById(`team-name-${teamId}-edit-icon`).style.display = 'inline';
        })
        .catch(() => {
            document.getElementById(`team-name-${teamId}-loading-icon`).style.display = 'none';
            document.getElementById(`team-name-${teamId}-edit-icon`).style.display = 'inline';
            teamNameField.textContent = previousTeamName;
        });
}

function changeTeamShortName(newName) {
    fetch(`/api/teams/${teamId}/`, {
        method: 'PATCH',
        headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({'short_name': newName})
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            document.getElementById(`team-short-name-${teamId}-loading-icon`).style.display = 'none';
            document.getElementById(`team-short-name-${teamId}-edit-icon`).style.display = 'inline';
        })
        .catch(() => {
            document.getElementById(`team-short-name-${teamId}-loading-icon`).style.display = 'none';
            document.getElementById(`team-short-name-${teamId}-edit-icon`).style.display = 'inline';
            teamShortNameField.textContent = previousTeamShortName;
        });
}

function createPatrol(patrolName, teamId) {
    if (patrolName.trim() === "") {
        alert("Nazwa zastępu nie może być pusta");
        return;
    }

    fetch("/api/patrols/", {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({'name': patrolName, 'team': teamId})
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            location.reload();
            alert("Zastęp został utworzony");
        })
        .catch(() => {
            alert("Nie udało się utworzyć zastępu");
        });
}

function changePatrolName(patrolId, newName) {
    if (newName === "" || newName === " ") {
        alert("Nazwa zastępu nie może być pusta");
        return;
    }
    fetch(`/api/patrols/${patrolId}/`, {
        method: 'PATCH',
        headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({'name': newName})
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            location.reload();
            alert("Nazwa zastępu została zmieniona");
        })
        .catch(() => {
            alert("Nie udało się zmienić nazwy zastępu");
        });
}

function deletePatrol(patrolId) {
    fetch(`/api/patrols/${patrolId}/`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json'
        }
    })
        .then(response => {
            if (!response.ok) {
                if (response.status === 409) {
                    throw new Error("Nie można usunąć zastępu, ponieważ istnieją w nim aktywni harcerze");
                } else {
                    throw new Error("Nie udało się usunąć zastępu");
                }
            }
            location.reload();
            alert("Zastęp został usunięty");
        })
        .catch(error => {
            if (error.message === "Failed to fetch") {
                alert("Nie udało się usunąć zastępu: \nSprawdź swoje połączenie z internetem");
            } else {
                alert(error.message);
            }
        });
}


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

document.addEventListener('DOMContentLoaded', function () {
        teamNameField = document.getElementById(`team-name-${teamId}`);
        teamShortNameField = document.getElementById(`team-short-name-${teamId}`);
        previousTeamName = teamNameField.textContent;
        previousTeamShortName = teamShortNameField.textContent;

        teamNameField.addEventListener('focusin', function () {
            document.getElementById(`team-name-${teamId}-edit-icon`).style.display = 'none';
            document.getElementById(`team-name-${teamId}-save-icons`).style.display = 'inline'
        });

        teamNameField.addEventListener('focusout', function (event) {
            if (event.relatedTarget !== null && event.relatedTarget.id === `team-name-${teamId}-confirm-icon`) {
                previousTeamName = teamNameField.textContent;
                document.getElementById(`team-name-${teamId}-save-icons`).style.display = 'none';
                document.getElementById(`team-name-${teamId}-loading-icon`).style.display = 'inline'
                changeTeamName(teamNameField.textContent);
                return;
            }
            document.getElementById(`team-name-${teamId}-edit-icon`).style.display = 'inline'
            document.getElementById(`team-name-${teamId}-save-icons`).style.display = 'none';
            teamNameField.textContent = previousTeamName;
        });

        teamNameField.addEventListener('keydown', function (event) {
            if (event.key === "Enter") {
                event.preventDefault();
                previousTeamName = teamNameField.textContent;
                changeTeamName(teamNameField.textContent);
                document.getElementById(`team-name-${teamId}-save-icons`).style.display = 'none';
                document.getElementById(`team-name-${teamId}-loading-icon`).style.display = 'inline'
                teamNameField.blur();
            }
        });

        teamShortNameField.addEventListener('focusin', function () {
            document.getElementById(`team-short-name-${teamId}-edit-icon`).style.display = 'none';
            document.getElementById(`team-short-name-${teamId}-save-icons`).style.display = 'inline'
        });

        teamShortNameField.addEventListener('focusout', function (event) {
            if (event.relatedTarget !== null && event.relatedTarget.id === `team-short-name-${teamId}-confirm-icon`) {
                previousTeamShortName = teamShortNameField.textContent;
                document.getElementById(`team-short-name-${teamId}-save-icons`).style.display = 'none';
                document.getElementById(`team-short-name-${teamId}-loading-icon`).style.display = 'inline'
                changeTeamShortName(teamShortNameField.textContent);
                return;
            }
            document.getElementById(`team-short-name-${teamId}-edit-icon`).style.display = 'inline'
            document.getElementById(`team-short-name-${teamId}-save-icons`).style.display = 'none';
            teamShortNameField.textContent = previousTeamShortName;
        });

        teamShortNameField.addEventListener('keydown', function (event) {
            if (event.key === "Enter") {
                event.preventDefault();
                previousTeamShortName = teamShortNameField.textContent;
                changeTeamShortName(teamShortNameField.textContent);
                document.getElementById(`team-short-name-${teamId}-save-icons`).style.display = 'none';
                document.getElementById(`team-short-name-${teamId}-loading-icon`).style.display = 'inline'
                teamShortNameField.blur();
            }
        });


        // Add a click event on buttons to open a specific modal
        document.querySelectorAll('.js-modal-trigger').forEach((trigger) => {
            const modal = trigger.dataset.target;
            const target = document.getElementById(modal);

            trigger.addEventListener('click', () => {
                openModal(target);
            });

            if (trigger.id === "edit-patrol-trigger") {
                trigger.addEventListener('click', () => {
                    target.dataset.patrolId = trigger.dataset.patrolId;
                    document.getElementById('edit-patrol-modal-input').value = trigger.dataset.patrolName;
                });
            } else if (trigger.id === "delete-patrol-trigger") {
                trigger.addEventListener('click', () => {
                    target.dataset.patrolId = trigger.dataset.patrolId;
                    document.getElementById('delete-patrol-message').textContent = `Czy na pewno chcesz usunąć zastęp "${trigger.dataset.patrolName}"?`;
                });
            }
        });

        // Add a click event on various child elements to close the parent modal
        document.querySelectorAll('.modal-background, .modal-close, .modal-card-head .delete, .modal-card-foot .button').forEach((close) => {
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

        // Add a click event to switch to graph view
        document.getElementById('graph-view-button').addEventListener('click', () => {
            const url = new URL(window.location.href);
            url.searchParams.set('graph', 'true');
            location.href = url;
        });
    }
);
