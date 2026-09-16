"""
Streamlit Community Cloud Entrypoint.
Punto de entrada compatible para despliegues automáticos en Streamlit Cloud.
Redirige la ejecución directamente a app.py.
"""
import runpy
from pathlib import Path

app_path = Path(__file__).resolve().parent / "app.py"
runpy.run_path(str(app_path), run_name="__main__")
