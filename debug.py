#!/usr/bin/env python3
"""
Simplified Python Vibe Dashboard with better error handling
"""

import sys
import os

print("=== Python Vibe Dashboard Starting ===")

# Check Flask first
try:
    from flask import Flask, render_template_string, jsonify
    print("✓ Flask imported successfully")
except ImportError:
    print("✗ Flask not installed. Installing...")
    import subprocess
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'flask'])
        from flask import Flask, render_template_string, jsonify
        print("✓ Flask installed and imported")
    except Exception as e:
        print(f"✗ Failed to install Flask: {e}")
        input("Press Enter to exit...")
        sys.exit(1)

# Other imports
import json
import subprocess
from datetime import datetime
from pathlib import Path

# Configuration
PROJECTS_DIR = "/Volumes/BaseHDD/python/"
print(f"Projects directory: {PROJECTS_DIR}")
print(f"Directory exists: {os.path.exists(PROJECTS_DIR)}")

app = Flask(__name__)

def scan_projects():
    """Simple project scanner"""
    projects = []
    projects_path = Path(PROJECTS_DIR)
    
    if not projects_path.exists():
        print(f"Warning: {PROJECTS_DIR} doesn't exist")
        return projects
    
    try:
        for item in projects_path.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                python_files = list(item.glob('*.py'))
                if python_files:
                    projects.append({
                        'name': item.name,
                        'path': str(item),
                        'pythonFiles': len(python_files),
                        'lastModified': 'Recently'
                    })
        print(f"Found {len(projects)} projects")
        return projects
    except Exception as e:
        print(f"Error scanning projects: {e}")
        return []

# Simple HTML template
SIMPLE_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Python Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .project { background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .header { background: #2563eb; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .no-projects { text-align: center; padding: 40px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Python Vibe Dashboard</h1>
            <p>{{ projects_dir }}</p>
        </div>
        
        <div id="projects">
            <!-- Projects will be loaded here -->
        </div>
    </div>
    
    <script>
        async function loadProjects() {
            try {
                const response = await fetch('/api/projects');
                const projects = await response.json();
                
                const container = document.getElementById('projects');
                
                if (projects.length === 0) {
                    container.innerHTML = '<div class="no-projects"><h3>No Python projects found</h3><p>Add some .py files to {{ projects_dir }}</p></div>';
                    return;
                }
                
                container.innerHTML = projects.map(project => `
                    <div class="project">
                        <h3>${project.name}</h3>
                        <p>📁 ${project.path}</p>
                        <p>🐍 ${project.pythonFiles} Python files • ${project.lastModified}</p>
                    </div>
                `).join('');
                
            } catch (error) {
                document.getElementById('projects').innerHTML = `
                    <div class="no-projects">
                        <h3>Error loading projects</h3>
                        <p>${error.message}</p>
                    </div>
                `;
            }
        }
        
        // Load projects when page loads
        document.addEventListener('DOMContentLoaded', loadProjects);
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    try:
        return render_template_string(SIMPLE_TEMPLATE, projects_dir=PROJECTS_DIR)
    except Exception as e:
        return f"""
        <h1>Error</h1>
        <p>Error loading dashboard: {str(e)}</p>
        <pre>{repr(e)}</pre>
        """

@app.route('/api/projects')
def get_projects():
    try:
        projects = scan_projects()
        return jsonify(projects)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def main():
    print("\n=== Starting Server ===")
    print("URL: http://localhost:8080")
    
    # Try to open browser
    try:
        import webbrowser
        import threading
        import time
        
        def open_browser():
            time.sleep(1.5)
            webbrowser.open('http://localhost:8080')
            
        threading.Thread(target=open_browser, daemon=True).start()
        print("Browser will open automatically...")
    except:
        print("Open http://localhost:8080 manually")
    
    # Start server
    try:
        print("Starting Flask server...")
        app.run(
            debug=False,
            port=8080,
            host='0.0.0.0',  # Try this instead of 127.0.0.1
            use_reloader=False
        )
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"\n✗ Server error: {e}")
        print(f"Error type: {type(e).__name__}")
        
        # Common solutions
        print("\nPossible solutions:")
        print("1. Try running: sudo python3 dash.py")
        print("2. Try a different port: change port=8080 ")
        print("3. Check if port 8080 is in use: lsof -i :8080")
        
        input("\nPress Enter to exit...")

if __name__ == '__main__':
    main()