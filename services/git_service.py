import os
import json
from utils.command_runner import run_command

class GitService:
    def __init__(self, git_name, git_email, github_username, github_token):
        self.git_name = git_name
        self.git_email = git_email
        self.github_username = github_username
        self.github_token = github_token
    
    def init_repository(self, project_path):
        if not project_path or not os.path.exists(project_path):
            return {'success': False, 'error': 'Invalid project path'}
        result = run_command('git init', cwd=project_path)
        if result['success']:
            run_command(f'git config user.email "{self.git_email}"', cwd=project_path)
            run_command(f'git config user.name "{self.git_name}"', cwd=project_path)
        return {'success': result['success'], 'message': 'Git repository initialized' if result['success'] else result['stderr']}
    
    def add_files(self, project_path):
        if not project_path or not os.path.exists(project_path):
            return {'success': False, 'error': 'Invalid project path'}
        result = run_command('git add .', cwd=project_path)
        return {'success': result['success'], 'message': 'Files added to git' if result['success'] else result['stderr']}
    
    def commit_changes(self, project_path, message='Auto commit'):
        if not project_path or not os.path.exists(project_path):
            return {'success': False, 'error': 'Invalid project path'}
        result = run_command(f'git commit -m "{message}"', cwd=project_path)
        return {'success': result['success'], 'message': 'Changes committed' if result['success'] else result['stderr']}
    
    def get_status(self, project_path):
        if not project_path or not os.path.exists(project_path):
            return {'success': False, 'error': 'Invalid project path'}
        result = run_command('git status --short', cwd=project_path)
        output = result['stdout'] if result['stdout'] else "Working tree clean"
        return {'success': result['success'], 'message': f'Git Status:\\n{output}', 'output': output}
    
    def push_changes(self, project_path):
        result = run_command('git push', cwd=project_path)
        return {'success': result['success'], 'message': 'Changes pushed' if result['success'] else result['stderr']}
    
    def pull_changes(self, project_path):
        result = run_command('git pull', cwd=project_path)
        return {'success': result['success'], 'message': 'Changes pulled' if result['success'] else result['stderr']}
    
    def create_github_repository(self, project_path, repo_name=None, description=None):
        if self.github_token == "your_token_here":
            return {'success': False, 'error': 'GitHub token not configured'}
        
        repo_name = repo_name or os.path.basename(project_path)
        payload = {"name": repo_name, "description": description or f'Python project: {repo_name}', "private": False}
        
        cmd = f'''curl -s -H "Authorization: token {self.github_token}" -H "Content-Type: application/json" -d '{json.dumps(payload)}' https://api.github.com/user/repos'''
        result = run_command(cmd)
        
        if result['success']:
            try:
                data = json.loads(result['stdout'])
                if 'html_url' in data:
                    remote_url = data['clone_url'].replace('https://', f'https://{self.github_username}:{self.github_token}@')
                    run_command(f'git remote add origin {remote_url}', cwd=project_path)
                    run_command('git branch -M main', cwd=project_path)
                    return {'success': True, 'message': f'GitHub repository created: {repo_name}', 'url': data['html_url']}
                return {'success': False, 'error': 'Failed to create repository'}
            except:
                return {'success': False, 'error': 'Failed to parse GitHub response'}
        return {'success': False, 'error': result['stderr']}
    
    def handle_action(self, action, project_path, data=None):
        data = data or {}
        actions = {
            'init': lambda: self.init_repository(project_path),
            'add': lambda: self.add_files(project_path),
            'commit': lambda: self.commit_changes(project_path, data.get('message', 'Auto commit')),
            'status': lambda: self.get_status(project_path),
            'push': lambda: self.push_changes(project_path),
            'pull': lambda: self.pull_changes(project_path),
            'create-github': lambda: self.create_github_repository(project_path, data.get('name'), data.get('description'))
        }
        return actions.get(action, lambda: {'success': False, 'error': f'Unknown action: {action}'})()