# models/venta_model.py

from .base_model import BaseModel
from datetime import datetime, timedelta, date
from supabase import Client
from typing import Dict, Any, Optional

class VentaModel(BaseModel):
    """Modelo para la gestión de Ventas (Conversiones de Leads)."""

    def __init__(self, supabase_client: Client): 
        # Sincronizado con esquema SQL: tabla 'venta', PK 'id_venta'
        super().__init__('venta', supabase_client, primary_key='id_venta') 

    # --- MÉTODOS DE BÚSQUEDA DE IDs (HELPERS) ---
    def get_vendedor_id_by_query(self, query: str) -> Optional[int]:
        """Busca el ID del vendedor por su nombre o email."""
        if not query: return None
        try:
            # 1. Intentar por Email (exacto)
            res_e = self.client.table('vendedor').select('id_vendedor').eq('email', query).execute()
            if res_e.data:
                return res_e.data[0]['id_vendedor']
            
            # 2. Intentar por Nombre (parcial)
            res_n = self.client.table('vendedor').select('id_vendedor').ilike('nombre', f"%{query}%").limit(1).execute()
            if res_n.data:
                return res_n.data[0]['id_vendedor']
        except Exception as e:
            print(f"Error buscando vendedor {query}: {e}")
        return None

    def get_tour_id_by_name(self, nombre: str) -> Optional[int]:
        """Busca el ID del tour por su nombre exacto o parcial."""
        if not nombre: return None
        try:
            res = self.client.table('tour').select('id_tour').ilike('nombre', f"%{nombre}%").limit(1).execute()
            if res.data:
                return res.data[0]['id_tour']
        except Exception as e:
            print(f"Error buscando tour {nombre}: {e}")
        return None

    def get_or_create_cliente(self, nombre: str, celular: str, origen: str, id_lead: Optional[int] = None, tipo_cliente: str = "B2C", id_vendedor: Optional[int] = None) -> Optional[int]:
        """Busca un cliente por nombre (simplicidad), si no existe lo crea. Crea el lead asociado si hay celular."""
        if not nombre: 
            raise Exception("El nombre del cliente es obligatorio")
        
        # 1. Buscar existente
        res = self.client.table('cliente').select('id_cliente').eq('nombre', nombre).limit(1).execute()
        if res.data:
            return res.data[0]['id_cliente']
            
        # 1.5 Crear Lead si es necesario para mantener el número de celular
        if not id_lead and celular:
            from .lead_model import LeadModel
            lead_mod = LeadModel(self.client)
            nuevo_lead = lead_mod.create_lead(
                telefono=celular,
                origen=origen or "B2B",
                vendedor=id_vendedor,
                nombre_pasajero=nombre
            )
            if nuevo_lead:
                id_lead = nuevo_lead
        
        # 2. Crear nuevo (esto lanzará excepción si falla)
        nuevo_cliente = {
            "nombre": nombre,
            "tipo_cliente": tipo_cliente,
            "id_lead": id_lead
        }
        res_insert = self.client.table('cliente').insert(nuevo_cliente).execute()
        if res_insert.data and len(res_insert.data) > 0:
            return res_insert.data[0].get('id_cliente')
        else:
            raise Exception("Supabase no devolvió el ID del cliente creado")

    def _clean_float(self, value) -> float:
        """Convierte un valor (str o num) a float de forma robusta, manejando comas de miles."""
        if value is None: return 0.0
        if isinstance(value, (int, float)): return float(value)
        try:
            # Eliminar comas de miles y espacios, luego convertir
            clean_val = str(value).replace(',', '').replace(' ', '').strip()
            return float(clean_val)
        except:
            return 0.0

    # --- MÉTODO PRINCIPAL DE CREACIÓN DE VENTA ---
    def create_venta(self, venta_data: Dict[str, Any]) -> int:
        """
        Orquesta la creación de la Venta Relacional según esquema SQL:
        """
        
        # 1. Determinar Tipo de Cliente (B2C o B2B)
        id_age = venta_data.get('id_agencia_aliada')
        tipo_final = "B2B" if id_age else "B2C"

        id_vendedor = self.get_vendedor_id_by_query(venta_data.get('vendedor'))
        
        if not id_vendedor:
            # Fallback: Usar el primer vendedor si no se encuentra ninguno por nombre
            res_fb = self.client.table('vendedor').select('id_vendedor').limit(1).execute()
            if res_fb.data:
                id_vendedor = res_fb.data[0]['id_vendedor']
            else:
                raise Exception("No hay vendedores en la base de datos.")

        # 2. Obtener IDs Relacionales
        id_cliente = self.get_or_create_cliente(
            venta_data.get('nombre_cliente'), 
            venta_data.get('telefono_cliente'), 
            venta_data.get('origen'),
            id_lead=venta_data.get('id_lead'),
            tipo_cliente=tipo_final,
            id_vendedor=id_vendedor
        )
        
        tour_raw = venta_data.get('tour', '')
        id_paquete = None
        id_tour_catalogo = None
        
        if str(tour_raw).startswith("P-"):
            try: id_paquete = int(tour_raw.replace("P-", ""))
            except: pass
        elif str(tour_raw).startswith("T-"):
            try: id_tour_catalogo = int(tour_raw.replace("T-", ""))
            except: pass
            
        if not id_tour_catalogo and not id_paquete:
            id_tour_catalogo = self.get_tour_id_by_name(tour_raw)

        # 2. Preparar Payload para tabla 'venta' (Columnas del esquema SQL)
        id_itin = venta_data.get("id_itinerario_digital")
        num_pax_final = 1
        
        # Intentar extraer info extra del itinerario si existe
        if id_itin:
            try:
                res_it = self.client.table('itinerario_digital').select('datos_render').eq('id_itinerario_digital', id_itin).single().execute()
                if res_it.data:
                    render = res_it.data.get('datos_render', {})
                    # Extraer Pax de raíz o control interno
                    num_pax_temp = render.get('cantidad_pax') or render.get('pax_count') or render.get('num_pax') or 0
                    if not num_pax_temp:
                        ci = render.get('control_interno', {})
                        num_pax_temp = ci.get('total_pasajeros') or ci.get('total_pax') or 1
                    num_pax_final = int(num_pax_temp)
            except: pass

        datos_venta_sql = {
            "id_cliente": id_cliente,
            "id_vendedor": id_vendedor,
            "fecha_venta": venta_data.get("fecha_registro", datetime.now().strftime("%Y-%m-%d")),
            "fecha_inicio": venta_data.get("fecha_inicio"),
            "fecha_fin": venta_data.get("fecha_fin"),
            "canal_venta": venta_data.get("origen", "DIRECTO"),
            "precio_total_cierre": venta_data.get("monto_total"),
            "moneda": venta_data.get("moneda", "USD"),
            "tipo_cambio": venta_data.get("tipo_cambio"), # "Foto" del dólar
            "estado_pago": "PENDIENTE", # Será actualizado por el trigger de pagos
            "estado_venta": "CONFIRMADO",
            "id_paquete": id_paquete,
            "tour_nombre": tour_raw,
            "num_pasajeros": num_pax_final,
            "id_agencia_aliada": id_age,
            "id_itinerario_digital": id_itin,
            "nro_vuelo_internacional": venta_data.get("nro_vuelo_internacional"),
            "correo_cliente": venta_data.get("correo_cliente"),
            "nombre_contacto_emergencia": venta_data.get("nombre_contacto_emergencia"),
            "telefono_contacto_emergencia": venta_data.get("telefono_contacto_emergencia")
        }

        # 3. Insertar Venta
        nuevo_id_venta = self.save(datos_venta_sql)
        
        if not nuevo_id_venta:
            raise Exception("No se pudo insertar en la tabla 'venta'.")
        
        # 4. Registrar Desglose de Ingresos (Opción 3)
        # Intentar obtener items del controller o extraerlos del itinerario si no vienen
        items_ingreso = venta_data.get("items_ingreso", [])
        if not items_ingreso and id_itin:
            # Si no vienen del UI, intentamos rescatarlos del itinerario digital
            try:
                res_it = self.client.table('itinerario_digital').select('datos_render').eq('id_itinerario_digital', id_itin).single().execute()
                if res_it.data:
                    render = res_it.data.get('datos_render', {})
                    if isinstance(render, str):
                        import json
                        try: render = json.loads(render)
                        except: render = {}
                    
                    # PRIORIDAD: Usar el TC de la VENTA actual si está disponible, 
                    # si no, usar el tc_itin como fallback.
                    tc_conversion = venta_data.get('tipo_cambio') or tc_itin
                    try: tc_conversion = float(tc_conversion)
                    except: tc_conversion = tc_itin

                    # 1. PRIORIDAD MÁXIMA: 'detalle_ingresos'
                    det_ing = render.get('detalle_ingresos', [])
                    if isinstance(det_ing, list):
                        for d in det_ing:
                            t_raw = str(d.get('tipo', '')).upper()
                            t = t_raw
                            if t in ['EXT', 'INT', 'EXTRANJERO']: t = 'EXTRANJERO'
                            elif t in ['NAC', 'NACIONAL']: t = 'NACIONAL'
                            elif t in ['CAN']: t = 'CAN'

                            c = int(self._clean_float(d.get('cantidad', 0)))
                            p_raw = self._clean_float(d.get('precio_unitario', 0))
                            
                            # Conversión USD -> PEN para el backend usando el TC de la Venta
                            p_final = p_raw
                            info_xtra = ""
                            if t in ['EXTRANJERO', 'CAN']:
                                p_final = p_raw * tc_conversion
                                info_xtra = f" (${p_raw}x{tc_conversion})"

                            lbl = d.get('descripcion') or f"Pax {t.capitalize()}"
                            if c > 0:
                                items_ingreso.append({
                                    "descripcion": f"{lbl}{info_xtra}", 
                                    "cantidad": c, 
                                    "precio_unitario": p_final
                                })
                                tipos_vistos.add(t)

                    # 2. SEGUNDA PRIORIDAD: 'control_interno'
                    ci = render.get('control_interno', {})
                    desglose = ci.get('desglose_pasajeros', {})
                    if isinstance(desglose, dict):
                        for k, v in desglose.items():
                            t_slug = k.upper()
                            if t_slug not in tipos_vistos:
                                c_total = 0
                                if isinstance(v, dict): c_total = sum(int(x or 0) for x in v.values())
                                elif isinstance(v, (int, float)): c_total = int(v)
                                
                                if c_total > 0:
                                    p_u_raw = 0.0
                                    if t_slug == 'NACIONAL': p_u_raw = render.get('precio_nacional') or render.get('p_nac')
                                    elif t_slug == 'EXTRANJERO': p_u_raw = render.get('precio_extranjero') or render.get('p_ext')
                                    elif t_slug == 'CAN': p_u_raw = render.get('precio_can') or render.get('p_can')
                                    
                                    if not p_u_raw:
                                        sub_p = render.get('precios', {})
                                        p_obj = sub_p.get(k.lower()) or sub_p.get(t_slug)
                                        if isinstance(p_obj, dict): p_u_raw = p_obj.get('total') or p_obj.get('monto')
                                        else: p_u_raw = p_obj
                                    
                                    p_u_raw = self._clean_float(p_u_raw)
                                    
                                    p_u_final = p_u_raw
                                    inf_e = ""
                                    if t_slug in ['EXTRANJERO', 'CAN']:
                                        p_u_final = p_u_raw * tc_conversion
                                        inf_e = f" (${p_u_raw}x{tc_conversion})"

                                    items_ingreso.append({
                                        "descripcion": f"Pax {k.capitalize()}{inf_e}", 
                                        "cantidad": c_total, 
                                        "precio_unitario": p_u_final
                                    })
                                    tipos_vistos.add(t_slug)

                    # 3. FALLBACK LEGACY
                    fallbacks = [
                        ('NACIONAL', ['num_pax_nac', 'pax_nac'], ['precio_nacional', 'p_nac']),
                        ('EXTRANJERO', ['num_pax_ext', 'pax_ext'], ['precio_extranjero', 'p_ext']),
                        ('CAN', ['num_pax_can', 'pax_can'], ['precio_can', 'p_can'])
                    ]
                    for t_code, c_keys, p_keys in fallbacks:
                        if t_code not in tipos_vistos:
                            c_f = 0
                            for ck in c_keys:
                                try: c_f = int(render.get(ck, 0) or 0)
                                except: c_f = 0
                                if c_f > 0: break
                            if c_f > 0:
                                p_f_total_raw = 0.0
                                for pk in p_keys:
                                    p_f_total_raw = self._clean_float(render.get(pk, 0))
                                    if p_f_total_raw > 0: break
                                
                                # Calcular precio unitario si es que lo que viene es un total
                                p_f_unit_raw = p_f_total_raw / c_f
                                
                                p_f_final = p_f_unit_raw
                                inf_f = ""
                                if t_code in ['EXTRANJERO', 'CAN']:
                                    p_f_final = p_f_unit_raw * tc_conversion
                                    inf_f = f" (${p_f_unit_raw:.2f}x{tc_conversion})"

                                items_ingreso.append({
                                    "descripcion": f"Pax {t_code.capitalize()}{inf_f}", 
                                    "cantidad": c_f, 
                                    "precio_unitario": p_f_final
                                })
            except Exception as e:
                print(f"Error extrayendo items del itinerario (Backend): {e}")

        # Guardar items en la tabla nueva (con corrección de redondeo)
        if items_ingreso:
            # Calcular diferencia de redondeo para equilibrar con el total de la venta
            total_items = sum(it.get('cantidad', 1) * it.get('precio_unitario', 0) for it in items_ingreso)
            monto_total_venta = self._clean_float(venta_data.get("monto_total", 0))
            dif_redondeo = monto_total_venta - total_items
            
            # Si la diferencia es pequeña (ajuste de céntimos), la aplicamos al último item
            if 0 < abs(dif_redondeo) < 1.0 and items_ingreso:
                # Ajustar el precio unitario del último item para absorber la diferencia
                items_ingreso[-1]['precio_unitario'] += dif_redondeo / items_ingreso[-1].get('cantidad', 1)

            for item in items_ingreso:
                item["id_venta"] = nuevo_id_venta
                self.client.table('venta_item_ingreso').insert(item).execute()
        else:
            # Fallback: Si no hay items, crear uno genérico por el total
            self.client.table('venta_item_ingreso').insert({
                "id_venta": nuevo_id_venta,
                "descripcion": f"Servicio: {tour_raw}",
                "cantidad": num_pax_final,
                "precio_unitario": float(venta_data.get("monto_total", 0)) / (num_pax_final if num_pax_final > 0 else 1)
            }).execute()

        # 5. Registrar Pago Inicial (Tabla 'pago')
        if venta_data.get("monto_depositado", 0) >= 0:
            try:
                # Si el monto es 0, igual creamos un registro "PENDIENTE" o simplemente saltamos
                # En este flujo, si hay monto_depositado (adelanto) lo registramos
                monto_dep = venta_data.get("monto_depositado", 0)
                if monto_dep > 0:
                    # Normalizar tipo de comprobante para el CHECK constraint del SQL
                    tipo_c_raw = str(venta_data.get("tipo_comprobante", "RECIBO")).upper()
                    if "BOLETA" in tipo_c_raw: tipo_c_db = "BOLETA"
                    elif "FACTURA" in tipo_c_raw: tipo_c_db = "FACTURA"
                    elif "SIMPLE" in tipo_c_raw: tipo_c_db = "RECIBO SIMPLE"
                    else: tipo_c_db = "RECIBO"

                    pago_data = {
                        "id_venta": nuevo_id_venta,
                        "fecha_pago": datetime.now().strftime("%Y-%m-%d"),
                        "monto_pagado": self._clean_float(monto_dep), # Asegurar float limpio
                        "moneda": venta_data.get("moneda", "USD"),
                        "metodo_pago": venta_data.get("metodo_pago", "OTRO"),
                        "tipo_pago": "ADELANTO" if monto_dep < venta_data.get("monto_total", 0) else "TOTAL",
                        "tipo_comprobante": tipo_c_db,
                        "tasa_cambio": 1.0, # Al crear la venta, el adelanto es en la misma moneda
                        "monto_moneda_venta": self._clean_float(monto_dep)
                    }
                    self.client.table('pago').insert(pago_data).execute()
            except Exception as e:
                # Ahora lanzamos el error para que el controlador lo capture y lo muestre al usuario
                raise Exception(f"Error registrando el pago inicial (Adelanto): {e}")

        # 5. Registrar Detalles venta_tour (Expansión de Días para Operaciones)
        try:
            val_inicio = venta_data.get("fecha_inicio")
            val_fin = venta_data.get("fecha_fin")
            
            # Robustez: Convertir a objeto date si son strings o usar directamente si ya son date objects
            if isinstance(val_inicio, str):
                f_inicio = datetime.strptime(val_inicio, "%Y-%m-%d").date()
            else:
                f_inicio = val_inicio if val_inicio else date.today()
                
            if isinstance(val_fin, str):
                f_fin = datetime.strptime(val_fin, "%Y-%m-%d").date()
            else:
                f_fin = val_fin if val_fin else f_inicio
                
            num_dias = (f_fin - f_inicio).days + 1
            if num_dias < 1: num_dias = 1
            
            # Intentar obtener detalles del itinerario digital si existe
            itin_detalles = []
            id_itin = venta_data.get("id_itinerario_digital")
            if id_itin:
                res_itin = self.client.table('itinerario_digital').select('datos_render').eq('id_itinerario_digital', id_itin).single().execute()
                if res_itin.data:
                    render = res_itin.data.get('datos_render', {})
                    itin_detalles = render.get('itinerario_detalles', []) or render.get('itinerario_detales', []) or render.get('days', [])

            for i in range(num_dias):
                f_servicio = f_inicio + timedelta(days=i)
                nombre_servicio_dia = venta_data.get("tour") # Default
                
                # Inteligencia extraída del JSON de Itinerario Digital
                if i < len(itin_detalles):
                    dia_info = itin_detalles[i]
                    # 1. Extraer Título (Servicio)
                    nombre_servicio_dia = dia_info.get('titulo') or dia_info.get('nombre') or dia_info.get('title') or nombre_servicio_dia
                    
                    # 2. Extraer Fecha (si el JSON la trae y es válida, priorizarla)
                    f_raw = dia_info.get('fecha')
                    if f_raw and isinstance(f_raw, str):
                        try:
                            # Limpiar espacios: "20 / 02 / 2026" -> "20/02/2026"
                            f_clean = f_raw.replace(" ", "")
                            f_parsed = datetime.strptime(f_clean, "%d/%m/%Y").date()
                            f_servicio = f_parsed
                        except:
                            pass # Fallback al cálculo secuencial
                
                # Calcular precio proporcional por día para evitar ceros en reportes
                monto_total_v = self._clean_float(venta_data.get("monto_total", 0))
                precio_dia = monto_total_v / num_dias if num_dias > 0 else monto_total_v

                detalle_tour = {
                    "id_venta": nuevo_id_venta,
                    "n_linea": i + 1,
                    "id_tour": id_tour_catalogo if i == 0 else None,
                    "fecha_servicio": f_servicio.isoformat(),
                    "precio_applied": precio_dia,
                    "precio_vendedor": precio_dia,
                    "costo_applied": 0,
                    "cantidad": num_pax_final,
                    "observacion": nombre_servicio_dia,
                    "id_itinerario_dia_index": i + 1
                }
                self.client.table('venta_tour').insert(detalle_tour).execute()
        except Exception as e:
            print(f"Advertencia: Error expandiendo detalle tour: {e}")

        return nuevo_id_venta
