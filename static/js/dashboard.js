let currentData = {};

// Load initial data
async function loadData() {
    try {
        console.log('Loading data...');
        
        // Add timeout to the fetch request
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout
        
        const response = await fetch('/api/data', {
            signal: controller.signal
        });
        clearTimeout(timeoutId);
        
        console.log('Response received, status:', response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('Data parsed successfully');
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        currentData = data;
        console.log('Data loaded:', currentData);
        console.log(`Found ${currentData.projects ? currentData.projects.length : 0} projects`);
        
        await renderProjects();
        
        // Hide loading, show content
        document.getElementById('loading').style.display = 'none';
        document.getElementById('projects-grid').classList.remove('hidden');
        
        console.log('UI updated successfully');
        
    } catch (error) {
        console.error('Error loading data:', error);
        
        let errorMessage = 'Unknown error occurred';
        if (error.name === 'AbortError') {
            errorMessage = 'Request timed out after 30 seconds. The server may be busy scanning a large number of projects.';
        } else if (error.message) {
            errorMessage = error.message;
        }
        
        document.getElementById('loading').innerHTML = `
            <div class="text-red-600 max-w-md mx-auto">
                <div class="text-center mb-4">
                    <svg class="mx-auto h-12 w-12 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                </div>
                <h3 class="text-lg font-medium text-red-800 mb-2">Failed to Load Projects</h3>
                <p class="text-red-700 mb-4">${errorMessage}</p>
                <div class="space-y-2">
                    <button onclick="loadData()" class="block w-full bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700">
                        Try Again
                    </button>
                    <button onclick="loadDataSimple()" class="block w-full bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700">
                        Load Without Project Scan
                    </button>
                </div>
                <div class="mt-4 text-sm text-gray-600">
                    <strong>Debug Info:</strong><br>
                    Check the browser console (F12) and terminal for more details.
                </div>
            </div>
        `;
        
        addToErrorLog(`Data loading failed: ${errorMessage}`);
    }
}

// Simplified data loading that skips project scanning
async function loadDataSimple() {
    try {
        console.log('Loading data without project scan...');
        document.getElementById('loading').innerHTML = `
            <div class="text-center py-8">
                <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <p class="mt-2 text-gray-600">Loading basic data...</p>
            </div>
        `;
        
        // Load just the basic data structure without scanning projects
        currentData = {
            projects: [],
            snippets: [],
            sessions: []
        };
        
        renderProjects();
        
        // Hide loading, show content
        document.getElementById('loading').style.display = 'none';
        document.getElementById('projects-grid').classList.remove('hidden');
        
        showMessage('Loaded in simple mode. Click "Refresh" to scan for projects.', 'success');
        
    } catch (error) {
        console.error('Error in simple loading:', error);
        addToErrorLog(`Simple loading failed: ${error.message}`);
    }
}

// Render projects with optimized template
function renderProjects() {
    console.log('Starting renderProjects...');
    const grid = document.getElementById('projects-grid');
    
    if (!currentData.projects || currentData.projects.length === 0) {
        console.log('No projects to render');
        grid.innerHTML = `
            <div class="col-span-full text-center py-8 bg-white rounded-lg border border-gray-200">
                <div class="mb-4">
                    <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z"></path>
                    </svg>
                </div>
                <h3 class="text-lg font-medium text-gray-900 mb-2">No Python projects found</h3>
                <p class="text-gray-500 mb-4">No Python projects found in your projects directory.</p>
                <button onclick="refreshProjects()" class="text-blue-600 hover:text-blue-800 font-medium">Click to scan for projects</button>
            </div>`;
        return;
    }

    console.log(`Rendering ${currentData.projects.length} projects...`);
    
    // Build HTML in chunks to avoid blocking the UI
    const projects = currentData.projects;
    let html = '';
    
    for (let i = 0; i < projects.length; i++) {
        const project = projects[i];
        console.log(`Rendering project ${i + 1}/${projects.length}: ${project.name}`);
        
        // Simplified template - removed complex conditionals and heavy SVGs
        html += `
        <div class="project-card bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div class="flex items-start justify-between mb-4">
                <div class="flex items-center space-x-2">
                    <div class="w-5 h-5 ${project.type === 'folder' ? 'bg-blue-500' : 'bg-green-500'} rounded"></div>
                    <div>
                        <h3 class="font-semibold text-gray-900">${project.name}</h3>
                        <p class="text-sm text-gray-500">
                            ${project.type === 'folder' 
                                ? `${project.pythonFiles || 0} Python files${project.relevantFiles ? ` • ${project.relevantFiles} total files` : ''} • ${project.lastModified}`
                                : `Python file • ${project.lastModified}`}
                        </p>
                    </div>
                </div>
            </div>

            <div class="flex items-center space-x-4 mb-4">
                <div class="flex items-center">
                    <span class="w-2 h-2 rounded-full ${project.venv && project.venv.exists ? 'bg-green-500' : 'bg-gray-400'} mr-1"></span>
                    <span class="text-sm text-gray-600">venv ${project.venv && project.venv.exists ? 'exists' : 'missing'}</span>
                </div>
                <div class="flex items-center">
                    <span class="w-2 h-2 rounded-full ${project.git && project.git.hasGit ? (project.git.hasChanges ? 'bg-yellow-500' : 'bg-green-500') : 'bg-gray-400'} mr-1"></span>
                    <span class="text-sm text-gray-600">
                        ${project.git && project.git.hasGit ? (project.git.hasChanges ? 'git changes' : 'git clean') : 'no git'}
                    </span>
                </div>
            </div>

            <div class="grid grid-cols-2 gap-2 mb-3">
                <button onclick="openProject('${project.path}', 'code')" class="px-3 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 transition-colors">
                    Code
                </button>
                <button onclick="openProject('${project.path}', 'terminal')" class="px-3 py-2 bg-gray-600 text-white text-sm rounded-md hover:bg-gray-700 transition-colors">
                    Terminal
                </button>
            </div>

            <div class="border-t border-gray-100 pt-3 mb-3">
                <div class="text-xs font-medium text-gray-500 mb-2">Virtual Environment</div>
                <div class="flex space-x-1">
                    ${project.venv && project.venv.exists ? 
                        `<button onclick="venvAction('${project.path}', 'activate')" class="text-xs px-2 py-1 bg-green-100 text-green-800 rounded hover:bg-green-200">Activate</button>
                         <button onclick="venvAction('${project.path}', 'delete')" class="text-xs px-2 py-1 bg-red-100 text-red-800 rounded hover:bg-red-200">Delete</button>` :
                        `<button onclick="venvAction('${project.path}', 'create')" class="text-xs px-2 py-1 bg-blue-100 text-blue-800 rounded hover:bg-blue-200">Create venv</button>`
                    }
                </div>
            </div>

            <div class="border-t border-gray-100 pt-3">
                <div class="text-xs font-medium text-gray-500 mb-2">Git</div>
                <div class="flex flex-wrap gap-1">`;
        
        // Git buttons - simplified
        if (project.git && project.git.hasGit) {
            html += `
                <button onclick="gitAction('${project.path}', 'status')" class="text-xs px-2 py-1 bg-gray-100 text-gray-800 rounded hover:bg-gray-200">Status</button>
                <button onclick="gitAction('${project.path}', 'add')" class="text-xs px-2 py-1 bg-yellow-100 text-yellow-800 rounded hover:bg-yellow-200">Add</button>
                <button onclick="showGitCommit('${project.path}')" class="text-xs px-2 py-1 bg-yellow-100 text-yellow-800 rounded hover:bg-yellow-200">Commit</button>
                <button onclick="gitAction('${project.path}', 'remote-info')" class="text-xs px-2 py-1 bg-gray-100 text-gray-800 rounded hover:bg-gray-200">Remote Info</button>`;
            
            if (project.git.hasRemote) {
                html += `
                    <button onclick="gitAction('${project.path}', 'push')" class="text-xs px-2 py-1 bg-green-100 text-green-800 rounded hover:bg-green-200">Push</button>
                    <button onclick="gitAction('${project.path}', 'pull')" class="text-xs px-2 py-1 bg-blue-100 text-blue-800 rounded hover:bg-blue-200">Pull</button>`;
            } else {
                html += `<button onclick="showCreateGitHub('${project.path}')" class="text-xs px-2 py-1 bg-purple-100 text-purple-800 rounded hover:bg-purple-200">Create GitHub</button>`;
            }
        } else {
            html += `<button onclick="gitAction('${project.path}', 'init')" class="text-xs px-2 py-1 bg-blue-100 text-blue-800 rounded hover:bg-blue-200">Init Git</button>`;
        }
        
        html += `
                </div>
            </div>
        </div>`;
        
        // Render in batches to avoid blocking
        if (i % 3 === 2 || i === projects.length - 1) {
            // Use requestAnimationFrame to avoid blocking the UI
            if (i < projects.length - 1) {
                await new Promise(resolve => requestAnimationFrame(resolve));
            }
        }
    }
    
    console.log('Setting innerHTML...');
    grid.innerHTML = html;
    console.log('✓ Projects rendered successfully');
}

// Git modal functions
function showGitCommit(path) {
    showModal('Commit Changes', `
        <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700 mb-2">Commit Message</label>
            <input id="commit-message" type="text" placeholder="Enter commit message..." 
                   class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
        </div>
    `, () => {
        const message = document.getElementById('commit-message').value.trim();
        if (!message) {
            alert('Please enter a commit message');
            return false;
        }
        gitActionWithData(path, 'commit', { message });
        return true;
    });
}

function showCreateGitHub(path) {
    const projectName = path.split('/').pop();
    showModal('Create GitHub Repository', `
        <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700 mb-2">Repository Name</label>
            <input id="repo-name" type="text" value="${projectName}" 
                   class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
        </div>
        <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700 mb-2">Description (Optional)</label>
            <input id="repo-description" type="text" placeholder="Brief description of your project..." 
                   class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
        </div>
        <div class="text-sm text-gray-500">
            This will create a public repository on GitHub and add it as a remote to your local git repository.
        </div>
    `, () => {
        const name = document.getElementById('repo-name').value.trim();
        const description = document.getElementById('repo-description').value.trim();
        if (!name) {
            alert('Please enter a repository name');
            return false;
        }
        gitActionWithData(path, 'create-github', { name, description });
        return true;
    });
}

function showModal(title, content, confirmAction) {
    // Remove existing modal if any
    const existingModal = document.getElementById('git-modal');
    if (existingModal) {
        existingModal.remove();
    }

    const modal = document.createElement('div');
    modal.id = 'git-modal';
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
    modal.innerHTML = `
        <div class="bg-white rounded-lg p-6 w-96 max-w-90vw mx-4">
            <h3 class="text-lg font-semibold mb-4 text-gray-900">${title}</h3>
            <div class="mb-6">${content}</div>
            <div class="flex justify-end space-x-3">
                <button onclick="hideModal()" class="px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 transition-colors">Cancel</button>
                <button onclick="confirmAction()" class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors">Confirm</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Store the confirm action
    window.currentModalAction = confirmAction;
    
    // Focus first input if any
    const firstInput = modal.querySelector('input');
    if (firstInput) {
        setTimeout(() => firstInput.focus(), 100);
    }
}

function hideModal() {
    const modal = document.getElementById('git-modal');
    if (modal) {
        modal.remove();
    }
    window.currentModalAction = null;
}

function confirmAction() {
    if (window.currentModalAction) {
        const shouldClose = window.currentModalAction();
        if (shouldClose !== false) {
            hideModal();
        }
    }
}

// Enhanced git action function with data
async function gitActionWithData(path, action, data = {}) {
    try {
        console.log(`Git action: ${action} for ${path}`, data);
        const response = await fetch(`/api/git/${action}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path, ...data })
        });
        const result = await response.json();
        
        if (action === 'status' && result.success) {
            // Show status in an alert for now - could be enhanced with a modal
            alert(result.output || 'Working directory clean');
        } else if (action === 'remote-info' && result.success) {
            // Show remote info in a formatted alert
            const info = result.info;
            const message = `Remote Information:\n\n` +
                          `Current Branch: ${info.current_branch}\n\n` +
                          `Remotes:\n${info.remotes}\n\n` +
                          `Remote Branches:\n${info.remote_branches}`;
            alert(message);
        } else if (action === 'create-github' && result.success && result.url) {
            showMessage(`Repository created! Opening ${result.url}`, 'success');
            // Optionally open the GitHub repository
            setTimeout(() => {
                if (confirm('Would you like to open the GitHub repository?')) {
                    window.open(result.url, '_blank');
                }
            }, 1000);
        } else {
            showMessage(result.message || result.error, result.success ? 'success' : 'error');
        }
        
        if (result.success) {
            refreshProjects();
        }
    } catch (error) {
        showMessage('Error: ' + error.message, 'error');
    }
}

