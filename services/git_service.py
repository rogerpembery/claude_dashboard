"""
Git management service.
"""
import os
import json

from utils.command_runner import run_command
from utils.time_utils import debug_log


class GitService:
    """Service for managing Git repositories."""
    
    def __init__(self, git_name, git_email, github_username, github_token):
        """
        Initialize GitService with configuration.
        
        Args:
            git_name (str): Git user name
            git_email (str): Git user email  
            github_username (str): GitHub username
            github_token (str): GitHub personal access token
        """
        self.git_name = git_name
        self.git_email = git_email
        self.github_username = github_username
        self.github_token = github_token
    
    def init_repository(self, project_path):
        """
        Initialize a git repository in the project directory.
        
        Args:
            project_path (str): Path to the project directory
            
        Returns:
            dict: Result with success status and message
        """
        debug_log(f"Initializing git for: {project_path}")
        
        if not project_path or not os.path.exists(project_path):
            return {'success': False, 'error': 'Invalid project path'}
        
        # Initialize git repository
        result = run_command('git init', cwd=project_path)
        if result['success']:
            # Set up git config
            run_command(f'git config user.email "{self.git_email}"', cwd=project_path)
            run_command(f'git config user.name "{self.git_name}"', cwd=project_path)
            debug_log("✓ Git initialized successfully")
            return {'success': True, 'message': 'Git repository initialized'}
        else:
            debug_log(f"✗ Git init failed: {result['stderr']}")
            return {'success': False, 'error': result['stderr']}
    
    def add_files(self, project_path):
        """
        Add all files to git staging area.
        
        Args:
            project_path (str): Path to the project directory
            
        Returns:
            dict: Result with success status and message
        """
        debug_log(f"Adding files to git for: {project_path}")
        
        if not project_path or not os.path.exists(project_path):
            return {'success': False, 'error': 'Invalid project path'}
        
        result = run_command('git add .', cwd=project_path)
        if result['success']:
            debug_log("✓ Files added to git")
            return {'success': True, 'message': 'Files added to git staging area'}
        else:
            debug_log(f"✗ Git add failed: {result['stderr']}")
            return {'success': False, 'error': result['stderr']}
    
    def commit_changes(self, project_path, message='Auto commit from Vibe Dashboard'):
        """
        Commit changes with a message.
        
        Args:
            project_path (str): Path to the project directory
            message (str): Commit message
            
        Returns:
            dict: Result with success status and message
        """
        debug_log(f"Committing changes for: {project_path}")
        
        if not project_path or not os.path.exists(project_path):
            return {'success': False, 'error': 'Invalid project path'}
        
        result = run_command(f'git commit -m "{message}"', cwd=project_path)
        if result['success']:
            debug_log("✓ Changes committed")
            return {'success': True, 'message': 'Changes committed successfully'}
        else:
            debug_log(f"✗ Git commit failed: {result['stderr']}")
            return {'success': False, 'error': result['stderr']}
    
    def get_status(self, project_path):
        """
        Get git status for the project.
        
        Args:
            project_path (str): Path to the project directory
            
        Returns:
            dict: Result with success status, message and output
        """
        debug_log(f"Getting git status for: {project_path}")
        
        if not project_path or not os.path.exists(project_path):
            return {'success': False, 'error': 'Invalid project path'}
        
        result = run_command('git status --short', cwd=project_path)
        if result['success']:
            status_output = result['stdout'] if result['stdout'] else "Working tree clean"
            debug_log(f"✓ Git status retrieved: {status_output}")
            return {'success': True, 'message': f'Git Status:\\n{status_output}', 'output': status_output}
        else:
            return {'success': False, 'error': result['stderr']}
    
    def push_changes(self, project_path):
        """
        Push changes to remote repository.
        
        Args:
            project_path (str): Path to the project directory
            
        Returns:
            dict: Result with success status and message
        """
        debug_log(f"Pushing changes for: {project_path}")
        
        if not project_path or not os.path.exists(project_path):
            return {'success': False, 'error': 'Invalid project path'}
        
        result = run_command('git push', cwd=project_path)
        if result['success']:
            debug_log("✓ Changes pushed")
            return {'success': True, 'message': 'Changes pushed to remote repository'}
        else:
            debug_log(f"✗ Git push failed: {result['stderr']}")
            return {'success': False, 'error': result['stderr']}
    
    def pull_changes(self, project_path):
        """
        Pull changes from remote repository.
        
        Args:
            project_path (str): Path to the project directory
            
        Returns:
            dict: Result with success status and message
        """
        debug_log(f"Pulling changes for: {project_path}")
        
        if not project_path or not os.path.exists(project_path):
            return {'success': False, 'error': 'Invalid project path'}
        
        result = run_command('git pull', cwd=project_path)
        if result['success']:
            debug_log("✓ Changes pulled")
            return {'success': True, 'message': 'Changes pulled from remote repository'}
        else:
            debug_log(f"✗ Git pull failed: {result['stderr']}")
            return {'success': False, 'error': result['stderr']}
    
    def create_github_repository(self, project_path, repo_name=None, description=None):
        """
        Create a GitHub repository and add it as remote.
        
        Args:
            project_path (str): Path to the project directory
            repo_name (str, optional): Repository name
            description (str, optional): Repository description
            
        Returns:
            dict: Result with success status, message and URL
        """
        debug_log(f"Creating GitHub repository for: {project_path}")
        
        if not project_path or not os.path.exists(project_path):
            return {'success': False, 'error': 'Invalid project path'}
        
        repo_name = repo_name or os.path.basename(project_path)
        description = description or f'Python project: {repo_name}'
        
        # Check if GitHub token is set
        if self.github_token == "your_token_here":
            return {'success': False, 'error': 'GitHub token not configured. Please update GITHUB_TOKEN in the script.'}
        
        # Create GitHub repository using curl
        create_payload = {
            "name": repo_name,
            "description": description,
            "private": False,
            "auto_init": False
        }
        
        create_cmd = f'''curl -s -H "Authorization: token {self.github_token}" \\
                        -H "Content-Type: application/json" \\
                        -H "Accept: application/vnd.github.v3+json" \\
                        -d '{json.dumps(create_payload)}' \\
                        https://api.github.com/user/repos'''
        
        debug_log(f"Creating GitHub repo with command: {create_cmd[:100]}...")
        result = run_command(create_cmd)
        
        if result['success']:
            try:
                response_data = json.loads(result['stdout'])
                if 'html_url' in response_data:
                    # Repository created successfully
                    clone_url = response_data['clone_url']
                    html_url = response_data['html_url']
                    
                    # Add remote origin
                    remote_url = clone_url.replace('https://', f'https://{self.github_username}:{self.github_token}@')
                    add_remote_result = run_command(f'git remote add origin {remote_url}', cwd=project_path)
                    
                    if add_remote_result['success']:
                        # Set main branch and push
                        run_command('git branch -M main', cwd=project_path)
                        
                        debug_log(f"✓ GitHub repository created: {html_url}")
                        return {
                            'success': True, 
                            'message': f'GitHub repository created: {repo_name}',
                            'url': html_url
                        }
                    else:
                        debug_log(f"✗ Failed to add remote: {add_remote_result['stderr']}")
                        return {'success': False, 'error': f'Repository created but failed to add remote: {add_remote_result["stderr"]}'}
                
                elif 'errors' in response_data:
                    error_msg = response_data['errors'][0]['message'] if response_data['errors'] else 'Unknown error'
                    debug_log(f"✗ GitHub API error: {error_msg}")
                    return {'success': False, 'error': f'GitHub API error: {error_msg}'}
                
                else:
                    debug_log(f"✗ Unexpected GitHub response: {result['stdout']}")
                    return {'success': False, 'error': f'Unexpected response from GitHub API'}
                    
            except json.JSONDecodeError as e:
                debug_log(f"✗ Failed to parse GitHub response: {e}")
                debug_log(f"Raw response: {result['stdout']}")
                return {'success': False, 'error': 'Failed to parse GitHub API response'}
        else:
            debug_log(f"✗ GitHub API call failed: {result['stderr']}")
            return {'success': False, 'error': f'Failed to create GitHub repository: {result["stderr"]}'}
    
    def handle_action(self, action, project_path, data=None):
        """
        Handle various git actions.
        
        Args:
            action (str): The git action to perform
            project_path (str): Path to the project directory
            data (dict, optional): Additional data for the action
            
        Returns:
            dict: Result with success status and message
        """
        data = data or {}
        
        if action == 'init':
            return self.init_repository(project_path)
        elif action == 'add':
            return self.add_files(project_path)
        elif action == 'commit':
            message = data.get('message', 'Auto commit from Vibe Dashboard')
            return self.commit_changes(project_path, message)
        elif action == 'status':
            return self.get_status(project_path)
        elif action == 'push':
            return self.push_changes(project_path)
        elif action == 'pull':
            return self.pull_changes(project_path)
        elif action == 'create-github':
            repo_name = data.get('name')
            description = data.get('description')
            return self.create_github_repository(project_path, repo_name, description)
        else:
            return {'success': False, 'error': f'Unknown git action: {action}'}