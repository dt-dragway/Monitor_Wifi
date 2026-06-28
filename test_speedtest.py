#!/usr/bin/env python3
"""
Script de prueba para verificar que speedtest-cli funciona correctamente
"""

import sys
import os

# Agregar el directorio al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=" * 60)
print("  PRUEBA DE SPEEDTEST")
print("=" * 60)
print()

try:
    import speedtest
    print("✅ Módulo speedtest importado correctamente")
    print()
    
    print("🚀 Iniciando test de velocidad...")
    print("⚠️  Esto puede tardar 30-60 segundos")
    print()
    
    st = speedtest.Speedtest()
    
    print("📡 Buscando mejor servidor...")
    st.get_best_server()
    print(f"✅ Servidor: {st.results.server['sponsor']} ({st.results.server['country']})")
    print()
    
    print("📶 Midiendo ping...")
    ping = st.results.ping
    print(f"✅ Ping: {ping:.2f} ms")
    print()
    
    print("⬇️  Midiendo velocidad de descarga...")
    download = st.download() / 1_000_000  # Convertir a Mbps
    print(f"✅ Descarga: {download:.2f} Mbps")
    print()
    
    print("⬆️  Midiendo velocidad de subida...")
    upload = st.upload() / 1_000_000  # Convertir a Mbps
    print(f"✅ Subida: {upload:.2f} Mbps")
    print()
    
    print("=" * 60)
    print("  RESULTADOS FINALES")
    print("=" * 60)
    print(f"  📶 Ping:     {ping:.2f} ms")
    print(f"  ⬇️  Descarga: {download:.2f} Mbps")
    print(f"  ⬆️  Subida:   {upload:.2f} Mbps")
    print("=" * 60)
    print()
    print("✅ Test completado exitosamente")
    
except ImportError as e:
    print("❌ Error: No se pudo importar el módulo speedtest")
    print(f"   Detalles: {e}")
    print()
    print("💡 Solución: Instala speedtest-cli con:")
    print("   ./venv/bin/pip install speedtest-cli")
    sys.exit(1)
    
except Exception as e:
    print(f"❌ Error durante el test: {e}")
    print()
    print("💡 Posibles causas:")
    print("   - Sin conexión a internet")
    print("   - Firewall bloqueando speedtest")
    print("   - Problema con el módulo speedtest-cli")
    sys.exit(1)
