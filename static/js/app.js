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

function renderDevices(devices) {
    const list = document.getElementById('device-list');
    list.innerHTML = '';

    if (devices.length === 0) {
        list.innerHTML = `
            <div class="p-12 text-center text-gray-400">
                <i class="fas fa-search text-4xl mb-4 opacity-50"></i>
                <p>No se encontraron dispositivos.</p>
            </div>`;
        return;
    }

    // Sort: Intruder > Online > Offline
    devices.sort((a, b) => {
        const scoreA = (a.status === 'online' ? 10 : 0) + (!a.is_trusted ? 5 : 0);
        const scoreB = (b.status === 'online' ? 10 : 0) + (!b.is_trusted ? 5 : 0);
        return scoreB - scoreA;
    });

    devices.forEach(device => {
        const isOnline = device.status === 'online';
        const isTrusted = device.is_trusted;
        const icon = getDeviceIcon(device.vendor || "", device.alias || "");

        let statusClass = isOnline
            ? (isTrusted ? 'bg-emerald-500/10 border-emerald-500/30' : 'bg-red-500/10 border-red-500/30')
            : 'bg-white/5 border-white/10 opacity-60';

        const item = document.createElement('div');
        item.className = `p-4 rounded-xl border backdrop-blur-sm transition-all hover:scale-[1.01] ${statusClass} flex flex-col md:flex-row justify-between items-center mb-3`;

        item.innerHTML = `
            <div class="flex items-center w-full md:w-auto mb-3 md:mb-0">
                <div class="w-12 h-12 rounded-full flex items-center justify-center bg-black/20 text-2xl mr-4 shadow-inner">
                    ${icon}
                </div>
                <div>
                    <div class="flex items-center gap-2">
                        <h3 class="font-bold text-lg text-white">${device.alias || device.vendor || 'Dispositivo Desconocido'}</h3>
                        ${!isTrusted && isOnline ?
                '<span class="px-2 py-0.5 rounded-full text-xs bg-red-500/20 text-red-300 border border-red-500/30 font-bold shadow-lg shadow-red-500/20">⚠ INTRUSO</span>'
                : ''}
                        ${isTrusted ?
                '<span class="px-2 py-0.5 rounded-full text-xs bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-medium"><i class="fas fa-check-circle"></i> Seguro</span>'
                : ''}
                    </div>
                    <div class="text-xs text-gray-400 mt-1 font-mono flex gap-4">
                        <span><i class="fas fa-ethernet"></i> ${device.ip}</span>
                        <span><i class="fas fa-fingerprint"></i> ${device.mac}</span>
                    </div>
                    ${device.vendor ? `<p class="text-xs text-gray-500 mt-0.5">${device.vendor}</p>` : ''}
                </div>
            </div>
            
            <div class="flex gap-2">
                <button onclick="editAlias('${device.mac}', '${device.alias || ''}')" class="p-2 rounded-lg bg-blue-600/20 hover:bg-blue-600 text-blue-400 hover:text-white transition-all border border-blue-500/30" title="Editar Nombre">
                    <i class="fas fa-pen"></i>
                </button>
                ${!isTrusted ? `
                    <button onclick="setTrust('${device.mac}', true)" class="px-4 py-2 rounded-lg bg-emerald-600/20 hover:bg-emerald-600 text-emerald-400 hover:text-white transition-all border border-emerald-500/30 font-medium text-sm flex items-center gap-2" title="Hacer de Confianza">
                        <i class="fas fa-shield-alt"></i> Confiar
                    </button>
                ` : `
                    <button onclick="setTrust('${device.mac}', false)" class="p-2 rounded-lg bg-orange-600/20 hover:bg-orange-600 text-orange-400 hover:text-white transition-all border border-orange-500/30" title="Quitar Confianza">
                        <i class="fas fa-ban"></i>
                    </button>
                `}
                <button onclick="blockDevice('${device.mac}')" class="p-2 rounded-lg bg-red-600/20 hover:bg-red-600 text-red-400 hover:text-white transition-all border border-red-500/30" title="Bloquear">
                    <i class="fas fa-lock"></i>
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
            input: 'text-gray-800'
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

// Poll every 5 seconds
setInterval(fetchDevices, 5000);
fetchDevices();
