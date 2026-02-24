# controllers/excel_controller.py
import pandas as pd
from io import BytesIO
import datetime
from openpyxl.styles import Alignment, Font, PatternFill

class ExcelController:
    """Controlador para la generación de documentos Excel a partir de datos del itinerario."""

    def generar_resumen_itinerario_xlsx(self, datos_render: dict) -> BytesIO:
        """Genera un archivo XLSX resumido para operaciones basado estrictamente en el itinerario."""
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
            
            # Precio (Priorizar costo según origen del JSON)
            origen = str(datos_render.get('origen', '')).upper()
            p_val = "---"
            
            if "NAC" in origen or "PERU" in origen:
                p_val = d.get('costo_nac')
            elif "EXT" in origen or "EXTRANJERO" in origen:
                p_val = d.get('costo_ext')
            elif "CAN" in origen:
                p_val = d.get('costo_can')
            
            # Si p_val sigue siendo None o no se encontró por origen, buscar cualquier costo
            if p_val is None or p_val == "---":
                p_val = (d.get('precio') or d.get('costo') or 
                         d.get('costo_nac') or d.get('costo_ext') or d.get('costo_can') or
                         d.get('valor') or d.get('monto') or 
                         d.get('price') or "---")
            
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
        Genera un Excel Maestro para Operaciones sin diseño visual complejo.
        data_hoja debe contener: 'venta', 'itinerario', 'pasajeros'
        """
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment
        
        wb = openpyxl.Workbook()
        
        # --- HOJA 1: RESUMEN DE VENTA ---
        ws1 = wb.active
        ws1.title = "RESUMEN_VENTA"
        v = data_hoja.get('venta', {})
        
        datos_v = [
            ["CAMPO", "VALOR"],
            ["ID Venta", v.get('id_venta')],
            ["Cliente", v.get('nombre_cliente')],
            ["Celular", v.get('telefono')],
            ["Tour/Paquete", v.get('tour_nombre')],
            ["Fecha Inicio", v.get('fecha_inicio')],
            ["Fecha Fin", v.get('fecha_fin')],
            ["Pax Totales", v.get('num_pasajeros')],
            ["Vendedor", v.get('vendedor')],
            ["", ""],
            ["FINANCIERO", ""],
            ["Moneda", v.get('moneda')],
            ["Monto Total", v.get('monto_total')],
            ["Monto Pagado", v.get('monto_pagado')],
            ["Saldo Pendiente", float(v.get('monto_total') or 0) - float(v.get('monto_pagado') or 0)]
        ]
        
        for r_idx, row in enumerate(datos_v, 1):
            for c_idx, val in enumerate(row, 1):
                cell = ws1.cell(row=r_idx, column=c_idx, value=val)
                if r_idx == 1 or "FINANCIERO" in str(val):
                    cell.font = Font(bold=True)
                    cell.fill = PatternFill(start_color="DDDDDD", end_color="DDDDDD", fill_type="solid")

        ws1.column_dimensions['A'].width = 25
        ws1.column_dimensions['B'].width = 50

        # --- HOJA 2: ITINERARIO LOGÍSTICO ---
        ws2 = wb.create_sheet("LOGISTICA_DIARIA")
        it = data_hoja.get('itinerario', [])
        
        headers_it = ["Día", "Fecha", "Hora", "Servicio", "Proveedor/Asignado", "Pax", "Tipo", "Observaciones"]
        for c_idx, h in enumerate(headers_it, 1):
            cell = ws2.cell(row=1, column=c_idx, value=h)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="CCE5FF", end_color="CCE5FF", fill_type="solid")
            cell.alignment = Alignment(horizontal='center')

        for r_idx, s in enumerate(it, 2):
            ws2.cell(row=r_idx, column=1, value=s.get('Día Itin.'))
            ws2.cell(row=r_idx, column=2, value=s.get('Fecha'))
            ws2.cell(row=r_idx, column=3, value=s.get('Hora'))
            ws2.cell(row=r_idx, column=4, value=s.get('Servicio'))
            ws2.cell(row=r_idx, column=5, value=s.get('Proveedor'))
            ws2.cell(row=r_idx, column=6, value=s.get('Pax'))
            ws2.cell(row=r_idx, column=7, value=s.get('Tipo'))
            ws2.cell(row=r_idx, column=8, value=s.get('observacion') or "")

        for col in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:
            ws2.column_dimensions[col].width = 15 if col != 'D' and col != 'H' else 40

        # --- HOJA 3: PASAJEROS (ROOMING) ---
        ws3 = wb.create_sheet("PASAJEROS_ROOMING")
        pax = data_hoja.get('pasajeros', [])
        
        headers_px = ["Nombre Completo", "Documento", "Tipo Doc", "Nacionalidad", "Fecha Nac", "Género", "Cuidados", "Principal?"]
        for c_idx, h in enumerate(headers_px, 1):
            cell = ws3.cell(row=1, column=c_idx, value=h)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="D1E7DD", end_color="D1E7DD", fill_type="solid")

        for r_idx, p in enumerate(pax, 2):
            ws3.cell(row=r_idx, column=1, value=p.get('nombre_completo'))
            ws3.cell(row=r_idx, column=2, value=p.get('numero_documento'))
            ws3.cell(row=r_idx, column=3, value=p.get('tipo_documento'))
            ws3.cell(row=r_idx, column=4, value=p.get('nacionalidad'))
            ws3.cell(row=r_idx, column=5, value=p.get('fecha_nacimiento'))
            ws3.cell(row=r_idx, column=6, value=p.get('genero'))
            ws3.cell(row=r_idx, column=7, value=p.get('cuidados_especiales'))
            ws3.cell(row=r_idx, column=8, value="SÍ" if p.get('es_principal') else "NO")

        ws3.column_dimensions['A'].width = 40
        for col in ['B', 'C', 'D', 'E', 'F', 'G', 'H']:
            ws3.column_dimensions[col].width = 15

        output = BytesIO()
        wb.save(output)
        output.seek(0)
        return output
