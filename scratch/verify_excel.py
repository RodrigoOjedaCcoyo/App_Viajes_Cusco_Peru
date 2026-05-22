# scratch/verify_excel.py
import sys
import os
sys.path.append(os.getcwd())

from controllers.excel_controller import ExcelController

def test_excel():
    print("Testing ExcelController...")
    controller = ExcelController()

    # Mock data structure matching data_hoja for master sheet
    mock_data = {
        'venta': {
            'id_venta': 999,
            'nombre_cliente': 'Juan Perez',
            'telefono': '+51 987654321',
            'tour_nombre': 'Machu Picchu VIP',
            'fecha_inicio': '2026-06-01',
            'fecha_fin': '2026-06-05',
            'num_pasajeros': 2,
            'monto_total': 1500.0,
            'monto_pagado': 1000.0,
            'total_reembolsado': 0.0,
            'moneda': 'USD',
            'tipo_cambio': 3.82,
            'estado_venta': 'CONFIRMADO',
            'drive_url': 'http://drive.google.com/test'
        },
        'itinerario': [
            {
                'Día Itin.': 1,
                'Fecha': '2026-06-01',
                'Hora': '08:00',
                'Servicio': 'City Tour Cusco',
                'Proveedor': 'Cusco Transport',
                'Pax': 2,
                'Tipo': 'Tour',
                'observacion': 'Hotel pickup'
            }
        ],
        'pasajeros': [
            {
                'nombre_completo': 'Juan Perez',
                'numero_documento': '12345678',
                'tipo_documento': 'DNI',
                'fecha_nacimiento': '1990-05-15',
                'fecha_caducidad_doc': '2030-05-15',
                'nacionalidad': 'Peruana',
                'edad': 36,
                'genero': 'Masculino',
                'cuidados_especiales': 'Ninguno',
                'es_principal': True
            }
        ],
        'liquidaciones': [
            {
                'n_linea': 1,
                'proveedor': {'nombre_comercial': 'Hotel Hilton'},
                'tipo_servicio': 'HOSPEDAJE',
                'moneda': 'PEN',
                'costo_unitario': 200.0,
                'cantidad_pax': 2,
                'tipo_cambio': 3.80,
                'terminado': True,
                'metodo_pago': 'TRANSFERENCIA',
                'observaciones_contables': 'Paid on account'
            },
            {
                'n_linea': 2,
                'proveedor': {'nombre_comercial': 'Machu Picchu Entrance'},
                'tipo_servicio': 'TICKET',
                'moneda': 'USD',
                'costo_unitario': 50.0,
                'cantidad_pax': 2,
                'tipo_cambio': 1.0,
                'terminado': False,
                'metodo_pago': 'EFECTIVO',
                'observaciones_contables': 'Pending payment'
            }
        ]
    }

    try:
        buffer = controller.generar_hoja_servicio_maestra_xlsx(mock_data)
        print("Master spreadsheet buffer generated successfully!")
        print(f"Buffer size: {len(buffer.getvalue())} bytes")
        
        # Save to artifacts for inspection
        output_path = "artifacts/test_reporte_maestro.xlsx"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(buffer.getvalue())
        print(f"Saved generated Excel to {output_path} for visual inspection!")
        
    except Exception as e:
        print(f"FAILED Master sheet generation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_excel()
