function updateElementIndex(el, prefix, ndx) {
    const idRegex = new RegExp(`(${prefix}-\\d+)`);
    const replacement = `${prefix}-${ndx}`;
    if (el.htmlFor) el.htmlFor = el.htmlFor.replace(idRegex, replacement);
    if (el.id) el.id = el.id.replace(idRegex, replacement);
    if (el.name) el.name = el.name.replace(idRegex, replacement);
}

function addForm(selector, prefix) {
    const newElement = selector.cloneNode(true);
    const totalForms = document.getElementById(`id_${prefix}-TOTAL_FORMS`);
    let total = parseInt(totalForms.value, 10);

    newElement.querySelectorAll('input:not([type=submit]):not([type=reset])').forEach(input => {
        const name = input.name.replace(`-${total - 1}-`, `-${total}-`);
        input.name = name;
        input.id = `id_${name}`;
        input.value = '';
        input.checked = false;
    });

    newElement.querySelectorAll('button:not([type=submit]):not([type=reset])').forEach(button => {
        button.id = button.id.replace(`-${total - 1}-`, `-${total}-`);
        button.value = '';
        button.checked = false;
    });

    newElement.querySelectorAll('.field-label').forEach(label => {
        label.textContent = `${total + 1}. `;
    });

    newElement.querySelectorAll('label').forEach(label => {
        if (label.htmlFor) {
            label.htmlFor = label.htmlFor.replace(`-${total - 1}-`, `-${total}-`);
        }
    });

    total++;
    totalForms.value = total;
    selector.after(newElement);

    const conditionRow = document.querySelectorAll('.form-row:not(:last-child)');
    conditionRow.forEach(row => {
        row.querySelector('.button.add-form-row').classList.add('is-hidden');
        row.querySelector('.button.remove-form-row').classList.remove('is-hidden');
    });

    newElement.querySelector('input').focus();
    return false;
}

function deleteForm(prefix, button) {
    const totalForms = document.getElementById(`id_${prefix}-TOTAL_FORMS`);
    let total = parseInt(totalForms.value, 10);

    if (total > 1) {
        button.closest('.form-row').remove();
        const forms = document.querySelectorAll('.form-row');
        totalForms.value = forms.length;

        forms.forEach((form, index) => {
            form.querySelectorAll('input').forEach(input => {
                updateElementIndex(input, prefix, index);
            });
            form.querySelectorAll('label').forEach(label => {
                updateElementIndex(label, prefix, index);
            });
            form.querySelector('.field-label').textContent = `${index + 1}.`;
        });
    }
    return false;
}

document.addEventListener('click', event => {
    const target = event.target;
    const addButton = target.closest('.add-form-row');
    const removeButton = target.closest('.remove-form-row');

    if (addButton) {
        event.preventDefault();
        addForm(document.querySelector('.form-row:last-child'), 'form');
    } else if (removeButton) {
        event.preventDefault();
        deleteForm('form', removeButton);
    }
});

function handleFormChange() {
    const forms = document.querySelectorAll('.form-row');
    forms.forEach((form, index) => {
        form.querySelector('.field-label').textContent = `${index + 1}.`;
        // update index of input elements
        form.querySelectorAll('input').forEach(input => {
            updateElementIndex(input, 'form', index);
        });
        if (index === forms.length - 1) {
            form.querySelector('.button.add-form-row').classList.remove('is-hidden');
            form.querySelector('.button.remove-form-row').classList.add('is-hidden');
        } else {
            form.querySelector('.button.add-form-row').classList.add('is-hidden');
            form.querySelector('.button.remove-form-row').classList.remove('is-hidden');
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    window.addEventListener('keydown', event => {
        if (event.key === 'Enter') {
            event.preventDefault();
        }
    });

    const el = document.getElementById('tasks');
    new Sortable(el, {
        handle: '.draggable',
        animation: 150,
        onEnd: handleFormChange,
        onChange: handleFormChange,
    });
});