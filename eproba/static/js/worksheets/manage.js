const API = {
    get: async (endpoint) => {
        try {
            const response = await fetch(endpoint);
            return await response.json();
        } catch (error) {
            console.error(`Error fetching ${endpoint}:`, error);
            return [];
        }
    },
    post: async (endpoint, body) => {
        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {'Content-Type': 'application/json', 'X-CSRFToken': csrfToken},
                body: JSON.stringify(body)
            });
            return await response.json();
        } catch (error) {
            console.error(`Error posting to ${endpoint}:`, error);
            return null;
        }
    },
    patch: async (endpoint, body) => {
        try {
            const response = await fetch(endpoint, {
                method: 'PATCH',
                headers: {'Content-Type': 'application/json', 'X-CSRFToken': csrfToken},
                body: JSON.stringify(body)
            });
            return await response.json();
        } catch (error) {
            console.error(`Error patching ${endpoint}:`, error);
            return null;
        }
    },
    delete: async (endpoint) => {
        try {
            const response = await fetch(endpoint, {method: 'DELETE', headers: {'X-CSRFToken': csrfToken}});
            return response.ok;
        } catch (error) {
            console.error(`Error deleting ${endpoint}:`, error);
            return false;
        }
    }
};

async function deleteWorksheet(worksheetId) {
    const confirmed = confirm('Czy na pewno chcesz usunąć tę próbę?');
    if (!confirmed) return;

    const success = await API.delete(`/api/worksheets/${worksheetId}/`);
    if (success) {
        document.getElementById(`worksheet_${worksheetId}`).remove();
        alert('Próba została pomyślnie usunięta.');
    } else {
        alert('Wystąpił problem podczas usuwania próby. Spróbuj ponownie później.');
    }
}

async function archiveWorksheet(worksheetId) {
    const confirmed = confirm('Czy na pewno chcesz zarchiwizować tę próbę?');
    if (!confirmed) return;

    const success = await API.patch(`/api/worksheets/${worksheetId}/`, {is_archived: true});
    if (success) {
        document.getElementById(`worksheet_${worksheetId}`).remove()
        alert('Próba została pomyślnie zarchiwizowana.');
    } else {
        alert('Wystąpił problem podczas archiwizowania próby. Spróbuj ponownie później.');
    }
}

async function fetchWorksheets() {
    return API.get('/api/worksheets/');
}

function calculatePercentage(tasks) {
    const totalTasks = tasks.length;
    const completedTasks = tasks.filter(task => task.status === 2).length;

    return totalTasks ? `${Math.round((completedTasks / totalTasks) * 100)}%` : "Nie masz jeszcze dodanych żadnych zadań";
}

function createElement(tag, {id = '', className = '', innerHTML = '', attributes = {}} = {}) {
    const element = document.createElement(tag);
    if (id) element.id = id;
    if (className) element.className = className;
    if (innerHTML) element.innerHTML = innerHTML;
    Object.entries(attributes).forEach(([key, value]) => element.setAttribute(key, value));
    return element;
}

function appendToParent(parent, child) {
    parent.appendChild(child);
}

function renderNoWorksheetsMessage(parent) {
    const messageDiv = createElement('div', {
        className: 'worksheets-container',
        innerHTML: '<div class="box">W systemie nie ma jeszcze żadnej próby którą możesz edytować.</div>'
    });
    appendToParent(parent, messageDiv);
}

function sortWorksheets(worksheets) {
    return worksheets.sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at));
}

function renderWorksheets(worksheets) {
    const worksheetsList = document.getElementById('worksheets-list');
    document.getElementById('loading').style.display = 'none';

    if (!worksheets.length) {
        return renderNoWorksheetsMessage(worksheetsList);
    }

    const sortedWorksheets = sortWorksheets(worksheets);

    sortedWorksheets
        .filter(worksheet => !worksheet.deleted)
        .forEach(worksheet => appendToParent(worksheetsList, renderWorksheet(worksheet)));
}

