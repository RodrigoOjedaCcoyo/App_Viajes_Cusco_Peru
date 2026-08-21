import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def render_sales_dashboard(df_ventas, supabase_client=None, periodo=None):
    """Genera el Dashboard Comercial (Objetivos B2C - SOLES) con metas mensuales congeladas en BD."""
    st.subheader("🎯 Dashboard de Objetivos (B2C)")
    
    meta_actual = 10000.0
    esta_congelada = False
    
    # 1. Intentar obtener de la BD
    if supabase_client is not None and periodo is not None:
        try:
            from controllers.reporte_controller import ReporteController
            reporte_ctrl = ReporteController(supabase_client)
            meta_actual, esta_congelada = reporte_ctrl.obtener_meta_mensual(periodo)
        except Exception as e:
            print(f"Error cargando meta de la BD: {e}")
            
    # 2. Renderizar Interfaz según estado
    if esta_congelada:
        with st.container(border=True):
            st.markdown(f"### 🔒 Meta Mensual Establecida: **S/ {meta_actual:,.2f}**")
            st.info(f"💡 La meta de ventas para el periodo **{periodo}** está guardada en la base de datos y se encuentra congelada para resguardar la integridad del reporte mensual.")
    else:
        # Si no está congelada, permitimos que la establezcan por primera vez
        c_meta, c_btn = st.columns([1, 1])
        with c_meta:
            meta_actual = st.number_input(
                f"Establecer Meta de {periodo} (S/)", 
                min_value=1.0, 
                value=float(st.session_state.get('meta_ventas', meta_actual)), 
                step=1000.0
            )
            st.session_state['meta_ventas'] = meta_actual
        with c_btn:
            st.write("")  # Spacing
            st.write("")  # Spacing
            if st.button("🔒 Establecer y Congelar Meta", type="primary", use_container_width=True):
                if supabase_client is not None and periodo is not None:
                    from controllers.reporte_controller import ReporteController
                    reporte_ctrl = ReporteController(supabase_client)
                    if reporte_ctrl.guardar_meta_mensual(periodo, meta_actual):
                        st.success(f"¡Meta de S/ {meta_actual:,.2f} congelada con éxito!")
                        st.rerun()
                    else:
                        st.error("Error al guardar la meta. Intente nuevamente.")
                else:
                    st.warning("No hay conexión con la base de datos para congelar la meta.")

    if df_ventas.empty:
        st.info("No hay datos de ventas B2C para mostrar el avance aún.")
        total_sales_pen = 0.0
    else:
        # Asumimos que la columna 'monto_total' ya viene convertida a Soles desde page_dashboards
        # o que la vista lo asegura. Por requerimiento: TODO ES SOLES.
        df_ventas['monto_total_pen'] = pd.to_numeric(df_ventas.get('monto_total_pen', df_ventas.get('monto_total', 0)))
        total_sales_pen = df_ventas['monto_total_pen'].sum()
        
    # Cálculos
    porcentaje = (total_sales_pen / meta_actual) * 100 if meta_actual > 0 else 0
    faltante = max(0, meta_actual - total_sales_pen)
    
    # --- MÉTRICAS ---
    k1, k2, k3 = st.columns(3)
    k1.metric("Ventas Acumuladas (S/)", f"S/ {total_sales_pen:,.2f}")
    k2.metric("Meta Establecida (S/)", f"S/ {meta_actual:,.2f}")
    k3.metric("Faltante para Meta (S/)", f"S/ {faltante:,.2f}")
    
    # --- GRÁFICO TIPO GAUGE / VELOCÍMETRO ---
    st.markdown("### 🚀 Progreso de la Meta Ménsual")
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = total_sales_pen,
        number = {'prefix': "S/ ", 'valueformat': ",.2f"},
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': f"Avance: {porcentaje:.1f}%"},
        delta = {'reference': meta_actual, 'position': "top", 'prefix': "Meta: S/ ", 'valueformat': ",.0f"},
        gauge = {
            'axis': {'range': [None, meta_actual], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "#00C853" if porcentaje >= 100 else "#2196F3"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, meta_actual * 0.5], 'color': '#FFCDD2'},
                {'range': [meta_actual * 0.5, meta_actual * 0.8], 'color': '#FFF9C4'},
                {'range': [meta_actual * 0.8, meta_actual], 'color': '#DCEDC8'}],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': meta_actual}
        }
    ))
    fig.update_layout(height=400, margin=dict(l=20, r=20, t=50, b=20))
    st.plotly_chart(fig, use_container_width=True)
    
    # --- MENSAJE MOTIVACIONAL ---
    if not df_ventas.empty:
        st.markdown("---")
        if porcentaje >= 100:
            st.success("🎉 ¡Felicidades equipo! Hemos alcanzado la meta del mes. ¡Sigan así!")
            st.balloons()
        elif porcentaje >= 80:
            st.info("🔥 ¡Estamos muy cerca de la meta! ¡Un último esfuerzo!")
        elif porcentaje >= 50:
            st.warning("💪 ¡Ya pasamos la mitad de la meta! Sigamos empujando.")
        else:
            st.write("✨ ¡Cada venta cuenta! Vamos juntos por esa meta.")
            
        st.markdown("---")
        
        # --- CALCULADORA GENERAL DE COMISIONES ---
        st.subheader("💰 Calculadora de Comisiones Reales")
        st.write("Calcula dinámicamente el pozo estimado de comisiones según las ventas logradas.")
        
        if 'porcentaje_comision' not in st.session_state:
            st.session_state['porcentaje_comision'] = 10.0 # Valor por defecto: 10%
            
        c_comis, c_resul = st.columns([1, 2])
        
        with c_comis:
            porcentaje_input = st.number_input(
                "% de Comisión General",
                min_value=0.0,
                max_value=100.0,
                value=st.session_state['porcentaje_comision'],
                step=1.0,
                format="%.1f"
            )
            st.session_state['porcentaje_comision'] = porcentaje_input
            
        with c_resul:
            pozo_comisiones = total_sales_pen * (porcentaje_input / 100.0)
            with st.container(border=True):
                st.metric("Pozo de Comisiones Generadas", f"S/ {pozo_comisiones:,.2f}", delta=f"{porcentaje_input}% del Total")


