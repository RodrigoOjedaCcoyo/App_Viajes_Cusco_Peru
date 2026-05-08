# controllers/pdf_controller.py
import os
import base64
from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa
from io import BytesIO
import datetime

class PDFController:
    """Controlador para la generación de documentos PDF a partir de plantillas HTML."""
    
    def __init__(self):
        # Localización de las plantillas
        self.template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
        self.env = Environment(loader=FileSystemLoader(self.template_dir))
        # Ruta del logo (en la raíz del proyecto)
        self.logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logo_background.png')

    def _get_logo_base64(self) -> str:
        """Lee el logo y lo convierte a base64 para incrustar en el PDF."""
        try:
            with open(self.logo_path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except Exception as e:
            print(f"No se pudo cargar el logo: {e}")
            return ""

    def _render_pdf(self, template_name: str, context: dict) -> BytesIO:
        """Helper centralizado para renderizar HTML y convertir a PDF."""
        try:
            template = self.env.get_template(template_name)
            html_content = template.render(context)
            
            pdf_output = BytesIO()
            pisa_status = pisa.CreatePDF(html_content, dest=pdf_output)
            
            if pisa_status.err:
                print(f"Error en xhtml2pdf ({template_name}): {pisa_status.err}")
                return None
            
            pdf_output.seek(0)
            return pdf_output
        except Exception as e:
            print(f"Error renderizando PDF {template_name}: {e}")
            return None

    def _extraer_fecha_viaje_robusta(self, datos_render: dict) -> str:
        f_inicio = datos_render.get('fecha_viaje') or datos_render.get('fecha_inicio') or datos_render.get('fechaViaje') or datos_render.get('fecha')
        ci = datos_render.get('control_interno', {})
        if not f_inicio and ci:
            f_inicio = ci.get('fecha_inicio') or ci.get('fecha_llegada') or ci.get('fecha_viaje')
        if not f_inicio:
            dias_itin = datos_render.get('itinerario') or datos_render.get('days') or datos_render.get('itinerario_detalles')
            if dias_itin and isinstance(dias_itin, list) and len(dias_itin) > 0 and isinstance(dias_itin[0], dict):
                f_inicio = dias_itin[0].get('fecha')
        return str(f_inicio).strip() if f_inicio else ""

    def generar_itinerario_pdf(self, datos_render: dict) -> BytesIO:
        """Genera un PDF de itinerario PREMIUM."""
        fecha_robusta = self._extraer_fecha_viaje_robusta(datos_render)
        precios = datos_render.get("precios", {})
        total_val = precios.get("extranjero", 0)
        moneda_val = precios.get("moneda_extranjero", "USD")
        
        context = {
            "cliente_nombre": datos_render.get("nombre_pasajero") or "Pasajero",
            "cliente_telefono": datos_render.get("cliente_telefono") or datos_render.get("telefono") or "",
            "fecha_viaje": fecha_robusta,
            "num_adultos": datos_render.get("num_adultos", 1),
            "num_ninos": datos_render.get("num_ninos", 0),
            "itinerario": (datos_render.get("itinerario_detalles") or 
                           datos_render.get("itinerario_detales") or 
                           datos_render.get("days") or 
                           datos_render.get("servicios") or 
                           datos_render.get("itinerario") or []),
            "total": total_val,
            "moneda_total": moneda_val
        }
        return self._render_pdf('itinerario_template.html', context)

    def generar_itinerario_simple_pdf(self, datos_render: dict) -> BytesIO:
        """Genera un PDF de itinerario SIMPLE (Ink Saver)."""
        fecha_robusta = self._extraer_fecha_viaje_robusta(datos_render)
        precios = datos_render.get("precios", {})
        total_val = precios.get("extranjero", 0)
        moneda_val = precios.get("moneda_extranjero", "USD")

        # --- Extracción de PAX Robusta ---
        num_adultos = datos_render.get("num_adultos") or datos_render.get("num_pasajeros") or datos_render.get("pax") or datos_render.get("total_pax") or 1
        num_ninos = datos_render.get("num_ninos") or 0
        ci = datos_render.get('control_interno', {})
        if ci and not datos_render.get("num_adultos"):
            num_adultos = ci.get('total_pasajeros') or ci.get('total_pax') or num_adultos

        itinerario_raw = (datos_render.get("itinerario_detalles") or 
                          datos_render.get("itinerario_detales") or 
                          datos_render.get("days") or 
                          datos_render.get("servicios") or 
                          datos_render.get("itinerario") or [])
        
        # Procesar datos (Negritas y Listas de Inclusiones)
        itinerario_procesado = []
        for item in itinerario_raw:
            if not isinstance(item, dict):
                continue
            it_copy = item.copy()
            
            # 1. Procesar negritas (*** -> <b>)
            desc = it_copy.get('descripcion', '')
            if desc:
                parts = desc.split('***')
                new_desc = ""
                for i, part in enumerate(parts):
                    if i % 2 == 0: new_desc += part
                    else: new_desc += f"<b>{part}</b>"
                it_copy['descripcion'] = new_desc
            
            # 2. Consolidar INCLUSIONES
            it_copy['incluye_final'] = (item.get('incluye') or item.get('inclusiones') or item.get('servicios') or [])
            it_copy['no_incluye_final'] = (item.get('no_incluye') or item.get('exclusiones') or item.get('servicios_no') or [])
            
            # 3. Extraer HORA Robusta
            it_copy['hora'] = item.get('hora') or item.get('time') or item.get('hora_inicio') or ""
            
            itinerario_procesado.append(it_copy)

        context = {
            "cliente_nombre": datos_render.get("nombre_pasajero") or "Pasajero",
            "cliente_telefono": datos_render.get("cliente_telefono") or datos_render.get("telefono") or "",
            "fecha_viaje": fecha_robusta if fecha_robusta else "Pendiente",
            "num_adultos": int(num_adultos),
            "num_ninos": int(num_ninos),
            "itinerario": itinerario_procesado,
            "comentarios_generales": datos_render.get("comentarios_generales", ""),
            "total": total_val,
            "moneda_total": moneda_val,
            "hoy": datetime.date.today().strftime("%d/%m/%Y")
        }
        return self._render_pdf('itinerario_simple_template.html', context)

    def generar_voucher_endose_pdf(self, data: dict) -> BytesIO:
        """Genera un Vale de Endose para un proveedor específico."""
        data['hoy'] = datetime.date.today().strftime("%d/%m/%Y")
        return self._render_pdf('voucher_endose_template.html', data)

    def generar_voucher_reserva_pdf(self, data: dict) -> BytesIO:
        """
        Genera un Voucher de Reserva profesional para el cliente.
        'data' contiene campos de la venta + campos temporales (pasaporte, hotel, etc.)
        que NO se guardan en la base de datos.
        """
        # Procesar itinerario desde datos_render del itinerario digital
        datos_render = data.get('datos_render', {})
        itinerario_raw = (
            datos_render.get("itinerario_detalles") or
            datos_render.get("itinerario_detales") or
            datos_render.get("days") or
            datos_render.get("servicios") or
            datos_render.get("itinerario") or []
        )

        itinerario_procesado = []
        for item in itinerario_raw:
            if not isinstance(item, dict):
                continue
            it_copy = item.copy()

            # Título del día
            it_copy['titulo'] = (
                item.get('titulo') or item.get('title') or
                item.get('day_title') or item.get('nombre') or
                item.get('dia') or ""
            )

            # Procesar negritas *** -> <b>
            desc = it_copy.get('descripcion', '')
            if desc:
                parts = desc.split('***')
                new_desc = ""
                for i, part in enumerate(parts):
                    if i % 2 == 0:
                        new_desc += part
                    else:
                        new_desc += f"<b>{part}</b>"
                it_copy['descripcion'] = new_desc

            # Consolidar inclusiones y extraer SOLO el texto (los items pueden ser dicts)
            raw_incluye = (
                item.get('incluye') or item.get('inclusiones') or
                item.get('servicios') or []
            )
            incluye_limpio = []
            for inc in raw_incluye:
                if isinstance(inc, dict):
                    texto = (inc.get('texto') or inc.get('text') or
                             inc.get('nombre') or inc.get('title') or "")
                    if texto:
                        incluye_limpio.append(str(texto).strip())
                elif isinstance(inc, str) and inc.strip():
                    incluye_limpio.append(inc.strip())
            it_copy['incluye_final'] = incluye_limpio
            itinerario_procesado.append(it_copy)

        # Número de voucher: 000YY-MM-IDDDD
        # Ejemplo: 00026-05-00013 → año 2026, mes mayo, ID venta 13
        id_venta = data.get('id_venta') or 1
        anio_2d = datetime.date.today().year % 100      # últimos 2 dígitos del año (ej: 26)
        mes_actual = datetime.date.today().month         # número de mes (ej: 5)
        try:
            id_num = int(id_venta)
        except Exception:
            id_num = 1

        parte_anio = f"{anio_2d:05d}"      # 00026
        parte_mes  = f"{mes_actual:02d}"   # 05
        parte_id   = f"{id_num:05d}"       # 00013
        numero_voucher = f"{parte_anio}-{parte_mes}-{parte_id}"

        # Montos
        monto_total = float(data.get('monto_total') or 0)
        monto_pagado = float(data.get('monto_depositado') or data.get('monto_pagado') or 0)
        saldo = monto_total - monto_pagado

        context = {
            # Empresa
            "empresa_nombre": "LATITUD VIAJES CUSCO PERU SAC",
            "empresa_telefono": "942128412 / 970909088",
            "empresa_direccion": "Av. Mariscal José Luis de Obregoso BI-B",
            "empresa_email": "viajescuscoperu@gmail.com",
            "empresa_web": "www.viajescuscoperu.com",
            # Voucher
            "numero_voucher": numero_voucher,
            "fecha_emision": datetime.date.today().strftime("%d/%m/%Y"),
            # Logo en base64
            "logo_base64": self._get_logo_base64(),
            "nombre_cliente": data.get('nombre_cliente', ''),
            "telefono_cliente": data.get('telefono', data.get('telefono_cliente', '')),
            "correo_cliente": data.get('correo_cliente', ''),
            # Datos temporales para el voucher (no guardados en DB)
            "pasaporte": data.get('pasaporte', '---'),
            "hotel": data.get('hotel', '---'),
            "nacionalidad": data.get('nacionalidad', '---'),
            "edad": data.get('edad', '---'),
            "num_adultos": data.get('num_adultos_voucher', data.get('cantidad', 1)),
            "num_estudiantes": data.get('num_estudiantes_voucher', 0),
            # Fechas y PAX
            "fecha_inicio": data.get('fecha_inicio', ''),
            "fecha_fin": data.get('fecha_fin', ''),
            "num_pax": data.get('cantidad', 1),
            # Itinerario
            "itinerario": itinerario_procesado,
            # Montos
            "moneda": data.get('moneda', 'USD'),
            "monto_total": monto_total,
            "monto_pagado": monto_pagado,
            "saldo": saldo,
        }
        pdf_bytes = self._render_pdf('voucher_reserva_template.html', context)
        return pdf_bytes
