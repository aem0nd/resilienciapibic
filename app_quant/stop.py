import os
import sys
import signal

PID_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'analise_quant.pid')

def main():
    if not os.path.exists(PID_FILE):
        print("❌ Arquivo PID não encontrado. O serviço já está parado.")
        return
    try:
        pid = int(open(PID_FILE).read().strip())
    except Exception:
        print("❌ PID inválido.")
        return

    try:
        if sys.platform == 'win32':
            os.system(f'taskkill /PID {pid} /F > nul 2>&1')
        else:
            os.kill(pid, signal.SIGTERM)
        print(f"✅ Processo {pid} encerrado.")
    except Exception as e:
        print(f"⚠️  Não foi possível encerrar: {e}")

    try: os.remove(PID_FILE)
    except Exception: pass

if __name__ == '__main__':
    main()