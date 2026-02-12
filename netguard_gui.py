import sys
import threading
import time
import requests
import webview
import os
import socket
import subprocess
from PIL import Image
import pystray
from webview.menu import Menu, MenuAction

# Configuración
BACKEND_URL = "http://localhost:8000"
WINDOW_TITLE = "NetGuard Profesional"
ICON_PATH = "/opt/netguard/icon.png"
TARGET_URL = 'http://localhost:8000'
ICON_PATH = os.path.abspath("icon.png")
# Variables Globales
main_window = None
tray_icon = None
force_close = False

def check_notifications():
    global last_event_id, last_security_status
    time.sleep(5)
    
    # Inicializar último evento
    try:
        r = requests.get(TARGET_URL + '/api/events', params={'limit': 1})
        if r.status_code == 200 and r.json():
            last_event_id = r.json()[0]['id']
    except: pass

    while True:
        try:
            # 1. Verificar Eventos Nuevos
            r = requests.get(TARGET_URL + '/api/events', params={'limit': 5}, timeout=2)
            if r.status_code == 200:
                events = r.json()
                new_events = [e for e in events if e['id'] > last_event_id]
                new_events.sort(key=lambda x: x['id'])
                
                for ev in new_events:
                    last_event_id = max(last_event_id, ev['id'])
                    # Notificar
                    level = ev['event_type']
                    urgency = "critical" if level in ["WARNING", "DANGER"] else "normal"
                    subprocess.run(["notify-send", "-a", "NetGuard", "-u", urgency, f"NetGuard: {level}", ev['message']])
            
            # 2. Seguridad
            r = requests.get(TARGET_URL + '/api/security/status', timeout=2)
            if r.status_code == 200:
                status = r.json().get('status', 'secure')
                if status == 'danger' and last_security_status != 'danger':
                    subprocess.run(["notify-send", "-u", "critical", "-a", "NetGuard", "🚨 ALERTA DE SEGURIDAD", "¡Ataque MITM Detectado!"])
                last_security_status = status
                
        except: pass
        time.sleep(5)

def on_show(icon, item):
    if main_window:
        main_window.show()
        main_window.restore()

def on_exit(icon, item):
    """Cierra la aplicación completamente"""
    global force_close
    force_close = True
    icon.stop()
    if main_window:
        main_window.destroy()
    os._exit(0)

def run_tray():
    global tray_icon
    try:
        image = Image.open(ICON_PATH)
        menu = pystray.Menu(
            pystray.MenuItem("Mostrar NetGuard", on_show, default=True),
            pystray.MenuItem("Salir Totalmente", on_exit)
        )
        
        tray_icon = pystray.Icon("NetGuard", image, "NetGuard Pro", menu=menu)
        tray_icon.run()
    except Exception as e:
        print(f"Error tray: {e}")

def on_minimized():
    """Al minimizar, ocultar la ventana (irse al tray)"""
    if main_window:
        time.sleep(0.2)
        main_window.hide()

def on_closing():
    """Al cerrar, detener todo y salir"""
    global force_close
    force_close = True
    if tray_icon:
        tray_icon.stop()
    return True

def wait_for_backend(window):
    # Intentar contactar backend
    max_tries = 30
    for i in range(max_tries):
        try:
            r = requests.get(TARGET_URL + '/api/devices', timeout=1)
            if r.status_code == 200:
                print("✅ Backend listo. Cargando UI...")
                window.load_url(TARGET_URL)
                return
        except: pass
        time.sleep(1)
    window.load_url('data:text/html,<h1 style="color:red;text-align:center;margin-top:20%">Error conectando al servicio.</h1>')

def ensure_single_instance():
    global _socket_lock
    _socket_lock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        _socket_lock.bind(('127.0.0.1', 44555))
    except socket.error:
        print("⚠️ NetGuard ya está abierto.")
        sys.exit(0)

if __name__ == '__main__':
    ensure_single_instance()
    
    # Iniciar Hilos
    threading.Thread(target=run_tray, daemon=True).start()
    threading.Thread(target=check_notifications, daemon=True).start()
    
    # Crear ventana
    main_window = webview.create_window(
        'NetGuard Pro', 
        html='<h1 style="color:#3b82f6;text-align:center;margin-top:20%;font-family:sans-serif">🛡️ Cargando NetGuard...</h1>', 
        width=1200, 
        height=800, 
        background_color='#0f172a',
        text_select=False,
        resizable=True
    )
    
    # Comportamiento:
    # 1. Minimizar -> Ocultar a Tray
    main_window.events.minimized += on_minimized
    
    # 2. Cerrar -> Salir Totalmente
    main_window.events.closing += on_closing
    
    # Iniciar (DEBUG OFF)
    webview.start(wait_for_backend, main_window, debug=False)