function renderWorksheet(worksheet) {
    const {id, name, description, tasks, supervisor, supervisor_name, updated_at} = worksheet;
    return createElement('div', {
        id: `worksheet_${id}`,
        className: 'block worksheet show',
        attributes: {
            'data-tasks-count': tasks.length,
            'data-completed-tasks-count': tasks.filter(task => task.status === 2).length,
            'data-patrol-id': worksheet.user.patrol
        },
        innerHTML: `
            <div class="box">
                <div class="level mb-1">
                            <div class="level-left">
                    <span class="level-item title has-text-weight-medium" style="margin-bottom: 0" id="worksheet-title_${id}">${name} - ${renderUserInfo(worksheet.user)}</span>
                    </div>
                    <div class="level-right">
                    <div class="level-right is-gapless is-flex-direction-row\t">${renderWorksheetActions(worksheet)}</div>
                    </div>
                </div>
                ${supervisor ? `<h2 class="subtitle mb-2" id="worksheet_supervisor_${id}">Opiekun próby: <a href="/profile/view/${supervisor}">${supervisor_name}</a></h2>` : ''}
                <h2 class="subtitle is-6">Ostatnia edycja: <span id="worksheet-updated_${id}">${(new Date(updated_at)).toLocaleString()}</span></h2>
                ${description ? `<p>${description}</p>` : ''}
                <p><br/></p>
                <div style="overflow-x: auto;">
                ${renderTasksTable(worksheet)}
                </div>
            </div>
        `
    });
}

function renderUserInfo(user) {
    return `${user.rank} ${user.nickname || user.first_name + ' ' + user.last_name}`;
}


function renderWorksheetActions(worksheet) {

    return `
        <span class="level-item icon has-tooltip-bottom has-tooltip-arrow" id="tooltip_text_${worksheet.id}" data-tooltip="Naciśnij aby skopiować link do próby">
            <span onclick="copy_to_clipboard('tooltip_text_${worksheet.id}', '${location.host}/worksheets/share/view/${worksheet.id}')">
                <i class="fa-solid fa-clipboard"></i>
            </span>
        </span>
        <span class="level-item icon has-tooltip-bottom has-tooltip-arrow" id="tooltip_text_${worksheet.id}_print" data-tooltip="Drukuj próbę">
            <span onclick="location.href='/worksheets/print/${worksheet.id}'">
                <i class="fas fa-print"></i>
            </span>
        </span>
        <span class="level-item icon has-tooltip-bottom has-tooltip-arrow" data-tooltip="Zarchiwizuj próbę">
            <span onclick="archiveWorksheet('${worksheet.id}')">
                <i class="fa-solid fa-box-archive"></i>
            </span>
        </span>
        ${userFunction > 2 ? renderDeleteWorksheetAction(worksheet.id) : ''}
        <span class="level-item icon has-tooltip-bottom has-tooltip-arrow" data-tooltip="Edytuj próbę">
            <span onclick="location.href='/worksheets/edit/${worksheet.id}'">
                <i class="fas fa-edit"></i>
            </span>
        </span>
    `;
}

function renderDeleteWorksheetAction(id) {
    return `
        <span class="level-item icon has-tooltip-bottom has-tooltip-arrow" data-tooltip="Usuń próbę">
            <span onclick="deleteWorksheet('${id}')">
                <i class="fa-solid fa-trash"></i>
            </span>
        </span>
    `;
}

function renderTasksTable(worksheet) {
    const showDescription = worksheet.tasks.some(task => task.description);
    return `
        <table class="table">
            <thead>
                <tr>
                    <th class="is-narrow">Lp.</th>
                    <th>Zadanie</th>
                    ${showDescription ? '<th>Opis</th>' : ''}
                    <th style="width:4rem">Status</th>
                    <th style="width:4rem">Akcja</th>
                </tr>
            </thead>
            <tfoot>
                <tr>
                    <th></th>
                    <th></th>
                    ${showDescription ? '<th></th>' : ''}
                    <th></th>
                    <th>
                        <span class="has-tooltip-arrow has-tooltip-left has-tooltip-primary" data-tooltip="Procent wykonanych zadań" id="worksheet-percentage_${worksheet.id}">
                            ${calculatePercentage(worksheet.tasks)}
                        </span>
                    </th>
                </tr>
            </tfoot>
            <tbody>
                ${renderTasks(worksheet, showDescription)}
            </tbody>
        </table>
    `;
}

