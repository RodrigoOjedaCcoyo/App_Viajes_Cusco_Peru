# controllers/gerencia_controller.py

from supabase import Client
import pandas as pd
from datetime import date

class GerenciaController:
    def __init__(self, supabase_client: Client):
        self.client = supabase_client

    def get_kpis_financieros(self, moneda_destino: str = 'PEN'):
        """Calcula Ventas Totales, Recaudado y Pendiente, normalizado a la moneda de destino ('PEN' o 'USD')."""
        try:
            # 1. Ventas Totales
            res_ventas = self.client.table('venta').select('precio_total_cierre, moneda, tipo_cambio').execute()
            ventas_data = res_ventas.data or []
            
            total_ventas = 0.0
            for v in ventas_data:
                monto = float(v.get('precio_total_cierre') or 0)
                moneda_orig = (v.get('moneda') or 'USD').strip().upper()
                tc = float(v.get('tipo_cambio') or 3.80)
                if tc <= 0:
                    tc = 3.80
                
                if moneda_destino == 'PEN':
                    # Todo a Soles
                    if moneda_orig == 'USD':
                        total_ventas += monto * tc
                    else:
                        total_ventas += monto
                else:
                    # Todo a Dólares
                    if moneda_orig == 'PEN':
                        total_ventas += monto / tc
                    else:
                        total_ventas += monto

            # 2. Pagos Recaudados
            res_pagos = self.client.table('pago').select('monto_pagado, moneda, tasa_cambio, tipo_pago').execute()
            pagos_data = res_pagos.data or []
            
            total_recaudado = 0.0
            for p in pagos_data:
                monto = float(p.get('monto_pagado') or 0)
                moneda_orig = (p.get('moneda') or 'USD').strip().upper()
                tc = float(p.get('tasa_cambio') or 1.0)
                if tc <= 0:
                    tc = 3.80
                tipo = p.get('tipo_pago') or 'ADELANTO'
                
                if moneda_destino == 'PEN':
                    # Todo a Soles
                    if moneda_orig == 'USD':
                        monto_dest = monto * tc
                    else:
                        monto_dest = monto
                else:
                    # Todo a Dólares
                    if moneda_orig == 'PEN':
                        monto_dest = monto / tc
                    else:
                        monto_dest = monto
                        
                if tipo == 'REEMBOLSO':
                    total_recaudado -= monto_dest
                else:
                    total_recaudado += monto_dest

            # 3. Cálculo de Pendiente
            total_pendiente = total_ventas - total_recaudado

            return {
                'ventas_totales': total_ventas,
                'total_recaudado': total_recaudado,
                'total_pendiente': total_pendiente
            }
        except Exception as e:
            print(f"Error Gerencia Financiero: {e}")
            return {'ventas_totales': 0, 'total_recaudado': 0, 'total_pendiente': 0}

    def get_metricas_comerciales(self):
        """Calcula Leads, Clientes y Tasa de Conversión."""
        try:
            # 1. Leads Totales
            res_leads = self.client.table('lead').select('id_lead, red_social').execute()
            leads_data = res_leads.data or []
            total_leads = len(leads_data)

            # 2. Leads Convertidos (Leads que ya son clientes)
            res_cli = self.client.table('cliente').select('id_lead').not_.is_('id_lead', 'null').execute()
            converted_lead_ids = {c['id_lead'] for c in res_cli.data}
            total_convertidos = len(converted_lead_ids)

            # 3. Tasa de Conversión
            tasa_conversion = (total_convertidos / total_leads * 100) if total_leads > 0 else 0

            # 4. Distribución por Medio (MMM Focus)
            df_leads = pd.DataFrame(leads_data)
            distribucion_medios = {}
            if not df_leads.empty and 'red_social' in df_leads.columns:
                distribucion_medios = df_leads['red_social'].value_counts().to_dict()

            return {
                'total_leads': total_leads,
                'total_convertidos': total_convertidos,
                'tasa_conversion': tasa_conversion,
                'distribucion_medios': distribucion_medios
            }
        except Exception as e:
            print(f"Error Gerencia Comercial: {e}")
            return {'total_leads': 0, 'total_convertidos': 0, 'tasa_conversion': 0, 'distribucion_medios': {}}

    def get_pax_totales(self):
        """Calcula el total de pasajeros programados en tours."""
        try:
            res = self.client.table('venta_tour').select('cantidad').execute()
            pax_data = res.data or []
            return sum([p.get('cantidad') or 0 for p in pax_data])
        except Exception as e:
            print(f"Error Gerencia Pax: {e}")
            return 0

    def get_alertas_gestion(self):
        """Busca ventas con criticidades detectadas (Ej: Saldos altos sin pago)."""
        try:
            # Lógica simplificada: Ventas con saldo > 50% y fecha inicio próxima
            res = self.client.table('venta').select('id_venta, precio_total_cierre, fecha_inicio').gt('precio_total_cierre', 0).execute()
            # Retornar vacío por ahora hasta definir nueva lógica de alertas post-summarization
            return []
        except Exception as e:
            print(f"Error Gerencia Alertas: {e}")
            return []

    def get_ventas_mensuales(self, moneda_destino: str = 'PEN'):
        """Agrupa ventas por mes para el gráfico de barras, normalizado a la moneda de destino ('PEN' o 'USD')."""
        try:
            res_ventas = self.client.table('venta').select('precio_total_cierre, fecha_venta, moneda, tipo_cambio').execute()
            if not res_ventas.data:
                return pd.DataFrame()

            df = pd.DataFrame(res_ventas.data)
            df['precio_total_cierre'] = pd.to_numeric(df['precio_total_cierre'], errors='coerce').fillna(0)
            df['tipo_cambio'] = pd.to_numeric(df['tipo_cambio'], errors='coerce').fillna(3.80)
            df.loc[df['tipo_cambio'] <= 0, 'tipo_cambio'] = 3.80

            # Normalizar
            if moneda_destino == 'PEN':
                df['monto_dest'] = df.apply(
                    lambda row: row['precio_total_cierre'] * row['tipo_cambio'] if row['moneda'] == 'USD' else row['precio_total_cierre'],
                    axis=1
                )
            else:
                df['monto_dest'] = df.apply(
                    lambda row: row['precio_total_cierre'] / row['tipo_cambio'] if row['moneda'] == 'PEN' else row['precio_total_cierre'],
                    axis=1
                )

            df['fecha_venta'] = pd.to_datetime(df['fecha_venta'])
            df['Mes'] = df['fecha_venta'].dt.strftime('%Y-%m')
            
            resumen = df.groupby('Mes')['monto_dest'].sum().reset_index()
            resumen.columns = ['Mes', 'Ventas']
            return resumen.sort_values('Mes')
        except Exception as e:
            print(f"Error Gerencia Mensual: {e}")
            return pd.DataFrame()

    def get_desempeno_vendedores(self):
        """Calcula Leads vs Ventas por cada vendedor."""
        try:
            # 1. Obtener Leads con vendedor
            res_leads = self.client.table('lead').select('id_vendedor').execute()
            df_leads = pd.DataFrame(res_leads.data or [])
            
            # 2. Obtener Ventas con vendedor
            res_ventas = self.client.table('venta').select('id_vendedor').execute()
            df_ventas = pd.DataFrame(res_ventas.data or [])
            
            # 3. Mapeo de Nombres de Vendedores
            res_vend = self.client.table('vendedor').select('id_vendedor, nombre').execute()
            vend_map = {v['id_vendedor']: v['nombre'] for v in res_vend.data}
            
            # Procesamiento
            leads_count = {}
            if not df_leads.empty:
                leads_count = df_leads.groupby('id_vendedor').size().to_dict()
                
            ventas_count = {}
            if not df_ventas.empty:
                ventas_count = df_ventas.groupby('id_vendedor').size().to_dict()
            
            data = []
            for vid, nombre in vend_map.items():
                data.append({
                    'Vendedor': nombre,
                    'Leads': leads_count.get(vid, 0),
                    'Ventas': ventas_count.get(vid, 0)
                })
            
            return pd.DataFrame(data)
        except Exception as e:
            print(f"Error Desempeño Vendedores: {e}")
            return pd.DataFrame()

    def get_distribucion_origen_leads(self):
        """Obtiene la cantidad de leads por origen (MMM)."""
        try:
            res = self.client.table('lead').select('red_social').execute()
            df = pd.DataFrame(res.data or [])
            if df.empty: return pd.DataFrame()
            
            resumen = df.groupby('red_social').size().reset_index()
            resumen.columns = ['Origen', 'Cantidad']
            return resumen.sort_values('Cantidad', ascending=False)
        except Exception as e:
            print(f"Error Distribución Lead Origen: {e}")
            return pd.DataFrame()
    def get_ventas_por_canal(self, moneda_destino: str = 'PEN'):
        """Obtiene el monto total de ventas por cada canal, excluyendo B2B del canal DIRECTO, normalizado a la moneda de destino ('PEN' o 'USD')."""
        try:
            res = self.client.table('venta').select('canal_venta, precio_total_cierre, id_agencia_aliada, moneda, tipo_cambio').execute()
            df = pd.DataFrame(res.data or [])
            if df.empty: return pd.DataFrame()

            df['precio_total_cierre'] = pd.to_numeric(df['precio_total_cierre'], errors='coerce').fillna(0)
            df['tipo_cambio'] = pd.to_numeric(df['tipo_cambio'], errors='coerce').fillna(3.80)
            df.loc[df['tipo_cambio'] <= 0, 'tipo_cambio'] = 3.80

            # Normalizar a la moneda destino
            if moneda_destino == 'PEN':
                df['monto_dest'] = df.apply(
                    lambda row: row['precio_total_cierre'] * row['tipo_cambio'] if row['moneda'] == 'USD' else row['precio_total_cierre'],
                    axis=1
                )
            else:
                df['monto_dest'] = df.apply(
                    lambda row: row['precio_total_cierre'] / row['tipo_cambio'] if row['moneda'] == 'PEN' else row['precio_total_cierre'],
                    axis=1
                )

            # El canal DIRECTO debe sumar solo ventas B2C (sin agencia aliada).
            mask_directo_b2b = (
                df['canal_venta'].fillna('').astype(str).str.upper().eq('DIRECTO')
            ) & df['id_agencia_aliada'].notna()
            df = df[~mask_directo_b2b].copy()

            resumen = df.groupby('canal_venta')['monto_dest'].sum().reset_index()
            resumen.columns = ['Canal', 'Monto']
            return resumen.sort_values('Monto', ascending=False)
        except Exception as e:
            print(f"Error Ventas por Canal: {e}")
            return pd.DataFrame()

    def get_ventas_por_estado(self):
        """Obtiene la distribución de ventas por estado actual."""
        try:
            res = self.client.table('venta').select('estado_venta').execute()
            df = pd.DataFrame(res.data or [])
            if df.empty: return pd.DataFrame()
            
            resumen = df.groupby('estado_venta').size().reset_index()
            resumen.columns = ['Estado', 'Cantidad']
            return resumen.sort_values('Cantidad', ascending=False)
        except Exception as e:
            print(f"Error Ventas por Estado: {e}")
            return pd.DataFrame()

    def get_detalle_ventas_limpio(self):
        """Retorna el DataFrame de ventas con nombres de clientes y vendedores para la tabla."""
        try:
            # 1. Ventas
            res_v = self.client.table('venta').select('*').execute()
            df_v = pd.DataFrame(res_v.data or [])
            if df_v.empty: return df_v

            # 2. Clientes
            res_c = self.client.table('cliente').select('id_cliente, nombre').execute()
            cli_map = {c['id_cliente']: c['nombre'] for c in res_c.data}

            # 3. Vendedores
            res_vend = self.client.table('vendedor').select('id_vendedor, nombre').execute()
            vend_map = {v['id_vendedor']: v['nombre'] for v in res_vend.data}

            # Aplicar mapeos
            df_v['Cliente'] = df_v['id_cliente'].map(cli_map).fillna('Desconocido')
            df_v['Vendedor'] = df_v['id_vendedor'].map(vend_map).fillna('Desconocido')
            
            # Ordenar columnas para Gerencia (Sincronizado: estado_venta)
            cols = ['fecha_venta', 'Cliente', 'Vendedor', 'canal_venta', 'precio_total_cierre', 'moneda', 'estado_venta']
            return df_v[cols].rename(columns={
                'fecha_venta': 'Fecha',
                'canal_venta': 'Canal',
                'precio_total_cierre': 'Monto',
                'moneda': 'Divisa',
                'estado_venta': 'Estado'
            })
        except Exception as e:
            print(f"Error Detalle Ventas Limpio: {e}")
            return pd.DataFrame()

    def get_marketing_dashboard_data(self):
        """Procesa itinerarios digitales vinculados a leads para obtener métricas de Marketing."""
        import json
        try:
            # Traemos los itinerarios con información de su lead
            res = self.client.table('itinerario_digital').select('id_lead, fecha_generacion, datos_render, lead(red_social)').execute()
            data = res.data or []
            
            resultados = []
            for d in data:
                lead_info = d.get('lead') or {}
                origen = lead_info.get('red_social') or 'DESCONOCIDO'
                fecha_gen = d.get('fecha_generacion')
                
                raw_render = d.get('datos_render')
                if isinstance(raw_render, str):
                    try:
                        render = json.loads(raw_render)
                    except:
                        render = {}
                elif isinstance(raw_render, dict):
                    render = raw_render
                else:
                    render = {}
                    
                # 1. Extraer Precio (priorizamos total_final_calculado)
                precio = float(render.get('total_final_calculado') or render.get('precio_total') or render.get('total') or 0)
                if not precio and render.get('totales_por_moneda'):
                    tot = render['totales_por_moneda']
                    precio = float(tot.get('USD', 0) or tot.get('PEN', 0) / 3.8)
                
                # 2. Pasajeros
                ci = render.get('control_interno') or {}
                num_pax = int(ci.get('total_pasajeros') or render.get('num_pasajeros') or render.get('pax') or render.get('adultos') or 1)
                
                desglose = ci.get('desglose_pasajeros') or {}
                adultos = 0
                ninos = 0
                for region, stats in desglose.items():
                    if isinstance(stats, dict):
                        adultos += stats.get('adultos', 0)
                        ninos += stats.get('niños', 0)
                if adultos == 0 and ninos == 0:
                    adultos = int(render.get('adultos') or num_pax)
                    ninos = int(render.get('ninos') or 0)
                    
                tipo_pax = "Familia" if ninos > 0 else ("Pareja" if num_pax == 2 else ("Solo" if num_pax == 1 else "Grupo"))
                
                # 3. Fechas y Días
                itinerario_lista = render.get('itinerario') or render.get('days') or render.get('itinerario_detalles') or []
                fecha_viaje = render.get('fechas') or render.get('fecha_viaje') or render.get('fecha_inicio')
                if not fecha_viaje and isinstance(itinerario_lista, list) and len(itinerario_lista) > 0:
                    fecha_viaje = itinerario_lista[0].get('fecha')
                if not fecha_viaje:
                    fecha_viaje = 'SIN FECHA'
                    
                duracion_str = render.get('duracion') or ''
                if duracion_str and 'D' in duracion_str.upper():
                    # Extraer el primer número de "5D / 4N"
                    nums = [int(s) for s in duracion_str.replace('/',' ').split() if s.isdigit()]
                    dias = nums[0] if nums else 1
                else:
                    dias = int(render.get('duracion_dias') or len(itinerario_lista) or 1)
                
                # 4. Tour / Categoría
                t1 = render.get('title_1') or ''
                t2 = render.get('title_2') or ''
                tour = f"{t1} {t2}".strip()
                if not tour:
                    tour = render.get('titulo') or render.get('paquete_nombre') or 'Personalizado'
                    
                # 5. Origen (Prioridad a fuente interna del JSON si existe, sino al Lead)
                fuente_json = render.get('fuente') or render.get('origen')
                origen = fuente_json if fuente_json else origen
                
                resultados.append({
                    'Origen': str(origen),
                    'Fecha_Cotizacion': fecha_gen,
                    'Fecha_Viaje': str(fecha_viaje),
                    'Precio_USD': float(precio),
                    'Pax': int(num_pax),
                    'Adultos': int(adultos),
                    'Ninos': int(ninos),
                    'Tipo_Pax': str(tipo_pax),
                    'Dias': int(dias),
                    'Tour': str(tour)
                })
                
            return pd.DataFrame(resultados)
        except Exception as e:
            print(f"Error Marketing Dashboard Data: {e}")
            return pd.DataFrame()
