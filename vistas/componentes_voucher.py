# vistas/componentes_voucher.py
import streamlit as st
import pandas as pd
import json
import datetime
from controllers.pdf_controller import PDFController

def render_panel_voucher(supabase_client, id_venta_default=None, key_prefix="vch"):
    """
    Renders a unified voucher printing panel.
    If id_venta_default is provided, it loads that sale directly.
    Otherwise, it shows a dropdown to search and select a sale.
    """
    st.markdown("### 🎫 Panel de Impresión de Voucher de Reserva")
    
    # 1. Obtener todas las ventas para el selector si no hay una predefinida
    id_venta_act = id_venta_default
    
    if not id_venta_act:
        try:
            # Obtener ventas recientes para seleccionar
            res_sales = supabase_client.table('venta').select('id_venta, tour_nombre, canal_venta, precio_total_cierre, cliente(nombre)').order('id_venta', desc=True).limit(100).execute()
            sales_data = res_sales.data or []
            
            if not sales_data:
                st.info("No se encontraron ventas registradas.")
                return
                
            opciones = []
            mapa_ventas = {}
            for s in sales_data:
                cli_info = s.get('cliente') or {}
                cli_name = cli_info.get('nombre', 'Desconocido') if isinstance(cli_info, dict) else str(cli_info)
                lbl = f"ID: {s['id_venta']} | {cli_name} | {s.get('tour_nombre', 'Sin Tour')}"
                opciones.append(lbl)
                mapa_ventas[lbl] = s['id_venta']
                
            sel_lbl = st.selectbox("Seleccione la Venta para el Voucher:", ["--- Seleccione una venta ---"] + opciones, key=f"{key_prefix}_sel_box")
            if sel_lbl != "--- Seleccione una venta ---":
                id_venta_act = mapa_ventas[sel_lbl]
            else:
                return
        except Exception as e:
            st.error(f"Error cargando lista de ventas: {e}")
            return

    # 2. Cargar datos detallados de la venta activa
    try:
        res_v = supabase_client.table('venta').select('*, cliente(nombre, lead(numero_celular, pais_origen))').eq('id_venta', id_venta_act).single().execute()
        if not res_v.data:
            st.error("No se pudo encontrar la información de la venta especificada.")
            return
            
        v_raw = res_v.data
        cliente_nest = v_raw.get('cliente') or {}
        lead_nest = {}
        nombre_cliente = "Cliente"
        telefono_cliente = ""
        correo_cliente = ""
        nacionalidad_def = ""
        
        if isinstance(cliente_nest, dict):
            nombre_cliente = cliente_nest.get('nombre', 'Desconocido')
            lead_nest = cliente_nest.get('lead') or {}
            if isinstance(lead_nest, dict):
                telefono_cliente = lead_nest.get('numero_celular', '')
                correo_cliente = lead_nest.get('correo', '')
                nacionalidad_def = lead_nest.get('pais_origen', '')
                
        # Fallback de campos si vienen planos en la tabla venta
        telefono_cliente = v_raw.get('telefono_cliente') or telefono_cliente or '---'
        correo_cliente = v_raw.get('correo_cliente') or correo_cliente or '---'
        
        tour_nombre = v_raw.get('tour_nombre', 'Sin Tour')
        monto_total = float(v_raw.get('precio_total_cierre') or 0)
        moneda = v_raw.get('moneda', 'USD')
        num_pax = int(v_raw.get('num_pasajeros', 1))
        
        # Formatear fechas
        fecha_ini_raw = v_raw.get('fecha_inicio')
        fecha_fin_raw = v_raw.get('fecha_fin')
        
        # Convertir a objetos date o mantener string formateado
        try:
            if isinstance(fecha_ini_raw, str):
                d_ini = datetime.datetime.strptime(fecha_ini_raw.split("T")[0], "%Y-%m-%d")
                fecha_ini_str = d_ini.strftime("%d/%m/%Y")
            else:
                fecha_ini_str = "—"
        except:
            fecha_ini_str = str(fecha_ini_raw)
            
        try:
            if isinstance(fecha_fin_raw, str):
                d_fin = datetime.datetime.strptime(fecha_fin_raw.split("T")[0], "%Y-%m-%d")
                fecha_fin_str = d_fin.strftime("%d/%m/%Y")
            else:
                fecha_fin_str = "—"
        except:
            fecha_fin_str = str(fecha_fin_raw)
            
        # Calcular pagos abonados (monto_depositado)
        res_p = supabase_client.table('pago').select('monto_pagado, tipo_pago').eq('id_venta', id_venta_act).execute()
        pagos = res_p.data or []
        monto_pagado = sum(float(p['monto_pagado'] or 0) for p in pagos if p.get('tipo_pago') != 'REEMBOLSO')
        
        # Recuperar pasajeros de la venta para obtener documento / nacionalidad por defecto
        res_pasajeros = supabase_client.table('pasajero').select('tipo_documento, numero_documento, nacionalidad').eq('id_venta', id_venta_act).execute()
        lista_pax = res_pasajeros.data or []
        
        pasaporte_def = "---"
        if lista_pax:
            first_pax = lista_pax[0]
            pasaporte_def = f"{first_pax.get('tipo_documento','')} {first_pax.get('numero_documento','')}".strip() or "---"
            if not nacionalidad_def:
                nacionalidad_def = first_pax.get('nacionalidad', '')
                
        # Obtener itinerario digital vinculado
        render_para_voucher = {}
        id_itin_dig = v_raw.get('id_itinerario_digital')
        if id_itin_dig:
            res_it = supabase_client.table('itinerario_digital').select('datos_render').eq('id_itinerario_digital', id_itin_dig).single().execute()
            if res_it.data:
                render_para_voucher = res_it.data.get('datos_render')
                if isinstance(render_para_voucher, str):
                    try:
                        render_para_voucher = json.loads(render_para_voucher)
                    except:
                        render_para_voucher = {}
                        
    except Exception as e:
        st.error(f"Error al cargar datos de la venta {id_venta_act}: {e}")
        return

    # 3. Formulario para el Voucher
    st.markdown("#### 📝 Completar Información para el Voucher")
    
    with st.container(border=True):
        col_info1, col_info2 = st.columns(2)
        with col_info1:
            st.write(f"**👤 Cliente:** {nombre_cliente}")
            st.write(f"**📞 Teléfono:** {telefono_cliente}")
            st.write(f"**📧 Correo:** {correo_cliente}")
        with col_info2:
            st.write(f"**🚙 Tour:** {tour_nombre}")
            st.write(f"**📅 Fechas:** {fecha_ini_str} al {fecha_fin_str}")
            st.write(f"**💰 Total / Pagado:** {moneda} {monto_total:,.2f} / {moneda} {monto_pagado:,.2f}")

        st.divider()
        
        c_v1, c_v2, c_v3 = st.columns(3)
        v_pasaporte = c_v1.text_input("Pasaporte / DNI", value=pasaporte_def if pasaporte_def != "---" else "", placeholder="Ej: AAH121307", key=f"{key_prefix}_pasaporte_{id_venta_act}")
        v_hotel = c_v2.text_input("Hotel de Hospedaje", value="", placeholder="Ej: Casa Andina 3*", key=f"{key_prefix}_hotel_{id_venta_act}")
        v_nacionalidad = c_v3.text_input("Nacionalidad", value=nacionalidad_def, placeholder="Ej: PERUANA", key=f"{key_prefix}_nac_{id_venta_act}")
        
        c_v4, c_v5 = st.columns(2)
        v_adultos = c_v4.number_input("N° Adultos", min_value=0, value=num_pax, step=1, key=f"{key_prefix}_adultos_{id_venta_act}")
        v_estudiantes = c_v5.number_input("N° Estudiantes", min_value=0, value=0, step=1, key=f"{key_prefix}_estudiantes_{id_venta_act}")
        
        if st.button("🖨️ Generar PDF de Voucher", use_container_width=True, key=f"{key_prefix}_btn_gen_{id_venta_act}"):
            try:
                pdf_ctrl = PDFController()
                
                voucher_data = {
                    'nombre_cliente':       nombre_cliente,
                    'telefono_cliente':     telefono_cliente,
                    'correo_cliente':       correo_cliente,
                    'fecha_inicio':         fecha_ini_str,
                    'fecha_fin':            fecha_fin_str,
                    'monto_total':          monto_total,
                    'monto_depositado':     monto_pagado,
                    'moneda':               moneda,
                    'cantidad':             num_pax,
                    'tour_nombre':          tour_nombre,
                    'id_venta':             id_venta_act,
                    
                    # Datos del formulario
                    'pasaporte':            v_pasaporte or '---',
                    'hotel':                v_hotel or '---',
                    'nacionalidad':         v_nacionalidad or '---',
                    'num_adultos_voucher':  int(v_adultos),
                    'num_estudiantes_voucher': int(v_estudiantes),
                    'datos_render':         render_para_voucher,
                }
                
                pdf_bytes_io = pdf_ctrl.generar_voucher_reserva_pdf(voucher_data)
                
                if pdf_bytes_io:
                    pdf_bytes = pdf_bytes_io.read()
                    
                    # Calcular número de voucher
                    anio_2d = datetime.date.today().year % 100
                    mes_actual = datetime.date.today().month
                    num_v = f"{anio_2d:05d}-{mes_actual:02d}-{int(id_venta_act):05d}"
                    file_name = f"VOUCHER DE RESERVA {num_v} {nombre_cliente.upper()}.pdf"
                    
                    st.success("✅ Voucher PDF generado exitosamente.")
                    st.download_button(
                        label="📥 Descargar Voucher de Reserva (PDF)",
                        data=pdf_bytes,
                        file_name=file_name,
                        mime='application/pdf',
                        use_container_width=True,
                        key=f"{key_prefix}_dl_btn_{id_venta_act}"
                    )
            except Exception as e_pdf:
                st.error(f"Error generando el PDF del Voucher: {e_pdf}")
