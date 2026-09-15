"""
Módulo de Gestión de Túnel Online Seguro (Cloudflare Tunnel) para Streamlit.
Permite habilitar y compartir una URL pública HTTPS sin costo, sin registros y con soporte WebSockets.
"""
import sys
import os
import re
import time
import socket
import urllib.request
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CLOUDFLARED_EXE = BASE_DIR / "cloudflared.exe"
TUNNEL_URL_FILE = BASE_DIR / ".tunnel_url"
CLOUDFLARED_URL = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"

_active_process = None

def get_local_ip():
    """Obtiene la IP local de la máquina en la red local (Wi-Fi/LAN)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "localhost"

def ensure_cloudflared(progress_callback=None):
    """Verifica que cloudflared.exe exista, y si no, lo descarga automáticamente."""
    if CLOUDFLARED_EXE.exists():
        return True
    
    if progress_callback:
        progress_callback("Descargando componente para túnel online...")
    else:
        print("[*] Descargando componente para túnel online (cloudflared)...")
        
    try:
        urllib.request.urlretrieve(CLOUDFLARED_URL, CLOUDFLARED_EXE)
        return True
    except Exception as e:
        print(f"[!] Error al descargar cloudflared: {e}")
        return False

def copy_to_clipboard(text):
    """Copia texto al portapapeles en Windows sin dependencias externas."""
    try:
        process = subprocess.Popen('clip', stdin=subprocess.PIPE, shell=True)
        process.communicate(input=text.strip().encode('utf-8'))
        return True
    except Exception:
        return False

def get_active_url():
    """Devuelve la URL pública activa si existe y es válida."""
    if not TUNNEL_URL_FILE.exists():
        return None
    try:
        url = TUNNEL_URL_FILE.read_text(encoding="utf-8").strip()
        if url.startswith("https://") and "trycloudflare.com" in url:
            return url
    except Exception:
        pass
    return None

def start_tunnel(port=8501, timeout_seconds=15):
    """
    Inicia el túnel de Cloudflare apuntando al puerto local especificado.
    Retorna la URL pública HTTPS o None si falla.
    """
    global _active_process

    # Verificar si ya tenemos un túnel activo válido
    current_url = get_active_url()
    if current_url:
        return current_url

    if not ensure_cloudflared():
        return None

    # Comando de túnel Cloudflare
    cmd = [str(CLOUDFLARED_EXE), "tunnel", "--url", f"http://localhost:{port}"]
    
    # Flags para evitar ventana emergente en Windows si se corre en segundo plano
    creationflags = 0
    if sys.platform == "win32":
        creationflags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0x08000000

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            cwd=str(BASE_DIR),
            creationflags=creationflags
        )
        _active_process = proc

        start_time = time.time()
        url = None
        while time.time() - start_time < timeout_seconds:
            if proc.poll() is not None:
                break
            line = proc.stderr.readline()
            if not line:
                time.sleep(0.08)
                continue
            match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
            if match:
                url = match.group(0)
                break

        if url:
            try:
                TUNNEL_URL_FILE.write_text(url, encoding="utf-8")
            except Exception:
                pass
            copy_to_clipboard(url)
            return url
        else:
            proc.terminate()
            return None
    except Exception as e:
        print(f"[!] Error al iniciar túnel: {e}")
        return None

def stop_tunnel():
    """Detiene el túnel activo y elimina el archivo de URL."""
    global _active_process
    if _active_process and _active_process.poll() is None:
        try:
            _active_process.terminate()
            _active_process.kill()
        except Exception:
            pass
        _active_process = None

    if TUNNEL_URL_FILE.exists():
        try:
            TUNNEL_URL_FILE.unlink()
        except Exception:
            pass

    # En Windows, asegurar que no queden procesos huérfanos de cloudflared
    if sys.platform == "win32":
        try:
            subprocess.run("taskkill /F /IM cloudflared.exe", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
