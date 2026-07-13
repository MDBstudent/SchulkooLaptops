import json
import re
from pathlib import Path

import flask

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / 'static'
UPGRADE_FILE = STATIC_DIR / 'upgrade.json'
INSTALLED_PACKAGES_FILE = STATIC_DIR / 'installed_packages.json'

app = flask.Flask(
    __name__,
    template_folder=str(BASE_DIR / 'templates'),
    static_folder=str(STATIC_DIR),
    static_url_path='/static',
)


def load_json_file(path, default):
    if not path.exists():
        return default

    with path.open('r', encoding='utf-8') as handle:
        return json.load(handle)


def write_json_file(path, data):
    with path.open('w', encoding='utf-8') as handle:
        json.dump(data, handle, indent=4)
        handle.write('\n')


def normalize_list(value):
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def load_upgrade_data():
    data = load_json_file(UPGRADE_FILE, {})
    version = data.get('version', 1)
    try:
        version = int(version)
    except (TypeError, ValueError):
        version = 1

    return {
        'version': version,
        'install': normalize_list(data.get('install', [])),
        'uninstall': normalize_list(data.get('uninstall', [])),
        'additional': normalize_list(data.get('additional', data.get('addiditional', []))),
    }


def save_upgrade_data(data):
    existing = load_upgrade_data()
    next_version = existing.get('version', 0) + 1

    normalized = {
        'version': next_version,
        'install': normalize_list(data.get('install', [])),
        'uninstall': normalize_list(data.get('uninstall', [])),
        'additional': normalize_list(data.get('additional', [])),
    }

    write_json_file(UPGRADE_FILE, normalized)
    return normalized


def load_installed_packages():
    saved_data = load_json_file(INSTALLED_PACKAGES_FILE, {})
    current_config = load_upgrade_data()
    current_version = current_config.get('version', 1)

    if isinstance(saved_data, dict):
        stored_version = saved_data.get('version', 1)
        packages = saved_data.get('packages', [])
    else:
        stored_version = 1
        packages = saved_data

    if stored_version != current_version:
        return []

    install_names = {str(item).strip() for item in current_config.get('install', []) if str(item).strip()}
    normalized_packages = [str(item).strip() for item in packages if str(item).strip()]
    return sorted({name for name in normalized_packages if name not in install_names})


def save_installed_packages(packages, version=None):
    current_config = load_upgrade_data()
    effective_version = version if version is not None else current_config.get('version', 1)
    install_names = {str(item).strip() for item in current_config.get('install', []) if str(item).strip()}
    filtered_packages = [
        str(item).strip()
        for item in packages
        if str(item).strip() and str(item).strip() not in install_names
    ]
    normalized = {
        'version': effective_version,
        'packages': sorted(set(filtered_packages)),
    }
    write_json_file(INSTALLED_PACKAGES_FILE, normalized)
    return normalized


def extract_packages_from_winget_output(text):
    if not text:
        return []

    packages = []
    for line in str(text).splitlines():
        cleaned = line.strip()
        if not cleaned:
            continue
        lowered = cleaned.lower()
        if lowered.startswith('name') or lowered.startswith('id') or lowered.startswith('available'):
            continue
        if 'no installed package' in lowered or 'no packages found' in lowered:
            continue
        if cleaned.startswith('---'):
            continue

        columns = [part.strip() for part in re.split(r'\s{2,}', cleaned) if part.strip()]
        if not columns:
            continue

        package_name = columns[0]
        if package_name.lower() in {'name', 'id', 'version', 'source'}:
            continue
        packages.append(package_name)

    return sorted(set(packages))


@app.route('/')
def index():
    return flask.render_template(
        'index.html',
        upgrade_data=load_upgrade_data(),
        installed_packages=load_installed_packages(),
    )


@app.route('/upgrade')
def upgrade():
    return flask.jsonify(load_upgrade_data())


@app.route('/api/upgrade', methods=['GET', 'POST'])
def api_upgrade():
    if flask.request.method == 'POST':
        payload = flask.request.get_json(silent=True) or {}
        saved_data = save_upgrade_data(payload)
        return flask.jsonify(saved_data), 200

    return flask.jsonify(load_upgrade_data()), 200


@app.route('/api/installed-packages', methods=['GET', 'POST'])
def api_installed_packages():
    if flask.request.method == 'POST':
        payload = flask.request.get_json(silent=True) or {}
        if isinstance(payload, dict):
            raw_output = payload.get('output') or payload.get('packages') or payload.get('data') or payload.get('text')
        else:
            raw_output = payload

        if raw_output is None:
            raw_output = flask.request.get_data(as_text=True)

        if isinstance(raw_output, list):
            new_packages = [str(item).strip() for item in raw_output if str(item).strip()]
        else:
            new_packages = extract_packages_from_winget_output(raw_output)

        current_config = load_upgrade_data()
        effective_version = payload.get('version', current_config.get('version', 1))
        existing_packages = load_installed_packages()
        merged_packages = sorted(set(existing_packages) | set(new_packages))
        saved_packages = save_installed_packages(merged_packages, version=effective_version)
        return flask.jsonify({'version': current_config.get('version', 1), 'packages': saved_packages['packages']}), 200

    return flask.jsonify({'version': load_upgrade_data().get('version', 1), 'packages': load_installed_packages()}), 200


if __name__ == '__main__':
    app.run(host='localhost', port=5000, debug=True)
