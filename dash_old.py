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
import webbrowser
import traceback
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv

# Import our services and utilities
from services.project_scanner import scan_projects
from services.git_service import GitService
from services.venv_service import VenvService
from utils.data_manager import load_data, save_data
from utils.time_utils import debug_log
from utils.command_runner import run_command
import config

# Debug logging is now imported from utils.time_utils

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

# Configuration loaded via config module
debug_log("✓ Configuration loaded")

# Functions moved to services - using load_data from utils.data_manager
# Old functions removed to clean up the code
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
            return render_template('minimal.html', projects_count=len(projects), projects_dir=PROJECTS_DIR)
        
        debug_log("✓ Rendering full template")
        result = render_template('dashboard.html', projects_dir=PROJECTS_DIR, initial_data=json.dumps(data))
        
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

debug_log("✓ Templates externalized")

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