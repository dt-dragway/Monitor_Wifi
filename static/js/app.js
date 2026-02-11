const API_URL = '/api';

// Configuración de SweetAlert2 con tema oscuro/glass
const Toast = Swal.mixin({
    toast: true,
    position: 'top-end',
    showConfirmButton: false,
    timer: 3000,
    timerProgressBar: true,
    background: '#1e293b',
    color: '#fff',
    didOpen: (toast) => {
        toast.addEventListener('mouseenter', Swal.stopTimer)
        toast.addEventListener('mouseleave', Swal.resumeTimer)
    }
});

async function fetchDevices() {
    try {
        const response = await fetch(`${API_URL}/devices`);
        const devices = await response.json();
        renderDevices(devices);
        updateStats(devices);
    } catch (error) {
        console.error('Error fetching devices:', error);
    }
}

function updateStats(devices) {
    const total = devices.length;
    const online = devices.filter(d => d.status === 'online').length;

    // Intrusos = Online + No Confiables
    const intruders = devices.filter(d => !d.is_trusted && d.status === 'online').length;

    document.getElementById('total-count').innerText = total;
    document.getElementById('online-count').innerText = online;
    document.getElementById('intruder-count').innerText = intruders;

    const now = new Date();
    document.getElementById('last-update').innerHTML = `<i class="fas fa-clock mr-1"></i> Actualizado: ${now.toLocaleTimeString()}`;
}

function getDeviceIcon(vendor, alias) {
    const text = (vendor + " " + alias).toLowerCase();

    if (text.includes("win") || text.includes("pc") || text.includes("laptop") || text.includes("desktop") || text.includes("msi") || text.includes("asus")) return '<i class="fab fa-windows text-blue-400"></i>';
    if (text.includes("apple") || text.includes("iphone") || text.includes("mac") || text.includes("ipad")) return '<i class="fab fa-apple text-gray-200"></i>';
    if (text.includes("android") || text.includes("samsung") || text.includes("xiaomi") || text.includes("huawei") || text.includes("pixel")) return '<i class="fab fa-android text-green-400"></i>';
    if (text.includes("tv") || text.includes("chromecast") || text.includes("roku")) return '<i class="fas fa-tv text-purple-400"></i>';
    if (text.includes("printer") || text.includes("hp") || text.includes("epson") || text.includes("canon")) return '<i class="fas fa-print text-yellow-400"></i>';
    if (text.includes("game") || text.includes("playstation") || text.includes("xbox") || text.includes("nintendo")) return '<i class="fas fa-gamepad text-indigo-400"></i>';

    return '<i class="fas fa-network-wired text-gray-400"></i>';
}

let currentTab = 'all';
let currentPage = ITEMS_PER_PAGE = 8;
let allDevices = [];
let trafficStats = {}; // Global store for traffic
let currentView = 'dashboard';

// --- TRAFFIC STATS ---
let lastTotalBytes = 0;
let lastTrafficTime = 0;
let lastDeviceBytes = {};
let deviceSpeeds = {};

async function fetchTrafficStats() {
    try {
        const res = await fetch(`${API_URL}/traffic`);
        if (res.ok) {
            trafficStats = await res.json();

            // --- REAL-TIME NETWORK SPEED CALCULATION ---
            const now = Date.now();
            let currentTotalBytes = 0;
            const timeDiff = (now - lastTrafficTime) / 1000; // seconds

            // Calculate per-device and global total
            Object.entries(trafficStats).forEach(([mac, s]) => {
                const total = (s.down || 0) + (s.up || 0);
                currentTotalBytes += total;

                // Per-Device Speed Calculation
                const macLower = mac.toLowerCase();
                const lastBytes = lastDeviceBytes[macLower]; // undefined on first run

                if (lastTrafficTime > 0 && lastBytes !== undefined) {
                    const diff = total - lastBytes;
                    if (diff >= 0 && timeDiff > 0) {
                        const mbps = ((diff * 8) / 1000000) / timeDiff;
                        deviceSpeeds[macLower] = mbps;
                    }
                }
                lastDeviceBytes[macLower] = total;
            });

            // Global Speed Calculation
            if (lastTrafficTime > 0 && lastTotalBytes > 0) {
                const bytesDiff = currentTotalBytes - lastTotalBytes;

                if (timeDiff > 0 && bytesDiff >= 0) {
                    const mbps = ((bytesDiff * 8) / 1000000) / timeDiff;
                    const speedEl = document.getElementById('dashboard-speed');
                    if (speedEl) speedEl.innerText = mbps.toFixed(2);
                }
            }

            lastTotalBytes = currentTotalBytes;
            lastTrafficTime = now;

            // Re-render only if current view depends on it
            if (currentView === 'dashboard') updateDashboardData(allDevices);
            if (currentView === 'devices') renderDevices(allDevices);
        }
    } catch (e) { console.error("Traffic fetch error", e); }
}

// Monitoring Loop
setInterval(() => {
    fetchTrafficStats();
    if (currentView === 'dashboard') fetchRecentActivity();
}, 1000);
fetchTrafficStats();
fetchRecentActivity();

// Helper for bytes (Modified to prefer KB over B)
function formatBytes(bytes, decimals = 2) {
    if (!+bytes) return '0 KB';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    let i = Math.floor(Math.log(bytes) / Math.log(k));

    // User request: "no me lo represente en b si no en kb"
    // Force at least KB (index 1) unless it's literally 0 (handled above)
    if (i < 1) i = 1;

    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
}

// Nueva función para calcular tiempo offline
function getOfflineTime(lastSeenStr) {
    if (!lastSeenStr) return '';

    try {
        const lastSeen = new Date(lastSeenStr + (lastSeenStr.includes('Z') ? '' : 'Z'));
        const now = new Date();
        const diffMs = now - lastSeen;
        const diffMinutes = Math.floor(diffMs / 60000);

        if (diffMinutes < 60) {
            return `${diffMinutes} min`;
        } else if (diffMinutes < 1440) { // menos de 24 horas
            const hours = Math.floor(diffMinutes / 60);
            return `${hours}h`;
        } else {
            const days = Math.floor(diffMinutes / 1440);
            const hours = Math.floor((diffMinutes % 1440) / 60);
            return hours > 0 ? `${days}d ${hours}h` : `${days}d`;
        }
    } catch (e) {
        return '';
    }
}



// --- VIEW MANAGEMENT (Phase 24: Persistence) ---
function switchView(viewName) {
    // Save state
    localStorage.setItem('currentView', viewName);

    // Hide all views
    document.querySelectorAll('.view-section').forEach(el => el.classList.add('hidden'));

    // Deactivate nav items
    document.querySelectorAll('.nav-item').forEach(el => {
        el.classList.remove('bg-white/5', 'text-white', 'shadow-inner');
        el.classList.add('text-slate-400');
    });

    // Show target view
    const target = document.getElementById(`view-${viewName}`);
    if (target) {
        target.classList.remove('hidden');
        target.classList.add('animate-fade-in');
    }

    // Activate nav item
    const nav = document.getElementById(`nav-${viewName}`);
    if (nav) {
        nav.classList.add('bg-white/5', 'text-white', 'shadow-inner');
        nav.classList.remove('text-slate-400');
    }

    currentView = viewName;
    const titles = {
        'dashboard': 'Resumen General',
        'devices': 'Gestión de Dispositivos',
        'map': 'Mapa de Red',
        'speedtest': 'Monitor de Velocidad'
    };
    if (document.getElementById('page-title')) document.getElementById('page-title').innerText = titles[viewName] || 'Dashboard';

    // View specific logic
    if (viewName === 'speedtest') {
        fetchSpeedHistory();
        setTimeout(() => { if (speedChart) speedChart.resize(); }, 100);
    }
    if (viewName === 'map') fetchTopology();
    if (viewName === 'devices') renderDevices(allDevices);
}

// Ensure defaults with persistence
window.addEventListener('load', () => {
    const savedView = localStorage.getItem('currentView') || 'dashboard';
    switchView(savedView);
});

// Create Global updateStats function with Top Talkers
window.updateDashboardData = function (devices) {
    window.updateStats(devices);
};
// Store monthly stats
window.monthlyStats = {};

async function fetchMonthlyStats() {
    try {
        const res = await fetch(`${API_URL}/traffic/monthly`);
        if (res.ok) {
            window.monthlyStats = await res.json();
            // Trigger UI update if on dashboard
            if (currentView === 'dashboard') updateDashboardData(allDevices);
        }
    } catch (e) {
        console.error("Monthly stats error", e);
    }
}