def render_operations_dashboard(df_servicios):
    """Genera el Dashboard Operativo Profesional."""
    if df_servicios.empty:
        st.info("No hay servicios operativos registrados para el periodo.")
        return

    # Mapeo defensivo interno para visualización
    fallbacks_fecha = ['fecha_servicio', 'Fecha', 'fecha']
    for fb in fallbacks_fecha:
        if fb in df_servicios.columns:
            if fb != 'fecha_servicio':
                df_servicios.rename(columns={fb: 'fecha_servicio'}, inplace=True)
            break

    # Convertir fecha si es necesario
    if 'fecha_servicio' in df_servicios.columns:
        df_servicios['fecha_servicio'] = pd.to_datetime(df_servicios['fecha_servicio'])

    # KPIs Logísticos removidos a petición del usuario.
    
    # Gráficos de Operación
    st.markdown("**📉 Volumen de Pasajeros por Fecha**")
    if 'fecha_servicio' in df_servicios.columns:
        ops_by_date = df_servicios.groupby('fecha_servicio').size().reset_index(name='servicios')
        fig_timeline = px.area(ops_by_date, x='fecha_servicio', y='servicios', 
                                markers=True, title="Carga de Trabajo Diaria",
                                color_discrete_sequence=['#4CAF50'])
        st.plotly_chart(fig_timeline, use_container_width=True)
    else:
        st.warning("⚠️ No se puede mostrar la línea de tiempo: falta columna 'fecha_servicio'")
        if not df_servicios.empty:
            st.write("Columnas disponibles:", df_servicios.columns.tolist())

