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
                res_c = self.client.table('cliente').select('id_cliente, nombre').in_('id_cliente', ids_clientes).execute()
                for c in res_c.data:
                    clientes_map[c['id_cliente']] = c['nombre']

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
                    'fecha_servicio': s['fecha_servicio'],
                    'Hora': s.get('hora_inicio', '08:00 AM'), 
                    'Servicio': nombre_tour,
                    'observacion': nombre_tour,
                    'Endoso?': es_endoso,
                    'Pax': s.get('cantidad', 1),
                    'cantidad': s.get('cantidad', 1),
                    'Cliente': nombre_cliente,
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

    def vincular_endoses_masivos(self, id_venta: str, df_liq: pd.DataFrame):
        """
        Vincula masivamente costos y proveedores a una venta basándose en el 'Dia'.
        df_liq debe tener: ['Dia', 'Tipo_Servicio', 'Proveedor', 'Moneda', 'Costo Unitario', 'Pax']
        """
        resultados = {"exitos": 0, "errores": []}
        
        try:
            res_p = self.client.table('proveedor').select('id_proveedor, nombre_comercial').eq('activo', True).execute()
            mapa_prov = {str(p['nombre_comercial']).strip().upper(): p['id_proveedor'] for p in res_p.data}
        except Exception as e:
            return {"exitos": 0, "errores": [f"Error al cargar proveedores: {str(e)}"]}

        try:
            res_s = self.client.table('venta_tour').select('n_linea, id_itinerario_dia_index').eq('id_venta', id_venta).execute()
            mapa_servicios = {}
            for s in res_s.data:
                dia = s.get('id_itinerario_dia_index')
                if dia:
                    if dia not in mapa_servicios: mapa_servicios[dia] = []
                    mapa_servicios[dia].append(s['n_linea'])
        except Exception as e:
            return {"exitos": 0, "errores": [f"Error al obtener servicios de la venta: {str(e)}"]}

        # PASO 1.5: Sobrescritura Limpia Inteligente (Bulk Delete)
        # Identificamos qué días vienen en el Excel y borramos SOLO los servicios anteriores de esos días
        # para que el Excel actúe como la fuente de la verdad absoluta para esos días específicos.
        try:
            dias_en_excel = df_liq['Dia'].dropna().astype(int).unique().tolist()
            lineas_a_borrar = []
            for d in dias_en_excel:
                if d in mapa_servicios:
                    # Agregamos todas las n_linea asociadas a este día
                    lineas_a_borrar.extend(mapa_servicios[d])
            
            if lineas_a_borrar:
                self.client.table('venta_servicio_proveedor') \
                    .delete() \
                    .eq('id_venta', id_venta) \
                    .in_('n_linea', lineas_a_borrar) \
                    .execute()
        except Exception as e:
            print(f"Alerta: Fallo en Bulk Delete previo: {e}")

        # PASO 2: Inserción de Nuevos Servicios
        for idx, row in df_liq.iterrows():
            try:
                dia_excel = int(row.get('Dia', 0))
                prov_nombre = str(row.get('Proveedor', '')).strip().upper()
                costo_unit = float(row.get('Costo Unitario', 0))
                # Cast to float first to handle string decimals ("7.0"), then to int for Postgres
                pax = int(float(row.get('Pax', 1))) 
                tipo = str(row.get('Tipo_Servicio', 'ENDOSE')).strip().upper()
                moneda = str(row.get('Moneda', 'USD')).strip().upper()

                id_prov = mapa_prov.get(prov_nombre)
                if not id_prov:
                    resultados["errores"].append(f"Fila {idx+1}: Proveedor '{prov_nombre}' no encontrado.")
                    continue

                n_lineas_disponibles = mapa_servicios.get(dia_excel)
                if not n_lineas_disponibles:
                    resultados["errores"].append(f"Fila {idx+1}: No se encontró el Día {dia_excel} en esta venta.")
                    continue
                
                # Consumir la PRIMERA línea (n_linea) asociada a este día como "Ancla"
                # Múltiples servicios del mismo día compartirán esta misma n_linea (permitido por UNIQUE constraint)
                nl = n_lineas_disponibles[0]

                try:
                    data_ins = {
                        "id_venta": id_venta,
                        "n_linea": nl,
                        "id_proveedor": id_prov,
                        "tipo_servicio": tipo,
                        "costo_unitario": costo_unit,
                        "moneda": moneda,
                        "cantidad_pax": pax
                    }
                    self.client.table('venta_servicio_proveedor').upsert(data_ins).execute()
                    
                    # Actualiza referencialmente venta_tour (para sincronización heredada)
                    update_data = {"costo_unitario": (costo_unit * float(pax))}
                    if tipo == "ENDOSE":
                        update_data["es_endoso"] = True
                    
                    self.client.table('venta_tour').update(update_data).eq('id_venta', id_venta).eq('n_linea', nl).execute()
                    resultados["exitos"] += 1
                except Exception as e:
                    resultados["errores"].append(f"Fila {idx+1}: Error DB al guardar Día {dia_excel}, Línea {nl}: {str(e)}")
            except Exception as e:
                resultados["errores"].append(f"Fila {idx+1}: Error formato: {str(e)}")

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
                nombre = str(row.get('Nombre Completo', '')).strip()
                if not nombre:
                    resultados["errores"].append(f"Fila {idx+1}: Nombre vacío.")
                    continue
                
                doc = str(row.get('Documento', '')).strip()
                tipo_doc = str(row.get('Tipo Doc', 'PASAPORTE')).strip().upper()
                nac = str(row.get('Nacionalidad', '')).strip()
                f_nac = row.get('Fecha Nacimiento')
                genero = str(row.get('Genero', '')).strip()
                cuidados = str(row.get('Cuidados', '')).strip()
                # Lógica robusta para 'Es Principal'
                es_p_raw = str(row.get('Es Principal', '')).strip().upper()
                es_p = es_p_raw in ['SI', 'SÍ', 'TRUE', '1', 'VERDADERO']

                if tipo_doc not in ['DNI', 'PASAPORTE', 'CARNET_EXTRANJERIA', 'DIE']:
                    tipo_doc = 'PASAPORTE'

                data_ins = {
                    "id_venta": id_venta,
                    "nombre_completo": nombre,
                    "numero_documento": doc if doc else None,
                    "tipo_documento": tipo_doc,
                    "nacionalidad": nac if nac else None,
                    "fecha_nacimiento": str(f_nac) if pd.notnull(f_nac) else None,
                    "genero": genero if genero else None,
                    "cuidados_especiales": cuidados if cuidados else None,
                    "es_principal": es_p
                }
                
                self.client.table('pasajero').insert(data_ins).execute()
                resultados["exitos"] += 1
            except Exception as e:
                resultados["errores"].append(f"Fila {idx+1}: {e}")
        
        return resultados

    def finalizar_liquidacion_venta(self, id_venta: int):
        """
        Marca la liquidación de la venta como FINALIZADA en la DB.
        """
        try:
            res = self.client.table('venta').update({"estado_liquidacion": "FINALIZADO"}).eq('id_venta', id_venta).execute()
            if res.data:
                return True, "Liquidación enviada a Contabilidad correctamente."
            return False, "No se pudo actualizar el estado de la venta."
        except Exception as e:
            return False, f"Error al finalizar liquidación: {e}"

    def get_liquidaciones_venta(self, id_venta: int):
        """
        Obtiene el detalle de costos (liquidación) vinculado a una venta.
        """
        try:
            res = (
                self.client.table('venta_servicio_proveedor')
                .select('*, proveedor(nombre_comercial)')
                .eq('id_venta', id_venta)
                .execute()
            )
            return res.data or []
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

    def actualizar_estado_servicio_proveedor(self, id_registro: int, estado_bool: bool):
        """
        Actualiza el estado 'terminado' de un registro en venta_servicio_proveedor.
        """
        try:
            self.client.table('venta_servicio_proveedor').update({"terminado": estado_bool}).eq('id', id_registro).execute()
            return True, "Estado actualizado."
        except Exception as e:
            return False, f"Error al actualizar estado: {str(e)}"

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
                    .select('id_venta, cliente(nombre)')
                    .in_('id_venta', list(id_ventas_unicas))
                    .execute()
                )
                if res_clientes.data:
                    for v in res_clientes.data:
                        c = v.get('cliente') or {}
                        if isinstance(c, list): c = c[0] if c else {}
                        cliente_nombres[v['id_venta']] = c.get('nombre', 'Cliente Desconocido')
            
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
            if res_vt.data:
                for vt in res_vt.data:
                    k = f"{vt['id_venta']}-{vt['n_linea']}"
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
                            alertas["sin_asignar"].append({
                                "id_venta": vt['id_venta'],
                                "n_linea": vt['n_linea'],
                                "fecha": f_serv.strftime("%d/%m/%Y"),
                                "servicio": vt.get('observacion') or "Tour Desconocido",
                                "cliente": cliente_nombres.get(vt['id_venta'], '---'),
                                "proveedor": "🚨 NO ASIGNADO",
                                "dias": diff
                            })

            return alertas
        except Exception as e:
            err_msg = str(e)
            trace = __import__('traceback').format_exc()
            print(f"Error en Alertas Operativas: {err_msg}\n{trace}")
            return {"error": err_msg, "trace": trace, "rojo": [], "amarillo": [], "verde": [], "machupicchu": [], "sin_asignar": []}