import streamlit as st
import os
import subprocess
import json
from pathlib import Path
from datetime import datetime
from datos_tours import tours_db, paquetes_db

# --- FUNCIONES DE PERSISTENCIA ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PAQUETES_CUSTOM_FILE = os.path.join(BASE_DIR, 'paquetes_personalizados.json')

def guardar_itinerario_como_paquete(nombre, itinerario):
    data = {}
    if os.path.exists(PAQUETES_CUSTOM_FILE):
        with open(PAQUETES_CUSTOM_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    
    data[nombre] = itinerario
    with open(PAQUETES_CUSTOM_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def cargar_paquetes_custom():
    if os.path.exists(PAQUETES_CUSTOM_FILE):
        with open(PAQUETES_CUSTOM_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# --- CONFIGURACIÓN DE PÁGINA ---
# --- CONFIGURACIÓN DE PÁGINA (COMENTADO PARA INTEGRACIÓN) ---
# st.set_page_config(
#     page_title="Viajes Cusco Perú - Constructor de Itinerarios",
#     page_icon="🏔️",
#     layout="wide"
# )

# --- ESTILOS PERSONALIZADOS (TURQUESA & PREMIUM) ---
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton>button {
        background-color: #55b7b0;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 24px;
        font-weight: bold;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #449e98;
        border: none;
        color: white;
    }
    .package-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border-left: 5px solid #55b7b0;
        margin-bottom: 20px;
    }
    h1, h2, h3 {
        color: #2d3436;
    }
    /* Estilo SOLO para los botoncitos de control (cuando hay 3 columnas juntas) */
    div[data-testid="column"] > div > div > div[data-testid="stHorizontalBlock"]:has(div[data-testid="column"]:nth-child(3)) button {
        background-color: transparent !important;
        border: 1px solid #e0e0e0 !important;
        color: #55b7b0 !important;
        padding: 0px !important;
        height: 32px !important;
        width: 32px !important;
        font-size: 14px !important;
        min-height: unset !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    div[data-testid="column"] > div > div > div[data-testid="stHorizontalBlock"]:has(div[data-testid="column"]:nth-child(3)) button:hover {
        background-color: #f0f0f0 !important;
        border-color: #55b7b0 !important;
    }
    /* El botón de borrar (3ro de la fila) */
    div[data-testid="column"] > div > div > div[data-testid="stHorizontalBlock"] div[data-testid="column"]:nth-child(3) button {
        color: #ff7675 !important;
    }
    /* BOTONES GRANDES (Volver a la normalidad) */
    .stButton > button {
        width: 100% !important;
        height: auto !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- LÓGICA DE PDF (REUTILIZADA) ---
HTML_TEMPLATE_FILE = os.path.join(BASE_DIR, 'Estructura.html')
EDGE_PATH = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'

def generar_pdf_web(tours, pasajero, fechas, categoria, modo, vendedor, celular, cover_img, title_1, title_2, info_precios):
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    OUTPUT_HTML = os.path.join(BASE_DIR, f'temp_web_itinerario_{unique_id}.html')
    OUTPUT_PDF = os.path.join(BASE_DIR, f'Itinerario_{unique_id}.pdf')

    if not os.path.exists(HTML_TEMPLATE_FILE):
        raise FileNotFoundError(f"Plantilla no encontrada: {HTML_TEMPLATE_FILE}")

    with open(HTML_TEMPLATE_FILE, 'r', encoding='utf-8') as f:
        template = f.read()

    page_start = template.find('<div class="page-container">')
    page_end = template.rfind('</div>') + 6
    page_structure = template[page_start:page_end]
    html_head = template[:page_start]
    html_foot = template[page_end:]

    # Diccionario de Iconos Inteligentes
    icon_map = {
        'transporte': '<path d="M19 17h2c.6 0 1-.4 1-1v-3c0-.9-.7-1.7-1.5-1.9C18.7 10.6 16 10 16 10s-1.3-1.4-2.2-2.3c-.5-.4-1.1-.7-1.8-.7H5c-1.1 0-2 .9-2 2v7c0 1.1.9 2 2 2h2"></path><circle cx="7" cy="17" r="2"></circle><path d="M9 17h6"></path><circle cx="17" cy="17" r="2"></circle>',
        'traslado': '<path d="M19 17h2c.6 0 1-.4 1-1v-3c0-.9-.7-1.7-1.5-1.9C18.7 10.6 16 10 16 10s-1.3-1.4-2.2-2.3c-.5-.4-1.1-.7-1.8-.7H5c-1.1 0-2 .9-2 2v7c0 1.1.9 2 2 2h2"></path><circle cx="7" cy="17" r="2"></circle><path d="M9 17h6"></path><circle cx="17" cy="17" r="2"></circle>',
        'guía': '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M22 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path>',
        'asistencia': '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M22 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path>',
        'almuerzo': '<path d="M3 2v7c0 1.1.9 2 2 2h4V2"></path><path d="M7 2v20"></path><path d="M21 15V2v0a5 5 0 0 0-5 5v6c0 1.1.9 2 2 2h3Zm0 0v7"></path>',
        'alimentación': '<path d="M3 2v7c0 1.1.9 2 2 2h4V2"></path><path d="M7 2v20"></path><path d="M21 15V2v0a5 5 0 0 0-5 5v6c0 1.1.9 2 2 2h3Zm0 0v7"></path>',
        'ingreso': '<path d="M2 9a3 3 0 0 1 0 6v2a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-2a3 3 0 0 1 0-6V7a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2Z"></path><path d="M13 5v2"></path><path d="M13 17v2"></path><path d="M13 11v2"></path>',
        'boleto': '<path d="M2 9a3 3 0 0 1 0 6v2a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-2a3 3 0 0 1 0-6V7a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2Z"></path><path d="M13 5v2"></path><path d="M13 17v2"></path><path d="M13 11v2"></path>',
        'vuelo': '<path d="M17.8 19.2 16 11l3.5-3.5C21 6 21.5 4 21 3c-1-.5-3 0-4.5 1.5L13 8 4.8 6.2c-.5-.1-.9.1-1.1.5l-.3.5c-.2.5-.1 1 .3 1.3L9 12l-2 3H4l-1 1 3 2 2 3 1-1v-3l3-2 3.5 5.3c.3.4.8.5 1.3.3l.5-.2c.4-.3.6-.7.5-1.2z"></path>',
        'botiquín': '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M9 12h6"/><path d="M12 9v6"/>',
        'oxígeno': '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M9 12h6"/><path d="M12 9v6"/>',
        'propinas': '<line x1="12" y1="2" x2="12" y2="22"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>',
        'default_in': '<polyline points="20 6 9 17 4 12"></polyline>',
        'default_out': '<line x1="5" y1="12" x2="19" y2="12"></line>'
    }

    def get_svg(text, default_key):
        text_lower = text.lower()
        for key, svg in icon_map.items():
            if key in text_lower:
                return svg
        return icon_map[default_key]

    # Función auxiliar para obtener imágenes locales (OPTIMIZADO: Usamos File URIs para velocidad)
    def obtener_imagenes_tour(nombre_carpeta):
        
        # Construir ruta base
        base_path = Path(BASE_DIR) / 'assets' / 'img' / 'tours' / nombre_carpeta
        
        # Fallback a 'general' si no existe
        if not base_path.exists():
            base_path = Path(BASE_DIR) / 'assets' / 'img' / 'tours' / 'general'
        
        imagenes = []
        if base_path.exists():
            # Solo listamos los archivos, no los leemos ni codificamos (Mucho más rápido)
            for f in base_path.iterdir():
                if f.suffix.lower() in ['.png', '.jpg', '.jpeg', '.webp']:
                    imagenes.append(f.as_uri())
        
        # Rellenar si faltan imágenes (Usar placeholder local si es posible)
        while len(imagenes) < 5:
            imagenes.append("https://via.placeholder.com/400x300?text=Foto+Tour")
            
        return imagenes[:5]

    # --- LOGICA DE PORTADA ---
    try:
        with open('Portada.html', 'r', encoding='utf-8') as f:
            portada_template = f.read()
    except:
        portada_template = "<div>Error cargando Portada.html</div>"

    try:
        with open('Extras.html', 'r', encoding='utf-8') as f:
            extras_template = f.read()
    except:
        extras_template = ""
    
    # Logo (Usamos el que esté en la raíz según Estructura.html)
    path_logo = Path(os.getcwd()) / 'Captura de pantalla 2026-01-05 102612.png'
    uri_logo = path_logo.as_uri() if path_logo.exists() else ""

    # Imagen de la llama para la página de extras (usamos Fondo.png)
    path_llama = Path(os.getcwd()) / 'Fondo.png'
    uri_llama = path_llama.as_uri() if path_llama.exists() else ""
    
    # --- CONSTRUIR SECCIÓN DE PRECIOS DINÁMICA ---
    html_precios = ""
    n_nac, m_nac = info_precios.get('nac', (0, 0))
    n_ext, m_ext = info_precios.get('ext', (0, 0))
    n_can, m_can = info_precios.get('can', (0, 0))

    def gen_bloque_precio(titulo, monto, moneda):
        return f"""
        <div class="extra-title" style="margin-top: 10px;">PRECIO {titulo}</div>
        <div class="extra-subtitle">por persona</div>
        <div class="price-value">{moneda} {monto:,.2f}</div>
        <div class="price-detail">ADULTO<br>NO INCLUYE HOTEL</div>
        """

    # Si hay nacionales
    if n_nac > 0:
        html_precios += gen_bloque_precio("NACIONAL", m_nac, "S/")
    
    # Si hay extranjeros o CAN (ambos en USD)
    if n_ext > 0 or n_can > 0:
        # Si ambos existen y son diferentes, podríamos mostrar ambos, 
        # pero usualmente se prefiere uno solo si es informativo.
        # Por simplicidad, si hay extranjeros mostramos ese, si no, el CAN.
        m_usd = m_ext if n_ext > 0 else m_can
        tipo_usd = "EXTRANJERO" if n_ext > 0 else "CAN"
        if n_ext > 0 and n_can > 0: tipo_usd = "EXT / CAN"
        
        html_precios += gen_bloque_precio(tipo_usd, m_usd, "$")

    pag_extras = extras_template.replace('[[SECCION_PRECIOS]]', html_precios)
    pag_extras = pag_extras.replace('[[LOGO_URL]]', uri_logo)
    pag_extras = pag_extras.replace('url(\'https://images.unsplash.com/photo-1589923158776-cb4485d99fd6?auto=format&fit=crop&q=80&w=400\')', f"url('{uri_llama}')")

    # Calcular duración automática
    num_dias = len(tours)
    num_noches = max(0, num_dias - 1)
    duracion_str = f"{num_dias}D-{num_noches}N"
    
    # Imagen de portada (Dinámica)
    path_portada = Path(os.getcwd()) / cover_img
    uri_portada = path_portada.as_uri() if path_portada.exists() else ""

    pag_portada = portada_template.replace('[[IMAGEN_PORTADA]]', uri_portada)
    pag_portada = pag_portada.replace('[[TITLE_1]]', title_1.upper())
    pag_portada = pag_portada.replace('[[TITLE_2]]', title_2.upper())
    pag_portada = pag_portada.replace('[[DURACION]]', duracion_str)
    pag_portada = pag_portada.replace('[[LOGO_URL]]', uri_logo)
    pag_portada = pag_portada.replace('[[VENDEDOR]]', vendedor.upper())
    pag_portada = pag_portada.replace('[[CELULAR]]', celular)
    pag_portada = pag_portada.replace('class="cover-container"', 'class="cover-container" style="page-break-after: always;"')

    paginas_finales = pag_portada
    for i, tour in enumerate(tours):
        current_page = page_structure
        h_html = "".join([f'<li class="highlight-item">{h}</li>' for h in tour['highlights']])
        
        s_incluye_html = ""
        for s in tour['servicios']:
            svg_content = get_svg(s, 'default_in')
            s_incluye_html += f'<div class="service-item"><div class="service-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{svg_content}</svg></div><div class="service-text">{s}</div></div>'
            
        s_no_html = ""
        for s in tour['servicios_no_incluye']:
            svg_content = get_svg(s, 'default_out')
            s_no_html += f'<div class="service-item"><div class="service-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{svg_content}</svg></div><div class="service-text">{s}</div></div>'

        # OBTENER IMÁGENES DEL TOUR
        carpeta = tour.get('carpeta_img', 'general')
        imgs = obtener_imagenes_tour(carpeta)

        current_page = current_page.replace('[[PASAJERO]]', pasajero.upper())
        current_page = current_page.replace('[[VENDEDOR]]', vendedor.upper())
        current_page = current_page.replace('[[CELULAR]]', celular)
        current_page = current_page.replace('[[FECHAS]]', fechas.upper())
        current_page = current_page.replace('[[CATEGORIA_T]]', categoria.upper())
        current_page = current_page.replace('[[MODO_S]]', modo.upper())
        current_page = current_page.replace('[[DIA]]', f"DÍA {i+1}:")
        current_page = current_page.replace('[[TITULO]]', tour['titulo'])
        current_page = current_page.replace('[[DESCRIPCION]]', tour['descripcion'])
        current_page = current_page.replace('[[HIGHLIGHTS]]', h_html)
        current_page = current_page.replace('[[SERVICIOS]]', s_incluye_html)
        current_page = current_page.replace('[[SERVICIOS_NO]]', s_no_html)
        
        # INYECCIÓN DE IMÁGENES (Método Directo Hardcore)
        # Buscamos y reemplazamos los estilos uno por uno para asegurar que entren
        # Asumimos que el HTML tiene: class="circular-img img-1" style="..."
        
        # Limpiamos estilos previos si los hubiera (si el template tiene placeholders)
        # Como es reemplazo de texto, vamos a ser agresivos reemplazando todo el div
        
        # Patrón para encontrar el div y reemplazar su style
        # Pero como no tenemos regex fácil aquí, usaremos los identificadores únicos que ya tienen
        # El HTML tiene: class="circular-img img-1" style="background-image: url('...');"
        
        # Vamos a inyectar un nuevo style="background-image..." justo después de la clase
        current_page = current_page.replace('class="circular-img img-1"', f'class="circular-img img-1" style="background-image: url(\'{imgs[0]}\') !important;" data-replaced="true"')
        current_page = current_page.replace('class="circular-img img-2"', f'class="circular-img img-2" style="background-image: url(\'{imgs[1]}\') !important;" data-replaced="true"')
        current_page = current_page.replace('class="circular-img img-3"', f'class="circular-img img-3" style="background-image: url(\'{imgs[2]}\') !important;" data-replaced="true"')
        current_page = current_page.replace('class="circular-img img-4"', f'class="circular-img img-4" style="background-image: url(\'{imgs[3]}\') !important;" data-replaced="true"')
        current_page = current_page.replace('class="circular-img img-5"', f'class="circular-img img-5" style="background-image: url(\'{imgs[4]}\') !important;" data-replaced="true"')
        
        # Eliminar el style original que venía después para evitar conflictos (opcional, pero el !important arriba debería ganar)
        # Lo dejamos así por ahora confiando en la cascada y el atributo style directo

        if i < len(tours) - 1:
            current_page = current_page.replace('class="page-container"', 'class="page-container" style="page-break-after: always;"')
        paginas_finales += current_page

    # Agregar páginas extras al final
    if pag_extras:
        paginas_finales += pag_extras

    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html_head + paginas_finales + html_foot)

    subprocess.run([EDGE_PATH, '--headless', f'--print-to-pdf={os.path.abspath(OUTPUT_PDF)}', '--no-pdf-header-footer', f"file:///{os.path.abspath(OUTPUT_HTML)}"], check=True)
    if os.path.exists(OUTPUT_HTML): os.remove(OUTPUT_HTML)
    return os.path.abspath(OUTPUT_PDF)

def main():
    # --- ESTADO DE LA SESIÓN ---
    if 'itinerario' not in st.session_state:
        st.session_state.itinerario = []

    # --- INTERFAZ ---
    st.title("🛡️ Constructor de Itinerarios Premium")
    st.write("Interfaz exclusiva para el equipo de ventas de Viajes Cusco Perú.")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("👤 Datos del Pasajero")
        nombre = st.text_input("Nombre Completo del Cliente", placeholder="Ej: Juan Pérez")
        
        cv1, cv2 = st.columns(2)
        vendedor = cv1.text_input("Vendedor", placeholder="Nombre del Agente")
        celular = cv2.text_input("Celular del Cliente", placeholder="Ej: +51 9XX XXX XXX")
        
        t_col1, t_col2 = st.columns(2)
        # Guardar el origen anterior para detectar cambios
        if 'origen_previo' not in st.session_state:
            st.session_state.origen_previo = "Nacional/Chileno"

        tipo_t = t_col1.radio("Origen", ["Nacional/Chileno", "Extranjero"])
        modo_s = t_col2.radio("Servicio", ["Sistema Pool", "Servicio Privado"])

        # Lógica de actualización automática de precios al cambiar origen
        if tipo_t != st.session_state.origen_previo:
            for tour in st.session_state.itinerario:
                t_base = next((t for t in tours_db if t['titulo'] == tour['titulo']), None)
                if t_base:
                    tour['costo'] = t_base['costo_nacional'] if "Nacional" in tipo_t else t_base['costo_extranjero']
            st.session_state.origen_previo = tipo_t
            st.rerun()

        st.markdown("#### 👥 Cantidad de Pasajeros")
        p_col1, p_col2, p_col3 = st.columns(3)
        with p_col1:
            n_adultos_nac = st.number_input("Adultos Nacionales", min_value=0, value=1 if "Nacional" in tipo_t else 0, step=1)
            n_ninos_nac = st.number_input("Niños Nacionales", min_value=0, value=0, step=1)
        with p_col2:
            n_adultos_ext = st.number_input("Adultos Extranjeros", min_value=0, value=1 if "Extranjero" in tipo_t else 0, step=1)
            n_ninos_ext = st.number_input("Niños Extranjeros", min_value=0, value=0, step=1)
        with p_col3:
            n_adultos_can = st.number_input("Adultos CAN", min_value=0, value=0, step=1)
            n_ninos_can = st.number_input("Niños CAN", min_value=0, value=0, step=1)
        
        total_pasajeros = n_adultos_nac + n_ninos_nac + n_adultos_ext + n_ninos_ext + n_adultos_can + n_ninos_can
        st.info(f"Total personas: {total_pasajeros}")

        col_f1, col_f2 = st.columns(2)
        fecha_inicio = col_f1.date_input("Fecha Inicio", datetime.now())
        fecha_fin = col_f2.date_input("Fecha Fin", datetime.now())
        rango_fechas = f"Del {fecha_inicio.strftime('%d/%m')} al {fecha_fin.strftime('%d/%m, %Y')}"

        # --- ZONA DE GUARDADO (OTRO LUGAR - SIDEBAR) ---
        with st.sidebar:
            st.header("💾 Mis Paquetes Guardados")
            st.write("Aquí puedes guardar tus propios armados con tus precios.")
            
            # Guardar Paquete
            with st.expander("➕ Guardar Itinerario Actual", expanded=False):
                nombre_p = st.text_input("Nombre de tu paquete", placeholder="Ej: Machu Picchu VIP 3D")
                if st.button("💾 Confirmar Guardado"):
                    if nombre_p and st.session_state.itinerario:
                        guardar_itinerario_como_paquete(nombre_p, st.session_state.itinerario)
                        st.success(f"¡'{nombre_p}' guardado!")
                        st.rerun()
                    else:
                        st.warning("Ponle un nombre y agrega tours primero.")

            st.divider()
            
            # Cargar Paquete Custom
            paquetes_c = cargar_paquetes_custom()
            if paquetes_c:
                p_sel = st.selectbox("📂 Selecciona uno de tus paquetes", ["-- Seleccione --"] + list(paquetes_c.keys()))
                if p_sel != "-- Seleccione --":
                    if st.button("🚀 Cargar mi Paquete"):
                        st.session_state.itinerario = paquetes_c[p_sel]
                        st.success(f"Paquete '{p_sel}' cargado.")
                        st.rerun()
            else:
                st.caption("No tienes paquetes guardados aún.")

        st.divider()
        
        st.subheader("🎁 Cargar Paquete Sugerido")
        cat_sel = st.selectbox("Elija Línea de Producto", ["-- Seleccione --", "Cusco Tradicional", "Perú para el Mundo"])
        
        if cat_sel != "-- Seleccione --":
            pkgs_filtered = [p for p in paquetes_db if cat_sel.upper() in p['nombre'].upper()]
            dias_disponibles = [p['nombre'].split(" ")[-1] for p in pkgs_filtered]
            dia_sel = st.selectbox("Seleccione Duración", dias_disponibles)
            
            if st.button("🚀 Cargar Itinerario"):
                pkg_final = next(p for p in pkgs_filtered if dia_sel in p['nombre'])
                st.session_state.itinerario = []
                for t_n in pkg_final['tours']:
                    t_f = next((t for t in tours_db if t['titulo'] == t_n), None)
                    if t_f:
                        nuevo_t = t_f.copy()
                        nuevo_t['costo_nac'] = t_f.get('costo_nacional', 0)
                        nuevo_t['costo_ext'] = t_f.get('costo_extranjero', 0)
                        # Lógica CAN: -20 USD solo en Machupicchu
                        if "MACHU PICCHU" in t_f['titulo'].upper():
                            nuevo_t['costo_can'] = nuevo_t['costo_ext'] - 20
                        else:
                            nuevo_t['costo_can'] = nuevo_t['costo_ext']
                        st.session_state.itinerario.append(nuevo_t)
                st.success(f"Itinerario cargado.")
                st.rerun()

        st.subheader("📍 Agregar Tour Individual")
        tour_nombres = [t['titulo'] for t in tours_db]
        tour_sel = st.selectbox("Seleccione un tour", ["-- Seleccione --"] + tour_nombres)
        if st.button("Agregar Tour"):
            if tour_sel != "-- Seleccione --":
                t_data = next(t for t in tours_db if t['titulo'] == tour_sel)
                nuevo_t = t_data.copy()
                nuevo_t['costo_nac'] = t_data.get('costo_nacional', 0)
                nuevo_t['costo_ext'] = t_data.get('costo_extranjero', 0)
                # Lógica CAN: -20 USD solo en Machupicchu
                if "MACHU PICCHU" in t_data['titulo'].upper():
                    nuevo_t['costo_can'] = nuevo_t['costo_ext'] - 20
                else:
                    nuevo_t['costo_can'] = nuevo_t['costo_ext']
                st.session_state.itinerario.append(nuevo_t)
                st.rerun()

    with col2:
        st.subheader("📋 Plan de Viaje Actual")
        
        total_nac_pp = 0
        total_ext_pp = 0
        total_can_pp = 0
        
        # Bloqueo por tipo de servicio
        es_pool = (modo_s == "Sistema Pool")
        
        if not st.session_state.itinerario:
            st.info("El itinerario está vacío. Comienza cargando un paquete o un tour individual.")
        else:
            for i, tour in enumerate(st.session_state.itinerario):
                # Sumar costos unitarios
                total_nac_pp += tour.get('costo_nac', 0)
                total_ext_pp += tour.get('costo_ext', 0)
                total_can_pp += tour.get('costo_can', 0)
                
                # --- FILA DE DÍA PREMIUM ---
                c_content, c_btns = st.columns([0.88, 0.12])
                
                with c_content:
                    # Detectar si es MP para mostrar o no el cuadro CAN
                    es_mp = "MACHU PICCHU" in tour['titulo'].upper()
                    
                    header_text = f"DÍA {i+1}: {tour['titulo']} - (S/ {tour.get('costo_nac', 0)} | $ {tour.get('costo_ext', 0)})"
                    if es_mp:
                        header_text = f"DÍA {i+1}: {tour['titulo']} - (S/ {tour.get('costo_nac', 0)} | $ {tour.get('costo_ext', 0)} | CAN $ {tour.get('costo_can', 0)})"
                    
                    with st.expander(header_text, expanded=False):
                        if es_mp:
                            # Para MP mostramos las 3 columnas
                            col_t1, col_n, col_e, col_c = st.columns([1.5, 0.8, 0.8, 0.8])
                            tour['titulo'] = col_t1.text_input(f"Título día {i+1}", tour['titulo'], key=f"title_{i}", disabled=es_pool)
                            tour['costo_nac'] = col_n.number_input(f"Nac (S/)", value=float(tour.get('costo_nac', 0)), key=f"cn_{i}", disabled=es_pool)
                            tour['costo_ext'] = col_e.number_input(f"Ext ($)", value=float(tour.get('costo_ext', 0)), key=f"ce_{i}", disabled=es_pool)
                            tour['costo_can'] = col_c.number_input(f"CAN ($)", value=float(tour.get('costo_can', 0)), key=f"cc_{i}", disabled=es_pool)
                        else:
                            # Para el resto, solo Nac y Ext (CAN se iguala a Ext)
                            col_t1, col_n, col_e = st.columns([2, 1, 1])
                            tour['titulo'] = col_t1.text_input(f"Título día {i+1}", tour['titulo'], key=f"title_{i}", disabled=es_pool)
                            tour['costo_nac'] = col_n.number_input(f"Nac (S/)", value=float(tour.get('costo_nac', 0)), key=f"cn_{i}", disabled=es_pool)
                            tour['costo_ext'] = col_e.number_input(f"Ext ($)", value=float(tour.get('costo_ext', 0)), key=f"ce_{i}", disabled=es_pool)
                            tour['costo_can'] = tour['costo_ext'] # Sincronización automática
                        
                        st.divider()
                        tour['description'] = st.text_area(f"Descripción día {i+1}", tour.get('descripcion', ""), key=f"desc_{i}", height=100, disabled=es_pool)
                        
                        # Edición de Listas (Sincronizada)
                        col_ex1, col_ex2 = st.columns(2)
                        h_text = col_ex1.text_area(f"📍 Atractivos", "\\n".join(tour['highlights']), key=f"h_{i}", height=120, disabled=es_pool)
                        tour['highlights'] = [line.strip() for line in h_text.split("\\n") if line.strip()]
                        
                        s_text = col_ex2.text_area(f"✅ Incluye", "\\n".join(tour['servicios']), key=f"s_{i}", height=120, disabled=es_pool)
                        tour['servicios'] = [line.strip() for line in s_text.split("\\n") if line.strip()]

                        if es_pool:
                            st.caption("⚠️ Los detalles del servicio Pool no se pueden modificar.")

                with c_btns:
                    # Controles minimalistas
                    st.write('<div style="margin-top: 4px;">', unsafe_allow_html=True)
                    b1, b2, b3 = st.columns(3)
                    if b1.button("🔼", key=f"up_{i}"):
                        if i > 0:
                            st.session_state.itinerario.insert(i-1, st.session_state.itinerario.pop(i))
                            st.rerun()
                    if b2.button("🔽", key=f"down_{i}"):
                        if i < len(st.session_state.itinerario)-1:
                            st.session_state.itinerario.insert(i+1, st.session_state.itinerario.pop(i))
                            st.rerun()
                    if b3.button("🗑️", key=f"del_{i}"):
                        st.session_state.itinerario.pop(i)
                        st.rerun()
                    st.write('</div>', unsafe_allow_html=True)
                
                st.markdown('<div style="margin-top: -15px;"></div>', unsafe_allow_html=True)

            st.divider()
            
            # --- CÁLCULO DE TOTALES SEPARADOS ---
            pasajeros_nac = n_adultos_nac + n_ninos_nac
            pasajeros_ext = n_adultos_ext + n_ninos_ext
            pasajeros_can = n_adultos_can + n_ninos_can
            
            real_nac = total_nac_pp * pasajeros_nac
            real_ext = total_ext_pp * pasajeros_ext
            real_can = total_can_pp * pasajeros_can
            
            col_res1, col_res2, col_res3 = st.columns(3)
            with col_res1:
                st.markdown(f"### 🇵🇪 Nacionales")
                st.markdown(f"**S/ {real_nac:,.2f}**")
                st.caption(f"({pasajeros_nac} pas x S/ {total_nac_pp:,.2f} p/p)")
            
            with col_res2:
                st.markdown(f"### 🌎 Extranjeros")
                st.markdown(f"**$ {real_ext:,.2f}**")
                st.caption(f"({pasajeros_ext} pas x $ {total_ext_pp:,.2f} p/p)")

            with col_res3:
                st.markdown(f"### 🤝 CAN")
                st.markdown(f"**$ {real_can:,.2f}**")
                st.caption(f"({pasajeros_can} pas x $ {total_can_pp:,.2f} p/p)")

            st.divider()
            
            c_btn1, c_btn2 = st.columns(2)
            if c_btn2.button("🧹 Limpiar Todo"):
                st.session_state.itinerario = []
                st.rerun()

            if c_btn1.button("🔥 GENERAR ITINERARIO PDF"):
                if nombre and st.session_state.itinerario:
                    # Determinar portada y títulos
                    if cat_sel == "Perú para el Mundo":
                        cover_img = "Captura de pantalla 2026-01-13 094212.png"
                        t1, t2 = "PERÚ", "PARA EL MUNDO"
                    else: # Cusco Tradicional o por defecto
                        cover_img = "Captura de pantalla 2026-01-13 094056.png"
                        t1, t2 = "CUSCO", "TRADICIONAL"

                    # Estructura de precios para el PDF
                    info_p = {
                        'nac': (pasajeros_nac, total_nac_pp),
                        'ext': (pasajeros_ext, total_ext_pp),
                        'can': (pasajeros_can, total_can_pp)
                    }

                    # Para el PDF usamos la categoría dominante o una genérica
                    cat_final = f"{pasajeros_nac} Nac + {pasajeros_ext} Ext + {pasajeros_can} CAN"
                    pdf_path = generar_pdf_web(st.session_state.itinerario, nombre, rango_fechas, cat_final, modo_s, vendedor, celular, cover_img, t1, t2, info_p)
                    with open(pdf_path, "rb") as file:
                        st.download_button(
                            label="📥 Descargar PDF Final",
                            data=file,
                            file_name=f"Itinerario_{nombre.replace(' ', '_')}.pdf",
                            mime="application/pdf"
                        )
                    st.success(f"¡Itinerario listo para {nombre}!")
                else:
                    st.warning("Asegúrate de poner el nombre del cliente y tener al menos un día en el plan.")

    # Pie de página
    st.markdown("---")
    st.caption("v1.1 - Sistema de Gestión de Itinerarios con Costos | Viajes Cusco Perú")

if __name__ == "__main__":
    main()