// Poll monthly stats frequent enough to feel "real-time" (User Request)
setInterval(fetchMonthlyStats, 3000); // 3s polling
fetchMonthlyStats();



window.updateStats = function (devices) {
    const total = devices.length;
    const online = devices.filter(d => d.status === 'online').length;
    const intruders = devices.filter(d => d.status === 'online' && !d.is_trusted && !d.is_blocked).length;

    // Use animateValue if available, else direct set
    if (typeof animateValue === 'function') {
        const getVal = (id) => parseInt(document.getElementById(id).innerText.replace(/,/g, '')) || 0;
        animateValue("total-count", getVal("total-count"), total, 1000);
        animateValue("online-count", getVal("online-count"), online, 1000);
        animateValue("intruder-count", getVal("intruder-count"), intruders, 1000);
    } else {
        document.getElementById('total-count').innerText = total;
        document.getElementById('online-count').innerText = online;
        document.getElementById('intruder-count').innerText = intruders;
    }

    const now = new Date();
    document.getElementById('last-update').innerHTML = `<i class="fas fa-clock mr-1"></i> Actualizado: ${now.toLocaleTimeString()}`;

    // Top Talkers Logic (NOW MONTHLY)
    const list = document.getElementById('top-talkers-list');
    if (!list) return;

    // Change Title to indicate Monthly
    const ttTitle = document.querySelector("#view-dashboard h3 span.text-xs");
    if (ttTitle) ttTitle.innerHTML = "(Mes Actual)";
    // Or find parent via text? Or ID based... 
    // Just in case, let's assume user knows or we can verify ID earlier. 
    // The previous HTML had (Top Talkers) in span. Ideally we update that text.

    // Use MONTHLY stats instead of live trafficStats
    const sourceStats = window.monthlyStats || {};

    // CASE INSENSITIVE LOOKUP
    const getTotal = (mac) => {
        if (!mac) return 0;
        const macLower = mac.toLowerCase();

        // Try direct lookup
        if (sourceStats[macLower]) {
            return (sourceStats[macLower].down || 0) + (sourceStats[macLower].up || 0);
        }

        // Fallback: iterate keys if simple lower case fails (e.g. mixed separators?)
        // Usually lower matches.
        return 0;
    };

    // Filter active talkers (from ALL known devices, not just current list which might be paginated/filtered? 
    // Actually allDevices is usually the full list from fetchDevices)

    // We need to map MACs from monthly stats even if device is offline now?
    // Yes, Top Talkers should show whoever consumed most, even if offline now.
    // So we iterate keys of sourceStats OR devices? 
    // Better to iterate devices to get Alias/Vendor info.
    // Ensure allDevices covers all history? Maybe not. 
    // If a device is gone from ARP scan but present in DB, it should be in allDevices.

    // --- TOP TALKERS PAGINATION ---
    if (!window.topTalkersPage) window.topTalkersPage = 1;
    const itemsPerPage = 6; // Professional consistent pagination

    // Sort logic using ALL devices (Online + Offline) to ensure persistence
    // Filter talkers: Must have > 0 traffic in sourceStats
    const activeTalkers = devices
        .filter(d => getTotal(d.mac) > 0)
        .sort((a, b) => getTotal(b.mac) - getTotal(a.mac));

    const totalTalkers = activeTalkers.length;
    const totalPages = Math.ceil(totalTalkers / itemsPerPage) || 1;

    // Bound page
    if (window.topTalkersPage > totalPages) window.topTalkersPage = totalPages;
    if (window.topTalkersPage < 1) window.topTalkersPage = 1;

    // Slice
    const startIndex = (window.topTalkersPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const topTalkers = activeTalkers.slice(startIndex, endIndex);

    // HTML Update
    list.innerHTML = '';

    if (activeTalkers.length === 0) {
        if (Object.keys(sourceStats).length === 0) {
            list.innerHTML = '<div class="text-slate-500 text-sm italic p-2">Cargando consumo mensual...</div>';
        } else {
            list.innerHTML = '<div class="text-slate-500 text-sm italic p-2">Sin consumo este mes.</div>';
        }
    } else {
        // Max val from the CURRENT PAGE or GLOBAL? Usually local max for bars looks better, or global max?
        // Let's use topTalkers visible max for better bar scaling on widely different pages
        const maxVal = Math.max(...topTalkers.map(d => getTotal(d.mac))) || 1;

        topTalkers.forEach(d => {
            const val = getTotal(d.mac);
            const percent = Math.min((val / maxVal) * 100, 100);
            const icon = getDeviceIcon(d.vendor || "", d.alias || "");
            const isOffline = d.status === 'offline';
            const offlineClass = isOffline ? 'opacity-60 grayscale' : '';

            // Real time speed
            const speedMbps = deviceSpeeds[d.mac ? d.mac.toLowerCase() : ''] || 0;
            let speedHtml = '';
            if (speedMbps > 0.01) { // Filter noise
                const speedText = speedMbps < 1 ?
                    `${(speedMbps * 1000).toFixed(0)} Kbps` :
                    `${speedMbps.toFixed(1)} Mbps`;
                speedHtml = `<span class="text-[10px] text-emerald-400 font-mono animate-pulse mr-2">↓${speedText}</span>`;
            }

            const item = document.createElement('div');
            item.className = `flex items-center gap-3 group cursor-pointer hover:bg-white/5 p-2 rounded-lg transition-colors ${offlineClass}`;
            // Add tooltip or indicator for offline
            if (isOffline) item.title = "Dispositivo Offline (Histórico)";

            item.onclick = function () {
                switchView('devices');
                const search = document.getElementById('device-search');
                if (search) {
                    search.value = d.ip;
                    renderDevices(allDevices);
                }
            };

            item.innerHTML = `
                <div class="flex-shrink-0 w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center border border-white/5 group-hover:border-blue-500/30 transition-colors text-slate-400 relative">
                    ${icon}
                    ${isOffline ? '<span class="absolute -bottom-1 -right-1 w-2.5 h-2.5 bg-slate-600 rounded-full border-2 border-[#0f172a]"></span>' : ''}
                </div>
                <div class="flex-1 min-w-0">
                    <div class="flex justify-between items-center mb-1">
                        <span class="text-sm font-medium text-slate-200 truncate w-24">${d.alias || d.vendor || d.ip}</span>
                        <div class="flex items-center">
                            ${speedHtml}
                            <span class="text-xs text-blue-400 font-mono bg-blue-500/10 px-1.5 py-0.5 rounded">${formatBytes(val)}</span>
                        </div>
                    </div>
                    <div class="w-full bg-slate-700/30 rounded-full h-1.5 overflow-hidden">
                        <div class="bg-gradient-to-r from-blue-600 to-cyan-400 h-1.5 rounded-full transition-all duration-1000" style="width: ${percent}%"></div>
                    </div>
                </div>
            `;
            list.appendChild(item);
        });

        // PAGINATION CONTROLS
        if (totalTalkers > itemsPerPage) {
            const controls = document.createElement('div');
            controls.className = "flex justify-center items-center gap-4 mt-3 pt-2 border-t border-white/5";
            controls.innerHTML = `
                <button onclick="changeTopTalkersPage(-1)" class="p-1 text-slate-400 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed" ${window.topTalkersPage === 1 ? 'disabled' : ''}>
                    <i class="fas fa-chevron-left"></i>
                </button>
                <span class="text-[10px] text-slate-500 font-mono">Página ${window.topTalkersPage} / ${totalPages}</span>
                <button onclick="changeTopTalkersPage(1)" class="p-1 text-slate-400 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed" ${window.topTalkersPage === totalPages ? 'disabled' : ''}>
                    <i class="fas fa-chevron-right"></i>
                </button>
            `;
            list.appendChild(controls);
        }
    }
}

// Pagination helper
window.changeTopTalkersPage = function (delta) {
    if (!window.topTalkersPage) window.topTalkersPage = 1;
    window.topTalkersPage += delta;
    updateStats(allDevices); // Re-render
}

function setTab(tab) {
    currentTab = tab;
    currentPage = 1;
    updateTabsUI();
    renderDevices(allDevices);
}

function updateTabsUI() {
    const tabs = ['all', 'intruder', 'trusted', 'blocked', 'offline'];

    tabs.forEach(t => {
        // Select by data-tab attribute since IDs might be missing
        const btn = document.querySelector(`button[data-tab="${t}"]`);
        if (!btn) return;

        if (t === currentTab) {
            // Active Styles based on type
            let colorClass = "bg-blue-600 shadow-blue-500/50"; // Default All
            if (t === 'intruder') colorClass = "bg-red-600 shadow-red-500/50";
            if (t === 'trusted') colorClass = "bg-emerald-600 shadow-emerald-500/50";
            if (t === 'blocked') colorClass = "bg-slate-700 border border-red-500/30 text-red-400";
            if (t === 'offline') colorClass = "bg-slate-600";

            btn.className = `px-4 py-1.5 rounded-md text-sm font-bold transition-all text-white shadow-lg transform scale-105 ${colorClass}`;
            // Ensure no conflicting hover classes
        } else {
            // Inactive Styles
            btn.className = "px-4 py-1.5 rounded-md text-sm font-medium transition-all text-slate-400 hover:text-white hover:bg-white/5";
        }
    });

    // Also update stats if needed or handled globally
}

function changePage(delta) {
    currentPage += delta;
    renderDevices(allDevices);
}

function renderDevices(devices) {
    allDevices = devices; // Store for re-rendering

    // 1. Filter
    let filtered = devices.filter(d => {
        const isOnline = d.status === 'online';
        const isTrusted = d.is_trusted;
        const isJailed = jailedDevices.includes(d.ip);
        const isLegacyBlocked = blockedDevices.includes(d.mac);
        const isBlocked = isJailed || isLegacyBlocked;

        if (currentTab === 'intruder') return isOnline && !isTrusted && !isBlocked;
        if (currentTab === 'trusted') return isTrusted && isOnline;
        if (currentTab === 'offline') return !isOnline;
        if (currentTab === 'blocked') return isBlocked;
        return true; // all
    });

    // Update Badges
    if (document.getElementById('badge-all')) document.getElementById('badge-all').innerText = devices.length;
    if (document.getElementById('badge-intruder')) document.getElementById('badge-intruder').innerText = devices.filter(d => !d.is_trusted && d.status === 'online' && !jailedDevices.includes(d.ip) && !blockedDevices.includes(d.mac)).length;
    if (document.getElementById('badge-trusted')) document.getElementById('badge-trusted').innerText = devices.filter(d => d.is_trusted && d.status === 'online').length;
    if (document.getElementById('badge-offline')) document.getElementById('badge-offline').innerText = devices.filter(d => d.status === 'offline').length;

    // 2. Sort
    filtered.sort((a, b) => {
        const isBlockedA = jailedDevices.includes(a.ip) || blockedDevices.includes(a.mac);
        const isBlockedB = jailedDevices.includes(b.ip) || blockedDevices.includes(b.mac);
        if (isBlockedA !== isBlockedB) return isBlockedA ? -1 : 1;

        const scoreA = (a.status === 'online' ? 10 : 0) + (!a.is_trusted ? 5 : 0);
        const scoreB = (b.status === 'online' ? 10 : 0) + (!b.is_trusted ? 5 : 0);
        return scoreB - scoreA;
    });

    // 3. Paginate
    const totalPages = Math.ceil(filtered.length / ITEMS_PER_PAGE) || 1;
    if (currentPage < 1) currentPage = 1;
    if (currentPage > totalPages) currentPage = totalPages;

    const start = (currentPage - 1) * ITEMS_PER_PAGE;
    const end = start + ITEMS_PER_PAGE;
    const paginated = filtered.slice(start, end);

    // Update Pagination UI
    if (document.getElementById('pagination-info')) document.getElementById('pagination-info').innerText = `${filtered.length > 0 ? start + 1 : 0}-${Math.min(end, filtered.length)} de ${filtered.length}`;
    if (document.getElementById('btn-prev')) document.getElementById('btn-prev').disabled = currentPage === 1;
    if (document.getElementById('btn-next')) document.getElementById('btn-next').disabled = currentPage === totalPages;

    // Render Grid (DOM Diffing)
    const list = document.getElementById('device-list');
    if (!list) return;

    if (paginated.length === 0) {
        list.innerHTML = `
            <div class="p-12 text-center text-slate-500">
                <i class="fas fa-filter text-4xl mb-4 opacity-30"></i>
                <p>No hay dispositivos en esta categoría.</p>
            </div>`;
        return;
    }

    // Helper to get traffic
    const getTraffic = (mac) => trafficStats[mac] || { down: 0, up: 0 };

    // Mark current children
    const currentIds = Array.from(list.children).map(c => c.id).filter(id => id);
    const newIds = paginated.map(d => `device-${d.mac}`);

    // Remove stale
    Array.from(list.children).forEach(child => {
        if (child.id && !newIds.includes(child.id)) {
            child.remove();
        }
    });

    // Remove placeholder if present
    if (list.querySelector('.text-slate-500')) list.innerHTML = '';

    paginated.forEach(device => {
        const isOnline = device.status === 'online';
        const isTrusted = device.is_trusted;
        const isJailed = jailedDevices.includes(device.ip);
        const isLegacyBlocked = blockedDevices.includes(device.mac);
        const isBlocked = isJailed || isLegacyBlocked;
        const tStats = getTraffic(device.mac);

        const statusClass = isBlocked ? 'bg-slate-900/40 opacity-75 grayscale' :
            isOnline ? (isTrusted ? 'bg-emerald-900/10' : 'bg-red-900/10') :
                'bg-slate-800/20 opacity-60 grayscale';

        const statusBorder = isBlocked ? 'border-red-900/30 hover:border-red-500/50' :
            isOnline ? (isTrusted ? 'border-emerald-500/20 hover:border-emerald-500/40' : 'border-red-500/20 hover:border-red-500/40') :
                'border-slate-700/30 hover:border-slate-500/30';

        const cardId = `device-${device.mac}`;
        let item = document.getElementById(cardId);

        const innerHTML = `
            ${isBlocked ? `<div class="absolute inset-0 flex items-center justify-center pointer-events-none bg-black/50 z-20"><i class="fas fa-lock text-5xl text-red-500/40 -rotate-12 drop-shadow-lg"></i></div>` : ''}
            <div class="flex items-center w-full md:w-auto mb-3 md:mb-0 relative z-10 gap-4">
                <div class="w-12 h-12 rounded-xl flex items-center justify-center bg-slate-800/80 text-xl shadow-lg border border-white/5 relative group-hover:bg-slate-700 transition-colors">
                    ${getDeviceIcon(device.vendor || "", device.alias || "")}
                    ${isOnline && !isBlocked ? '<div class="absolute -bottom-1 -right-1 w-3 h-3 bg-emerald-500 rounded-full border-2 border-slate-900 shadow-lg shadow-emerald-500/50"></div>' : ''}
                    ${isBlocked ? '<div class="absolute -bottom-1 -right-1 w-3 h-3 bg-red-500 rounded-full border-2 border-slate-900 shadow-lg shadow-red-500/50"></div>' : ''}
                </div>
                <div>
                    <div class="flex items-center gap-2">
                        <h3 class="font-bold text-base text-slate-100 group-hover:text-blue-300 transition-colors">${device.alias || device.vendor || 'Dispositivo Desconocido'}</h3>
                        ${isBlocked ? '<span class="px-1.5 py-0.5 rounded text-[10px] bg-red-900/40 text-red-400 border border-red-800/50 font-bold uppercase tracking-wider">Bloqueado</span>' : ''}
                        ${!isTrusted && isOnline && !isBlocked ? '<span class="px-1.5 py-0.5 rounded text-[10px] bg-red-500/10 text-red-400 border border-red-500/20 font-bold uppercase tracking-wider animate-pulse">Intruso</span>' : ''}
                        ${!isOnline ? `<span class="px-1.5 py-0.5 rounded text-[10px] bg-slate-800 text-slate-500 font-mono uppercase">Offline ${getOfflineTime(device.last_seen) ? '· ' + getOfflineTime(device.last_seen) : ''}</span>` : ''}
                    </div>
                    <div class="text-xs text-slate-500 mt-1 font-mono flex flex-wrap gap-3 items-center">
                        <span title="IP Address" class="hover:text-slate-300 cursor-help transition-colors"><i class="fas fa-ethernet mr-1.5"></i>${device.ip}</span>
                        <span title="MAC Address" class="hover:text-slate-300 cursor-help transition-colors"><i class="fas fa-fingerprint mr-1.5"></i>${device.mac}</span>
                        ${device.interface ? `<span class="px-1 py-0.5 rounded bg-slate-800/80 border border-slate-700/50 text-[10px] text-slate-400 font-sans tracking-wide">${device.interface}</span>` : ''}
                    </div>
                </div>
            </div>

            <!-- Traffic Stats -->
            <div class="hidden lg:flex w-48 px-4 border-l border-r border-white/5 mx-6 opacity-80 group-hover:opacity-100 transition-opacity flex-col justify-center gap-1">
                 <div class="flex justify-between text-[10px] font-mono text-slate-400">
                    <span><i class="fas fa-arrow-down text-blue-500 mr-1"></i>${formatBytes(tStats.down)}</span>
                    <span><i class="fas fa-arrow-up text-green-500 mr-1"></i>${formatBytes(tStats.up)}</span>
                </div>
                <div class="w-full bg-slate-800/50 rounded-full h-1 flex overflow-hidden">
                     <div class="bg-blue-500 h-full" style="width: 50%"></div>
                     <div class="bg-green-500 h-full" style="width: 50%"></div>
                </div>
            </div>
            
            <!-- Actions -->
            <div class="flex gap-2 relative z-10 w-full md:w-auto justify-end mt-3 md:mt-0">
                 <button onclick="showTrafficHistory('${device.mac}')" class="w-8 h-8 rounded-lg bg-cyan-500/10 hover:bg-cyan-600 text-cyan-500 hover:text-white transition-all border border-cyan-500/20 flex items-center justify-center" title="Historial de Tráfico">
                    <i class="fas fa-chart-line text-xs"></i>
                </button>

                 ${!isTrusted ? `
                    <button onclick="setTrust('${device.mac}', true)" class="w-8 h-8 rounded-lg bg-emerald-500/10 hover:bg-emerald-500 text-emerald-500 hover:text-white transition-all border border-emerald-500/20 flex items-center justify-center" title="Hacer de Confianza">
                        <i class="fas fa-check text-xs"></i>
                    </button>
                ` : `
                    <button onclick="setTrust('${device.mac}', false)" class="w-8 h-8 rounded-lg bg-slate-800 hover:bg-orange-500 text-slate-400 hover:text-white transition-all border border-slate-700 hover:border-orange-500 flex items-center justify-center" title="Quitar de Confianza">
                        <i class="fas fa-ban text-xs"></i>
                    </button>
                `}
                ${isBlocked ? `
                    <button onclick="unwarnDevice('${device.ip}'); unblockDevice('${device.mac}')" class="w-8 h-8 rounded-lg bg-slate-800 hover:bg-slate-600 text-slate-400 hover:text-white transition-all border border-slate-700 flex items-center justify-center" title="Desbloquear">
                        <i class="fas fa-unlock text-xs"></i>
                    </button>
                ` : `
                    <button onclick="warnDevice('${device.ip}')" class="w-8 h-8 rounded-lg bg-red-500/10 hover:bg-red-600 text-red-500 hover:text-white transition-all border border-red-500/20 shadow-lg shadow-red-500/10 flex items-center justify-center" title="BLOQUEAR">
                        <i class="fas fa-lock text-xs"></i>
                    </button>
                `}
                <button onclick="editAlias('${device.mac}', '${device.alias || ''}')" class="w-8 h-8 rounded-lg bg-blue-500/10 hover:bg-blue-600 text-blue-500 hover:text-white transition-all border border-blue-500/20 flex items-center justify-center" title="Editar Nombre">
                    <i class="fas fa-pen text-xs"></i>
                </button>
                <button onclick="triggerDeepScan('${device.ip}')" class="w-8 h-8 rounded-lg bg-purple-500/10 hover:bg-purple-600 text-purple-500 hover:text-white transition-all border border-purple-500/20 flex items-center justify-center" title="Scan Nmap">
                    <i class="fas fa-search text-xs"></i>
                </button>
                <button onclick="triggerAudit('${device.ip}')" class="w-8 h-8 rounded-lg bg-pink-500/10 hover:bg-pink-600 text-pink-500 hover:text-white transition-all border border-pink-500/20 flex items-center justify-center" title="Auditoría de Seguridad (Vulns)">
                    <i class="fas fa-bug text-xs"></i>
                </button>
            </div>`;

        if (!item) {
            // Create new
            item = document.createElement('div');
            item.id = cardId;
            item.className = `p-4 rounded-xl border backdrop-blur-sm transition-all hover:scale-[1.01] ${statusClass} ${statusBorder} flex flex-col md:flex-row justify-between items-center mb-3 relative overflow-hidden group`;
            item.innerHTML = innerHTML;
            list.appendChild(item);
        } else {
            // Update existing
            // Only update className and innerHTML if changed to save DOM (simplified: just update)
            // Actually, updating innerHTML destroys event listeners if any were added via split code, but we use inline onclicks
            // To avoid "jump", we update properties.
            item.className = `p-4 rounded-xl border backdrop-blur-sm transition-all hover:scale-[1.01] ${statusClass} ${statusBorder} flex flex-col md:flex-row justify-between items-center mb-3 relative overflow-hidden group`;
            // Check if innerHTML needs update? (Comparing large strings is expensive, maybe just write it)
            // To be super smooth, we could check. But writing innerHTML is fast enough if not recreating node.
            if (item.innerHTML !== innerHTML) item.innerHTML = innerHTML;

            // Ensure order: if item is not the last child, or correct index?
            // Just appending moves it to end. If we iterate in order, this effectively sorts the DOM.
            list.appendChild(item);
        }
    });
}

// New Function for History
async function showTrafficHistory(mac) {
    if (!mac) return;

    Swal.fire({
        title: 'Historial de Tráfico',
        html: `
            <div id="history-buttons" class="flex flex-wrap justify-center gap-2 mb-4">
                <button data-period="24h" class="px-3 py-1 bg-slate-700 hover:bg-slate-600 transition-colors rounded text-xs select-period" onclick="loadTrafficChart('${mac}', '24h')">24h</button>
                <button data-period="7d" class="px-3 py-1 bg-slate-700 hover:bg-slate-600 transition-colors rounded text-xs select-period" onclick="loadTrafficChart('${mac}', '7d')">7 Días</button>
                <button data-period="30d" class="px-3 py-1 bg-slate-700 hover:bg-slate-600 transition-colors rounded text-xs select-period" onclick="loadTrafficChart('${mac}', '30d')">30 Días</button>
                <button data-period="365d" class="px-3 py-1 bg-slate-700 hover:bg-slate-600 transition-colors rounded text-xs select-period" onclick="loadTrafficChart('${mac}', '365d')">1 Año</button>
                <button data-period="all" class="px-3 py-1 bg-slate-700 hover:bg-slate-600 transition-colors rounded text-xs select-period" onclick="loadTrafficChart('${mac}', 'all')">Todo</button>
            </div>
            <div class="h-64 relative">
                <div id="chart-loader" class="absolute inset-0 bg-slate-900/80 flex items-center justify-center z-10 hidden">
                    <i class="fas fa-spinner fa-spin text-blue-500 text-3xl"></i>
                </div>
                <canvas id="trafficHistoryChart"></canvas>
            </div>
        `,
        width: '700px',
        background: '#1e293b',
        color: '#fff',
        showConfirmButton: false,
        didOpen: () => {
            // Initial load
            loadTrafficChart(mac, '24h');
        }
    });
}

window.loadTrafficChart = async (mac, period) => {
    // 1. Update Buttons Visual State
    const container = document.getElementById('history-buttons');
    if (container) {
        container.querySelectorAll('button').forEach(btn => {
            btn.classList.remove('bg-blue-600', 'text-white', 'ring-2', 'ring-blue-400');
            btn.classList.add('bg-slate-700', 'text-slate-300');
        });
        const activeBtn = container.querySelector(`button[data-period="${period}"]`);
        if (activeBtn) {
            activeBtn.classList.remove('bg-slate-700', 'text-slate-300');
            activeBtn.classList.add('bg-blue-600', 'text-white', 'ring-2', 'ring-blue-400');
        }
    }

    // 2. Show Loader
    const loader = document.getElementById('chart-loader');
    if (loader) loader.classList.remove('hidden');

    try {
        const res = await fetch(`${API_URL}/traffic/history/${mac}?period=${period}`);
        if (!res.ok) throw new Error("Error fetching history");

        const data = await res.json();

        const ctx = document.getElementById('trafficHistoryChart');
        if (!ctx) return; // Closed modal?

        // Destroy old chart
        if (window.myTrafficChart) {
            window.myTrafficChart.destroy();
            window.myTrafficChart = null;
        }

        // Process Data
        // If data is dense, maybe aggregate? For now, raw points.
        const labels = data.map(d => new Date(d.timestamp + "Z").toLocaleString());
        const down = data.map(d => d.bytes_down);
        const up = data.map(d => d.bytes_up);

        if (data.length === 0) {
            // Show empty state? Or empty chart.
            // Let chart render empty axes or handle visual feedback
        }

        // Create Chart
        window.myTrafficChart = new Chart(ctx.getContext('2d'), {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Descarga',
                        data: down,
                        borderColor: '#3b82f6', // blue-500
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'Subida',
                        data: up,
                        borderColor: '#10b981', // emerald-500
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        tension: 0.4,
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: (val) => formatBytes(val, 0),
                            color: '#94a3b8'
                        },
                        grid: { color: '#334155' }
                    },
                    x: {
                        ticks: { color: '#94a3b8', maxTicksLimit: 8 },
                        grid: { display: false }
                    }
                },
                plugins: {
                    legend: { labels: { color: '#fff' } },
                    tooltip: {
                        backgroundColor: '#0f172a',
                        titleColor: '#fff',
                        bodyColor: '#cbd5e1',
                        borderColor: '#334155',
                        borderWidth: 1,
                        callbacks: {
                            label: function (context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                if (context.parsed.y !== null) {
                                    label += formatBytes(context.parsed.y);
                                }
                                return label;
                            }
                        }
                    }
                }
            }
        });

    } catch (e) {
        console.error(e);
        // Show error message in chart area
        const ctx = document.getElementById('trafficHistoryChart');
        if (ctx && ctx.parentNode) ctx.parentNode.innerHTML = '<div class="flex items-center justify-center h-full text-red-400">Error cargando datos</div>';
    } finally {
        // Hide Loader
        if (loader) loader.classList.add('hidden');
    }
};

