# controllers/excel_controller.py
import pandas as pd
from io import BytesIO
import datetime
from openpyxl.styles import Alignment, Font, PatternFill

class ExcelController:
    """Controlador para la generación de documentos Excel a partir de datos del itinerario."""

    def generar_resumen_itinerario_xlsx(self, datos_render: dict, precios_reales: dict = None, nombre_cliente: str = None, num_pax: int = None) -> BytesIO:
        """
        Genera un archivo XLSX resumido para operaciones basado estrictamente en el itinerario.
        Permite inyectar 'precios_reales' (mapa {n_linea: precio}) desde la base de datos.
        """
        import openpyxl
        from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "RESUMEN_OPERATIVO"
        
        # --- ESTILOS ---
        bold_f = Font(bold=True)
        center_al = Alignment(horizontal='center', vertical='center')
        top_al = Alignment(vertical='top', wrap_text=True)
        
        # --- HEADER ---
        ws.merge_cells('A1:E1')
        titulo_itin = (datos_render.get('titulo') or datos_render.get('paquete_nombre') or 'ITINERARIO').upper()
        ws['A1'] = f"RESUMEN OPERATIVO: {titulo_itin}"
        ws['A1'].font = Font(bold=True, size=14)
        ws['A1'].alignment = center_al
        
        ws['A3'] = "FECHA INICIO:"
        
        # --- EXTRACCIÓN ROBUSTA DE FECHA (Misma lógica que Ventas) ---
        f_inicio = datos_render.get('fecha_viaje') or datos_render.get('fecha_inicio') or datos_render.get('fechaViaje') or datos_render.get('fecha')
        
        ci = datos_render.get('control_interno', {})
        if not f_inicio and ci:
            f_inicio = ci.get('fecha_inicio') or ci.get('fecha_llegada') or ci.get('fecha_viaje')
            
        if not f_inicio:
            dias_itin = datos_render.get('itinerario') or datos_render.get('days') or datos_render.get('itinerario_detalles')
            if dias_itin and isinstance(dias_itin, list) and len(dias_itin) > 0 and isinstance(dias_itin[0], dict):
                f_inicio = dias_itin[0].get('fecha')
        
        f_inicio_str = str(f_inicio).strip() if f_inicio else "---"
        
        # Extracción de fecha fin robusta
        f_fin_str = datos_render.get('fecha_fin') or datos_render.get('fechaFin')
        if not f_fin_str and f_inicio and f_inicio_str != "---":
            # Calcular base a duración
            duracion_raw = datos_render.get('duracion')
            if duracion_raw and isinstance(duracion_raw, str) and 'D' in duracion_raw.upper():
                try:
                    num_dias_str = ''.join(filter(str.isdigit, duracion_raw.split('D')[0]))
                    if num_dias_str:
                        num_dias = int(num_dias_str)
                        # Intento de parseo
                        f_clean = f_inicio_str.replace(" ", "")
                        obj_f_inicio = None
                        if '/' in f_clean:
                            for fmt in ("%d/%m/%Y", "%Y/%m/%d", "%m/%d/%Y"):
                                try:
                                    obj_f_inicio = datetime.datetime.strptime(f_clean, fmt).date()
                                    break
                                except: pass
                        elif '-' in f_clean:
                            obj_f_inicio = datetime.date.fromisoformat(f_clean[:10])
                        
                        if obj_f_inicio:
                            f_fin_obj = obj_f_inicio + datetime.timedelta(days=num_dias - 1)
                            f_fin_str = f_fin_obj.strftime("%d/%m/%Y")
                except Exception:
                    pass
        
        if not f_fin_str:
            f_fin_str = "---"

        ws['B3'] = f_inicio_str
        ws['D3'] = "FECHA FINAL:"
        ws['E3'] = f_fin_str
        
        ws['A4'] = "PASAJERO:"
        # Mapeo robusto de nombre: PRIORIDAD PARÁMETRO > POSIBLES_NOMBRES > PLACEHOLDER
        control_int = datos_render.get("control_interno") or {}
        posibles_nombres = [
            nombre_cliente, # Parámetro directo (Máxima prioridad)
            datos_render.get("nombre_pasajero"),
            datos_render.get("cliente_nombre"),
            datos_render.get("Cliente"),
            datos_render.get("cliente"),
            datos_render.get("pax_nombre"),
            control_int.get("cliente"),
            control_int.get("nombre_pasajero"),
            datos_render.get("titulo")
        ]
        nombre_pax = "---"
        for n in posibles_nombres:
            if n and str(n).strip() not in ["", "---", "None", "Desconocido", "Sin Título"]:
                nombre_pax = str(n).upper()
                break
        ws['B4'] = nombre_pax

        ws['D4'] = "TOTAL PAX:"
        # Mapeo robusto de PAX: PRIORIDAD PARÁMETRO > DB > CALCULADO
        p_total_param = int(num_pax or 0)
        p_total_db = int(datos_render.get("num_pasajeros") or 0)
        p_adultos = int(datos_render.get("num_adultos") or datos_render.get("adultos") or 0)
        p_ninos = int(datos_render.get("num_ninos") or datos_render.get("ninos") or 0)
        p_pax_fallback = int(datos_render.get("pax") or datos_render.get("total_pax") or 0)
        
        # Lógica de prioridad: 
        if p_total_param > 0:
            pax_count = p_total_param
        elif p_total_db > 0:
            pax_count = p_total_db
        else:
            pax_count = (p_adultos + p_ninos) if (p_adultos + p_ninos) > 0 else (p_pax_fallback if p_pax_fallback > 0 else 1)
        
        ws['E4'] = f"{pax_count} Personas"
        ws['E4'].font = bold_f

        # --- TABLA DE DÍAS ---
        current_row = 6
        headers = ["DÍA", "FECHA", "SERVICIO / TOUR", "PAX", "INCLUYE / NO INCLUYE"]
        for c_idx, h in enumerate(headers, 1):
            cell = ws.cell(row=current_row, column=c_idx, value=h)
            cell.font = bold_f
            cell.fill = PatternFill(start_color="DDDDDD", end_color="DDDDDD", fill_type="solid")
            cell.alignment = center_al
        current_row += 1

        items = (datos_render.get("itinerario_detalles") or 
                 datos_render.get("days") or 
                 datos_render.get("servicios") or 
                 datos_render.get("itinerario") or [])

        for i, d in enumerate(items):
            ws.cell(row=current_row, column=1, value=i+1).alignment = center_al
            ws.cell(row=current_row, column=2, value=d.get('fecha') or f"DIA {i+1}").alignment = center_al
            
            # Nombre del Servicio (Mapeo robusto)
            nombre_serv = (d.get('titulo') or d.get('nombre') or d.get('title') or d.get('servicio') or "---").upper()
            ws.cell(row=current_row, column=3, value=nombre_serv).font = bold_f
            
            ws.cell(row=current_row, column=4, value=pax_count).alignment = center_al
            
            # (Columna PRECIO eliminada por solicitud del usuario para reporte puramente logístico)
            # ws.cell(row=current_row, column=5, value=p_val).alignment = center_al
            
            # Detalles (Solo Inclusiones/Exclusiones, sin descripción)
            details_txt = []
            
            # Inclusiones
            inc_list = d.get('incluye') or d.get('inclusiones') or d.get('servicios') or []
            if isinstance(inc_list, list) and inc_list:
                details_txt.append("✅ INCLUYE:")
                for inc in inc_list:
                    txt = inc.get('texto') if isinstance(inc, dict) else inc
                    if txt: details_txt.append(f"  • {str(txt).upper()}")
            
            # Exclusiones
            exc_list = d.get('no_incluye') or d.get('exclusiones') or d.get('servicios_no') or []
            if isinstance(exc_list, list) and exc_list:
                if details_txt: details_txt.append("")
                details_txt.append("❌ NO INCLUYE:")
                for exc in exc_list:
                    txt = exc.get('texto') if isinstance(exc, dict) else exc
                    if txt: details_txt.append(f"  • {str(txt).upper()}")
            
            detail_cell = ws.cell(row=current_row, column=5, value="\n".join(details_txt))
            detail_cell.alignment = top_al
            detail_cell.font = Font(size=9)
            
            # Ajustar altura de fila basada en el contenido
            if details_txt:
                line_count = len(details_txt)
                ws.row_dimensions[current_row].height = max(20, line_count * 12)
            else:
                ws.row_dimensions[current_row].height = 20
            
            current_row += 1

        # --- ANCHOS DE COLUMNA ---
        ws.column_dimensions['A'].width = 5
        ws.column_dimensions['B'].width = 15
        ws.column_dimensions['C'].width = 45
        ws.column_dimensions['D'].width = 8
        ws.column_dimensions['E'].width = 75

        output = BytesIO()
        wb.save(output)
        output.seek(0)
        return output

    def generar_hoja_servicio_maestra_xlsx(self, data_hoja: dict) -> BytesIO:
        """
        Genera un Excel Maestro Premium Consolidado en una sola pestaña.
        """
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "EXPEDIENTE_MAESTRO"
        
        # --- ESTILOS PREMIUM ---
        header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
        subheader_fill = PatternFill(start_color="DBEAFE", end_color="DBEAFE", fill_type="solid")
        section_fill = PatternFill(start_color="334155", end_color="334155", fill_type="solid")
        pax_fill = PatternFill(start_color="059669", end_color="059669", fill_type="solid")
        
        white_font = Font(color="FFFFFF", bold=True)
        bold_font = Font(bold=True)
        thin_border = Border(
            left=Side(style='thin', color='CBD5E1'),
            right=Side(style='thin', color='CBD5E1'),
            top=Side(style='thin', color='CBD5E1'),
            bottom=Side(style='thin', color='CBD5E1')
        )
        center_al = Alignment(horizontal='center', vertical='center')
        left_al = Alignment(horizontal='left', vertical='center', indent=1)

        # --- DATA PREP ---
        v = data_hoja.get('venta', {})
        it = data_hoja.get('itinerario', [])
        pax = data_hoja.get('pasajeros', [])
        liq = data_hoja.get('liquidaciones', [])

        costo_total_liq = sum(float(l.get('costo_unitario') or 0) * (int(l.get('cantidad_pax') or v.get('num_pasajeros', 1))) for l in liq)
        monto_venta = float(v.get('monto_total') or 0)
        utilidad = monto_venta - costo_total_liq

        # --- SECCIÓN 1: PANEL DE CONTROL FINANCIERO ---
        ws.merge_cells('A1:H1')
        ws['A1'] = "REPORTE MAESTRO CONSOLIDADO: OPERACIONES & CONTABILIDAD"
        ws['A1'].font = Font(bold=True, size=16, color="1E3A8A")
        ws['A1'].alignment = center_al

        datos_v = [
            ["INFORMACIÓN GENERAL", "", ""],
            ["ID Venta", v.get('id_venta'), "Fecha Inicio"],
            ["Cliente Principal", v.get('nombre_cliente'), v.get('fecha_inicio')],
            ["Teléfono", v.get('telefono'), "Fecha Fin"],
            ["Servicio", v.get('tour_nombre'), v.get('fecha_fin')],
            ["Total Pax", f"{v.get('num_pasajeros')} PAX", ""],
            ["Carpeta Drive", v.get('drive_url') or "No vinculado", ""],
            ["", "", ""],
            ["RESUMEN FINANCIERO", "", ""],
            ["Moneda", v.get('moneda'), "Monto Venta"],
            ["Ingreso Total", monto_venta, "RECAUDADO"],
            ["Costo Total", costo_total_liq, "COSTO NETO"],
            ["UTILIDAD ESTIMADA", utilidad, "MARGEN"],
            ["Rentabilidad", f"{(utilidad / monto_venta * 100):.2f}%" if monto_venta > 0 else "0%", ""],
        ]
        
        current_row = 3
        for row in datos_v:
            is_header = row[0] in ["INFORMACIÓN GENERAL", "RESUMEN FINANCIERO"]
            if is_header:
                ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=3)
                cell = ws.cell(row=current_row, column=1, value=row[0])
                for c in range(1, 4):
                    ws.cell(row=current_row, column=c).fill = header_fill
                    ws.cell(row=current_row, column=c).font = white_font
                    ws.cell(row=current_row, column=c).border = thin_border
            else:
                for c_idx, val in enumerate(row, 1):
                    if val != "":
                        cell = ws.cell(row=current_row, column=c_idx, value=val)
                        cell.border = thin_border
                        # Formato especial para links
                        if row[0] == "Carpeta Drive" and c_idx == 2 and val.startswith("http"):
                            cell.hyperlink = val
                            cell.font = Font(color="0000FF", underline="single")
                        elif c_idx % 2 != 0: 
                            cell.fill = subheader_fill
                            cell.font = bold_font
            current_row += 1

        current_row += 2 # Espacio

        # --- SECCIÓN 2: LOGÍSTICA DIARIA (ITINERARIO) ---
        ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=8)
        ws.cell(row=current_row, column=1, value="📅 CRONOGRAMA LOGÍSTICO COMPLETO").font = white_font
        for c in range(1, 9): 
            ws.cell(row=current_row, column=c).fill = section_fill
            ws.cell(row=current_row, column=c).alignment = center_al
        current_row += 1

        headers_it = ["Día", "Fecha", "Hora", "Servicio / Tour", "Proveedor Sugerido", "Pax", "Tipo", "Observaciones"]
        for c_idx, h in enumerate(headers_it, 1):
            cell = ws.cell(row=current_row, column=c_idx, value=h)
            cell.fill = subheader_fill
            cell.font = bold_font
            cell.border = thin_border
            cell.alignment = center_al
        current_row += 1

        for s in it:
            ws.cell(row=current_row, column=1, value=s.get('Día Itin.'))
            ws.cell(row=current_row, column=2, value=s.get('Fecha'))
            ws.cell(row=current_row, column=3, value=s.get('Hora'))
            ws.cell(row=current_row, column=4, value=s.get('Servicio')).font = bold_font
            ws.cell(row=current_row, column=5, value=s.get('Proveedor'))
            ws.cell(row=current_row, column=6, value=s.get('Pax'))
            ws.cell(row=current_row, column=7, value=s.get('Tipo'))
            ws.cell(row=current_row, column=8, value=s.get('observacion') or "")
            for c in range(1, 9): ws.cell(row=current_row, column=c).border = thin_border
            current_row += 1

        current_row += 2 # Espacio

        # --- SECCIÓN 3: LIQUIDACIÓN DE COSTOS (DETALLE PROVEEDORES) ---
        ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=8)
        ws.cell(row=current_row, column=1, value="💰 DETALLE DE LIQUIDACIÓN Y PAGOS").font = white_font
        for c in range(1, 9): 
            ws.cell(row=current_row, column=c).fill = section_fill
            ws.cell(row=current_row, column=c).alignment = center_al
        current_row += 1

        headers_l = ["Día", "Proveedor Real", "Tipo Servicio", "Moneda", "Costo Unit.", "Cant/Pax", "Total Línea", "Estado"]
        for c_idx, h in enumerate(headers_l, 1):
            cell = ws.cell(row=current_row, column=c_idx, value=h)
            cell.fill = subheader_fill
            cell.font = bold_font
            cell.border = thin_border
        current_row += 1

        red_font = Font(color="FF0000", bold=True) # Rojo para pendientes

        for l in liq:
            ws.cell(row=current_row, column=1, value=l.get('n_linea'))
            prov_name = l.get('proveedor', {}).get('nombre_comercial', '---') if isinstance(l.get('proveedor'), dict) else '---'
            ws.cell(row=current_row, column=2, value=prov_name).font = bold_font
            ws.cell(row=current_row, column=3, value=l.get('tipo_servicio'))
            ws.cell(row=current_row, column=4, value=l.get('moneda'))
            
            c_unit = float(l.get('costo_unitario') or 0)
            pax_count = int(l.get('cantidad_pax') or v.get('num_pasajeros', 1))
            ws.cell(row=current_row, column=5, value=c_unit).number_format = '#,##0.00'
            ws.cell(row=current_row, column=6, value=pax_count)
            ws.cell(row=current_row, column=7, value=c_unit * pax_count).number_format = '#,##0.00'
            
            # Formateo condicional del estado
            estado_txt = "O.K." if l.get('terminado') else "Pte"
            cell_est = ws.cell(row=current_row, column=8, value=estado_txt)
            if estado_txt == "Pte":
                cell_est.font = red_font
            
            for c in range(1, 9): ws.cell(row=current_row, column=c).border = thin_border
            current_row += 1

        current_row += 2 # Espacio

        # --- SECCIÓN 4: ROOMING LIST ---
        ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=8)
        ws.cell(row=current_row, column=1, value="👥 LISTA DE PASAJEROS (ROOMING LIST)").font = white_font
        for c in range(1, 9): 
            ws.cell(row=current_row, column=c).fill = pax_fill
            ws.cell(row=current_row, column=c).alignment = center_al
        current_row += 1

        headers_px = ["Nombre Completo", "Documento", "Tipo Doc", "Nacionalidad", "Fecha Nac", "Género", "Cuidados", "Principal?"]
        for c_idx, h in enumerate(headers_px, 1):
            cell = ws.cell(row=current_row, column=c_idx, value=h)
            cell.fill = subheader_fill
            cell.font = bold_font
            cell.border = thin_border
        current_row += 1

        for p in pax:
            ws.cell(row=current_row, column=1, value=p.get('nombre_completo')).font = bold_font
            ws.cell(row=current_row, column=2, value=p.get('numero_documento'))
            ws.cell(row=current_row, column=3, value=p.get('tipo_documento'))
            ws.cell(row=current_row, column=4, value=p.get('nacionalidad'))
            ws.cell(row=current_row, column=5, value=p.get('fecha_nacimiento'))
            ws.cell(row=current_row, column=6, value=p.get('genero'))
            ws.cell(row=current_row, column=7, value=p.get('cuidados_especiales'))
            ws.cell(row=current_row, column=8, value="SÍ" if p.get('es_principal') else "NO")
            for c in range(1, 9): ws.cell(row=current_row, column=c).border = thin_border
            current_row += 1

        # Anchos de columna finales
        for col, w in zip(['A','B','C','D','E','F','G','H'], [10, 25, 12, 40, 30, 10, 15, 40]):
            ws.column_dimensions[col].width = w

        output = BytesIO()
        wb.save(output)
        output.seek(0)
        return output

    def generar_reporte_cuentas_cobrar_xlsx(self, df_cuentas: pd.DataFrame) -> BytesIO:
        """
        Genera un reporte Excel basado en la data de Cuentas por Cobrar B2B.
        """
        import openpyxl
        from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Cuentas_por_Cobrar_B2B"
        
        # --- Cabecera ---
        headers = list(df_cuentas.columns)
        for c_idx, h in enumerate(headers, 1):
            cell = ws.cell(row=1, column=c_idx, value=h)
            cell.fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid") # Azul oscuro
            cell.font = Font(color="FFFFFF", bold=True)
            cell.alignment = Alignment(horizontal='center')
        
        # --- Datos ---
        for r_idx, row in enumerate(df_cuentas.values, 2):
            for c_idx, value in enumerate(row, 1):
                ws.cell(row=r_idx, column=c_idx, value=value)
        
        # Ajustar anchos
        for column_cells in ws.columns:
            length = max(len(str(cell.value)) for cell in column_cells)
            ws.column_dimensions[column_cells[0].column_letter].width = length + 2

        output = BytesIO()
        wb.save(output)
        output.seek(0)
        return output
