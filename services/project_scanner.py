"""
Project scanning service for detecting Python projects in a directory.
"""
import os
from datetime import datetime
from pathlib import Path

from utils.time_utils import get_relative_time, debug_log
from utils.command_runner import run_command


# File scanning constants
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


def check_venv_status(project_path):
    """
    Check if venv exists and if it's currently active.
    
    Args:
        project_path (str): Path to the project directory
        
    Returns:
        dict: venv status information
    """
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
    """
    Get detailed git status for a project.
    
    Args:
        project_path (str): Path to the project directory
        
    Returns:
        dict: Git status information
    """
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


def analyze_project_fast(project_path, python_files, relevant_files):
    """
    Fast project analysis with pre-scanned files.
    
    Args:
        project_path (Path): Path to the project directory
        python_files (list): List of Python files found
        relevant_files (list): List of relevant files found
        
    Returns:
        dict: Project analysis data or None if analysis failed
    """
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
    """
    Analyze a project directory (fallback method).
    
    Args:
        project_path (Path): Path to the project directory
        
    Returns:
        dict: Project analysis data or None if analysis failed
    """
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


def scan_projects(projects_dir):
    """
    Scan the projects directory for Python projects - optimized for speed.
    
    Args:
        projects_dir (str): Path to the projects directory
        
    Returns:
        list: List of discovered Python projects
    """
    debug_log(f"Scanning projects in: {projects_dir}")
    projects = []
    projects_path = Path(projects_dir)
    
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