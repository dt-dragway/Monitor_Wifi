# 🛡️ Laboratorio de Ciberseguridad Pro - NetGuard

Este laboratorio ha sido potenciado con herramientas de nivel profesional para hacking ético y monitoreo defensivo.

## 🍯 Honeypots (Puertos Trampa)
Se han configurado "HoneyPorts" en este servidor. Si algún dispositivo de la red intenta escanear o conectarse a estos puertos, se generará una alerta inmediata de **DANGER**.
- **SSH (22)**: Simula un servidor OpenSSH.
- **Telnet (23)**: Simula un servicio antiguo vulnerable.
- **RDP (3389)**: Simula acceso a escritorio remoto Windows.
- **SMB (445)**: Simula puertos de compartición de archivos (objetivo común de exploits como EternalBlue).
- **MSSQL (1433)**: Simula bases de datos.

## 🔍 Auditoría de Vulnerabilidades Pro
El escaneo de dispositivos ahora integra **Nmap Scripting Engine (NSE)**. 
- Al ejecutar un "Audit" desde la interfaz, el sistema buscará vulnerabilidades conocidas, configuraciones inseguras y servicios expuestos.
- Los resultados se clasifican automáticamente por severidad: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`.
- Los hallazgos se guardan en la base de datos para seguimiento.

## 🕵️ Detector MITM (Man-in-the-Middle)
El sistema monitorea constantemente la integridad del Gateway (Router):
- Verifica que la dirección MAC del Gateway no sea suplantada (ARP Spoofing).
- Alerta si se detecta un cambio sospechoso en la ruta de salida a Internet.

## 📊 Análisis de Tráfico Pasivo
El analizador de tráfico (sniffer) permite identificar patrones sospechosos sin necesidad de escanear activamente, manteniendo el sigilo en el laboratorio.

---
### Cómo usarlo:
1. Asegúrate de que `nmap` esté instalado en el sistema (`sudo apt install nmap`).
2. Los servicios Honeypot se inician automáticamente con el backend.
3. Puedes ver las vulnerabilidades detectadas en el nuevo endpoint `/api/security/vulnerabilities`.
