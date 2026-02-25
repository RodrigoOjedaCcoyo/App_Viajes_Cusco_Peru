
# debug_report.py
from supabase import create_client
import os
from controllers.operaciones_controller import OperacionesController
from controllers.excel_controller import ExcelController
from controllers.venta_controller import VentaController
from datetime import date

# Configuración (Ajustar con tus credenciales si es necesario, o usar env)
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

controller = OperacionesController(supabase)
xl_ctrl = ExcelController()

id_venta = 14  # Cambia por un ID de venta válido en tu DB

try:
    print(f"--- Iniciando Depuración para Venta {id_venta} ---")
    
    # 1. Obtener Datos de la Venta
    res_v = supabase.table('venta').select('*, cliente(nombre, lead(numero_celular))').eq('id_venta', id_venta).single().execute()
    v_raw = res_v.data
    print("Venta cargada correctamente.")
    
    cliente_nest = v_raw.get('cliente', {})
    lead_nest = cliente_nest.get('lead', {}) if isinstance(cliente_nest, dict) else {}
    
    v_data = {
        "id_venta": v_raw['id_venta'],
        "nombre_cliente": cliente_nest.get('nombre', 'Desconocido'),
        "telefono": lead_nest.get('numero_celular', '---'),
        "tour_nombre": v_raw.get('tour_nombre', 'Sin Tour'),
        "fecha_inicio": v_raw.get('fecha_inicio'),
        "fecha_fin": v_raw.get('fecha_fin'),
        "num_pasajeros": v_raw.get('num_pasajeros', 1),
        "vendedor": "---", 
        "moneda": v_raw.get('moneda', 'USD'),
        "monto_total": v_raw.get('precio_total_cierre', 0),
        "monto_pagado": 0 
    }

    # 2. Calcular Pagos
    res_p = supabase.table('pago').select('monto_pagado').eq('id_venta', id_venta).execute()
    v_data['monto_pagado'] = sum(float(p['monto_pagado'] or 0) for p in res_p.data)
    print(f"Pagos calculados: {v_data['monto_pagado']}")

    # 3. Obtener Itinerario Logístico
    itinerario = controller.get_servicios_rango_fechas(date(2000,1,1), date(2100,1,1))
    it_venta = [s for s in itinerario if s['ID Venta'] == id_venta]
    print(f"Servicios encontrados: {len(it_venta)}")

    # 4. Obtener Pasajeros
    pasajeros = controller.pasajero_model.get_by_venta_id(id_venta)
    print(f"Pasajeros encontrados: {len(pasajeros)}")

    # 5. Obtener Liquidación Detallada (Costos)
    liquidaciones = controller.get_liquidaciones_venta(id_venta)
    print(f"Liquidaciones encontradas: {len(liquidaciones)}")

    # 6. Generar Excel
    data_hoja = {
        "venta": v_data,
        "itinerario": it_venta,
        "pasajeros": pasajeros,
        "liquidaciones": liquidaciones
    }
    
    print("Generando Excel...")
    master_buffer = xl_ctrl.generar_hoja_servicio_maestra_xlsx(data_hoja)
    
    if master_buffer:
        with open(f"test_report_{id_venta}.xlsx", "wb") as f:
            f.write(master_buffer.getvalue())
        print(f"✅ ÉXITO: Reporte generado en test_report_{id_venta}.xlsx")
    else:
        print("❌ ERROR: El buffer del Excel salió vacío.")

except Exception as e:
    print(f"❌ FALLO TÉCNICO: {e}")
    import traceback
    traceback.print_exc()
