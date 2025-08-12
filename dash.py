#!/usr/bin/env python3
import os
import webbrowser
import threading
import time
from flask import Flask, render_template, jsonify, request
from services.project_scanner import scan_projects
from services.git_service import GitService
from services.venv_service import VenvService
from utils.data_manager import load_data, save_data
from utils.command_runner import run_command
import config

app = Flask(__name__)
git_service = GitService(config.GIT_NAME, config.GIT_EMAIL, config.GITHUB_USERNAME, config.GITHUB_TOKEN)
venv_service = VenvService()

@app.route('/')
def index():
    try:
        data = load_data(config.DATA_FILE)
        data['projects'] = scan_projects(config.PROJECTS_DIR)
        return render_template('dashboard.html', projects_dir=config.PROJECTS_DIR)
    except Exception as e:
        return f"<h1>Error</h1><p>{str(e)}</p>"

@app.route('/api/data')
def get_data():
    try:
        data = load_data(config.DATA_FILE)
        data['projects'] = scan_projects(config.PROJECTS_DIR)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e), 'projects': [], 'snippets': [], 'sessions': []}), 500

@app.route('/api/scan-projects')
def scan_projects_route():
    try:
        data = load_data(config.DATA_FILE)
        data['projects'] = scan_projects(config.PROJECTS_DIR)
        save_data(data, config.DATA_FILE)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/open-project', methods=['POST'])
def open_project_route():
    try:
        data = request.json
        project_path = data.get('path')
        action = data.get('action', 'code')
        
        if action == 'code':
            for editor in ['code', 'pycharm', 'subl']:
                if run_command(f'{editor} "{project_path}"')['success']:
                    return jsonify({'success': True, 'message': f'Opened in {editor}'})
            run_command(f'open "{project_path}"')
            return jsonify({'success': True, 'message': 'Opened in Finder'})
        elif action == 'terminal':
            run_command(f'open -a Terminal "{project_path}"')
            return jsonify({'success': True, 'message': 'Opened in Terminal'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/venv/<action>', methods=['POST'])
def venv_action(action):
    try:
        project_path = request.json.get('path')
        if action == 'create':
            result = venv_service.create_venv(project_path)
        elif action == 'activate':
            result = venv_service.activate_venv(project_path)
        elif action == 'delete':
            result = venv_service.delete_venv(project_path)
        else:
            return jsonify({'success': False, 'error': 'Unknown action'})
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/git/<action>', methods=['POST'])
def git_action(action):
    try:
        data = request.json
        result = git_service.handle_action(action, data.get('path'), data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/save-data', methods=['POST'])
def save_data_route():
    try:
        success = save_data(request.json, config.DATA_FILE)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def main():
    if not os.path.exists(config.PROJECTS_DIR):
        os.makedirs(config.PROJECTS_DIR, exist_ok=True)
    
    def open_browser():
        time.sleep(2)
        webbrowser.open('http://localhost:8080')
    
    threading.Thread(target=open_browser, daemon=True).start()
    app.run(host='127.0.0.1', port=8080, debug=False, use_reloader=False, threaded=True)

if __name__ == '__main__':
    main()