import subprocess

def run_command(command, cwd=None, timeout=30):
    # Use longer timeout for git push operations
    if 'git push' in command:
        timeout = 120
    
    try:
        result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, shell=True, timeout=timeout)
        return {'success': result.returncode == 0, 'stdout': result.stdout.strip(), 'stderr': result.stderr.strip()}
    except subprocess.TimeoutExpired:
        return {'success': False, 'stderr': 'Command timed out'}
    except Exception as e:
        return {'success': False, 'stderr': str(e)}