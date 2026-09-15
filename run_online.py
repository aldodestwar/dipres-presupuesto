"""
Launcher con Soporte de Enlace Online Automático (Cloudflare Tunnel).
Inicia Streamlit localmente y habilita un enlace público HTTPS seguro para compartir por Internet.
"""
import sys
import os
import time
import socket
import atexit
import signal
import webbrowser
import subprocess
import urllib.request
from pathlib import Path

# Configurar salida UTF-8 segura y sin retrasos de búfer en Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
        sys.stderr.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from src.tunnel_manager import start_tunnel, stop_tunnel, get_active_url, get_local_ip, copy_to_clipboard

def is_streamlit_running(port=8501):
    """Verifica si Streamlit ya está respondiendo en el puerto local."""
    try:
        url = f"http://localhost:{port}/_stcore/health"
        req = urllib.request.Request(url, headers={"User-Agent": "HealthCheck"})
        with urllib.request.urlopen(req, timeout=1.5) as response:
            return response.status == 200
    except Exception:
        return False

def wait_for_streamlit(port=8501, max_seconds=20):
    """Espera a que Streamlit esté listo para recibir peticiones."""
    start = time.time()
    while time.time() - start < max_seconds:
        if is_streamlit_running(port):
            return True
        time.sleep(0.4)
    return False

def main():
    port = 8501
    print("=" * 70)
    print("        DASHBOARD DE EJECUCIÓN PRESUPUESTARIA DIPRES")
    print("=" * 70)

    # 1. Asegurar estado de Streamlit
    p_streamlit = None
    if is_streamlit_running(port):
        print(f"[*] Streamlit ya está en ejecución en http://localhost:{port}")
    else:
        print(f"[*] Iniciando servidor local Streamlit (puerto {port})...")
        st_cmd = [
            sys.executable, "-m", "streamlit", "run", "app.py",
            f"--server.port={port}",
            "--server.headless=true"
        ]
        p_streamlit = subprocess.Popen(st_cmd, cwd=str(BASE_DIR))
        
        print("[*] Esperando inicialización del servidor...")
        if not wait_for_streamlit(port, max_seconds=25):
            print("[!] Advertencia: El servidor local tardó en responder, continuando...")

    # 2. Iniciar Túnel Online
    print("[*] Habilitando enlace público seguro en línea (Cloudflare Tunnel)...")
    public_url = start_tunnel(port=port, timeout_seconds=20)

    # 3. Datos de red
    local_ip = get_local_ip()
    local_url = f"http://localhost:{port}"
    network_url = f"http://{local_ip}:{port}"

    # 4. Imprimir resumen
    print("\n" + "=" * 70)
    print("       >>> DASHBOARD EN EJECUCION Y ACCESIBLE ONLINE <<<")
    print("=" * 70)
    
    if public_url:
        print("\n  [ONLINE] ENLACE PUBLICO (ACCESO DESDE CUALQUIER LUGAR POR INTERNET):")
        print(f"     >>  {public_url}")
        print("     (OK: Copiado automaticamente al portapapeles)")
    else:
        print("\n  [!] No se pudo generar el enlace publico temporal.")
        print("      Puedes usar el boton 'Habilitar Enlace Online' en el panel lateral.")

    print(f"\n  [LOCAL]  ENLACE LOCAL (ESTE EQUIPO):")
    print(f"     >>  {local_url}")

    print(f"\n  [RED]    ENLACE RED LOCAL (MISMA RED WI-FI / CELULAR EN MISMA RED):")
    print(f"     >>  {network_url}")

    print("\n" + "-" * 70)
    print("  Manten esta ventana abierta mientras desees compartir la app.")
    print("  Para detener todo, presiona [Ctrl + C].")
    print("=" * 70 + "\n")

    # Abrir en navegador local
    try:
        webbrowser.open(local_url)
    except Exception:
        pass

    # Función de salida segura
    def cleanup(*args):
        print("\n[*] Cerrando servicios y túnel online...")
        stop_tunnel()
        if p_streamlit and p_streamlit.poll() is None:
            try:
                p_streamlit.terminate()
                p_streamlit.kill()
            except Exception:
                pass
        print("[✓] Todo detenido correctamente.")
        sys.exit(0)

    # Registrar señales de término
    atexit.register(stop_tunnel)
    signal.signal(signal.SIGINT, cleanup)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, cleanup)

    # Mantener el proceso vivo
    try:
        while True:
            if p_streamlit and p_streamlit.poll() is not None:
                # Si el proceso de Streamlit terminó por su cuenta
                break
            time.sleep(1)
    except KeyboardInterrupt:
        cleanup()

if __name__ == "__main__":
    main()
