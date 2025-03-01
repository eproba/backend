function updateElementIndex(el, prefix, ndx) {
    const idRegex = new RegExp(`(${prefix}-\\d+)`);
    const replacement = `${prefix}-${ndx}`;
    if (el.htmlFor) el.htmlFor = el.htmlFor.replace(idRegex, replacement);
    if (el.id) el.id = el.id.replace(idRegex, replacement);
    if (el.name) el.name = el.name.replace(idRegex, replacement);
}

function addFormRow(selector, prefix) {
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

    newElement.querySelectorAll('textarea').forEach(textarea => {
        const name = textarea.name.replace(`-${total - 1}-`, `-${total}-`);
        textarea.name = name;
        textarea.id = `id_${name}`;
        textarea.value = '';
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

function deleteFormRow(prefix, button) {
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
        addFormRow(document.querySelector('.form-row:last-child'), 'form');
    } else if (removeButton) {
        event.preventDefault();
        deleteFormRow('form', removeButton);
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
        // update index of description elements
        form.querySelectorAll('textarea').forEach(textarea => {
            updateElementIndex(textarea, 'form', index);
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
        if (event.key === 'Enter' && event.target.tagName !== 'TEXTAREA') {
            event.preventDefault();
        }
    });

    const el = document.getElementById('tasks');
    try {
        new Sortable(el, {
            handle: '.draggable',
            animation: 150,
            onEnd: handleFormChange,
            onChange: handleFormChange,
        });
    } catch (error) {
        alert('Could not initialize Sortable library. You will not be able to reorder tasks.');
    }

    try {
        const tasksDescriptionsButton = document.getElementById('additional-fields-button');
        tasksDescriptionsButton.addEventListener('click', () => {
            tasksDescriptionsButton.classList.toggle('is-outlined');
            const enabled = !tasksDescriptionsButton.classList.contains('is-outlined');

            const tasksDescriptions = document.querySelectorAll('.additional-field');
            tasksDescriptions.forEach(description => {
                if (enabled) {
                    description.classList.remove('is-hidden');
                    // const label = description.closest('.form-row').querySelector('.field-label');
                    // description.parentElement.style.marginLeft = label.offsetWidth + parseFloat(getComputedStyle(label).marginRight) + 'px';
                } else {
                    description.classList.add('is-hidden');
                }
            });
        });
        let shouldEnableDescriptionsAutomatically = false;
        document.querySelectorAll('.field.additional-field textarea').forEach(description => {
            if (description.value) {
                shouldEnableDescriptionsAutomatically = true;
            }
        });
        if (shouldEnableDescriptionsAutomatically && tasksDescriptionsButton.classList.contains('is-outlined')) {
            tasksDescriptionsButton.click();
        }
    } catch (error) {
        // pass - tasks descriptions button is not present and this feature is not needed
    }
});
