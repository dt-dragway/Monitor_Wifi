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
let currentPage = 1;
const ITEMS_PER_PAGE = 5;
let allDevices = [];

function setTab(tab) {
    currentTab = tab;
    currentPage = 1;
    updateTabsUI();
    renderDevices(allDevices);
}

function updateTabsUI() {
    ['all', 'intruder', 'trusted', 'blocked', 'offline'].forEach(t => {
        const btn = document.getElementById(`tab-${t}`);
        if (!btn) return;
        if (t === currentTab) {
            btn.className = "px-4 py-2 rounded-lg text-sm font-bold transition-all text-white bg-blue-600 shadow-lg transform scale-105";
        } else {
            btn.className = "px-4 py-2 rounded-lg text-sm font-medium transition-all text-gray-400 hover:text-white hover:bg-white/5";
        }
    });
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
    const countBlocked = devices.filter(d => jailedDevices.includes(d.ip) || blockedDevices.includes(d.mac)).length;

    document.getElementById('badge-all').innerText = devices.length;
    // Intruders exclude blocked ones now, to keep the list clean
    document.getElementById('badge-intruder').innerText = devices.filter(d => !d.is_trusted && d.status === 'online' && !jailedDevices.includes(d.ip) && !blockedDevices.includes(d.mac)).length;
    document.getElementById('badge-trusted').innerText = devices.filter(d => d.is_trusted && d.status === 'online').length;
    document.getElementById('badge-offline').innerText = devices.filter(d => d.status === 'offline').length;

    // Tab counters (UI update if elements exist)
    if (document.getElementById('count-all')) document.getElementById('count-all').innerText = devices.length;
    if (document.getElementById('count-intruders')) document.getElementById('count-intruders').innerText = document.getElementById('badge-intruder').innerText;
    if (document.getElementById('count-trusted')) document.getElementById('count-trusted').innerText = document.getElementById('badge-trusted').innerText;
    if (document.getElementById('count-blocked')) document.getElementById('count-blocked').innerText = countBlocked;
    if (document.getElementById('count-offline')) document.getElementById('count-offline').innerText = document.getElementById('badge-offline').innerText;

    // 2. Sort (Blocked > Intruder > Online > Offline)
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
    document.getElementById('pagination-info').innerText = `Mostrando ${filtered.length > 0 ? start + 1 : 0}-${Math.min(end, filtered.length)} de ${filtered.length}`;
    document.getElementById('btn-prev').disabled = currentPage === 1;
    document.getElementById('btn-next').disabled = currentPage === totalPages;

    // Render Grid
    const list = document.getElementById('device-list');
    list.innerHTML = '';

    if (paginated.length === 0) {
        list.innerHTML = `
            <div class="p-12 text-center text-gray-400">
                <i class="fas fa-filter text-4xl mb-4 opacity-50"></i>
                <p>No hay dispositivos en esta categoría.</p>
            </div>`;
        return;
    }

    paginated.forEach(device => {
        const isOnline = device.status === 'online';
        const isTrusted = device.is_trusted;
        const isJailed = jailedDevices.includes(device.ip);
        const isLegacyBlocked = blockedDevices.includes(device.mac);
        const isBlocked = isJailed || isLegacyBlocked;

        const icon = getDeviceIcon(device.vendor || "", device.alias || "");

        let statusClass = "";
        if (isBlocked) {
            statusClass = 'bg-gray-900/50 border-red-900/50 opacity-75 grayscale sepia';
        } else if (isOnline) {
            statusClass = isTrusted ? 'bg-emerald-500/10 border-emerald-500/30' : 'bg-red-500/10 border-red-500/30';
        } else {
            statusClass = 'bg-white/5 border-white/10 opacity-60 grayscale';
        }

        const item = document.createElement('div');
        item.className = `p-4 rounded-xl border backdrop-blur-sm transition-all hover:scale-[1.01] ${statusClass} flex flex-col md:flex-row justify-between items-center mb-3 relative overflow-hidden`;

        // Blocked Overlay
        const lockedOverlay = isBlocked ? `<div class="absolute inset-0 flex items-center justify-center pointer-events-none bg-black/10"><i class="fas fa-lock text-6xl text-red-500/20 rotate-12"></i></div>` : '';

        item.innerHTML = `
            ${lockedOverlay}
            <div class="flex items-center w-full md:w-auto mb-3 md:mb-0 relative z-10">
                <div class="w-12 h-12 rounded-full flex items-center justify-center bg-black/20 text-2xl mr-4 shadow-inner relative">
                    ${icon}
                    ${isOnline && !isBlocked ? '<div class="absolute bottom-0 right-0 w-3 h-3 bg-green-500 rounded-full border-2 border-slate-900"></div>' : ''}
                    ${isBlocked ? '<div class="absolute bottom-0 right-0 w-3 h-3 bg-red-500 rounded-full border-2 border-slate-900"></div>' : ''}
                </div>
                <div>
                    <div class="flex items-center gap-2">
                        <h3 class="font-bold text-lg text-white">${device.alias || device.vendor || 'Dispositivo Desconocido'}</h3>
                        ${isBlocked ?
                '<span class="px-2 py-0.5 rounded-full text-xs bg-red-900/50 text-red-400 border border-red-700/50 font-bold">⛔ BLOQUEADO</span>'
                : ''}
                        ${!isTrusted && isOnline && !isBlocked ?
                '<span class="px-2 py-0.5 rounded-full text-xs bg-red-500/20 text-red-300 border border-red-500/30 font-bold shadow-lg shadow-red-500/20">⚠ INTRUSO</span>'
                : ''}
                        ${!isOnline ?
                '<span class="px-2 py-0.5 rounded-full text-xs bg-gray-700 text-gray-400 font-mono">OFFLINE</span>'
                : ''}
                    </div>
                    </div>
                    <div class="text-xs text-gray-400 mt-1 font-mono flex flex-wrap gap-4 items-center">
                        <span title="IP Address"><i class="fas fa-ethernet"></i> ${device.ip}</span>
                        <span title="MAC Address"><i class="fas fa-fingerprint"></i> ${device.mac}</span>
                        ${device.interface ? `
                            <span class="px-1.5 py-0.5 rounded bg-gray-700/50 border border-gray-600/50 text-gray-300" title="Interfaz de Conexión">
                                ${device.interface.startsWith('wlan') || device.interface.startsWith('wifi') ? '<i class="fas fa-wifi text-blue-400"></i>' :
                    device.interface.startsWith('eth') || device.interface.startsWith('en') ? '<i class="fas fa-network-wired text-green-400"></i>' :
                        '<i class="fas fa-server text-purple-400"></i>'} 
                                ${device.interface}
                            </span>
                        ` : ''}
                    </div>
                </div>
            </div>
            
            <div class="flex gap-2 relative z-10">
                 ${!isTrusted ? `
                    <button onclick="setTrust('${device.mac}', true)" class="px-4 py-2 rounded-lg bg-emerald-600/20 hover:bg-emerald-600 text-emerald-400 hover:text-white transition-all border border-emerald-500/30 font-medium text-sm flex items-center gap-2" title="Hacer de Confianza">
                        <i class="fas fa-shield-alt"></i>
                    </button>
                ` : `
                    <button onclick="setTrust('${device.mac}', false)" class="p-2 rounded-lg bg-orange-600/20 hover:bg-orange-600 text-orange-400 hover:text-white transition-all border border-orange-500/30" title="Quitar de Confianza">
                        <i class="fas fa-ban"></i>
                    </button>
                `}

                <!-- UNIFIED ACTION BUTTON -->
                ${isBlocked ? `
                    <button onclick="unwarnDevice('${device.ip}'); unblockDevice('${device.mac}')" class="p-2 rounded-lg bg-gray-600/20 hover:bg-gray-500 text-gray-400 hover:text-white transition-all border border-gray-500/30" title="Desbloquear y Liberar">
                        <i class="fas fa-unlock"></i>
                    </button>
                ` : `
                    <button onclick="warnDevice('${device.ip}')" class="p-2 rounded-lg bg-red-600 hover:bg-red-700 text-white transition-all border border-red-500/50 shadow-lg shadow-red-500/30" title="BLOQUEAR Y ALERTAR (Wall of Shame)">
                        <i class="fas fa-lock"></i>
                    </button>
                `}
                
                <button onclick="editAlias('${device.mac}', '${device.alias || ''}')" class="p-2 rounded-lg bg-blue-600/20 hover:bg-blue-600 text-blue-400 hover:text-white transition-all border border-blue-500/30" title="Editar Nombre">
                    <i class="fas fa-pen"></i>
                </button>
                
                <button onclick="triggerDeepScan('${device.ip}')" class="p-2 rounded-lg bg-purple-600/20 hover:bg-purple-600 text-purple-400 hover:text-white transition-all border border-purple-500/30" title="Escaneo Profundo (Nmap)">
                    <i class="fas fa-microscope"></i>
                </button>

                <button onclick="triggerAudit('${device.ip}')" class="p-2 rounded-lg bg-pink-600/20 hover:bg-pink-600 text-pink-400 hover:text-white transition-all border border-pink-500/30" title="Auditoría de Seguridad (Vulns)">
                    <i class="fas fa-bug"></i>
                </button>
            </div>
        `;
        list.appendChild(item);
    });
}

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

setInterval(fetchJailedDevices, 5000);
fetchJailedDevices();