function animateValue(id, start, end, duration) {
    if (start === end) return;
    const range = end - start;
    let current = start;
    const increment = end > start ? 1 : -1;
    const stepTime = Math.abs(Math.floor(duration / range));
    const obj = document.getElementById(id);
    const timer = setInterval(function () {
        current += increment;
        obj.innerHTML = current;
        if (current == end) {
            clearInterval(timer);
        }
    }, stepTime);
}

async function setTrust(mac, trustState) {
    const result = await Swal.fire({
        title: trustState ? '¿Confiar en este dispositivo?' : '¿Marcar como desconocido?',
        text: trustState ? "Se marcará en verde y no generará alertas." : "Volverá a aparecer como posible intruso.",
        icon: trustState ? 'question' : 'warning',
        showCancelButton: true,
        confirmButtonColor: trustState ? '#10b981' : '#f59e0b',
        cancelButtonColor: '#64748b',
        confirmButtonText: trustState ? 'Sí, confiar' : 'Sí, desconfiar',
        background: '#1e293b',
        color: '#fff'
    });

    if (result.isConfirmed) {
        try {
            await fetch(`${API_URL}/devices/${mac}/trust?is_trusted=${trustState}`, { method: 'POST' });
            Toast.fire({ icon: 'success', title: 'Estado actualizado correctamente' });
            fetchDevices();
        } catch (e) {
            Swal.fire({ icon: 'error', title: 'Error', text: 'No se pudo actualizar el estado', background: '#1e293b', color: '#fff' });
        }
    }
}

