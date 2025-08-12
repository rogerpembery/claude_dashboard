import os
from utils.command_runner import run_command

class VenvService:
    @staticmethod
    def create_venv(project_path):
        if not project_path or not os.path.exists(project_path):
            return {'success': False, 'error': 'Invalid project path'}
        result = run_command('python3 -m venv venv', cwd=project_path)
        return {'success': result['success'], 'message': 'Virtual environment created' if result['success'] else result['stderr']}
    
    @staticmethod
    def activate_venv(project_path):
        if not project_path or not os.path.exists(project_path):
            return {'success': False, 'error': 'Invalid project path'}
        venv_path = os.path.join(project_path, 'venv', 'bin', 'activate')
        if os.path.exists(venv_path):
            script = f'tell application "Terminal" to do script "cd \'{project_path}\' && source venv/bin/activate"'
            run_command(f'osascript -e \'{script}\'')
            return {'success': True, 'message': 'Opening terminal with activated venv'}
        return {'success': False, 'error': 'Virtual environment not found'}
    
    @staticmethod
    def delete_venv(project_path):
        if not project_path or not os.path.exists(project_path):
            return {'success': False, 'error': 'Invalid project path'}
        venv_path = os.path.join(project_path, 'venv')
        if os.path.exists(venv_path):
            run_command(f'rm -rf "{venv_path}"')
            return {'success': True, 'message': 'Virtual environment deleted'}
        return {'success': False, 'error': 'Virtual environment not found'}