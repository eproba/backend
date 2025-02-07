function sanitizeFilename(filename) {
    // Regular expression to match forbidden characters
    const forbiddenChars = /[<>:"\/\\|?*]/g;
    // Replace forbidden characters with an empty string
    return filename.replace(forbiddenChars, '');
}

document.addEventListener('DOMContentLoaded', function () {
    const buttons = [
        {
            id: 'export_all_user_worksheets_button',
            container: 'user_worksheets_div',
            zipBaseName: 'eksport_z_twoich_prob'
        },
        {
            id: 'export_all_team_worksheets_button',
            container: 'team_worksheets_div',
            zipBaseName: 'eksport_z_prob_druzyny'
        },
        {
            id: 'export_all_patrol_worksheets_button',
            container: 'patrol_worksheets_div',
            zipBaseName: 'eksport_z_prob_zastepu'
        },
        {
            id: 'export_all_archived_user_worksheets_button',
            container: 'archived_user_worksheets_div',
            zipBaseName: 'eksport_z_twoich_prob_z_archiwum'
        },
        {
            id: 'export_all_archived_team_worksheets_button',
            container: 'archived_team_worksheets_div',
            zipBaseName: 'eksport_z_prob_druzyny_z_archiwum'
        },
        {
            id: 'export_all_archived_patrol_worksheets_button',
            container: 'archived_patrol_worksheets_div',
            zipBaseName: 'eksport_z_prob_zastepu_z_archiwum'
        },
    ];

    buttons.forEach(function (button) {
        const element = document.getElementById(button.id);
        if (element) {
            element.addEventListener('click', function () {
                exportWorksheets(button.container);
            });
        }
    });
});


async function exportWorksheets(worksheetContainerId, zipBaseName) {
    const modal = document.getElementById('progress_modal');
    const errorModal = document.getElementById('error_modal');
    const progressBar = document.getElementById('progress_bar');
    const progressText = document.getElementById('progress_text');
    modal.classList.add('is-active');

    const zip = new JSZip();
    const worksheetContainer = document.getElementById(worksheetContainerId);
    const worksheets = worksheetContainer.getElementsByClassName('worksheet');
    const totalWorksheets = worksheets.length;

    const abortController = new AbortController(); // Step 1

    function cancelExport() {
        abortController.abort(); // Abort the fetch request
        modal.classList.remove('is-active');
        progressBar.value = 0;
        progressText.textContent = '0%';
        document.getElementById('cancel_export_button').removeEventListener('click', cancelExport);
    }

    document.getElementById('cancel_export_button').addEventListener('click', cancelExport); // Step 3

    for (let i = 0; i < totalWorksheets; i++) {
        const worksheet = worksheets[i];
        const pdfUrl = worksheet.getAttribute('data-pdf-url');

        try {
            const response = await fetch(pdfUrl, {signal: abortController.signal}); // Step 2
            if (!response.ok) throw new Error('Network response was not ok.');
            const blob = await response.blob();

            const fileName = `Epróba - ${worksheet.querySelector('.title').textContent} (ID:${worksheet.id.split('_')[1]}).pdf`;
            zip.file(sanitizeFilename(fileName), blob);

            const progress = Math.round(((i + 1) / totalWorksheets) * 100);
            progressBar.value = progress;
            progressText.textContent = `${progress}%`;

        } catch (error) {
            if (error.name === 'AbortError') { // Step 5
                console.log('Export aborted by the user.');
                document.getElementById('error_text').textContent = 'Eksportowanie zostało anulowane przez użytkownika.';
                errorModal.classList.add('is-active');
                break; // Exit the loop
            } else {
                console.error('There was a problem with the fetch operation:', error);
                document.getElementById('error_text').textContent = 'Wystąpił błąd podczas eksportowania prób. Spróbuj ponownie później.';
                errorModal.classList.add('is-active');
            }
        }
    }


    try {
        if (!abortController.signal.aborted && Object.keys(zip.files).length !== 0) {

            const content = await zip.generateAsync({type: 'blob'});
            const zipName = `${zipBaseName || 'eksport'}_${new Date().toISOString().split('T')[0]} (Epróba).zip`;

            const link = document.createElement('a');
            link.href = URL.createObjectURL(content);
            link.download = zipName;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    } catch (error) {
        console.error('There was a problem with the zip generation:', error);
        document.getElementById('error_text').textContent = 'Wystąpił błąd podczas generowania pliku ZIP. Spróbuj ponownie później.';
        errorModal.classList.add('is-active');
    }

    // Cleanup
    modal.classList.remove('is-active');
    progressBar.value = 0;
    progressText.textContent = '0%';
    document.getElementById('cancel_export_button').removeEventListener('click', cancelExport); // Step 4
}

