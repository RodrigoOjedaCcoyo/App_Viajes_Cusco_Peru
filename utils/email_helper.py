# utils/email_helper.py
import smtplib
import threading
import streamlit as st
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime

def _bloque_html_drive(carpeta_link, drive_links=None):
    """Genera el bloque HTML con el link a la carpeta de Drive (y a cada archivo si se conocen)."""
    if not carpeta_link:
        return ""

    lista_archivos_html = ""
    if drive_links:
        items = "".join(
            f'<li><a href="{d["link"]}" target="_blank">{d["nombre"]}</a></li>'
            for d in drive_links if d.get("link")
        )
        if items:
            lista_archivos_html = f'<ul style="margin:8px 0 0 0;">{items}</ul>'

    return f"""
    <div style="margin-top: 15px; padding: 15px; background-color: #e3f2fd; border-radius: 5px;">
        <p style="margin: 0;"><strong>📁 Comprobantes / Adjuntos:</strong>
            <a href="{carpeta_link}" target="_blank">Ver carpeta en Google Drive</a>
        </p>
        {lista_archivos_html}
    </div>
    """

def enviar_notificacion_venta_async(venta_data, adjuntos=None, drive_links=None, carpeta_link=None):
    """
    Inicia un hilo para enviar el correo en segundo plano sin bloquear la UI.
    Si se pasa `carpeta_link` (los archivos ya se subieron a Drive), el correo
    manda el link en vez de adjuntar los archivos. `adjuntos` solo se usa como
    respaldo cuando la subida a Drive falló.
    """
    thread = threading.Thread(
        target=_enviar_correo_worker,
        args=(venta_data, adjuntos, drive_links, carpeta_link)
    )
    thread.start()

