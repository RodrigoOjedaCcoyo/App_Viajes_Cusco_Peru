# utils/drive_helper.py
import io
import mimetypes
from datetime import date, datetime

import streamlit as st
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

SCOPES = ['https://www.googleapis.com/auth/drive']

MESES_NOMBRE = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
}
MESES_ABREV = {
    1: "ENE", 2: "FEB", 3: "MAR", 4: "ABR",
    5: "MAY", 6: "JUN", 7: "JUL", 8: "AGO",
    9: "SEP", 10: "OCT", 11: "NOV", 12: "DIC",
}


def _get_drive_service():
    """
    Autentica como el usuario real (viajescuscoperu@gmail.com) usando el refresh token
    guardado en st.secrets['google_drive'], para que los archivos cuenten contra su
    propio espacio de Drive (las cuentas de servicio no tienen cupo propio).
    """
    conf = st.secrets["google_drive"]
    credentials = Credentials(
        token=None,
        refresh_token=conf["refresh_token"],
        client_id=conf["client_id"],
        client_secret=conf["client_secret"],
        token_uri=conf["token_uri"],
        scopes=SCOPES,
    )
    return build('drive', 'v3', credentials=credentials, cache_discovery=False)


def _escapar_nombre(nombre: str) -> str:
    return nombre.replace("'", "\\'")


def _buscar_o_crear_carpeta(service, nombre: str, id_padre: str) -> str:
    """Busca una carpeta por nombre exacto dentro de id_padre; si no existe, la crea."""
    query = (
        f"name = '{_escapar_nombre(nombre)}' and '{id_padre}' in parents "
        "and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    )
    res = service.files().list(q=query, fields="files(id, name)", pageSize=1).execute()
    encontradas = res.get('files', [])
    if encontradas:
        return encontradas[0]['id']

    metadata = {
        'name': nombre,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [id_padre],
    }
    nueva = service.files().create(body=metadata, fields='id').execute()
    return nueva['id']


def _parsear_fecha(fecha_viaje) -> date:
    if isinstance(fecha_viaje, datetime):
        return fecha_viaje.date()
    if isinstance(fecha_viaje, date):
        return fecha_viaje
    return date.fromisoformat(str(fecha_viaje)[:10])


def subir_comprobantes_venta(fecha_viaje, nombre_cliente: str, num_pasajeros: int, archivos: dict):
    """
    Sube los archivos (dict {nombre_archivo: bytes}) a Drive, dentro de:
    CLIENTES / {Año} / {Mes} / {Día MES_ABREV - NOMBRE_CLIENTE [X{n}]}
    usando la FECHA DE VIAJE para ubicar/crear cada carpeta (crea las que falten,
    reutiliza las que ya existan).

    Devuelve (lista_links_archivos, link_carpeta_cliente).
    Si algo falla (credenciales, permisos, sin conexión, etc.) devuelve (None, None)
    para que quien llama pueda hacer un fallback (ej. adjuntar por correo como antes).
    """
    if not archivos:
        return [], None

    try:
        service = _get_drive_service()
        folder_id_clientes = st.secrets["google_drive"]["folder_id_clientes"]

        fecha = _parsear_fecha(fecha_viaje)

        id_carpeta_anio = _buscar_o_crear_carpeta(service, str(fecha.year), folder_id_clientes)

        nombre_mes = f"{fecha.month:02d} {MESES_NOMBRE[fecha.month]}"
        id_carpeta_mes = _buscar_o_crear_carpeta(service, nombre_mes, id_carpeta_anio)

        nombre_cliente_fmt = str(nombre_cliente or "SIN NOMBRE").strip().upper()
        if num_pasajeros and int(num_pasajeros) > 1:
            nombre_cliente_fmt = f"{nombre_cliente_fmt} X{int(num_pasajeros)}"
        nombre_carpeta_cliente = f"{fecha.day:02d} {MESES_ABREV[fecha.month]} - {nombre_cliente_fmt}"
        id_carpeta_cliente = _buscar_o_crear_carpeta(service, nombre_carpeta_cliente, id_carpeta_mes)

        links = []
        for nombre_archivo, contenido in archivos.items():
            mimetype = mimetypes.guess_type(nombre_archivo)[0] or 'application/octet-stream'
            media = MediaIoBaseUpload(io.BytesIO(contenido), mimetype=mimetype, resumable=False)
            metadata = {'name': nombre_archivo, 'parents': [id_carpeta_cliente]}
            archivo_subido = service.files().create(
                body=metadata, media_body=media, fields='id, webViewLink'
            ).execute()
            links.append({'nombre': nombre_archivo, 'link': archivo_subido.get('webViewLink')})

        link_carpeta = f"https://drive.google.com/drive/folders/{id_carpeta_cliente}"
        return links, link_carpeta

    except Exception as e:
        print(f"❌ Error subiendo comprobantes a Google Drive: {e}")
        return None, None
