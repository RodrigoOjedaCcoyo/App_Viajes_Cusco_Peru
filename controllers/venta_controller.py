# controllers/venta_controller.py

from models.venta_model import VentaModel
from supabase import Client
from datetime import date
from typing import Optional, Any
import pandas as pd

class VentaController:
    """Controlador para manejar la lógica de Ventas."""
    def __init__(self, supabase_client:Client):
        self.client = supabase_client
        self.model = VentaModel(supabase_client)

    def registrar_venta_directa(self, 
                                nombre_cliente: str,
                                telefono: str, 
                                origen: str, 
                                vendedor: str,
                                tour: str, 
                                tipo_hotel: str,
                                fecha_inicio: str,
                                fecha_fin: str,
                                monto_total: float,
                                monto_depositado: float,
                                tipo_comprobante: str,
                                moneda: str = "USD",
                                tipo_cambio: Optional[float] = None,
                                id_itinerario_digital: Optional[str] = None,
                                id_lead: Optional[int] = None,
                                items_ingreso: Optional[list] = None,
                                metodo_pago: str = "OTRO",
                                cantidad_pax: int = 1,
                                comentarios: Optional[str] = None,
                                vuelo_internacional: Optional[str] = None,
                                correo: Optional[str] = None,
                                contacto_emergencia_nombre: Optional[str] = None,
                                contacto_emergencia_tel: Optional[str] = None,
                                enviar_correo: bool = False,
                                adjuntos: Optional[dict] = None
                                ) -> tuple[bool, str]:
        """Registra una venta con todos los detalles extendidos."""
        
        # 1. Validaciones Básicas
        if not nombre_cliente or not telefono or not tour or monto_total <= 0:
             return False, "Campos obligatorios faltantes (Nombre, Teléfono, Tour o Monto)."

        # 1.5 Actualizar Comentarios en el Itinerario Digital si existe
        if id_itinerario_digital and comentarios:
            try:
                res_it = self.client.table('itinerario_digital').select('datos_render').eq('id_itinerario_digital', id_itinerario_digital).single().execute()
                if res_it.data:
                    render = res_it.data.get('datos_render', {})
                    render['comentarios_generales'] = comentarios
                    self.client.table('itinerario_digital').update({"datos_render": render}).eq('id_itinerario_digital', id_itinerario_digital).execute()
            except Exception as e:
                print(f"Error actualizando comentarios en itinerario: {e}")

        # 2. Preparar datos
        saldo = monto_total - monto_depositado
        estado_pago = "COMPLETADO" if saldo <= 0 else "PENDIENTE"
        
        venta_data = {
            "nombre_cliente": nombre_cliente,
            "telefono_cliente": telefono,
            "origen": origen,
            "vendedor": vendedor,
            "tour": tour,
            "tipo_hotel": tipo_hotel,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "monto_total": monto_total,
            "monto_depositado": monto_depositado,
            "saldo": saldo,
            "tipo_comprobante": tipo_comprobante,
            "moneda": moneda,
            "tipo_cambio": tipo_cambio,
            "id_itinerario_digital": id_itinerario_digital,
            "id_lead": id_lead,
            "items_ingreso": items_ingreso,
            "metodo_pago": metodo_pago,
            "cantidad": cantidad_pax,
            "nro_vuelo_internacional": vuelo_internacional,
            "correo_cliente": correo,
            "nombre_contacto_emergencia": contacto_emergencia_nombre,
            "telefono_contacto_emergencia": contacto_emergencia_tel,
            "comentarios": comentarios
        }
        
        # Corregir typo detectado
        venta_data["estado_pago"] = estado_pago
        
        # 4. Guardar
        try:
            nuevo_id = self.model.create_venta(venta_data)
            if nuevo_id:
                # 5. Enviar Notificación por Correo (Async)
                if enviar_correo:
                    from utils.email_helper import enviar_notificacion_venta_async
                    # Incluimos el ID generado en la data para el correo
                    venta_data['id_venta'] = nuevo_id
                    enviar_notificacion_venta_async(venta_data, adjuntos)

                return True, f"Venta registrada. ID: {nuevo_id}. Saldo pendiente: {moneda} {float(saldo or 0):.2f}", nuevo_id
            else:
                return False, "Error: no se pudo crear la venta.", None
        except Exception as e:
            return False, f"Error de base de datos: {e}", None

    def registrar_venta_proveedor(self, 
                                  nombre_proveedor: str,
                                  nombre_cliente: str,
                                  telefono: Optional[str], 
                                  vendedor: Optional[int],
                                  tour: str, 
                                  monto_total: float,
                                  monto_depositado: float,
                                  id_agencia_aliada: Optional[int] = None,
                                  estado_limpieza: str = "PENDIENTE",
                                  fecha_inicio: Optional[date] = None,
                                  fecha_fin: Optional[date] = None,
                                  cantidad_pax: int = 1,
                                  id_itinerario_digital: Optional[str] = None,
                                  id_lead: Optional[int] = None,
                                  tipo_comprobante: str = "RECIBO",
                                  tipo_cambio: Optional[float] = None,
                                  items_ingreso: Optional[list] = None,
                                  metodo_pago: str = "OTRO",
                                  vuelo_internacional: Optional[str] = None,
                                  correo: Optional[str] = None,
                                  contacto_emergencia_nombre: Optional[str] = None,
                                  contacto_emergencia_tel: Optional[str] = None,
                                  comentarios: Optional[str] = None,
                                  enviar_correo: bool = True,
                                  adjuntos: Optional[dict] = None
                                  ) -> tuple[bool, str]:
        """Registra una venta proveniente de una agencia externa (B2B)."""
        try:
            # 1. Lógica de Pago
            saldo = monto_total - monto_depositado
            estado_pago = "PAGADO" if saldo <= 0 else "DEBITO"
            
            venta_data = {
                "nombre_cliente": nombre_cliente,
                "telefono_cliente": telefono,
                "vendedor": vendedor,
                "tour": tour,
                "monto_total": monto_total,
                "monto_depositado": monto_depositado,
                "saldo": saldo,
                "estado_pago": estado_pago,
                "origen": f"B2B: {nombre_proveedor}",
                "id_agencia_aliada": id_agencia_aliada,
                "fecha_inicio": (fecha_inicio or date.today()).isoformat(),
                "fecha_fin": (fecha_fin or date.today()).isoformat(),
                "cantidad": cantidad_pax,
                "id_itinerario_digital": id_itinerario_digital,
                "tipo_comprobante": tipo_comprobante,
                "tipo_cambio": tipo_cambio,
                "items_ingreso": items_ingreso,
                "metodo_pago": metodo_pago,
                "nro_vuelo_internacional": vuelo_internacional,
                "correo_cliente": correo,
                "nombre_contacto_emergencia": contacto_emergencia_nombre,
                "telefono_contacto_emergencia": contacto_emergencia_tel or telefono,
                "comentarios": comentarios
            }
            
            res_id = self.model.create_venta(venta_data)
            
            if res_id:
                # 2. Enviar Notificación por Correo (B2B)
                if enviar_correo:
                    try:
                        from utils.email_helper import enviar_notificacion_venta_async
                        venta_data['id_venta'] = res_id
                        # Ajustar moneda por defecto si no viene
                        venta_data['moneda'] = venta_data.get('moneda', 'PEN')
                        enviar_notificacion_venta_async(venta_data, adjuntos)
                    except Exception as e_mail:
                        print(f"Error enviando correo B2B: {e_mail}")

                return True, f"Venta B2B de {nombre_proveedor} registrada éxito (ID: {res_id})"
            return False, "No se pudo registrar la venta en la base de datos."
            
        except Exception as e:
            print(f"Error en registro B2B: {e}")
            return False, f"Error de base de datos: {e}"

    def obtener_agencias_aliadas(self) -> list:
        """Obtiene la lista de agencias aliadas (B2B)."""
        try:
            res = self.client.table('agencia_aliada').select('*').order('nombre').execute()
            return res.data or []
        except Exception as e:
            print(f"Error obteniendo agencias: {e}")
            return []

    def obtener_catalogo_opciones(self) -> list:
        """Obtiene una lista combinada de Tours y Paquetes para selectores."""
        opciones = []
        try:
            # 1. Obtener Tours
            tours = self.client.table('tour').select('id_tour, nombre').execute().data or []
            for t in tours:
                opciones.append({"id": f"T-{t['id_tour']}", "nombre": f"TOUR: {t['nombre']}"})
            
            # 2. Obtener Paquetes
            paquetes = self.client.table('paquete').select('id_paquete, nombre').execute().data or []
            for p in paquetes:
                opciones.append({"id": f"P-{p['id_paquete']}", "nombre": f"PAQUETE: {p['nombre']}"})
                
            return opciones
        except Exception as e:
            print(f"Error obteniendo catálogo: {e}")
            return []

    def obtener_ventas_agencia(self, id_agencia: int) -> list:
        """Obtiene las ventas vinculadas a una agencia aliada específica con nombre de cliente."""
        try:
            # Join con cliente para obtener el nombre - Excluir finalizadas
            res = self.client.table('venta').select('*, cliente(nombre, lead(numero_celular))')\
                .eq('id_agencia_aliada', id_agencia)\
                .neq('estado_venta', 'FINALIZADO')\
                .order('fecha_venta', desc=True).execute()
            
            # Aplanar el resultado para que 'nombre_cliente' esté al primer nivel
            data = []
            for v in (res.data or []):
                c_info = v.get('cliente') or {}
                v['nombre_cliente'] = c_info.get('nombre', 'Desconocido')
                
                # Extraer celular
                l_info = c_info.get('lead') or {}
                if isinstance(l_info, list) and len(l_info) > 0:
                    v['telefono'] = l_info[0].get('numero_celular', '---')
                else:
                    v['telefono'] = l_info.get('numero_celular', '---')
                
                data.append(v)
            return data
        except Exception as e:
            print(f"Error obteniendo ventas de agencia: {e}")
            return []

    def obtener_ventas_directas(self) -> list:
        """Obtiene las ventas directas (B2C) que NO tienen agencia aliada."""
        try:
            # Join con cliente - Excluir finalizadas
            res = self.client.table('venta').select('*, cliente(nombre, lead(numero_celular))')\
                .is_('id_agencia_aliada', 'null')\
                .neq('estado_venta', 'FINALIZADO')\
                .order('fecha_venta', desc=True).execute()
            
            data = []
            for v in (res.data or []):
                c_info = v.get('cliente') or {}
                v['nombre_cliente'] = c_info.get('nombre', 'Desconocido')
                
                # Extraer celular
                l_info = c_info.get('lead') or {}
                if isinstance(l_info, list) and len(l_info) > 0:
                    v['telefono'] = l_info[0].get('numero_celular', '---')
                else:
                    v['telefono'] = l_info.get('numero_celular', '---')
                    
                data.append(v)
            return data
        except Exception as e:
            print(f"Error obteniendo ventas directas: {e}")
            return []

    def obtener_detalles_itinerario_venta(self, id_venta: int) -> list:
        """Obtiene el desglose de días/servicios de una venta específica (venta_tour)."""
        try:
            res = self.client.table('venta_tour').select('*').eq('id_venta', id_venta).order('n_linea').execute()
            return res.data or []
        except Exception as e:
            print(f"Error obteniendo detalles de itinerario: {e}")
            return []

    def sincronizar_venta_con_itinerario(self, id_venta: int) -> tuple[bool, str]:
        """
        Sincroniza venta_tour con la ULTIMA version del itinerario del lead.
        Estrategia: Lead -> itinerario mas reciente por fecha_generacion -> venta_tour.
        """
        import json
        from datetime import datetime, timedelta, date as date_type
        try:
            # PASO 1: Leer datos de la venta
            res_v = self.client.table('venta').select(
                'id_itinerario_digital, id_cliente, precio_total_cierre, num_pasajeros, fecha_inicio, tour_nombre'
            ).eq('id_venta', id_venta).single().execute()

            venta = res_v.data
            if not venta:
                return False, "No se encontro la venta en la base de datos."

            id_itin_guardado = venta.get('id_itinerario_digital')
            id_cliente       = venta.get('id_cliente')

            # PASO 2: Buscar el ULTIMO itinerario disponible para este cliente/lead
            id_itin_final = None
            fuente_itin   = ""

            # Intento A: buscar el itinerario mas reciente del LEAD del cliente
            if id_cliente:
                try:
                    res_cli = self.client.table('cliente').select('id_lead').eq('id_cliente', id_cliente).single().execute()
                    id_lead = (res_cli.data or {}).get('id_lead')
                    if id_lead:
                        res_li = self.client.table('itinerario_digital') \
                            .select('id_itinerario_digital, fecha_generacion') \
                            .eq('id_lead', id_lead) \
                            .order('fecha_generacion', desc=True) \
                            .limit(1).execute()
                        if res_li.data:
                            id_itin_final = res_li.data[0]['id_itinerario_digital']
                            fecha_g = str(res_li.data[0].get('fecha_generacion', ''))[:10]
                            fuente_itin = f"ultimo del Lead (generado {fecha_g})"
                except Exception as e_a:
                    print(f"[Sync-A] {e_a}")

            # Intento B: usar el que esta guardado en la venta (puede ser mas viejo)
            if not id_itin_final and id_itin_guardado:
                id_itin_final = id_itin_guardado
                fuente_itin   = "vinculado a la venta"

            if not id_itin_final:
                return False, (
                    "No se encontro ningun itinerario para sincronizar.\n"
                    "Asegurate de que la venta tenga un lead vinculado con al menos un itinerario generado en el Constructor."
                )

            # PASO 3: Leer el JSON del itinerario encontrado
            res_it = self.client.table('itinerario_digital') \
                .select('datos_render') \
                .eq('id_itinerario_digital', id_itin_final).single().execute()

            if not res_it.data:
                return False, f"El itinerario {id_itin_final} no contiene datos."

            render = res_it.data.get('datos_render', {})
            if isinstance(render, str):
                try:
                    render = json.loads(render)
                except Exception:
                    return False, "El formato del itinerario no es valido (JSON corrupto)."

            if not isinstance(render, dict):
                return False, "El itinerario tiene un formato desconocido."

            # Buscar lista de dias en las claves posibles
            itin_detalles = (
                render.get('itinerario_detalles') or
                render.get('itinerario_detales') or
                render.get('days') or
                render.get('itinerario') or
                []
            )

            if not itin_detalles:
                return False, (
                    f"El itinerario ({fuente_itin}) no tiene dias definidos.\n"
                    "Completa el itinerario en el Constructor primero."
                )

            # PASO 4: Datos base
            f_inicio_raw = venta.get('fecha_inicio')
            try:
                f_inicio = datetime.strptime(str(f_inicio_raw)[:10], "%Y-%m-%d").date() if f_inicio_raw else date_type.today()
            except Exception:
                f_inicio = date_type.today()

            num_pax     = int(venta.get('num_pasajeros') or 1)
            monto_total = float(venta.get('precio_total_cierre') or 0)
            precio_dia  = round(monto_total / len(itin_detalles), 2) if itin_detalles else 0

            # PASO 5: Lineas existentes en venta_tour
            res_cur = self.client.table('venta_tour').select('n_linea').eq('id_venta', id_venta).execute()
            lineas_actuales = {row['n_linea'] for row in (res_cur.data or [])}

            # PASO 6: Upsert de cada dia
            lineas_procesadas = set()
            fechas_servicio   = []

            for i, dia_info in enumerate(itin_detalles):
                n_linea = i + 1
                lineas_procesadas.add(n_linea)

                nombre_servicio = (
                    dia_info.get('titulo') or dia_info.get('nombre') or
                    dia_info.get('title') or dia_info.get('nombre_dia') or
                    render.get('titulo') or venta.get('tour_nombre') or "Servicio"
                )

                f_raw = dia_info.get('fecha') or dia_info.get('date')
                f_servicio = f_inicio + timedelta(days=i)
                if f_raw:
                    f_str = str(f_raw).replace(" ", "").strip()
                    for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%d/%m/%y", "%Y/%m/%d"]:
                        try:
                            f_servicio = datetime.strptime(f_str[:10], fmt).date()
                            break
                        except Exception:
                            continue

                fechas_servicio.append(f_servicio)

                payload = {
                    "fecha_servicio":          f_servicio.isoformat(),
                    "observacion":             nombre_servicio,
                    "cantidad":                num_pax,
                    "precio_applied":          precio_dia,
                    "precio_vendedor":         precio_dia,
                    "id_itinerario_dia_index": n_linea
                }

                if n_linea in lineas_actuales:
                    self.client.table('venta_tour').update(payload) \
                        .eq('id_venta', id_venta).eq('n_linea', n_linea).execute()
                else:
                    payload.update({"id_venta": id_venta, "n_linea": n_linea})
                    self.client.table('venta_tour').insert(payload).execute()

            # PASO 7: Borrar lineas sobrantes
            lineas_a_borrar = lineas_actuales - lineas_procesadas
            if lineas_a_borrar:
                self.client.table('venta_tour').delete() \
                    .eq('id_venta', id_venta).in_('n_linea', list(lineas_a_borrar)).execute()

            # PASO 8: Actualizar venta con el ID del itinerario usado y las fechas reales
            venta_update = {"id_itinerario_digital": id_itin_final}
            if fechas_servicio:
                venta_update['fecha_inicio'] = min(fechas_servicio).isoformat()
                venta_update['fecha_fin']    = max(fechas_servicio).isoformat()
            titulo_render = render.get('titulo') or render.get('title_1') or render.get('tour_nombre')
            if titulo_render:
                venta_update['tour_nombre'] = titulo_render

            self.client.table('venta').update(venta_update).eq('id_venta', id_venta).execute()

            return True, (
                f"Sincronizacion exitosa. "
                f"{len(itin_detalles)} dias actualizados en el calendario operativo. "
                f"Itinerario: {fuente_itin}."
            )

        except Exception as e:
            import traceback
            detalle = traceback.format_exc()[-400:]
            return False, f"Error durante la sincronizacion: {str(e)}\n\nDetalle tecnico:\n{detalle}"

    def agregar_servicio_operativo(self, id_venta: int, id_tour: int, fecha: str, observacion: str, cantidad: int = 1) -> tuple[bool, str]:
        """Añade un servicio manualmente a la logística de una venta."""
        try:
            # 1. Calcular n_linea (el máximo + 1)
            res_max = self.client.table('venta_tour').select('n_linea').eq('id_venta', id_venta).order('n_linea', desc=True).limit(1).execute()
            next_line = (res_max.data[0]['n_linea'] + 1) if res_max.data else 1
            
            # 2. Preparar datos
            payload = {
                "id_venta": id_venta,
                "n_linea": next_line,
                "id_tour": id_tour,
                "fecha_servicio": fecha,
                "observacion": observacion,
                "cantidad": cantidad,
                "precio_applied": 0, # Se puede ajustar luego
                "precio_vendedor": 0
            }
            
            # 3. Insertar
            self.client.table('venta_tour').insert(payload).execute()
            return True, f"Servicio '{observacion}' añadido correctamente al Día {next_line}."
            
        except Exception as e:
            return False, f"Error al añadir servicio: {e}"

    def eliminar_servicio_operativo(self, id_venta: int, n_linea: int) -> tuple[bool, str]:
        """Elimina un servicio específico de la logística."""
        try:
            res = self.client.table('venta_tour').delete().eq('id_venta', id_venta).eq('n_linea', n_linea).execute()
            return True, f"Día {n_linea} eliminado de la logística."
        except Exception as e:
            return False, f"Error al eliminar servicio: {e}"

    def actualizar_servicio_operativo(self, id_venta: int, n_linea: int, update_data: dict) -> tuple[bool, str]:
        """Actualiza los datos de un servicio existente."""
        try:
            res = self.client.table('venta_tour').update(update_data).eq('id_venta', id_venta).eq('n_linea', n_linea).execute()
            return True, f"Día {n_linea} actualizado correctamente."
        except Exception as e:
            return False, f"Error al actualizar servicio: {e}"


    def obtener_todas_ventas_b2b(self) -> list:
        """Obtiene todas las ventas registradas vía agencias aliadas para el dashboard global."""
        try:
            res = self.client.table('venta').select('*, agencia_aliada(nombre), cliente(nombre, lead(numero_celular))').not_.is_('id_agencia_aliada', 'null').order('fecha_venta', desc=True).execute()
            data = []
            for v in (res.data or []):
                v['nombre_agencia'] = v.get('agencia_aliada', {}).get('nombre', 'Desconocido')
                c_info = v.get('cliente') or {}
                v['nombre_cliente'] = c_info.get('nombre', 'Desconocido')
                
                # Extraer celular
                l_info = c_info.get('lead') or {}
                if isinstance(l_info, list) and len(l_info) > 0:
                    v['telefono'] = l_info[0].get('numero_celular', '---')
                else:
                    v['telefono'] = l_info.get('numero_celular', '---')
                    
                data.append(v)
            return data
        except Exception as e:
            print(f"Error obteniendo ventas B2B globales: {e}")
            return []

    def obtener_venta_por_id(self, id_venta: int) -> Optional[dict]:
        """Obtiene los datos básicos de una venta por su ID."""
        try:
            res = self.client.table('venta').select('id_venta, moneda, precio_total_cierre, tour_nombre').eq('id_venta', id_venta).single().execute()
            return res.data
        except Exception as e:
            print(f"Error obteniendo venta {id_venta}: {e}")
            return None

    def registrar_pago(self, 
                       id_venta: int, 
                       monto_pagado: float, 
                       moneda_pago: str, 
                       tasa_cambio: float, 
                       fecha_pago: str, 
                       metodo: str, 
                       tipo_pago: str, 
                       comprobante: str = "RECIBO",
                       observaciones_contables: str = None) -> tuple[bool, str]:
        """Registra un pago individual manejando la conversión de moneda si es necesario."""
        try:
            # 1. Obtener la moneda de la venta
            venta = self.obtener_venta_por_id(id_venta)
            if not venta:
                return False, f"No se encontró la venta con ID {id_venta}"
            
            moneda_venta = venta.get('moneda', 'USD')
            
            # 2. Calcular monto equivalente en moneda de la venta
            monto_equivalente = monto_pagado
            if moneda_pago != moneda_venta:
                if tasa_cambio <= 0:
                    return False, "El tipo de cambio debe ser mayor a 0 para monedas distintas."
                monto_equivalente = round(monto_pagado / tasa_cambio, 2)
            else:
                tasa_cambio = 1.0
            
            # 3. Preparar data
            pago_data = {
                "id_venta": id_venta,
                "fecha_pago": fecha_pago,
                "monto_pagado": monto_pagado,
                "moneda": moneda_pago,
                "metodo_pago": metodo,
                "tipo_pago": tipo_pago,
                "tipo_comprobante": comprobante,
                "tasa_cambio": tasa_cambio,
                "monto_moneda_venta": monto_equivalente,
                "observaciones_contables": observaciones_contables
            }
            
            # 4. Insertar
            self.client.table('pago').insert(pago_data).execute()
            
            return True, f"Pago de {moneda_pago} {monto_pagado:,.2f} registrado exitosamente. Abono a cuenta: {moneda_venta} {monto_equivalente:,.2f}"
            
        except Exception as e:
            return False, f"Error al registrar pago: {e}"

    def vincular_pagos_masivos(self, df: Any) -> dict:
        """Procesa un DataFrame de Excel/CSV para registrar múltiples pagos a la vez con soporte multimoneda."""
        exitos = 0
        errores = []
        
        # Cache de monedas de venta para evitar consultas repetitivas
        cache_monedas = {}
        
        for idx, row in df.iterrows():
            try:
                id_v = row.get('ID Venta')
                monto = row.get('Monto')
                
                if pd.isna(id_v) or pd.isna(monto):
                    continue
                
                id_v = int(id_v)
                monto = float(monto)
                moneda_pago = str(row.get('Moneda') or 'USD').strip().upper()
                tc_row = row.get('TC') or row.get('Tipo de Cambio') or 1.0
                
                # Obtener moneda de la venta (con cache)
                if id_v not in cache_monedas:
                    v = self.obtener_venta_por_id(id_v)
                    cache_monedas[id_v] = v.get('moneda', 'USD') if v else 'USD'
                
                moneda_venta = cache_monedas[id_v]
                
                # Conversión
                tasa_cambio = float(tc_row) if moneda_pago != moneda_venta else 1.0
                monto_equivalente = round(monto / tasa_cambio, 2) if moneda_pago != moneda_venta else monto
                
                pago_data = {
                    "id_venta": id_v,
                    "fecha_pago": str(row.get('Fecha') or date.today()),
                    "monto_pagado": monto,
                    "moneda": moneda_pago,
                    "metodo_pago": str(row.get('Metodo') or 'TRANSFERENCIA').strip().upper(),
                    "tipo_pago": str(row.get('Tipo') or 'ABONO').strip().upper(),
                    "tipo_comprobante": str(row.get('Comprobante') or 'RECIBO').strip().upper(),
                    "tasa_cambio": tasa_cambio,
                    "monto_moneda_venta": monto_equivalente,
                    "observaciones_contables": str(row.get('Obs. Contables') or row.get('Observaciones Contables') or '').strip() or None
                }
                
                # Validaciones de enums
                if pago_data['moneda'] not in ['USD', 'PEN', 'EUR']: pago_data['moneda'] = 'USD'
                if pago_data['metodo_pago'] not in ["EFECTIVO", "TRANSFERENCIA", "YAPE", "PLIN", "TARJETA", "PAYPAL", "IZIPAY", "VISA", "MASTER CARD", "INTERBANK", "OTRO"]: 
                    pago_data['metodo_pago'] = 'TRANSFERENCIA'
                if pago_data['tipo_pago'] not in ['ADELANTO', 'SALDO', 'TOTAL', 'PARCIAL', 'REEMBOLSO']: pago_data['tipo_pago'] = 'PARCIAL'
                if pago_data['tipo_comprobante'] not in ['BOLETA', 'FACTURA', 'RECIBO', 'RECIBO SIMPLE', 'SIN_COMPROBANTE']: pago_data['tipo_comprobante'] = 'RECIBO'
                
                self.client.table('pago').insert(pago_data).execute()
                exitos += 1
                
            except Exception as e:
                errores.append(f"Fila {idx+2}: {str(e)}")
        
        return {"exitos": exitos, "errores": errores}

    def eliminar_venta(self, id_venta: int) -> tuple[bool, str]:
        """Elimina una venta y sus registros asociados (dependiendo de FK cascades)."""
        try:
            # 1. Eliminar pagos asociados (por si no hay cascade en DB)
            self.client.table('pago').delete().eq('id_venta', id_venta).execute()
            # 2. Eliminar logística asociada
            self.client.table('venta_tour').delete().eq('id_venta', id_venta).execute()
            # 3. Eliminar la venta principal
            exito = self.model.delete_by_id(id_venta)
            
            if exito:
                return True, f"Venta {id_venta} eliminada correctamente."
            return False, "No se encontró la venta o no pudo ser eliminada."
        except Exception as e:
            return False, f"Error al eliminar la venta: {e}"
