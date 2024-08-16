function confirm_popup(url = null, message = "", fun = null) {
    if (confirm(message)) {
        if (!url && fun) {
            fun()
        } else {
            location.href = url;
        }
    }
}

function fallbackCopyTextToClipboard(text, id) {
    const textArea = document.createElement("textarea");
    textArea.value = text;

    // Avoid scrolling to bottom
    textArea.style.top = "0";
    textArea.style.left = "0";
    textArea.style.position = "fixed";

    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();

    const old_tooltip = document.getElementById(id).getAttribute("data-tooltip");
    try {
        const successful = document.execCommand('copy');
        const msg = successful ? 'Skopiowano do schowka' : 'Nie udało się skopiować';
        document.getElementById(id).setAttribute("data-tooltip", msg);
        setTimeout(() => {
            document.getElementById(id).setAttribute("data-tooltip", old_tooltip);
        }, 5000);
    } catch (err) {
        console.error('Fallback: Oops, unable to copy', err);
        document.getElementById(id).setAttribute("data-tooltip", 'Wystąpił błąd i nie udało się skopiować');
        setTimeout(() => {
            document.getElementById(id).setAttribute("data-tooltip", old_tooltip);
        }, 5000);
    }

    document.body.removeChild(textArea);
}

function copy_to_clipboard(id, text) {
    if (!navigator.clipboard) {
        fallbackCopyTextToClipboard(text, id);
        return;
    }
    navigator.clipboard.writeText(text)
    const old_tooltip = document.getElementById(id).getAttribute("data-tooltip");
    document.getElementById(id).setAttribute("data-tooltip", "Skopiowano do schowka");
    setTimeout(() => {
        document.getElementById(id).setAttribute("data-tooltip", old_tooltip);
    }, 5000);
}