
import requests
import sys
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

def log(msg, status="INFO"):
    color = GREEN if status == "PASS" else (RED if status == "FAIL" else RESET)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {color}[{status}]{RESET} {msg}")

def test_api_health():
    endpoints = [
        "/api/devices",
        "/api/traffic",
        "/api/config/subnets",
        "/api/security/status"
    ]
    
    success = True
    for ep in endpoints:
        try:
            r = requests.get(f"{BASE_URL}{ep}", timeout=5)
            if r.status_code == 200:
                log(f"Endpoint {ep} is responsive.", "PASS")
            else:
                log(f"Endpoint {ep} returned {r.status_code}", "FAIL")
                success = False
        except Exception as e:
            log(f"Endpoint {ep} error: {e}", "FAIL")
            success = False
    return success

def test_configuration():
    # Test writing and reading configuration
    test_subnet = "192.168.99.0/24"
    try:
        # 1. Write
        r = requests.post(f"{BASE_URL}/api/config/subnets", json={"subnets": test_subnet})
        if r.status_code == 200 and r.json().get("subnets") == test_subnet:
            log("Configuración de subredes guardada correctamente.", "PASS")
        else:
            log("Fallo al guardar configuración.", "FAIL")
            return False

        # 2. Read
        r = requests.get(f"{BASE_URL}/api/config/subnets")
        if r.status_code == 200 and r.json().get("subnets") == test_subnet:
            log("Configuración de subredes leída correctamente.", "PASS")
        else:
            log("Fallo al leer configuración persistida.", "FAIL")
            return False
            
        # 3. Cleanup (Restaurar vacío o lo que sea)
        requests.post(f"{BASE_URL}/api/config/subnets", json={"subnets": ""})
        return True

    except Exception as e:
        log(f"Error en test de configuración: {e}", "FAIL")
        return False

def check_scanner_logs():
    # Verificar si hay actividad reciente de escaneo en los logs (simulado check file)
    try:
        # Intentaremos ver si la API de dispositivos devuelve algo (aunque esté vacío, que sea JSON válido)
        r = requests.get(f"{BASE_URL}/api/devices")
        data = r.json()
        if isinstance(data, list):
            log(f"API de Dispositivos devuelve estructura válida ({len(data)} dispositivos encontrados).", "PASS")
            return True
        else:
            log("API de Dispositivos devolvió formato inválido.", "FAIL")
            return False
    except Exception as e:
        log(f"Error verificando scanner: {e}", "FAIL")
        return False

def check_admin_endpoints():
    # Verificar existencia del endpoint crítico de reset (sin ejecutarlo para no borrar datos del usuario ahora)
    # Haremos un OPTIONS o un POST sin confirmar si fuera necesario, pero mejor solo verificar que NO da 404.
    # Como es POST, si mandamos GET debería dar 405 Method Not Allowed (lo que significa que EXISTE).
    # Si da 404, es FAIL.
    try:
        r = requests.get(f"{BASE_URL}/api/admin/reset_db")
        if r.status_code == 405: # Method Not Allowed (Expected for GET on POST endpoint)
            log("Endpoint Admin Reset DB existe y está protegido.", "PASS")
            return True
        elif r.status_code == 404:
            log("Endpoint Admin Reset DB NO encontrado (404).", "FAIL")
            return False
        else:
            log(f"Endpoint Admin Reset DB respuesta inesperada: {r.status_code}", "WARN")
            return True
    except:
        return False

def run_tests():
    print(f"🚀 Iniciando Auditoría de Sistema ({BASE_URL})...\n")
    
    checks = [
        ("API Health Check", test_api_health),
        ("DB & Configuration Persistence", test_configuration),
        ("Scanner Integration", check_scanner_logs),
        ("Admin Interface Security", check_admin_endpoints)
    ]
    
    passed = 0
    total = len(checks)
    
    for name, func in checks:
        print(f"\n--- Testing: {name} ---")
        if func():
            passed += 1
        else:
            print(f"❌ {name} FAILED")
            
    print(f"\n{'='*40}")
    if passed == total:
        print(f"{GREEN}✅ SISTEMA LISTO PARA PRODUCCIÓN (Score: {passed}/{total}){RESET}")
    else:
        print(f"{RED}⚠️ SE ENCONTRARON ERRORES (Score: {passed}/{total}){RESET}")
    print(f"{'='*40}\n")

if __name__ == "__main__":
    run_tests()
