#!/usr/bin/env python3
"""
Python Vibe Dashboard - Local Development Server with Debug Logging
A productivity tool for Python developers on macOS with full venv and git integration

Requirements:
    pip install flask

Usage:
    python dash.py
    
Then open: http://localhost:8080
"""

import sys
import os
import json
import subprocess
import webbrowser
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, render_template_string, jsonify, request

def debug_log(message):
    """Debug logging function"""
    print(f"[DEBUG] {message}")
    sys.stdout.flush()

debug_log("=== DASHBOARD STARTUP ===")
debug_log(f"Python version: {sys.version}")
debug_log(f"Working directory: {os.getcwd()}")
debug_log(f"Script file: {__file__}")

app = Flask(__name__)
debug_log("✓ Flask app created")

# Configuration - CUSTOMIZE THESE FOR YOUR SETUP
PROJECTS_DIR = os.path.expanduser("/Volumes/BaseHDD/python/")
DATA_FILE = os.path.expanduser("~/.vibe_dashboard_data.json")

debug_log(f"Projects directory: {PROJECTS_DIR}")
debug_log(f"Directory exists: {os.path.exists(PROJECTS_DIR)}")
debug_log(f"Data file: {DATA_FILE}")

if not os.path.exists(PROJECTS_DIR):
    debug_log("WARNING: Projects directory doesn't exist, creating it...")
    os.makedirs(PROJECTS_DIR, exist_ok=True)

# Git/GitHub Configuration - UPDATE THESE WITH YOUR INFO
GITHUB_USERNAME = "rogerpembery"  # Replace with your GitHub username
GITHUB_TOKEN = "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"  # Replace with your GitHub personal access token
GIT_EMAIL = "roger@pembery.com"  # Replace with your git email
GIT_NAME = "roger pembery"  # Replace with your git name

# Sample data structure
DEFAULT_DATA = {
    "projects": [],
    "snippets": [
        {
            "id": 1,
            "title": "Virtual Environment Setup",
            "code": "# Create and activate venv\npython -m venv venv\nsource venv/bin/activate  # macOS/Linux\n# pip install -r requirements.txt",
            "tags": ["venv", "setup"],
            "created": datetime.now().isoformat()
        },
        {
            "id": 2,
            "title": "Quick DataFrame Info",
            "code": "import pandas as pd\n\n# Quick data overview\ndf.info()\nprint(f\"Shape: {df.shape}\")\nprint(f\"Nulls: {df.isnull().sum().sum()}\")",
            "tags": ["pandas", "data-analysis"],
            "created": datetime.now().isoformat()
        }
    ],
    "sessions": []
}

debug_log("✓ Configuration loaded")

def load_data():
    """Load dashboard data from file"""
    debug_log("Loading data from file...")
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                # Ensure all required keys exist
                for key in DEFAULT_DATA:
                    if key not in data:
                        data[key] = DEFAULT_DATA[key]
                debug_log(f"✓ Data loaded from {DATA_FILE}")
                return data
        except Exception as e:
            debug_log(f"Error loading data file: {e}")
            return DEFAULT_DATA.copy()
    debug_log("No data file found, using defaults")
    return DEFAULT_DATA.copy()

def save_data(data):
    """Save dashboard data to file"""
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        debug_log(f"✓ Data saved to {DATA_FILE}")
        return True
    except Exception as e:
        debug_log(f"Error saving data: {e}")
        return False

def run_command(command, cwd=None, capture_output=True):
    """Run a shell command and return result"""
    try:
        result = subprocess.run(
            command, 
            cwd=cwd, 
            capture_output=capture_output, 
            text=True, 
            shell=True,
            timeout=30
        )
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout.strip() if capture_output else '',
            'stderr': result.stderr.strip() if capture_output else '',
            'returncode': result.returncode
        }
    except subprocess.TimeoutExpired:
        return {'success': False, 'stderr': 'Command timed out', 'returncode': -1}
    except Exception as e:
        return {'success': False, 'stderr': str(e), 'returncode': -1}

def check_venv_status(project_path):
    """Check if venv exists and if it's currently active"""
    venv_path = Path(project_path) / 'venv'
    exists = venv_path.exists() and (venv_path / 'bin' / 'activate').exists()
    
    # Check if this venv is currently active
    active = False
    if exists:
        current_venv = os.environ.get('VIRTUAL_ENV')
        if current_venv and str(venv_path.absolute()) in current_venv:
            active = True
    
    return {'exists': exists, 'active': active, 'path': str(venv_path)}

def get_git_status(project_path):
    """Get detailed git status for a project"""
    if not (Path(project_path) / '.git').exists():
        return {'hasGit': False}
    
    # Get current branch
    branch_result = run_command('git branch --show-current', cwd=project_path)
    branch = branch_result['stdout'] if branch_result['success'] else 'main'
    
    # Get status
    status_result = run_command('git status --porcelain', cwd=project_path)
    has_changes = bool(status_result['stdout']) if status_result['success'] else False
    
    # Get remote info
    remote_result = run_command('git remote -v', cwd=project_path)
    has_remote = bool(remote_result['stdout']) if remote_result['success'] else False
    
    # Get last commit
    log_result = run_command('git log -1 --pretty=format:"%h %s" 2>/dev/null', cwd=project_path)
    last_commit = log_result['stdout'] if log_result['success'] else ''
    
    return {
        'hasGit': True,
        'branch': branch,
        'hasChanges': has_changes,
        'hasRemote': has_remote,
        'lastCommit': last_commit
    }

