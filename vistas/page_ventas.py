# vistas/page_ventas.py
import streamlit as st
import pandas as pd
from datetime import date, timedelta, datetime
from controllers.lead_controller import LeadController
from controllers.venta_controller import VentaController
from controllers.operaciones_controller import OperacionesController
from vistas.page_operaciones import render_centro_alertas
from services.exchange_service import ExchangeService

def render_itinerary_details_visual(render):
    """Renderiza el detalle visual del itinerario de forma robusta."""
    # Soportar múltiples estructuras de datos de itinerario
    tours = render.get('itinerario_detalles', []) or render.get('itinerario_detales', []) or render.get('days', [])
    
    with st.container(border=True):
        # Título del Itinerario
        titulo_itin = render.get('titulo') or f"{render.get('title_1', '')} {render.get('title_2', '')}".strip() or "General"
        st.success(f"📍 **ITINERARIO:** {titulo_itin.upper()}")
        
        # --- SECCIÓN GLOBAL (Inclusiones/Exclusiones Generales) ---
        g_inc = render.get('inclusiones_globales') or render.get('servicios_incluidos', []) or render.get('incluye', [])
        g_exc = render.get('exclusiones_globales') or render.get('servicios_no_incluidos', []) or render.get('no_incluye', [])
        
        if g_inc or g_exc:
            with st.expander("✨ Inclusiones y Exclusiones Generales del Paquete", expanded=True):
                if g_inc:
                    st.markdown("<span style='color:#2E7D32; font-weight:bold;'>INCLUYE (Global):</span>", unsafe_allow_html=True)
                    for item in g_inc:
                        txt = item.get('texto') if isinstance(item, dict) else item
                        if txt: st.markdown(f"&nbsp;&nbsp;✔️ {str(txt).upper()}")
                if g_exc:
                    st.markdown("<span style='color:#2E7D32; font-weight:bold;'>NO INCLUYE (Global):</span>", unsafe_allow_html=True)
                    for item in g_exc:
                        txt = item.get('texto') if isinstance(item, dict) else item
                        if txt: st.markdown(f"&nbsp;&nbsp;❌ {str(txt).upper()}")
        st.divider()
        
        # Rendereado Día por Día
        for i, t in enumerate(tours):
            # Obtener Label del Día
            dia_label = f"DIA {i+1}"
            if t.get('fecha'): dia_label = f"DIA: {t['fecha']}"
            elif t.get('numero'): dia_label = f"DIA {t['numero']}"
            
            st.markdown(f"**{dia_label}**")
            
            # Nombre del Servicio y Hora
            t_nom = (t.get('nombre') or t.get('titulo') or "Servicio").upper()
            t_hora = t.get('hora', '')
            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;✅ **{f'({t_hora}) ' if t_hora else ''}{t_nom}**")
            
            # Inclusiones del Día (Soporta lista de strings o lista de objetos con 'texto')
            inc = t.get('incluye') or t.get('inclusiones', []) or t.get('servicios', [])
            if inc:
                st.markdown("&nbsp;&nbsp;&nbsp;&nbsp;<span style='color:#2E7D32; font-weight:bold; font-size:12px;'>INCLUYE:</span>", unsafe_allow_html=True)
                for item in inc:
                    txt = item.get('texto') if isinstance(item, dict) else item
                    if txt: st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;✔️ <small>{str(txt).upper()}</small>", unsafe_allow_html=True)
            
            # Exclusiones del Día (Soporta lista de strings o lista de objetos con 'texto')
            exc = t.get('no_incluye') or t.get('exclusiones', []) or t.get('servicios_no', [])
            if exc:
                st.markdown("&nbsp;&nbsp;&nbsp;&nbsp;<span style='color:#2E7D32; font-weight:bold; font-size:12px;'>NO INCLUYE:</span>", unsafe_allow_html=True)
                for item in exc:
                    txt = item.get('texto') if isinstance(item, dict) else item
                    if txt: st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;❌ <small>{str(txt).upper()}</small>", unsafe_allow_html=True)
            st.write("")

        # --- BOTÓN DE DESCARGA EXCEL ---
        st.divider()
        if tours:
            try:
                import io
                import pandas as pd
                
                excel_data = []
                for i, t in enumerate(tours):
                    dia_lbl = f"DIA {i+1}"
                    if t.get('fecha'): dia_lbl = t['fecha']
                    elif t.get('numero'): dia_lbl = f"DIA {t['numero']}"
                    
                    nom = (t.get('nombre') or t.get('titulo') or "Servicio").upper()
                    hora = t.get('hora', '')
                    
                    inc = t.get('incluye') or t.get('inclusiones', []) or t.get('servicios', [])
                    inc_str = ", ".join([item.get('texto') if isinstance(item, dict) else str(item) for item in inc])
                    
                    exc = t.get('no_incluye') or t.get('exclusiones', []) or t.get('servicios_no', [])
                    exc_str = ", ".join([item.get('texto') if isinstance(item, dict) else str(item) for item in exc])
                    
                    excel_data.append({
                        "Día / Fecha": dia_lbl,
                        "Hora": hora,
                        "Tour / Actividad": nom,
                        "Incluye": inc_str,
                        "No Incluye": exc_str
                    })
                
                df_itin = pd.DataFrame(excel_data)
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    df_itin.to_excel(writer, index=False, sheet_name='Itinerario')
                
                st.download_button(
                    label="📥 Descargar Resumen en Excel",
                    data=buffer.getvalue(),
                    file_name=f"Resumen_Itinerario_{titulo_itin.replace(' ', '_')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            except Exception as e:
                pass




def get_vendedor_id():
    return st.session_state.get('user_id')

# --- MÓDULOS DE LEADS Y VENTAS (RESTAURADOS) ---

def formulario_registro_leads():
    lead_controller = st.session_state.get('lead_controller')
    if not lead_controller: st.error("Error de inicialización de LeadController."); return
    
    st.subheader("📝 Registro de Nuevo Lead")
    vendedor_actual = get_vendedor_id()
    st.info(f"Registrando a cargo de: **{vendedor_actual}**")
        
    with st.form("form_nuevo_lead"):
        nombre_pax = st.text_input("Nombre del Pasajero", placeholder="Ej: Juan Pérez")
        telefono = st.text_input("Número de Celular")
        origen = st.selectbox("Origen / Red Social", ["---Seleccione---","Instagram", "Facebook", "TikTok", "Web", "WhatsApp", "Otro"])
        vendedores_map = lead_controller.obtener_mapeo_vendedores()
        nombres_vendedores = list(vendedores_map.values())
        vendedor_sel = st.selectbox("Asignar a", ["---Seleccione---"] + nombres_vendedores)
        submitted = st.form_submit_button("Guardar Lead")
        
        if submitted:
            # Encontrar el ID del vendedor seleccionado
            id_vendedor = None
            for vid, vnom in vendedores_map.items():
                if vnom == vendedor_sel:
                    id_vendedor = vid
                    break
            
            exito, mensaje = lead_controller.registrar_nuevo_lead(telefono, origen, id_vendedor, nombre_pax)
            if exito: st.success(mensaje)
            else: st.error(mensaje)

def seguimiento_leads():
    lead_controller = st.session_state.get('lead_controller')
    if not lead_controller: st.error("Error de inicialización de LeadController."); return

    st.subheader("🔎 Listado de Leads (MMM Analysis)")
    leads = lead_controller.obtener_todos_leads()
    
    if leads:
        df = pd.DataFrame(leads)
        # Mostrar solo columnas relevantes para gerencia y el reporte resumido
        display_cols = ['id_lead', 'nombre_pasajero', 'numero_celular', 'red_social', 'fecha_creacion']
        # Asegurar que las columnas existen
        existing_cols = [c for c in display_cols if c in df.columns]
        st.dataframe(df[existing_cols], use_container_width=True, hide_index=True)
    else:
        st.info("No hay leads registrados.")

def registro_ventas_directa():
    venta_controller = st.session_state.get('venta_controller')
    lead_controller = st.session_state.get('lead_controller')
    it_controller = st.session_state.get('itinerario_digital_controller')
    
    if not venta_controller or not lead_controller or not it_controller: 
        st.error("Error de inicialización de controladores.")
        return

    st.subheader("💰 Registro de Venta Confirmada")
    
    # 1. Buscador Inteligente de Lead
    search_query = st.text_input("🔍 Buscar Pasajero (Nombre o Celular)", placeholder="Escriba para filtrar...").strip().lower()
    
    leads = lead_controller.obtener_todos_leads()
    lead_opt = ["--- Selecciona un Lead (Obligatorio) ---"]
    lead_map = {}
    
    if leads:
        # Filtrar leads si hay búsqueda
        if search_query:
            filtered_leads = [
                l for l in leads 
                if search_query in str(l.get('nombre_pasajero', '')).lower() or 
                   search_query in str(l.get('numero_celular', '')).lower()
            ]
            st.caption(f"✨ Se encontraron {len(filtered_leads)} coincidencias.")
        else:
            # Si no hay búsqueda, mostrar solo los 20 más recientes para velocidad
            filtered_leads = leads[:20]
            st.caption("💡 Mostrando los 20 más recientes. Use el buscador para ver otros.")

        for l in filtered_leads:
            lbl = f"{l['numero_celular']} - {l.get('nombre_pasajero') or 'Sin Nombre'}"
            lead_opt.append(lbl)
            lead_map[lbl] = l

    lead_sel = st.selectbox("🎯 Vincular con un Lead existente", lead_opt, help="Busque por nombre o celular arriba")
    lead_data = lead_map.get(lead_sel)

    # --- 🕵️ SELECTOR DE ITINERARIO (Buscador por Contacto) ---
    id_lead_seleccionado = lead_data.get('id_lead') if lead_data else None
    
    if id_lead_seleccionado:
        itinerarios_recuperados = it_controller.listar_itinerarios_lead(id_lead_seleccionado)
    else:
        # Si no hay lead, mostrar itinerarios recientes (opción de búsqueda global)
        itinerarios_recuperados = it_controller.obtener_todos_recientes(limit=30)
    
    # Crear opciones para el selector
    opciones_itinerario = ["--- Sin Itinerario ---"]
    mapa_itinerarios = {}
    
    if itinerarios_recuperados:
        # 1. Ordenar por fecha de generación (antigüedad)
        itinerarios_recuperados.sort(key=lambda x: x.get('fecha_generacion', ''))
        
        # 2. Contador para versiones
        conteos = {}

        for it in itinerarios_recuperados:
            id_lead_from_itinerario = it.get('id_lead')
            render_data = it.get('datos_render', {})
            if isinstance(render_data, str):
                try: import json; render_data = json.loads(render_data)
                except: render_data = {}

            # --- FILTRO B2C: Solo mostrar itinerarios generados como B2C ---
            tipo_v = render_data.get('metadata', {}).get('tipo_venta', 'B2C')
            if tipo_v != 'B2C':
                continue

            # Soportar ambas estructuras
            titulo = render_data.get('titulo', '')
            if not titulo:
                title_1 = render_data.get('title_1', '')
                title_2 = render_data.get('title_2', '')
                titulo = f"{title_1} {title_2}".strip() or 'Sin título'
            
            fecha = it.get('fecha_generacion', '')[:10] if it.get('fecha_generacion') else 'Sin fecha'
            
            # Celular para el label
            celular = it.get('lead', {}).get('numero_celular', '') if it.get('lead') else lead_data.get('numero_celular', '') if lead_data else ''
            cel_label = f"📱 {celular} | " if celular else ""
            
            # Label base sin versión
            base_label = f"{cel_label}{titulo} ({fecha})"
            
            # Manejo de Versiones (V1, V2...)
            conteos[base_label] = conteos.get(base_label, 0) + 1
            ver = conteos[base_label]
            
            label_final = f"{base_label} - V{ver}"
            opciones_itinerario.append(label_final)
            mapa_itinerarios[label_final] = it
    
    itinerario_seleccionado = st.selectbox(
        "✨ Seleccionar Itinerario Visual (Diseño Cloud)", 
        opciones_itinerario,
        help="Seleccione el diseño que corresponde a esta venta"
    )
    
    # Auto-completar datos si se seleccionó un itinerario
    id_itinerario_dig = None
    id_lead_from_itinerario = None  # Respaldo: extraer id_lead del itinerario
    if itinerario_seleccionado != "--- Sin Itinerario ---":
        it_data = mapa_itinerarios.get(itinerario_seleccionado)
        if it_data:
            id_itinerario_dig = it_data.get('id_itinerario_digital')
            id_lead_from_itinerario = it_data.get('id_lead')
            render = it_data.get('datos_render', {})
            if isinstance(render, str):
                import json
                try: render = json.loads(render)
                except: render = {}
            
            # Extraer nombre del pasajero (soporta ambas estructuras)
            nombre_pax_cloud = it_data.get('nombre_pasajero_itinerario', '') or render.get('pasajero', '')
            
            # Extraer título del tour (soporta ambas estructuras)
            # Estructura interna: render.get('titulo')
            # Estructura externa: title_1 + title_2
            tour_nombre_cloud = render.get('titulo', '')
            if not tour_nombre_cloud:
                title_1 = render.get('title_1', '')
                title_2 = render.get('title_2', '')
                tour_nombre_cloud = f"{title_1} {title_2}".strip()
            
            # Extraer celular del lead asociado al itinerario
            cel_cloud = ''
            if it_data.get('lead') and isinstance(it_data['lead'], dict):
                cel_cloud = it_data['lead'].get('numero_celular', '')
            
            # Inyectar teléfono en el render para el PDF
            render['cliente_telefono'] = cel_cloud
            
            st.session_state[f"val_nom_{id_itinerario_dig}"] = nombre_pax_cloud
            st.session_state[f"val_tour_{id_itinerario_dig}"] = tour_nombre_cloud
            st.session_state[f"val_cel_{id_itinerario_dig}"] = cel_cloud
            # --- NUEVA LÓGICA: EXTRACCIÓN Y SUMA INTELIGENTE (MULTI-FORMATO) ---
            items_extraidos = []
            tipos_vistos = set()
            ci = render.get('control_interno', {})
            tc_itin = ci.get('tipo_cambio_aplicado', 3.8)
            try: tc_itin = float(tc_itin or 3.8)
            except: tc_itin = 3.8

            # 1. PRIORIDAD: Precios Cierre (Itinerario Automático)
            precios_cierre = render.get('precios_cierre', [])
            if precios_cierre and isinstance(precios_cierre, list):
                for pc in precios_cierre:
                    label = pc.get('label', '').upper()
                    m_raw = pc.get('monto_total', 0) or 0
                    try: monto_total = float(str(m_raw).replace(',', ''))
                    except: monto_total = 0.0
                    simbolo = pc.get('simbolo', '$')
                    
                    t_code = 'NACIONAL' if 'NACIONAL' in label else ('EXTRANJERO' if 'EXTRANJERO' in label else 'CAN')
                    es_usd = (simbolo == '$')
                    
                    pax_info = ci.get('desglose_pasajeros', {}).get(t_code.lower(), {})
                    c_f = sum(int(v or 0) for v in pax_info.values()) if isinstance(pax_info, dict) else 0
                    if not c_f: c_f = 1
                    
                    p_f_soles = monto_total * tc_itin if es_usd else monto_total
                    items_extraidos.append({
                        "descripcion": f"Pax {t_code.capitalize()} (Auto-Total)", 
                        "cantidad": int(c_f), 
                        "precio_unitario": p_f_soles / int(c_f), 
                        "tipo": t_code, 
                        "p_raw": monto_total / int(c_f),
                        "moneda": "USD" if es_usd else "PEN"
                    })
                    tipos_vistos.add(t_code)

            # 2. SEGUNDA OPCIÓN: Precios Estructurados
            precios_meta = render.get('precios', {})
            if not items_extraidos and precios_meta:
                mapeo_p = [('NACIONAL', ['nacional', 'nac']), ('EXTRANJERO', ['extranjero', 'ext']), ('CAN', ['can'])]
                for t_code, keys in mapeo_p:
                    p_data = None
                    for k in keys:
                        p_data = precios_meta.get(k)
                        if p_data is not None: break
                    
                    if p_data is not None:
                        try:
                            if isinstance(p_data, dict): 
                                m_raw = p_data.get('total') or p_data.get('monto') or 0
                                p_raw = float(str(m_raw).replace(',', ''))
                            else: 
                                p_raw = float(str(p_data).replace(',', ''))
                        except:
                            p_raw = 0.0
                        
                        if p_raw > 0:
                            moneda_key = f"moneda_{t_code.lower()}"
                            moneda_fix = precios_meta.get(moneda_key)
                            es_usd = (moneda_fix == "USD") if moneda_fix else (t_code in ['EXTRANJERO', 'CAN'])
                            c_f = int(render.get(f'num_pax_{t_code.lower()[0:3]}', 1) or 1)
                            
                            p_f_soles = p_raw * tc_itin if es_usd else p_raw
                            items_extraidos.append({
                                "descripcion": f"Pax {t_code.capitalize()} (Precio)", 
                                "cantidad": c_f, "precio_unitario": p_f_soles, "tipo": t_code, "p_raw": p_raw,
                                "moneda": "USD" if es_usd else "PEN"
                            })
                            tipos_vistos.add(t_code)

            # 3. FALLBACK LEGACY
            if not items_extraidos:
                # Intento por detalle_ingresos si existe (B2C puede tenerlo)
                det_ing = render.get('detalle_ingresos', [])
                if isinstance(det_ing, list) and det_ing:
                    for d in det_ing:
                        t = str(d.get('tipo', '')).upper()
                        if t in ['EXT', 'INT', 'EXTRANJERO']: t = 'EXTRANJERO'
                        elif t in ['NAC', 'NACIONAL']: t = 'NACIONAL'
                        c = int(d.get('cantidad', 1) or 1)
                        p_u_str = str(d.get('precio_unitario', '0')).replace(',', '')
                        try: p_raw = float(p_u_str)
                        except: p_raw = 0.0
                        es_usd = (t in ['EXTRANJERO', 'CAN'])
                        p_soles = p_raw * tc_itin if es_usd else p_raw
                        items_extraidos.append({"descripcion": d.get('descripcion') or f"Pax {t.capitalize()}", "cantidad": c, "precio_unitario": p_soles, "tipo": t, "p_raw": p_raw, "moneda": "USD" if es_usd else "PEN"})
                        tipos_vistos.add(t)
                
                # Intento por num_pax_nac en raíz
                if not items_extraidos:
                    fallbacks = [('NACIONAL', ['num_pax_nac', 'pax_nac'], ['precio_nacional', 'p_nac']), ('EXTRANJERO', ['num_pax_ext', 'pax_ext'], ['precio_extranjero', 'p_ext'])]
                    for t_code, c_keys, p_keys in fallbacks:
                        c_f = 0
                        for ck in c_keys:
                            c_f = int(render.get(ck, 0) or 0)
                            if c_f > 0: break
                        if c_f > 0:
                            p_f_raw = 0.0
                            for pk in p_keys:
                                val_pk = render.get(pk, 0) or 0
                                try: p_f_raw = float(str(val_pk).replace(',', ''))
                                except: p_f_raw = 0.0
                                if p_f_raw > 0: break
                            es_usd = (t_code in ['EXTRANJERO', 'CAN'])
                            p_f_soles = p_f_raw * tc_itin if es_usd else p_f_raw
                            items_extraidos.append({"descripcion": f"Pax {t_code.capitalize()} (Legacy)", "cantidad": c_f, "precio_unitario": p_f_soles, "tipo": t_code, "p_raw": p_f_raw, "moneda": "USD" if es_usd else "PEN"})

            if id_itinerario_dig:
                st.session_state[f"items_itin_{id_itinerario_dig}"] = items_extraidos
                
                if id_itinerario_dig != st.session_state.get('last_loaded_itin'):
                    current_tc_form = st.session_state.get('tc_ref_manual_form', tc_itin)
                    moneda_final = st.session_state.get('moneda_auto', 'PEN')
                    
                    nuevo_calc = 0.0
                    for it in items_extraidos:
                        if moneda_final == "USD":
                            nuevo_calc += it['cantidad'] * (it['p_raw'] if it['moneda'] == "USD" else it['p_raw'] / current_tc_form)
                        else:
                            nuevo_calc += it['cantidad'] * (it['p_raw'] * current_tc_form if it['moneda'] == "USD" else it['p_raw'])
                            
                    st.session_state['m_total'] = round(nuevo_calc, 2)
                    st.session_state['last_loaded_itin'] = id_itinerario_dig
                    st.success(f"✅ Itinerario cargado: **{tour_nombre_cloud}** (Sincronizado: {moneda_final} {nuevo_calc:,.2f})")
                else:
                    st.success(f"✅ Itinerario cargado: **{tour_nombre_cloud}**")

                # Insertar el componente de descarga idéntico al de Operaciones
                from vistas.page_operaciones import render_itinerary_simple_download
                render_itinerary_simple_download(render)

                with st.expander("👀 Ver Desglose Día por Día", expanded=False):
                    render_itinerary_details_visual(render)


    # --- 💳 BALANCE Y MONEDA (TIEMPO REAL / INTERACTIVO) ---
    st.markdown("### 💰 Detalles de Pago")
    c_m0, c_m1, c_m2, c_m3 = st.columns([1, 1.5, 1.5, 1.5])
    
    # Auto-seleccionar moneda desde itinerario
    monedas_list = ["USD", "PEN"]
    moneda_auto = st.session_state.get('moneda_auto', 'USD')
    
    # --- MOSTRAR SUB-TOTALES POR MONEDA (PEDIDO USUARIO) ---
    if id_itinerario_dig:
        items_ref = st.session_state.get(f"items_itin_{id_itinerario_dig}", [])
        if items_ref:
            sub_soles = sum(it['cantidad'] * it['p_raw'] for it in items_ref if it.get('moneda') == 'PEN')
            sub_dolares = sum(it['cantidad'] * it['p_raw'] for it in items_ref if it.get('moneda') == 'USD')
            
            st.markdown(f"📊 **SUB-TOTALES POR MONEDA:** Soles: **S/ {sub_soles:,.2f}** | Dólares: **$ {sub_dolares:,.2f}**")

    # Eliminamos el index calculable y pasamos directamente el key a Streamlit para que recuerde el estado
    moneda_sel = c_m0.selectbox("Moneda", monedas_list, key="moneda_auto", help="Puede elegir la divisa de cobro manual")
    
    # TC: Tipo de Cambio "Foto Congelada" - Se intenta jalar automático
    default_tc = ExchangeService.get_current_tc()
    tipo_cambio = c_m1.number_input(
        "Tipo de Cambio (Foto)", 
        min_value=0.0, 
        value=default_tc, 
        format="%.3f", 
        help="A cuánto está el dólar hoy para esta venta",
        key="tc_ref_manual_form"
    )
    # Guardar en session para el cargado de itinerarios posterior
    st.session_state['tipo_cambio_ref_ui'] = tipo_cambio

    # --- RECÁLCULO DINÁMICO: Usar el TC del usuario y la Moneda para actualizar el total ---
    if id_itinerario_dig and tipo_cambio > 0:
        items_recalc = st.session_state.get(f"items_itin_{id_itinerario_dig}", [])
        if items_recalc:
            nuevo_total = 0.0
            
            # Lógica:
            # Si se elige "USD", todo se cobra en Dólares. Los peruanos (Nacional en PEN) se dividen entre el TC.
            # Si se elige "PEN", todo se cobra en Soles. Los extranjeros (Tienen tarifa USD) se multiplican por el TC.
            for it in items_recalc:
                item_moneda = it.get('moneda', 'PEN')
                if moneda_sel == "USD":
                    # Cobramos en Dólares
                    if item_moneda == "USD":
                        nuevo_total += it['cantidad'] * it['p_raw']
                    else:
                        nuevo_total += it['cantidad'] * (it['p_raw'] / tipo_cambio)
                else:
                    # Cobramos en Soles (PEN)
                    if item_moneda == "USD":
                        nuevo_total += it['cantidad'] * (it['p_raw'] * tipo_cambio)
                    else:
                        nuevo_total += it['cantidad'] * it['p_raw']
                        
            st.session_state['m_total'] = round(nuevo_total, 2)

    if 'm_total' not in st.session_state: st.session_state['m_total'] = 0.0
    if 'm_pago' not in st.session_state: st.session_state['m_pago'] = 0.0
    
    monto_total = c_m2.number_input(f"Monto Total ({moneda_sel})", min_value=0.0, format="%.2f", key="m_total", disabled=(id_itinerario_dig is not None))
    monto_pagado = c_m3.number_input(f"Monto Pagado ({moneda_sel})", min_value=0.0, format="%.2f", key="m_pago")
    
    # --- MOSTRAR CONVERSIÓN EN TIEMPO REAL ---
    if tipo_cambio > 0:
        if moneda_sel == "USD":
            c_m2.caption(f"🛡️ Equiv: **S/ {monto_total * tipo_cambio:,.2f}**")
            c_m3.caption(f"🛡️ Equiv: **S/ {monto_pagado * tipo_cambio:,.2f}**")
        else:
            c_m2.caption(f"🛡️ Equiv: **$ {monto_total / tipo_cambio:,.2f}**")
            c_m3.caption(f"🛡️ Equiv: **$ {monto_pagado / tipo_cambio:,.2f}**")

    saldo = monto_total - monto_pagado
    
    # Visualización Dinámica del Saldo
    if monto_total > 0:
        col_saldo = st.container()
        if saldo <= 0.01: # Margen de error flotante
             col_saldo.success(f"✅ **VENTA SALDADA** (Saldo: {moneda_sel} 0.00)")
        else:
             porcentaje = (monto_pagado / monto_total) * 100
             # Mostrar saldo en ambas monedas
             if moneda_sel == "USD":
                 info_saldo = f"⏳ **SALDO PENDIENTE: ${saldo:,.2f}** (S/ {saldo * tipo_cambio:,.2f})"
             else:
                 info_saldo = f"⏳ **SALDO PENDIENTE: S/ {saldo:,.2f}** (${saldo / tipo_cambio:,.2f})"
             col_saldo.warning(f"{info_saldo} (A cuenta: {porcentaje:.0f}%)")
             
    # --- 📝 FORMULARIO DE REGISTRO ---
    with st.form("form_registro_venta"):
        col1, col2 = st.columns(2)
        
        # Valores por defecto basados en Lead o en la Consulta Cloud
        def_nombre = st.session_state.get(f"val_nom_{id_itinerario_dig}", lead_data.get('nombre_pasajero', '') if lead_data else '')
        def_tour = st.session_state.get(f"val_tour_{id_itinerario_dig}", "")

        # --- SE HA MOVIDO EL BALANCE FUERA DEL FORMULARIO PARA INTERACTIVIDAD --
        
        st.divider()

        # Opciones de bloqueo si hay itinerario
        edit_manual = False
        is_disabled = False
        if id_itinerario_dig and not edit_manual:
            is_disabled = True
            
        nombre = col1.text_input("Nombre Cliente", value=def_nombre, disabled=False)
        def_cel = lead_data.get('numero_celular', '') if lead_data else st.session_state.get(f"val_cel_{id_itinerario_dig}", '')
        tel = col1.text_input("Celular", value=def_cel, disabled=False)
        
        vendedor_actual = st.session_state.get('user_id', 'Admin')
        col1.markdown(f"👤 **Vendedor:** {vendedor_actual}")
        
        # Tour: Auto-completado desde itinerario, pero editable manualmente
        id_paquete = col2.text_input(
            "Nombre del Tour / Paquete", 
            value=def_tour,
            placeholder="Ej: Cusco Mágico & Machu Picchu",
            disabled=False,
            help="Se auto-completa si seleccionas un itinerario"
        )
        
        # --- CÁLCULO PREVIO DE PAX SI HAY ITINERARIO ---
        def_pax = 1
        if id_itinerario_dig:
            render = mapa_itinerarios.get(itinerario_seleccionado, {}).get('datos_render', {})
            if render.get('control_interno'):
                def_pax = render['control_interno'].get('total_pasajeros') or render['control_interno'].get('total_pax') or 1
            elif render.get('detalle_ingresos'):
                def_pax = sum(int(d.get('cantidad', 0)) for d in render['detalle_ingresos'])
            else:
                def_pax = render.get('cantidad_pax') or render.get('pax_count') or 1
        
        cantidad_pax = col1.number_input("Cantidad Pax", min_value=1, value=int(def_pax), disabled=is_disabled)
        
        tipo_comp = col2.radio("Tipo Comprobante", ["BOLETA", "FACTURA", "RECIBO SIMPLE"], horizontal=True)
        metodo_pago = col2.selectbox("💳 Método de Pago", ["EFECTIVO", "TRANSFERENCIA", "YAPE", "PLIN", "TARJETA", "PAYPAL", "IZIPAY", "VISA", "MASTER CARD", "INTERBANK", "OTRO"])

        
        # --- 📅 CÁLCULO AUTOMÁTICO DE FECHAS ---
        itin_fecha_inicio = date.today()
        itin_fecha_fin = date.today()
        
        if id_itinerario_dig:
            render = mapa_itinerarios.get(itinerario_seleccionado, {}).get('datos_render', {})
            f_viaje = render.get('fecha_viaje') or render.get('fecha_inicio') or render.get('fechaViaje') or render.get('fecha')
            if not f_viaje and render.get('control_interno'):
                ci = render.get('control_interno', {})
                f_viaje = ci.get('fecha_inicio') or ci.get('fecha_llegada') or ci.get('fecha_viaje')
            if not f_viaje:
                dias = render.get('itinerario') or render.get('days') or render.get('itinerario_detalles')
                if dias and isinstance(dias, list) and len(dias) > 0 and isinstance(dias[0], dict):
                    f_viaje = dias[0].get('fecha')
                
            if f_viaje:
                try: 
                    # Limpiar espacios: "23 / 02 / 2026" -> "23/02/2026"
                    f_clean = str(f_viaje).replace(" ", "").strip()
                    if '/' in f_clean:
                        try:
                            itin_fecha_inicio = datetime.strptime(f_clean, "%d/%m/%Y").date()
                        except ValueError:
                            try:
                                itin_fecha_inicio = datetime.strptime(f_clean, "%Y/%m/%d").date()
                            except ValueError:
                                # Último intento MM/DD/YYYY
                                itin_fecha_inicio = datetime.strptime(f_clean, "%m/%d/%Y").date()
                    elif '-' in f_clean:
                        itin_fecha_inicio = date.fromisoformat(f_clean[:10])
                except: pass
            
            # Calcular Fin basado en Duración (ej: "3D")
            itin_fecha_fin = itin_fecha_inicio
            duracion_raw = render.get('duracion')
            if duracion_raw and isinstance(duracion_raw, str) and 'D' in duracion_raw.upper():
                try:
                    num_dias_str = ''.join(filter(str.isdigit, duracion_raw.split('D')[0]))
                    if num_dias_str:
                        num_dias = int(num_dias_str)
                        itin_fecha_fin = itin_fecha_inicio + timedelta(days=num_dias - 1)
                except Exception as e:
                    print(f"Error calculando fecha fin: {e}")
            
            # Mostrar Pax Count (Búsqueda robusta)
            num_pax = 1
            if render.get('control_interno'):
                num_pax = render['control_interno'].get('total_pasajeros') or render['control_interno'].get('total_pax') or 1
            elif render.get('detalle_ingresos'):
                num_pax = sum(int(d.get('cantidad', 0)) for d in render['detalle_ingresos'])
            else:
                num_pax = render.get('cantidad_pax') or render.get('pax_count') or 1

            st.success(f"🗓️ **Viaje Programado:** Del {itin_fecha_inicio.strftime('%d/%m/%Y')} al {itin_fecha_fin.strftime('%d/%m/%Y')} | 👥 **Pax:** {num_pax}")
            fecha_inicio_sel = itin_fecha_inicio
            fecha_fin_sel = itin_fecha_fin
        else:
            c_f1, c_f2 = st.columns(2)
            fecha_inicio_sel = c_f1.date_input("Fecha Inicio", value=date.today())
            fecha_fin_sel = c_f2.date_input("Fecha Fin", value=date.today())
        
        # --- NUEVO: DESGLOSE DE INGRESOS (USANDO CACHE DE SESIÓN) ---
        st.markdown("##### 📝 Desglose de Ingresos (Opcional)")
        items_ingreso = []
        if id_itinerario_dig:
            cached_items = st.session_state.get(f"items_itin_{id_itinerario_dig}", [])
            if cached_items:
                for it in cached_items:
                    # RECALCULAR PRECIO UNITARIO con el TC actual del formulario para evitar discrepancias
                    item_moneda = it.get('moneda', 'PEN')
                    p_unit_final = it['p_raw'] * tipo_cambio if item_moneda == "USD" else it['p_raw']
                    
                    desc = it['descripcion']
                    if item_moneda == "USD":
                        desc += f" (Ref: ${it['p_raw']:.2f} x {tipo_cambio})"
                    
                    items_ingreso.append({
                        "descripcion": desc,
                        "cantidad": it['cantidad'],
                        "precio_unitario": p_unit_final
                    })
                    st.info(f"✨ **{desc}**: Se han cargado **{it['cantidad']}** pax a **S/ {p_unit_final:,.2f}** c/u.")
            else:
                st.warning("⚠️ No se encontró desglose en este itinerario.")
        else:
            st.caption("No hay itinerario vinculado. El desglose se generará automáticamente por el total.")
        
        st.markdown("##### 🛡️ Información de Emergencia y Logística")
        col_log1, col_log2 = st.columns(2)
        vuelo_int = col_log1.text_input("Nro de Vuelo Internacional", placeholder="Ej: AA947 / LA2345")
        correo_cli = col_log2.text_input("Correo Electrónico", placeholder="ejemplo@correo.com")
        
        cont_nom = col_log1.text_input("Nombre del Contacto de Emergencia", placeholder="Ej: María García (Hermana)")
        cont_tel = col_log2.text_input("Teléfono del Contacto de Emergencia", placeholder="+51 999 888 777")

        comentarios_op = st.text_area("🗒️ Comentarios para Operaciones", placeholder="Ej: Pasajero alérgico, requiere recojo puntual, etc.", key="coment_op_b2c")

        st.markdown("##### 🏨 Datos Adicionales para el Voucher (sólo para el documento)")
        cv1, cv2, cv3 = st.columns(3)
        v_pasaporte  = cv1.text_input("Pasaporte / DNI", placeholder="Ej: AAH121307")
        v_hotel      = cv2.text_input("Hotel de Hospedaje", placeholder="Ej: Casa Andina 3*")
        v_nacionalidad = cv3.text_input("Nacionalidad", placeholder="Ej: ARGENTINA")
        cv4, cv5 = st.columns(2)
        v_adultos    = cv4.number_input("N° Adultos", min_value=0, value=int(def_pax), step=1)
        v_estudiantes = cv5.number_input("N° Estudiantes", min_value=0, value=0, step=1)

        st.markdown("##### 📧 Notificaciones y Adjuntos")
        c_not1, c_not2 = st.columns([1, 1])
        enviar_notif = c_not1.checkbox("Enviar Resumen por Correo Corporativo", value=True, help="Envía un resumen de la venta a los correos de gerencia y reservas.")
        archivos_adjuntos = c_not2.file_uploader("Adjuntar Comprobantes o Fotos", accept_multiple_files=True, help="Opcional: Estas imágenes se enviarán como adjuntos en el correo.")

        submitted = st.form_submit_button("🚀 REGISTRAR VENTA Y NOTIFICAR", use_container_width=True)

        if submitted:
            # Validación previa
            id_lead_final = id_lead_seleccionado or id_lead_from_itinerario
            if not id_lead_final:
                st.error("❌ Debes seleccionar un Lead. No se puede registrar una venta sin Lead vinculado.")
            elif not nombre or not tel:
                st.error("❌ El Nombre y el Celular son obligatorios.")
            elif not id_paquete:
                st.error("❌ El nombre del Tour/Paquete es obligatorio.")
            elif monto_total <= 0:
                st.error("❌ El Monto Total debe ser mayor a 0.")
            else:
                exito, msg = venta_controller.registrar_venta_directa(
                    nombre_cliente=nombre,
                    telefono=tel,
                    origen="Directo",
                    vendedor=vendedor_actual, 
                    tour=id_paquete,
                    tipo_hotel="Estándar", 
                    fecha_inicio=fecha_inicio_sel.isoformat(),
                    fecha_fin=fecha_fin_sel.isoformat(),
                    monto_total=monto_total,
                    monto_depositado=monto_pagado,
                    tipo_comprobante=tipo_comp,
                    moneda=moneda_sel,
                    tipo_cambio=tipo_cambio,
                    id_itinerario_digital=id_itinerario_dig if id_itinerario_dig else None,
                    id_lead=id_lead_seleccionado or id_lead_from_itinerario,
                    items_ingreso=items_ingreso if items_ingreso else None,
                    metodo_pago=metodo_pago,
                    cantidad_pax=int(cantidad_pax),
                    comentarios=comentarios_op,
                    vuelo_internacional=vuelo_int,
                    correo=correo_cli,
                    contacto_emergencia_nombre=cont_nom,
                    contacto_emergencia_tel=cont_tel,
                    enviar_correo=enviar_notif,
                    adjuntos={f.name: f.getvalue() for f in archivos_adjuntos} if archivos_adjuntos else None
                )
                
                if exito:
                    # --- Generar Voucher PDF (datos temporales, no se guardan en DB) ---
                    try:
                        from controllers.pdf_controller import PDFController
                        pdf_ctrl = PDFController()

                        # Obtener datos_render del itinerario seleccionado
                        render_para_voucher = {}
                        if id_itinerario_dig and itinerario_seleccionado != "--- Sin Itinerario ---":
                            it_raw = mapa_itinerarios.get(itinerario_seleccionado, {})
                            render_para_voucher = it_raw.get('datos_render', {})
                            if isinstance(render_para_voucher, str):
                                import json
                                try: render_para_voucher = json.loads(render_para_voucher)
                                except: render_para_voucher = {}

                        voucher_data = {
                            'nombre_cliente':       nombre,
                            'telefono_cliente':     tel,
                            'correo_cliente':       correo_cli,
                            'fecha_inicio':         fecha_inicio_sel.strftime('%d/%m/%Y'),
                            'fecha_fin':            fecha_fin_sel.strftime('%d/%m/%Y'),
                            'monto_total':          monto_total,
                            'monto_depositado':     monto_pagado,
                            'moneda':               moneda_sel,
                            'cantidad':             int(cantidad_pax),
                            # Temporales (voucher only)
                            'pasaporte':            v_pasaporte or '---',
                            'hotel':                v_hotel or '---',
                            'nacionalidad':         v_nacionalidad or '---',
                            'num_adultos_voucher':  int(v_adultos),
                            'num_estudiantes_voucher': int(v_estudiantes),
                            # Itinerario
                            'datos_render':         render_para_voucher,
                        }

                        pdf_bytes_io = pdf_ctrl.generar_voucher_reserva_pdf(voucher_data)
                        if pdf_bytes_io:
                            pdf_bytes = pdf_bytes_io.read()
                            st.session_state['voucher_pdf_bytes'] = pdf_bytes
                            st.session_state['voucher_pdf_nombre'] = f"Voucher_{nombre.replace(' ','_')}.pdf"

                            # Si el correo está activo, adjuntar el voucher automáticamente
                            if enviar_notif:
                                from utils.email_helper import enviar_notificacion_venta_async
                                venta_notif = {
                                    'nombre_cliente':  nombre,
                                    'tour':            id_paquete,
                                    'vendedor':        vendedor_actual,
                                    'cantidad':        int(cantidad_pax),
                                    'fecha_inicio':    fecha_inicio_sel.strftime('%d/%m/%Y'),
                                    'fecha_fin':       fecha_fin_sel.strftime('%d/%m/%Y'),
                                    'moneda':          moneda_sel,
                                    'monto_total':     monto_total,
                                    'monto_depositado': monto_pagado,
                                    'saldo':           monto_total - monto_pagado,
                                    'metodo_pago':     metodo_pago,
                                    'comentarios':     comentarios_op,
                                }
                                adjuntos_final = {f.name: f.getvalue() for f in archivos_adjuntos} if archivos_adjuntos else {}
                                adjuntos_final[st.session_state['voucher_pdf_nombre']] = pdf_bytes
                                enviar_notificacion_venta_async(venta_notif, adjuntos_final)
                        else:
                            # Si no se pudo generar PDF, igual enviar correo sin adjunto
                            if enviar_notif:
                                from utils.email_helper import enviar_notificacion_venta_async
                                venta_notif = {
                                    'nombre_cliente':  nombre,
                                    'tour':            id_paquete,
                                    'vendedor':        vendedor_actual,
                                    'cantidad':        int(cantidad_pax),
                                    'fecha_inicio':    fecha_inicio_sel.strftime('%d/%m/%Y'),
                                    'fecha_fin':       fecha_fin_sel.strftime('%d/%m/%Y'),
                                    'moneda':          moneda_sel,
                                    'monto_total':     monto_total,
                                    'monto_depositado': monto_pagado,
                                    'saldo':           monto_total - monto_pagado,
                                    'metodo_pago':     metodo_pago,
                                    'comentarios':     comentarios_op,
                                }
                                adjuntos_final = {f.name: f.getvalue() for f in archivos_adjuntos} if archivos_adjuntos else None
                                enviar_notificacion_venta_async(venta_notif, adjuntos_final)

                    except Exception as e_pdf:
                        st.warning(f"⚠️ Venta registrada, pero hubo un problema generando el Voucher: {e_pdf}")

                    st.success(msg)
                    st.balloons()
                else:
                    st.error(msg)

    # --- Boton de descarga del Voucher PDF (fuera del form, persiste en sesión) ---
    if st.session_state.get('voucher_pdf_bytes'):
        st.divider()
        st.success("✅ Voucher PDF generado y adjuntado al correo. ¡También puedes descargarlo aquí!")
        st.download_button(
            label="📅 Descargar Voucher de Reserva (PDF)",
            data=st.session_state['voucher_pdf_bytes'],
            file_name=st.session_state.get('voucher_pdf_nombre', 'Voucher_Reserva.pdf'),
            mime='application/pdf',
            use_container_width=True
        )
        if st.button("🗑️ Limpiar", key="limpiar_voucher"):
            del st.session_state['voucher_pdf_bytes']
            st.rerun()

def render_reminders_dashboard():
    lead_controller = st.session_state.get('lead_controller')
    if not lead_controller: st.error("Error de inicialización."); return
    
    st.subheader("🔔 Panel de Alertas de Seguimiento")
    leads = lead_controller.obtener_todos_leads()
    
    if not leads:
        st.info("No hay recordatorios pendientes.")
        return
        
    df = pd.DataFrame(leads)
    
    # Filtrar solo recordatorios (asumiendo que los marcamos con REC: o tienen fecha_seguimiento)
    if 'red_social' in df.columns:
        df_rec = df[df['red_social'].str.contains("REC:", na=False)].copy()
    else:
        df_rec = pd.DataFrame()

    if df_rec.empty:
        st.info("No hay clientes en la agenda de recordatorios.")
        return

    # Procesar fechas para alertas
    hoy = date.today()
    
    # Intentar obtener fecha_seguimiento, si no, parsear de red_social si lo guardamos ahí temporalmente
    # Pero ahora ya tenemos el campo en el modelo.
    if 'fecha_seguimiento' in df_rec.columns:
        df_rec['fecha_seguimiento'] = pd.to_datetime(df_rec['fecha_seguimiento']).dt.date
    else:
        df_rec['fecha_seguimiento'] = hoy # Fallback
        
    df_rec = df_rec.sort_values(by='fecha_seguimiento', ascending=True)

    # Clasificación
    atrasados = df_rec[df_rec['fecha_seguimiento'] < hoy]
    hoy_pendientes = df_rec[df_rec['fecha_seguimiento'] == hoy]
    futuros = df_rec[df_rec['fecha_seguimiento'] > hoy]

    # Visualización con Columnas
    c1, c2, c3 = st.columns(3)
    c1.metric("🔴 Atrasados", len(atrasados))
    c2.metric("🟠 Para Hoy", len(hoy_pendientes))
    c3.metric("🟢 Próximos", len(futuros))

    st.markdown("---")
    
    if not atrasados.empty:
        st.error("🚨 **CLIENTES QUE DEBISTE LLAMAR (ATRASADOS)**")
        for _, r in atrasados.iterrows():
            with st.expander(f"⚠️ {r.get('numero_celular')} - {r.get('fecha_seguimiento')}"):
                st.write(f"**Notas:** {r.get('comentario', 'Sin notas')}")
                st.write(f"**Vendedor:** {r.get('id_vendedor')}")
                if st.button(f"Llamada Realizada {r.get('id_lead')}"):
                    # Aquí iría lógica para actualizar estado
                    st.success("Gestión de seguimiento registrada.")

    if not hoy_pendientes.empty:
        st.warning("📅 **GESTIONES PARA HOY**")
        st.dataframe(hoy_pendientes[['numero_celular', 'comentario', 'id_vendedor']], use_container_width=True)

    st.write("📖 **Agenda Completa de Seguimiento**")
    st.dataframe(df_rec[['fecha_seguimiento', 'numero_celular', 'red_social', 'comentario']], use_container_width=True)

def formulario_recordatorio():
    lead_controller = st.session_state.get('lead_controller')
    if not lead_controller: st.error("Error de inicialización de LeadController."); return
    
    st.subheader("⏰ Nuevo Cliente Potencial (Recordatorio)")
    st.markdown("Registra aquí a los clientes que han mostrado interés pero comprarán en otra fecha.")
    
    with st.form("form_recordatorio"):
        col1, col2 = st.columns(2)
        nombre = col1.text_input("Nombre del Cliente")
        telefono = col1.text_input("Celular/WhatsApp")
        
        fecha_proxima = col2.date_input("Fecha Tentativa de Contacto/Compra")
        servicio_interes = col2.selectbox("Servicio de Interés", ["Cusco Tradicional", "Machu Picchu Full Day", "Valle Sagrado", "Montaña 7 Colores", "Laguna Humantay", "Otros"])
        
        vendedores_map = lead_controller.obtener_mapeo_vendedores()
        vendedor_sel = st.selectbox("Asignar a Vendedor", list(vendedores_map.values()))
        comentario = st.text_area("Notas / Observaciones (¿Por qué no compra ahora?)")
        
        submitted = st.form_submit_button("GUARDAR RECORDATORIO", use_container_width=True)
        
        if submitted:
            # Buscar ID del vendedor
            id_vendedor = next((id for id, name in vendedores_map.items() if name == vendedor_sel), None)
            
            if not telefono or not nombre:
                st.warning("El Nombre y el Celular son obligatorios.")
            else:
                exito, mensaje = lead_controller.registrar_nuevo_lead(
                    telefono=telefono, 
                    origen=f"REC: {servicio_interes}", 
                    vendedor=id_vendedor,
                    comentario=f"CLIENTE: {nombre} | {comentario}",
                    fecha_seguimiento=fecha_proxima.isoformat()
                )
                
                if exito:
                    st.success(f"📌 Recordatorio para {nombre} guardado correctamente.")
                    st.balloons()
                else:
                    st.error(mensaje)

def constructor_itinerarios():
    """Interfaz para generar el Itinerario Digital y sincronizar con Cloud."""
    it_controller = st.session_state.get('itinerario_digital_controller')
    lead_controller = st.session_state.get('lead_controller')
    
    st.subheader("🎨 Constructor de Itinerario Automático")
    st.info("Esta sección genera el diseño visual y lo sincroniza con el Lead en la nube.")

    # 1. Selección de Lead
    leads = lead_controller.obtener_todos_leads()
    if not leads:
        st.warning("No hay leads registrados para asignar un itinerario.")
        return

    df_leads = pd.DataFrame(leads)
    lead_options = {f"{r['numero_celular']} - {r['id_lead']}": r['id_lead'] for _, r in df_leads.iterrows()}
    lead_sel = st.selectbox("Seleccione el Lead (Cliente)", options=list(lead_options.keys()))
    id_lead_actual = lead_options[lead_sel]

    # 2. Datos del Itinerario
    with st.expander("📝 Datos Generales del Pasajero", expanded=True):
        col1, col2 = st.columns(2)
        nombre_pasajero = col1.text_input("Nombre que aparecerá en el PDF", placeholder="Ej: Familia Rodriguez")
        titulo_viaje = col2.text_input("Título del Programa", placeholder="Ej: Cusco Mágico & Machu Picchu")
        duracion = col1.text_input("Duración", placeholder="Ej: 4D-3N")
        fecha_viaje = col2.date_input("Fecha Tentativa")
        # El checkbox B2B se movió abajo, cerca del botón de generar

    # 3. Construcción del Itinerario por Días
    st.markdown("---")
    st.write("📅 **Detalle de Tours por Día**")
    
    # Sistema dinámico de ingreso de tours (Simplificado para este ejemplo)
    num_dias = st.number_input("Número de días a detallar", min_value=1, max_value=15, value=1)
    tours_detalles = []
    
    for i in range(num_dias):
        with st.expander(f"Día {i+1}", expanded=(i==0)):
            t_nom = st.text_input(f"Nombre del Tour Día {i+1}", key=f"t_nom_{i}")
            t_desc = st.text_area(f"Descripción breve Día {i+1}", key=f"t_desc_{i}")
            
            c_inc, c_exc = st.columns(2)
            t_inc = c_inc.text_area(f"Incluye (Día {i+1}) - Uno por línea", key=f"t_inc_{i}", placeholder="Ticket de Ingreso\nAlmuerzo Buffet")
            t_exc = c_exc.text_area(f"No Incluye (Día {i+1}) - Uno por línea", key=f"t_exc_{i}", placeholder="Cena\nPropinas")
            
            tours_detalles.append({
                "numero": i + 1,
                "fecha": (fecha_viaje + timedelta(days=i)).strftime("%d / %m / %Y"),
                "nombre": t_nom, 
                "descripcion": t_desc,
                "incluye": [x.strip() for x in t_inc.split("\n") if x.strip()],
                "no_incluye": [x.strip() for x in t_exc.split("\n") if x.strip()]
            })

    st.write("📈 **Configuración de Precios**")
    cp1, cp2, cp3 = st.columns(3)
    p_nac = cp1.number_input("Precio Nacional", min_value=0.0)
    m_nac = cp1.selectbox("Moneda Nacional", ["PEN", "USD"], key="m_nac")
    
    p_ext = cp2.number_input("Precio Extranjero", min_value=0.0)
    m_ext = cp2.selectbox("Moneda Extranjero", ["USD", "PEN"], key="m_ext")
    
    p_can = cp3.number_input("Precio CAN", min_value=0.0)
    m_can = cp3.selectbox("Moneda CAN", ["USD", "PEN"], key="m_can")

    # Configuración de la "Culebrita" y Highlights
    st.markdown("---")
    st.write("🌍 **Inclusiones y Exclusiones Generales (Globales)**")
    highlights = st.text_area("Hitos / Highlights (Separados por comas)", placeholder="Machu Picchu, Montaña de Colores, Valle Sagrado")
    
    col_g1, col_g2 = st.columns(2)
    inc_global = col_g1.text_area("Incluye (Global) - Uno por línea", placeholder="Traslados Aeropuerto\nSeguro de Viaje")
    exc_global = col_g2.text_area("No Incluye (Global) - Uno por línea", placeholder="Vuelos Internacionales\nGastos Personales")
    
    comentarios_generales = st.text_area("🗒️ Comentarios Generales (Para Operaciones)", placeholder="Ej: Pasajero es alérgico al maní. Requiere habitación en primer piso.")
    
    # Checkbox B2B reubicado para mayor visibilidad
    es_b2b = st.checkbox("🚩 Este itinerario es para Venta B2B / Agencia", value=False, help="Marque esta casilla si la venta proviene de una agencia aliada.")

    # 4. Botón de Generación y Sincronización
    if st.button("🚀 GENERAR ITINERARIO PDF & SINCRONIZAR CLOUD", use_container_width=True):
        if not nombre_pasajero:
            st.error("El nombre del pasajero es obligatorio para el PDF.")
        else:
            # Construir el paquete JSON (datos_render) solicitado por el usuario
            telefono_lead = lead_sel.split(' - ')[0] if ' - ' in lead_sel else ""
            datos_render = {
                "titulo": titulo_viaje,
                "duracion": duracion,
                "nombre_pasajero": nombre_pasajero,
                "cliente_telefono": telefono_lead,
                "fecha_viaje": fecha_viaje.isoformat(),
                "highlights": [h.strip() for h in highlights.split(",")],
                "inclusiones_globales": [h.strip() for h in inc_global.split("\n") if h.strip()],
                "exclusiones_globales": [h.strip() for h in exc_global.split("\n") if h.strip()],
                "comentarios_generales": comentarios_generales,
                "itinerario_detalles": tours_detalles, # Enviamos la lista de tours con nombre corregido
                "precios": {
                    "nacional": p_nac,
                    "extranjero": p_ext,
                    "can": p_can,
                    "moneda_nacional": m_nac,
                    "moneda_extranjero": m_ext,
                    "moneda_can": m_can
                },
                "vendedor_id": st.session_state.get('user_id'),
                "metadata": {
                    "version": "1.0",
                    "snake_code": "snake_default_vcp",
                    "generado_por": st.session_state.get('user_email'),
                    "tipo_venta": "B2B" if es_b2b else "B2C"
                }
            }

            with st.spinner("Generando PDF y sincronizando con Supabase..."):
                exito, msg, url_pdf = it_controller.registrar_generacion_itinerario(
                    id_lead=id_lead_actual,
                    nombre_pasajero=nombre_pasajero,
                    id_vendedor=st.session_state.get('user_id'),
                    datos_render=datos_render
                )
                
                if exito:
                    st.success(f"✅ {msg}")
                    if url_pdf:
                        st.markdown(f"### [📥 DESCARGAR ITINERARIO PDF]({url_pdf})")
                        st.info("El link también ha sido guardado en la ficha del lead.")
                    st.balloons()
                else:
                    st.error(msg)

def seguimiento_ventas_vendedor():
    venta_controller = st.session_state.get('venta_controller')
    if not venta_controller: st.error("Error de inicialización."); return
    
    st.subheader("📋 Mis Ventas y Seguimiento de Itinerarios")
    st.info("Desde aquí puedes sincronizar cambios si modificaste el itinerario en el constructor.")
    
    # 1. Obtener ventas (Simplificado para el vendedor)
    ventas = venta_controller.obtener_ventas_directas()
    if not ventas:
        st.info("No tienes ventas registradas para gestionar.")
        return
        
    for v in ventas[:10]: # Mostrar las 10 más recientes
        with st.container(border=True):
            col1, col2, col3 = st.columns([3, 2, 2])
            col1.markdown(f"👤 **{v['nombre_cliente']}**")
            col1.caption(f"📅 {v['fecha_inicio']} | ID: {v['id_venta']}")
            
            # Botón de Sincronización
            if col2.button("🔄 Sincronizar Itinerario", key=f"sync_v_{v['id_venta']}", help="Aplica los cambios realizados en el constructor a esta venta."):
                exito, msg = venta_controller.sincronizar_venta_con_itinerario(v['id_venta'])
                if exito: st.success(msg)
                else: st.error(msg)
            
            # Link al itinerario digital si existe (Carga robusta para evitar error de columna inexistente)
            res_it = venta_controller.client.table('itinerario_digital').select('*').eq('id_itinerario_digital', v['id_itinerario_digital']).single().execute()
            if res_it.data:
                # Prioridad 1: Columna real (si existiera en el futuro)
                # Prioridad 2: Dentro de datos_render (donde suele guardarse el backup)
                pdf_link = res_it.data.get('url_pdf') or res_it.data.get('datos_render', {}).get('url_pdf')
                
                if pdf_link:
                    col3.link_button("📄 Ver PDF Cloud", pdf_link, use_container_width=True)
                else:
                    col3.caption("🚫 Sin PDF")
            else:
                col3.caption("🚫 No encontrado")

def gestion_registros_multicanal():
    tabs = st.tabs(["💰 Registrar Nueva Venta", "📋 Mis Ventas Activas"])
    
    with tabs[0]:
        registro_ventas_directa()
    
    with tabs[1]:
        seguimiento_ventas_vendedor()

def mostrar_pagina(funcionalidad_seleccionada: str, supabase_client, rol_actual='Desconocido', user_id=None): 
    import controllers.lead_controller
    import controllers.venta_controller
    import controllers.itinerario_digital_controller
    import models.venta_model
    import importlib
    
    # Forzar recarga de módulos
    importlib.reload(models.venta_model)
    importlib.reload(controllers.lead_controller)
    importlib.reload(controllers.venta_controller)
    importlib.reload(controllers.itinerario_digital_controller)
    
    st.session_state.lead_controller = controllers.lead_controller.LeadController(supabase_client)
    st.session_state.venta_controller = controllers.venta_controller.VentaController(supabase_client)
    st.session_state.itinerario_digital_controller = controllers.itinerario_digital_controller.ItinerarioDigitalController(supabase_client)
    
    st.session_state.user_id = user_id

    # --- 🔔 Centro de Alertas Universal ---
    from controllers.operaciones_controller import OperacionesController
    from vistas.page_operaciones import render_centro_alertas
    ctrl_op = OperacionesController(supabase_client)
    render_centro_alertas(ctrl_op)

    if funcionalidad_seleccionada in ["Gestión de Registros", "Registro de Ventas (CRM)"]:
        gestion_registros_multicanal()
    elif funcionalidad_seleccionada == "Constructor Itinerarios":
        constructor_itinerarios()