def render_financial_dashboard(df_ventas, df_gastos_op=None, supabase_client=None, filtro_moneda="Ambas", df_ventas_gastos=None):
    """Genera el Dashboard Financiero con gastos reales desde pago_operativo."""
    st.subheader("Resultados Financieros")

    # --- Moneda de presentación: sigue al filtro "Moneda Original" ---
    # Solo cuando se elige explícitamente Dólares se muestra en USD; Soles y Ambas se muestran en Soles.
    if filtro_moneda == "Dólares (USD)":
        moneda_destino, simbolo = 'USD', '$'
    else:
        moneda_destino, simbolo = 'PEN', 'S/'

    def _convertir(monto, moneda_origen, tc):
        moneda_origen = (moneda_origen or 'USD').strip().upper()
        if moneda_origen == moneda_destino:
            return monto
        if moneda_destino == 'PEN':
            return monto * tc  # USD -> PEN
        return monto / tc  # PEN -> USD

    # --- INGRESOS: suma de precio_total_cierre normalizado a la moneda destino ---
    total_ingresos = 0.0
    if not df_ventas.empty:
        for _, row in df_ventas.iterrows():
            monto = float(row.get('precio_total_cierre') or row.get('monto_total') or 0)
            moneda = str(row.get('moneda') or 'USD').strip().upper()
            tc = float(row.get('tipo_cambio') or 3.80)
            if tc <= 0:
                tc = 3.80
            total_ingresos += _convertir(monto, moneda, tc)

    # --- GASTOS: leer pago_operativo directamente desde Supabase ---
    # Se restringe a las ventas de "df_ventas_gastos" (filtradas por fecha de INICIO del viaje)
    # si se provee; si no, cae de vuelta a df_ventas (mismo comportamiento de antes).
    # Ingresos = por fecha de venta. Gastos = por fecha en que viaja el pasajero (egreso real del período).
    df_scope_gastos = df_ventas_gastos if df_ventas_gastos is not None else df_ventas
    ids_venta_filtradas = None
    if not df_scope_gastos.empty and 'id_venta' in df_scope_gastos.columns:
        ids_venta_filtradas = set(df_scope_gastos['id_venta'].dropna().tolist())

    total_gastos = 0.0
    if supabase_client is not None:
        try:
            res_op = supabase_client.table('pago_operativo').select(
                'id_venta, monto_pagado, moneda, tasa_cambio'
            ).execute()
            for p in (res_op.data or []):
                if ids_venta_filtradas is not None and p.get('id_venta') not in ids_venta_filtradas:
                    continue

                # No se filtra por moneda del pago al proveedor: un pasajero puede pagar
                # en soles y la agencia pagarle al proveedor en dólares (o viceversa) —
                # ese costo sigue siendo real y debe contarse, convertido a moneda_destino.
                moneda = str(p.get('moneda') or 'USD').strip().upper()

                monto = float(p.get('monto_pagado') or 0)
                tc = float(p.get('tasa_cambio') or 3.80)
                if tc <= 0:
                    tc = 3.80
                total_gastos += _convertir(monto, moneda, tc)
        except Exception as e:
            st.warning(f"No se pudieron cargar los gastos operativos: {e}")
    elif df_gastos_op is not None and not df_gastos_op.empty and 'total' in df_gastos_op.columns:
        total_gastos = float(df_gastos_op['total'].sum())

    utilidad = total_ingresos - total_gastos
    margen = (utilidad / total_ingresos * 100) if total_ingresos > 0 else 0

    # --- SCORECARDS ---
    sc1, sc2, sc3 = st.columns(3)
    sc1.metric("Total Ingresos (Ventas)", f"{simbolo}{total_ingresos:,.2f}", delta="Cifra Bruta",
               help="Ventas cuya fecha de VENTA cae en el rango seleccionado.")
    sc2.metric("Total Gastos Operativos", f"{simbolo}{total_gastos:,.2f}", delta_color="inverse",
               help="Costos de las ventas cuyo VIAJE (fecha de inicio) cae en el rango seleccionado. "
                    "No es necesariamente el mismo grupo de ventas que Ingresos.")
    sc3.metric("Utilidad Operativa", f"{simbolo}{utilidad:,.2f}", delta=f"{margen:.1f}% margen")

    # --- WATERFALL CHART ---
    fig_wf = go.Figure(go.Waterfall(
        name="Flujo", orientation="v",
        measure=["relative", "relative", "total"],
        x=["Ingresos Ventas", "Costos Operativos", "Utilidad Neta"],
        textposition="outside",
        text=[f"{simbolo}{total_ingresos/1000:.1f}k", f"-{simbolo}{total_gastos/1000:.1f}k", f"{simbolo}{utilidad/1000:.1f}k"],
        y=[total_ingresos, -total_gastos, utilidad],
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        decreasing={"marker": {"color": "#EF5350"}},
        increasing={"marker": {"color": "#66BB6A"}},
        totals={"marker": {"color": "#42A5F5"}}
    ))
    fig_wf.update_layout(title=f"Cascada de Rentabilidad Global ({moneda_destino})", showlegend=False, height=420)
    st.plotly_chart(fig_wf, use_container_width=True)
    
    st.divider()

    # =========================================================
    # INFORME FINANCIERO COMPARATIVO MENSUAL (SEÚN BOCETO)
    # =========================================================
    st.subheader("📅 Informe Financiero Mensual (Comparativo Anual)")
    st.caption("Comparativa de Ingresos, Costos y Utilidad (Ganancia) mes a mes. Basado en fechas de ventas y pagos operativos.")
    
    # 1. Extraer y agrupar Ingresos por Mes
    ingresos_list = []
    if not df_ventas.empty:
        for _, row in df_ventas.iterrows():
            monto = float(row.get('precio_total_cierre') or row.get('monto_total') or 0)
            moneda = str(row.get('moneda') or 'USD').strip().upper()
            tc = float(row.get('tipo_cambio') or 3.80)
            if tc <= 0: tc = 3.80
            
            monto_usd = monto / tc if moneda == 'PEN' else monto
            
            fecha_str = row.get('fecha_venta')
            if pd.isna(fecha_str) or not fecha_str:
                continue
            
            try:
                # Extraemos 'YYYY-MM'
                mes = pd.to_datetime(str(fecha_str).split('T')[0]).strftime('%Y-%m')
                ingresos_list.append({'mes': mes, 'Ingresos': monto_usd})
            except:
                pass

    # 2. Extraer y agrupar Gastos por Mes
    gastos_list = []
    if supabase_client is not None:
        try:
            res_op = supabase_client.table('pago_operativo').select('fecha_pago, monto_pagado, moneda, tasa_cambio').execute()
            for p in (res_op.data or []):
                moneda = str(p.get('moneda') or 'USD').strip().upper()
                
                # Filtrar gastos por moneda para la gráfica mensual
                if filtro_moneda == "Soles (PEN)" and moneda != 'PEN': continue
                if filtro_moneda == "Dólares (USD)" and moneda != 'USD': continue

                monto = float(p.get('monto_pagado') or 0)
                tc = float(p.get('tasa_cambio') or 3.80)
                if tc <= 0: tc = 3.80
                
                monto_usd = monto / tc if moneda == 'PEN' else monto
                
                fecha_str = p.get('fecha_pago')
                if not fecha_str:
                    continue
                    
                try:
                    mes = pd.to_datetime(str(fecha_str).split('T')[0]).strftime('%Y-%m')
                    gastos_list.append({'mes': mes, 'Costos': monto_usd})
                except:
                    pass
        except Exception as e:
            pass

    df_ingresos = pd.DataFrame(ingresos_list)
    df_gastos = pd.DataFrame(gastos_list)
    
    if not df_ingresos.empty:
        df_ingresos = df_ingresos.groupby('mes')['Ingresos'].sum().reset_index()
    else:
        df_ingresos = pd.DataFrame(columns=['mes', 'Ingresos'])
        
    if not df_gastos.empty:
        df_gastos = df_gastos.groupby('mes')['Costos'].sum().reset_index()
    else:
        df_gastos = pd.DataFrame(columns=['mes', 'Costos'])
        
    # Unir ambos DataFrames
    df_mensual = pd.merge(df_ingresos, df_gastos, on='mes', how='outer').fillna(0).sort_values('mes')
    
    if not df_mensual.empty:
        # Calcular Utilidad (Ingresos - Costos)
        df_mensual['Utilidad'] = df_mensual['Ingresos'] - df_mensual['Costos']
        
        # Mapear nombres de meses legibles
        meses_nombres = {
            '01': 'Enero', '02': 'Febrero', '03': 'Marzo', '04': 'Abril',
            '05': 'Mayo', '06': 'Junio', '07': 'Julio', '08': 'Agosto',
            '09': 'Septiembre', '10': 'Octubre', '11': 'Noviembre', '12': 'Diciembre'
        }
        df_mensual['Mes_Nombre'] = df_mensual['mes'].apply(lambda x: f"{meses_nombres.get(x.split('-')[1], '')} {x.split('-')[0]}")
        
        # --- TABLA COMPARATIVA (TIPO BOCETO) ---
        # Pivotar para que las columnas sean los meses y las filas los conceptos
        df_pivot = df_mensual.set_index('Mes_Nombre')[['Ingresos', 'Costos', 'Utilidad']].T
        
        st.markdown("**1. Tabla Resumen por Mes (USD)**")
        st.dataframe(df_pivot.style.format("${:,.2f}"), use_container_width=True)
        
        # --- GRÁFICA DE LÍNEAS TIPO CURVA ---
        st.markdown("**2. Evolución y Tendencia de Utilidad**")
        fig_line = px.line(df_mensual, x='Mes_Nombre', y=['Ingresos', 'Costos', 'Utilidad'], 
                           markers=True,
                           labels={'value': 'Monto (USD)', 'Mes_Nombre': 'Mes', 'variable': 'Categoría'},
                           color_discrete_sequence=['#42A5F5', '#EF5350', '#66BB6A'])
        fig_line.update_traces(line_shape='spline', line_width=3, marker=dict(size=8)) # Curvas suaves como en el boceto
        fig_line.update_layout(legend_title_text='Flujo', hovermode="x unified")
        st.plotly_chart(fig_line, use_container_width=True)
        
        # --- GRÁFICO COMPARATIVO DE BARRAS ---
        st.markdown("**3. Comparativo Anual de Barras**")
        fig_bar = px.bar(df_mensual, x='Mes_Nombre', y=['Ingresos', 'Costos', 'Utilidad'], 
                         barmode='group',
                         labels={'value': 'Monto (USD)', 'Mes_Nombre': 'Mes', 'variable': 'Categoría'},
                         color_discrete_sequence=['#90CAF9', '#EF9A9A', '#A5D6A7'])
        fig_bar.update_layout(legend_title_text='Flujo')
        st.plotly_chart(fig_bar, use_container_width=True)
        
    else:
        st.info("No hay suficientes datos de ingresos o costos para generar el reporte comparativo mensual.")


