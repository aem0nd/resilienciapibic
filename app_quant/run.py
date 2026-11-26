"""
PONTO DE ENTRADA. Uso: python run.py
Para parar: CTRL+C ou parar.bat / parar.sh
"""
import os
import sys
import signal
import threading
import time

PID_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'analise_quant.pid')

def main():
    try:
        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
    except Exception:
        pass

    stop_event = threading.Event()
    run_now_event = threading.Event()

    def shutdown(signum, frame):
        print("\n⏹  Desligando...")
        stop_event.set()
        time.sleep(1.5)
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    try:
        signal.signal(signal.SIGTERM, shutdown)
    except Exception:
        pass

    from worker import rodar_worker
    from server import iniciar_server
    from config import PORT

    wt = threading.Thread(target=rodar_worker, args=(stop_event, run_now_event), daemon=True)
    wt.start()

    print("=" * 60)
    print(f"🌐 Painel disponível em: http://localhost:{PORT}")
    print(f"   Rede local: http://<SEU-IP>:{PORT}")
    print("   Para parar: CTRL+C ou parar.bat/parar.sh")
    print("=" * 60)

    try:
        iniciar_server(stop_event, run_now_event)
    finally:
        stop_event.set()
        time.sleep(1)
        try: os.remove(PID_FILE)
        except Exception: pass

if __name__ == '__main__':
    main()