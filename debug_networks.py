import subprocess
import json
import sys

def check_networks():
    print("🔍 Diagnosticando redes visibles...")
    try:
        result = subprocess.run(['ip', '-j', 'addr'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Error ejecutando 'ip -j addr'")
            return
            
        data = json.loads(result.stdout)
        found = False
        
        for iface in data:
            name = iface.get('ifname')
            state = iface.get('operstate', 'UNKNOWN')
            
            # Mostrar todas, incluso las DOWN, para diagnosticar
            print(f"\nInterfaz: {name} (Estado: {state})")
            
            ips = []
            for addr in iface.get('addr_info', []):
                if addr.get('family') == 'inet':
                    ip = addr.get('local')
                    prefix = addr.get('prefixlen')
                    ips.append(f"{ip}/{prefix}")
                    found = True
            
            if ips:
                print(f"  IPs detectadas: {', '.join(ips)}")
            else:
                print("  (Sin dirección IPv4)")
                
    except Exception as e:
        print(f"❌ Error crítico: {e}")

if __name__ == "__main__":
    check_networks()
