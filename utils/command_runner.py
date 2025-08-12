"""
Command runner utility for executing shell commands safely.
"""
import subprocess


def run_command(command, cwd=None, capture_output=True):
    """
    Run a shell command and return result.
    
    Args:
        command (str): The command to execute
        cwd (str, optional): Working directory for the command
        capture_output (bool): Whether to capture stdout/stderr
        
    Returns:
        dict: Result with success status, stdout, stderr, and return code
    """
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