def _enviar_correo_worker(venta_data, adjuntos=None, drive_links=None, carpeta_link=None):
    """
    Lógica interna de envío de correo (corre en segundo plano).
    """
    try:
        # 1. Cargar configuración de secretos
        if "smtp" not in st.secrets:
            print("Error: No se encontró la configuración [smtp] en st.secrets")
            return

        smtp_conf = st.secrets["smtp"]
        server_host = smtp_conf["server"]
        port = int(smtp_conf["port"])
        user = smtp_conf["user"]
        password = smtp_conf["password"]
        destinatarios = [d.strip() for d in smtp_conf["destination"].split(",")]

        # 2. Crear el mensaje
        msg = MIMEMultipart()
        msg['From'] = user
        msg['To'] = ", ".join(destinatarios)
        
        # Asegurar moneda para evitar errores de formato
        if not venta_data.get('moneda'):
            venta_data['moneda'] = 'PEN'

        # Limpiar nombre del vendedor si es un correo
        vendedor_nombre = venta_data.get('vendedor', 'Desconocido')
        if "@" in vendedor_nombre:
            vendedor_nombre = vendedor_nombre.split("@")[0].capitalize()

        msg['Subject'] = f"Venta: {venta_data.get('nombre_cliente')} - {vendedor_nombre}"

        # 3. Construir Cuerpo HTML (Diseño Profesional)
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: auto; border: 1px solid #ddd; padding: 20px; border-radius: 10px;">
                <h2 style="color: #2e7d32; text-align: center;">💰 Registro de Venta Confirmada</h2>
                <hr>
                <p>Se ha registrado una nueva venta en el sistema con los siguientes detalles:</p>
                
                <table style="width: 100%; border-collapse: collapse;">
                    <tr style="background-color: #f9f9f9;">
                        <td style="padding: 8px; font-weight: bold;">Cliente:</td>
                        <td style="padding: 8px;">{venta_data.get('nombre_cliente')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; font-weight: bold;">Servicio:</td>
                        <td style="padding: 8px;">{venta_data.get('tour')}</td>
                    </tr>
                    <tr style="background-color: #f9f9f9;">
                        <td style="padding: 8px; font-weight: bold;">Pax:</td>
                        <td style="padding: 8px;">{venta_data.get('cantidad')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; font-weight: bold;">Fechas:</td>
                        <td style="padding: 8px;">Del {venta_data.get('fecha_inicio')} al {venta_data.get('fecha_fin')}</td>
                    </tr>
                    <tr style="background-color: #f9f9f9;">
                        <td style="padding: 8px; font-weight: bold;">Total:</td>
                        <td style="padding: 8px;">{venta_data.get('moneda')} {venta_data.get('monto_total'):,.2f}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; font-weight: bold;">Pagado:</td>
                        <td style="padding: 8px;">{venta_data.get('moneda')} {venta_data.get('monto_depositado'):,.2f}</td>
                    </tr>
                    <tr style="background-color: #f9f9f9; color: #d32f2f;">
                        <td style="padding: 8px; font-weight: bold;">Saldo Pendiente:</td>
                        <td style="padding: 8px; font-weight: bold;">{venta_data.get('moneda')} {venta_data.get('saldo', 0):,.2f}</td>
                    </tr>
                </table>
                
                <div style="margin-top: 20px; padding: 15px; background-color: #e8f5e9; border-radius: 5px;">
                    <p style="margin: 0;"><strong>Vendedor:</strong> {venta_data.get('vendedor')}</p>
                    <p style="margin: 0;"><strong>Método Pago:</strong> {venta_data.get('metodo_pago')}</p>
                    <p style="margin: 0;"><strong>Comentarios:</strong> {venta_data.get('comentarios') or 'Sin comentarios'}</p>
                </div>
                {_bloque_html_drive(carpeta_link, drive_links)}
                <p style="font-size: 12px; color: #777; text-align: center; margin-top: 20px;">
                    Este es un mensaje automático generado por el Sistema Viajes Cusco.
                </p>
            </div>
        </body>
        </html>
        """
        msg.attach(MIMEText(html, 'html'))

        # 4. Adjuntos: si ya se subieron a Drive, NO se adjuntan los archivos al correo
        # (evita correos pesados que llegan incompletos). Solo se adjunta como respaldo
        # si la subida a Drive falló (carpeta_link es None) y sí llegaron bytes.
        if not carpeta_link and adjuntos:
            for nombre_archivo, contenido in adjuntos.items():
                part = MIMEApplication(contenido, Name=nombre_archivo)
                part['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
                msg.attach(part)

        # 5. Envío vía SMTP
        if port == 465:
            # SSL directo (típico de Hostinger)
            with smtplib.SMTP_SSL(server_host, port) as server:
                server.login(user, password)
                server.sendmail(user, destinatarios, msg.as_string())
        else:
            # TLS
            with smtplib.SMTP(server_host, port) as server:
                server.starttls()
                server.login(user, password)
                server.sendmail(user, destinatarios, msg.as_string())
        
        print(f"✅ Correo de notificación enviado con éxito a {destinatarios}")

    except Exception as e:
        print(f"❌ Error al enviar correo de notificación: {str(e)}")


def enviar_adjuntos_adicionales(asunto: str, nota: str, adjuntos: dict = None, drive_links=None, carpeta_link=None):
    """
    Envía un correo con asunto y nota personalizados. Si se pasa `carpeta_link`
    (los archivos ya se subieron a Drive), el correo manda el link en vez de
    adjuntar los archivos. `adjuntos` solo se usa como respaldo si la subida a
    Drive falló. adjuntos: dict {nombre_archivo: bytes}
    """
    import threading
    thread = threading.Thread(
        target=_worker_adjuntos_adicionales,
        args=(asunto, nota, adjuntos, drive_links, carpeta_link),
        daemon=True
    )
    thread.start()


def _worker_adjuntos_adicionales(asunto: str, nota: str, adjuntos: dict = None, drive_links=None, carpeta_link=None):
    try:
        if "smtp" not in st.secrets:
            print("Error: No se encontró la configuración [smtp] en st.secrets")
            return

        smtp_conf     = st.secrets["smtp"]
        server_host   = smtp_conf["server"]
        port          = int(smtp_conf["port"])
        user          = smtp_conf["user"]
        password      = smtp_conf["password"]
        destinatarios = [d.strip() for d in smtp_conf["destination"].split(",")]

        msg = MIMEMultipart()
        msg['From']    = user
        msg['To']      = ", ".join(destinatarios)
        msg['Subject'] = asunto

        # Cuerpo HTML simple con la nota
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: auto; border: 1px solid #ddd;
                        padding: 20px; border-radius: 10px;">
                <h2 style="color: #1565c0; text-align: center;">
                    📎 Documentos Adicionales
                </h2>
                <hr>
                <p style="font-size: 15px; white-space: pre-line;">{nota}</p>
                {_bloque_html_drive(carpeta_link, drive_links)}
                <p style="font-size: 12px; color: #777; text-align: center; margin-top: 20px;">
                    Este mensaje fue enviado desde el Sistema Viajes Cusco Perú.
                </p>
            </div>
        </body>
        </html>
        """
        msg.attach(MIMEText(html, 'html'))

        # Adjuntar archivos solo como respaldo (si no se pudo subir a Drive)
        if not carpeta_link and adjuntos:
            for nombre_archivo, contenido in adjuntos.items():
                part = MIMEApplication(contenido, Name=nombre_archivo)
                part['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
                msg.attach(part)

        # Envío
        if port == 465:
            with smtplib.SMTP_SSL(server_host, port) as server:
                server.login(user, password)
                server.sendmail(user, destinatarios, msg.as_string())
        else:
            with smtplib.SMTP(server_host, port) as server:
                server.starttls()
                server.login(user, password)
                server.sendmail(user, destinatarios, msg.as_string())

        n_archivos = len(adjuntos) if adjuntos else len(drive_links or [])
        print(f"✅ Adjuntos adicionales enviados a {destinatarios} ({n_archivos} archivos, drive={'si' if carpeta_link else 'no'})")

    except Exception as e:
        print(f"❌ Error enviando adjuntos adicionales: {str(e)}")
