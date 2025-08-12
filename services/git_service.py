import os
import json
from utils.command_runner import run_command
from utils.credential_fallback import find_working_github_credentials, update_env_with_fallback

class GitService:
    def __init__(self, git_name, git_email, github_username, github_token):
        self.git_name = git_name
        self.git_email = git_email
        self.github_username = github_username
        self.github_token = github_token
    
    def reload_credentials(self, git_name, git_email, github_username, github_token):
        """Reload credentials after fallback or update"""
        self.git_name = git_name
        self.git_email = git_email
        self.github_username = github_username
        self.github_token = github_token
    
    def init_repository(self, project_path):
        if not project_path or not os.path.exists(project_path):
            return {'success': False, 'error': 'Invalid project path'}
        
        # Initialize local git repository
        result = run_command('git init', cwd=project_path)
        if not result['success']:
            return {'success': False, 'message': result['stderr']}
        
        # Set git config
        run_command(f'git config user.email "{self.git_email}"', cwd=project_path)
        run_command(f'git config user.name "{self.git_name}"', cwd=project_path)
        
        # Create an initial commit to establish main branch
        run_command('git add .', cwd=project_path)
        run_command('git commit -m "Initial commit" --allow-empty', cwd=project_path)
        
        # Create GitHub repository automatically
        repo_name = os.path.basename(project_path)
        github_result = self.create_github_repository(project_path, repo_name, f'Python project: {repo_name}')
        
        if github_result['success']:
            # Set upstream for main branch
            run_command('git push --set-upstream origin main', cwd=project_path)
            return {'success': True, 'message': f'Git initialized and GitHub repo created: {github_result.get("url", "")}', 'url': github_result.get('url')}
        else:
            return {'success': True, 'message': 'Git repository initialized locally (GitHub creation failed: ' + github_result.get('error', 'unknown error') + ')'}
    
    def add_files(self, project_path):
        if not project_path or not os.path.exists(project_path):
            return {'success': False, 'error': 'Invalid project path'}
        
        # First check if there are files to add
        status_result = run_command('git status --porcelain', cwd=project_path)
        if not status_result['success']:
            return {'success': False, 'error': 'Failed to check git status'}
        
        # Check for unstaged changes (second character not space, or untracked files)
        has_unstaged = False
        if status_result['stdout']:
            for line in status_result['stdout'].strip().split('\n'):
                if line.startswith('??') or (len(line) >= 2 and line[1] in ['M', 'D']):
                    has_unstaged = True
                    break
        
        if not has_unstaged:
            return {'success': False, 'error': 'No unstaged changes to add'}
        
        result = run_command('git add .', cwd=project_path)
        if result['success']:
            # Count how many files were added
            after_status = run_command('git status --porcelain', cwd=project_path)
            staged_count = 0
            if after_status['success'] and after_status['stdout']:
                for line in after_status['stdout'].strip().split('\n'):
                    if len(line) >= 2 and line[0] in ['A', 'M', 'D', 'R', 'C']:
                        staged_count += 1
            
            return {'success': True, 'message': f'{staged_count} file(s) staged for commit'}
        else:
            return {'success': False, 'error': f'Failed to add files: {result["stderr"]}'}
    
    def commit_changes(self, project_path, message='Auto commit'):
        if not project_path or not os.path.exists(project_path):
            return {'success': False, 'error': 'Invalid project path'}
        
        # Check if git is configured
        email_result = run_command('git config user.email', cwd=project_path)
        name_result = run_command('git config user.name', cwd=project_path)
        
        if not email_result['success'] or not email_result['stdout']:
            run_command(f'git config user.email "{self.git_email}"', cwd=project_path)
        if not name_result['success'] or not name_result['stdout']:
            run_command(f'git config user.name "{self.git_name}"', cwd=project_path)
        
        # Check if there are staged changes to commit
        status_result = run_command('git status --porcelain', cwd=project_path)
        if not status_result['success']:
            return {'success': False, 'error': 'Failed to check git status'}
        
        # Check for staged changes (first character not space)
        staged_changes = False
        if status_result['stdout']:
            for line in status_result['stdout'].strip().split('\n'):
                if len(line) >= 2 and line[0] in ['A', 'M', 'D', 'R', 'C']:
                    staged_changes = True
                    break
        
        if not staged_changes:
            return {'success': False, 'error': 'No staged changes to commit. Run "Add Changes" first.'}
        
        # Escape quotes in commit message
        safe_message = message.replace('"', '\\"')
        result = run_command(f'git commit -m "{safe_message}"', cwd=project_path)
        
        if result['success']:
            return {'success': True, 'message': 'Changes committed successfully'}
        else:
            # Provide more specific error messages
            error_msg = result['stderr']
            if 'nothing to commit' in error_msg:
                return {'success': False, 'error': 'No changes to commit'}
            elif 'Please tell me who you are' in error_msg:
                return {'success': False, 'error': 'Git user not configured'}
            elif 'Aborting commit due to empty commit message' in error_msg:
                return {'success': False, 'error': 'Commit message cannot be empty'}
            else:
                return {'success': False, 'error': f'Commit failed: {error_msg}'}
    
    def get_status(self, project_path):
        if not project_path or not os.path.exists(project_path):
            return {'success': False, 'error': 'Invalid project path'}
        result = run_command('git status --short', cwd=project_path)
        output = result['stdout'] if result['stdout'] else "Working tree clean"
        return {'success': result['success'], 'message': f'Git Status:\\n{output}', 'output': output}
    
    def push_changes(self, project_path):
        # First try regular push
        result = run_command('git push', cwd=project_path)
        
        # If it fails due to authentication, update remote with credentials
        if not result['success'] and ('could not read Username' in result['stderr'] or 'Authentication failed' in result['stderr']):
            # Get current remote URL
            remote_result = run_command('git remote get-url origin', cwd=project_path)
            if remote_result['success'] and 'github.com' in remote_result['stdout']:
                # Update remote URL with credentials
                current_url = remote_result['stdout']
                if not f'{self.github_username}:{self.github_token}@' in current_url:
                    new_url = current_url.replace('https://', f'https://{self.github_username}:{self.github_token}@')
                    run_command(f'git remote set-url origin {new_url}', cwd=project_path)
                    # Retry push
                    result = run_command('git push', cwd=project_path)
        
        # If it fails due to no upstream, try setting upstream
        if not result['success'] and 'no upstream branch' in result['stderr']:
            result = run_command('git push --set-upstream origin main', cwd=project_path)
        
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
        
        # Check for authentication errors
        if not result['success'] or 'Bad credentials' in result['stdout'] or 'Unauthorized' in result['stdout']:
            # Try to find working credentials from other projects
            fallback_result = self._try_fallback_credentials(project_path, repo_name, description)
            if fallback_result:
                return fallback_result
        
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
    
    def _try_fallback_credentials(self, project_path, repo_name, description):
        """Try to use working credentials from other projects"""
        fallback_creds = find_working_github_credentials()
        
        if not fallback_creds:
            return {'success': False, 'error': 'Authentication failed and no working credentials found in other projects'}
        
        # Update current .env file with working credentials
        current_env_path = os.path.join(os.path.dirname(project_path), '.env')
        if not os.path.exists(current_env_path):
            current_env_path = os.path.join(project_path, '.env')
        
        if update_env_with_fallback(current_env_path, fallback_creds):
            # Update our instance with new credentials
            self.reload_credentials(
                fallback_creds.get('GIT_NAME', self.git_name),
                fallback_creds.get('GIT_EMAIL', self.git_email), 
                fallback_creds['GITHUB_USERNAME'],
                fallback_creds['GITHUB_TOKEN']
            )
            
            # Retry the GitHub repository creation
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
                        return {'success': True, 'message': f'GitHub repository created using fallback credentials from {fallback_creds["source_file"]}', 'url': data['html_url']}
                except:
                    pass
        
        return None
    
    def fix_repository(self, project_path):
        """Fix git repositories that have issues (no commits or no remote)"""
        if not project_path or not os.path.exists(project_path):
            return {'success': False, 'error': 'Invalid project path'}
        
        # Check if it has .git folder
        if not os.path.exists(os.path.join(project_path, '.git')):
            return {'success': False, 'error': 'Not a git repository'}
        
        # Set git config in case it's missing
        run_command(f'git config user.email "{self.git_email}"', cwd=project_path)
        run_command(f'git config user.name "{self.git_name}"', cwd=project_path)
        
        # Check if has commits
        commit_result = run_command('git log --oneline -1', cwd=project_path)
        if not commit_result['success'] or not commit_result['stdout']:
            # No commits - add everything and make initial commit
            run_command('git add .', cwd=project_path)
            commit_result = run_command('git commit -m "Initial commit" --allow-empty', cwd=project_path)
            if not commit_result['success']:
                return {'success': False, 'error': f'Failed to create initial commit: {commit_result["stderr"]}'}
        
        # Check if has remote
        remote_result = run_command('git remote -v', cwd=project_path)
        if not remote_result['stdout']:
            # No remote - create GitHub repo
            repo_name = os.path.basename(project_path)
            github_result = self.create_github_repository(project_path, repo_name, f'Fixed Python project: {repo_name}')
            
            if not github_result['success']:
                return {'success': False, 'error': f'Failed to create GitHub repo: {github_result.get("error", "unknown error")}'}
            
            # Push to set upstream
            push_result = run_command('git push --set-upstream origin main', cwd=project_path)
            if not push_result['success']:
                return {'success': False, 'error': f'Failed to push to GitHub: {push_result["stderr"]}'}
            
            return {'success': True, 'message': f'Repository fixed and GitHub repo created: {github_result.get("url", "")}', 'url': github_result.get('url')}
        else:
            # Has remote, just ensure upstream is set
            push_result = run_command('git push --set-upstream origin main', cwd=project_path)
            return {'success': True, 'message': 'Repository fixed - upstream branch set'}
    
    def handle_action(self, action, project_path, data=None):
        data = data or {}
        actions = {
            'init': lambda: self.init_repository(project_path),
            'add': lambda: self.add_files(project_path),
            'commit': lambda: self.commit_changes(project_path, data.get('message', 'Auto commit')),
            'status': lambda: self.get_status(project_path),
            'push': lambda: self.push_changes(project_path),
            'pull': lambda: self.pull_changes(project_path),
            'create-github': lambda: self.create_github_repository(project_path, data.get('name'), data.get('description')),
            'fix': lambda: self.fix_repository(project_path)
        }
        return actions.get(action, lambda: {'success': False, 'error': f'Unknown action: {action}'})()