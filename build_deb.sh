#!/bin/bash

# Configuración
APP_NAME="netguard"
VERSION="1.0"
ARCH="amd64"
BUILD_DIR="build_deb"
DEB_NAME="${APP_NAME}_${VERSION}_${ARCH}"
TARGET_DIR="$BUILD_DIR/$DEB_NAME"

echo "📦 Iniciando construcción del paquete .deb para $APP_NAME..."

# 1. Limpiar y Crear Directorios
rm -rf "$BUILD_DIR"
mkdir -p "$TARGET_DIR/DEBIAN"
mkdir -p "$TARGET_DIR/opt/$APP_NAME"
mkdir -p "$TARGET_DIR/usr/bin"
mkdir -p "$TARGET_DIR/usr/share/applications"
mkdir -p "$TARGET_DIR/usr/share/icons/hicolor/512x512/apps"
mkdir -p "$TARGET_DIR/etc/systemd/system"

# 2. Copiar Archivos del Proyecto a /opt/netguard
echo "📂 Copiando archivos fuente..."
# Excluir venv, git, y archivos temporales
rsync -av --progress . "$TARGET_DIR/opt/$APP_NAME" \
    --exclude venv \
    --exclude .git \
    --exclude .gitignore \
    --exclude build_deb \
    --exclude *.deb \
    --exclude __pycache__ \
    --exclude .gemini \
    --exclude logs \
    --exclude tmp

# Copiar icono
if [ -f "icon.png" ]; then
    cp icon.png "$TARGET_DIR/usr/share/icons/hicolor/512x512/apps/$APP_NAME.png"
fi

# 3. Crear Lanzador (/usr/bin/netguard)
echo "🚀 Creando lanzador..."
cat <<EOF > "$TARGET_DIR/usr/bin/$APP_NAME"
#!/bin/bash
export NETGUARD_HOME=/opt/$APP_NAME
cd /opt/$APP_NAME
# Usar explícitamente el python del entorno virtual
exec /opt/$APP_NAME/venv/bin/python3 netguard_gui.py
EOF
chmod +x "$TARGET_DIR/usr/bin/$APP_NAME"

# 4. Crear Archivo .desktop
echo "🖥️  Creando acceso directo..."
cat <<EOF > "$TARGET_DIR/usr/share/applications/$APP_NAME.desktop"
[Desktop Entry]
Name=NetGuard Pro
Comment=Monitor de Seguridad de Red Profesional
Exec=/usr/bin/$APP_NAME
Icon=$APP_NAME
Terminal=false
Type=Application
Categories=Network;Security;System;
StartupWMClass=NetGuard Pro
StartupNotify=true
EOF

# 5. Crear Servicio Systemd
echo "⚙️  Creando servicio systemd..."
cat <<EOF > "$TARGET_DIR/etc/systemd/system/$APP_NAME.service"
[Unit]
Description=NetGuard Security Backend Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/$APP_NAME
ExecStart=/opt/$APP_NAME/venv/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 6. Crear Archivo de Control (Metadatos y Dependencias)
echo "📝 Creando metadatos (control)..."
cat <<EOF > "$TARGET_DIR/DEBIAN/control"
Package: $APP_NAME
Version: $VERSION
Section: utils
Priority: optional
Architecture: $ARCH
Maintainer: JDiaz <jdiaz1589@outlook.com>
Depends: python3, python3-venv, python3-pip, python3-gi, gir1.2-webkit2-4.0, libgirepository1.0-dev, libcairo2-dev, git, rsync, python3-requests, libnotify-bin
Description: Monitor de Seguridad Wifi y Red Profesional
 NetGuard protege tu red detectando intrusos en tiempo real,
 monitoreando el tráfico y gestionando dispositivos.
EOF

# 7. Script Post-Instalación (Configura venv y permisos)
echo "🔧 Creando script post-instalación..."
cat <<EOF > "$TARGET_DIR/DEBIAN/postinst"
#!/bin/bash
set -e

echo "🔧 Configurando NetGuard Pro..."

# Crear entorno virtual en /opt/netguard
cd /opt/$APP_NAME
if [ ! -d "venv" ]; then
    echo "📦 Creando entorno virtual Python..."
    python3 -m venv venv --system-site-packages
fi

# Instalar dependencias Python dentro del venv
echo "📥 Instalando librerías Python..."
./venv/bin/pip install --no-cache-dir -r requirements.txt
./venv/bin/pip install --no-cache-dir pywebview pystray Pillow

# Permisos
chown -R root:root /opt/$APP_NAME
chmod +x /opt/$APP_NAME/startup.sh

# Recargar servicios
systemctl daemon-reload
systemctl enable $APP_NAME
systemctl restart $APP_NAME

echo "✅ NetGuard configurado correctamente."
exit 0
EOF
chmod 755 "$TARGET_DIR/DEBIAN/postinst"

# 8. Script Pre-Eliminación (Limpia servicio)
cat <<EOF > "$TARGET_DIR/DEBIAN/prerm"
#!/bin/bash
set -e
systemctl stop $APP_NAME
systemctl disable $APP_NAME
exit 0
EOF
chmod 755 "$TARGET_DIR/DEBIAN/prerm"

# 9. Construir el paquete
echo "🔨 Compilando .deb..."
dpkg-deb --build "$TARGET_DIR"

mv "$BUILD_DIR/$DEB_NAME.deb" .
echo "🎉 Paquete creado: $(pwd)/$DEB_NAME.deb"
echo "👉 Instálalo con: sudo apt install ./$DEB_NAME.deb"

# Limpieza
rm -rf "$BUILD_DIR"