def scan_projects():
    """Scan the projects directory for Python projects - optimized for speed"""
    debug_log(f"Scanning projects in: {PROJECTS_DIR}")
    projects = []
    projects_path = Path(PROJECTS_DIR)
    
    # Relevant file extensions for code and config
    RELEVANT_EXTENSIONS = {
        '.py', '.pyx', '.pyi',  # Python files
        '.js', '.ts', '.jsx', '.tsx',  # JavaScript/TypeScript
        '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg',  # Config files
        '.md', '.txt', '.rst',  # Documentation
        '.sh', '.bat', '.ps1',  # Scripts
        '.sql', '.html', '.css',  # Other code
        '.requirements', '.lock'  # Dependency files
    }
    
    # Files to always include (even without extension)
    IMPORTANT_FILES = {
        'requirements.txt', 'pyproject.toml', 'setup.py', 'setup.cfg',
        'Pipfile', 'Pipfile.lock', 'poetry.lock', 'Dockerfile',
        'makefile', 'Makefile', 'README', 'LICENSE', 'CHANGELOG'
    }
    
    # Directories to skip entirely
    SKIP_DIRS = {
        '__pycache__', '.git', '.svn', '.hg', 'node_modules',
        '.pytest_cache', '.mypy_cache', '.tox', 'venv', '.venv',
        'env', '.env', 'build', 'dist', '.eggs', '*.egg-info',
        '.idea', '.vscode', '.DS_Store', 'logs', 'tmp', 'temp'
    }
    
    if not projects_path.exists():
        debug_log("Projects directory doesn't exist, creating sample project...")
        sample_path = projects_path / "sample_project"
        sample_path.mkdir(parents=True, exist_ok=True)
        with open(sample_path / "main.py", "w") as f:
            f.write("#!/usr/bin/env python3\nprint('Hello from sample project!')\n")
        debug_log(f"Created sample project at: {sample_path}")
    
    try:
        items = list(projects_path.iterdir())
        debug_log(f"Found {len(items)} items to check")
        
        # Limit total items and add timeout
        MAX_ITEMS = 50
        MAX_SCAN_TIME = 15  # 15 seconds max
        start_scan_time = datetime.now()
        
        if len(items) > MAX_ITEMS:
            debug_log(f"Too many items ({len(items)}). Limiting to {MAX_ITEMS} most recently modified.")
            # Sort by modification time and take the most recent
            items.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            items = items[:MAX_ITEMS]
        
        processed = 0
        for item in items:
            # Check timeout
            if (datetime.now() - start_scan_time).total_seconds() > MAX_SCAN_TIME:
                debug_log(f"Scan timeout reached ({MAX_SCAN_TIME}s). Processed {processed} items.")
                break
            
            try:
                processed += 1
                if processed % 5 == 0:
                    elapsed = (datetime.now() - start_scan_time).total_seconds()
                    debug_log(f"Processed {processed}/{len(items)} items in {elapsed:.1f}s...")
                
                if item.is_dir() and not item.name.startswith('.') and item.name.lower() not in SKIP_DIRS:
                    debug_log(f"Checking directory: {item.name}")
                    
                    # Quick scan for relevant files only
                    relevant_files = []
                    python_files = []
                    
                    try:
                        # Scan directory with timeout for individual directories
                        dir_start_time = datetime.now()
                        MAX_DIR_TIME = 3  # 3 seconds max per directory
                        
                        # First, quick check of root directory
                        for file_item in item.iterdir():
                            if (datetime.now() - dir_start_time).total_seconds() > MAX_DIR_TIME:
                                debug_log(f"Directory {item.name} scan timeout - skipping deeper scan")
                                break
                                
                            if file_item.is_file():
                                file_ext = file_item.suffix.lower()
                                file_name = file_item.name.lower()
                                
                                if file_ext == '.py':
                                    python_files.append(file_item)
                                elif (file_ext in RELEVANT_EXTENSIONS or 
                                      file_name in IMPORTANT_FILES or
                                      any(imp in file_name for imp in IMPORTANT_FILES)):
                                    relevant_files.append(file_item)
                                
                                # Limit files per directory
                                if len(python_files) + len(relevant_files) > 100:
                                    debug_log(f"File limit reached for {item.name}")
                                    break
                        
                        # If we have time left and few files, check one level deeper
                        if ((datetime.now() - dir_start_time).total_seconds() < MAX_DIR_TIME/2 and 
                            len(python_files) + len(relevant_files) < 20):
                            
                            for subdir in item.iterdir():
                                if (datetime.now() - dir_start_time).total_seconds() > MAX_DIR_TIME:
                                    break
                                    
                                if (subdir.is_dir() and 
                                    not subdir.name.startswith('.') and 
                                    subdir.name.lower() not in SKIP_DIRS):
                                    
                                    for sub_file in subdir.iterdir():
                                        if sub_file.is_file() and sub_file.suffix == '.py':
                                            python_files.append(sub_file)
                                            if len(python_files) > 50:  # Max 50 Python files per project
                                                break
                                    
                                    if len(python_files) > 50:
                                        break
                    
                    except Exception as e:
                        debug_log(f"Error scanning directory {item.name}: {e}")
                        continue
                    
                    # Only consider it a Python project if it has Python files
                    if python_files:
                        total_files = len(python_files) + len(relevant_files)
                        debug_log(f"Found Python project: {item.name} ({len(python_files)} .py files, {total_files} total relevant files)")
                        
                        project = analyze_project_fast(item, python_files, relevant_files)
                        if project:
                            projects.append(project)
                    else:
                        debug_log(f"Skipping {item.name} - no Python files found")
                
                elif item.is_file() and item.suffix == '.py':
                    debug_log(f"Found standalone Python file: {item.name}")
                    try:
                        projects.append({
                            "name": item.name,
                            "path": str(item),
                            "type": "file",
                            "venv": {'exists': False, 'active': False},
                            "git": {'hasGit': False},
                            "lastModified": get_relative_time(item.stat().st_mtime),
                            "size": item.stat().st_size,
                            "favorite": False
                        })
                    except Exception as e:
                        debug_log(f"Error processing file {item.name}: {e}")
                        continue
            
            except Exception as e:
                debug_log(f"Error processing item {item}: {e}")
                continue
        
        total_time = (datetime.now() - start_scan_time).total_seconds()
        debug_log(f"✓ Scan completed in {total_time:.1f}s: processed {processed} items, found {len(projects)} Python projects")
        return projects
        
    except Exception as e:
        debug_log(f"Error scanning projects: {e}")
        import traceback
        traceback.print_exc()
        return []