def render_informe_mensual_vendido_operado(supabase_client):
    """Informe mensual para Contabilidad: Pax Vendidos vs Pax Operados, por pasajero/grupo.
    Reemplaza el armado manual en Excel: jala los datos directo del sistema."""
    st.subheader("📊 Informe Mensual: Vendidos vs Operados", divider='blue')
    st.caption("Reemplaza el reporte manual de Excel. Los montos se muestran en su moneda original (no se mezcla USD con PEN).")

    from datetime import date
    import calendar

    hoy = date.today()
    c_anio, c_mes, c_tipo = st.columns(3)
    with c_anio:
        anio = c_anio.selectbox("Año", list(range(hoy.year - 2, hoy.year + 1)), index=2, key="inf_mv_anio")
    with c_mes:
        meses_nombres = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio",
                          "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        mes_idx = c_mes.selectbox("Mes", list(range(1, 13)), index=hoy.month - 1,
                                   format_func=lambda m: meses_nombres[m - 1], key="inf_mv_mes")
    with c_tipo:
        filtro_tipo = c_tipo.selectbox("Tipo de Venta", ["Todos", "Directas (B2C)", "Agencias (B2B)"], key="inf_mv_tipo")

    fecha_ini = date(anio, mes_idx, 1)
    fecha_fin = date(anio, mes_idx, calendar.monthrange(anio, mes_idx)[1])

    tab_vend, tab_op = st.tabs(["🛍️ Pax Vendidos", "🧳 Pax Operados"])

    with tab_vend:
        _render_pax_vendidos(supabase_client, fecha_ini, fecha_fin, filtro_tipo)

    with tab_op:
        _render_pax_operados(supabase_client, fecha_ini, fecha_fin, filtro_tipo)