function renderTasks(worksheet, showDescription = false) {
    return worksheet.tasks.map((task, i) => `
        <tr>
            <td>${i + 1}</td>
            <td>${task.task}</td>
            ${showDescription ? `<td>${task.description}</td>` : ''}
            <td class="task-status">
                ${renderTaskStatus(task)}
            </td>
            <td class="task-action">
                <span class="has-tooltip-arrow has-tooltip-left has-tooltip-success" data-tooltip="Zatwierdź zadanie">
                    <a onclick="updateTaskStatus('${worksheet.id}', '${task.id}', 2, 'Czy na pewno chcesz zatwierdzić to zadanie?')">
                        <i class="far fa-check-circle" style="color:green;"></i>
                    </a>
                </span>
                <span class="has-tooltip-arrow has-tooltip-left has-tooltip-danger" data-tooltip="Odrzuć zadanie">
                    <a onclick="updateTaskStatus('${worksheet.id}', '${task.id}', 3, 'Czy na pewno chcesz odrzucić to zadanie?')">
                        <i class="far fa-times-circle" style="color:red;"></i>
                    </a>
                </span>
            </td>
        </tr>
    `).join('');
}

function renderTaskStatus(task) {
    const {id, status, approver_name, approval_date} = task;
    const iconClass = status === 3 ? 'fa-circle-xmark' : status === 2 ? 'fa-check-circle' : status === 1 ? 'fa-clock' : '';
    let tooltipMessage = "";
    switch (status) {
        case 3  :
            tooltipMessage = `${approver_name}  odrzucił ${(new Date(approval_date)).toLocaleString()}`;
            break;
        case 2:
            tooltipMessage = `${approver_name}  zatwierdził ${(new Date(approval_date)).toLocaleString()}`;
            break;
        case 1:
            tooltipMessage = `Zadanie oczekuje na zatwierdzenie ${approver_name} od ${(new Date(approval_date)).toLocaleString()}`;
            break;
        default:
            break;
    }
    return `
    <div id="status-icon_${id}" data-status="${status}">
        <span class="icon ${tooltipMessage ? 'has-tooltip-arrow has-tooltip-bottom has-tooltip-multiline' : ''}" id="status-icon-tooltip_${id}" ${tooltipMessage ? `data-tooltip="${tooltipMessage}"` : ''}>
            <i class="far ${iconClass}""></i>
        </span>
    </div>
    `;
}

async function updateTaskStatus(worksheetId, taskId, newStatus, message) {
    if (!message || confirm(message)) {
        const statusIcon = document.getElementById(`status-icon_${taskId}`);
        const oldStatus = parseInt(statusIcon.dataset.status);
        statusIcon.innerHTML = `<span class="has-tooltip-arrow has-tooltip-left" data-tooltip="Ładowanie"><i class="fas fa-spinner fa-spin"></i></span>`;

        const endpoint = `/api/worksheets/${worksheetId}/task/${taskId}/`;
        const success = await API.patch(endpoint, {status: newStatus});

        if (success) {
            statusIcon.outerHTML = renderTaskStatus({
                id: taskId,
                status: newStatus,
                approver: userId,
                approval_date: new Date()
            }, [], []);
            if (oldStatus !== newStatus) {
                const completedTasksCount = parseInt(document.getElementById(`worksheet_${worksheetId}`).dataset.completedTasksCount);
                document.getElementById(`worksheet_${worksheetId}`).dataset.completedTasksCount = completedTasksCount + (oldStatus === 2 ? -1 : 0) + (newStatus === 2 ? 1 : 0);
                updateWorksheetPercentage(worksheetId);
            }
            document.getElementById(`worksheet-updated_${worksheetId}`).innerHTML = (new Date()).toLocaleString();
            alert(`Zadanie zostało ${newStatus === 2 ? 'zatwierdzone' : 'odrzucone'}.`);
        } else {
            showErrorStatus(statusIcon);
        }
    }
}

function updateWorksheetPercentage(worksheetId) {
    const worksheetElement = document.getElementById(`worksheet_${worksheetId}`);
    const completedTasksCount = parseInt(worksheetElement.dataset.completedTasksCount);
    const totalTasksCount = parseInt(worksheetElement.dataset.tasksCount);
    document.getElementById(`worksheet-percentage_${worksheetId}`).innerHTML = Math.round((completedTasksCount / totalTasksCount) * 100) + "%";
}

function showErrorStatus(statusIcon) {
    statusIcon.innerHTML = `<span class="has-tooltip-arrow has-tooltip-left has-tooltip-danger" data-tooltip="Wystąpił błąd"><i class="fas fa-exclamation-circle bounce" style="color:red;"></i></span>`;
    alert("Wystąpił błąd przy edycji zadania, spróbuj ponownie później.");
}


(async () => {
    const worksheets = await fetchWorksheets();
    renderWorksheets(worksheets);
})();
