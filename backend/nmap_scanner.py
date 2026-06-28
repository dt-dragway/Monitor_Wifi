import nmap
import asyncio
from backend.database import engine
from backend.models import Vulnerability, Device
from sqlmodel import Session, select
from datetime import datetime

nm = nmap.PortScanner()

def scan_device_details(ip):
    """
    Realiza un escaneo intenso a una IP específica para detectar SO y puertos.
    Retorna un diccionario con los detalles.
    """
    print(f"Iniciando escaneo detallado para {ip}...")
    try:
        # Escaneo silencioso, detección de OS (-O), versión (-sV)
        # Requiere root para -O. Agregamos --top-ports para rapidez
        nm.scan(ip, arguments='-O -sV --version-intensity 5 --top-ports 100')
        
        if ip not in nm.all_hosts():
            return {"error": "Host no accesible o bloqueado"}

        host_data = nm[ip]
        
        # Extraer OS
        os_match = "Desconocido"
        if 'osmatch' in host_data and host_data['osmatch']:
            os_match = host_data['osmatch'][0]['name']
            
        # Extraer Puertos
        open_ports = []
        if 'tcp' in host_data:
            for port in host_data['tcp']:
                state = host_data['tcp'][port]['state']
                name = host_data['tcp'][port]['name']
                product = host_data['tcp'][port].get('product', '')
                version = host_data['tcp'][port].get('version', '')
                if state == 'open':
                    open_ports.append(f"{port}/tcp ({name}) {product} {version}".strip())

        return {
            "os": os_match,
            "ports": open_ports,
            "hostname": host_data.hostname() if host_data.hostname() else None
        }

    except Exception as e:
        print(f"Error en Nmap: {e}")
        return {"error": str(e)}

def scan_vulnerabilities(ip):
    """
    Ejecuta scripts de vulnerabilidades de Nmap contra la IP y las guarda en la DB.
    """
    print(f"Iniciando auditoría PRO de vulnerabilidades para {ip}...")
    try:
        # --script vuln: Ejecuta scripts de detección de vulnerabilidades conocidas
        # Agregamos scripts específicos de auditoría comunes
        # vuln, discovery, auth
        nm.scan(ip, arguments='-sV --script vuln,auth --script-timeout 30s')
        
        if ip not in nm.all_hosts():
            return {"error": "Host no accesible"}

        host_data = nm[ip]
        found_vulns = []
        
        # Buscar el dispositivo en la DB para obtener el MAC
        with Session(engine) as session:
            device = session.exec(select(Device).where(Device.ip == ip)).first()
            mac = device.mac if device else "UNKNOWN"

            # Limpiar vulnerabilidades viejas de este dispositivo si queremos mantenerlo fresco
            # (Opcional: podrías preferir un histórico)

            # Analizar scripts a nivel de host
            if 'hostscript' in host_data:
                for script in host_data['hostscript']:
                    v = Vulnerability(
                        device_mac=mac,
                        severity="MEDIUM", # Default
                        title=script['id'],
                        description=script['output'],
                        timestamp=datetime.utcnow()
                    )
                    # Intentar inferir severidad por palabras clave
                    output_lower = script['output'].lower()
                    if "critical" in output_lower or "vuln" in output_lower: v.severity = "CRITICAL"
                    elif "high" in output_lower: v.severity = "HIGH"
                    
                    found_vulns.append(v)
                    session.add(v)
            
            # Analizar scripts a nivel de puerto
            if 'tcp' in host_data:
                for port, data in host_data['tcp'].items():
                    if 'script' in data:
                        for script_id, output in data['script'].items():
                            v = Vulnerability(
                                device_mac=mac,
                                severity="LOW",
                                title=f"Port {port}: {script_id}",
                                description=output,
                                port=port,
                                timestamp=datetime.utcnow()
                            )
                            output_lower = output.lower()
                            if "vulnerable" in output_lower or "critical" in output_lower: v.severity = "CRITICAL"
                            elif "high" in output_lower: v.severity = "HIGH"
                            elif "medium" in output_lower: v.severity = "MEDIUM"
                            
                            found_vulns.append(v)
                            session.add(v)
            
            session.commit()
        
        return {"success": True, "count": len(found_vulns), "vulnerabilities": [v.dict() for v in found_vulns]}

    except Exception as e:
        print(f"Error en auditoría: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}
def scan_subnet_fast(cidr):
    """
    Realiza un escaneo masivo y rápido sobre una subred completa para detectar
    servicios críticos (HTTP, SSH, RDP, SMB, DBs, Cámaras).
    """
    print(f"🚀 Lanzando Escaneo Masivo Global en {cidr}...")
    try:
        # Puertos de interés:
        # 21,22,23,25,53,80,443,445,1433,3306,3389,554,8080,8443
        ports = "21,22,23,53,80,443,445,1433,3306,3389,554,8000,8080,8443"
        
        # -F (rápido), --open (solo abiertos), -n (sin resolución DNS para velocidad)
        nm.scan(cidr, arguments=f'-p {ports} --open -n -T4')
        
        results = []
        for ip in nm.all_hosts():
            host_info = {
                "ip": ip,
                "mac": "UNKNOWN",
                "services": []
            }
            
            # Obtener MAC desde la DB si existe
            with Session(engine) as session:
                dev = session.exec(select(Device).where(Device.ip == ip)).first()
                if dev: host_info["mac"] = dev.mac

            if 'tcp' in nm[ip]:
                for port in nm[ip]['tcp']:
                    service_name = nm[ip]['tcp'][port]['name']
                    host_info["services"].append({
                        "port": port,
                        "name": service_name
                    })
            
            if host_info["services"]:
                results.append(host_info)
        
        return {
            "success": True,
            "cidr": cidr,
            "total_found": len(results),
            "hosts": results
        }
    except Exception as e:
        print(f"Error en escaneo masivo: {e}")
        return {"error": str(e)}
