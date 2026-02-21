# controllers/operaciones_controller.py
from models.operaciones_model import PasajeroModel
from models.venta_model import VentaModel
from datetime import date, timedelta
from supabase import Client
import pandas as pd

class OperacionesController:
    # Inyección de dependencia del Cliente Supabase
    def __init__(self, supabase_client: Client):
        self.client = supabase_client
        self.venta_model = VentaModel(supabase_client)
        self.pasajero_model = PasajeroModel(supabase_client)

    # ------------------------------------------------------------------
    # LÓGICA DE TABLERO DE EJECUCIÓN DIARIA (Dashboard #2)
    # ------------------------------------------------------------------

    def get_fechas_con_servicios(self, year: int, month: int):
        try:
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1)
            else:
                end_date = date(year, month + 1, 1)
                
            res = (
                self.client.table('venta_tour')
                .select('fecha_servicio')
                .gte('fecha_servicio', start_date.isoformat())
                .lt('fecha_servicio', end_date.isoformat())
                .execute()
            )
            
            fechas_activas = set()
            if res.data:
                # DEBUG print(f"DEBUG: Found {len(res.data)} services for {month}/{year}")
                for item in res.data:
                    try:
                        f_raw = item['fecha_servicio']
                        f_date = pd.to_datetime(f_raw).date()
                        fechas_activas.add(f_date)
                    except Exception as e:
                        # DEBUG print(f"DEBUG: Error parsing date {item.get('fecha_servicio')}: {e}")
                        pass
            return list(fechas_activas)
        except Exception as e:
            print(f"Error en Calendario: {e}")
            return []

    def get_servicios_rango_fechas(self, start_date: date, end_date: date):
        """Obtiene servicios para un rango de fechas con nombres de clientes y ventas."""
        try:
            print(f"DEBUG Dashboard: Querying range {start_date} to {end_date}")
            res_servicios = (
                self.client.table('venta_tour')
                .select('*')
                .gte('fecha_servicio', start_date.isoformat())
                .lt('fecha_servicio', (end_date + timedelta(days=1)).isoformat())
                .order('fecha_servicio')
                .execute()
            )
            print(f"DEBUG Dashboard: Found {len(res_servicios.data or [])} raw rows in range")
            
            if not res_servicios.data:
                return []
                
            servicios_data = res_servicios.data
            ids_ventas = list(set([s['id_venta'] for s in servicios_data]))
            ids_tours = list(set([s['id_tour'] for s in servicios_data if s.get('id_tour')]))
            
            ventas_map = {}
            if ids_ventas:
                res_v = self.client.table('venta').select('*').in_('id_venta', ids_ventas).execute()
                for v in res_v.data:
                    ventas_map[v['id_venta']] = v
                    
            tours_map = {}
            if ids_tours:
                res_t = self.client.table('tour').select('id_tour, nombre').in_('id_tour', ids_tours).execute()
                for t in res_t.data:
                    tours_map[t['id_tour']] = t['nombre']
                    
            ids_clientes = list(set([v['id_cliente'] for v in ventas_map.values() if v.get('id_cliente')]))
            clientes_map = {}
            if ids_clientes:
                res_c = self.client.table('cliente').select('id_cliente, nombre').in_('id_cliente', ids_clientes).execute()
                for c in res_c.data:
                    clientes_map[c['id_cliente']] = c['nombre']

            pagos_map = {} 
            if ids_ventas:
                res_p = self.client.table('pago').select('id_venta, monto_pagado').in_('id_venta', ids_ventas).execute()
                for p in res_p.data:
                    vid = p['id_venta']
                    pagos_map[vid] = pagos_map.get(vid, 0) + (p['monto_pagado'] or 0)

            # Guías y Endosos
            guias_map = {}
            proveedor_endoso_map = {}
            detalles_proveedores_map = {}
            if ids_ventas:
                res_g = (
                    self.client.table('venta_servicio_proveedor')
                    .select('id_venta, n_linea, tipo_servicio, proveedor(nombre_comercial)')
                    .in_('id_venta', ids_ventas)
                    .execute()
                )
                for g in res_g.data:
                    key = f"{g['id_venta']}-{g['n_linea']}"
                    prov_nom = g['proveedor']['nombre_comercial'] if g.get('proveedor') else "Desconocido"
                    if g.get('tipo_servicio') == 'GUIA':
                        guias_map[key] = prov_nom
                    elif g.get('tipo_servicio') == 'ENDOSE':
                        proveedor_endoso_map[key] = prov_nom
                    
                    if key not in detalles_proveedores_map:
                        detalles_proveedores_map[key] = []
                    detalles_proveedores_map[key].append({
                        "tipo": g.get('tipo_servicio'),
                        "nombre": prov_nom,
                        "estado": 'PENDIENTE' # Por defecto ya que no está en DB aún
                    })
            
            resultado = []
            for s in servicios_data:
                v = ventas_map.get(s['id_venta'], {})
                id_cliente = v.get('id_cliente')
                nombre_cliente = clientes_map.get(id_cliente, "Desconocido")
                
                precio_total = v.get('precio_total_cierre', 0) or 0
                total_pagado = pagos_map.get(s['id_venta'], 0)
                saldo = precio_total - total_pagado
                estado_pago = "✅ SALDADO" if float(saldo or 0) <= 0.1 else "🔴 PENDIENTE"
                
                nombre_tour = s.get('observacion') or tours_map.get(s['id_tour']) or v.get('tour_nombre') or "Tour Desconocido"
                
                key_g = f"{s['id_venta']}-{s['n_linea']}"
                nombre_guia = guias_map.get(key_g, "Por Asignar")
                nombre_endoso = proveedor_endoso_map.get(key_g, "---")
                es_endoso = s.get('es_endoso', False)
                tipo_venta = '🏢 B2B' if v.get('id_agencia_aliada') else '👤 B2C'

                resultado.append({
                    'ID Venta': s['id_venta'],
                    'N Linea': s['n_linea'],
                    'Fecha': s['fecha_servicio'],
                    'fecha_servicio': s['fecha_servicio'], # Para analítica
                    'Hora': s.get('hora_inicio', '08:00 AM'), # Updated to use s.get
                    'Servicio': nombre_tour,
                    'observacion': nombre_tour, # Para analítica
                    'Endoso?': es_endoso,
                    'Pax': s.get('cantidad', 1),
                    'cantidad': s.get('cantidad', 1), # Para analítica
                    'Cliente': nombre_cliente,
                    'Guía': nombre_guia,
                    'Agencia Endoso': nombre_endoso,
                    'Proveedor': nombre_endoso if es_endoso else nombre_guia,
                    'Detalle Proveedores': detalles_proveedores_map.get(key_g, []),
                    'Estado Pago': estado_pago,
                    'Tipo': tipo_venta,
                    'Día Itin.': s.get('id_itinerario_dia_index', 1),
                    'ID Itinerario': v.get('id_itinerario_digital'),
                    'URL Cloud': v.get('url_itinerario') or ""
                })
            return resultado
        except Exception as e:
            print(f"Error en Rango de Fechas: {e}")
            return []

    def get_servicios_por_fecha(self, fecha_filtro: date):
        try:
            f_iso_start = fecha_filtro.isoformat()
            f_iso_end = (fecha_filtro + timedelta(days=1)).isoformat()
            
            res_servicios = (
                self.client.table('venta_tour')
                .select('*')
                .gte('fecha_servicio', f_iso_start)
                .lt('fecha_servicio', f_iso_end)
                .execute()
            )
            print(f"DEBUG Today: Found {len(res_servicios.data or [])} rows for {f_iso_start}")
            
            if not res_servicios.data:
                return []
                
            servicios_data = res_servicios.data
            ids_ventas = list(set([s['id_venta'] for s in servicios_data]))
            
            ventas_map = {}
            if ids_ventas:
                res_v = self.client.table('venta').select('*').in_('id_venta', ids_ventas).execute()
                for v in res_v.data:
                    ventas_map[v['id_venta']] = v
                    
            ids_clientes = list(set([v['id_cliente'] for v in ventas_map.values() if v.get('id_cliente')]))
            clientes_map = {}
            if ids_clientes:
                res_c = self.client.table('cliente').select('id_cliente, nombre').in_('id_cliente', ids_clientes).execute()
                for c in res_c.data:
                    clientes_map[c['id_cliente']] = c['nombre']

            resultado = []
            for s in servicios_data:
                try:
                    v = ventas_map.get(s['id_venta'], {})
                    id_cliente = v.get('id_cliente')
                    nombre_cliente = clientes_map.get(id_cliente, "Desconocido")
                    
                    nombre_tour = s.get('observacion') or v.get('tour_nombre') or "Tour Desconocido"
                    
                    es_endoso = s.get('es_endoso', False)
                    tipo_venta = '🏢 B2B' if v.get('id_agencia_aliada') else '👤 B2C'

                    resultado.append({
                        'ID Servicio': f"{s['id_venta']}-{s['n_linea']}", 
                        'Hora': s.get('hora_inicio', "08:00 AM") or "08:00 AM",
                        'Log.': "🟢",
                        'Servicio': nombre_tour,
                        'Endoso?': es_endoso,
                        'Pax': s.get('cantidad', 1),
                        'Cliente': nombre_cliente,
                        'Guía': "Ver Detalle",
                        'Agencia Endoso': "---",
                        'Proveedor': "Ver Detalle",
                        'Detalle Proveedores': [],
                        'Estado Pago': "✅", # Simplificado para evitar fallos por ahora
                        'Tipo': tipo_venta,
                        'ID Venta': s['id_venta'],
                        'N Linea': s['n_linea'],
                        'Día Itin.': s.get('id_itinerario_dia_index', 1),
                        'ID Itinerario': v.get('id_itinerario_digital'),
                        'URL Cloud': v.get('url_itinerario') or ""
                    })
                except Exception as inner_e:
                    print(f"DEBUG: Error processing service row: {inner_e}")
                    
            return resultado
        except Exception as e:
            print(f"Error en Tablero Diario: {e}")
            return []

    def save_liquidation(self, items: list) -> tuple[bool, str]:
        """
        Persiste los datos del simulador/liquidación en la tabla venta_servicio_proveedor.
        Realiza upsert basado en el UNIQUE constraint (id_venta, n_linea, tipo_servicio).
        """
        try:
            if not items:
                return False, "No hay datos para guardar."

            clean_items = []
            for it in items:
                if not it.get('id_venta') or it.get('n_linea') is None:
                    continue
                
                clean_items.append({
                    "id_venta": it['id_venta'],
                    "n_linea": it['n_linea'],
                    "id_proveedor": it.get('id_proveedor'),
                    "tipo_servicio": it.get('TIPO_SERVICIO', 'ENDOSE'),
                    "costo_unitario": float(it.get('TOTAL') or 0.0),
                    "moneda": it.get('MONEDA', 'USD')
                })

            if clean_items:
                self.client.table('venta_servicio_proveedor').upsert(
                    clean_items,
                    on_conflict='id_venta, n_linea, tipo_servicio'
                ).execute()
                return True, "Liquidación guardada exitosamente."
            return False, "No se encontraron filas válidas para procesar."
        except Exception as e:
            print(f"Error en save_liquidation: {e}")
            return False, f"Error al guardar: {str(e)}"

    def get_liquidaciones_venta(self, id_venta: int) -> list:
        """Obtiene el desglose detallado de costos por servicio de una venta."""
        try:
            res = (
                self.client.table('venta_servicio_proveedor')
                .select('*, proveedor(nombre_comercial, servicios_ofrecidos)')
                .eq('id_venta', id_venta)
                .execute()
            )
            return res.data or []
        except Exception as e:
            print(f"Error en get_liquidaciones_venta: {e}")
            return []

    def get_data_for_analytics(self):
        try:
            # Traer los servicios de los últimos meses para el dashboard
            res = self.client.table('venta_tour').select('*').execute()
            data = res.data or []
            return data
        except Exception as e:
            print(f"Error dashboard operaciones: {e}")
            return []