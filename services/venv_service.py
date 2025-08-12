"""
Virtual environment management service.
"""
import os

from utils.command_runner import run_command
from utils.time_utils import debug_log


class VenvService:
    """Service for managing Python virtual environments."""
    
    @staticmethod
    def create_venv(project_path):
        """
        Create a virtual environment in the project directory.
        
        Args:
            project_path (str): Path to the project directory
            
        Returns:
            dict: Result with success status and message
        """
        debug_log(f"Creating venv for: {project_path}")
        
        if not project_path or not os.path.exists(project_path):
            return {'success': False, 'error': 'Invalid project path'}
        
        # Create virtual environment
        result = run_command('python3 -m venv venv', cwd=project_path)
        if result['success']:
            debug_log("✓ Venv created successfully")
            return {'success': True, 'message': 'Virtual environment created successfully'}
        else:
            debug_log(f"✗ Venv creation failed: {result['stderr']}")
            return {'success': False, 'error': result['stderr']}
    
    @staticmethod
    def activate_venv(project_path):
        """
        Generate activation script for a virtual environment.
        
        Args:
            project_path (str): Path to the project directory
            
        Returns:
            dict: Result with success status and message
        """
        if not project_path or not os.path.exists(project_path):
            return {'success': False, 'error': 'Invalid project path'}
        
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
            return {'success': True, 'message': 'Opening terminal with activated venv'}
        else:
            return {'success': False, 'error': 'Virtual environment not found'}
    
    @staticmethod
    def delete_venv(project_path):
        """
        Delete a virtual environment.
        
        Args:
            project_path (str): Path to the project directory
            
        Returns:
            dict: Result with success status and message
        """
        if not project_path or not os.path.exists(project_path):
            return {'success': False, 'error': 'Invalid project path'}
        
        # Delete virtual environment
        venv_path = os.path.join(project_path, 'venv')
        if os.path.exists(venv_path):
            result = run_command(f'rm -rf "{venv_path}"')
            return {'success': True, 'message': 'Virtual environment deleted'}
        else:
            return {'success': False, 'error': 'Virtual environment not found'}