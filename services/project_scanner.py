import os
from datetime import datetime
from pathlib import Path
from utils.time_utils import get_relative_time
from utils.command_runner import run_command

SKIP_DIRS = {'__pycache__', '.git', 'venv', '.venv', 'node_modules', 'build', 'dist', '.idea', '.vscode'}

def check_venv_status(project_path):
    venv_path = Path(project_path) / 'venv'
    exists = venv_path.exists() and (venv_path / 'bin' / 'activate').exists()
    return {'exists': exists, 'active': False, 'path': str(venv_path)}

def get_git_status(project_path):
    if not (Path(project_path) / '.git').exists():
        return {'hasGit': False}
    
    branch_result = run_command('git branch --show-current', cwd=project_path)
    status_result = run_command('git status --porcelain', cwd=project_path)
    remote_result = run_command('git remote -v', cwd=project_path)
    
    return {
        'hasGit': True,
        'branch': branch_result['stdout'] if branch_result['success'] else 'main',
        'hasChanges': bool(status_result['stdout']) if status_result['success'] else False,
        'hasRemote': bool(remote_result['stdout']) if remote_result['success'] else False,
        'lastCommit': ''
    }

def analyze_project(project_path, python_files):
    try:
        last_modified = project_path.stat().st_mtime
        if python_files:
            last_modified = max(f.stat().st_mtime for f in python_files[:5])
        
        return {
            "name": project_path.name,
            "path": str(project_path),
            "type": "folder",
            "venv": check_venv_status(project_path),
            "git": get_git_status(project_path),
            "lastModified": get_relative_time(last_modified),
            "pythonFiles": len(python_files),
            "favorite": False
        }
    except:
        return None

def scan_projects(projects_dir):
    projects = []
    projects_path = Path(projects_dir)
    
    if not projects_path.exists():
        projects_path.mkdir(parents=True, exist_ok=True)
        return projects
    
    try:
        items = sorted(projects_path.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)[:30]
        
        for item in items:
            if item.is_dir() and not item.name.startswith('.') and item.name not in SKIP_DIRS:
                python_files = list(item.glob('*.py')) or list(item.glob('**/*.py'))
                if python_files:
                    project = analyze_project(item, python_files)
                    if project:
                        projects.append(project)
            elif item.is_file() and item.suffix == '.py':
                projects.append({
                    "name": item.name,
                    "path": str(item),
                    "type": "file",
                    "venv": {'exists': False, 'active': False},
                    "git": {'hasGit': False},
                    "lastModified": get_relative_time(item.stat().st_mtime),
                    "favorite": False
                })
        return projects
    except:
        return []