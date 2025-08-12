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
            
            <div class="flex space-x-2 mb-2">
                <span class="text-xs ${project.venv?.exists ? 'text-green-600' : 'text-gray-400'}">venv</span>
                <span class="text-xs ${project.git?.hasGit ? (project.git.hasChanges ? 'text-yellow-600' : 'text-green-600') : 'text-gray-400'}">git</span>
            </div>
            
            <div class="grid grid-cols-2 gap-1 mb-2">
                <button onclick="openProject('${project.path}', 'code')" class="px-2 py-1 bg-blue-600 text-white text-xs rounded">Code</button>
                <button onclick="openProject('${project.path}', 'terminal')" class="px-2 py-1 bg-gray-600 text-white text-xs rounded">Terminal</button>
            </div>
            
            <div class="flex flex-wrap gap-1">
                ${project.venv?.exists ? 
                    `<button onclick="venvAction('${project.path}', 'activate')" class="px-2 py-1 bg-green-100 text-green-800 text-xs rounded">Activate</button>
                     <button onclick="venvAction('${project.path}', 'delete')" class="px-2 py-1 bg-red-100 text-red-800 text-xs rounded">Delete venv</button>` :
                    `<button onclick="venvAction('${project.path}', 'create')" class="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">Create venv</button>`
                }
                ${project.git?.hasGit ? 
                    `<button onclick="gitAction('${project.path}', 'status')" class="px-2 py-1 bg-gray-100 text-gray-800 text-xs rounded">Status</button>
                     <button onclick="gitAction('${project.path}', 'add')" class="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded">Add</button>
                     <button onclick="showCommit('${project.path}')" class="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded">Commit</button>` :
                    `<button onclick="gitAction('${project.path}', 'init')" class="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">Init Git</button>`
                }
            </div>
        </div>
    `).join('');
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
            alert(result.output || 'Working directory clean');
        } else {
            showMessage(result.message || result.error, result.success ? 'success' : 'error');
        }
        
        if (result.success) refreshProjects();
    } catch (error) {
        showMessage('Error: ' + error.message, 'error');
    }
}

function showCommit(path) {
    const message = prompt('Commit message:');
    if (message) gitAction(path, 'commit', {message});
}

async function refreshProjects() {
    document.getElementById('loading').style.display = 'block';
    document.getElementById('projects-grid').classList.add('hidden');
    await loadData();
}

function showMessage(message, type) {
    const toast = document.createElement('div');
    toast.className = `fixed top-4 right-4 px-4 py-2 rounded text-white ${type === 'error' ? 'bg-red-500' : 'bg-green-500'}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

document.addEventListener('DOMContentLoaded', loadData);