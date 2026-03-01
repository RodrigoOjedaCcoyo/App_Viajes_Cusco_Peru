# controllers/excel_controller.py
import pandas as pd
from io import BytesIO
import datetime
from openpyxl.styles import Alignment, Font, PatternFill

class ExcelController:
    """Controlador para la generación de documentos Excel a partir de datos del itinerario."""

    def generar_resumen_itinerario_xlsx(self, datos_render: dict, precios_reales: dict = None) -> BytesIO:
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
        ws.merge_cells('A1:F1')
        titulo_itin = (datos_render.get('titulo') or datos_render.get('paquete_nombre') or 'ITINERARIO').upper()
        ws['A1'] = f"RESUMEN OPERATIVO: {titulo_itin}"
        ws['A1'].font = Font(bold=True, size=14)
        ws['A1'].alignment = center_al
        
        ws['A3'] = "FECHA INICIO:"
        ws['B3'] = datos_render.get("fecha_inicio") or datos_render.get("fecha_viaje") or "---"
        ws['D3'] = "FECHA FINAL:"
        ws['E3'] = datos_render.get("fecha_fin") or "---"
        
        ws['A4'] = "PASAJERO:"
        ws['B4'] = (datos_render.get("nombre_pasajero") or datos_render.get("cliente_nombre") or "---").upper()
        ws['D4'] = "TOTAL PAX:"
        pax_count = int(datos_render.get("num_adultos", 1)) + int(datos_render.get("num_ninos", 0))
        ws['E4'] = f"{pax_count} Personas"
        ws['E4'].font = bold_f

        # --- TABLA DE DÍAS ---
        current_row = 6
        headers = ["DÍA", "FECHA", "SERVICIO / TOUR", "PAX", "PRECIO", "INCLUYE / NO INCLUYE"]
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
            
            # Precio (Prioridad Máxima: Precios Reales desde base de datos)
            nl = i + 1
            if precios_reales and nl in precios_reales:
                p_val = precios_reales[nl]
            else:
                # Fallback: Priorizar precio negociado sobre el costo base de la plantilla
                p_val = (d.get('precio') or d.get('monto') or 
                         d.get('precio_venta') or d.get('valor') or 
                         d.get('price') or "---")
                
                # Si no hay precio negociado, usar el costo por origen (Base)
                if p_val == "---":
                    origen = str(datos_render.get('origen', '')).upper()
                    if "NAC" in origen or "PERU" in origen:
                        p_val = d.get('costo_nac')
                    elif "EXT" in origen or "EXTRANJERO" in origen:
                        p_val = d.get('costo_ext')
                    elif "CAN" in origen:
                        p_val = d.get('costo_can')
                
                # Último intento si sigue siendo None o "---"
                if p_val is None or p_val == "---":
                    p_val = (d.get('costo_nac') or d.get('costo_ext') or d.get('costo_can') or
                             d.get('costo') or "---")
            
            ws.cell(row=current_row, column=5, value=p_val).alignment = center_al
            
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
            
            detail_cell = ws.cell(row=current_row, column=6, value="\n".join(details_txt))
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
        ws.column_dimensions['E'].width = 15
        ws.column_dimensions['F'].width = 70

        output = BytesIO()
        wb.save(output)
        output.seek(0)
        return output

        output = BytesIO()
        wb.save(output)
        output.seek(0)
        return output

        output = BytesIO()
        wb.save(output)
        output.seek(0)
        return output

    def generar_hoja_servicio_maestra_xlsx(self, data_hoja: dict) -> BytesIO:
        """
        Genera un Excel Maestro Premium para Operaciones y Contabilidad.
        """
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        
        wb = openpyxl.Workbook()
        
        # --- ESTILOS PREMIUM ---
        header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid") # Azul Profundo
        subheader_fill = PatternFill(start_color="DBEAFE", end_color="DBEAFE", fill_type="solid") # Azul Claro
        accent_fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid") # Gris suave
        
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
        liq = data_hoja.get('liquidaciones', []) # Nueva data

        # Calcular Costo Total Liquidado
        costo_total_liq = sum(float(l.get('costo_unitario') or 0) for l in liq)
        utilidad = float(v.get('monto_total') or 0) - costo_total_liq

        # --- HOJA 1: PANEL DE CONTROL FINANCIERO ---
        ws1 = wb.active
        ws1.title = "1_RESUMEN_FINANCIERO"
        
        # Título
        ws1.merge_cells('A1:C1')
        ws1['A1'] = "REPORTE MAESTRO DE OPERACIONES Y CIERRE"
        ws1['A1'].font = Font(bold=True, size=16, color="1E3A8A")
        ws1['A1'].alignment = center_al

        datos_v = [
            ["INFORMACIÓN GENERAL", "", ""],
            ["ID Venta", v.get('id_venta'), ""],
            ["Cliente Principal", v.get('nombre_cliente'), ""],
            ["Teléfono Contacto", v.get('telefono'), ""],
            ["Servicio Contratado", v.get('tour_nombre'), ""],
            ["Periodo de Viaje", f"{v.get('fecha_inicio')} al {v.get('fecha_fin')}", ""],
            ["Total Pasajeros", f"{v.get('num_pasajeros')} PAX", ""],
            ["Vendedor Responsable", v.get('vendedor'), ""],
            ["", "", ""],
            ["ESTADO FINANCIERO (RESUMEN)", "", ""],
            ["Moneda de Operación", v.get('moneda'), ""],
            ["Monto Total Venta (Cierre)", v.get('monto_total'), "INGRESO"],
            ["Total Cobrado / Pagado", v.get('monto_pagado'), "RECAUDO"],
            ["Saldo por Cobrar", float(v.get('monto_total') or 0) - float(v.get('monto_pagado') or 0), "PENDIENTE"],
            ["", "", ""],
            ["LIQUIDACIÓN DE COSTOS (OPERACIONES)", "", ""],
            ["Costo Total de Proveedores", costo_total_liq, "COSTO NETO"],
            ["UTILIDAD BRUTA ESTIMADA", utilidad, "MARGEN"],
            ["Rentabilidad (%)", (utilidad / float(v.get('monto_total') or 1)) * 100 if float(v.get('monto_total') or 0) > 0 else 0, "%"]
        ]
        
        row_start = 3
        for r_idx, row in enumerate(datos_v, row_start):
            # Detectar si es una cabecera de sección
            tipo_seccion = row[0] in ["INFORMACIÓN GENERAL", "ESTADO FINANCIERO (RESUMEN)", "LIQUIDACIÓN DE COSTOS (OPERACIONES)"]
            
            if tipo_seccion:
                # Caso especial: Cabecera fusionada
                ws1.merge_cells(start_row=r_idx, start_column=1, end_row=r_idx, end_column=3)
                cell_main = ws1.cell(row=r_idx, column=1, value=row[0])
                
                # Estilos para todo el bloque fusionado
                for c_idx in range(1, 4):
                    c_node = ws1.cell(row=r_idx, column=c_idx)
                    c_node.border = thin_border
                    c_node.fill = header_fill
                    c_node.font = white_font
                    c_node.alignment = center_al
                continue # Saltar al siguiente registro
            
            # Caso Normal: Celdas individuales
            for c_idx, val in enumerate(row, 1):
                # No intentar escribir a la columna 1 si está vacía en este bloque (ya procesada)
                cell = ws1.cell(row=r_idx, column=c_idx, value=val)
                cell.border = thin_border
                
                # Formato Etiquetas (Col 1)
                if c_idx == 1 and val != "":
                    cell.fill = subheader_fill
                    cell.font = bold_font
                
                # Formato Números (Col 2)
                elif c_idx == 2 and isinstance(val, (int, float)):
                    cell.number_format = '#,##0.00'
                
                # Formato utilidades especiales (Verde suave)
                if val == "UTILIDAD BRUTA ESTIMADA":
                    cell.fill = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid")

        ws1.column_dimensions['A'].width = 30
        ws1.column_dimensions['B'].width = 35
        ws1.column_dimensions['C'].width = 15

        # --- HOJA 2: LOGÍSTICA DIARIA ---
        ws2 = wb.create_sheet("2_LOGISTICA_PASAJERO")
        headers_it = ["Día", "Fecha", "Hora", "Servicio / Tour", "Proveedor Sugerido", "Pax", "Tipo", "Observaciones"]
        for c_idx, h in enumerate(headers_it, 1):
            cell = ws2.cell(row=1, column=c_idx, value=h)
            cell.fill = header_fill
            cell.font = white_font
            cell.alignment = center_al

        for r_idx, s in enumerate(it, 2):
            ws2.cell(row=r_idx, column=1, value=s.get('Día Itin.'))
            ws2.cell(row=r_idx, column=2, value=s.get('Fecha'))
            ws2.cell(row=r_idx, column=3, value=s.get('Hora'))
            ws2.cell(row=r_idx, column=4, value=s.get('Servicio')).font = bold_font
            ws2.cell(row=r_idx, column=5, value=s.get('Proveedor'))
            ws2.cell(row=r_idx, column=6, value=s.get('Pax'))
            ws2.cell(row=r_idx, column=7, value=s.get('Tipo'))
            ws2.cell(row=r_idx, column=8, value=s.get('observacion') or "")
            for c in range(1, 9): ws2.cell(row=r_idx, column=c).border = thin_border

        for col, w in zip(['A','B','C','D','E','F','G','H'], [8, 12, 10, 40, 30, 8, 15, 40]):
            ws2.column_dimensions[col].width = w

        # --- HOJA 3: DETALLE DE PAGOS (LIQUIDACIÓN) ---
        ws3 = wb.create_sheet("3_LIQUIDACION_DETALLADA")
        headers_l = ["Día", "Proveedor Real", "Tipo Servicio", "Moneda", "Costo Unitario", "Pax", "Total Línea"]
        for c_idx, h in enumerate(headers_l, 1):
            cell = ws3.cell(row=1, column=c_idx, value=h)
            cell.fill = PatternFill(start_color="334155", end_color="334155", fill_type="solid") # Slate
            cell.font = white_font
            cell.alignment = center_al

        for r_idx, l in enumerate(liq, 2):
            ws3.cell(row=r_idx, column=1, value=l.get('n_linea'))
            prov_name = l.get('proveedor', {}).get('nombre_comercial', '---') if isinstance(l.get('proveedor'), dict) else '---'
            ws3.cell(row=r_idx, column=2, value=prov_name).font = bold_font
            ws3.cell(row=r_idx, column=3, value=l.get('tipo_servicio'))
            ws3.cell(row=r_idx, column=4, value=l.get('moneda'))
            
            c_unit = float(l.get('costo_unitario') or 0)
            pax_count = int(l.get('cantidad_pax') or v.get('num_pasajeros', 1))
            ws3.cell(row=r_idx, column=5, value=c_unit).number_format = '#,##0.00'
            ws3.cell(row=r_idx, column=6, value=pax_count)
            ws3.cell(row=r_idx, column=7, value=c_unit * pax_count).number_format = '#,##0.00'
            
            for c in range(1, 8): ws3.cell(row=r_idx, column=c).border = thin_border

        ws3.column_dimensions['B'].width = 35
        ws3.column_dimensions['D'].width = 10
        ws3.column_dimensions['E'].width = 15

        # --- HOJA 4: ROOMING LIST OFICIAL ---
        ws4 = wb.create_sheet("4_ROOMING_LIST")
        headers_px = ["Nombre Completo", "Documento", "Tipo Doc", "Nacionalidad", "Fecha Nac", "Género", "Cuidados", "Principal?"]
        for c_idx, h in enumerate(headers_px, 1):
            cell = ws4.cell(row=1, column=c_idx, value=h)
            cell.fill = PatternFill(start_color="059669", end_color="059669", fill_type="solid") # Esmeralda
            cell.font = white_font

        for r_idx, p in enumerate(pax, 2):
            ws4.cell(row=r_idx, column=1, value=p.get('nombre_completo')).font = bold_font
            ws4.cell(row=r_idx, column=2, value=p.get('numero_documento'))
            ws4.cell(row=r_idx, column=3, value=p.get('tipo_documento'))
            ws4.cell(row=r_idx, column=4, value=p.get('nacionalidad'))
            ws4.cell(row=r_idx, column=5, value=p.get('fecha_nacimiento'))
            ws4.cell(row=r_idx, column=6, value=p.get('genero'))
            ws4.cell(row=r_idx, column=7, value=p.get('cuidados_especiales'))
            ws4.cell(row=r_idx, column=8, value="SÍ" if p.get('es_principal') else "NO")
            for c in range(1, 9): ws4.cell(row=r_idx, column=c).border = thin_border

        ws4.column_dimensions['A'].width = 40
        for col in ['B','C','D','E','F','G','H']: ws4.column_dimensions[col].width = 15

        output = BytesIO()
        wb.save(output)
        output.seek(0)
        return output