async function editAlias(mac, currentAlias) {
    const { value: newAlias } = await Swal.fire({
        title: 'Nombrar Dispositivo',
        input: 'text',
        inputValue: currentAlias,
        inputLabel: 'Asigne un nombre para identificarlo fácilmente',
        inputPlaceholder: 'Ej: Laptop de Juan',
        showCancelButton: true,
        background: '#1e293b',
        color: '#fff',
        inputAttributes: {
            autocapitalize: 'off'
        },
        customClass: {
            input: 'bg-gray-700 text-white border-gray-600 focus:ring-blue-500 focus:border-blue-500'
        }
    });

    if (newAlias !== null && newAlias !== currentAlias) {
        try {
            await fetch(`${API_URL}/devices/${mac}/alias?alias=${encodeURIComponent(newAlias)}`, { method: 'POST' });
            Toast.fire({ icon: 'success', title: 'Nombre actualizado' });
            fetchDevices();
        } catch (e) {
            Toast.fire({ icon: 'error', title: 'Error al actualizar nombre' });
        }
    }
}

function blockDevice(mac) {
    Swal.fire({
        title: 'Funcionalidad Restringida',
        text: "El bloqueo de MAC requiere acceso directo a la configuración de su Router o hardware específico de firewall. Esta versión solo monitorea.",
        icon: 'info',
        background: '#1e293b',
        color: '#fff',
        confirmButtonColor: '#3b82f6'
    });
}

