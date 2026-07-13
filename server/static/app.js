const form = document.getElementById('upgrade-form');
const statusMessage = document.getElementById('status-message');
const installedList = document.getElementById('installed-packages-list');
const lists = {
    install: document.getElementById('install-list'),
    uninstall: document.getElementById('uninstall-list'),
    additional: document.getElementById('additional-list'),
};

function createRow(value = '') {
    const row = document.createElement('div');
    row.className = 'item-row';

    const input = document.createElement('input');
    input.type = 'text';
    input.value = value;
    input.placeholder = 'Enter value';

    const removeButton = document.createElement('button');
    removeButton.type = 'button';
    removeButton.className = 'remove-btn';
    removeButton.textContent = 'Remove';
    removeButton.addEventListener('click', () => row.remove());

    row.appendChild(input);
    row.appendChild(removeButton);
    return row;
}

function renderItems(data) {
    Object.entries(lists).forEach(([key, container]) => {
        container.innerHTML = '';
        const values = data[key] || [];
        values.forEach((value) => {
            container.appendChild(createRow(value));
        });
    });
}

function renderInstalledPackages(packages) {
    if (!installedList) {
        return;
    }

    installedList.innerHTML = '';
    const values = Array.isArray(packages) ? packages : [];

    if (!values.length) {
        const emptyState = document.createElement('li');
        emptyState.className = 'package-pill';
        emptyState.textContent = 'No installed packages reported yet.';
        installedList.appendChild(emptyState);
        return;
    }

    values.forEach((value) => {
        const item = document.createElement('li');
        item.className = 'package-pill';
        item.textContent = value;
        installedList.appendChild(item);
    });
}

async function refreshInstalledPackages() {
    try {
        const response = await fetch('/api/installed-packages');
        if (!response.ok) {
            throw new Error('Failed to load installed packages');
        }
        const data = await response.json();
        renderInstalledPackages(data.packages || []);
    } catch (error) {
        console.error(error);
    }
}

function collectData() {
    const data = {
        install: [],
        uninstall: [],
        additional: [],
    };

    Object.entries(lists).forEach(([key, container]) => {
        Array.from(container.querySelectorAll('.item-row')).forEach((row) => {
            const value = row.querySelector('input').value.trim();
            if (value) {
                data[key].push(value);
            }
        });
    });

    return data;
}

Array.from(document.querySelectorAll('.add-btn')).forEach((button) => {
    button.addEventListener('click', () => {
        const listName = button.dataset.list;
        lists[listName].appendChild(createRow());
    });
});

form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const payload = collectData();

    statusMessage.textContent = 'Saving...';

    try {
        const response = await fetch('/api/upgrade', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });

        if (!response.ok) {
            throw new Error('Failed to save');
        }

        statusMessage.textContent = 'Saved successfully.';
        renderItems(await response.json());
    } catch (error) {
        statusMessage.textContent = 'Could not save the configuration.';
        console.error(error);
    }
});

renderItems(window.initialUpgradeData || { install: [], uninstall: [], additional: [] });
renderInstalledPackages(window.initialInstalledPackages || []);
refreshInstalledPackages();
