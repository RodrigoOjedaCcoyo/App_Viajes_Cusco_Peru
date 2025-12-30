# main.py 
import streamlit as st
import sys
import os
import importlib
from supabase import create_client, Client

# --- 1. Configuración de Roles y Rutas ---
ROLES = ["VENTAS", "OPERACIONES", "CONTABLE", "GERENCIA"]
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 1. Aseguramos que Python encuentre las carpetas, dándole la MÁXIMA PRIORIDAD
if BASE_DIR not in sys.path:
       sys.path.append(BASE_DIR)

# 2. Insertamos la ruta en la posición 0 (el primer lugar donde buscar)
sys.path.insert(0, BASE_DIR)

# Mapeo de roles a las funcionalidades (Correcto)
MODULOS_VISIBLES = {
    "VENTAS": [
        ("Registro de Leads", "page_ventas"),
        ("Seguimiento de Leads", "page_ventas"),
        ("Registro de Ventas", "page_ventas")
    ],
    "OPERACIONES": [
        ("Dashboard Operaciones", "page_operaciones")
    ],
    "CONTABLE": [
        ("Reporte de Montos", "page_contabilidad"),
        ("Auditoría de Pagos", "page_contabilidad")
    ],
    "GERENCIA": [
        ("Dashboard Ejecutivo", "page_gerencia"),
        ("Auditoría Completa", "page_gerencia")
    ]
}

# -- 2. Inicializacion de Supabase (CLAVE por RLS)
try:
    SUPABASE_URL = st.secrets["supabase"]["URL"]
    SUPABASE_ANON_KEY = st.secrets["supabase"]["ANON_KEY"]
except KeyError:
    st.error("Error: Las credenciales de Supabase no estan configurado en st.secrets.")
    st.stop()

@st.cache_resource
def init_supabase_client() -> Client:
    """Inicializa y cachea el cliente se Supabase."""
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

supabase: Client = init_supabase_client()

# --- 3. Logica de Autenticación y Estado ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'user_role' not in st.session_state:
    st.session_state['user_role'] = None
if 'user_email' not in st.session_state:
    st.session_state['user_email'] = None

# Modificacion añadimiento de los roles
@st.cache_data
def fetch_app_role(user_uuid):
    """
    Busca el UUID del usuario en las tablas de mapeo para determinar el rol de la aplicación.
    """
    if supabase.table('vendedor_mapeo').select('id_vendedor_int').eq('id_supabase_uuid', user_uuid).execute().data:
        return 'VENTAS'
    if supabase.table('operador_mapeo').select('id_operador_int').eq('id_supabase_uuid', user_uuid).execute().data:
        return 'OPERACIONES'
    if supabase.table('contador_mapeo').select('id_contador_int').eq('id_supabase_uuid', user_uuid).execute().data:
        return 'CONTABLE'
    if supabase.table('gerente_mapeo').select('id_gerente_int').eq('id_supabase_uuid', user_uuid).execute().data:
        return 'GERENCIA'
    return 'SIN_ROL'

def handle_login_supabase(email, password):
    """Maneja el inicio de sesion"""

    try:
        # 1. Autneticacion de Supabase Auth (CLAVE para RLS)
        user_session = supabase.auth.sign_in_with_password({
            "email": email,
            "password" : password,
        })

        user_uuid = user_session.user.id

        # 2. Determinar el rol de la aplicacion usando el UUID
        app_role = fetch_app_role(user_uuid)

        if app_role == 'SIN_ROL':
            st.error("Su correo esta en la base de datos, pero no esta asignado a un rol")
            supabase.auth.sign_out()
            return

        # 3. Establecer el estado
        st.session_state['authenticated'] = True
        st.session_state['user_role'] = app_role
        st.session_state['user_email'] = email
        st.rerun()
    except Exception as e:
        st.error(f'Error de autenticacion. Verifique su correo electronico y contraseña: {e}')

def logout_user():
    """Cierra la sesion del usuario y limpia el estado."""
    supabase.auth.sign_out()
    st.session_state.clear()
    st.rerun()

def main():
    st.set_page_config(page_title="SGVO - Cusco", layout="wide") # Nombre de la pestaña

    if not st.session_state['authenticated']:
        # ... Lógica de Login (Correcta) ...
        st.title("🔐 Sistema VCP - Iniciar Sesión")
        st.warning("Ingrese su correo y su contraseña de su área para acceder .")
        
        with st.form("login_form"):
            email = st.text_input("Correo Electronico")
            password = st.text_input("Contraseña", type="password")

            submitted = st.form_submit_button("Entrar")

        if submitted:
                handle_login_supabase(email, password)
        return

    # --- 3. Lógica Principal de Navegación (para autenticados) ---
    rol = st.session_state['user_role']

    st.session_state['rol_actual'] = rol
    st.sidebar.title("Navegación")
    st.sidebar.write(f"**Rol Actual:** {rol}")

    paginas_permitidas = MODULOS_VISIBLES.get(rol, [])

    if paginas_permitidas:
        # Se renombra 'nombres_modulos' a 'nombres_funcionalidades' para claridad
        nombres_funcionalidades = [nombre for nombre, _ in paginas_permitidas]
        
        st.sidebar.markdown("---")
        st.sidebar.info(f"Usuario: {st.session_state['user_email']}")
        
        # Seleccion de página en el sidebar
        index_seleccionado = st.sidebar.selectbox(
            "Seleccione Módulo",
            range(len(nombres_funcionalidades)), # <<-- CORRECCIÓN A: nombres_funcionalidades
            format_func=lambda i: nombres_funcionalidades[i]
        )

        # Capturamos el nombre de la funcionalidad (Ej. "Registro de Leads")
        funcionalidad_seleccionada = paginas_permitidas[index_seleccionado][0]# <<-- CORRECCIÓN A: funcionalidad_seleccionada
        pagina_seleccionada_archivo = paginas_permitidas[index_seleccionado][1]

        try:
            nombres_modulo_completo = f'vistas.{pagina_seleccionada_archivo}'

            # 🚨 AÑADIR ESTA LÍNEA DE DIAGNÓSTICO TEMPORAL 🚨
            st.warning(f"Intentando importar el módulo: {nombres_modulo_completo}")

            modulo = importlib.import_module(nombres_modulo_completo)

            if hasattr(modulo, 'mostrar_pagina'):
                # Pasamos el cliente Supabase para que las vistas puedan hacer consultas seguras
                modulo.mostrar_pagina(funcionalidad_seleccionada, rol_actual= rol, supabase_client=supabase)
            else:
                 st.error(f"Error: El módulo {pagina_seleccionada_archivo} no tiene la función de entrada esperada.")
 
        except ImportError as e:
            st.error(f"Error de Carga: No se pudo importar el módulo {pagina_seleccionada_archivo}. Revise la estructura de carpetas y el nombre del archivo.")
        except Exception as e:
            st.error(f"Error General Inesperado durante la ejecución del módulo: {e}")

    st.sidebar.markdown("---")
    st.sidebar.button("Cerrar Sesión", on_click=logout_user)

if __name__ == "__main__":
    main()