async function triggerScan() {
    const btn = document.querySelector('button[onclick="triggerScan()"]');

    Toast.fire({ icon: 'info', title: 'Iniciando escaneo de red...' });

    try {
        await fetch(`${API_URL}/scan`, { method: 'POST' });
        // No bloqueamos el botón visualmente mucho tiempo, el toast avisa.
        setTimeout(fetchDevices, 2000);
    } catch (e) {
        console.error(e);
    }
}

async function triggerDeepScan(ip) {
    if (!ip) return;

    // Mostrar loader
    Swal.fire({
        title: 'Escaneo Profundo en curso...',
        text: `Analizando ${ip} con Nmap (Detectando OS y Puertos). Esto puede tardar unos segundos.`,
        icon: 'info',
        allowOutsideClick: false,
        showConfirmButton: false,
        background: '#1e293b',
        color: '#fff',
        willOpen: () => {
            Swal.showLoading()
        }
    });

    try {
        const response = await fetch(`${API_URL}/scan/${ip}/deep`, { method: 'POST' });
        const result = await response.json();

        Swal.close(); // Cerrar loader

        if (result.success) {
            const data = result.data;
            const portsList = data.ports.length > 0
                ? `<ul style="text-align: left; margin-top: 10px;">${data.ports.map(p => `<li>🔹 ${p}</li>`).join('')}</ul>`
                : "No se detectaron puertos abiertos (o firewall activo).";

            Swal.fire({
                title: 'Resultados del Escaneo',
                html: `
                    <div style="text-align: left;">
                        <p><strong>IP:</strong> ${ip}</p>
                        <p><strong>OS Detectado:</strong> ${data.os || 'Desconocido'}</p>
                        <p><strong>Hostname (Nmap):</strong> ${data.hostname || 'No resuelto'}</p>
                        <hr style="margin: 10px 0; border-color: #475569;">
                        <p><strong>Puertos Abiertos:</strong></p>
                        ${portsList}
                    </div>
                `,
                icon: 'success',
                background: '#1e293b',
                color: '#fff'
            });
        } else {
            Swal.fire({
                title: 'Error en Escaneo',
                text: result.error || "No se pudo completar el análisis.",
                icon: 'error',
                background: '#1e293b',
                color: '#fff'
            });
        }
    } catch (e) {
        Swal.fire({
            title: 'Error de Conexión',
            text: "Fallo al comunicar con el servidor.",
            icon: 'error',
            background: '#1e293b',
            color: '#fff'
        });
    }
}

