
import sys
import os

# Simular el entorno de main.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
sys.path.insert(1, os.path.join(BASE_DIR, 'controllers'))
sys.path.insert(1, os.path.join(BASE_DIR, 'vistas'))
sys.path.insert(1, os.path.join(BASE_DIR, 'models'))

print("--- Iniciando Diagnóstico de Imports ---")
print(f"SYS.PATH: {sys.path}")

try:
    print("1. Intentando importar models.lead_model...")
    import models.lead_model
    print("   -> OK")
except Exception as e:
    print(f"   -> FALLO: {e}")

try:
    print("2. Intentando importar controllers.lead_controller...")
    import controllers.lead_controller
    print("   -> OK")
except Exception as e:
    print(f"   -> FALLO: {e}")

try:
    print("3. Intentando importar controllers.venta_controller...")
    import controllers.venta_controller
    print("   -> OK")
except Exception as e:
    print(f"   -> FALLO: {e}")

try:
    print("4. Intentando importar vistas.funcionalidad_page_ventas...")
    import vistas.funcionalidad_page_ventas
    print("   -> OK")
except Exception as e:
    print(f"   -> FALLO CRÍTICO EN VISTA: {e}")
    import traceback
    traceback.print_exc()

print("--- Fin del Diagnóstico ---")
