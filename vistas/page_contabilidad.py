# vistas/page_contabilidad.py
import streamlit as st
import pandas as pd
from datetime import date
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
    
    with st.container(border=True):
        st.markdown(f"#### 📄 Resumen Financiero: {render.get('titulo', 'Sin Título')}")
        st.info("Este documento es una versión simplificada (Ink Saver) para auditoría interna.")
        
        c1, c2 = st.columns(2)
        
        with c1:
            # Generar el PDF en memoria
            pdf_buffer = pdf_ctrl.generar_itinerario_simple_pdf(render)
            if pdf_buffer:
                st.download_button(
                    label="📥 Bajar Resumen (PDF Simple)",
                    data=pdf_buffer,
                    file_name=f"auditoria_{render.get('titulo', 'itinerario')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
        
        with c2:
            # Generar el Excel en memoria (Reporte Logístico Unificado)
            xlsx_buffer = xl_ctrl.generar_resumen_itinerario_xlsx(render)
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
        tab1, tab2 = st.tabs([
            "📊 Estructurador Financiero", 
            "💎 Cuentas por Cobrar (B2B)"
        ])
        
        with tab1:
            estructurador_liquidacion_pro(st.session_state['reporte_controller'])
            
        with tab2:
            dashboard_cuentas_por_cobrar_b2b(supabase_client)
    else:
        st.info("Utilice el Dashboard Contable para ver reportes.")

def estructurador_liquidacion_pro(controller):
    """
    Herramienta avanzada para estructurar liquidaciones (Versión Contabilidad).
    Permite cargar ventas y asignar costos/proveedores directamente.
    """
    from datetime import date
    st.subheader("📊 Estructurador de Liquidación Profesional", divider='rainbow')

    if 'simulador_contable_adv_data' not in st.session_state:
        st.session_state['simulador_contable_adv_data'] = [
            {"FECHA": date.today(), "SERVICIO": "Servicio Ejemplo", "MONEDA": "USD", "TOTAL": 0.0},
        ]

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
                
                # Mapear costos: n_linea -> Suma de costos de liquidación
                mapa_costos_reales = {}
                for liq in liquidaciones:
                    nl = liq.get('n_linea')
                    if nl is not None:
                        mapa_costos_reales[nl] = mapa_costos_reales.get(nl, 0.0) + float(liq.get('costo_unitario') or 0.0)

                if detalles:
                    st.session_state['simulador_contable_adv_data'] = [{
                        "FECHA": date.fromisoformat(d['fecha_servicio']),
                        "SERVICIO": d.get('observacion') or "Servicio",
                        "MONEDA": d.get('moneda_costo', 'USD'),
                        # Usar el costo real liquidado, si no hay, usar el applied (para no romper nada)
                        "TOTAL": mapa_costos_reales.get(d['n_linea'], float(d.get('costo_applied') or 0.0)),
                        "id_venta": d['id_venta'],
                        "n_linea": d['n_linea']
                    } for d in detalles]
                    st.session_state['last_loaded_id_venta_acc'] = v_act['id_venta']
                    st.rerun()

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

    lista_prov = ["--- Sin Asignar ---"]
    res_prov_data = []
    try:
        res_prov = controller.client.table('proveedor').select('id_provider' if 'id_provider' in str(controller.client.table('proveedor').select('*').limit(1).execute().data) else 'id_proveedor', 'nombre', 'tipo_servicio').execute()
        res_prov_data = res_prov.data or []
        lista_prov += [f"{p['nombre']} ({p['tipo_servicio']})" for p in res_prov_data]
    except: pass

    # VISTA DE SOLO LECTURA
    st.dataframe(
        df, 
        column_config={
            "FECHA": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY"),
            "SERVICIO": st.column_config.TextColumn("Servicio", width="large"),
            "MONEDA": "💵",
            "TOTAL": st.column_config.NumberColumn("Costo", format="%.2f")
        },
        use_container_width=True, 
        hide_index=True
    )

    # Totales
    t_costos = df['TOTAL'].sum() if not df.empty else 0.0
    st.divider()
    st.metric("COSTO TOTAL REGISTRADO", f"$ {t_costos:,.2f}")
    
    st.info("💡 Esta vista es de solo consulta (Auditoría). Para modificar costos o asignar proveedores, utiliza el Google Sheet Maestro.")

from controllers.venta_controller import VentaController

def dashboard_cuentas_por_cobrar_b2b(supabase_client):
    """Dashboard específico para controlar deudas de Agencias (B2B)."""
    st.subheader("💎 Cuentas por Cobrar (B2B)", divider='blue')
    
    vc = VentaController(supabase_client)
    ventas = vc.obtener_todas_ventas_b2b()
    
    if not ventas:
        st.info("No hay ventas B2B registradas.")
        return

    # Obtener pagos de estas ventas para calcular saldo real
    ids_ventas = [v['id_venta'] for v in ventas]
    pagos = supabase_client.table('pago').select('id_venta, monto_pagado').in_('id_venta', ids_ventas).execute().data
    
    mapa_pagos = {}
    for p in pagos:
        pid = p['id_venta']
        mapa_pagos[pid] = mapa_pagos.get(pid, 0) + (p['monto_pagado'] or 0)

    # Procesar data
    data_agencias = {}
    lista_detalle = []
    
    for v in ventas:
        id_agencia = v.get('id_agencia_aliada')
        nombre_agencia = v.get('nombre_agencia', 'Sin Nombre')
        monto = float(v.get('precio_total_cierre') or 0)
        pagado = float(mapa_pagos.get(v['id_venta'], 0))
        saldo = monto - pagado
        
        # Agregado por Agencia
        if id_agencia not in data_agencias:
            data_agencias[id_agencia] = {'Nombre': nombre_agencia, 'Total Ventas': 0.0, 'Cobrado': 0.0, 'Por Cobrar': 0.0, 'Count': 0}
        
        data_agencias[id_agencia]['Total Ventas'] += monto
        data_agencias[id_agencia]['Cobrado'] += pagado
        data_agencias[id_agencia]['Por Cobrar'] += saldo
        data_agencias[id_agencia]['Count'] += 1
        
        lista_detalle.append({
            'Agencia': nombre_agencia,
            'Pasajero': v.get('nombre_cliente'),
            'Fecha Venta': v.get('fecha_venta'),
            'Total ($)': monto,
            'A Cuenta ($)': pagado,
            'Saldo ($)': saldo,
            'Estado': '✅ PAGADO' if saldo <= 0.1 else '🔴 DEBE'
        })
        
    # Visualización 1: Métricas Globales
    total_deuda_b2b = sum(d['Por Cobrar'] for d in data_agencias.values())
    c1, c2 = st.columns(2)
    c1.metric("Total por Cobrar a Agencias", f"${total_deuda_b2b:,.2f}")
    c2.metric("Agencias con Deuda", len([d for d in data_agencias.values() if d['Por Cobrar'] > 1]))
    
    st.divider()
    
    # Visualización 2: Tabla Resumen por Agencia
    st.write("### 🏢 Resumen por Agencia")
    df_agencias = pd.DataFrame(data_agencias.values())
    if not df_agencias.empty:
        st.dataframe(
            df_agencias,
            column_config={
                "Total Ventas": st.column_config.NumberColumn(format="$ %.2f"),
                "Cobrado": st.column_config.NumberColumn(format="$ %.2f"),
                "Por Cobrar": st.column_config.NumberColumn(format="$ %.2f"),
            },
            hide_index=True,
            use_container_width=True
        )

    # Visualización 3: Detalle Expandible
    with st.expander("🔎 Ver Detalle de Todas las Ventas B2B"):
        df_det = pd.DataFrame(lista_detalle, index=None)
        st.dataframe(df_det, use_container_width=True, hide_index=True)

    st.divider()

    # --- NUEVO: FORMULARIO DE REGISTRO MANUAL DE PAGOS ---
    with st.expander("➕ Registrar Nuevo Abono / Pago Manual", expanded=False):
        st.write("Selecciona una venta con saldo pendiente para registrar un abono.")
        
        # Solo mostrar ventas con saldo > 0
        ventas_deuda = [v for v in ventas if (float(v.get('precio_total_cierre') or 0) - float(mapa_pagos.get(v['id_venta'], 0))) > 0.1]
        
        if not ventas_deuda:
            st.success("No hay ventas con saldo pendiente actualmente.")
        else:
            opciones_pago = [f"{v['id_venta']} | {v['nombre_cliente']} (Debe: ${float(v.get('precio_total_cierre') or 0) - float(mapa_pagos.get(v['id_venta'], 0)):.2f})" for v in ventas_deuda]
            v_sel_pago = st.selectbox("Seleccione Venta:", opciones_pago, key="sel_v_pago_manual")
            
            if v_sel_pago:
                id_v_pago = int(v_sel_pago.split(" | ")[0])
                v_data_pago = next(v for v in ventas_deuda if v['id_venta'] == id_v_pago)
                
                c1, c2, c3 = st.columns(3)
                with c1:
                    monto_pago = st.number_input("Monto del Abono:", min_value=1.0, step=10.0, format="%.2f")
                with c2:
                    moneda_pago = st.selectbox("Moneda:", ["USD", "PEN"], index=0)
                with c3:
                    fecha_pago = st.date_input("Fecha de Pago:", date.today())
                
                c4, c5 = st.columns(2)
                with c4:
                    metodo_pago = st.selectbox("Método:", ["TRANSFERENCIA", "EFECTIVO", "YAPE/PLIN", "TARJETA", "DEPÓSITO"])
                with c5:
                    tipo_pago = st.selectbox("Tipo de Pago:", ["ABONO", "SALDO TOTAL", "ADELANTO"])
                
                if st.button("🚀 Registrar Pago Ahora", type="primary", use_container_width=True):
                    try:
                        nuevo_pago = {
                            "id_venta": id_v_pago,
                            "fecha_pago": fecha_pago.isoformat(),
                            "monto_pagado": monto_pago,
                            "moneda": moneda_pago,
                            "metodo_pago": metodo_pago,
                            "tipo_pago": tipo_pago
                        }
                        supabase_client.table('pago').insert(nuevo_pago).execute()
                        st.success(f"✅ Pago de ${monto_pago} registrado correctamente para {v_data_pago['nombre_cliente']}.")
                        st.balloons()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al registrar el pago: {e}")

