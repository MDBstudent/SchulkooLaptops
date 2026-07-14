import json
import os
import subprocess
import urllib.request
from pathlib import Path

SERVER_URL = os.getenv('SERVER_URL', 'http://localhost:5000')
SCRIPT_DIR = Path(__file__).resolve().parent
WINGET_PATH = 'winget'


def request_json(url, payload=None):
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode('utf-8')
        headers['Content-Type'] = 'application/json'

    req = urllib.request.Request(url, data=data, headers=headers, method='POST' if payload is not None else 'GET')
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode('utf-8'))


def fetch_upgrade_config():
    return request_json(f'{SERVER_URL}/api/upgrade')


def run_upgrade_steps(config):
    for value in config.get('install', []):
        subprocess.run([str(WINGET_PATH), 'install', value], check=False)

    for value in config.get('uninstall', []):
        subprocess.run([str(WINGET_PATH), 'uninstall', value], check=False)

    for value in config.get('additional', []):
        commands = value.split()
        if commands:
            subprocess.run(commands, check=False)


def collect_installed_packages():
    try:
        result = subprocess.run([str(WINGET_PATH), 'list'], capture_output=True, text=True, check=False)
        stdout = result.stdout or ''
        stderr = result.stderr or ''
        if stdout == '' and stderr == '':
            print("Warning: winget command produced no output. Ensure that the winget executable is available and functioning.")
            
        return stdout or stderr or ''
    except FileNotFoundError:
        print("Error: winget executable not found. Ensure that it is installed and available in the system PATH.")
        return ''


def report_installed_packages(output, version):
    return request_json(f'{SERVER_URL}/api/installed-packages', {'output': output, 'version': version})


if __name__ == '__main__':
    config = fetch_upgrade_config()
    run_upgrade_steps(config)
    winget_output = collect_installed_packages()
    print("Reporting installed packages to server...")
    print(f"Winget output:\n{winget_output}")
    report_installed_packages(winget_output, config.get('version', 1))
