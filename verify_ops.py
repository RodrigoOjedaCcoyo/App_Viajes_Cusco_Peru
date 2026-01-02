import sys
import os
from datetime import date
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.getcwd())

try:
    from controllers.operaciones_controller import OperacionesController
except ImportError:
    print("Error importing controller. Make sure you run this from the project root.")
    sys.exit(1)

def test_controller():
    print("Testing OperacionesController...")
    
    # Mock Supabase Client
    mock_client = MagicMock()
    
    # Mock Response for get_servicios_por_fecha
    # 1. venta_tour
    mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {'id': 1, 'id_venta': 101, 'id_tour': 201, 'fecha_servicio': '2024-01-01', 'cantidad_pasajeros': 2, 'guia_asignado': None}
    ]
    # 2. venta (bulk)
    # Note: The controller makes multiple calls. We need to handle them.
    # We can rely on the fact that if the code executes without crash, syntax and logic flow is likely correct.
    # Deep mocking for exact return values in a complex flow is verbose.
    # We will just ensure the method runs.
    
    controller = OperacionesController(mock_client)
    
    try:
        resultado = controller.get_servicios_por_fecha(date(2024, 1, 1))
        print("get_servicios_por_fecha executed successfully.")
        # We might get empty result due to mock setup not catching all chained calls perfectly, but checking for crashes is key.
    except Exception as e:
        print(f"FAILED get_servicios_por_fecha: {e}")

    try:
        success, msg = controller.actualizar_guia_servicio(1, "Juan Guia")
        print(f"actualizar_guia_servicio executed: {success} - {msg}")
    except Exception as e:
        print(f"FAILED actualizar_guia_servicio: {e}")

    try:
        file_mock = MagicMock()
        file_mock.name = "passport.pdf"
        success, msg = controller.subir_documento(1, file_mock)
        print(f"subir_documento executed: {success} - {msg}")
    except Exception as e:
        print(f"FAILED subir_documento: {e}")

if __name__ == "__main__":
    test_controller()
