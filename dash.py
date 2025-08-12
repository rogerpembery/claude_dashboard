#!/usr/bin/env python3
"""
Python Vibe Dashboard - Refactored Version
A productivity tool for Python developers on macOS with full venv and git integration
"""

import sys
import os
import webbrowser
import traceback
from flask import Flask, render_template, jsonify, request

# Import our services and utilities
from services.project_scanner import scan_projects
from services.git_service import GitService
from services.venv_service import VenvService
from utils.data_manager import load_data, save_data
from utils.time_utils import debug_log
from utils.command_runner import run_command
import config

debug_log("=== DASHBOARD STARTUP ===")
debug_log(f"Python version: {sys.version}")
debug_log(f"Working directory: {os.getcwd()}")
debug_log(f"Script file: {__file__}")

app = Flask(__name__)
debug_log("✓ Flask app created")

debug_log(f"Projects directory: {config.PROJECTS_DIR}")
debug_log(f"Directory exists: {os.path.exists(config.PROJECTS_DIR)}")
debug_log(f"Data file: {config.DATA_FILE}")

if not os.path.exists(config.PROJECTS_DIR):
    debug_log("WARNING: Projects directory doesn't exist, creating it...")
    os.makedirs(config.PROJECTS_DIR, exist_ok=True)

# Initialize services
git_service = GitService(config.GIT_NAME, config.GIT_EMAIL, config.GITHUB_USERNAME, config.GITHUB_TOKEN)
venv_service = VenvService()
debug_log("✓ Services initialized")

debug_log("✓ Configuration loaded")

# Flask Routes
@app.route('/')
def index():
    debug_log("Index route accessed")
    try:
        data = load_data(config.DATA_FILE)
        projects = scan_projects(config.PROJECTS_DIR)
        data['projects'] = projects
        
        # Check HTML size before rendering
        initial_data_size = len(str(data))
        debug_log(f"Data size: {initial_data_size} bytes")
        debug_log(f"Projects count: {len(projects)}")
        
        # Try minimal template first if too much data
        if initial_data_size > 100000:  # 100KB limit
            debug_log("Data too large, using minimal template")
            return render_template('minimal.html', projects_count=len(projects), projects_dir=config.PROJECTS_DIR)
        
        debug_log("✓ Rendering full template")
        result = render_template('dashboard.html', projects_dir=config.PROJECTS_DIR)
        
        debug_log("✓ Template rendered successfully")
        return result
        
    except Exception as e:
        debug_log(f"✗ Error in index route: {e}")
        traceback.print_exc()
        return f"""
        <html>
        <head><title>Dashboard Error</title></head>
        <body style="font-family: Arial, sans-serif; margin: 40px;">
            <h1>Dashboard Error</h1>
            <p><strong>Error:</strong> {str(e)}</p>
            <h3>Debug Info:</h3>
            <pre>{traceback.format_exc()}</pre>
            <p><a href="/minimal">Try Minimal Version</a></p>
        </body>
        </html>
        """

@app.route('/minimal')
def minimal_dashboard():
    """Minimal dashboard for testing"""
    debug_log("Minimal dashboard route accessed")
    try:
        data = load_data(config.DATA_FILE)
        projects = scan_projects(config.PROJECTS_DIR)
        return render_template('minimal.html', projects_count=len(projects), projects_dir=config.PROJECTS_DIR)
        
    except Exception as e:
        debug_log(f"Error in minimal route: {e}")
        return f"<h1>Error</h1><pre>{str(e)}</pre>"

@app.route('/api/data')
def get_data():
    debug_log("API data route accessed")
    try:
        debug_log("Loading basic data...")
        data = load_data(config.DATA_FILE)
        
        debug_log("Starting project scan...")
        # Always refresh projects on data load
        from datetime import datetime
        start_time = datetime.now()
        data['projects'] = scan_projects(config.PROJECTS_DIR)
        end_time = datetime.now()
        scan_duration = (end_time - start_time).total_seconds()
        
        debug_log(f"✓ Project scan completed in {scan_duration:.2f} seconds")
        debug_log(f"✓ Returning {len(data['projects'])} projects via API")
        debug_log(f"✓ Returning {len(data.get('snippets', []))} snippets")
        debug_log(f"✓ Returning {len(data.get('sessions', []))} sessions")
        
        return jsonify(data)
    except Exception as e:
        debug_log(f"✗ Error in API data route: {e}")
        traceback.print_exc()
        return jsonify({
            'error': str(e),
            'projects': [],
            'snippets': [],
            'sessions': []
        }), 500

