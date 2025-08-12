let currentData = {};

async function loadData() {
    try {
        const response = await fetch('/api/data');
        const data = await response.json();
        if (data.error) throw new Error(data.error);
        
        currentData = data;
        renderProjects();
        document.getElementById('loading').style.display = 'none';
        document.getElementById('projects-grid').classList.remove('hidden');
    } catch (error) {
        document.getElementById('loading').innerHTML = `<div class="text-red-600">Error: ${error.message}</div>`;
    }
}

function renderProjects() {
    const grid = document.getElementById('projects-grid');
    
    if (!currentData.projects || currentData.projects.length === 0) {
        grid.innerHTML = '<div class="col-span-full text-center py-8 text-gray-500">No Python projects found</div>';
        return;
    }

    grid.innerHTML = currentData.projects.map(project => `
        <div class="bg-white rounded-lg p-4 shadow">
            <div class="flex items-center mb-2">
                <div class="w-4 h-4 ${project.type === 'folder' ? 'bg-blue-500' : 'bg-green-500'} rounded mr-2"></div>
                <h3 class="font-semibold">${project.name}</h3>
            </div>
            <p class="text-sm text-gray-600 mb-2">${project.pythonFiles || 0} Python files • ${project.lastModified}</p>
            
            <div class="flex space-x-2 mb-3">
                <span class="text-xs px-2 py-1 rounded ${project.venv?.exists ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}">
                    ${project.venv?.exists ? '✓ venv' : '✗ venv'}
                </span>
                <span class="text-xs px-2 py-1 rounded ${getGitStatusColor(project.git)}">
                    ${getGitStatusText(project.git)}
                </span>
            </div>
            
            <div class="grid grid-cols-2 gap-1 mb-3">
                <button onclick="openProject('${project.path}', 'code')" class="px-3 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700">
                    Open Code
                </button>
                <button onclick="openProject('${project.path}', 'terminal')" class="px-3 py-2 bg-gray-600 text-white text-sm rounded hover:bg-gray-700">
                    Terminal
                </button>
            </div>
            
            <div class="border-t pt-3 mb-3">
                <div class="text-xs font-medium text-gray-600 mb-2">Virtual Environment</div>
                <div class="flex gap-1">
                    ${project.venv?.exists ? 
                        `<button onclick="venvAction('${project.path}', 'activate')" class="px-2 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700">Activate</button>
                         <button onclick="venvAction('${project.path}', 'delete')" class="px-2 py-1 bg-red-100 text-red-700 text-xs rounded hover:bg-red-200">Delete</button>` :
                        `<button onclick="venvAction('${project.path}', 'create')" class="px-2 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700">Create venv</button>`
                    }
                </div>
            </div>
            
            <div class="border-t pt-3">
                <div class="text-xs font-medium text-gray-600 mb-2">Git Workflow</div>
                ${project.git?.hasGit ? 
                    renderGitWorkflow(project) :
                    `<button onclick="gitAction('${project.path}', 'init')" class="px-3 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 w-full">Initialize Git</button>`
                }
            </div>
        </div>
    `).join('');
}

function getGitStatusColor(git) {
    if (!git?.hasGit) return 'bg-gray-100 text-gray-500';
    if (git.hasUnstagedChanges) return 'bg-red-100 text-red-700';
    if (git.hasStagedChanges) return 'bg-yellow-100 text-yellow-700';
    return 'bg-green-100 text-green-700';
}

function getGitStatusText(git) {
    if (!git?.hasGit) return '✗ no git';
    if (git.hasUnstagedChanges) return '🔴 unstaged';
    if (git.hasStagedChanges) return '🟡 staged';
    return '✅ clean';
}

