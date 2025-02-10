let districts = [];
let selectedStatuses = ["submitted", "pending_verification"];

const FUNCTION_LEVELS = {
    3: "Przyboczny",
    4: "Drużynowy",
    5: "Wyższa funkcja"
}

async function fetchData(url) {
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
}

async function fetchDistricts() {
    districts = await fetchData('/api/districts/');
}

async function saveTeamRequest(teamId) {
    const card = document.getElementById(`team-card-${teamId}`);
    const note = card.querySelector('textarea').value.trim();
    const sendEmail = card.querySelector('input[name="send_email"]').checked;
    const sendNote = card.querySelector('input[name="send_note"]').checked;
    const status = card.querySelector('select').value;

    document.getElementById(`save-button-${teamId}`).classList.add('is-loading');

    const response = await fetch(`/api/team-requests/${teamId}/`, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({note, send_email: sendEmail, send_note: sendNote, status})
    });

    if (!response.ok) {
        alert("Wystąpił błąd podczas zapisywania.");
        return;
    }

    // Odświeżenie danych na stronie
    fetchTeamRequests();
}

function createRequestCard(request) {
    const card = document.createElement('div');
    card.classList.add('card');
    card.id = `team-card-${request.id}`;

    card.innerHTML = `
        <div class="card-content">
            <p class="title">${request.team.name}</p>
            <p class="subtitle mb-0">${request.team.short_name}</p>
            <p class="subtitle">${request.team.district?.name || "Brak danych"}</p>
            
            <div class="content">
                <p><strong>Wnioskodawca:</strong> ${request.created_by.first_name} ${request.created_by.last_name} "${request.created_by.nickname}" <span class="${request.created_by.email_verified ? 'has-text-success' : 'has-text-danger'}">${request.created_by.email}</span></p>
                <p><strong>Data zgłoszenia:</strong> ${new Date(request.created_at).toLocaleString()}</p>
                <p><strong>Zastępy:</strong> ${request.team.patrols.map(patrol => patrol.name).join(', ')}</p>
                <p><strong>Funkcja:</strong> ${FUNCTION_LEVELS[request.function_level]}</p>
            </div>
            
            <div class="content">
                <p><strong>Status:</strong></p>
                <div class="select">
                    <select>
                        <option value="submitted" ${request.status === "submitted" ? "selected" : ""}>Zgłoszone</option>
                        <option value="approved" ${request.status === "approved" ? "selected" : ""}>Zaakceptowane</option>
                        <option value="rejected" ${request.status === "rejected" ? "selected" : ""}>Odrzucone</option>
                        <option value="pending_verification" ${request.status === "pending_verification" ? "selected" : ""}>Oczekuje na dodatkową weryfikację</option>
                    </select>
                </div>

                <p class="mt-4"><strong>Notatka:</strong></p>
                <textarea class="textarea" placeholder="Dodaj notatkę (opcjonalnie)">${request.note || ""}</textarea>

                <label class="checkbox mt-4">
                    <input type="checkbox" name="send_email"> Wyślij e-mail z powiadomieniem
                </label>
                <br>
                <label class="checkbox mt-2">
                    <input type="checkbox" name="send_note"> Wyślij notatkę mailem
                </label>

                <div class="mt-4">
                    <button class="button is-success" onclick="saveTeamRequest('${request.id}')" id="save-button-${request.id}">Zapisz</button>
                </div>
            </div>
        </div>
    `;

    return card;
}

async function fetchTeamRequests() {
    const teamRequests = document.getElementById('team-requests');
    try {
        let requests = await fetchData('/api/team-requests/');
        await fetchDistricts();

        // Filtrowanie po statusie
        if (!selectedStatuses.includes("all")) {
            requests = requests.filter(request => selectedStatuses.includes(request.status));
        }

        if (requests.length === 0) {
            teamRequests.innerHTML = '<p class="has-text-centered">Brak zgłoszeń pasujących do filtra.</p>';
        } else {
            teamRequests.innerHTML = '';
            requests.forEach(request => {
                const card = createRequestCard(request);
                teamRequests.appendChild(card);
            });
        }
    } catch (error) {
        console.error(error);
        teamRequests.innerHTML = '<p class="has-text-centered has-text-danger">Błąd ładowania zgłoszeń.</p>';
    }
}

function handleStatusFilterChange() {
    let selectedStatus = this.value;
    let statusesToFilter = selectedStatus === "submitted_pending_verification" ? ["submitted", "pending_verification"] : [selectedStatus];
    selectedStatuses = statusesToFilter;

    fetchTeamRequests();
}

document.addEventListener('DOMContentLoaded', () => {
    fetchTeamRequests();

    document.getElementById('status-filter').value = "submitted_pending_verification";
    document.getElementById('status-filter').addEventListener('change', handleStatusFilterChange);
});