async function triggerAudit(ip) {
    if (!ip) return;

    // Mostrar loader
    Swal.fire({
        title: 'Auditoría de Seguridad (CVEs)',
        text: `Ejecutando scripts de vulnerabilidad en ${ip}. ESTO PUEDE TARDAR VARIOS MINUTOS. Por favor espere...`,
        icon: 'warning',
        allowOutsideClick: false,
        showConfirmButton: false,
        background: '#1e293b',
        color: '#fff',
        willOpen: () => {
            Swal.showLoading()
        }
    });

    try {
        const response = await fetch(`${API_URL}/scan/${ip}/audit`, { method: 'POST' });
        const result = await response.json();

        Swal.close();

        if (result.error) {
            Swal.fire({
                title: 'Error en Auditoría',
                text: result.error,
                icon: 'error',
                background: '#1e293b',
                color: '#fff'
            });
            return;
        }

        const vulns = result.vulnerabilities || [];
        let htmlContent = "";

        if (vulns.length === 0) {
            htmlContent = "<p class='text-green-400'>✅ No se detectaron vulnerabilidades conocidas con los scripts actuales.</p>";
        } else {
            htmlContent = `<div style="text-align: left; max-height: 300px; overflow-y: auto;">`;
            vulns.forEach(v => {
                // Puede venir como objeto (hostscript) o dictionary con port
                if (v.id && v.output) {
                    // Host script result
                    htmlContent += `<div class="mb-2 p-2 bg-red-900/40 rounded border border-red-700">
                        <p class="font-bold text-red-300">⚠️ ${v.id}</p>
                        <pre class="text-xs text-gray-300 whitespace-pre-wrap">${v.output}</pre>
                     </div>`;
                } else if (v.script && v.output) {
                    // Port script result
                    htmlContent += `<div class="mb-2 p-2 bg-red-900/40 rounded border border-red-700">
                        <p class="font-bold text-red-300">⚠️ Puerto ${v.port} - ${v.script}</p>
                        <pre class="text-xs text-gray-300 whitespace-pre-wrap">${v.output}</pre>
                     </div>`;
                }
            });
            htmlContent += "</div>";
        }

        Swal.fire({
            title: `Reporte de Seguridad: ${ip}`,
            html: htmlContent,
            icon: vulns.length > 0 ? 'warning' : 'success',
            background: '#1e293b',
            color: '#fff',
            width: '600px'
        });

    } catch (e) {
        Swal.fire({
            title: 'Error de Conexión',
            text: "Fallo al comunicar con el servidor.",
            icon: 'error',
            background: '#1e293b',
            color: '#fff'
        });
    }
}

async function checkSecurityStatus() {
    try {
        const response = await fetch(`${API_URL}/security/status`);
        const data = await response.json();

        const shield = document.getElementById('security-shield');
        const icon = shield.querySelector('i');

        if (data.status === 'secure') {
            shield.className = "p-3 rounded-xl bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 transition-all duration-300";
            icon.className = "fas fa-shield-alt text-2xl";
            shield.title = "Red Segura";
        } else if (data.status === 'danger') {
            shield.className = "p-3 rounded-xl bg-red-600 text-white border border-red-500 shadow-[0_0_15px_rgba(239,68,68,0.7)] animate-pulse transition-all duration-300";
            icon.className = "fas fa-shield-virus text-2xl";
            shield.title = "¡PELIGRO! Ataque Detectado";

            // Mostrar alerta toast persistente si hay mensajes
            if (data.alerts && data.alerts.length > 0) {
                Toast.fire({
                    icon: 'warning',
                    title: 'ALERTA DE SEGURIDAD',
                    text: data.alerts[0],
                    background: '#7f1d1d',
                    timer: 5000
                });
            }
        } else if (data.status === 'warning') {
            shield.className = "p-3 rounded-xl bg-yellow-500/20 text-yellow-400 border border-yellow-500/30 transition-all duration-300";
            icon.className = "fas fa-exclamation-triangle text-2xl";
            shield.title = "Advertencia de Seguridad";
        }
    } catch (e) {
        console.error("Error checking security status:", e);
    }
}

// Poll every 5 seconds
setInterval(fetchDevices, 5000);
// Check security every 10 seconds
setInterval(checkSecurityStatus, 10000);

fetchDevices();
checkSecurityStatus();

async function blockDevice(mac) {
    if (!mac) return;

    const result = await Swal.fire({
        title: '¿Bloquear Dispositivo?',
        text: "Se enviarán paquetes de desautenticación para desconectarlo de la red. Esto puede ser agresivo.",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#ef4444',
        cancelButtonColor: '#3085d6',
        confirmButtonText: 'Sí, Bloquear',
        cancelButtonText: 'Cancelar',
        background: '#1e293b',
        color: '#fff'
    });

    if (result.isConfirmed) {
        try {
            const response = await fetch(`${API_URL}/devices/${mac}/block`, { method: 'POST' });
            if (response.ok) {
                Toast.fire({ icon: 'success', title: 'Dispositivo Bloqueado' });
                // Actualizar estado local si es necesario, o esperar al polling
                fetchDevices();
            }
        } catch (e) {
            Toast.fire({ icon: 'error', title: 'Error al bloquear' });
        }
    }
}

async function unblockDevice(mac) {
    if (!mac) return;

    try {
        const response = await fetch(`${API_URL}/devices/${mac}/unblock`, { method: 'POST' });
        if (response.ok) {
            Toast.fire({ icon: 'success', title: 'Dispositivo Desbloqueado' });
            fetchDevices();
        }
    } catch (e) {
        Toast.fire({ icon: 'error', title: 'Error al desbloquear' });
    }
}

// Necesitamos saber qué dispositivos están bloqueados para pintar la UI correctamente
// Modificaremos renderDevices para consultar esta lista o asumiremos que el backend nos lo dice.
// Por simplicidad, añadiremos un endpoint o modificaremos el GET /devices.
// Pero como no queremos cambiar todo el backend ahora, haremos un fetch adicional de bloqueados.

let blockedDevices = [];

async function fetchBlockedDevices() {
    try {
        const response = await fetch(`${API_URL}/blocked_devices`);
        const data = await response.json();
        blockedDevices = data.blocked || [];
        // Re-render si ya tenemos dispositivos
        if (allDevices.length > 0) renderDevices(allDevices);
    } catch (e) {
        console.error("Error fetching blocked devices", e);
    }
}

// Poll blocked list
setInterval(fetchBlockedDevices, 5000);
fetchBlockedDevices();

// --- JAIL / WARN LOGIC ---
let jailedDevices = [];

async function fetchJailedDevices() {
    try {
        const response = await fetch(`${API_URL}/jailed_devices`);
        const data = await response.json();
        jailedDevices = data.jailed || [];
        if (allDevices.length > 0) renderDevices(allDevices);
    } catch (e) {
        console.error("Error fetching jailed devices", e);
    }
}

async function warnDevice(ip) {
    if (!ip) return;

    const result = await Swal.fire({
        title: '¿ACTIVAR PROTOCOLO DE EXPULSIÓN?',
        text: "El dispositivo será aislado y redirigido a una PANTALLA ROJA DE ADVERTENCIA. ¿Estás seguro?",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#ff0000',
        cancelButtonColor: '#3085d6',
        confirmButtonText: 'SÍ, ADVERTIR',
        cancelButtonText: 'Cancelar',
        background: '#000',
        color: '#ff0000',
        iconColor: '#ff0000'
    });

    if (result.isConfirmed) {
        try {
            const response = await fetch(`${API_URL}/devices/${ip}/warn`, { method: 'POST' });
            if (response.ok) {
                Toast.fire({ icon: 'success', title: 'Protocolo Iniciado' });
                fetchJailedDevices();
            }
        } catch (e) {
            Toast.fire({ icon: 'error', title: 'Error al advertir' });
        }
    }
}

async function unwarnDevice(ip) {
    try {
        await fetch(`${API_URL}/devices/${ip}/unwarn`, { method: 'POST' });
        Toast.fire({ icon: 'success', title: 'Protocolo Desactivado' });
        fetchJailedDevices();
    } catch (e) {
        console.error(e);
    }
}


// --- BACKUP / RESTORE ---
async function backupConfig() {
    window.open(`${API_URL}/backup`, '_blank');
}

window.restoreConfig = async function (input) {
    const file = input.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = async function (e) {
        try {
            const json = JSON.parse(e.target.result);

            Swal.fire({
                title: 'Restaurando...',
                text: 'Procesando archivo de configuración',
                allowOutsideClick: false,
                didOpen: () => Swal.showLoading()
            });

            const response = await fetch(`${API_URL}/backup`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(json)
            });

            const result = await response.json();

            if (result.success) {
                await Swal.fire({
                    icon: 'success',
                    title: 'Restauración Exitosa',
                    text: `Se han importado/actualizado ${result.count} dispositivos.`,
                    background: '#1e293b',
                    color: '#fff'
                });
                fetchDevices(); // Refresh list
            } else {
                Swal.fire({
                    icon: 'error',
                    title: 'Error',
                    text: result.error,
                    background: '#1e293b',
                    color: '#fff'
                });
            }
        } catch (err) {
            Swal.fire({
                icon: 'error',
                title: 'Archivo Inválido',
                text: 'El archivo de respaldo está corrupto o no es JSON válido.',
                background: '#1e293b',
                color: '#fff'
            });
        }
    };
    reader.readAsText(file);
    input.value = ''; // Reset input to allow re-upload same file
}