function renderGitWorkflow(project) {
    const git = project.git;
    
    if (git.hasUnstagedChanges) {
        // Step 1: Has unstaged changes - show Add button
        return `
            <div class="space-y-2">
                <div class="text-xs text-red-600 mb-1">🔴 Unstaged changes detected</div>
                <div class="flex gap-1">
                    <button onclick="gitAction('${project.path}', 'status')" class="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded hover:bg-gray-200">View Changes</button>
                    <button onclick="gitAction('${project.path}', 'add')" class="px-4 py-2 bg-red-500 text-white text-sm rounded hover:bg-red-600 font-medium">
                        1️⃣ Add Changes
                    </button>
                    ${git.hasRemote ? `<button onclick="gitAction('${project.path}', 'pull')" class="px-2 py-1 bg-purple-500 text-white text-xs rounded hover:bg-purple-600">Pull</button>` : ''}
                </div>
            </div>
        `;
    } else if (git.hasStagedChanges) {
        // Step 2: Has staged changes - show Commit button
        return `
            <div class="space-y-2">
                <div class="text-xs text-yellow-600 mb-1">🟡 Changes staged for commit</div>
                <div class="flex gap-1">
                    <button onclick="gitAction('${project.path}', 'status')" class="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded hover:bg-gray-200">View Staged</button>
                    <button onclick="showCommit('${project.path}')" class="px-4 py-2 bg-yellow-500 text-white text-sm rounded hover:bg-yellow-600 font-medium">
                        2️⃣ Commit Changes
                    </button>
                    ${git.hasRemote ? `<button onclick="gitAction('${project.path}', 'pull')" class="px-2 py-1 bg-purple-500 text-white text-xs rounded hover:bg-purple-600">Pull</button>` : ''}
                </div>
            </div>
        `;
    } else {
        // Step 3: Working directory clean - show Push and other options
        return `
            <div class="space-y-2">
                <div class="text-xs text-green-600 mb-1">✅ Working directory clean</div>
                <div class="flex gap-1 flex-wrap">
                    <button onclick="gitAction('${project.path}', 'status')" class="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded hover:bg-gray-200">Status</button>
                    ${git.hasRemote ? 
                        `<button onclick="gitAction('${project.path}', 'push')" class="px-3 py-1 bg-green-500 text-white text-xs rounded hover:bg-green-600 font-medium">
                            3️⃣ Push
                        </button>
                        <button onclick="gitAction('${project.path}', 'pull')" class="px-2 py-1 bg-purple-500 text-white text-xs rounded hover:bg-purple-600">Pull</button>` :
                        `<button onclick="showCreateGitHub('${project.path}')" class="px-2 py-1 bg-purple-500 text-white text-xs rounded hover:bg-purple-600">Create GitHub</button>`
                    }
                </div>
            </div>
        `;
    }
}

function showCreateGitHub(path) {
    const name = prompt('GitHub repository name:', path.split('/').pop());
    if (name) {
        const description = prompt('Description (optional):');
        gitAction(path, 'create-github', {name, description});
    }
}

async function openProject(path, action) {
    try {
        const response = await fetch('/api/open-project', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({path, action})
        });
        const result = await response.json();
        showMessage(result.message || result.error, result.success ? 'success' : 'error');
    } catch (error) {
        showMessage('Error: ' + error.message, 'error');
    }
}

async function venvAction(path, action) {
    try {
        const response = await fetch(`/api/venv/${action}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({path})
        });
        const result = await response.json();
        showMessage(result.message || result.error, result.success ? 'success' : 'error');
        if (result.success) refreshProjects();
    } catch (error) {
        showMessage('Error: ' + error.message, 'error');
    }
}

async function gitAction(path, action, data = {}) {
    try {
        const response = await fetch(`/api/git/${action}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({path, ...data})
        });
        const result = await response.json();
        
        if (action === 'status') {
            alert(`Git Status for ${path.split('/').pop()}:\n\n${result.output || 'Working directory clean'}`);
        } else if (action === 'create-github' && result.success && result.url) {
            showMessage(`Repository created! Opening ${result.url}`, 'success');
            setTimeout(() => {
                if (confirm('Open GitHub repository in browser?')) {
                    window.open(result.url, '_blank');
                }
            }, 1000);
        } else {
            showMessage(result.message || result.error, result.success ? 'success' : 'error');
        }
        
        if (result.success) {
            // Auto-refresh after git actions to update workflow state
            setTimeout(refreshProjects, 500);
        }
    } catch (error) {
        showMessage('Error: ' + error.message, 'error');
    }
}

function showCommit(path) {
    const message = prompt('Commit message:', 'Update files');
    if (message) gitAction(path, 'commit', {message});
}

async function refreshProjects() {
    document.getElementById('loading').style.display = 'block';
    document.getElementById('projects-grid').classList.add('hidden');
    await loadData();
    showMessage('Projects refreshed', 'success');
}

function showMessage(message, type) {
    const toast = document.createElement('div');
    toast.className = `fixed top-4 right-4 px-4 py-2 rounded text-white shadow-lg z-50 ${type === 'error' ? 'bg-red-500' : 'bg-green-500'}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), type === 'error' ? 5000 : 3000);
}

document.addEventListener('DOMContentLoaded', loadData);