@app.route('/api/scan-projects')
def scan_projects_route():
    debug_log("API scan-projects route accessed")
    try:
        data = load_data(config.DATA_FILE)
        data['projects'] = scan_projects(config.PROJECTS_DIR)
        save_data(data, config.DATA_FILE)
        return jsonify(data)
    except Exception as e:
        debug_log(f"✗ Error in scan-projects route: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/open-project', methods=['POST'])
def open_project_route():
    debug_log("API open-project route accessed")
    try:
        data = request.json
        project_path = data.get('path')
        action = data.get('action', 'code')
        debug_log(f"Opening project: {project_path} with action: {action}")
        
        if action == 'code':
            # Try VS Code first, then other editors
            editors = ['code', 'pycharm', 'subl', 'atom']
            for editor in editors:
                result = run_command(f'{editor} "{project_path}"')
                if result['success']:
                    debug_log(f"✓ Opened in {editor}")
                    return jsonify({'success': True, 'message': f'Opened in {editor}'})
            # Fallback to Finder
            run_command(f'open "{project_path}"')
            return jsonify({'success': True, 'message': 'Opened in Finder'})
        elif action == 'terminal':
            run_command(f'open -a Terminal "{project_path}"')
            return jsonify({'success': True, 'message': 'Opened in Terminal'})
    except Exception as e:
        debug_log(f"✗ Error in open-project route: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/venv/<action>', methods=['POST'])
def venv_action(action):
    debug_log(f"API venv/{action} route accessed")
    try:
        data = request.json
        project_path = data.get('path')
        
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
        debug_log(f"✗ Error in venv route: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/git/<action>', methods=['POST'])
def git_action(action):
    debug_log(f"API git/{action} route accessed")
    try:
        data = request.json
        project_path = data.get('path')
        
        result = git_service.handle_action(action, project_path, data)
        return jsonify(result)
        
    except Exception as e:
        debug_log(f"✗ Error in git route: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/save-data', methods=['POST'])
def save_data_route():
    debug_log("API save-data route accessed")
    try:
        data = request.json
        success = save_data(data, config.DATA_FILE)
        return jsonify({'success': success})
    except Exception as e:
        debug_log(f"✗ Error in save-data route: {e}")
        return jsonify({'success': False, 'error': str(e)})

debug_log("✓ All routes defined")

def main():
    """Main function to start the Flask server"""
    debug_log("=== MAIN FUNCTION STARTING ===")
    
    # Test project scanning
    try:
        debug_log("Testing project scan...")
        projects = scan_projects(config.PROJECTS_DIR)
        debug_log(f"✓ Test scan successful: {len(projects)} projects found")
        for project in projects[:3]:  # Show first 3 projects
            debug_log(f"  - {project['name']} ({project['type']})")
    except Exception as e:
        debug_log(f"✗ Test scan failed: {e}")
        traceback.print_exc()
    
    # Browser setup
    debug_log("Setting up browser auto-open...")
    try:
        import threading
        import time
        
        def open_browser():
            time.sleep(2)
            debug_log("Opening browser to http://localhost:8080")
            webbrowser.open('http://localhost:8080')
            debug_log("✓ Browser open command sent")
        
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()
        debug_log("✓ Browser thread started")
        
    except Exception as e:
        debug_log(f"Warning: Browser auto-open setup failed: {e}")
    
    # Flask server startup
    debug_log("=== FLASK SERVER STARTUP ===")
    debug_log("Server configuration:")
    debug_log("- Host: 127.0.0.1")
    debug_log("- Port: 8080")
    debug_log("- Debug: False")
    debug_log("- URL: http://localhost:8080")
    debug_log("- Use reloader: False")
    
    debug_log("About to call app.run()...")
    
    try:
        # Start the Flask development server
        app.run(
            debug=False,
            port=8080,
            host='127.0.0.1',
            use_reloader=False,
            threaded=True
        )
        debug_log("app.run() returned (this should not happen during normal operation)")
        
    except KeyboardInterrupt:
        debug_log("✓ Server stopped by user (Ctrl+C)")
        
    except OSError as e:
        if "Address already in use" in str(e):
            debug_log("✗ Port 8080 is already in use!")
            debug_log("Try these solutions:")
            debug_log("1. Kill process using port 8080: sudo lsof -ti:8080 | xargs kill -9")
            debug_log("2. Use a different port in the code")
            debug_log("3. Wait a minute and try again")
        else:
            debug_log(f"✗ Network error: {e}")
        
    except Exception as e:
        debug_log(f"✗ FLASK SERVER ERROR: {e}")
        debug_log(f"Error type: {type(e).__name__}")
        traceback.print_exc()
        
        debug_log("\n=== DEBUGGING INFO ===")
        debug_log(f"Flask app: {app}")
        debug_log(f"Routes registered: {[rule.rule for rule in app.url_map.iter_rules()]}")
        debug_log("If you see this error, please check:")
        debug_log("1. Python version compatibility")
        debug_log("2. Flask installation")
        debug_log("3. Port availability")
        debug_log("4. File permissions")
        
        input("\nPress Enter to exit...")
    
    debug_log("=== MAIN FUNCTION ENDING ===")

if __name__ == '__main__':
    debug_log("=== SCRIPT EXECUTION STARTING ===")
    debug_log(f"Script name: {__name__}")
    debug_log(f"Command line args: {sys.argv}")
    
    try:
        main()
    except Exception as e:
        debug_log(f"✗ FATAL ERROR: {e}")
        traceback.print_exc()
        input("\nPress Enter to exit...")
    
    debug_log("=== SCRIPT EXECUTION ENDING ===")