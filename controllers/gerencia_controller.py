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
            # 1. Ventas Totales (excluye canceladas: no son ingreso real)
            res_ventas = self.client.table('venta').select('precio_total_cierre, moneda, tipo_cambio').neq('estado_venta', 'CANCELADO').execute()
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
            res_ventas = self.client.table('venta').select('precio_total_cierre, fecha_venta, moneda, tipo_cambio').neq('estado_venta', 'CANCELADO').execute()
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

    def get_desempeno_vendedores(self, fecha_inicio=None, fecha_fin=None, segmento=None):
        """Calcula Leads vs Ventas por cada vendedor."""
        try:
            # 1. Obtener Leads con vendedor
            res_leads = self.client.table('lead').select('id_vendedor, fecha_registro').execute()
            df_leads = pd.DataFrame(res_leads.data or [])
            if not df_leads.empty and fecha_inicio and fecha_fin:
                df_leads['fecha_registro'] = pd.to_datetime(df_leads['fecha_registro']).dt.date
                df_leads = df_leads[(df_leads['fecha_registro'] >= fecha_inicio) & (df_leads['fecha_registro'] <= fecha_fin)]
            
            # 2. Obtener Ventas con vendedor
            res_ventas = self.client.table('venta').select('id_vendedor, fecha_venta, id_agencia_aliada').execute()
            df_ventas = pd.DataFrame(res_ventas.data or [])
            if not df_ventas.empty:
                if fecha_inicio and fecha_fin:
                    df_ventas['fecha_venta'] = pd.to_datetime(df_ventas['fecha_venta']).dt.date
                    df_ventas = df_ventas[(df_ventas['fecha_venta'] >= fecha_inicio) & (df_ventas['fecha_venta'] <= fecha_fin)]
                if segmento == 'B2C':
                    df_ventas = df_ventas[df_ventas['id_agencia_aliada'].isna()]
                elif segmento == 'Corporativo':
                    df_ventas = df_ventas[df_ventas['id_agencia_aliada'].notna()]
            
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
            raise  # Temporal: dejar que el error real se vea en pantalla para diagnosticar

    def get_distribucion_origen_leads(self, fecha_inicio=None, fecha_fin=None):
        """Obtiene la cantidad de leads por origen (MMM)."""
        try:
            res = self.client.table('lead').select('red_social, fecha_registro').execute()
            df = pd.DataFrame(res.data or [])
            if df.empty: return pd.DataFrame()
            if fecha_inicio and fecha_fin:
                df['fecha_registro'] = pd.to_datetime(df['fecha_registro']).dt.date
                df = df[(df['fecha_registro'] >= fecha_inicio) & (df['fecha_registro'] <= fecha_fin)]
            
            resumen = df.groupby('red_social').size().reset_index()
            resumen.columns = ['Origen', 'Cantidad']
            return resumen.sort_values('Cantidad', ascending=False)
        except Exception as e:
            print(f"Error Distribución Lead Origen: {e}")
            return pd.DataFrame()
    def get_ventas_por_canal(self, moneda_destino: str = 'PEN', fecha_inicio=None, fecha_fin=None, segmento=None):
        """Obtiene el monto total de ventas por cada canal, excluyendo B2B del canal DIRECTO, normalizado a la moneda de destino ('PEN' o 'USD')."""
        try:
            res = self.client.table('venta').select('canal_venta, precio_total_cierre, id_agencia_aliada, moneda, tipo_cambio, fecha_venta').neq('estado_venta', 'CANCELADO').execute()
            df = pd.DataFrame(res.data or [])
            if df.empty: return pd.DataFrame()
            if fecha_inicio and fecha_fin:
                df['fecha_venta'] = pd.to_datetime(df['fecha_venta']).dt.date
                df = df[(df['fecha_venta'] >= fecha_inicio) & (df['fecha_venta'] <= fecha_fin)]
            if segmento == 'B2C':
                df = df[df['id_agencia_aliada'].isna()]
            elif segmento == 'Corporativo':
                df = df[df['id_agencia_aliada'].notna()]

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

    def get_ventas_por_estado(self, fecha_inicio=None, fecha_fin=None, segmento=None):
        """Obtiene la distribución de ventas por estado actual."""
        try:
            res = self.client.table('venta').select('estado_venta, fecha_venta, id_agencia_aliada').execute()
            df = pd.DataFrame(res.data or [])
            if df.empty: return pd.DataFrame()
            if fecha_inicio and fecha_fin:
                df['fecha_venta'] = pd.to_datetime(df['fecha_venta']).dt.date
                df = df[(df['fecha_venta'] >= fecha_inicio) & (df['fecha_venta'] <= fecha_fin)]
            if segmento == 'B2C':
                df = df[df['id_agencia_aliada'].isna()]
            elif segmento == 'Corporativo':
                df = df[df['id_agencia_aliada'].notna()]
            
            resumen = df.groupby('estado_venta').size().reset_index()
            resumen.columns = ['Estado', 'Cantidad']
            return resumen.sort_values('Cantidad', ascending=False)
        except Exception as e:
            print(f"Error Ventas por Estado: {e}")
            return pd.DataFrame()

    def get_detalle_ventas_limpio(self, fecha_inicio=None, fecha_fin=None, segmento=None):
        """Retorna el DataFrame de ventas con nombres de clientes y vendedores para la tabla."""
        try:
            # 1. Ventas
            res_v = self.client.table('venta').select('*').execute()
            df_v = pd.DataFrame(res_v.data or [])
            if df_v.empty: return df_v
            if fecha_inicio and fecha_fin:
                df_v['fecha_venta'] = pd.to_datetime(df_v['fecha_venta']).dt.date
                df_v = df_v[(df_v['fecha_venta'] >= fecha_inicio) & (df_v['fecha_venta'] <= fecha_fin)]
            if segmento == 'B2C':
                df_v = df_v[df_v['id_agencia_aliada'].isna()]
            elif segmento == 'Corporativo':
                df_v = df_v[df_v['id_agencia_aliada'].notna()]

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

    # ------------------------------------------------------------------
    # DESEMPEÑO DE CONTABILIDAD (Panel de Gerencia > Desempeño de Contabilidad)
    # ------------------------------------------------------------------

    def _normalizar_moneda(self, monto: float, moneda_orig: str, tc: float, moneda_destino: str) -> float:
        """Convierte un monto a la moneda de destino ('PEN' o 'USD') usando la tasa de cambio dada."""
        moneda_orig = (moneda_orig or 'USD').strip().upper()
        tc = float(tc or 3.80)
        if tc <= 0:
            tc = 3.80
        if moneda_destino == 'PEN':
            return monto * tc if moneda_orig == 'USD' else monto
        return monto / tc if moneda_orig == 'PEN' else monto

    def get_ingresos_detalle_periodo(self, fecha_inicio, fecha_fin, segmento=None, moneda_destino='PEN') -> pd.DataFrame:
        """Pagos de clientes (ingresos cobrados) en el rango de fecha_pago, normalizados a la moneda de destino."""
        try:
            res = (
                self.client.table('pago')
                .select('fecha_pago, monto_pagado, moneda, tasa_cambio, tipo_pago, metodo_pago, id_venta, venta(id_agencia_aliada)')
                .gte('fecha_pago', fecha_inicio.isoformat())
                .lte('fecha_pago', fecha_fin.isoformat())
                .execute()
            )
            filas = []
            for p in (res.data or []):
                v = p.get('venta') or {}
                if isinstance(v, list):
                    v = v[0] if v else {}
                tipo = 'B2B' if v.get('id_agencia_aliada') else 'B2C'
                if segmento and tipo != segmento:
                    continue

                monto_dest = self._normalizar_moneda(
                    float(p.get('monto_pagado') or 0), p.get('moneda'), p.get('tasa_cambio'), moneda_destino
                )
                if p.get('tipo_pago') == 'REEMBOLSO':
                    monto_dest = -monto_dest

                filas.append({
                    'fecha': p.get('fecha_pago'),
                    'monto': monto_dest,
                    'metodo_pago': p.get('metodo_pago') or 'OTRO',
                    'tipo_venta': tipo,
                })
            return pd.DataFrame(filas)
        except Exception as e:
            print(f"Error get_ingresos_detalle_periodo: {e}")
            return pd.DataFrame()

    def get_gastos_detalle_periodo(self, fecha_inicio, fecha_fin, segmento=None, moneda_destino='PEN') -> pd.DataFrame:
        """Pagos a proveedores (gastos operativos) en el rango de fecha_pago, normalizados a la moneda de destino."""
        try:
            res = (
                self.client.table('pago_operativo')
                .select('fecha_pago, monto_pagado, moneda, tasa_cambio, metodo_pago, id_venta, proveedor(nombre_comercial), venta(id_agencia_aliada)')
                .gte('fecha_pago', fecha_inicio.isoformat())
                .lte('fecha_pago', fecha_fin.isoformat())
                .execute()
            )
            filas = []
            for g in (res.data or []):
                v = g.get('venta') or {}
                if isinstance(v, list):
                    v = v[0] if v else {}
                tipo = 'B2B' if v.get('id_agencia_aliada') else 'B2C'
                if segmento and tipo != segmento:
                    continue

                monto_dest = self._normalizar_moneda(
                    float(g.get('monto_pagado') or 0), g.get('moneda'), g.get('tasa_cambio'), moneda_destino
                )
                prov = g.get('proveedor') or {}
                if isinstance(prov, list):
                    prov = prov[0] if prov else {}

                filas.append({
                    'fecha': g.get('fecha_pago'),
                    'monto': monto_dest,
                    'metodo_pago': g.get('metodo_pago') or 'OTRO',
                    'proveedor': prov.get('nombre_comercial') or 'Sin Proveedor',
                    'tipo_venta': tipo,
                })
            return pd.DataFrame(filas)
        except Exception as e:
            print(f"Error get_gastos_detalle_periodo: {e}")
            return pd.DataFrame()

    def get_cuentas_por_cobrar_periodo(self, fecha_inicio, fecha_fin, segmento=None, moneda_destino='PEN', top_n=10) -> pd.DataFrame:
        """Clientes con saldo pendiente, para ventas cerradas dentro del rango de fecha_venta."""
        try:
            res_v = (
                self.client.table('venta')
                .select('id_venta, precio_total_cierre, moneda, tipo_cambio, id_agencia_aliada, cancelada, cliente(nombre)')
                .gte('fecha_venta', fecha_inicio.isoformat())
                .lte('fecha_venta', fecha_fin.isoformat())
                .execute()
            )

            ventas = []
            ids_venta = []
            for v in (res_v.data or []):
                if v.get('cancelada'):
                    continue
                tipo = 'B2B' if v.get('id_agencia_aliada') else 'B2C'
                if segmento and tipo != segmento:
                    continue
                ventas.append(v)
                ids_venta.append(v['id_venta'])

            if not ids_venta:
                return pd.DataFrame()

            res_p = (
                self.client.table('pago')
                .select('id_venta, monto_pagado, moneda, tasa_cambio, tipo_pago')
                .in_('id_venta', ids_venta)
                .execute()
            )
            pagos_por_venta = {}
            for p in (res_p.data or []):
                monto_dest = self._normalizar_moneda(
                    float(p.get('monto_pagado') or 0), p.get('moneda'), p.get('tasa_cambio'), moneda_destino
                )
                if p.get('tipo_pago') == 'REEMBOLSO':
                    monto_dest = -monto_dest
                id_v = p['id_venta']
                pagos_por_venta[id_v] = pagos_por_venta.get(id_v, 0.0) + monto_dest

            filas = []
            for v in ventas:
                total_dest = self._normalizar_moneda(
                    float(v.get('precio_total_cierre') or 0), v.get('moneda'), v.get('tipo_cambio'), moneda_destino
                )
                saldo = total_dest - pagos_por_venta.get(v['id_venta'], 0.0)
                if saldo <= 0.5:
                    continue

                cli = v.get('cliente') or {}
                if isinstance(cli, list):
                    cli = cli[0] if cli else {}
                filas.append({'Cliente': cli.get('nombre') or 'Desconocido', 'Saldo Pendiente': round(saldo, 2)})

            if not filas:
                return pd.DataFrame()

            df = pd.DataFrame(filas).groupby('Cliente', as_index=False)['Saldo Pendiente'].sum()
            return df.sort_values('Saldo Pendiente', ascending=False).head(top_n)
        except Exception as e:
            print(f"Error get_cuentas_por_cobrar_periodo: {e}")
            return pd.DataFrame()

    def get_top_proveedores_gasto_periodo(self, fecha_inicio, fecha_fin, segmento=None, moneda_destino='PEN', top_n=10) -> pd.DataFrame:
        """Top proveedores por monto realmente pagado (pago_operativo) en el rango de fecha_pago."""
        df = self.get_gastos_detalle_periodo(fecha_inicio, fecha_fin, segmento=segmento, moneda_destino=moneda_destino)
        if df.empty:
            return df
        resumen = (
            df.groupby('proveedor', as_index=False)['monto']
            .sum()
            .rename(columns={'proveedor': 'Proveedor', 'monto': 'Monto'})
        )
        return resumen.sort_values('Monto', ascending=False).head(top_n)

    def get_marketing_dashboard_data(self, fecha_inicio=None, fecha_fin=None, segmento=None):
        """Procesa itinerarios digitales vinculados a leads para obtener métricas de Marketing."""
        import json
        from datetime import datetime
        try:
            # 1. Total Leads en el sistema
            res_leads = self.client.table('lead').select('id_lead', count='exact').limit(1).execute()
            total_leads = res_leads.count if res_leads.count is not None else 0
            
            # 2. Traemos los itinerarios con información de su lead, ordenados por fecha desc
            res = self.client.table('itinerario_digital').select('id_lead, fecha_generacion, datos_render, lead(red_social)').order('fecha_generacion', desc=True).execute()
            data = res.data or []
            total_itinerarios = len(data)
            
            # 3. Quedarnos solo con el ÚLTIMO itinerario por lead
            leads_vistos = set()
            data_unica = []
            for d in data:
                id_lead = d.get('id_lead')
                if id_lead and id_lead not in leads_vistos:
                    leads_vistos.add(id_lead)
                    data_unica.append(d)
                elif not id_lead:
                    data_unica.append(d)
            
            resultados_paquetes = []
            resultados_tours = []
            
            for d in data_unica:
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
                    
                # Filtro de Segmento (Vendedor)
                vendedor = render.get('vendedor') or 'SIN ASIGNAR'
                if segmento:
                    es_maria = "MARIA" in str(vendedor).upper()
                    if segmento == "Corporativo" and not es_maria:
                        continue
                    if segmento == "B2C" and es_maria:
                        continue
                        
                # Filtro de Fechas
                fecha_gen = d.get('fecha_generacion')
                if fecha_gen:
                    fecha_gen = fecha_gen[:10]
                    if fecha_inicio and fecha_fin:
                        try:
                            f_obj = datetime.strptime(fecha_gen, '%Y-%m-%d').date()
                            if not (fecha_inicio <= f_obj <= fecha_fin):
                                continue
                        except:
                            continue
                elif fecha_inicio and fecha_fin:
                    continue # No date, skip if filter applied
                    
                # 1. Extraer Precio (priorizamos total_final_calculado)
                precio = float(render.get('total_final_calculado') or render.get('precio_total') or render.get('total') or 0)
                if not precio and render.get('totales_por_moneda'):
                    tot = render['totales_por_moneda']
                    precio = float(tot.get('USD', 0) or tot.get('PEN', 0) / 3.8)
                
                # 2. Origen (Nacionalidad: Extranjero, Nacional, Mixto)
                origen_nacionalidad = render.get('origen') or 'NO ESPECIFICADO'
                
                # 3. Paquete Cotizado
                t1 = render.get('title_1') or ''
                t2 = render.get('title_2') or ''
                paquete = f"{t1} {t2}".strip()
                if not paquete:
                    paquete = render.get('titulo') or render.get('paquete_nombre') or 'Personalizado'
                
                # 4. Pasajero y Vendedor
                pasajero = render.get('pasajero') or 'SIN NOMBRE'
                duracion = render.get('duracion') or '-'
                fechas_viaje = render.get('fechas') or '-'
                
                resultados_paquetes.append({
                    'Pasajero': str(pasajero).upper(),
                    'Vendedor': str(vendedor).title(),
                    'Paquete': str(paquete),
                    'Duración': str(duracion),
                    'Fechas_Viaje': str(fechas_viaje),
                    'Origen_Nacionalidad': str(origen_nacionalidad).title(),
                    'Precio_Total_USD': float(precio),
                    'Fecha_Cotizacion': fecha_gen
                })
                
                # 6. Tours individuales detallados
                itinerario_lista = render.get('itinerario') or render.get('days') or render.get('itinerario_detalles') or []
                if isinstance(itinerario_lista, list):
                    for dia in itinerario_lista:
                        if isinstance(dia, dict):
                            titulo_tour = dia.get('titulo')
                            if titulo_tour:
                                resultados_tours.append({'Tour': str(titulo_tour).upper().strip()})
                
            return total_leads, total_itinerarios, pd.DataFrame(resultados_paquetes), pd.DataFrame(resultados_tours)
        except Exception as e:
            print(f"Error Marketing Dashboard Data: {e}")
            return 0, 0, pd.DataFrame(), pd.DataFrame()