// --- TIMELINE / LOGS ---
async function showLogs() {
    Swal.fire({
        title: 'Bitácora de Eventos',
        html: `
            <div id="logs-container" class="text-left max-h-[60vh] overflow-y-auto space-y-2 p-2">
                <div class="text-center text-gray-400"><i class="fas fa-spinner fa-spin"></i> Cargando...</div>
            </div>
        `,
        width: '800px',
        showConfirmButton: false,
        showCloseButton: true,
        background: '#0f172a',
        color: '#f8fafc',
        didOpen: () => {
            fetchLogs();
        }
    });
}

// Initial Load
// Assuming fetchTrafficStats() is defined elsewhere or will be added.
// fetchTrafficStats();
// fetchRecentActivity(); // This will be called by the interval if currentView is dashboard

// Loop
// Assuming currentView is defined globally or accessible.
// setInterval(() => {
//     fetchTrafficStats();
//     if(currentView === 'dashboard') fetchRecentActivity();
// }, 2000); // 2s polling

// Logs
async function fetchRecentActivity() {
    const container = document.getElementById('mini-logs');
    if (!container) return;

    try {
        const res = await fetch(`${API_URL}/events?limit=7`);
        if (!res.ok) return;
        const events = await res.json();

        if (events.length === 0) {
            container.innerHTML = `<div class="text-slate-500 text-sm italic text-center py-4">Sin actividad reciente</div>`;
            return;
        }

        container.innerHTML = events.map(ev => {
            let iconClass = "text-blue-400 fa-info-circle";
            let bgClass = "bg-blue-500/10";

            if (ev.event_type === 'WARNING') { iconClass = "text-amber-400 fa-exclamation-triangle"; bgClass = "bg-amber-500/10"; }
            if (ev.event_type === 'DANGER') { iconClass = "text-red-400 fa-skull"; bgClass = "bg-red-500/10"; }
            if (ev.event_type === 'SYSTEM') { iconClass = "text-purple-400 fa-server"; bgClass = "bg-purple-500/10"; }

            // Format date: Just time if today, else date+time
            const date = new Date(ev.timestamp + "Z"); // Ensure UTC if backend sends it
            const timeStr = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

            return `
                <div class="flex items-start gap-3 p-2 rounded-lg hover:bg-white/5 transition-colors">
                    <div class="w-8 h-8 rounded-full ${bgClass} flex items-center justify-center shrink-0 mt-0.5">
                        <i class="fas ${iconClass} text-xs"></i>
                    </div>
                    <div class="flex-1 min-w-0">
                        <p class="text-xs text-slate-300 leading-snug">${ev.message}</p>
                        <span class="text-[10px] text-slate-500 font-mono">${timeStr}</span>
                    </div>
                </div>
            `;
        }).join('');

    } catch (e) {
        // silent fail
    }
}


async function fetchLogs() {
    try {
        const response = await fetch(`${API_URL}/events?limit=50`);
        const events = await response.json();
        renderLogs(events);
    } catch (e) {
        document.getElementById('logs-container').innerHTML = '<div class="text-red-400">Error cargando logs.</div>';
    }
}

function renderLogs(events) {
    const container = document.getElementById('logs-container');
    if (!container) return;

    container.innerHTML = '';

    if (events.length === 0) {
        container.innerHTML = '<div class="text-gray-500 text-center py-4">No hay eventos registrados.</div>';
        return;
    }

    events.forEach(event => {
        let icon = 'fas fa-info-circle';
        let color = 'text-blue-400';
        let bg = 'bg-blue-900/20';

        if (event.event_type === 'WARNING') { icon = 'fas fa-exclamation-triangle'; color = 'text-yellow-400'; bg = 'bg-yellow-900/20'; }
        if (event.event_type === 'DANGER') { icon = 'fas fa-radiation'; color = 'text-red-500'; bg = 'bg-red-900/20'; }
        if (event.event_type === 'SYSTEM') { icon = 'fas fa-cog'; color = 'text-gray-400'; bg = 'bg-gray-800/50'; }

        // Formatear fecha UTC a local
        const date = new Date(event.timestamp + "Z"); // Asumimos timestamp viene sin Z pero es UTC
        const timeStr = date.toLocaleString();

        const item = document.createElement('div');
        item.className = `flex items-start gap-3 p-3 rounded-lg border border-gray-700/50 ${bg}`;
        item.innerHTML = `
            <div class="mt-1 ${color}"><i class="${icon}"></i></div>
            <div class="flex-1">
                <div class="flex justify-between items-start">
                     <span class="font-medium text-gray-200 text-sm">${event.message}</span>
                     <span class="text-xs text-gray-500 font-mono ml-2 whitespace-nowrap">${timeStr}</span>
                </div>
                ${event.device_mac ? `<div class="text-xs text-gray-500 font-mono mt-0.5"><i class="fas fa-fingerprint opacity-50"></i> ${event.device_mac}</div>` : ''}
            </div>
        `;
        container.appendChild(item);
    });
}

setInterval(fetchJailedDevices, 5000);
fetchJailedDevices();

// --- SETTINGS ---
async function openSettings() {
    // 1. Get current webhook
    let currentUrl = '';
    try {
        const res = await fetch(`${API_URL}/settings/webhook`);
        if (res.ok) {
            const data = await res.json();
            currentUrl = data.url || '';
        }
    } catch (e) { console.error(e); }

    // 2. Show Modal with Multiple Tabs/Sections
    const { value: formValues } = await Swal.fire({
        title: 'Configuración del Sistema',
        html: `
            <div class="text-left space-y-6">
                
                <!-- Webhook Section -->
                <div>
                    <h3 class="text-blue-400 font-bold mb-2"><i class="fas fa-bell mr-2"></i>Notificaciones (Webhook)</h3>
                    <p class="text-sm text-gray-400 mb-2">URL para recibir alertas (ej: Discord, Slack, n8n)</p>
                    <input id="swal-input1" class="swal2-input w-full bg-slate-800 text-white border-slate-600 focus:border-blue-500" placeholder="https://discord.com/api/webhooks/..." value="${currentUrl}">
                </div>

                <hr class="border-white/10">

                <!-- Backup Section -->
                <div>
                    <h3 class="text-emerald-400 font-bold mb-2"><i class="fas fa-save mr-2"></i>Copia de Seguridad</h3>
                    <p class="text-sm text-gray-400 mb-3">Guarda o restaura la base de datos de dispositivos y configuraciones.</p>
                    
                    <div class="flex gap-3">
                        <button onclick="backupConfig()" class="flex-1 py-2 px-4 rounded-lg bg-emerald-600/20 hover:bg-emerald-600 text-emerald-400 hover:text-white border border-emerald-500/30 transition-all font-medium">
                            <i class="fas fa-download mr-2"></i>Descargar Backup
                        </button>
                        
                        <label class="flex-1 py-2 px-4 rounded-lg bg-blue-600/20 hover:bg-blue-600 text-blue-400 hover:text-white border border-blue-500/30 transition-all font-medium text-center cursor-pointer">
                            <i class="fas fa-upload mr-2"></i>Restaurar
                            <input type="file" id="restoreFile" class="hidden" onchange="restoreConfig(this)">
                        </label>
                    </div>
                </div>

                <hr class="border-white/10">

                <!-- Danger Zone -->
                <div>
                    <h3 class="text-red-400 font-bold mb-2"><i class="fas fa-exclamation-triangle mr-2"></i>Zona de Peligro</h3>
                     <button onclick="confirmResetDB()" class="w-full py-2 px-4 rounded-lg bg-red-600/10 hover:bg-red-600 text-red-500 hover:text-white border border-red-500/20 transition-all font-medium">
                        <i class="fas fa-trash-alt mr-2"></i>Borrar Base de Datos
                    </button>
                </div>

            </div>
        `,
        focusConfirm: false,
        showCancelButton: true,
        confirmButtonText: 'Guardar Cambios',
        cancelButtonText: 'Cerrar',
        confirmButtonColor: '#3b82f6',
        cancelButtonColor: '#1e293b',
        background: '#0f172a',
        color: '#f8fafc',
        width: '600px',
        preConfirm: () => {
            return document.getElementById('swal-input1').value;
        }
    });

    if (formValues !== undefined) {
        // Save Webhook
        try {
            const res = await fetch(`${API_URL}/settings/webhook`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: formValues })
            });
            if (res.ok) {
                Toast.fire({ icon: 'success', title: 'Configuración guardada' });
            } else {
                Toast.fire({ icon: 'error', title: 'Error al guardar' });
            }
        } catch (e) {
            console.error(e);
            Toast.fire({ icon: 'error', title: 'Error de conexión' });
        }
    }
}