def _nombre_cliente(v):
    cli = v.get('cliente') or {}
    if isinstance(cli, list):
        cli = cli[0] if cli else {}
    return cli.get('nombre') or 'Cliente'


def _filtrar_tipo_venta(ventas, filtro_tipo):
    """Filtra una lista de ventas (dicts) por segmento B2C/B2B según id_agencia_aliada."""
    if filtro_tipo == "Directas (B2C)":
        return [v for v in ventas if not v.get('id_agencia_aliada')]
    if filtro_tipo == "Agencias (B2B)":
        return [v for v in ventas if v.get('id_agencia_aliada')]
    return ventas


def _render_pax_vendidos(supabase_client, fecha_ini, fecha_fin, filtro_tipo="Todos"):
    """Ventas registradas (fecha_venta) dentro del período, por pasajero/grupo."""
    try:
        res = supabase_client.table('venta').select(
            'id_venta, precio_total_cierre, moneda, num_pasajeros, fecha_venta, id_agencia_aliada, cliente(nombre)'
        ).neq('estado_venta', 'CANCELADO') \
         .gte('fecha_venta', fecha_ini.isoformat()) \
         .lte('fecha_venta', fecha_fin.isoformat()) \
         .execute()
    except Exception as e:
        st.error(f"No se pudo cargar Ventas: {e}")
        return

    ventas = _filtrar_tipo_venta(res.data or [], filtro_tipo)
    if not ventas:
        st.info("No hay ventas registradas en este período.")
        return

    rows = []
    for v in ventas:
        pax = v.get('num_pasajeros') or 1
        rows.append({
            "Pasajero": f"{_nombre_cliente(v)} X {pax}",
            "Monto": float(v.get('precio_total_cierre') or 0),
            "Moneda": str(v.get('moneda') or 'USD').strip().upper()
        })

    df = pd.DataFrame(rows)

    tot_usd = df.loc[df['Moneda'] == 'USD', 'Monto'].sum()
    tot_pen = df.loc[df['Moneda'] == 'PEN', 'Monto'].sum()
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Vendido (USD)", f"$ {tot_usd:,.2f}")
    c2.metric("Total Vendido (PEN)", f"S/ {tot_pen:,.2f}")
    c3.metric("Ventas del Período", f"{len(df):,}")

    fig = px.bar(
        df, x='Pasajero', y='Monto', color='Moneda', barmode='group',
        title="Monto Vendido por Pasajero/Grupo",
        color_discrete_map={'USD': '#42A5F5', 'PEN': '#66BB6A'}
    )
    fig.update_layout(xaxis_tickangle=-45, height=450)
    st.plotly_chart(fig, use_container_width=True)

    # --- TABLA (mismo formato que el Excel: MONTO S/. | MONTO $) ---
    st.markdown("##### 📋 Detalle en Tabla")
    df_tabla = df.pivot_table(index='Pasajero', columns='Moneda', values='Monto', aggfunc='sum').reset_index()
    df_tabla = df_tabla.rename(columns={'PEN': 'MONTO S/.', 'USD': 'MONTO $'})
    for col in ['MONTO S/.', 'MONTO $']:
        if col not in df_tabla.columns:
            df_tabla[col] = 0.0
    df_tabla = df_tabla[['Pasajero', 'MONTO S/.', 'MONTO $']].fillna(0.0)
    fila_total = pd.DataFrame([{
        'Pasajero': 'TOTAL',
        'MONTO S/.': df_tabla['MONTO S/.'].sum(),
        'MONTO $': df_tabla['MONTO $'].sum()
    }])
    df_tabla = pd.concat([df_tabla, fila_total], ignore_index=True)
    st.dataframe(
        df_tabla.style.format({'MONTO S/.': 'S/ {:,.2f}', 'MONTO $': '$ {:,.2f}'}),
        use_container_width=True, hide_index=True
    )