// Project actions
async function openProject(path, action) {
    try {
        console.log(`Opening project: ${path} with action: ${action}`);
        const response = await fetch('/api/open-project', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path, action })
        });
        const result = await response.json();
        showMessage(result.message || result.error, result.success ? 'success' : 'error');
    } catch (error) {
        showMessage('Error opening project: ' + error.message, 'error');
    }
}

async function venvAction(path, action) {
    try {
        console.log(`Venv action: ${action} for ${path}`);
        const response = await fetch(`/api/venv/${action}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path })
        });
        const result = await response.json();
        showMessage(result.message || result.error, result.success ? 'success' : 'error');
        if (result.success) {
            refreshProjects();
        }
    } catch (error) {
        showMessage('Error: ' + error.message, 'error');
    }
}

async function gitAction(path, action) {
    // Simple git actions (no extra data needed)
    return gitActionWithData(path, action, {});
}

// Utility functions
async function refreshProjects() {
    try {
        console.log('Refreshing projects...');
        document.getElementById('loading').style.display = 'block';
        document.getElementById('projects-grid').classList.add('hidden');
        
        const response = await fetch('/api/scan-projects');
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        currentData = data;
        await renderProjects();
        
        document.getElementById('loading').style.display = 'none';
        document.getElementById('projects-grid').classList.remove('hidden');
        
        showMessage('Projects refreshed!', 'success');
    } catch (error) {
        console.error('Error refreshing projects:', error);
        document.getElementById('loading').innerHTML = 
            `<div class="text-red-600">Error refreshing projects: ${error.message}</div>`;
        showMessage('Error refreshing projects: ' + error.message, 'error');
    }
}

function showMessage(message, type) {
    const timestamp = new Date().toLocaleTimeString();
    console.log(`${timestamp} ${type.toUpperCase()}: ${message}`);
    
    // Add errors to persistent log
    if (type === 'error') {
        addToErrorLog(`[${timestamp}] ${message}`);
    }
    
    // Create a temporary toast message that stays longer for errors
    const toast = document.createElement('div');
    const isError = type === 'error';
    const duration = isError ? 8000 : 3000; // 8 seconds for errors, 3 for success
    
    toast.className = `fixed top-4 right-4 px-6 py-4 rounded-lg text-white z-50 max-w-md shadow-lg ${isError ? 'bg-red-500' : 'bg-green-500'}`;
    toast.style.fontSize = '14px';
    toast.style.lineHeight = '1.4';
    toast.innerHTML = `
        <div class="flex items-start justify-between">
            <div class="flex-1 pr-2">
                <strong>${isError ? 'Error' : 'Success'}:</strong><br>
                <span style="white-space: pre-wrap;">${message}</span>
            </div>
            <button onclick="this.parentElement.parentElement.remove()" class="ml-2 text-white hover:text-gray-200 font-bold">×</button>
        </div>
        <div class="mt-2 text-xs opacity-75">Click × to dismiss • Auto-dismiss in ${duration/1000}s</div>
    `;
    
    document.body.appendChild(toast);
    
    // Auto-remove after duration
    setTimeout(() => {
        if (document.body.contains(toast)) {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            toast.style.transition = 'all 0.3s ease';
            setTimeout(() => {
                if (document.body.contains(toast)) {
                    document.body.removeChild(toast);
                }
            }, 300);
        }
    }, duration);
}

function addToErrorLog(message) {
    const errorLog = document.getElementById('error-log');
    const errorContent = document.getElementById('error-log-content');
    
    // Show the error log if it's hidden
    errorLog.classList.remove('hidden');
    
    // Add the message
    const currentContent = errorContent.textContent;
    errorContent.textContent = currentContent + message + '\n\n';
    
    // Scroll to bottom
    errorContent.scrollTop = errorContent.scrollHeight;
    
    // Limit to last 10 errors
    const lines = errorContent.textContent.split('\n\n');
    if (lines.length > 10) {
        errorContent.textContent = lines.slice(-10).join('\n\n');
    }
}

function clearErrorLog() {
    document.getElementById('error-log-content').textContent = '';
    document.getElementById('error-log').classList.add('hidden');
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard initializing...');
    loadData();
});