
from scapy.all import sniff, ARP, IP

print("🔍 Iniciando Sniffer (Diagnostic Mode)...")
print("Si ves paquetes aquí, la tarjeta de red funciona.")
print("Si NO ves nada, hay un problema físico o de permisos.")

def packet_callback(packet):
    if ARP in packet:
        op = packet[ARP].op
        if op == 1:  # who-has
            print(f"⚡ ARP Request: {packet[ARP].psrc} pregunta por {packet[ARP].pdst} ({packet[ARP].hwsrc})")
        elif op == 2:  # is-at
            print(f"✅ ARP Reply:   {packet[ARP].psrc} es {packet[ARP].hwsrc}")
            
    elif IP in packet:
        # Solo mostramos broadcast o multicast para no saturar, o unicast si es prominente
        if packet[IP].dst == "255.255.255.255":
            print(f"📡 Broadcast IP: {packet[IP].src} -> {packet[IP].dst}")

sniff(prn=packet_callback, store=0, count=20, timeout=10)
print("🛑 Fin del diagnóstico.")
