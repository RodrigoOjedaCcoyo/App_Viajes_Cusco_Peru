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

def render_operational_master_download_acc(controller, id_venta):
    """Llamada al componente Maestro unificado."""
    from vistas.page_operaciones import render_operational_master_download
    from controllers.operaciones_controller import OperacionesController
    # Necesitamos un OperacionesController para esta función específica
    op_ctrl = OperacionesController(controller.client)
    render_operational_master_download(op_ctrl, id_venta, label="📊 Generar Informe Maestro", key=f"acc_master_dl_{id_venta}")

def mostrar_pagina(funcionalidad_seleccionada, rol_actual=None, user_id=None, supabase_client=None):
    if supabase_client:
        st.session_state['reporte_controller'] = ReporteController(supabase_client)

    st.title(f"📝 Gestión Contable")
    
    # --- 🔔 Centro de Alertas Universal ---
    from controllers.operaciones_controller import OperacionesController
    from vistas.page_operaciones import render_centro_alertas
    ctrl_op = OperacionesController(supabase_client)
    render_centro_alertas(ctrl_op)
    
    st.markdown("---")
    
    if funcionalidad_seleccionada in ["Gestión de Registros", "Finanzas y Caja"]:
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Estructurador Financiero", 
            "💰 Cuentas por Cobrar",
            "🚐 Pagos Operativos (Proveedores)",
            "📅 Calendario Operativo"
        ])
        
        with tab1:
            estructurador_liquidacion_pro(st.session_state['reporte_controller'])
            
        with tab2:
            dashboard_cuentas_por_cobrar_unified(supabase_client)
            
        with tab3:
            dashboard_pagos_operativos(supabase_client)

        with tab4:
            from controllers.operaciones_controller import OperacionesController
            from vistas.page_operaciones import dashboard_tablero_diario
            ctrl_ops = OperacionesController(supabase_client)
            dashboard_tablero_diario(ctrl_ops)
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
                df_saldos.style.map(highlight_saldo, subset=['Saldo Pendiente']),
                column_config={
                    "Total Costos": st.column_config.NumberColumn("Total Costos", format="%.2f"),
                    "Abonado": st.column_config.NumberColumn("Abonado", format="%.2f"),
                    "Saldo Pendiente": st.column_config.NumberColumn("Saldo Pendiente", format="%.2f"),
                },
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
                .select('id_venta, n_linea, tipo_servicio')\
                .eq('id_proveedor', id_prov)\
                .execute()
            
            opciones_serv = ["--- Pago General (No vinculado) ---"]
            mapa_serv = {}
            if res_serv.data:
                # Recuperar info de las ventas asociadas para nombres
                ids_ventas = list(set([s['id_venta'] for s in res_serv.data if s.get('id_venta')]))
                mapa_nombres_ventas = {}
                if ids_ventas:
                    res_v = supabase_client.table('venta').select('id_venta, tour_nombre, cliente(nombre)').in_('id_venta', ids_ventas).execute()
                    if res_v.data:
                        for v in res_v.data:
                            c_info = v.get('cliente') or {}
                            n_cliente = c_info.get('nombre') if isinstance(c_info, dict) else c_info
                            if isinstance(c_info, list) and len(c_info) > 0:
                                n_cliente = c_info[0].get('nombre')
                            mapa_nombres_ventas[v['id_venta']] = {
                                'tour_nombre': v.get('tour_nombre', 'Tour'),
                                'nombre_cliente': n_cliente or f"ID {v['id_venta']}"
                            }
                
                for s in res_serv.data:
                    v_info = mapa_nombres_ventas.get(s['id_venta'], {})
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
            obs_cont = c7.text_input("Observaciones Contables:", placeholder="Uso exclusivo contabilidad", key="obs_cont_op")
            
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
                    id_usuario=None,
                    observaciones_contables=obs_cont
                )

                if exito:
                    st.success(f"✅ Pago de {moneda_pago} {monto_pago:,.2f} registrado con éxito.")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("No se pudo registrar el pago. Verifique los campos.")

    # 3. Historial de Pagos (Recientes con Edición)
    with st.expander("🔎 Historial de Pagos Recientes (Editar/Borrar)"):
        if prov_sel != "--- Seleccione ---":
            st.write(f"Historial para **{prov_sel}**:")
            df_hist = po_ctrl.obtener_historial_pagos_proveedor(mapa_prov[prov_sel])
            if not df_hist.empty:
                # Columnas visibles y editables
                cols_ed = ['id_pago_op', 'Fecha', 'Monto', 'Moneda', 'TC', 'Abono Eq.', 'Metodo', 'Notas', 'Obs. Contables', 'Voucher']
                
                df_hist['Borrar'] = False
                
                edited_hist = st.data_editor(
                    df_hist[['Borrar'] + cols_ed],
                    column_config={
                        "id_pago_op": st.column_config.TextColumn("ID", width="small", disabled=True),
                        "Borrar": st.column_config.CheckboxColumn("❌", width="small"),
                        "Abono Eq.": st.column_config.NumberColumn("Descuento Deuda", format="%.2f", disabled=True),
                        "Fecha": st.column_config.DateColumn("Fecha"),
                        "Monto": st.column_config.NumberColumn("Monto", format="%.2f"),
                        "Moneda": st.column_config.SelectboxColumn("Moneda", options=["USD", "PEN", "EUR"]),
                        "Metodo": st.column_config.SelectboxColumn("Método", options=["YAPE", "PLIN", "TRANSFERENCIA", "EFECTIVO", "OTRO"]),
                        "TC": st.column_config.NumberColumn("TC", format="%.4f")
                    },
                    hide_index=True,
                    use_container_width=True,
                    key=f"editor_hist_prov_{id_prov}"
                )

                if st.button("💾 Aplicar Cambios en Historial de Proveedor", key=f"btn_save_hist_{id_prov}", use_container_width=True):
                    # 1. Procesar Borrados
                    borrados = edited_hist[edited_hist['Borrar'] == True]
                    for _, row in borrados.iterrows():
                        po_ctrl.eliminar_pago_operativo(row['id_pago_op'])
                    
                    # 2. Procesar Ediciones
                    state = st.session_state.get(f"editor_hist_prov_{id_prov}", {})
                    edits = state.get("edited_rows", {})
                    for idx, changes in edits.items():
                        if edited_hist.iloc[idx]['Borrar']: continue
                        reg_id = edited_hist.iloc[idx]['id_pago_op']
                        mapping = {
                            "Fecha": "fecha_pago",
                            "Monto": "monto_pagado",
                            "Moneda": "moneda",
                            "Metodo": "metodo_pago",
                            "TC": "tasa_cambio",
                            "Notas": "observaciones",
                            "Obs. Contables": "observaciones_contables",
                            "Voucher": "comprobante_url"
                        }
                        db_changes = {mapping[k]: (v.isoformat() if hasattr(v, 'isoformat') else v) for k, v in changes.items() if k in mapping}
                        if db_changes:
                            po_ctrl.actualizar_pago_operativo(reg_id, db_changes)
                    
                    st.success("✅ Cambios aplicados.")
                    st.rerun()
            else:
                st.caption("No se encontraron pagos anteriores para este proveedor.")
        else:
            st.caption("Seleccione un proveedor para ver su historial.")

