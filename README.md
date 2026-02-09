# Monitor Wifi Profesional 📡

Un sistema avanzado de vigilancia y monitoreo de red local, diseñado con una interfaz moderna y funcionalidades premium para detectar dispositivos, identificar intrusos y gestionar la seguridad de tu Wifi.

![Dashboard Preview](https://via.placeholder.com/800x400?text=Dashboard+Monitor+Wifi+Pro)

## 🚀 Características Premium

### 🎨 Interfaz Moderna (Glassmorphism)
- Diseño oscuro elegante con efectos de cristal y desenfoque.
- Animaciones suaves y transiciones fluidas.
- Iconos dinámicos que se adaptan al tipo de dispositivo (Windows, Apple, Android, SmartTV, Consolas, etc.).

### 🔍 Escaneo Inteligente
- **Detección ARP:** Utiliza el protocolo ARP para descubrir todos los dispositivos conectados en tu red local (LAN/WLAN) de forma fiable.
- **Identificación de Fabricante:** Muestra el fabricante del dispositivo (Vendor) basado en su dirección MAC.
- **Resolución de Hostname:** Intenta obtener el nombre del equipo (NetBIOS/DNS) para identificar fácilmente PCs Windows y servidores (ej: `DESKTOP-J8K2L`).

### 🛡️ Gestión de Seguridad
- **Clasificación de Confianza:** Marca tus dispositivos conocidos en **Verde** y recibe alertas visuales claras (**Rojo**) para nuevos dispositivos desconocidos.
- **Alias Personalizados:** Asigna nombres amigables a tus dispositivos (ej: "iPhone de María", "TV Sala").
- **Alertas Profesionales:** Sistema de notificaciones moderno (SweetAlert2) para confirmar acciones y mostrar estados.
- **Historial Persistente:** Base de datos local (`devices.db`) que recuerda tus preferencias y configuraciones.

## 🛠️ Instalación y Uso

### Prerequisitos
- Sistema operativo Linux (probado en Ubuntu/Debian/Mint).
- Python 3.10 o superior.
- Privilegios de administrador (`sudo`) para el escaneo de red ARP.

### Pasos
1.  **Clonar el repositorio** (o descargar los archivos):
    ```bash
    git clone https://github.com/tu-usuario/monitor-wifi-pro.git
    cd monitor-wifi-pro
    ```

2.  **Iniciar la aplicación**:
    El script `startup.sh` se encarga de todo: crear el entorno virtual, instalar dependencias y lanzar el servidor.
    ```bash
    sudo ./startup.sh
    ```
    *(La contraseña de sudo es necesaria para que `scapy` pueda enviar paquetes ARP a la red).*

3.  **Acceder al Dashboard**:
    Abre tu navegador web favorito y visita:
    👉 **http://localhost:8000**

## 🔧 Tecnologías Utilizadas

- **Backend:** Python, FastAPI, SQLModel (SQLite), Scapy.
- **Frontend:** HTML5, TailwindCSS (CDN), JavaScript (Vanilla), SweetAlert2.
- **Herramientas:** Uvicorn (Servidor ASGI), MacVendorLookup.

## ⚠️ Nota Legal y Responsabilidad
Este software está diseñado para uso educativo y personal en redes propias. El escaneo de redes ajenas sin autorización puede ser ilegal. El desarrollador no se hace responsable del mal uso de esta herramienta.

---
Desarrollado con ❤️ por [Tu Nombre/Alias]
