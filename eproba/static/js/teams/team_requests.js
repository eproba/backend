let districts

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

async function fetchUsers(teamId) {
    return await fetchData(`/api/users/?team=${teamId}`);
}

async function acceptTeam(teamId) {
    const response = await fetch(`/api/teams/${teamId}/`, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({is_verified: true})
    });
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    } else {
        window.location.reload();
    }
    return await response.json();
}

function createCard(team, users) {
    const card = document.createElement('div');
    card.classList.add('card');
    card.innerHTML = `
        <div class="card-content">
            <p class="title">${team.name}</p>
            <p class="subtitle mb-0">${team.short_name}</p>
            <p class="subtitle">${districts.find(d => d.id === team.district) ? districts.find(d => d.id === team.district).name : 'Nieznany okręg'}</p>
            <div class="content">
                <p><strong>Zastępy:</strong> ${team.patrols.map(p => p.name).join(', ')}</p>
                <p><strong>Obecni członkowie:</strong> 
                    ${users.map(u => `<span class="${u.email_verified ? 'has-text-success' : 'has-text-danger'}">${u.first_name} ${u.last_name} - ${u.nickname}</span>`).join(', ')}
                </p>
            </div>
        </div>
        <footer class="card-footer">
            <a class="card-footer-item has-text-success" href="#" onclick="acceptTeam('${team.id}'); return false;">Akceptuj</a>
        </footer>
    `;
    return card;
}

async function fetchTeamRequests() {
    const teamRequests = document.getElementById('team-requests');
    try {
        const teams = await fetchData('/api/teams/?is_verified=false&with_patrols=true');
        await fetchDistricts();
        if (teams.length === 0) {
            teamRequests.innerHTML = '<p class="has-text-centered">Brak nowych zgłoszeń drużyn.</p>';
        } else {
            teamRequests.innerHTML = '';
            for (const team of teams) {
                const users = await fetchUsers(team.id);
                const card = createCard(team, users);
                teamRequests.appendChild(card);
            }
        }
    } catch (error) {
        console.error(error);
        teamRequests.innerHTML = '<p class="has-text-centered has-text-danger">Wystąpił błąd podczas pobierania zgłoszeń. Odśwież stronę i spróbuj ponownie.</p>';
    }
}

document.addEventListener('DOMContentLoaded', fetchTeamRequests);
