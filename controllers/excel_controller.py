# controllers/excel_controller.py
import pandas as pd
from io import BytesIO
import datetime
from openpyxl.styles import Alignment, Font, PatternFill

class ExcelController:
    """Controlador para la generación de documentos Excel a partir de datos del itinerario."""

    def generar_resumen_itinerario_xlsx(self, datos_render: dict) -> BytesIO:
        """Genera un archivo XLSX detallado (Ink Saver) con el contenido real del itinerario."""
        import openpyxl
        from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "ITINERARIO_RESUMEN"
        
        # --- ESTILOS ---
        bold_font = Font(bold=True)
        header_font = Font(bold=True, size=14)
        border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
        
        # --- HEADER GENERAL ---
        ws.merge_cells('A1:E1')
        ws['A1'] = (datos_render.get('titulo') or "RESUMEN DE ITINERARIO").upper()
        ws['A1'].font = header_font
        ws['A1'].alignment = Alignment(horizontal='center')
        
        ws['A3'] = "PASAJERO:"
        ws['B3'] = (datos_render.get("nombre_pasajero") or "---").upper()
        ws['A4'] = "GRUPO:"
        pax_count = int(datos_render.get("num_adultos", 1)) + int(datos_render.get("num_ninos", 0))
        ws['B4'] = f"{pax_count} Persona(s)"
        
        ws['D3'] = "FECHA INICIO:"
        ws['E3'] = datos_render.get("fecha_inicio", "---")
        ws['D4'] = "DÍAS TOTALES:"
        ws['E4'] = len(datos_render.get("days", [])) or 1

        # --- CUERPO DEL ITINERARIO ---
        current_row = 6
        
        items = (datos_render.get("days") or 
                 datos_render.get("itinerario_detalles") or 
                 datos_render.get("servicios") or [])

        for i, d in enumerate(items):
            # Barra de Día
            ws.merge_cells(f'A{current_row}:E{current_row}')
            cell_dia = ws[f'A{current_row}']
            fecha_val = d.get('fecha') or f"DÍA {i+1}"
            titulo_val = (d.get('title') or d.get('nombre') or d.get('titulo') or "Servicio").upper()
            cell_dia.value = f" {fecha_val} - {titulo_val} "
            cell_dia.font = bold_font
            cell_dia.fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
            current_row += 1
            
            # Descripción (si existe)
            desc = d.get('description') or d.get('descripcion') or ""
            if desc:
                ws.merge_cells(f'B{current_row}:E{current_row+1}')
                cell_desc = ws[f'B{current_row}']
                cell_desc.value = desc
                cell_desc.alignment = Alignment(wrap_text=True, vertical='top')
                current_row += 2
            
            # Comidas y Hotel
            comidas = []
            if d.get('breakfast') or d.get('desayuno'): comidas.append("Desayuno")
            if d.get('lunch') or d.get('almuerzo'): comidas.append("Almuerzo")
            if d.get('dinner') or d.get('cena'): comidas.append("Cena")
            
            txt_extra = ""
            if comidas: txt_extra += f"🍴 Alimentos: {', '.join(comidas)} | "
            hotel = d.get('hotel') or d.get('accommodation') or ""
            if hotel: txt_extra += f"🏨 Hotel: {hotel}"
            
            if txt_extra:
                ws.merge_cells(f'B{current_row}:E{current_row}')
                ws[f'B{current_row}'] = txt_extra
                ws[f'B{current_row}'].font = Font(italic=True, size=9)
                current_row += 1
                
            current_row += 1 # Espacio entre días

        # --- RESUMEN FINAL DE INCLUSIONES ---
        current_row += 1
        ws.merge_cells(f'A{current_row}:E{current_row}')
        ws[f'A{current_row}'] = "RESUMEN DE SERVICIOS INCLUIDOS"
        ws[f'A{current_row}'].font = bold_font
        ws[f'A{current_row}'].fill = PatternFill(start_color="D9EAD3", end_color="D9EAD3", fill_type="solid")
        current_row += 1
        
        inclusiones = datos_render.get("incluye_resumen") or []
        for inc in inclusiones:
            ws.cell(row=current_row, column=1, value="•")
            ws.merge_cells(f'B{current_row}:E{current_row}')
            ws.cell(row=current_row, column=2, value=str(inc))
            current_row += 1

        # --- AJUSTES DE COLUMNAS ---
        ws.column_dimensions['A'].width = 15
        ws.column_dimensions['B'].width = 20
        ws.column_dimensions['C'].width = 20
        ws.column_dimensions['D'].width = 20
        ws.column_dimensions['E'].width = 30

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