def _render_pax_operados(supabase_client, fecha_ini, fecha_fin, filtro_tipo="Todos"):
    """Ventas cuyo viaje (fecha_inicio) cae dentro del período: Ingreso, Costo y Utilidad por pasajero/grupo.
    El costo se convierte siempre a la moneda de la venta (nunca se descarta un costo por estar en otra moneda)."""
    try:
        res = supabase_client.table('venta').select(
            'id_venta, precio_total_cierre, moneda, tipo_cambio, num_pasajeros, fecha_inicio, id_agencia_aliada, cliente(nombre)'
        ).neq('estado_venta', 'CANCELADO') \
         .gte('fecha_inicio', fecha_ini.isoformat()) \
         .lte('fecha_inicio', fecha_fin.isoformat()) \
         .execute()
    except Exception as e:
        st.error(f"No se pudo cargar Operaciones: {e}")
        return

    ventas = _filtrar_tipo_venta(res.data or [], filtro_tipo)
    if not ventas:
        st.info("No hay viajes operados en este período.")
        return

    ids_venta = [v['id_venta'] for v in ventas]
    costos_por_venta = {}
    try:
        res_costos = supabase_client.table('venta_servicio_proveedor').select(
            'id_venta, costo_unitario, cantidad_pax, moneda'
        ).in_('id_venta', ids_venta).execute()
        for c in (res_costos.data or []):
            vid = c['id_venta']
            mon = str(c.get('moneda') or 'USD').strip().upper()
            monto_c = float(c.get('costo_unitario') or 0) * int(c.get('cantidad_pax') or 1)
            costos_por_venta.setdefault(vid, {}).setdefault(mon, 0.0)
            costos_por_venta[vid][mon] += monto_c
    except Exception as e:
        st.warning(f"No se pudieron cargar los costos operativos: {e}")

    rows = []
    for v in ventas:
        pax = v.get('num_pasajeros') or 1
        ingreso = float(v.get('precio_total_cierre') or 0)
        moneda_v = str(v.get('moneda') or 'USD').strip().upper()
        tc = float(v.get('tipo_cambio') or 3.80) or 3.80

        costo_total = 0.0
        for mon_c, monto_c in costos_por_venta.get(v['id_venta'], {}).items():
            if mon_c == moneda_v:
                costo_total += monto_c
            elif moneda_v == 'PEN':
                costo_total += monto_c * tc  # costo en USD -> PEN
            else:
                costo_total += monto_c / tc  # costo en PEN -> USD

        rows.append({
            "Pasajero": f"{_nombre_cliente(v)} X {pax}",
            "Ingreso": ingreso,
            "Costo": costo_total,
            "Utilidad": ingreso - costo_total,
            "Moneda": moneda_v
        })

    df = pd.DataFrame(rows)

    monedas_presentes = [m for m in ['USD', 'PEN'] if (df['Moneda'] == m).any()]
    if not monedas_presentes:
        st.info("No hay datos para mostrar.")
        return

    moneda_vista = st.radio(
        "Ver en:", monedas_presentes,
        format_func=lambda m: "Dólares (USD)" if m == 'USD' else "Soles (PEN)",
        horizontal=True, key="inf_mv_moneda_op"
    )
    simbolo = '$' if moneda_vista == 'USD' else 'S/'

    df_v = df[df['Moneda'] == moneda_vista]

    c1, c2, c3 = st.columns(3)
    c1.metric(f"Ingreso Total ({moneda_vista})", f"{simbolo} {df_v['Ingreso'].sum():,.2f}")
    c2.metric(f"Costo Total ({moneda_vista})", f"{simbolo} {df_v['Costo'].sum():,.2f}")
    c3.metric(f"Utilidad Total ({moneda_vista})", f"{simbolo} {df_v['Utilidad'].sum():,.2f}")

    df_melt = df_v.melt(id_vars=['Pasajero'], value_vars=['Ingreso', 'Costo', 'Utilidad'],
                         var_name='Concepto', value_name='Monto')
    fig = px.bar(
        df_melt, x='Pasajero', y='Monto', color='Concepto', barmode='group',
        title=f"Ingreso / Costo / Utilidad por Pasajero/Grupo Operado ({moneda_vista})",
        color_discrete_map={'Ingreso': '#42A5F5', 'Costo': '#EF5350', 'Utilidad': '#66BB6A'}
    )
    fig.update_layout(xaxis_tickangle=-45, height=450)
    st.plotly_chart(fig, use_container_width=True)

    # --- TABLA (mismo formato que el Excel: NOMBRE | MONTO | COSTO | UTILIDAD) ---
    st.markdown("##### 📋 Detalle en Tabla")
    df_tabla = df_v[['Pasajero', 'Ingreso', 'Costo', 'Utilidad']].copy()
    fila_total = pd.DataFrame([{
        'Pasajero': 'TOTAL',
        'Ingreso': df_tabla['Ingreso'].sum(),
        'Costo': df_tabla['Costo'].sum(),
        'Utilidad': df_tabla['Utilidad'].sum()
    }])
    df_tabla = pd.concat([df_tabla, fila_total], ignore_index=True)
    fmt = f"{simbolo} " + "{:,.2f}"
    st.dataframe(
        df_tabla.style.format({'Ingreso': fmt, 'Costo': fmt, 'Utilidad': fmt}),
        use_container_width=True, hide_index=True
    )
