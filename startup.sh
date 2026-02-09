#!/bin/bash
echo "Iniciando Monitor Wifi Profesional..."

# Verificar si se ejecuta como root (opcional, scapy a veces lo requiere)
if [ "$EUID" -ne 0 ]
  then echo "Advertencia: Para un escaneo de red completo (ARP), se recomienda ejecutar como root."
  echo "Ejecute: sudo ./startup.sh"
  # No forzamos salida
fi

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    echo "Creando entorno virtual..."
    python3 -m venv venv
fi

# Activar entorno virtual
echo "Activando entorno virtual..."
source venv/bin/activate

# Instalar requerimientos
echo "Instalando dependencias..."
pip install -r requirements.txt

# Iniciar servidor
echo "Iniciando servidor web en http://0.0.0.0:8000"
# Escuchar en todas las interfaces, puerto 8000
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
