import sys
import threading
import time
import requests
import webview
import os
import socket
from PIL import Image
import pystray
from webview.menu import Menu, MenuAction

# Configuración
BACKEND_URL = "http://localhost:8000"
WINDOW_TITLE = "NetGuard Profesional"
ICON_PATH = "/opt/netguard/icon.png"
TARGET_URL = 'http://localhost:8000'
ICON_PATH = os.path.abspath("icon.png")
main_window = None

def on_show(icon, item):
    if main_window:
        main_window.show()
        main_window.restore()

def on_exit(icon, item):
    icon.stop()
    os._exit(0)

def run_tray():
    try:
        image = Image.open(ICON_PATH)
        menu = pystray.Menu(
            pystray.MenuItem("Abrir NetGuard", on_show, default=True),
            pystray.MenuItem("Salir", on_exit)
        )
        
        icon = pystray.Icon("NetGuard", image, "NetGuard Pro", menu=menu)
        icon.run()
    except Exception as e:
        print(f"Error tray: {e}")

def on_minimized():
    """Al minimizar, ocultar la ventana (irse al tray)"""
    if main_window:
        time.sleep(0.2) # Pequeña pausa para asegurar animación
        main_window.hide()

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
        except:
            pass
        time.sleep(1)
        
    print("❌ Backend no respondió a tiempo.")
    window.load_url('data:text/html,<h1 style="color:red;text-align:center;margin-top:20%">Error: El servicio NetGuard no responde.</h1><p style="text-align:center">Verifica: sudo systemctl status netguard</p>')

def ensure_single_instance():
    """Asegura que solo haya una ventana abierta usando un socket lock"""
    global _socket_lock
    _socket_lock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # Puerto arbitrario para bloqueo (no visible desde red externa)
        _socket_lock.bind(('127.0.0.1', 44555))
    except socket.error:
        print("⚠️ NetGuard Pro ya está en ejecución en otra ventana.")
        sys.exit(0)

if __name__ == '__main__':
    ensure_single_instance()
    
    # Iniciar Tray en hilo paralelo
    threading.Thread(target=run_tray, daemon=True).start()
    
    # Crear ventana (asignar a global)
    main_window = webview.create_window(
        'NetGuard Pro', 
        html='<h1 style="color:#3b82f6;text-align:center;margin-top:20%;font-family:sans-serif">🛡️ Iniciando NetGuard...</h1><p style="text-align:center;font-family:sans-serif;color:#64748b">Conectando con el motor de seguridad...</p>', 
        width=1200, 
        height=800, 
        background_color='#0f172a',
        text_select=False,
        resizable=True
    )
    
    # Conectar evento de minimizar
    main_window.events.minimized += on_minimized
    
    # Iniciar
    webview.start(wait_for_backend, main_window, debug=True)
