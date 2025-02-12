// Helper function to fetch data from a given URL
async function fetchData(url) {
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
}

// Helper function to update select options
function updateSelectOptions(selectElement, options, defaultOptionText) {
    selectElement.innerHTML = `<option value="" selected disabled hidden>${defaultOptionText}</option>`;
    options.forEach(option => {
        const opt = document.createElement('option');
        opt.value = option.id;
        opt.textContent = option.name;
        selectElement.appendChild(opt);
    });
}

// Helper function to handle errors
function handleError(element, helpElement, errorMessage) {
    console.error(errorMessage);
    helpElement.classList.remove('is-hidden');
    helpElement.textContent = errorMessage;
    helpElement.classList.add('is-danger');
    element.disabled = true;
    element.innerHTML = `<option value="" selected disabled hidden>Wybierz drużynę</option>`;
}

async function handleDistrictChange(districtSelect, teamSelect, patrolSelect, submitButton, teamSelectHelp) {
    teamSelect.parentElement.classList.add('is-loading');
    const districtId = districtSelect.value;
    submitButton.disabled = true;
    try {
        const teams = await fetchData(`/api/teams/?district=${districtId}&is_verified=true`);
        updateSelectOptions(teamSelect, teams, 'Wybierz drużynę');
        patrolSelect.innerHTML = '<option value="" selected disabled hidden>Wybierz zastęp</option>';
        patrolSelect.disabled = true;
        if (teams.length === 0) {
            teamSelectHelp.classList.remove('is-hidden');
            teamSelectHelp.innerHTML = 'Brak drużyn w tym okręgu, jeśli należysz do kadry swojej drużyny możesz dodać ją <a href="/team/request/">tutaj</a>.';
            teamSelectHelp.classList.add('is-danger');
            teamSelect.disabled = true;
        } else {
            teamSelect.disabled = false;
            teamSelectHelp.classList.remove('is-danger');
            teamSelectHelp.classList.remove('is-hidden');
            teamSelectHelp.innerHTML = 'Nie widzisz swojej drużyny? Członkowie kadry mogą dodać ją <a href="/team/request/">tutaj</a>.';
        }
    } catch (error) {
        handleError(teamSelect, teamSelectHelp, 'Wystąpił błąd podczas pobierania drużyn. Odśwież stronę i spróbuj ponownie.');
    } finally {
        teamSelect.parentElement.classList.remove('is-loading');
    }
}

async function handleTeamChange(teamSelect, patrolSelect, patrolSelectHelp, submitButton, team = null) {
    patrolSelect.parentElement.classList.add('is-loading');
    const teamId = teamSelect.value;
    try {
        if (!team) {
            team = await fetchData(`/api/teams/${teamId}/`);
        }
        updateSelectOptions(patrolSelect, team.patrols, 'Wybierz zastęp');
        if (team.patrols.length === 0) {
            patrolSelectHelp.classList.remove('is-hidden');
            patrolSelectHelp.innerHTML = 'Brak zastępów w tej drużynie, jeśli należysz do kadry swojej drużyny możesz dodać je <a href="/team/">tutaj</a>.';
            patrolSelectHelp.classList.add('is-danger');
            patrolSelect.disabled = true;
        } else {
            patrolSelect.disabled = false;
            patrolSelectHelp.classList.remove('is-danger');
            patrolSelectHelp.classList.remove('is-hidden');
            patrolSelectHelp.innerHTML = 'Nie widzisz swojego zastępu? Członkowie kadry mogą dodać go <a href="/team/">tutaj</a>.';
        }
    } catch (error) {
        handleError(patrolSelect, patrolSelectHelp, 'Wystąpił błąd podczas pobierania zastępów. Odśwież stronę i spróbuj ponownie.');
        submitButton.disabled = true;
    } finally {
        patrolSelect.parentElement.classList.remove('is-loading');
    }
}

document.addEventListener('DOMContentLoaded', async function () {
    const districtSelect = document.getElementById('district-select');
    const teamSelect = document.getElementById('team-select');
    const patrolSelect = document.getElementById('patrol-select');
    const submitButton = document.getElementById('submit-button');
    const teamSelectHelp = document.getElementById('team-select-help');
    const patrolSelectHelp = document.getElementById('patrol-select-help');

    const query = new URLSearchParams(window.location.search);
    const initialDistrictId = query.get('district') || sessionStorage.getItem('district');
    const initialTeamId = query.get('team') || sessionStorage.getItem('team');
    const initialPatrolId = query.get('patrol') || sessionStorage.getItem('patrol');
    sessionStorage.removeItem('district');
    sessionStorage.removeItem('team');
    sessionStorage.removeItem('patrol');

    districtSelect.addEventListener('change', async function () {
        await handleDistrictChange(districtSelect, teamSelect, patrolSelect, submitButton, teamSelectHelp);
    });

    teamSelect.addEventListener('change', async function () {
        await handleTeamChange(teamSelect, patrolSelect, patrolSelectHelp, submitButton);
    });

    patrolSelect.addEventListener('change', function () {
        submitButton.disabled = false;
    });

    if (initialDistrictId) {
        districtSelect.value = districtId;
        districtSelect.dispatchEvent(new Event('change'));
    }

    if (initialTeamId) {
        const team = await fetchData(`/api/teams/${initialTeamId}/`);
        districtSelect.value = team.district.id;
        await handleDistrictChange(districtSelect, teamSelect, patrolSelect, submitButton, teamSelectHelp);
        if (![...teamSelect.options].map(option => option.value).includes(initialTeamId)) {
            teamSelect.appendChild(new Option(team.name, team.id));
        }
        teamSelect.value = initialTeamId;
        await handleTeamChange(teamSelect, patrolSelect, patrolSelectHelp, submitButton, team);
    }

    if (initialPatrolId) {
        const patrol = await fetchData(`/api/patrols/${initialPatrolId}/`);
        console.log(patrol);
        const team = await fetchData(`/api/teams/${patrol.team}/`);
        console.log(team);
        districtSelect.value = team.district.id;
        await handleDistrictChange(districtSelect, teamSelect, patrolSelect, submitButton, teamSelectHelp);
        if (![...teamSelect.options].map(option => option.value).includes(initialTeamId)) {
            teamSelect.appendChild(new Option(team.name, team.id));
        }
        teamSelect.value = team.id;
        await handleTeamChange(teamSelect, patrolSelect, patrolSelectHelp, submitButton, team);
        patrolSelect.value = initialPatrolId;
        submitButton.disabled = false;
    }
});
