# controllers/operaciones_controller.py
from models.operaciones_model import PasajeroModel
from models.venta_model import VentaModel
from datetime import date, timedelta, datetime
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
                for item in res.data:
                    try:
                        f_raw = item['fecha_servicio']
                        f_date = pd.to_datetime(f_raw).date()
                        fechas_activas.add(f_date)
                    except:
                        pass
            return list(fechas_activas)
        except Exception as e:
            print(f"Error en Calendario: {e}")
            return []

    def get_servicios_rango_fechas(self, start_date: date, end_date: date):
        """Obtiene servicios para un rango de fechas con nombres de clientes y ventas."""
        try:
            res_servicios = (
                self.client.table('venta_tour')
                .select('*')
                .gte('fecha_servicio', start_date.isoformat())
                .lt('fecha_servicio', (end_date + timedelta(days=1)).isoformat())
                .order('fecha_servicio')
                .execute()
            )
            
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
                res_c = self.client.table('cliente').select('id_cliente, nombre, lead(numero_celular)').in_('id_cliente', ids_clientes).execute()
                for c in res_c.data:
                    # PostgREST devuelve el lead como un objeto o lista
                    lead_data = c.get('lead')
                    num_tel = "---"
                    if isinstance(lead_data, dict):
                        num_tel = lead_data.get('numero_celular', '---')
                    elif isinstance(lead_data, list) and len(lead_data) > 0:
                        num_tel = lead_data[0].get('numero_celular', '---')
                        
                    clientes_map[c['id_cliente']] = {
                        "nombre": c['nombre'],
                        "telefono": num_tel
                    }

            pagos_map = {} 
            if ids_ventas:
                res_p = self.client.table('pago').select('id_venta, monto_pagado').in_('id_venta', ids_ventas).execute()
                for p in res_p.data:
                    vid = p['id_venta']
                    pagos_map[vid] = pagos_map.get(vid, 0) + (p['monto_pagado'] or 0)

            guias_map = {}
            proveedor_endoso_map = {}
            detalles_proveedores_map = {}
            if ids_ventas:
                res_g = (
                    self.client.table('venta_servicio_proveedor')
                    .select('id, id_venta, n_linea, tipo_servicio, terminado, proveedor(nombre_comercial)')
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
                        "id": g.get('id'),
                        "tipo": g.get('tipo_servicio'),
                        "nombre": prov_nom,
                        "terminado": g.get('terminado', False)
                    })
            
            resultado = []
            for s in servicios_data:
                v = ventas_map.get(s['id_venta'], {})
                # NUEVO: Ignorar servicios de ventas ya archivadas/finalizadas
                if v.get('estado_venta') == 'FINALIZADO':
                    continue
                
                id_cliente = v.get('id_cliente')
                c_info = clientes_map.get(id_cliente, {"nombre": "Desconocido", "telefono": "---"})
                nombre_cliente = c_info['nombre']
                telefono_cliente = c_info['telefono']
                
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
                    'fecha_servicio': s['fecha_servicio'],
                    'Hora': s.get('hora_inicio', '08:00 AM'), 
                    'Servicio': nombre_tour,
                    'observacion': nombre_tour,
                    'Endoso?': es_endoso,
                    'Pax': s.get('cantidad', 1),
                    'cantidad': s.get('cantidad', 1),
                    'Cliente': nombre_cliente,
                    'Celular': telefono_cliente,
                    'Guía': nombre_guia,
                    'Agencia Endoso': nombre_endoso,
                    'Proveedor': nombre_endoso if es_endoso else nombre_guia,
                    'Detalle Proveedores': detalles_proveedores_map.get(key_g, []),
                    'Estado Pago': estado_pago,
                    'Tipo': tipo_venta,
                    'Día Itin.': s.get('id_itinerario_dia_index', 1),
                    'ID Itinerario': v.get('id_itinerario_digital'),
                    'URL Cloud': v.get('url_itinerario') or "",
                    'num_pasajeros': v.get('num_pasajeros', 1),
                    'ninos': v.get('ninos', 0)
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
                    # NUEVO: Ignorar servicios de ventas ya archivadas/finalizadas
                    if v.get('estado_venta') == 'FINALIZADO':
                        continue
                        
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
                        'Estado Pago': "✅",
                        'Tipo': tipo_venta,
                        'ID Venta': s['id_venta'],
                        'N Linea': s['n_linea'],
                        'Día Itin.': s.get('id_itinerario_dia_index', 1),
                        'ID Itinerario': v.get('id_itinerario_digital'),
                        'URL Cloud': v.get('url_itinerario') or ""
                    })
                except:
                    pass
            return resultado
        except Exception as e:
            print(f"Error en Tablero Diario: {e}")
            return []

    def get_data_for_analytics(self):
        try:
            res = self.client.table('venta_tour').select('*').execute()
            return res.data or []
        except Exception as e:
            print(f"Error dashboard operaciones: {e}")
            return []

    def vincular_endoses_masivos(self, id_venta: str, df_liq: pd.DataFrame, tc_manual: float = 3.80):
        """
        Vincula masivamente costos y proveedores a una venta con Mapeo Inteligente.
        Distribuye los servicios del Excel entre los servicios disponibles de la venta.
        """
        resultados = {"exitos": 0, "errores": []}
        
        try:
            # 0. Obtener moneda de la venta para normalización
            res_v = self.client.table('venta').select('moneda').eq('id_venta', id_venta).single().execute()
            moneda_v = (res_v.data or {}).get('moneda', 'USD')

            # 1. Cargar proveedores activos para mapeo de nombres
            res_p = self.client.table('proveedor').select('id_proveedor, nombre_comercial').eq('activo', True).execute()
            mapa_prov = {str(p['nombre_comercial']).strip().upper(): p['id_proveedor'] for p in res_p.data}
        except Exception as e:
            return {"exitos": 0, "errores": [f"Error al cargar proveedores: {str(e)}"]}

        try:
            # 2. Obtener todos los servicios de la venta con su descripción para el Smart Match
            res_s = self.client.table('venta_tour').select('n_linea, id_itinerario_dia_index, observacion').eq('id_venta', id_venta).execute()
            
            # Agrupar servicios por día
            servicios_por_dia = {}
            for s in res_s.data:
                dia = s.get('id_itinerario_dia_index')
                if dia:
                    if dia not in servicios_por_dia: servicios_por_dia[dia] = []
                    servicios_por_dia[dia].append(s)
            
            if not servicios_por_dia:
                return {"exitos": 0, "errores": ["No se encontró itinerario sincronizado para esta venta. Sincronice primero."]}
                
        except Exception as e:
            return {"exitos": 0, "errores": [f"Error al obtener servicios de la venta: {str(e)}"]}

        # Diccionario para rastrear qué (n_linea, tipo) ya hemos usado en esta carga
        # Esto evita que dos filas de 'TICKET' en el Excel se amontonen en el mismo n_linea si hay otros disponibles
        usados_en_carga = set()

        # Keywords para Smart Match (Mapeo por palabras clave)
        keywords_map = {
            "INCARAIL": ["TREN", "INCA", "TRAIN"],
            "PERURAIL": ["TREN", "PERU", "TRAIN"],
            "CONSETTUR": ["BUS", "SUBIDA", "CONSETTUR", "MAPI"],
            "FENIX": ["HOTEL", "ALOJAMIENTO", "FENIX", "FENIX MACHUPICCHU"],
            "RESTAURANTE": ["ALMUERZO", "CENA", "BUFFET", "COMIDA"],
            "GUIA": ["GUIA", "GUIDE", "JOSE"],
            "COSITUC": ["CITY", "BOLETO", "TURISTICO", "GENERAL"],
            "SALINERAS": ["MARAS", "MORAY", "SALINERAS"]
        }

        # 3. Procesar filas del Excel
        for idx, row in df_liq.iterrows():
            try:
                # Limpieza de datos del Excel
                dia_excel = int(row.get('Dia', 0))
                prov_nombre_raw = str(row.get('Proveedor', '')).strip()
                prov_nombre_up = prov_nombre_raw.upper()
                tipo = str(row.get('Tipo de Servicio', 'ENDOSE')).strip().upper()
                costo_unit = float(row.get('Costo Unitario', 0)) if not pd.isna(row.get('Costo Unitario')) else 0
                pax = int(float(row.get('Pax', 1))) if not pd.isna(row.get('Pax')) else 1
                moneda = str(row.get('Moneda', 'USD')).strip().upper() if not pd.isna(row.get('Moneda')) else "USD"

                # Buscar ID del proveedor
                id_prov = mapa_prov.get(prov_nombre_up)
                if not id_prov:
                    resultados["errores"].append(f"Fila {idx+1}: Proveedor '{prov_nombre_raw}' no encontrado en el Directorio.")
                    continue

                servicios_dia = servicios_por_dia.get(dia_excel, [])
                if not servicios_dia:
                    resultados["errores"].append(f"Fila {idx+1}: El Día {dia_excel} no existe en el itinerario de esta venta.")
                    continue
                
                # --- LÓGICA DE SMART MATCH (Encontrar el servicio correcto) ---
                target_service = None
                
                # Intento 1: Coincidencia por palabras clave en la descripción
                for s in servicios_dia:
                    obs = str(s.get('observacion', '')).upper()
                    # Si el nombre del proveedor está en la descripción (ej: "TREN INCARAIL")
                    if prov_nombre_up in obs:
                        target_service = s
                        break
                    # O si alguna keyword del proveedor coincide
                    for p_key, kws in keywords_map.items():
                        if p_key in prov_nombre_up:
                            if any(kw in obs for kw in kws):
                                target_service = s
                                break
                    if target_service: break

                # Intento 2: Si no hubo match, buscar por "Tipo de Servicio" en la descripción
                if not target_service:
                    for s in servicios_dia:
                        if tipo in str(s.get('observacion', '')).upper():
                            target_service = s
                            break

                # Intento 3: Si aún no hay match, usar el primero disponible para ese día/tipo que no hayamos usado aún
                if not target_service:
                    for s in servicios_dia:
                        key_check = (s['n_linea'], tipo)
                        if key_check not in usados_en_carga:
                            target_service = s
                            break
                    # Fallback final: primer servicio del día
                    if not target_service:
                        target_service = servicios_dia[0]

                nl = target_service['n_linea']
                usados_en_carga.add((nl, tipo))

                # Extraer campos adicionales
                hora_excel = row.get('Hora')
                obs_excel = row.get('Observacion')
                guia_excel = row.get('Nombre del Guia')
                f_conf_excel = row.get('Fecha de Confirmacion')

                try:
                    data_ins = {
                        "id_venta": id_venta,
                        "n_linea": nl,
                        "id_proveedor": id_prov,
                        "tipo_servicio": tipo,
                        "costo_unitario": costo_unit,
                        "moneda": moneda,
                        "cantidad_pax": pax,
                        "tipo_cambio": tc_manual,
                        "hora_servicio": str(hora_excel).strip() if not pd.isna(hora_excel) else None,
                        "observacion": str(obs_excel).strip() if not pd.isna(obs_excel) else None,
                        "nombre_guia": str(guia_excel).strip() if not pd.isna(guia_excel) else None
                    }
                    
                    # Parsear Fecha de Confirmación
                    if not pd.isna(f_conf_excel) and str(f_conf_excel).strip():
                        try:
                            if isinstance(f_conf_excel, (datetime, pd.Timestamp)):
                                data_ins["fecha_confirmacion"] = f_conf_excel.strftime("%Y-%m-%d")
                            else:
                                f_str = str(f_conf_excel).strip()
                                for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"]:
                                    try:
                                        data_ins["fecha_confirmacion"] = datetime.strptime(f_str, fmt).strftime("%Y-%m-%d")
                                        break
                                    except: continue
                        except: pass

                    # --- LÓGICA DE GUARDADO INTELIGENTE (BYPASS UNIQUE CONSTRAINT) ---
                    # Para permitir múltiples "TICKET" en un mismo servicio, hacemos que el tipo sea único
                    # añadiendo el nombre del proveedor al tipo si es necesario.
                    tipo_unico = f"{tipo} ({prov_nombre_raw})"
                    
                    data_ins["tipo_servicio"] = tipo_unico

                    res_check = self.client.table('venta_servicio_proveedor') \
                        .select('id') \
                        .eq('id_venta', id_venta) \
                        .eq('n_linea', nl) \
                        .eq('tipo_servicio', tipo_unico) \
                        .execute()

                    if res_check.data:
                        id_reg = res_check.data[0]['id']
                        self.client.table('venta_servicio_proveedor').update(data_ins).eq('id', id_reg).execute()
                    else:
                        self.client.table('venta_servicio_proveedor').insert(data_ins).execute()
                    
                    # --- ACTUALIZACIÓN DE VENTA_TOUR (COSTO ACUMULADO) ---
                    res_tot = self.client.table('venta_servicio_proveedor') \
                        .select('costo_unitario, cantidad_pax, moneda') \
                        .eq('id_venta', id_venta) \
                        .eq('n_linea', nl) \
                        .execute()
                    
                    total_n_linea = 0
                    for c in (res_tot.data or []):
                        c_u = float(c.get('costo_unitario', 0) or 0)
                        c_p = float(c.get('cantidad_pax', 1) or 1)
                        c_m = c.get('moneda', 'USD')

                        # Normalizar a la moneda de la venta (moneda_v)
                        if c_m != moneda_v:
                            if c_m == 'USD' and moneda_v == 'PEN':
                                c_u = c_u * tc_manual
                            elif c_m == 'PEN' and moneda_v == 'USD':
                                c_u = c_u / tc_manual
                        
                        total_n_linea += (c_u * c_p)

                    update_data = {"costo_unitario": total_n_linea}
                    if "ENDOSE" in tipo_unico.upper():
                        update_data["es_endoso"] = True
                    
                    self.client.table('venta_tour').update(update_data).eq('id_venta', id_venta).eq('n_linea', nl).execute()
                    resultados["exitos"] += 1
                except Exception as e:
                    resultados["errores"].append(f"Fila {idx+1}: Error al guardar en DB: {str(e)}")
            except Exception as e:
                resultados["errores"].append(f"Fila {idx+1}: Error de formato o datos: {str(e)}")

        return resultados

    def borrar_endoses_venta(self, id_venta: str):
        """
        Borra todos los costos y asignaciones vinculados a una venta.
        """
        try:
            # 1. Borrar en venta_servicio_proveedor
            self.client.table('venta_servicio_proveedor').delete().eq('id_venta', id_venta).execute()

            # 2. Resetear en venta_tour
            self.client.table('venta_tour').update({
                "costo_unitario": 0,
                "es_endoso": False,
                "id_proveedor": None
            }).eq('id_venta', id_venta).execute()

            return True, "Costos y proveedores reseteados exitosamente."
        except Exception as e:
            return False, f"Error al resetear costos: {str(e)}"

    def vincular_pasajeros_masivos(self, id_venta: str, df_pax: pd.DataFrame):
        """
        Registra masivamente pasajeros a una venta desde un DataFrame.
        """
        resultados = {"exitos": 0, "errores": []}
        
        for idx, row in df_pax.iterrows():
            try:
                nombre = str(row.get('Nombre', row.get('Nombre Completo', ''))).strip()
                apellidos = str(row.get('Apellidos', '')).strip()
                nombre_completo = f"{nombre} {apellidos}".strip() if apellidos else nombre
                if not nombre_completo:
                    resultados["errores"].append(f"Fila {idx+1}: Nombre vacío.")
                    continue
                
                doc = str(row.get('Documento', row.get('PASAPORTE', ''))).strip()
                tipo_doc = str(row.get('Tipo Doc', 'PASAPORTE')).strip().upper()
                nac = str(row.get('Nacionalidad', row.get('NACIONALIDAD', ''))).strip()
                f_nac = row.get('Fecha Nacimiento', row.get('FECHA NAC.', ''))
                f_cad = row.get('Fecha Caducidad', row.get('CADUCIDAD', ''))
                edad = row.get('Edad', None)
                genero = str(row.get('Genero', row.get('SEXO', ''))).strip()
                cuidados = str(row.get('Cuidados', row.get('DIETA', ''))).strip()
                
                # Nuevos campos logísticos
                habitacion = str(row.get('Tipo Habitacion', row.get('Habitación', row.get('TIPO DE ACOMODACIÓN', '')))).strip()

                # Lógica robusta para 'Es Principal'
                es_p_raw = str(row.get('Es Principal', '')).strip().upper()
                es_p = es_p_raw in ['SI', 'SÍ', 'TRUE', '1', 'VERDADERO']

                if tipo_doc not in ['DNI', 'PASAPORTE', 'CARNET_EXTRANJERIA', 'DIE']:
                    tipo_doc = 'PASAPORTE'

                data_ins = {
                    "id_venta": id_venta,
                    "nombre_completo": nombre_completo,
                    "numero_documento": doc if doc else None,
                    "tipo_documento": tipo_doc,
                    "nacionalidad": nac if nac else None,
                    "fecha_nacimiento": str(f_nac) if pd.notnull(f_nac) else None,
                    "fecha_caducidad_doc": str(f_cad) if pd.notnull(f_cad) else None,
                    "edad": int(edad) if pd.notnull(edad) else None,
                    "genero": genero if genero else None,
                    "cuidados_especiales": cuidados if cuidados else None,
                    "acomodacion": habitacion if habitacion else None,
                    "es_principal": es_p
                }
                
                self.client.table('pasajero').insert(data_ins).execute()
                resultados["exitos"] += 1
            except Exception as e:
                resultados["errores"].append(f"Fila {idx+1}: {e}")
        
        return resultados

    def finalizar_liquidacion_venta(self, id_venta: int):
        """
        Cierra definitivamente la venta:
        1. Marca la liquidación como FINALIZADA.
        2. Archiva la venta (estado_venta = FINALIZADO).
        3. Confirma todos los servicios operativos (terminado = True).
        """
        try:
            # 1. Actualizar estados de la Venta
            self.client.table('venta').update({
                "estado_liquidacion": "FINALIZADO",
                "estado_venta": "FINALIZADO"
            }).eq('id_venta', id_venta).execute()

            # 2. Confirmar todos los servicios operativos (Auto-Check OK)
            self.client.table('venta_servicio_proveedor').update({
                "terminado": True
            }).eq('id_venta', id_venta).execute()

            return True, "Expediente liquidado y archivado correctamente."
        except Exception as e:
            return False, f"Error al procesar el cierre del expediente: {e}"

    def get_liquidaciones_venta(self, id_venta: int):
        """
        Obtiene el detalle de costos (liquidación) vinculado a una venta,
        cruzado con los pagos operativos para método de pago y observaciones.
        """
        try:
            # 1. Obtener los costos/servicios
            res = (
                self.client.table('venta_servicio_proveedor')
                .select('*, proveedor(nombre_comercial)')
                .eq('id_venta', id_venta)
                .execute()
            )
            servicios = res.data or []
            
            # 2. Obtener TODOS los pagos operativos asociados a esta venta
            res_pagos = (
                self.client.table('pago_operativo')
                .select('n_linea, metodo_pago, observaciones, observaciones_contables')
                .eq('id_venta', id_venta)
                .order('created_at', desc=False)
                .execute()
            )
            
            # 3. Agrupar pagos por n_linea (puede haber múltiples pagos por línea)
            pagos_por_linea = {}
            for p in (res_pagos.data or []):
                nl = p.get('n_linea')
                if nl is not None:
                    if nl not in pagos_por_linea:
                        pagos_por_linea[nl] = []
                    pagos_por_linea[nl].append(p)
            
            # 4. Cruzar datos - cada servicio con sus pagos correspondientes
            for s in servicios:
                pagos_linea = pagos_por_linea.get(s['n_linea'], [])
                
                if pagos_linea:
                    # Método de pago: usar el del último pago registrado
                    s['metodo_pago'] = pagos_linea[-1].get('metodo_pago') or '---'
                    
                    # Función auxiliar para limpiar duplicados y subcadenas
                    def clean_obs(raw_list):
                        valid_obs = [str(o).strip() for o in raw_list if o and str(o).strip() and str(o).strip() != 'None']
                        if not valid_obs:
                            return '---'
                        
                        # Ordenar de mayor a menor longitud
                        valid_obs_sorted = sorted(valid_obs, key=len, reverse=True)
                        final_obs = []
                        
                        for obs in valid_obs_sorted:
                            # Solo agregamos si NO está contenido en uno más largo ya agregado
                            if not any(obs in existing for existing in final_obs):
                                final_obs.append(obs)
                                
                        # Invertir para mantener un orden más cronológico (los más largos suelen ser los últimos)
                        final_obs.reverse()
                        return ' | '.join(final_obs)

                    # Observaciones del pago: extraer únicas y limpiar subcadenas
                    raw_obs = [p.get('observaciones') for p in pagos_linea]
                    s['observaciones_pago'] = clean_obs(raw_obs)
                    
                    # Observaciones contables: extraer únicas y limpiar subcadenas
                    raw_obs_cont = [p.get('observaciones_contables') for p in pagos_linea]
                    s['observaciones_contables'] = clean_obs(raw_obs_cont)
                else:
                    # Sin pagos registrados para esta línea
                    s['metodo_pago'] = s.get('metodo_pago') or '---'
                    s['observaciones_pago'] = '---'
                    s['observaciones_contables'] = s.get('observaciones_contables') or '---'
                
            return servicios
        except Exception as e:
            print(f"Error cargando liquidaciones: {e}")
            return []

    def borrar_pasajeros_venta(self, id_venta: str):
        """Borra todos los pasajeros de una venta."""
        try:
            self.client.table('pasajero').delete().eq('id_venta', id_venta).execute()
        except Exception as e:
            print(f"Error borrando pasajeros: {e}")

    def obtener_data_hoja_servicio_maestra(self, id_venta):
        """
        Recopila toda la información de la operación para el Reporte Maestro.
        """
        # 1. Obtener Datos de la Venta básica
        res_v = self.client.table('venta').select('*, cliente(nombre, lead(numero_celular))').eq('id_venta', id_venta).single().execute()
        if not res_v.data:
            raise Exception("No se pudo recuperar la información de la venta.")
            
        v_raw = res_v.data
        cliente_nest = v_raw.get('cliente', {})
        lead_nest = cliente_nest.get('lead', {}) if isinstance(cliente_nest, dict) else {}
        
        v_data = {
            "id_venta": v_raw['id_venta'],
            "nombre_cliente": cliente_nest.get('nombre', 'Desconocido') if isinstance(cliente_nest, dict) else 'Desconocido',
            "telefono": lead_nest.get('numero_celular', '---') if isinstance(lead_nest, dict) else '---',
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
        res_p = self.client.table('pago').select('monto_pagado').eq('id_venta', id_venta).execute()
        v_data['monto_pagado'] = sum(float(p['monto_pagado'] or 0) for p in res_p.data)

        # 3. Obtener Itinerario Logístico (Con proveedores asignados)
        itinerario = self.get_servicios_rango_fechas(date(2000,1,1), date(2100,1,1))
        it_venta = [s for s in itinerario if s['ID Venta'] == id_venta]

        # 4. Obtener Pasajeros
        pasajeros = self.pasajero_model.get_by_venta_id(id_venta)

        # 5. Obtener Liquidación Detallada (Costos)
        liquidaciones = self.get_liquidaciones_venta(id_venta)

        # 6. Empaquetar
        return {
            "venta": v_data,
            "itinerario": it_venta,
            "pasajeros": pasajeros,
            "liquidaciones": liquidaciones
        }

    def actualizar_campos_liquidacion(self, id_registro: int, campos: dict):
        """
        Actualiza campos de un registro en venta_servicio_proveedor y sincroniza con venta_tour si es costo/pax.
        """
        try:
            # 1. Separar campos de pago vs campos de servicio
            campos_pago = {}
            if 'metodo_pago' in campos: campos_pago['metodo_pago'] = campos.pop('metodo_pago')
            if 'observaciones_contables' in campos: campos_pago['observaciones_contables'] = campos.pop('observaciones_contables')

            # 2. Actualizar venta_servicio_proveedor (Costo, Pax, Moneda, Terminados)
            if campos:
                res = self.client.table('venta_servicio_proveedor').update(campos).eq('id', id_registro).execute()
                
                # Sincronización de costo total en venta_tour
                if "costo_unitario" in campos or "cantidad_pax" in campos:
                    if res.data:
                        d = res.data[0]
                        c_u = float(d.get('costo_unitario', 0))
                        p = float(d.get('cantidad_pax', 1))
                        self.client.table('venta_tour').update({"costo_unitario": c_u * p})\
                            .eq('id_venta', d['id_venta']).eq('n_linea', d['n_linea']).execute()
            
            # 3. Actualizar o crear registro en pago_operativo si hay cambios en pago
            if campos_pago:
                # Obtener info del servicio para saber a qué n_linea e id_proveedor pertenece
                res_serv = self.client.table('venta_servicio_proveedor').select('id_venta, n_linea, id_proveedor, costo_unitario, cantidad_pax, moneda').eq('id', id_registro).single().execute()
                if res_serv.data:
                    s = res_serv.data
                    # Buscar si ya existe un pago para este servicio
                    res_p = self.client.table('pago_operativo').select('id_pago_op').eq('id_venta', s['id_venta']).eq('n_linea', s['n_linea']).execute()
                    
                    if res_p.data:
                        # Actualizar existente
                        id_pago = res_p.data[0]['id_pago_op']
                        self.client.table('pago_operativo').update(campos_pago).eq('id_pago_op', id_pago).execute()
                    else:
                        # Crear nuevo registro de pago (monto por defecto = costo total)
                        monto_total = float(s['costo_unitario'] or 0) * float(s['cantidad_pax'] or 1)
                        nuevo_pago = {
                            "id_venta": s['id_venta'],
                            "n_linea": s['n_linea'],
                            "id_proveedor": s['id_proveedor'],
                            "monto_pagado": monto_total,
                            "moneda": s['moneda'] or 'USD',
                            "monto_en_moneda_costo": monto_total,
                            "fecha_pago": date.today().isoformat(),
                            "metodo_pago": campos_pago.get('metodo_pago', 'TRANSFERENCIA'),
                            "observaciones_contables": campos_pago.get('observaciones_contables', '')
                        }
                        self.client.table('pago_operativo').insert(nuevo_pago).execute()
                        
            return True, "Cambios guardados."
        except Exception as e:
            return False, f"Error al guardar: {str(e)}"

    def get_alertas_operativas(self):
        """
        Obtiene alertas operativas desde HOY en adelante.
        Reglas: 
        Rojo: 0-2 días
        Amarillo: 3-5 días
        Verde: 6-10 días
        Machu Picchu: Proveedor 'MINISTERIO' (siempre)
        Sin Asignar: Servicios desde hoy a 10 días sin registro en venta_servicio_proveedor
        """
        import pandas as pd
        try:
            hoy = date.today()
            rango_max = hoy + timedelta(days=10)
            
            # --- 1. OBTENER TODOS LOS TOURS PROGRAMADOS DESDE HOY ---
            res_vt = (
                self.client.table('venta_tour')
                .select('id_venta, n_linea, fecha_servicio, observacion, estado_servicio')
                .gte('fecha_servicio', hoy.isoformat())
                .lte('fecha_servicio', rango_max.isoformat())
                .execute()
            )
            
            tours_dict = {}
            id_ventas_unicas = set()
            if res_vt.data:
                for vt in res_vt.data:
                    k = f"{vt['id_venta']}-{vt['n_linea']}"
                    tours_dict[k] = vt
                    id_ventas_unicas.add(vt['id_venta'])
            
            # --- 2. OBTENER NOMBRES DE CLIENTES (Pidiendo la columna correcta 'nombre') ---
            cliente_nombres = {}
            if id_ventas_unicas:
                res_clientes = (
                    self.client.table('venta')
                    .select('id_venta, estado_venta, cliente(nombre)')
                    .in_('id_venta', list(id_ventas_unicas))
                    .neq('estado_venta', 'FINALIZADO')
                    .execute()
                )
                if res_clientes.data:
                    ids_activas = set()
                    for v in res_clientes.data:
                        ids_activas.add(v['id_venta'])
                        c = v.get('cliente') or {}
                        if isinstance(c, list): c = c[0] if c else {}
                        cliente_nombres[v['id_venta']] = c.get('nombre', 'Cliente Desconocido')
                    
                    # Filtrar tours_dict para que solo queden las activas
                    tours_dict = {k: v for k, v in tours_dict.items() if v['id_venta'] in ids_activas}
                    id_ventas_unicas = ids_activas
            
            # --- 3. OBTENER SERVICIOS ASIGNADOS (Con proveedores) ---
            res_vsp = (
                self.client.table('venta_servicio_proveedor')
                .select('*, proveedor(nombre_comercial)')
                .eq('terminado', False)
                .execute()
            )
            
            alertas = {"rojo": [], "amarillo": [], "verde": [], "machupicchu": [], "sin_asignar": []}
            keys_asignadas = set()
            
            # --- 4. PROCESAR ASIGNACIONES EXISTENTES ---
            if res_vsp.data:
                for item in res_vsp.data:
                    k = f"{item['id_venta']}-{item['n_linea']}"
                    keys_asignadas.add(k)
                    
                    vt = tours_dict.get(k)
                    if not vt:
                        continue
                        
                    prov_nom = (item.get('proveedor') or {}).get('nombre_comercial', 'Sin Proveedor')
                    fecha_str = vt.get('fecha_servicio')
                    if not fecha_str: continue
                    
                    try:
                        fecha_serv = pd.to_datetime(fecha_str).date()
                    except:
                        continue
                        
                    dias_dif = (fecha_serv - hoy).days
                    
                    alerta_item = {
                        "id": item['id'],
                        "fecha": fecha_serv.strftime("%d/%m/%Y"),
                        "servicio": vt.get('observacion', item.get('tipo_servicio', 'Servicio')),
                        "cliente": cliente_nombres.get(vt['id_venta'], '---'),
                        "proveedor": prov_nom,
                        "dias": dias_dif
                    }
                    
                    if "MINISTERIO" in prov_nom.upper():
                        alertas["machupicchu"].append(alerta_item)
                    
                    if 0 <= dias_dif <= 10:
                        if dias_dif <= 2: alertas["rojo"].append(alerta_item)
                        elif dias_dif <= 5: alertas["amarillo"].append(alerta_item)
                        else: alertas["verde"].append(alerta_item)

            # --- 5. DETECTAR SERVICIOS SIN ASIGNAR (Huérfanos en venta_tour desde HOY) ---
            ventas_sin_asignar = {}
            if res_vt.data:
                for vt in res_vt.data:
                    k = f"{vt['id_venta']}-{vt['n_linea']}"
                    # Solo nos interesan los que NO están en venta_servicio_proveedor
                    if k not in keys_asignadas:
                        estado = vt.get('estado_servicio', 'PENDIENTE')
                        if estado in ['COMPLETADO', 'CANCELADO']:
                            continue
                            
                        fecha_str2 = vt.get('fecha_servicio')
                        if not fecha_str2: continue
                        
                        try:
                            f_serv = pd.to_datetime(fecha_str2).date()
                        except:
                            continue
                            
                        diff = (f_serv - hoy).days
                        
                        if 0 <= diff <= 10:
                            # AGREGAR A MACHU PICCHU SI ES TICKET Y NO TIENE DATA
                            obs = (vt.get('observacion') or "").upper()
                            if "MACHU" in obs or "MAPI" in obs or "TICKET" in obs:
                                alertas["machupicchu"].append({
                                    "id": None,
                                    "fecha": f_serv.strftime("%d/%m/%Y"),
                                    "servicio": vt.get('observacion', 'TICKET MP'),
                                    "cliente": cliente_nombres.get(vt['id_venta'], '---'),
                                    "proveedor": "🚨 PENDIENTE CARGAR DATA",
                                    "dias": diff
                                })

                            id_v = vt['id_venta']
                            if id_v not in ventas_sin_asignar:
                                ventas_sin_asignar[id_v] = {
                                    "id_venta": id_v,
                                    "n_linea": vt['n_linea'],
                                    "f_serv_minima": f_serv,
                                    "diff_minima": diff,
                                    "servicios": [vt.get('observacion') or "Tour Desconocido"],
                                    "cliente": cliente_nombres.get(id_v, '---')
                                }
                            else:
                                # Solo agregamos si no es un duplicado de servicio en la misma alerta agrupada
                                s_nom = vt.get('observacion') or "Tour Desconocido"
                                if s_nom not in ventas_sin_asignar[id_v]["servicios"]:
                                    ventas_sin_asignar[id_v]["servicios"].append(s_nom)
                                
                                if diff < ventas_sin_asignar[id_v]["diff_minima"]:
                                    ventas_sin_asignar[id_v]["diff_minima"] = diff
                                    ventas_sin_asignar[id_v]["f_serv_minima"] = f_serv
            
            # Formatear el diccionario agrupado a la lista final
            for v_data in ventas_sin_asignar.values():
                cantidad = len(v_data["servicios"])
                if cantidad == 1:
                    serv_text = v_data["servicios"][0]
                else:
                    serv_text = f"⚠️ {cantidad} servicios sin asignar"
                    
                alertas["sin_asignar"].append({
                    "id_venta": v_data["id_venta"],
                    "n_linea": v_data["n_linea"],
                    "fecha": v_data["f_serv_minima"].strftime("%d/%m/%Y"),
                    "servicio": serv_text,
                    "cliente": v_data["cliente"],
                    "proveedor": "🚨 PENDIENTE",
                    "dias": v_data["diff_minima"]
                })

            return alertas
        except Exception as e:
            err_msg = str(e)
            trace = __import__('traceback').format_exc()
            print(f"Error en Alertas Operativas: {err_msg}\n{trace}")
            return {"error": err_msg, "trace": trace, "rojo": [], "amarillo": [], "verde": [], "machupicchu": [], "sin_asignar": []}

    def obtener_resumen_financiero_cancelacion(self, id_venta: int):
        """
        Recupera el consolidado financiero de una venta para el cálculo de cancelaciones y devoluciones:
        - Datos generales de la venta (cliente, pasajeros, fechas)
        - Pagos recibidos (ingreso recaudado)
        - Costos operativos actuales de los servicios de proveedores
        """
        try:
            # 1. Obtener datos generales de la venta
            res_v = self.client.table('venta').select('*, cliente(nombre, lead(numero_celular))').eq('id_venta', id_venta).execute()
            venta = res_v.data[0] if (res_v and res_v.data) else None
            if not venta:
                return None, "No se encontró la venta especificada."
            
            # 2. Obtener pasajeros
            res_pax = self.client.table('pasajero').select('*').eq('id_venta', id_venta).execute()
            pasajeros = res_pax.data or []
            
            # 3. Obtener pagos
            res_pagos = self.client.table('pago').select('*').eq('id_venta', id_venta).execute()
            pagos = res_pagos.data or []
            
            # Calcular ingreso recaudado (reembolsos restan)
            ingreso_recaudado = 0.0
            pagos_detalle = []
            for p in pagos:
                monto = float(p.get('monto_pagado') or 0.0)
                tc = float(p.get('tasa_cambio') or 1.0)
                moneda = p.get('moneda') or 'USD'
                tipo = p.get('tipo_pago') or 'ADELANTO'
                
                # Convertir a soles
                monto_soles = float(p.get('monto_moneda_venta') or monto)
                if moneda == 'USD':
                    monto_soles = monto * tc
                elif moneda == 'PEN':
                    monto_soles = monto
                
                if tipo == 'REEMBOLSO':
                    ingreso_recaudado -= monto_soles
                else:
                    ingreso_recaudado += monto_soles
                
                pagos_detalle.append({
                    "id_pago": p['id_pago'],
                    "fecha_pago": p['fecha_pago'],
                    "monto": monto,
                    "moneda": moneda,
                    "tc": tc,
                    "monto_soles": -monto_soles if tipo == 'REEMBOLSO' else monto_soles,
                    "metodo_pago": p.get('metodo_pago') or '---',
                    "tipo_pago": tipo
                })
                
            # 4. Obtener servicios operativos y costos
            res_servs = self.client.table('venta_servicio_proveedor').select('*, proveedor(nombre_comercial)').eq('id_venta', id_venta).execute()
            servicios = res_servs.data or []
            
            servicios_detalle = []
            costo_incurrido_total = 0.0
            for s in servicios:
                c_unit = float(s.get('costo_unitario') or 0.0)
                pax = float(s.get('cantidad_pax') or 1.0)
                tc = float(s.get('tipo_cambio') or 3.80)
                moneda = s.get('moneda') or 'USD'
                
                total_soles = (c_unit * pax) * tc if moneda == 'USD' else (c_unit * pax)
                costo_incurrido_total += total_soles
                
                servicios_detalle.append({
                    "dia": s.get('n_linea'),
                    "proveedor": s.get('proveedor', {}).get('nombre_comercial') or 'Desconocido',
                    "tipo_servicio": s.get('tipo_servicio') or 'Servicio',
                    "costo_unitario": c_unit,
                    "cantidad_pax": int(pax),
                    "moneda": moneda,
                    "tc": tc,
                    "total_soles": total_soles
                })
                
            return {
                "venta": venta,
                "pasajeros": pasajeros,
                "pagos": pagos_detalle,
                "ingreso_recaudado": ingreso_recaudado,
                "servicios": servicios_detalle,
                "costo_incurrido_total": costo_incurrido_total
            }, None
        except Exception as e:
            return None, f"Error al consolidar resumen de cancelación: {e}"

    def ejecutar_cancelacion_reserva(self, id_venta: int, costo_penalidad: float = 0.0, descripcion_penalidad: str = None, monto_reembolsado: float = 0.0, metodo_reembolso: str = 'TRANSFERENCIA', observaciones: str = None):
        """
        Ejecuta la cancelación física y contable del viaje en el sistema:
        1. Marca el viaje como CANCELADO en la tabla 'venta'.
        2. Setea cancelada = True y fecha_cancelacion = now()
        3. Cambia todos los servicios asociados en 'venta_tour' a CANCELADO / inactivos.
        4. Si el monto_reembolsado > 0, inserta un egreso contable de tipo 'REEMBOLSO' en 'pago' para cuadrar caja.
        """
        try:
            from datetime import datetime, timezone
            now_iso = datetime.now(timezone.utc).isoformat()
            
            # 1. Actualizar la venta principal
            self.client.table('venta').update({
                "estado_venta": "CANCELADO",
                "cancelada": True,
                "fecha_cancelacion": now_iso
            }).eq('id_venta', id_venta).execute()
            
            # 2. Actualizar los servicios operativos de la venta
            self.client.table('venta_tour').update({
                "estado_servicio": "CANCELADO"
            }).eq('id_venta', id_venta).execute()
            
            # 3. Si se definió una penalidad y un reembolso contable:
            if monto_reembolsado > 0:
                self.client.table('pago').insert({
                    "id_venta": id_venta,
                    "fecha_pago": datetime.now().date().isoformat(),
                    "monto_pagado": monto_reembolsado, # positivo por CHECK constraint
                    "moneda": "PEN",
                    "tasa_cambio": 1.0,
                    "monto_moneda_venta": monto_reembolsado,
                    "metodo_pago": metodo_reembolso,
                    "tipo_pago": "REEMBOLSO",
                    "observaciones_contables": f"Reembolso de cancelación de viaje. Motivo: {observaciones or 'Ninguno'}"
                }).execute()
                
            return True, "Cancelación procesada correctamente en operaciones y contabilidad."
        except Exception as e:
            return False, f"Error al ejecutar cancelación de reserva: {e}"