// Helper for DB Reset
function confirmResetDB() {
    Swal.fire({
        title: '¿Estás seguro?',
        text: "Se borrarán todos los dispositivos y el historial. No se puede deshacer.",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#ef4444',
        cancelButtonColor: '#3085d6',
        confirmButtonText: 'Sí, borrar todo',
        background: '#1e293b',
        color: '#fff'
    }).then((result) => {
        if (result.isConfirmed) {
            // Call API to reset DB (Endpoint needed or manual clear)
            // For now, imply manual action or implement endpoint later if requested. 
            // Since user didn't ask for this specific feature but it is good UX in settings.
            Toast.fire({ icon: 'info', title: 'Funcionalidad en desarrollo' });
        }
    })
}

// --- SPEEDTEST ---
let speedChart = null;

async function fetchSpeedHistory() {
    try {
        const res = await fetch(`${API_URL}/speedtest/history?limit=20`);
        const data = await res.json();
        renderSpeedChart(data);
    } catch (e) {
        console.error("Error fetching speedtest history", e);
    }
}

function renderSpeedChart(data) {
    const ctx = document.getElementById('speedChart');
    if (!ctx) return;

    // Si no hay datos, mostrar mensaje
    if (!data || data.length === 0) {
        const container = ctx.parentElement;
        if (container) {
            container.innerHTML = `
                <div class="flex flex-col items-center justify-center h-full text-slate-400">
                    <i class="fas fa-chart-line text-6xl mb-4 opacity-20"></i>
                    <p class="text-lg font-medium">No hay datos de velocidad</p>
                    <p class="text-sm mt-2">Ejecuta un test de velocidad para ver el historial</p>
                    <button onclick="runSpeedtest()" class="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors">
                        <i class="fas fa-tachometer-alt mr-2"></i>Ejecutar Test
                    </button>
                </div>
            `;
        }
        return;
    }

    // Sort chronological (oldest -> newest) for Chart
    data.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

    const labels = data.map(d => {
        const date = new Date(d.timestamp + "Z");
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    });
    const download = data.map(d => d.download);
    const upload = data.map(d => d.upload);
    const ping = data.map(d => d.ping);

    if (data.length > 0) {
        const last = data[data.length - 1];
        const lastDate = new Date(last.timestamp + "Z").toLocaleString();

        // Actualizar dashboard
        const info = document.getElementById('last-speedtest');
        if (info) info.innerText = `Último: ⬇️${last.download} Mb/s ⬆️${last.upload} Mb/s 📶${last.ping}ms (${lastDate})`;

        // Actualizar página de velocidad
        const infoLg = document.getElementById('last-speedtest-lg');
        if (infoLg) {
            infoLg.innerText = `⬇️${last.download} Mb/s ⬆️${last.upload} Mb/s 📶${last.ping}ms`;
            infoLg.className = 'text-lg text-yellow-400 font-mono font-bold';
        }
    } else {
        // Si no hay datos, actualizar el texto
        const infoLg = document.getElementById('last-speedtest-lg');
        if (infoLg) {
            infoLg.innerText = 'No hay datos';
            infoLg.className = 'text-lg text-slate-400 font-mono';
        }
    }

    if (speedChart) speedChart.destroy();

    speedChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Descarga (Mbps)',
                    data: download,
                    borderColor: '#3b82f6', // blue-500
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    yAxisID: 'y',
                    tension: 0.4,
                    fill: true
                },
                {
                    label: 'Subida (Mbps)',
                    data: upload,
                    borderColor: '#10b981', // emerald-500
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    yAxisID: 'y',
                    tension: 0.4,
                    fill: true
                },
                {
                    label: 'Ping (ms)',
                    data: ping,
                    borderColor: '#f59e0b', // amber-500
                    borderDash: [5, 5],
                    yAxisID: 'y1',
                    tension: 0.1,
                    pointStyle: 'circle'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: { labels: { color: '#cbd5e1' } }
            },
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    grid: { color: 'rgba(255, 255, 255, 0.1)' },
                    ticks: { color: '#94a3b8' },
                    title: { display: true, text: 'Velocidad (Mbps)', color: '#94a3b8' }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    grid: { drawOnChartArea: false },
                    ticks: { color: '#f59e0b' },
                    title: { display: true, text: 'Ping (ms)', color: '#f59e0b' }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#94a3b8' }
                }
            }
        }
    });
}

async function runSpeedtest() {
    const btn = document.getElementById('btn-speedtest-lg');
    const originalText = btn.innerHTML;

    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Midiendo...';

    const toast = Swal.mixin({
        toast: true,
        position: 'top-end',
        showConfirmButton: false,
        timer: 3000,
        background: '#1e293b',
        color: '#fff'
    });

    toast.fire({
        icon: 'info',
        title: 'Speedtest Iniciado',
        text: 'Esto puede tardar unos 30-40 segundos...'
    });

    try {
        const res = await fetch(`${API_URL}/speedtest/run`, { method: 'POST' });
        const result = await res.json();

        if (result.success) {
            Swal.fire({
                icon: 'success',
                title: 'Test Finalizado 🚀',
                html: `
                    <div class="text-left ml-10">
                    <p><strong>Descarga:</strong> ${result.data.download} Mbps</p>
                    <p><strong>Subida:</strong> ${result.data.upload} Mbps</p>
                    <p><strong>Ping:</strong> ${result.data.ping} ms</p>
                    </div>
                `,
                background: '#1e293b',
                color: '#fff'
            });
            fetchSpeedHistory();
        } else {
            Swal.fire({ icon: 'error', title: 'Error', text: result.error, background: '#1e293b', color: '#fff' });
        }
    } catch (e) {
        Swal.fire({ icon: 'error', title: 'Error de conexión', background: '#1e293b', color: '#fff' });
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

// Initial fetch
fetchSpeedHistory();

// --- TOPOLOGY ---
let network = null;

async function fetchTopology() {
    try {
        const res = await fetch(`${API_URL}/topology`);
        const data = await res.json();
        renderTopology(data);
    } catch (e) {
        console.error("Error fetching topology", e);
    }
}

function renderTopology(data) {
    const container = document.getElementById('mynetwork');
    if (!container) return;

    // Convert generic data to vis format
    const nodes = new vis.DataSet(data.nodes);
    const edges = new vis.DataSet(data.edges);

    const options = {
        nodes: {
            shape: 'dot',
            size: 20,
            font: { size: 14, color: '#e2e8f0', face: 'ui-sans-serif' },
            borderWidth: 2,
            shadow: true
        },
        edges: {
            width: 2,
            color: { color: '#475569', highlight: '#3b82f6', opacity: 0.5 },
            smooth: { type: 'continuous' },
            length: 150
        },
        groups: {
            gateway: {
                color: { background: '#f59e0b', border: '#b45309' },
                shape: 'diamond',
                size: 35,
                font: { size: 16, color: '#f59e0b', face: 'bold' }
            },
            server: {
                color: { background: '#6366f1', border: '#4338ca' },
                shape: 'square',
                size: 25
            },
            trusted: { color: { background: '#10b981', border: '#047857' } },
            intruder: { color: { background: '#ef4444', border: '#b91c1c' }, shape: 'triangle' },
            blocked: {
                color: { background: '#1e293b', border: '#ef4444' },
                shape: 'icon',
                icon: { face: "'Font Awesome 6 Free'", code: '\uf023', size: 30, color: '#ef4444' }
            },
            device: { color: { background: '#3b82f6', border: '#1d4ed8' } }
        },
        physics: {
            stabilization: false,
            barnesHut: {
                gravitationalConstant: -4000,
                springConstant: 0.02,
                springLength: 150
            }
        },
        interaction: { hover: true, tooltipDelay: 200, zoomView: true }
    };

    if (network) network.destroy();
    network = new vis.Network(container, { nodes, edges }, options);
}

// Initial fetch
fetchTopology();


