
import speedtest
from sqlmodel import Session
from .database import engine
from .models import SpeedTestResult
from datetime import datetime

def run_speedtest():
    """
    Ejecuta un test de velocidad y guarda los resultados en la base de datos.
    Retorna el objeto SpeedTestResult o None si falla.
    Nota: Esta función es bloqueante y puede tardar 20-40 segundos.
    """
    print("🚀 Iniciando Speedtest...")
    try:
        st = speedtest.Speedtest()
        st.get_best_server()
        
        ping = st.results.ping
        
        print("⬇️ Midiendo descarga...")
        download = st.download() / 1_000_000 # Mbps
        
        print("⬆️ Midiendo subida...")
        upload = st.upload() / 1_000_000 # Mbps
        
        # Save to DB
        with Session(engine) as session:
            result = SpeedTestResult(
                timestamp=datetime.utcnow(),
                ping=round(ping, 2),
                download=round(download, 2),
                upload=round(upload, 2)
            )
            session.add(result)
            session.commit()
            session.refresh(result)
            
        print(f"✅ Speedtest finalizado: Ping {ping:.1f}ms, Down {download:.1f}Mbps, Up {upload:.1f}Mbps")
        
        # Log event
        from .logger import log_event
        log_event("INFO", f"Speedtest: ⬇️{download:.1f} Mb/s ⬆️{upload:.1f} Mb/s 📶{ping:.0f}ms")
        
        return result
    except Exception as e:
        print(f"Error running speedtest: {e}")
        from .logger import log_event
        log_event("WARNING", f"Fallo en Speedtest: {str(e)}")
        return None