def analyze_project_fast(project_path, python_files, relevant_files):
    """Fast project analysis with pre-scanned files"""
    try:
        # Get venv status (quick check)
        venv_status = check_venv_status(project_path)
        
        # Get git status (quick check)
        git_status = get_git_status(project_path)
        
        # Use the files we already found
        total_python = len(python_files)
        total_relevant = len(relevant_files)
        
        # Get last modified from the Python files we found (max 10 to check)
        last_modified = project_path.stat().st_mtime
        if python_files:
            recent_files = sorted(python_files, key=lambda f: f.stat().st_mtime, reverse=True)[:10]
            if recent_files:
                last_modified = max(f.stat().st_mtime for f in recent_files)
        
        return {
            "name": project_path.name,
            "path": str(project_path),
            "type": "folder",
            "venv": venv_status,
            "git": git_status,
            "lastModified": get_relative_time(last_modified),
            "pythonFiles": total_python,
            "relevantFiles": total_relevant,
            "favorite": False
        }
    except Exception as e:
        debug_log(f"Error analyzing project {project_path}: {e}")
        return None

def analyze_project(project_path):
    """Analyze a project directory"""
    try:
        # Get venv status
        venv_status = check_venv_status(project_path)
        
        # Get git status
        git_status = get_git_status(project_path)
        
        # Get Python files
        python_files = list(project_path.glob('*.py'))
        if not python_files:
            python_files = list(project_path.glob('**/*.py'))
        
        # Get last modified time
        last_modified = project_path.stat().st_mtime
        if python_files:
            last_modified = max(f.stat().st_mtime for f in python_files[:10])
        
        return {
            "name": project_path.name,
            "path": str(project_path),
            "type": "folder",
            "venv": venv_status,
            "git": git_status,
            "lastModified": get_relative_time(last_modified),
            "pythonFiles": len(python_files),
            "favorite": False
        }
    except Exception as e:
        debug_log(f"Error analyzing project {project_path}: {e}")
        return None

def get_relative_time(timestamp):
    """Convert timestamp to relative time string"""
    try:
        dt = datetime.fromtimestamp(timestamp)
        now = datetime.now()
        diff = now - dt
        
        if diff.days > 7:
            return dt.strftime("%b %d")
        elif diff.days > 0:
            return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            return "Just now"
    except Exception as e:
        debug_log(f"Error formatting time: {e}")
        return "Unknown"

debug_log("✓ All functions defined")

