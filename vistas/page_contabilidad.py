# vistas/page_contabilidad.py
import streamlit as st
import pandas as pd
from datetime import date
import io
from controllers.reporte_controller import ReporteController

# Renderiza el Botón para el PDF del Itinerario Simple.
def render_itinerary_simple_download(render):
    if not render:
        st.warning("No hay datos de itinerario para descargar.")
        return

    from controllers.pdf_controller import PDFController
    pdf_ctrl = PDFController()
    
    from controllers.excel_controller import ExcelController
    xl_ctrl = ExcelController()
    
    # Extraer parámetros de enriquecimiento
    nombre_pax = render.get('nombre_pasajero')
    total_pax = render.get('num_pasajeros')
    
    with st.container(border=True):
        st.markdown(f"#### 📄 Resumen de Viaje: {render.get('titulo', 'Sin Título')}")
        st.info("Este documento es una versión simplificada ideal para el control operativo de servicios.")
        
        c1, c2 = st.columns(2)
        
        with c1:
            # Generar el PDF en memoria
            pdf_buffer = pdf_ctrl.generar_itinerario_simple_pdf(render)
            if pdf_buffer:
                st.download_button(
                    label="📥 Bajar Resumen (PDF Simple)",
                    data=pdf_buffer,
                    file_name=f"resumen_viaje_{render.get('titulo', 'itinerario')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
        
        with c2:
            # Generar el Excel en memoria (Reporte Logístico Unificado)
            xlsx_buffer = xl_ctrl.generar_resumen_itinerario_xlsx(render, nombre_cliente=nombre_pax, num_pax=total_pax)
            if xlsx_buffer:
                st.download_button(
                    label="📊 Bajar Resumen (Excel XLSX)",
                    data=xlsx_buffer,
                    file_name=f"auditoria_{render.get('titulo','itin')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        
        if not pdf_buffer and not xlsx_buffer:
            st.error("No se pudo generar el documento en este momento.")

def render_operational_master_download(controller, id_venta):
    """Renderiza el GRAN BOTÓN ROJO para el reporte maestro (Excel)."""
    from controllers.excel_controller import ExcelController
    from controllers.operaciones_controller import OperacionesController
    from controllers.venta_controller import VentaController
    from datetime import date
    
    xl_ctrl = ExcelController()
    op_ctrl = OperacionesController(controller.client)
    
    # Generar el reporte maestro con toda la data junta
    if st.button("📊 Generar Informe Maestro (Operaciones + Contabilidad)", type="primary", use_container_width=True):
        with st.spinner("Compilando Reporte Maestro..."):
            try:
                # fallback: Obtener toda la data necesaria aquí mismo
                res_v = controller.client.table('venta').select('*, cliente(nombre, lead(numero_celular))').eq('id_venta', id_venta).single().execute()
                if not res_v.data:
                    st.error("No se pudo recuperar la información de la venta.")
                    return
                    
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
                res_p = controller.client.table('pago').select('monto_pagado').eq('id_venta', id_venta).execute()
                v_data['monto_pagado'] = sum(float(p['monto_pagado'] or 0) for p in res_p.data)

                # 3. Obtener Itinerario Logístico (Usando métodos estables del controller)
                itinerario = op_ctrl.get_servicios_rango_fechas(date(2000,1,1), date(2100,1,1))
                it_venta = [s for s in itinerario if s['ID Venta'] == id_venta]

                # 4. Obtener Pasajeros
                pasajeros = op_ctrl.pasajero_model.get_by_venta_id(id_venta)

                # 5. Obtener Liquidación Detallada (Costos)
                liquidaciones = op_ctrl.get_liquidaciones_venta(id_venta)

                data_maestra = {
                    "venta": v_data,
                    "itinerario": it_venta,
                    "pasajeros": pasajeros,
                    "liquidaciones": liquidaciones
                }

                xlsx_maestro = xl_ctrl.generar_hoja_servicio_maestra_xlsx(data_maestra)
                
                if xlsx_maestro:
                    st.download_button(
                        label="✅ ¡Reporte Listo! Haz clic para Descargar",
                        data=xlsx_maestro,
                        file_name=f"MAESTRO_{id_venta}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                    st.success("Reporte generado. Recuerda que contiene: Resumen Financiero, Logística, Liquidaciones y Rooming List.")
            except Exception as e:
                st.error(f"Error generando Hoja de Servicio: {e}")

def mostrar_pagina(funcionalidad_seleccionada, rol_actual=None, user_id=None, supabase_client=None):
    if supabase_client:
        st.session_state['reporte_controller'] = ReporteController(supabase_client)

    st.title(f"📝 Gestión Contable")
    st.markdown("---")
    
    if funcionalidad_seleccionada == "Gestión de Registros":
        tab1, tab2, tab3 = st.tabs([
            "📊 Estructurador Financiero", 
            "💰 Cuentas por Cobrar",
            "🚐 Pagos Operativos (Proveedores)"
        ])
        
        with tab1:
            estructurador_liquidacion_pro(st.session_state['reporte_controller'])
            
        with tab2:
            dashboard_cuentas_por_cobrar_unified(supabase_client)
            
        with tab3:
            dashboard_pagos_operativos(supabase_client)
    else:
        st.info("Utilice el Dashboard Contable para ver reportes.")

def dashboard_pagos_operativos(supabase_client):
    """Dashboard para controlar desembolsos a guías, transportes y agencias (Proveedores)."""
    st.subheader("🚐 Control de Pagos Operativos", divider='green')
    
    from controllers.pago_operativo_controller import PagoOperativoController
    po_ctrl = PagoOperativoController(supabase_client)
    
    # 1. Resumen de Saldos Pendientes
    st.write("### 📋 Resumen de Saldos por Proveedor")
    with st.spinner("Calculando balances con proveedores..."):
        df_saldos = po_ctrl.obtener_resumen_saldos_proveedores()
        if not df_saldos.empty:
            # Resaltar deudas
            def highlight_saldo(val):
                color = 'red' if val > 0 else 'green'
                return f'color: {color}; font-weight: bold'
            
            st.dataframe(
                df_saldos.style.applymap(highlight_saldo, subset=['Saldo Pendiente']),
                use_container_width=True,
                hide_index=True
            )
            
            total_deuda_pen = df_saldos[df_saldos['Moneda'] == 'PEN']['Saldo Pendiente'].sum()
            total_deuda_usd = df_saldos[df_saldos['Moneda'] == 'USD']['Saldo Pendiente'].sum()
            
            c1, c2 = st.columns(2)
            c1.metric("Deuda Total (S/.)", f"S/ {total_deuda_pen:,.2f}")
            c2.metric("Deuda Total ($)", f"$ {total_deuda_usd:,.2f}")
        else:
            st.info("No hay costos operativos registrados o todos están saldados.")

    st.divider()

    # 2. Formulario de Registro de Pago
    with st.expander("➕ Registrar Nuevo Pago a Proveedor", expanded=True):
        st.info("Utilice este formulario para descargar deuda con un proveedor específico.")
        
        # Obtener lista de proveedores
        res_prov = supabase_client.table('proveedor').select('id_proveedor, nombre_comercial').eq('activo', True).execute()
        mapa_prov = {p['nombre_comercial']: p['id_proveedor'] for p in res_prov.data} if res_prov.data else {}
        
        col1, col2 = st.columns(2)
        prov_sel = col1.selectbox("1. Seleccione Proveedor:", ["--- Seleccione ---"] + list(mapa_prov.keys()))
        
        if prov_sel != "--- Seleccione ---":
            id_prov = mapa_prov[prov_sel]
            
            # Intentar buscar ventas/servicios pendientes para este proveedor para ayudar a la vinculación
            res_serv = supabase_client.table('venta_servicio_proveedor')\
                .select('id_venta, n_linea, tipo_servicio, venta(tour_nombre, nombre_cliente)')\
                .eq('id_proveedor', id_prov)\
                .execute()
            
            opciones_serv = ["--- Pago General (No vinculado) ---"]
            mapa_serv = {}
            if res_serv.data:
                for s in res_serv.data:
                    v_info = s.get('venta') or {}
                    lbl = f"Venta {s['id_venta']} | {v_info.get('nombre_cliente', 'ID '+str(s['id_venta']))} - {s['tipo_servicio']} ({v_info.get('tour_nombre', 'Tour')})"
                    opciones_serv.append(lbl)
                    mapa_serv[lbl] = (s['id_venta'], s['n_linea'])
            
            serv_sel = col2.selectbox("2. Vincular a Servicio (Opcional):", opciones_serv)
            
            # --- Inteligencia de Moneda ---
            moneda_deuda = "USD" # Default
            if serv_sel != opciones_serv[0]:
                # Buscar moneda pactada para este servicio
                id_v_tmp, nl_tmp = mapa_serv[serv_sel]
                res_mon = supabase_client.table('venta_servicio_proveedor')\
                    .select('moneda')\
                    .eq('id_venta', id_v_tmp)\
                    .eq('n_linea', nl_tmp)\
                    .limit(1).execute()
                if res_mon.data:
                    moneda_deuda = res_mon.data[0]['moneda']
            
            st.markdown(f"Deuda pactada en: **{moneda_deuda}**")
            st.markdown("---")
            
            c3, c4, c5 = st.columns(3)
            monto_pago = c3.number_input("Monto a Entregar:", min_value=0.01, step=50.0)
            moneda_pago = c4.selectbox("Moneda del Pago:", ["PEN", "USD", "EUR"], index=0 if moneda_deuda == "PEN" else 1)
            fecha = c5.date_input("Fecha:", date.today())
            
            # Cálculo de Equivalencia
            tasa_cambio = 1.0
            monto_amortizado = monto_pago
            
            if moneda_pago != moneda_deuda:
                st.warning(f"⚠️ **Conversión Necessaria**: Pagas en {moneda_pago} una deuda en {moneda_deuda}.")
                col_tc1, col_tc2 = st.columns(2)
                
                # Sugerir TC
                from services.exchange_service import ExchangeService
                tc_sugerido = 1.0
                if moneda_pago == "PEN" and moneda_deuda == "USD": tc_sugerido = ExchangeService.get_current_tc()
                elif moneda_pago == "USD" and moneda_deuda == "PEN": tc_sugerido = 1 / ExchangeService.get_current_tc()
                
                tasa_cambio = col_tc1.number_input(f"TC ({moneda_pago} a {moneda_deuda}):", min_value=0.01, value=float(tc_sugerido), format="%.4f")
                monto_amortizado = round(monto_pago / tasa_cambio, 2)
                col_tc2.metric(f"Monto que descuenta de la deuda ({moneda_deuda}):", f"{monto_amortizado:,.2f}")
            else:
                st.success(f"Monedas coinciden. Se descuentan {moneda_deuda} {monto_pago:,.2f} íntegros.")

            c6, c7 = st.columns(2)
            metodo = c6.selectbox("Método de Pago:", ["YAPE", "PLIN", "TRANSFERENCIA", "EFECTIVO", "OTRO"])
            notas = c7.text_input("Observaciones / Nro Operación:", placeholder="Ej: Pago de guiado City Tour")
            
            voucher = st.text_input("🔗 Link al Voucher (Opcional):", placeholder="https://supabase-storage...")

            if st.button("🧧 Confirmar y Registrar Desembolso", type="primary", use_container_width=True):
                id_v, nl = (None, None)
                if serv_sel != opciones_serv[0]:
                    id_v, nl = mapa_serv[serv_sel]
                
                exito = po_ctrl.registrar_pago_operativo(
                    id_proveedor=id_prov,
                    id_venta=id_v,
                    n_linea=nl,
                    monto=monto_pago,
                    moneda=moneda_pago,
                    tasa_cambio=tasa_cambio,
                    monto_equivalente=monto_amortizado,
                    fecha=fecha.isoformat(),
                    metodo=metodo,
                    voucher_url=voucher,
                    notas=notas,
                    id_usuario=None
                )

                
                if exito:
                    st.success(f"✅ Pago de {moneda} {monto:,.2f} registrado para {prov_sel}.")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("No se pudo registrar el pago. Verifique los campos.")

    # 3. Historial de Pagos (Recientes)
    with st.expander("🔎 Historial de Pagos Recientes"):
        if prov_sel != "--- Seleccione ---":
            st.write(f"Historial para **{prov_sel}**:")
            df_hist = po_ctrl.obtener_historial_pagos_proveedor(mapa_prov[prov_sel])
            if not df_hist.empty:
                st.dataframe(df_hist, use_container_width=True, hide_index=True)
            else:
                st.caption("No se encontraron pagos anteriores para este proveedor.")
        else:
            st.caption("Seleccione un proveedor para ver su historial.")

def estructurador_liquidacion_pro(controller):
    """
    Herramienta avanzada para estructurar liquidaciones (Versión Contabilidad).
    Permite cargar ventas y asignar costos/proveedores directamente.
    """
    from datetime import date
    st.subheader("📊 Estructurador de Liquidación Profesional", divider='rainbow')

    # Forzar recarga siempre: descartar cache de versiones anteriores del código
    if 'simulador_contable_adv_data' not in st.session_state:
        st.session_state['simulador_contable_adv_data'] = []
    # Borrar el ID cacheado para que al seleccionar la venta recargue con la lógica nueva
    st.session_state.pop('last_loaded_id_venta_acc', None)

    st.info("💡 Selecciona la venta para cargar su desglose de servicios e itinerario.")
    
    # Barra de ventas
    from controllers.venta_controller import VentaController
    vc = VentaController(controller.client)
    
    c_tipo, c_pax = st.columns([1, 2])
    with c_tipo:
        tipo_v = st.selectbox("1️⃣ Tipo:", ["--- Seleccione ---", "🏢 B2B (Agencias)", "👤 B2C (Directas)"], key="acc_sel_tipo")
    
    ventas_data = []
    if tipo_v == "🏢 B2B (Agencias)":
        agencias = vc.obtener_agencias_aliadas()
        nombres_ag = [a['nombre'] for a in agencias]
        mapa_ag = {a['nombre']: a['id_agencia'] for a in agencias}
        ag_sel = st.selectbox("2️⃣ Agencia:", ["--- Seleccione ---"] + nombres_ag, key="acc_sel_ag")
        if ag_sel != "--- Seleccione ---":
            ventas_data = vc.obtener_ventas_agencia(mapa_ag[ag_sel])
    elif tipo_v == "👤 B2C (Directas)":
        ventas_data = vc.obtener_ventas_directas()

    if ventas_data:
        opciones_p = [f"{v['nombre_cliente']} | {v.get('tour_nombre', 'Sin Tour')} ({v['id_venta']})" for v in ventas_data]
        mapa_v = {opciones_p[i]: v for i, v in enumerate(ventas_data)}
        
        with c_pax:
            p_sel = st.selectbox("2️⃣ Cargar Venta:", ["--- Seleccione ---"] + opciones_p, key="acc_sel_pax")
        
        if p_sel != "--- Seleccione ---":
            v_act = mapa_v.get(p_sel)
            
            # Solo cargar si ha cambiado la venta
            if st.session_state.get('last_loaded_id_venta_acc') != v_act['id_venta']:
                from controllers.operaciones_controller import OperacionesController
                op_ctrl = OperacionesController(controller.client)
                
                detalles = vc.obtener_detalles_itinerario_venta(v_act['id_venta'])
                # Obtener liquidaciones reales para sumar los costos
                liquidaciones = op_ctrl.get_liquidaciones_venta(v_act['id_venta'])
                
                # ==============================================================
                # LÓGICA DE CONVERSIÓN DEFINITIVA (corregida)
                # El problema era: 100 USD + 20 USD + 100 PEN = 220 (mezcla incorrecta)
                # La solución: convertir CADA liquidación a PEN usando su propio
                # campo moneda_costo (que SÍ está guardado correctamente en
                # venta_servicio_proveedor) ANTES de sumar por n_linea.
                # ==============================================================
                tc_venta = float(v_act.get('tipo_cambio') or 3.70)

                # Sumar costos por n_linea, convirtiendo cada fila a PEN individualmente
                mapa_costos_pen = {}
                for liq in liquidaciones:
                    nl = liq.get('n_linea')
                    if nl is not None:
                        costo_liq    = float(liq.get('costo_unitario') or 0.0)
                        # CAMPO CORRECTO: en venta_servicio_proveedor la columna es 'moneda' (no 'moneda_costo')
                        moneda_liq   = (liq.get('moneda') or 'PEN').strip().upper()
                        # Convertir a PEN si es USD
                        costo_en_pen = round(costo_liq * tc_venta, 4) if moneda_liq == 'USD' else costo_liq
                        mapa_costos_pen[nl] = mapa_costos_pen.get(nl, 0.0) + costo_en_pen

                filas = []
                for d in (detalles or []):
                    # El mapa ya tiene todo en PEN → se muestra directamente
                    costo_pen = round(
                        mapa_costos_pen.get(d['n_linea'],
                                           float(d.get('costo_applied') or 0.0)),
                        2
                    )
                    filas.append({
                        "FECHA"    : date.fromisoformat(d['fecha_servicio']),
                        "HORA"     : d.get('hora_inicio', '--:--'),
                        "SERVICIO" : d.get('observacion') or "Servicio",
                        "PAX"      : d.get('cantidad', 1),
                        "COSTO_PEN": costo_pen,
                        "id_venta" : d['id_venta'],
                        "n_linea"  : d['n_linea']
                    })

                st.session_state['simulador_contable_adv_data'] = filas
                st.session_state['tc_venta_acc']             = tc_venta
                st.session_state['es_usd_acc']               = False  # ya convertido, no re-convertir
                st.session_state['last_loaded_id_venta_acc'] = v_act['id_venta']
                # No hacemos st.rerun() aquí porque causa un bucle infinito al renderizar la tabla de corrido

            # --- 📥 AUDITORÍA DE ITINERARIO (BOTÓN DE DESCARGA) ---
            id_it_dig = v_act.get('id_itinerario_digital')
            if id_it_dig:
                with st.expander("📄 Ver Itinerario Original para Auditoría", expanded=False):
                    res_it = controller.client.table('itinerario_digital').select('datos_render').eq('id_itinerario_digital', id_it_dig).single().execute()
                    if res_it.data:
                        render_data = res_it.data['datos_render']
                        if isinstance(render_data, str):
                            import json
                            render_data = json.loads(render_data)
                        
                        # --- ENRIQUECIMIENTO ---
                        if isinstance(render_data, dict):
                            render_data['fecha_inicio'] = v_act.get('fecha_inicio') or render_data.get('fecha_inicio')
                            render_data['fecha_fin'] = v_act.get('fecha_fin') or render_data.get('fecha_fin')
                            render_data['nombre_pasajero'] = v_act.get('cliente_nombre') or render_data.get('nombre_pasajero')
                            render_data['num_pasajeros'] = v_act.get('num_pasajeros') or v_act.get('adultos', 1)
                            render_data['num_ninos'] = v_act.get('ninos') or 0
                            
                            live_tours = vc.obtener_detalles_itinerario_venta(v_act['id_venta'])
                            if live_tours:
                                itin_list = render_data.get('itinerario_detalles') or render_data.get('days') or []
                                if isinstance(itin_list, list):
                                    for i, t_live in enumerate(live_tours):
                                        if i < len(itin_list) and isinstance(itin_list[i], dict):
                                            itin_list[i]['fecha'] = t_live.get('fecha_servicio') or itin_list[i].get('fecha')
                                    render_data['itinerario_detalles'] = itin_list

                        render_itinerary_simple_download(render_data)
                        st.markdown("---")
                        render_operational_master_download(controller, v_act['id_venta'])
            else:
                st.caption("Esta venta no tiene un itinerario digital vinculado.")

    # Editor estilo Excel
    df = pd.DataFrame(st.session_state['simulador_contable_adv_data'])
    if not df.empty and 'FECHA' in df.columns:
        df.sort_values(by='FECHA', inplace=True)

    tc_usado = st.session_state.get('tc_venta_acc', 3.70)
    es_usd   = st.session_state.get('es_usd_acc', False)

    # Nota informativa de moneda
    if es_usd:
        st.caption(f"💱 Venta en **USD** · TC aplicado: 1 USD = S/ {tc_usado:.4f} · Costos convertidos a Soles.")
    elif not df.empty:
        st.caption("🇵🇪 Venta en **Soles (PEN)** · Los costos se muestran tal cual, sin conversión.")

    # Columna de costo según esquema activo
    col_costo = 'COSTO_PEN' if 'COSTO_PEN' in df.columns else ('TOTAL_PEN' if 'TOTAL_PEN' in df.columns else 'TOTAL')

    # Vista de solo lectura unificada en S/.
    cols_orden = [c for c in ("FECHA", "HORA", "SERVICIO", "PAX", col_costo) if c in df.columns]
    st.dataframe(
        df,
        column_order=cols_orden,
        column_config={
            "FECHA"    : st.column_config.DateColumn("Fecha", format="DD/MM/YYYY"),
            "HORA"     : st.column_config.TextColumn("Hora", width="small"),
            "SERVICIO" : st.column_config.TextColumn("Servicio", width="large"),
            "PAX"      : st.column_config.NumberColumn("Pax", format="%d"),
            "COSTO_PEN": st.column_config.NumberColumn("Costo (S/.)", format="S/ %.2f"),
            "TOTAL_PEN": st.column_config.NumberColumn("Costo (S/.)", format="S/ %.2f"),
            "TOTAL"    : st.column_config.NumberColumn("Costo (S/.)", format="S/ %.2f"),
        },
        use_container_width=True,
        hide_index=True
    )

    # Total en Soles
    t_costos = df[col_costo].sum() if not df.empty and col_costo in df.columns else 0.0
    st.divider()
    st.metric("COSTO TOTAL EN SOLES", f"S/ {t_costos:,.2f}")
    st.info("💡 Vista de auditoría — solo lectura. Todos los costos expresados en Soles (S/.).")

from controllers.venta_controller import VentaController

def herramienta_carga_masiva_pagos(supabase_client, key_suffix=""):
    """Herramienta compartida para carga masiva de pagos desde Excel."""
    st.markdown("### 📥 Carga Masiva de Pagos (Excel)")
    
    tipo_import = st.selectbox("1️⃣ Tipo:", ["B2B (Agencias)", "B2C (Directas)"], key=f"sel_tipo_import_{key_suffix}")
    st.info(f"Importando pagos para ventas tipo: **{tipo_import}**")

    with st.expander("📁 Subir Archivo y Plantilla", expanded=True):
        st.markdown("""
        Descargue la plantilla, complete los datos y suba el archivo. 
        Asegúrese de que el **ID Venta** sea válido en el sistema.
        """)
        
        # 1. Crear plantilla en memoria
        template_df = pd.DataFrame(columns=[
            "ID Venta", "Fecha", "Monto", "Moneda", "Metodo", "Tipo", "Comprobante", "TC"
        ])
        
        output = io.BytesIO()
        try:
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                template_df.to_excel(writer, index=False, sheet_name='PlantillaPagos')
            processed_data = output.getvalue()
            
            st.download_button(
                label="📄 Descargar Plantilla Excel",
                data=processed_data,
                file_name="plantilla_pagos_masivos.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"dl_btn_{key_suffix}",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Error al generar plantilla: {e}")
        
        st.divider()
        
        uploaded_file = st.file_uploader("Subir Excel de Pagos:", type=["xlsx", "xls", "csv"], key=f"uploader_pagos_{key_suffix}")
        
        if uploaded_file:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df_upload = pd.read_csv(uploaded_file)
                else:
                    df_upload = pd.read_excel(uploaded_file)
                
                st.write("### 🔍 Previsualización de Datos:")
                st.dataframe(df_upload, use_container_width=True, hide_index=True)
                
                if st.button("🧧 Procesar y Registrar Todo", type="primary", use_container_width=True, key=f"btn_proc_{key_suffix}"):
                    with st.spinner("Registrando pagos en el sistema..."):
                        vc = VentaController(supabase_client)
                        resultado = vc.vincular_pagos_masivos(df_upload)
                        
                        if resultado["exitos"] > 0:
                            st.success(f"✅ Se registraron {resultado['exitos']} pagos exitosamente.")
                        
                        if resultado["errores"]:
                            with st.expander("⚠️ Ver Detalles de Errores"):
                                for err in resultado["errores"]:
                                    st.error(err)
                        
                        if resultado["exitos"] > 0:
                            st.balloons()
                            st.rerun()
                            
            except Exception as e:
                st.error(f"Error al leer/procesar el archivo: {e}")

def dashboard_cuentas_por_cobrar_unified(supabase_client):
    """Dashboard unificado para controlar deudas (B2B y B2C)."""
    st.subheader("💰 Cuentas por Cobrar", divider='orange')
    
    # 1. Herramienta de Carga Masiva (Siempre visible arriba)
    herramienta_carga_masiva_pagos(supabase_client, "unified")
    st.divider()

    # 2. Selector de Contexto
    tipo_vista = st.radio(
        "Seleccione el tipo de cobro a gestionar:",
        ["💎 B2B (Agencias)", "👤 B2C (Directas)"],
        horizontal=True,
        key="sb_tipo_cobro_unified"
    )

    vc = VentaController(supabase_client)
    from controllers.excel_controller import ExcelController
    exc_ctrl = ExcelController()

    if "B2B" in tipo_vista:
        # Lógica B2B
        ventas = vc.obtener_todas_ventas_b2b()
        if not ventas:
            st.info("No hay ventas B2B registradas.")
            return

        ids_ventas = [v['id_venta'] for v in ventas]
        pagos = supabase_client.table('pago').select('id_venta, monto_moneda_venta').in_('id_venta', ids_ventas).execute().data
        
        mapa_pagos = {}
        for p in pagos:
            pid = p['id_venta']
            mapa_pagos[pid] = mapa_pagos.get(pid, 0) + (p['monto_moneda_venta'] or 0)

        data_agencias = {}
        lista_detalle = []
        for v in ventas:
            id_agencia = v.get('id_agencia_aliada')
            nombre_agencia = v.get('nombre_agencia', 'Sin Nombre')
            moneda = v.get('moneda', 'USD')
            monto = float(v.get('precio_total_cierre') or 0)
            pagado = float(mapa_pagos.get(v['id_venta'], 0))
            saldo = monto - pagado
            
            if id_agencia not in data_agencias:
                data_agencias[id_agencia] = {'Nombre': nombre_agencia, 'Total Ventas': 0.0, 'Cobrado': 0.0, 'Por Cobrar': 0.0, 'Count': 0, 'Moneda': moneda}
            
            data_agencias[id_agencia]['Total Ventas'] += monto
            data_agencias[id_agencia]['Cobrado'] += pagado
            data_agencias[id_agencia]['Por Cobrar'] += saldo
            data_agencias[id_agencia]['Count'] += 1
            
            lista_detalle.append({
                'Agencia': nombre_agencia,
                'Pasajero': v.get('nombre_cliente'),
                'Fecha Venta': v.get('fecha_venta'),
                f'Total ({moneda})': monto,
                f'A Cuenta ({moneda})': pagado,
                f'Saldo ({moneda})': saldo,
                'Estado': '✅ PAGADO' if saldo <= 0.1 else '🔴 DEBE'
            })
            
        total_deuda = sum(d['Por Cobrar'] for d in data_agencias.values())
        c1, c2 = st.columns(2)
        c1.metric("Total por Cobrar Agencias", f"${total_deuda:,.2f}")
        c2.metric("Agencias con Deuda", len([d for d in data_agencias.values() if d['Por Cobrar'] > 1]))

        # Botón Excel B2B
        df_detalle_rep = pd.DataFrame(lista_detalle)
        if not df_detalle_rep.empty:
            try:
                reporte_xlsx = exc_ctrl.generar_reporte_cuentas_cobrar_xlsx(df_detalle_rep)
                st.download_button(
                    label="📊 Descargar Informe de Cuentas B2B (Excel)",
                    data=reporte_xlsx,
                    file_name=f"reporte_cuentas_b2b_{date.today()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    key="btn_dl_b2b_unified"
                )
            except Exception as e:
                st.error(f"Error: {e}")

        st.write("### 🏢 Resumen por Agencia")
        df_ag = pd.DataFrame(data_agencias.values())
        if not df_ag.empty:
            st.dataframe(df_ag, hide_index=True, use_container_width=True)

        with st.expander("🔎 Ver Detalle Individual"):
            st.dataframe(df_detalle_rep, use_container_width=True, hide_index=True)

    else:
        # Lógica B2C
        ventas = vc.obtener_ventas_directas()
        if not ventas:
            st.info("No hay ventas B2C con saldo pendiente.")
            return

        ids_ventas = [v['id_venta'] for v in ventas]
        # Obtener todos los pagos vinculados a estas ventas para calcular el saldo REAL en moneda de la venta
        pagos = supabase_client.table('pago').select('id_venta, monto_moneda_venta').in_('id_venta', ids_ventas).execute().data
        
        mapa_pagos = {}
        for p in pagos:
            pid = p['id_venta']
            # Usamos monto_moneda_venta para que el saldo siempre sea en la moneda original de la venta
            mapa_pagos[pid] = mapa_pagos.get(pid, 0) + (p['monto_moneda_venta'] or 0)

        lista_detalle = []
        for v in ventas:
            monto = float(v.get('precio_total_cierre') or 0)
            pagado = float(mapa_pagos.get(v['id_venta'], 0))
            saldo = monto - pagado
            mon = v.get('moneda', '$')
            
            lista_detalle.append({
                'ID Venta': v['id_venta'],
                'Cliente': v.get('nombre_cliente'),
                'Fecha': v.get('fecha_venta'),
                f'Total ({mon})': monto,
                f'Pagado ({mon})': pagado,
                f'Saldo ({mon})': saldo,
                'Estado': '✅ PAGADO' if saldo <= 0.1 else '🔴 DEBE'
            })
        
        df_b2c = pd.DataFrame(lista_detalle)
        # Nota: La suma total solo es válida si todas las ventas están en la misma moneda (usualmente USD)
        total_deuda = 0
        if not df_b2c.empty:
            # Buscar la columna de Saldo dinámicamente
            saldo_col = [c for c in df_b2c.columns if 'Saldo' in c]
            if saldo_col: total_deuda = df_b2c[saldo_col[0]].sum()

        c1, c2 = st.columns(2)
        c1.metric("Total por Cobrar Directos", f"$ {total_deuda:,.2f}")
        c2.metric("Clientes con Deuda", len(df_b2c[df_b2c.iloc[:, 5] > 1]) if not df_b2c.empty else 0)

        # Botón Excel B2C
        if not df_b2c.empty:
            try:
                reporte_xlsx = exc_ctrl.generar_reporte_cuentas_cobrar_xlsx(df_b2c)
                st.download_button(
                    label="📊 Descargar Informe de Cuentas B2C (Excel)",
                    data=reporte_xlsx,
                    file_name=f"reporte_cuentas_b2c_{date.today()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    key="btn_dl_b2c_unified"
                )
            except Exception as e:
                st.error(f"Error: {e}")

        st.write("### 📋 Detalle de Saldos Directos")
        st.dataframe(df_b2c, hide_index=True, use_container_width=True)

    # 3. Formulario de Pago Manual (Común al final)
    st.divider()
    with st.expander("➕ Registrar Nuevo Abono / Pago Manual", expanded=False):
        st.write("Selecciona una venta con saldo pendiente para registrar un abono.")
        
        todas_v = vc.obtener_todas_ventas_b2b() + vc.obtener_ventas_directas()
        ids_v_all = [v['id_venta'] for v in todas_v]
        p_all = supabase_client.table('pago').select('id_venta, monto_moneda_venta').in_('id_venta', ids_v_all).execute().data
        m_p = {}
        for p in p_all:
            m_p[p['id_venta']] = m_p.get(p['id_venta'], 0) + (p['monto_moneda_venta'] or 0)

        v_deuda = [v for v in todas_v if (float(v.get('precio_total_cierre') or 0) - float(m_p.get(v['id_venta'], 0))) > 0.1]
        
        if not v_deuda:
            st.success("No hay deudas pendientes.")
        else:
            # Crear un mapa para búsqueda rápida de moneda
            mapa_monedas = {v['id_venta']: v.get('moneda', 'USD') for v in v_deuda}
            opc = [f"{v['id_venta']} | {v.get('nombre_cliente') or v.get('nombre_agencia')} (Saldo: {v.get('moneda', 'USD')} {float(v.get('precio_total_cierre') or 0) - float(m_p.get(v['id_venta'], 0)):.2f})" for v in v_deuda]
            sel_v = st.selectbox("Seleccione Venta:", opc, key="sel_v_pago_manual_unified")
            
            if sel_v:
                id_v = int(sel_v.split(" | ")[0])
                moneda_venta = mapa_monedas.get(id_v, 'USD')
                
                c1, c2, c3 = st.columns(3)
                monto_p = c1.number_input("Monto Recibido:", min_value=1.0, step=10.0)
                moneda_p = c2.selectbox("Moneda del Pago:", ["USD", "PEN", "EUR"], index=0 if moneda_venta == "USD" else 1)
                fecha_p = c3.date_input("Fecha de Pago:", date.today())
                
                # Inteligencia de Tipo de Cambio
                tasa_cambio = 1.0
                if moneda_p != moneda_venta:
                    st.warning(f"⚠️ **Atención**: Estás recibiendo {moneda_p} para una deuda en {moneda_venta}. Se requiere Tipo de Cambio.")
                    col_tc1, col_tc2 = st.columns(2)
                    tc_sugerido = 1.0
                    from services.exchange_service import ExchangeService
                    if moneda_p == "PEN" and moneda_venta == "USD": 
                        tc_sugerido = ExchangeService.get_current_tc()
                    elif moneda_p == "USD" and moneda_venta == "PEN":
                        tc_sugerido = 1 / ExchangeService.get_current_tc()
                    
                    tasa_cambio = col_tc1.number_input(f"TC ({moneda_p} a {moneda_venta}):", min_value=0.01, value=float(tc_sugerido), format="%.4f")
                    monto_equiv = round(monto_p / tasa_cambio, 2)
                    col_tc2.metric(f"Equivale en {moneda_venta}:", f"{monto_equiv:,.2f}")

                c4, c5 = st.columns(2)
                metodo_p = c4.selectbox("Método:", ["TRANSFERENCIA", "EFECTIVO", "YAPE/PLIN", "TARJETA", "DEPÓSITO"])
                tipo_p = c5.selectbox("Tipo:", ["ABONO", "SALDO TOTAL", "ADELANTO"])
                
                if st.button("🚀 Registrar Pago Ahora", type="primary", use_container_width=True, key="btn_reg_pago_unified"):
                    exito, msg = vc.registrar_pago(
                        id_venta=id_v,
                        monto_pagado=monto_p,
                        moneda_pago=moneda_p,
                        tasa_cambio=tasa_cambio,
                        fecha_pago=fecha_p.isoformat(),
                        metodo=metodo_p,
                        tipo_pago=tipo_p
                    )
                    
                    if exito:
                        st.success(msg)
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(msg)