def estructurador_liquidacion_pro(controller):
    """
    Herramienta avanzada para estructurar liquidaciones (Versión Contabilidad).
    """
    from datetime import date
    st.subheader("📊 Estructurador de Liquidación Profesional", divider='rainbow')

    if 'simulador_contable_adv_data' not in st.session_state:
        st.session_state['simulador_contable_adv_data'] = []

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
            
            if st.session_state.get('last_loaded_id_venta_acc') != v_act['id_venta']:
                from controllers.operaciones_controller import OperacionesController
                op_ctrl = OperacionesController(controller.client)
                
                detalles = vc.obtener_detalles_itinerario_venta(v_act['id_venta'])
                liquidaciones = op_ctrl.get_liquidaciones_venta(v_act['id_venta'])
                
                tc_venta = float(v_act.get('tipo_cambio') or 3.70)
                mapa_costos_pen = {}
                for liq in liquidaciones:
                    nl = liq.get('n_linea')
                    if nl is not None:
                        costo_liq = float(liq.get('costo_unitario') or 0.0)
                        moneda_liq = (liq.get('moneda') or 'PEN').strip().upper()
                        costo_en_pen = round(costo_liq * tc_venta, 4) if moneda_liq == 'USD' else costo_liq
                        
                        if nl not in mapa_costos_pen:
                            mapa_costos_pen[nl] = {"total": 0.0, "confirmados": 0.0, "vistos": 0}
                        
                        mapa_costos_pen[nl]["total"] += costo_en_pen
                        if liq.get('terminado'):
                            mapa_costos_pen[nl]["confirmados"] += costo_en_pen
                        mapa_costos_pen[nl]["vistos"] += 1

                filas = []
                for d in (detalles or []):
                    info_nl = mapa_costos_pen.get(d['n_linea'], {"total": 0.0, "confirmados": 0.0, "vistos": 0})
                    costo_pen = round(info_nl["total"], 2)
                    estado_op = "✅ OK" if info_nl["confirmados"] >= info_nl["total"] and info_nl["vistos"] > 0 else "🔴 PEND"
                    
                    filas.append({
                        "FECHA"    : date.fromisoformat(d['fecha_servicio']),
                        "HORA"     : d.get('hora_inicio', '--:--'),
                        "ESTADO"   : estado_op,
                        "SERVICIO" : d.get('observacion') or "Servicio",
                        "PAX"      : d.get('cantidad', 1),
                        "COSTO_PEN": costo_pen,
                        "id_venta" : d['id_venta'],
                        "n_linea"  : d['n_linea']
                    })

                st.session_state['simulador_contable_adv_data'] = filas
                st.session_state['tc_venta_acc'] = tc_venta
                st.session_state['es_usd_acc'] = False
                st.session_state['last_loaded_id_venta_acc'] = v_act['id_venta']

            id_it_dig = v_act.get('id_itinerario_digital')
            if id_it_dig:
                with st.expander("📄 Ver Itinerario Original para Auditoría", expanded=False):
                    res_it = controller.client.table('itinerario_digital').select('datos_render').eq('id_itinerario_digital', id_it_dig).single().execute()
                    if res_it.data:
                        import json
                        render_data = res_it.data['datos_render']
                        if isinstance(render_data, str): render_data = json.loads(render_data)
                        render_itinerary_simple_download(render_data)
                        st.markdown("---")
                        render_operational_master_download_acc(controller, v_act['id_venta'])

    df = pd.DataFrame(st.session_state['simulador_contable_adv_data'])
    if not df.empty:
        df.sort_values(by='FECHA', inplace=True)
        col_costo = 'COSTO_PEN'
        st.dataframe(
            df,
            column_order=["FECHA", "HORA", "ESTADO", "SERVICIO", "PAX", col_costo],
            column_config={
                "FECHA"    : st.column_config.DateColumn("Fecha", format="DD/MM/YYYY"),
                "COSTO_PEN": st.column_config.NumberColumn("Costo (S/.)", format="S/ %.2f"),
            },
            use_container_width=True,
            hide_index=True
        )
        t_costos = df[col_costo].sum()
        st.metric("COSTO TOTAL EN SOLES", f"S/ {t_costos:,.2f}")