# Flask Routes
@app.route('/')
def index():
    debug_log("Index route accessed")
    try:
        data = load_data()
        projects = scan_projects()
        data['projects'] = projects
        
        # Check HTML size before rendering
        initial_data_size = len(json.dumps(data))
        debug_log(f"Data size: {initial_data_size} bytes")
        debug_log(f"Projects count: {len(projects)}")
        
        # Try minimal template first if too much data
        if initial_data_size > 100000:  # 100KB limit
            debug_log("Data too large, using minimal template")
            return MINIMAL_TEMPLATE.replace('{{projects_count}}', str(len(projects))).replace('{{projects_dir}}', PROJECTS_DIR)
        
        debug_log("✓ Rendering full template")
        result = render_template_string(TEMPLATE, projects_dir=PROJECTS_DIR, initial_data=json.dumps(data))
        
        # Check rendered HTML size
        html_size = len(result)
        debug_log(f"Rendered HTML size: {html_size} bytes ({html_size/1024:.1f}KB)")
        
        if html_size > 500000:  # 500KB limit
            debug_log("WARNING: Rendered HTML is very large, this might cause browser issues")
        
        debug_log("✓ Template rendered successfully")
        return result
        
    except Exception as e:
        debug_log(f"✗ Error in index route: {e}")
        import traceback
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
        data = load_data()
        projects = scan_projects()
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Minimal Dashboard</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .project {{ background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <h1>Python Dashboard - Minimal Mode</h1>
            <p>Projects: {PROJECTS_DIR}</p>
            <p>Found {len(projects)} projects</p>
            
            {"".join(f'<div class="project"><strong>{p["name"]}</strong> - {p.get("pythonFiles", 0)} Python files</div>' for p in projects)}
            
            <script>
                console.log('Minimal dashboard loaded successfully');
                console.log('Projects:', {json.dumps(projects)});
            </script>
        </body>
        </html>
        """
        
    except Exception as e:
        debug_log(f"Error in minimal route: {e}")
        return f"<h1>Error</h1><pre>{str(e)}</pre>"

@app.route('/api/data')
def get_data():
    debug_log("API data route accessed")
    try:
        debug_log("Loading basic data...")
        data = load_data()
        
        debug_log("Starting project scan...")
        # Always refresh projects on data load
        start_time = datetime.now()
        data['projects'] = scan_projects()
        end_time = datetime.now()
        scan_duration = (end_time - start_time).total_seconds()
        
        debug_log(f"✓ Project scan completed in {scan_duration:.2f} seconds")
        debug_log(f"✓ Returning {len(data['projects'])} projects via API")
        debug_log(f"✓ Returning {len(data.get('snippets', []))} snippets")
        debug_log(f"✓ Returning {len(data.get('sessions', []))} sessions")
        
        return jsonify(data)
    except Exception as e:
        debug_log(f"✗ Error in API data route: {e}")
        import traceback
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
        data = load_data()
        data['projects'] = scan_projects()
        save_data(data)
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
        
        if not project_path or not os.path.exists(project_path):
            return jsonify({'success': False, 'error': 'Invalid project path'})
        
        if action == 'create':
            debug_log(f"Creating venv for: {project_path}")
            # Create virtual environment
            result = run_command(f'python3 -m venv venv', cwd=project_path)
            if result['success']:
                debug_log("✓ Venv created successfully")
                return jsonify({'success': True, 'message': 'Virtual environment created successfully'})
            else:
                debug_log(f"✗ Venv creation failed: {result['stderr']}")
                return jsonify({'success': False, 'error': result['stderr']})
        
        elif action == 'activate':
            # Generate activation script that user can run
            venv_path = os.path.join(project_path, 'venv', 'bin', 'activate')
            if os.path.exists(venv_path):
                # Open terminal with activation command
                script = f'''
                tell application "Terminal"
                    do script "cd '{project_path}' && source venv/bin/activate"
                    activate
                end tell
                '''
                run_command(f'osascript -e \'{script}\'')
                return jsonify({'success': True, 'message': 'Opening terminal with activated venv'})
            else:
                return jsonify({'success': False, 'error': 'Virtual environment not found'})
        
        elif action == 'delete':
            # Delete virtual environment
            venv_path = os.path.join(project_path, 'venv')
            if os.path.exists(venv_path):
                result = run_command(f'rm -rf "{venv_path}"')
                return jsonify({'success': True, 'message': 'Virtual environment deleted'})
            else:
                return jsonify({'success': False, 'error': 'Virtual environment not found'})
        
        return jsonify({'success': False, 'error': 'Unknown action'})
    except Exception as e:
        debug_log(f"✗ Error in venv route: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/git/<action>', methods=['POST'])
def git_action(action):
    debug_log(f"API git/{action} route accessed")
    try:
        data = request.json
        project_path = data.get('path')
        
        if not project_path or not os.path.exists(project_path):
            return jsonify({'success': False, 'error': 'Invalid project path'})
        
        if action == 'init':
            debug_log(f"Initializing git for: {project_path}")
            # Initialize git repository
            result = run_command('git init', cwd=project_path)
            if result['success']:
                # Set up git config
                run_command(f'git config user.email "{GIT_EMAIL}"', cwd=project_path)
                run_command(f'git config user.name "{GIT_NAME}"', cwd=project_path)
                debug_log("✓ Git initialized successfully")
                return jsonify({'success': True, 'message': 'Git repository initialized'})
            else:
                debug_log(f"✗ Git init failed: {result['stderr']}")
                return jsonify({'success': False, 'error': result['stderr']})
        
        elif action == 'add':
            debug_log(f"Adding files to git for: {project_path}")
            result = run_command('git add .', cwd=project_path)
            if result['success']:
                debug_log("✓ Files added to git")
                return jsonify({'success': True, 'message': 'Files added to git staging area'})
            else:
                debug_log(f"✗ Git add failed: {result['stderr']}")
                return jsonify({'success': False, 'error': result['stderr']})
        
        elif action == 'commit':
            debug_log(f"Committing changes for: {project_path}")
            message = data.get('message', 'Auto commit from Vibe Dashboard')
            result = run_command(f'git commit -m "{message}"', cwd=project_path)
            if result['success']:
                debug_log("✓ Changes committed")
                return jsonify({'success': True, 'message': 'Changes committed successfully'})
            else:
                debug_log(f"✗ Git commit failed: {result['stderr']}")
                return jsonify({'success': False, 'error': result['stderr']})
        
        elif action == 'status':
            debug_log(f"Getting git status for: {project_path}")
            result = run_command('git status --short', cwd=project_path)
            if result['success']:
                status_output = result['stdout'] if result['stdout'] else "Working tree clean"
                debug_log(f"✓ Git status retrieved: {status_output}")
                return jsonify({'success': True, 'message': f'Git Status:\n{status_output}', 'output': status_output})
            else:
                return jsonify({'success': False, 'error': result['stderr']})
        
        elif action == 'push':
            debug_log(f"Pushing changes for: {project_path}")
            result = run_command('git push', cwd=project_path)
            if result['success']:
                debug_log("✓ Changes pushed")
                return jsonify({'success': True, 'message': 'Changes pushed to remote repository'})
            else:
                debug_log(f"✗ Git push failed: {result['stderr']}")
                return jsonify({'success': False, 'error': result['stderr']})
        
        elif action == 'pull':
            debug_log(f"Pulling changes for: {project_path}")
            result = run_command('git pull', cwd=project_path)
            if result['success']:
                debug_log("✓ Changes pulled")
                return jsonify({'success': True, 'message': 'Changes pulled from remote repository'})
            else:
                debug_log(f"✗ Git pull failed: {result['stderr']}")
                return jsonify({'success': False, 'error': result['stderr']})
        
        elif action == 'create-github':
            debug_log(f"Creating GitHub repository for: {project_path}")
            repo_name = data.get('name') or os.path.basename(project_path)
            description = data.get('description', f'Python project: {repo_name}')
            
            # Check if GitHub token is set
            if GITHUB_TOKEN == "your_token_here":
                return jsonify({'success': False, 'error': 'GitHub token not configured. Please update GITHUB_TOKEN in the script.'})
            
            # Create GitHub repository using curl
            create_payload = {
                "name": repo_name,
                "description": description,
                "private": False,
                "auto_init": False
            }
            
            import json as json_module
            create_cmd = f'''curl -s -H "Authorization: token {GITHUB_TOKEN}" \
                            -H "Content-Type: application/json" \
                            -H "Accept: application/vnd.github.v3+json" \
                            -d '{json_module.dumps(create_payload)}' \
                            https://api.github.com/user/repos'''
            
            debug_log(f"Creating GitHub repo with command: {create_cmd[:100]}...")
            result = run_command(create_cmd)
            
            if result['success']:
                try:
                    response_data = json_module.loads(result['stdout'])
                    if 'html_url' in response_data:
                        # Repository created successfully
                        clone_url = response_data['clone_url']
                        html_url = response_data['html_url']
                        
                        # Add remote origin
                        remote_url = clone_url.replace('https://', f'https://{GITHUB_USERNAME}:{GITHUB_TOKEN}@')
                        add_remote_result = run_command(f'git remote add origin {remote_url}', cwd=project_path)
                        
                        if add_remote_result['success']:
                            # Set main branch and push
                            run_command('git branch -M main', cwd=project_path)
                            
                            debug_log(f"✓ GitHub repository created: {html_url}")
                            return jsonify({
                                'success': True, 
                                'message': f'GitHub repository created: {repo_name}',
                                'url': html_url
                            })
                        else:
                            debug_log(f"✗ Failed to add remote: {add_remote_result['stderr']}")
                            return jsonify({'success': False, 'error': f'Repository created but failed to add remote: {add_remote_result["stderr"]}'})
                    
                    elif 'errors' in response_data:
                        error_msg = response_data['errors'][0]['message'] if response_data['errors'] else 'Unknown error'
                        debug_log(f"✗ GitHub API error: {error_msg}")
                        return jsonify({'success': False, 'error': f'GitHub API error: {error_msg}'})
                    
                    else:
                        debug_log(f"✗ Unexpected GitHub response: {result['stdout']}")
                        return jsonify({'success': False, 'error': f'Unexpected response from GitHub API'})
                        
                except json_module.JSONDecodeError as e:
                    debug_log(f"✗ Failed to parse GitHub response: {e}")
                    debug_log(f"Raw response: {result['stdout']}")
                    return jsonify({'success': False, 'error': 'Failed to parse GitHub API response'})
            else:
                debug_log(f"✗ GitHub API call failed: {result['stderr']}")
                return jsonify({'success': False, 'error': f'Failed to create GitHub repository: {result["stderr"]}'})
        
        else:
            return jsonify({'success': False, 'error': f'Unknown git action: {action}'})
        
    except Exception as e:
        debug_log(f"✗ Error in git route: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/save-data', methods=['POST'])
def save_data_route():
    debug_log("API save-data route accessed")
    try:
        data = request.json
        success = save_data(data)
        return jsonify({'success': success})
    except Exception as e:
        debug_log(f"✗ Error in save-data route: {e}")
        return jsonify({'success': False, 'error': str(e)})

debug_log("✓ All routes defined")

# Simplified HTML Template for testing
TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Python Vibe Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .tab-active { background-color: white; color: #2563eb; box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1); }
        .project-card { transition: all 0.2s; }
        .project-card:hover { transform: translateY(-1px); box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }
        .status-indicator { width: 8px; height: 8px; border-radius: 50%; display: inline-block; margin-right: 4px; }
        .status-active { background-color: #10b981; }
        .status-inactive { background-color: #6b7280; }
        .status-changes { background-color: #f59e0b; }
    </style>
</head>
<body class="min-h-screen bg-gray-50">
    <div class="container mx-auto px-6 py-6 max-w-7xl">
        <!-- Header -->
        <div class="mb-8">
            <h1 class="text-3xl font-bold text-gray-900 mb-2">Python Vibe Dashboard</h1>
            <p class="text-gray-600">Your coding workspace with full venv & git integration • <code class="bg-gray-100 px-2 py-1 rounded text-sm">{{ projects_dir }}</code></p>
            
            <!-- Error Log (hidden by default) -->
            <div id="error-log" class="mt-4 bg-red-50 border border-red-200 rounded-lg p-4 hidden">
                <div class="flex justify-between items-center mb-2">
                    <h3 class="text-red-800 font-medium">Recent Errors</h3>
                    <button onclick="clearErrorLog()" class="text-red-600 hover:text-red-800 text-sm">Clear</button>
                </div>
                <div id="error-log-content" class="text-red-700 text-sm font-mono whitespace-pre-wrap max-h-40 overflow-y-auto"></div>
            </div>
        </div>

        <!-- Projects Grid -->
        <div class="flex justify-between items-center mb-4">
            <h2 class="text-xl font-semibold text-gray-900">Python Projects</h2>
            <button onclick="refreshProjects()" class="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                </svg>
                <span>Refresh</span>
            </button>
        </div>
        
        <div id="loading" class="text-center py-8">
            <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p class="mt-2 text-gray-600">Loading projects...</p>
        </div>
        
        <div id="projects-grid" class="grid gap-6 md:grid-cols-2 lg:grid-cols-2 hidden"></div>
    </div>

    <script>
        let currentData = {};

        // Load initial data
        async function loadData() {
            try {
                console.log('Loading data...');
                
                // Add timeout to the fetch request
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout
                
                const response = await fetch('/api/data', {
                    signal: controller.signal
                });
                clearTimeout(timeoutId);
                
                console.log('Response received, status:', response.status);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                console.log('Data parsed successfully');
                
                if (data.error) {
                    throw new Error(data.error);
                }
                
                currentData = data;
                console.log('Data loaded:', currentData);
                console.log(`Found ${currentData.projects ? currentData.projects.length : 0} projects`);
                
                await renderProjects();
                
                // Hide loading, show content
                document.getElementById('loading').style.display = 'none';
                document.getElementById('projects-grid').classList.remove('hidden');
                
                console.log('UI updated successfully');
                
            } catch (error) {
                console.error('Error loading data:', error);
                
                let errorMessage = 'Unknown error occurred';
                if (error.name === 'AbortError') {
                    errorMessage = 'Request timed out after 30 seconds. The server may be busy scanning a large number of projects.';
                } else if (error.message) {
                    errorMessage = error.message;
                }
                
                document.getElementById('loading').innerHTML = `
                    <div class="text-red-600 max-w-md mx-auto">
                        <div class="text-center mb-4">
                            <svg class="mx-auto h-12 w-12 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                            </svg>
                        </div>
                        <h3 class="text-lg font-medium text-red-800 mb-2">Failed to Load Projects</h3>
                        <p class="text-red-700 mb-4">${errorMessage}</p>
                        <div class="space-y-2">
                            <button onclick="loadData()" class="block w-full bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700">
                                Try Again
                            </button>
                            <button onclick="loadDataSimple()" class="block w-full bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700">
                                Load Without Project Scan
                            </button>
                        </div>
                        <div class="mt-4 text-sm text-gray-600">
                            <strong>Debug Info:</strong><br>
                            Check the browser console (F12) and terminal for more details.
                        </div>
                    </div>
                `;
                
                addToErrorLog(`Data loading failed: ${errorMessage}`);
            }
        }

        // Simplified data loading that skips project scanning
        async function loadDataSimple() {
            try {
                console.log('Loading data without project scan...');
                document.getElementById('loading').innerHTML = `
                    <div class="text-center py-8">
                        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                        <p class="mt-2 text-gray-600">Loading basic data...</p>
                    </div>
                `;
                
                // Load just the basic data structure without scanning projects
                currentData = {
                    projects: [],
                    snippets: [],
                    sessions: []
                };
                
                renderProjects();
                
                // Hide loading, show content
                document.getElementById('loading').style.display = 'none';
                document.getElementById('projects-grid').classList.remove('hidden');
                
                showMessage('Loaded in simple mode. Click "Refresh" to scan for projects.', 'success');
                
            } catch (error) {
                console.error('Error in simple loading:', error);
                addToErrorLog(`Simple loading failed: ${error.message}`);
            }
        }

        // Render projects with optimized template
        function renderProjects() {
            console.log('Starting renderProjects...');
            const grid = document.getElementById('projects-grid');
            
            if (!currentData.projects || currentData.projects.length === 0) {
                console.log('No projects to render');
                grid.innerHTML = `
                    <div class="col-span-full text-center py-8 bg-white rounded-lg border border-gray-200">
                        <div class="mb-4">
                            <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z"></path>
                            </svg>
                        </div>
                        <h3 class="text-lg font-medium text-gray-900 mb-2">No Python projects found</h3>
                        <p class="text-gray-500 mb-4">No Python projects found in your projects directory.</p>
                        <button onclick="refreshProjects()" class="text-blue-600 hover:text-blue-800 font-medium">Click to scan for projects</button>
                    </div>`;
                return;
            }

            console.log(`Rendering ${currentData.projects.length} projects...`);
            
            // Build HTML in chunks to avoid blocking the UI
            const projects = currentData.projects;
            let html = '';
            
            for (let i = 0; i < projects.length; i++) {
                const project = projects[i];
                console.log(`Rendering project ${i + 1}/${projects.length}: ${project.name}`);
                
                // Simplified template - removed complex conditionals and heavy SVGs
                html += `
                <div class="project-card bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <div class="flex items-start justify-between mb-4">
                        <div class="flex items-center space-x-2">
                            <div class="w-5 h-5 ${project.type === 'folder' ? 'bg-blue-500' : 'bg-green-500'} rounded"></div>
                            <div>
                                <h3 class="font-semibold text-gray-900">${project.name}</h3>
                                <p class="text-sm text-gray-500">
                                    ${project.type === 'folder' 
                                        ? `${project.pythonFiles || 0} Python files${project.relevantFiles ? ` • ${project.relevantFiles} total files` : ''} • ${project.lastModified}`
                                        : `Python file • ${project.lastModified}`}
                                </p>
                            </div>
                        </div>
                    </div>

                    <div class="flex items-center space-x-4 mb-4">
                        <div class="flex items-center">
                            <span class="w-2 h-2 rounded-full ${project.venv && project.venv.exists ? 'bg-green-500' : 'bg-gray-400'} mr-1"></span>
                            <span class="text-sm text-gray-600">venv ${project.venv && project.venv.exists ? 'exists' : 'missing'}</span>
                        </div>
                        <div class="flex items-center">
                            <span class="w-2 h-2 rounded-full ${project.git && project.git.hasGit ? (project.git.hasChanges ? 'bg-yellow-500' : 'bg-green-500') : 'bg-gray-400'} mr-1"></span>
                            <span class="text-sm text-gray-600">
                                ${project.git && project.git.hasGit ? (project.git.hasChanges ? 'git changes' : 'git clean') : 'no git'}
                            </span>
                        </div>
                    </div>

                    <div class="grid grid-cols-2 gap-2 mb-3">
                        <button onclick="openProject('${project.path}', 'code')" class="px-3 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 transition-colors">
                            Code
                        </button>
                        <button onclick="openProject('${project.path}', 'terminal')" class="px-3 py-2 bg-gray-600 text-white text-sm rounded-md hover:bg-gray-700 transition-colors">
                            Terminal
                        </button>
                    </div>

                    <div class="border-t border-gray-100 pt-3 mb-3">
                        <div class="text-xs font-medium text-gray-500 mb-2">Virtual Environment</div>
                        <div class="flex space-x-1">
                            ${project.venv && project.venv.exists ? 
                                `<button onclick="venvAction('${project.path}', 'activate')" class="text-xs px-2 py-1 bg-green-100 text-green-800 rounded hover:bg-green-200">Activate</button>
                                 <button onclick="venvAction('${project.path}', 'delete')" class="text-xs px-2 py-1 bg-red-100 text-red-800 rounded hover:bg-red-200">Delete</button>` :
                                `<button onclick="venvAction('${project.path}', 'create')" class="text-xs px-2 py-1 bg-blue-100 text-blue-800 rounded hover:bg-blue-200">Create venv</button>`
                            }
                        </div>
                    </div>

                    <div class="border-t border-gray-100 pt-3">
                        <div class="text-xs font-medium text-gray-500 mb-2">Git</div>
                        <div class="flex flex-wrap gap-1">`;
                
                // Git buttons - simplified
                if (project.git && project.git.hasGit) {
                    html += `
                        <button onclick="gitAction('${project.path}', 'status')" class="text-xs px-2 py-1 bg-gray-100 text-gray-800 rounded hover:bg-gray-200">Status</button>
                        <button onclick="gitAction('${project.path}', 'add')" class="text-xs px-2 py-1 bg-yellow-100 text-yellow-800 rounded hover:bg-yellow-200">Add</button>
                        <button onclick="showGitCommit('${project.path}')" class="text-xs px-2 py-1 bg-yellow-100 text-yellow-800 rounded hover:bg-yellow-200">Commit</button>
                        <button onclick="gitAction('${project.path}', 'remote-info')" class="text-xs px-2 py-1 bg-gray-100 text-gray-800 rounded hover:bg-gray-200">Remote Info</button>`;
                    
                    if (project.git.hasRemote) {
                        html += `
                            <button onclick="gitAction('${project.path}', 'push')" class="text-xs px-2 py-1 bg-green-100 text-green-800 rounded hover:bg-green-200">Push</button>
                            <button onclick="gitAction('${project.path}', 'pull')" class="text-xs px-2 py-1 bg-blue-100 text-blue-800 rounded hover:bg-blue-200">Pull</button>`;
                    } else {
                        html += `<button onclick="showCreateGitHub('${project.path}')" class="text-xs px-2 py-1 bg-purple-100 text-purple-800 rounded hover:bg-purple-200">Create GitHub</button>`;
                    }
                } else {
                    html += `<button onclick="gitAction('${project.path}', 'init')" class="text-xs px-2 py-1 bg-blue-100 text-blue-800 rounded hover:bg-blue-200">Init Git</button>`;
                }
                
                html += `
                        </div>
                    </div>
                </div>`;
                
                // Render in batches to avoid blocking
                if (i % 3 === 2 || i === projects.length - 1) {
                    // Use requestAnimationFrame to avoid blocking the UI
                    if (i < projects.length - 1) {
                        await new Promise(resolve => requestAnimationFrame(resolve));
                    }
                }
            }
            
            console.log('Setting innerHTML...');
            grid.innerHTML = html;
            console.log('✓ Projects rendered successfully');
        }

        // Git modal functions
        function showGitCommit(path) {
            showModal('Commit Changes', `
                <div class="mb-4">
                    <label class="block text-sm font-medium text-gray-700 mb-2">Commit Message</label>
                    <input id="commit-message" type="text" placeholder="Enter commit message..." 
                           class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                </div>
            `, () => {
                const message = document.getElementById('commit-message').value.trim();
                if (!message) {
                    alert('Please enter a commit message');
                    return false;
                }
                gitActionWithData(path, 'commit', { message });
                return true;
            });
        }

        function showCreateGitHub(path) {
            const projectName = path.split('/').pop();
            showModal('Create GitHub Repository', `
                <div class="mb-4">
                    <label class="block text-sm font-medium text-gray-700 mb-2">Repository Name</label>
                    <input id="repo-name" type="text" value="${projectName}" 
                           class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                </div>
                <div class="mb-4">
                    <label class="block text-sm font-medium text-gray-700 mb-2">Description (Optional)</label>
                    <input id="repo-description" type="text" placeholder="Brief description of your project..." 
                           class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                </div>
                <div class="text-sm text-gray-500">
                    This will create a public repository on GitHub and add it as a remote to your local git repository.
                </div>
            `, () => {
                const name = document.getElementById('repo-name').value.trim();
                const description = document.getElementById('repo-description').value.trim();
                if (!name) {
                    alert('Please enter a repository name');
                    return false;
                }
                gitActionWithData(path, 'create-github', { name, description });
                return true;
            });
        }

        function showModal(title, content, confirmAction) {
            // Remove existing modal if any
            const existingModal = document.getElementById('git-modal');
            if (existingModal) {
                existingModal.remove();
            }

            const modal = document.createElement('div');
            modal.id = 'git-modal';
            modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
            modal.innerHTML = `
                <div class="bg-white rounded-lg p-6 w-96 max-w-90vw mx-4">
                    <h3 class="text-lg font-semibold mb-4 text-gray-900">${title}</h3>
                    <div class="mb-6">${content}</div>
                    <div class="flex justify-end space-x-3">
                        <button onclick="hideModal()" class="px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 transition-colors">Cancel</button>
                        <button onclick="confirmAction()" class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors">Confirm</button>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            
            // Store the confirm action
            window.currentModalAction = confirmAction;
            
            // Focus first input if any
            const firstInput = modal.querySelector('input');
            if (firstInput) {
                setTimeout(() => firstInput.focus(), 100);
            }
        }

        function hideModal() {
            const modal = document.getElementById('git-modal');
            if (modal) {
                modal.remove();
            }
            window.currentModalAction = null;
        }

        function confirmAction() {
            if (window.currentModalAction) {
                const shouldClose = window.currentModalAction();
                if (shouldClose !== false) {
                    hideModal();
                }
            }
        }

        // Enhanced git action function with data
        async function gitActionWithData(path, action, data = {}) {
            try {
                console.log(`Git action: ${action} for ${path}`, data);
                const response = await fetch(`/api/git/${action}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ path, ...data })
                });
                const result = await response.json();
                
                if (action === 'status' && result.success) {
                    // Show status in an alert for now - could be enhanced with a modal
                    alert(result.output || 'Working directory clean');
                } else if (action === 'remote-info' && result.success) {
                    // Show remote info in a formatted alert
                    const info = result.info;
                    const message = `Remote Information:\n\n` +
                                  `Current Branch: ${info.current_branch}\n\n` +
                                  `Remotes:\n${info.remotes}\n\n` +
                                  `Remote Branches:\n${info.remote_branches}`;
                    alert(message);
                } else if (action === 'create-github' && result.success && result.url) {
                    showMessage(`Repository created! Opening ${result.url}`, 'success');
                    // Optionally open the GitHub repository
                    setTimeout(() => {
                        if (confirm('Would you like to open the GitHub repository?')) {
                            window.open(result.url, '_blank');
                        }
                    }, 1000);
                } else {
                    showMessage(result.message || result.error, result.success ? 'success' : 'error');
                }
                
                if (result.success) {
                    refreshProjects();
                }
            } catch (error) {
                showMessage('Error: ' + error.message, 'error');
            }
        }

        // Project actions
        async function openProject(path, action) {
            try {
                console.log(`Opening project: ${path} with action: ${action}`);
                const response = await fetch('/api/open-project', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ path, action })
                });
                const result = await response.json();
                showMessage(result.message || result.error, result.success ? 'success' : 'error');
            } catch (error) {
                showMessage('Error opening project: ' + error.message, 'error');
            }
        }

        async function venvAction(path, action) {
            try {
                console.log(`Venv action: ${action} for ${path}`);
                const response = await fetch(`/api/venv/${action}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ path })
                });
                const result = await response.json();
                showMessage(result.message || result.error, result.success ? 'success' : 'error');
                if (result.success) {
                    refreshProjects();
                }
            } catch (error) {
                showMessage('Error: ' + error.message, 'error');
            }
        }

        async function gitAction(path, action) {
            // Simple git actions (no extra data needed)
            return gitActionWithData(path, action, {});
        }

        // Utility functions
        async function refreshProjects() {
            try {
                console.log('Refreshing projects...');
                document.getElementById('loading').style.display = 'block';
                document.getElementById('projects-grid').classList.add('hidden');
                
                const response = await fetch('/api/scan-projects');
                const data = await response.json();
                
                if (data.error) {
                    throw new Error(data.error);
                }
                
                currentData = data;
                await renderProjects();
                
                document.getElementById('loading').style.display = 'none';
                document.getElementById('projects-grid').classList.remove('hidden');
                
                showMessage('Projects refreshed!', 'success');
            } catch (error) {
                console.error('Error refreshing projects:', error);
                document.getElementById('loading').innerHTML = 
                    `<div class="text-red-600">Error refreshing projects: ${error.message}</div>`;
                showMessage('Error refreshing projects: ' + error.message, 'error');
            }
        }

        function showMessage(message, type) {
            const timestamp = new Date().toLocaleTimeString();
            console.log(`${timestamp} ${type.toUpperCase()}: ${message}`);
            
            // Add errors to persistent log
            if (type === 'error') {
                addToErrorLog(`[${timestamp}] ${message}`);
            }
            
            // Create a temporary toast message that stays longer for errors
            const toast = document.createElement('div');
            const isError = type === 'error';
            const duration = isError ? 8000 : 3000; // 8 seconds for errors, 3 for success
            
            toast.className = `fixed top-4 right-4 px-6 py-4 rounded-lg text-white z-50 max-w-md shadow-lg ${isError ? 'bg-red-500' : 'bg-green-500'}`;
            toast.style.fontSize = '14px';
            toast.style.lineHeight = '1.4';
            toast.innerHTML = `
                <div class="flex items-start justify-between">
                    <div class="flex-1 pr-2">
                        <strong>${isError ? 'Error' : 'Success'}:</strong><br>
                        <span style="white-space: pre-wrap;">${message}</span>
                    </div>
                    <button onclick="this.parentElement.parentElement.remove()" class="ml-2 text-white hover:text-gray-200 font-bold">×</button>
                </div>
                <div class="mt-2 text-xs opacity-75">Click × to dismiss • Auto-dismiss in ${duration/1000}s</div>
            `;
            
            document.body.appendChild(toast);
            
            // Auto-remove after duration
            setTimeout(() => {
                if (document.body.contains(toast)) {
                    toast.style.opacity = '0';
                    toast.style.transform = 'translateX(100%)';
                    toast.style.transition = 'all 0.3s ease';
                    setTimeout(() => {
                        if (document.body.contains(toast)) {
                            document.body.removeChild(toast);
                        }
                    }, 300);
                }
            }, duration);
        }

        function addToErrorLog(message) {
            const errorLog = document.getElementById('error-log');
            const errorContent = document.getElementById('error-log-content');
            
            // Show the error log if it's hidden
            errorLog.classList.remove('hidden');
            
            // Add the message
            const currentContent = errorContent.textContent;
            errorContent.textContent = currentContent + message + '\n\n';
            
            // Scroll to bottom
            errorContent.scrollTop = errorContent.scrollHeight;
            
            // Limit to last 10 errors
            const lines = errorContent.textContent.split('\n\n');
            if (lines.length > 10) {
                errorContent.textContent = lines.slice(-10).join('\n\n');
            }
        }

        function clearErrorLog() {
            document.getElementById('error-log-content').textContent = '';
            document.getElementById('error-log').classList.add('hidden');
        }

        // Initialize when page loads
        document.addEventListener('DOMContentLoaded', function() {
            console.log('Dashboard initializing...');
            loadData();
        });
    </script>
</body>
</html>
'''

debug_log("✓ Template defined")

# Minimal template for testing
MINIMAL_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard Test</title>
    <style>body { font-family: Arial, sans-serif; margin: 40px; }</style>
</head>
<body>
    <h1>Dashboard Loading Test</h1>
    <p>Projects directory: {{projects_dir}}</p>
    <p>Found {{projects_count}} projects</p>
    <p>If you see this, the basic HTML rendering works.</p>
    <script>
        console.log('Basic template loaded successfully');
        alert('Basic template loaded! The issue might be in the complex template.');
    </script>
</body>
</html>
'''

def main():
    """Main function to start the Flask server"""
    debug_log("=== MAIN FUNCTION STARTING ===")
    
    # Test project scanning
    try:
        debug_log("Testing project scan...")
        projects = scan_projects()
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