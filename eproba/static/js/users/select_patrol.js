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

document.addEventListener('DOMContentLoaded', function () {
    const districtSelect = document.getElementById('district-select');
    const teamSelect = document.getElementById('team-select');
    const patrolSelect = document.getElementById('patrol-select');
    const submitButton = document.getElementById('submit-button');
    const teamSelectHelp = document.getElementById('team-select-help');
    const patrolSelectHelp = document.getElementById('patrol-select-help');

    districtSelect.addEventListener('change', async function () {
        teamSelect.parentElement.classList.add('is-loading');
        const districtId = districtSelect.value;
        submitButton.disabled = true;
        try {
            const teams = await fetchData(`/api/teams/?district=${districtId}`);
            updateSelectOptions(teamSelect, teams, 'Wybierz drużynę');
            patrolSelect.innerHTML = '<option value="" selected disabled hidden>Wybierz zastęp</option>';
            patrolSelect.disabled = true;
            if (teams.length === 0) {
                teamSelectHelp.classList.remove('is-hidden');
                teamSelectHelp.innerHTML = 'Brak drużyn w tym okręgu, jeśli należysz do kadry swojej drużyny możesz dodać ją <a href="/register-team/">tutaj</a>.';
                teamSelectHelp.classList.add('is-danger');
                teamSelect.disabled = true;
            } else {
                teamSelect.disabled = false;
                teamSelectHelp.classList.remove('is-danger');
                teamSelectHelp.classList.remove('is-hidden');
                teamSelectHelp.innerHTML = 'Nie widzisz swojej drużyny? Członkowie kadry mogą dodać ją <a href="/register-team/">tutaj</a>.';
            }
        } catch (error) {
            handleError(teamSelect, teamSelectHelp, 'Wystąpił błąd podczas pobierania drużyn. Odśwież stronę i spróbuj ponownie.');
        } finally {
            teamSelect.parentElement.classList.remove('is-loading');
        }
    });

    teamSelect.addEventListener('change', async function () {
        patrolSelect.parentElement.classList.add('is-loading');
        const teamId = teamSelect.value;
        try {
            const patrols = await fetchData(`/api/teams/${teamId}/`);
            updateSelectOptions(patrolSelect, patrols.patrols, 'Wybierz zastęp');
            if (patrols.patrols.length === 0) {
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
    });

    patrolSelect.addEventListener('change', function () {
        submitButton.disabled = false;
    });
});