from controllers.venta_controller import VentaController

def herramienta_carga_masiva_pagos(supabase_client, key_suffix=""):
    st.markdown("### 📥 Carga Masiva de Pagos (Excel)")
    tipo_import = st.selectbox("1️⃣ Tipo:", ["B2B (Agencias)", "B2C (Directas)"], key=f"sel_tipo_import_{key_suffix}")
    
    with st.expander("📁 Subir Archivo y Plantilla", expanded=True):
        template_df = pd.DataFrame(columns=["ID Venta", "Fecha", "Monto", "Moneda", "Metodo", "Tipo", "Comprobante", "TC", "Obs. Contables"])
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            template_df.to_excel(writer, index=False, sheet_name='PlantillaPagos')
        
        st.download_button(label="📄 Descargar Plantilla Excel", data=output.getvalue(), file_name="plantilla_pagos.xlsx", use_container_width=True)
        uploaded_file = st.file_uploader("Subir Excel de Pagos:", type=["xlsx", "csv"], key=f"uploader_pagos_{key_suffix}")
        
        if uploaded_file:
            df_upload = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
            st.dataframe(df_upload, use_container_width=True, hide_index=True)
            if st.button("🧧 Procesar y Registrar Todo", type="primary", use_container_width=True, key=f"btn_proc_{key_suffix}"):
                vc = VentaController(supabase_client)
                resultado = vc.vincular_pagos_masivos(df_upload)
                if resultado["exitos"] > 0: st.success(f"✅ Se registraron {resultado['exitos']} pagos.")
                if resultado["errores"]:
                    with st.expander("⚠️ Ver Errores"):
                        for err in resultado["errores"]: st.error(err)
                st.rerun()

