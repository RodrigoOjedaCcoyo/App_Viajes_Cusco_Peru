# controllers/excel_controller.py
import pandas as pd
from io import BytesIO
import datetime
from openpyxl.styles import Alignment, Font, PatternFill

class ExcelController:
    """Controlador para la generación de documentos Excel a partir de datos del itinerario."""

    def generar_resumen_itinerario_xlsx(self, datos_render: dict) -> BytesIO:
        """Genera un archivo XLSX con el resumen del itinerario."""
        # Extraer información básica
        cliente = datos_render.get("nombre_pasajero") or "Pasajero"
        titulo_viaje = datos_render.get("titulo") or f"{datos_render.get('title_1', '')} {datos_render.get('title_2', '')}".strip() or "General"
        
        # Extraer items del itinerario
        items = (datos_render.get("itinerario_detalles") or 
                 datos_render.get("itinerario_detales") or 
                 datos_render.get("days") or 
                 datos_render.get("servicios") or 
                 datos_render.get("itinerario") or [])
        
        rows = []
        for i, t in enumerate(items):
            dia_label = f"DÍA {i+1}"
            if t.get('fecha'): dia_label = f"DÍA: {t['fecha']}"
            elif t.get('numero'): dia_label = f"DÍA {t['numero']}"
            
            servicio = (t.get('nombre') or t.get('titulo') or "Servicio").upper()
            hora = t.get('hora', '')
            
            # Recopilar Inclusiones
            inc_list = t.get('incluye') or t.get('inclusiones', []) or t.get('servicios', [])
            inclusiones_text = ""
            for item in inc_list:
                txt = item.get('texto') if isinstance(item, dict) else item
                if txt:
                    inclusiones_text += f"• {str(txt).upper()}\n"
            
            rows.append({
                "DÍA / FECHA": dia_label,
                "HORA": hora,
                "SERVICIO": servicio,
                "INCLUSIONES DETALLADAS": inclusiones_text.strip()
            })
            
        df = pd.DataFrame(rows)
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name="Resumen Itinerario", startrow=4)
            
            workbook = writer.book
            worksheet = writer.sheets["Resumen Itinerario"]
            
            # --- ESTILIZACIÓN --
            # Cabecera personalizada
            worksheet.merge_cells('A1:D1')
            worksheet['A1'] = f"RESUMEN DE ITINERARIO: {titulo_viaje.upper()}"
            worksheet['A1'].font = Font(size=14, bold=True, color="000000")
            worksheet['A1'].alignment = Alignment(horizontal='center')
            
            worksheet.merge_cells('A2:D2')
            worksheet['A2'] = f"CLIENTE: {cliente.upper()}"
            worksheet['A2'].font = Font(size=12, bold=True)
            
            worksheet.merge_cells('A3:D3')
            worksheet['A3'] = f"Fecha de reporte: {datetime.date.today().strftime('%d/%m/%Y')}"
            
            # Formato de la tabla
            header_fill = PatternFill(start_color="D9EAD3", end_color="D9EAD3", fill_type="solid")
            for cell in worksheet[5]: # La fila 5 es la cabecera del DataFrame (startrow=4 es 0-indexed para pandas, pero 1-indexed para excel es fila 5)
                cell.fill = header_fill
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal='center')

            # Ajustar anchos y alineación
            worksheet.column_dimensions['A'].width = 15
            worksheet.column_dimensions['B'].width = 12
            worksheet.column_dimensions['C'].width = 40
            worksheet.column_dimensions['D'].width = 70
            
            for row in worksheet.iter_rows(min_row=6):
                for cell in row:
                    cell.alignment = Alignment(wrapText=True, vertical='top')

        output.seek(0)
        return output
