function filterByPatrol(patrolId) {
    let worksheets = document.getElementsByClassName("worksheet");
    for (let i = 0; i < worksheets.length; i++) {
        let worksheet = worksheets[i];
        let worksheetTitle = worksheet.querySelector(".title").textContent.toLowerCase();
        let searchQuery = document.getElementById("worksheet_searchbar").value.toLowerCase();
        if ((worksheet.dataset.patrolId === patrolId || patrolId === "all") && worksheetTitle.indexOf(searchQuery) > -1) {
            worksheet.classList.add("show");
        } else {
            worksheet.classList.remove("show");
        }
    }
}

function filterByName(searchQuery) {
    let worksheets = document.getElementsByClassName("worksheet");
    const selectedPatrolId = document.getElementById('patrol_selector').value;
    for (let i = 0; i < worksheets.length; i++) {
        let worksheet = worksheets[i];
        let worksheetTitle = worksheet.querySelector(".title").textContent.toLowerCase();
        if (worksheetTitle.indexOf(searchQuery.toLowerCase()) > -1 && (selectedPatrolId === "all" || worksheet.dataset.patrolId === selectedPatrolId)) {
            worksheet.classList.add("show");
        } else {
            worksheet.classList.remove("show");
        }
    }
}
