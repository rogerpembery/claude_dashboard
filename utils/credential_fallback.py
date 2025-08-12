import os
import json
from pathlib import Path
from utils.command_runner import run_command

def find_working_github_credentials(projects_dir="/Volumes/BaseHDD/python"):
    """Scan projects for working GitHub credentials by testing them"""
    working_creds = None
    projects_path = Path(projects_dir)
    
    if not projects_path.exists():
        return None
    
    # Find all .env files in Python projects
    for item in projects_path.rglob('.env'):
        if item.is_file():
            try:
                env_vars = {}
                with open(item, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and '=' in line and not line.startswith('#'):
                            key, value = line.split('=', 1)
                            env_vars[key.strip()] = value.strip()
                
                # Check if it has GitHub credentials
                if 'GITHUB_TOKEN' in env_vars and 'GITHUB_USERNAME' in env_vars:
                    # Test the credentials by making a simple API call
                    token = env_vars['GITHUB_TOKEN']
                    if test_github_credentials(token):
                        working_creds = {
                            'GITHUB_TOKEN': token,
                            'GITHUB_USERNAME': env_vars.get('GITHUB_USERNAME', ''),
                            'GIT_EMAIL': env_vars.get('GIT_EMAIL', ''),
                            'GIT_NAME': env_vars.get('GIT_NAME', ''),
                            'source_file': str(item)
                        }
                        break
            except Exception:
                continue
    
    return working_creds

def test_github_credentials(token):
    """Test if GitHub token is valid by making a simple API call"""
    try:
        cmd = f'curl -s -H "Authorization: token {token}" https://api.github.com/user'
        result = run_command(cmd, timeout=10)
        
        if result['success'] and result['stdout']:
            data = json.loads(result['stdout'])
            # If we get a login field, the token works
            return 'login' in data
    except Exception:
        pass
    
    return False

def update_env_with_fallback(current_env_path, fallback_creds):
    """Update current .env file with working credentials from fallback"""
    if not fallback_creds:
        return False
    
    try:
        # Read current .env file
        current_lines = []
        if os.path.exists(current_env_path):
            with open(current_env_path, 'r') as f:
                current_lines = f.readlines()
        
        # Update or add GitHub credentials
        updated_lines = []
        updated_keys = set()
        
        for line in current_lines:
            line = line.strip()
            if line and '=' in line and not line.startswith('#'):
                key = line.split('=', 1)[0].strip()
                if key in ['GITHUB_TOKEN', 'GITHUB_USERNAME', 'GIT_EMAIL', 'GIT_NAME']:
                    # Replace with working credentials
                    if key in fallback_creds:
                        updated_lines.append(f"{key}={fallback_creds[key]}\n")
                        updated_keys.add(key)
                    else:
                        updated_lines.append(line + '\n')
                else:
                    updated_lines.append(line + '\n')
            else:
                updated_lines.append(line + '\n')
        
        # Add any missing credentials
        for key in ['GITHUB_TOKEN', 'GITHUB_USERNAME', 'GIT_EMAIL', 'GIT_NAME']:
            if key not in updated_keys and key in fallback_creds:
                updated_lines.append(f"{key}={fallback_creds[key]}\n")
        
        # Write updated .env file
        with open(current_env_path, 'w') as f:
            f.writelines(updated_lines)
        
        return True
    except Exception:
        return False