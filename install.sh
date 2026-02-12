#!/bin/bash

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🛡️  Instalador de NetGuard Profesional para Linux${NC}"
echo "------------------------------------------------"

if [ "$EUID" -ne 0 ]; then 
  echo -e "${RED}Por favor ejecuta este script como root (sudo ./install.sh)${NC}"
  exit 1
fi

INSTALL_DIR="/opt/netguard"
USER_HOME=$(eval echo ~${SUDO_USER})

echo -e "${GREEN}[1/5] Instalando dependencias del sistema...${NC}"
apt-get update -qq
apt-get install -y python3-venv python3-pip python3-gi gir1.2-webkit2-4.0 libgirepository1.0-dev libcairo2-dev -qq

echo -e "${GREEN}[2/5] Configurando directorio de instalación...${NC}"
mkdir -p "$INSTALL_DIR"
cp -r ./* "$INSTALL_DIR/"
chown -R root:root "$INSTALL_DIR"
chmod +x "$INSTALL_DIR/netguard_gui.py"
chmod +x "$INSTALL_DIR/startup.sh"

echo -e "${GREEN}[3/5] Configurando entorno virtual Python...${NC}"
cd "$INSTALL_DIR"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install pywebview pycairo PyGObject
deactivate

# Crear script de lanzamiento para la GUI (usuario normal)
cat <<EOF > /usr/bin/netguard-gui
#!/bin/bash
cd $INSTALL_DIR
source venv/bin/activate
python3 netguard_gui.py
EOF
chmod +x /usr/bin/netguard-gui

echo -e "${GREEN}[4/5] Instalando Servicio Systemd (Backend)...${NC}"
cat <<EOF > /etc/systemd/system/netguard.service
[Unit]
Description=NetGuard Security Backend Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable netguard
systemctl restart netguard

echo -e "${GREEN}[5/5] Creando Acceso Directo de Escritorio...${NC}"
cat <<EOF > /usr/share/applications/netguard.desktop
[Desktop Entry]
Name=NetGuard Pro
Comment=Monitor de Seguridad de Red Profesional
Exec=/usr/bin/netguard-gui
Icon=$INSTALL_DIR/static/img/logo.png
Terminal=false
Type=Application
Categories=Network;Security;System;
EOF

# Copiar icono si existe, o usar uno generico
if [ -f "icon.png" ]; then
    cp icon.png "$INSTALL_DIR/static/img/logo.png"
fi

echo -e "${BLUE}------------------------------------------------${NC}"
echo -e "${GREEN}✅ Instalación Completa.${NC}"
echo "NetGuard se iniciará automáticamente con el sistema."
echo "Puedes buscar 'NetGuard Pro' en tu menú de aplicaciones."