def dashboard_cuentas_por_cobrar_unified(supabase_client):
    st.subheader("💰 Cuentas por Cobrar", divider='orange')
    herramienta_carga_masiva_pagos(supabase_client, "unified")
    st.divider()

    tipo_vista = st.radio("Seleccione el tipo de cobro:", ["💎 B2B (Agencias)", "👤 B2C (Directas)"], horizontal=True)
    vc = VentaController(supabase_client)

    if "B2B" in tipo_vista:
        ventas = vc.obtener_todas_ventas_b2b()
    else:
        ventas = vc.obtener_ventas_directas()

    if not ventas:
        st.info("No hay ventas registradas.")
        return

    ids_v = [v['id_venta'] for v in ventas]
    pagos = supabase_client.table('pago').select('id_venta, monto_moneda_venta').in_('id_venta', ids_v).execute().data
    mapa_p = {}
    for p in pagos: mapa_p[p['id_venta']] = mapa_p.get(p['id_venta'], 0) + (p['monto_moneda_venta'] or 0)

    lista_detalle = []
    for v in ventas:
        monto = float(v.get('precio_total_cierre') or 0)
        pagado = float(mapa_p.get(v['id_venta'], 0))
        saldo = monto - pagado
        lista_detalle.append({
            'ID Venta': v['id_venta'],
            'Cliente': v.get('nombre_cliente') or v.get('nombre_agencia'),
            'Total': monto,
            'Pagado': pagado,
            'Saldo': saldo,
            'Moneda': v.get('moneda', 'USD')
        })

    df_cobros = pd.DataFrame(lista_detalle)
    st.dataframe(df_cobros, use_container_width=True, hide_index=True)

    st.divider()
    with st.expander("➕ Registrar Nuevo Abono / Pago Manual", expanded=False):
        sel_v = st.selectbox("Seleccione Venta:", [f"{v['ID Venta']} | {v['Cliente']} (Saldo: {v['Saldo']:.2f})" for v in lista_detalle if v['Saldo'] > 0.1])
        if sel_v:
            id_v = int(sel_v.split(" | ")[0])
            c1, c2, c3 = st.columns(3)
            monto_p = c1.number_input("Monto:", min_value=1.0)
            moneda_p = c2.selectbox("Moneda:", ["USD", "PEN", "EUR"])
            fecha_p = c3.date_input("Fecha:", date.today())
            obs_cont = st.text_input("Observaciones Contables:", key="obs_cont_manual")
            
            if st.button("🚀 Registrar Pago", type="primary", use_container_width=True):
                exito, msg = vc.registrar_pago(id_venta=id_v, monto_pagado=monto_p, moneda_pago=moneda_p, tasa_cambio=3.7, fecha_pago=fecha_p.isoformat(), metodo="TRANSFERENCIA", tipo_pago="ABONO", observaciones_contables=obs_cont)
                if exito: st.success(msg); st.rerun()
                else: st.error(msg)

            # --- Historial Editable ---
            st.markdown("#### 🔎 Historial de Pagos de esta Venta")
            pagos_v = vc.obtener_pagos_venta(id_v)
            if pagos_v:
                df_p = pd.DataFrame(pagos_v)
                df_p['Borrar'] = False
                cols_p = ['id_pago', 'fecha_pago', 'monto_pagado', 'moneda', 'metodo_pago', 'tipo_pago', 'observaciones_contables']
                edited_p = st.data_editor(df_p[['Borrar'] + cols_p], key=f"edit_p_{id_v}", hide_index=True, use_container_width=True)
                
                if st.button("💾 Guardar Cambios en Historial", key=f"btn_save_p_{id_v}"):
                    for _, row in edited_p[edited_p['Borrar']].iterrows(): vc.eliminar_pago(row['id_pago'])
                    state_p = st.session_state.get(f"edit_p_{id_v}", {}).get("edited_rows", {})
                    for idx, ch in state_p.items():
                        if not edited_p.iloc[idx]['Borrar']:
                            db_ch = {k: (v.isoformat() if hasattr(v, 'isoformat') else v) for k, v in ch.items()}
                            vc.actualizar_pago(edited_p.iloc[idx]['id_pago'], db_ch)
                    st.success("Cambios guardados"); st.rerun()
