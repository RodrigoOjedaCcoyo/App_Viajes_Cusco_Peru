# controllers/excel_controller.py
import pandas as pd
from io import BytesIO
import datetime
from openpyxl.styles import Alignment, Font, PatternFill

class ExcelController:
    """Controlador para la generación de documentos Excel a partir de datos del itinerario."""

    def generar_resumen_itinerario_xlsx(self, datos_render: dict) -> BytesIO:
        """Genera un archivo XLSX con el resumen del itinerario imitando el formato del usuario."""
        import openpyxl
        from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "RESUMEN"
        
        # --- DATOS GENERALES ---
        cliente = (datos_render.get("nombre_pasajero") or "Pasajero").upper()
        pax_count = int(datos_render.get("num_adultos", 1)) + int(datos_render.get("num_ninos", 0))
        dni = datos_render.get("dni", "---")
        
        # Precios (Simulado si no existe o extraído de precios)
        precios_d = datos_render.get("precios", {})
        moneda = "S/" if "PEN" in str(precios_d).upper() else "$"
        p_unit = precios_d.get("extranjero", 0) or precios_d.get("adulto", 0) or 0
        p_total = p_unit * pax_count
        pago = datos_render.get("monto_pagado", p_total) # Si no hay, asumimos pagado total
        pendiente = p_total - pago
        
        # --- HEADER (Filas 1-15 aprox) ---
        ws.merge_cells('D2:G2')
        ws['D2'] = "RESUMEN"
        ws['D2'].font = Font(bold=True, size=12)
        ws['D2'].alignment = Alignment(horizontal='center')
        
        ws['C4'] = "DIAS:"
        ws['D4'] = len(datos_render.get("days", [])) or len(datos_render.get("itinerario_detalles", [])) or 1
        ws['D4'].font = Font(bold=True)
        
        ws['A7'] = "GRUPO : X"
        ws['B7'] = pax_count
        ws['B7'].font = Font(bold=True)
        ws['C7'] = cliente
        ws['C8'] = f"DNI:{dni}"
        
        # Financiero
        ws['A11'] = f"PRECIO POR PERSONA: ADULTO {moneda} {p_unit}"
        ws['A11'].font = Font(bold=True)
        ws['A12'] = f"PRECIO TOTAL {pax_count:02d} PERSONAS: {moneda} {p_total}"
        ws['A12'].font = Font(bold=True)
        
        ws['A14'] = f"PAGÓ 100%: {moneda} {pago}" # Asumimos 100% o lo que haya
        ws['A14'].font = Font(bold=True)
        ws['A15'] = "PENDIENTE:"
        ws.merge_cells('C15:I15')
        ws['C15'].border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'), outline=True)
        ws['C15'] = f"{moneda} {pendiente}" if pendiente > 0 else ""
        
        # --- ITINERARIO (A partir de fila 18) ---
        current_row = 18
        
        items = (datos_render.get("itinerario_detalles") or 
                 datos_render.get("itinerario_detales") or 
                 datos_render.get("days") or 
                 datos_render.get("servicios") or 
                 datos_render.get("itinerario") or [])

        for i, t in enumerate(items):
            # Fila de Día
            ws.cell(row=current_row, column=1, value=i+1).font = Font(bold=True)
            fecha_txt = t.get('fecha') or f"DÍA {i+1}"
            ws.cell(row=current_row, column=2, value=f"DIA: {fecha_txt}").font = Font(bold=True)
            current_row += 2 # Espacio según imagen
            
            # Fila de Servicio
            ws.cell(row=current_row, column=2, value=1)
            ws.cell(row=current_row, column=3, value=t.get('hora', '---'))
            ws.cell(row=current_row, column=4, value=(t.get('nombre') or t.get('titulo') or "SERVICIO").upper()).font = Font(bold=True)
            current_row += 1
            
            # Inclusiones
            inc_list = t.get('incluye') or t.get('inclusiones', []) or t.get('servicios', [])
            for inc in inc_list:
                txt = inc.get('texto') if isinstance(inc, dict) else inc
                if txt:
                    ws.cell(row=current_row, column=2, value=1)
                    ws.cell(row=current_row, column=4, value=f"INCLUYE {str(txt).upper()}")
                    current_row += 1
            
            # Exclusiones
            exc_list = t.get('no_incluye') or t.get('exclusiones', []) or t.get('servicios_no', [])
            if exc_list:
                current_row += 1
                ws.cell(row=current_row, column=4, value="NO INCLUYE:").font = Font(bold=True, color="2E7D32")
                current_row += 1
                for exc in exc_list:
                    txt = exc.get('texto') if isinstance(exc, dict) else exc
                    if txt:
                        ws.cell(row=current_row, column=3, value=0)
                        ws.cell(row=current_row, column=4, value=str(txt).upper()).font = Font(color="2E7D32")
                        current_row += 1
            
            current_row += 2 # Salto entre días
            
        # Ajustes finales de ancho
        ws.column_dimensions['A'].width = 5
        ws.column_dimensions['B'].width = 12
        ws.column_dimensions['C'].width = 15
        ws.column_dimensions['D'].width = 60
        
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
