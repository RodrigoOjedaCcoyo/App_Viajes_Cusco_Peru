# main.py 
import streamlit as st
import sys
import os
import importlib
from supabase import create_client, Client

# --- 1. Configuración de Roles y Rutas ---
ROLES = ["VENTAS", "OPERACIONES", "CONTABILIDAD", "GERENCIA"]
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 1. Aseguramos que Python encuentre las carpetas, dándole la MÁXIMA PRIORIDAD
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# 2. Insertamos la ruta en la posición 0 (el primer lugar donde buscar)
controllers_path = os.path.join(BASE_DIR, 'controllers')
vistas_path = os.path.join(BASE_DIR, 'vistas')
models_path = os.path.join(BASE_DIR, 'models')

if controllers_path not in sys.path:
    sys.path.insert(1, controllers_path)
if vistas_path not in sys.path:
    sys.path.insert(1, vistas_path)
if models_path not in sys.path:
    sys.path.insert(1, models_path)

# Mapeo de roles a las funcionalidades (Actualizado para Usuario Maestro)
MODULOS_VISIBLES = {
    "VENTAS": [
        ("Dashboard Comercial", "page_dashboards"),
        ("Gestión de Registros", "page_ventas")
    ],
    "OPERACIONES": [
        ("Dashboard Operaciones", "page_dashboards"),
        ("Gestión de Registros", "page_operaciones")
    ],
    "CONTABILIDAD": [
        ("Dashboard Contable", "page_dashboards"),
        ("Gestión de Registros", "page_contabilidad")
    ],
    "GERENCIA": [
        ("Dashboard Ejecutivo", "page_dashboards"),
        ("Auditoría de Gestión", "page_gerencia")
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
st.session_state['supabase_client'] = supabase

# --- 3. Logica de Autenticación y Estado ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'user_role' not in st.session_state:
    st.session_state['user_role'] = None
if 'user_email' not in st.session_state:
    st.session_state['user_email'] = None

# Modificacion: Autenticación simplificada por Email (Sin UUIDs)
@st.cache_data
def fetch_app_role(email):
    """
    Busca el correo en la tabla usuarios_app y retorna el Rol.
    """
    try:
        res = supabase.table('usuarios_app').select('rol').eq('email', email).execute()
        if res.data:
            return res.data[0]['rol'], email # Usamos el email como ID interno para simplificar
        
        # Fallback si no está en la tabla pero es un usuario de Supabase
        return 'SIN_ROL', None
    except Exception as e:
        print(f"Error buscando rol por email: {e}")
        return 'SIN_ROL', None

def handle_login_supabase(email, password):
    """Maneja el inicio de sesion usando Supabase Auth y validacion de email."""

    try:
        # 1. Autenticación de Supabase Auth
        user_session = supabase.auth.sign_in_with_password({
            "email": email,
            "password" : password,
        })

        # 2. Determinar el rol usando el correo directamente
        app_role, user_id_simplificado = fetch_app_role(email)

        if app_role == 'SIN_ROL':
            st.error("Acceso denegado: Tu correo no tiene un rol asignado en 'usuarios_app'.")
            supabase.auth.sign_out()
            return

        # 3. Establecer el estado
        st.session_state['authenticated'] = True
        st.session_state['user_role'] = app_role
        st.session_state['user_id'] = user_id_simplificado 
        st.session_state['user_email'] = email
        st.rerun()
    except Exception as e:
        st.error(f'Error de inicio de sesión: {e}')

def logout_user():
    """Cierra la sesion del usuario y limpia el estado."""
    supabase.auth.sign_out()
    st.session_state.clear()
    st.rerun()

def main():
    st.set_page_config(page_title="Latitud VCP - Cusco", layout="wide") # Nombre de la pestaña

    if not st.session_state['authenticated']:
        # ... Lógica de Login (Correcta) ...
        st.title("🔐 Sistema Latitud VCP - Iniciar Sesión")
        st.warning("Ingrese su correo y su contraseña de su área para acceder .")
        
        with st.form("login_form"):
            email = st.text_input("Correo Electronico")
            password = st.text_input("Contraseña", type="password")

            submitted = st.form_submit_button("Entrar")

        if submitted:
                handle_login_supabase(email, password)
        return

    # --- 3. Lógica Principal de Navegación (para autenticados) ---
    rol_db = st.session_state['user_role']
    
    # Selector de Entorno para Gerencia
    if rol_db == "GERENCIA":
        if 'view_as' not in st.session_state:
            st.session_state['view_as'] = "GERENCIA"
        
        st.sidebar.markdown("### 🏢 Selector de Área")
        col1, col2 = st.sidebar.columns(2)
        
        # Botones de cambio de contexto
        if col1.button("🏛️ Gerencia", use_container_width=True, type="primary" if st.session_state['view_as'] == "GERENCIA" else "secondary"):
            st.session_state['view_as'] = "GERENCIA"
            st.rerun()
        if col2.button("📈 Ventas", use_container_width=True, type="primary" if st.session_state['view_as'] == "VENTAS" else "secondary"):
            st.session_state['view_as'] = "VENTAS"
            st.rerun()
        if col1.button("⚙️ Operac.", use_container_width=True, type="primary" if st.session_state['view_as'] == "OPERACIONES" else "secondary"):
            st.session_state['view_as'] = "OPERACIONES"
            st.rerun()
        if col2.button("🏦 Contab.", use_container_width=True, type="primary" if st.session_state['view_as'] == "CONTABILIDAD" else "secondary"):
            st.session_state['view_as'] = "CONTABILIDAD"
            st.rerun()
            
        rol_actual = st.session_state['view_as']
        st.sidebar.markdown(f"👁️ **Visto como:** `{rol_actual}`")
    else:
        rol_actual = rol_db

    st.session_state['rol_actual'] = rol_actual
    st.sidebar.title("Navegación")
    st.sidebar.write(f"**Usuario:** {st.session_state['user_email']}")
    
    paginas_permitidas = MODULOS_VISIBLES.get(rol_actual, [])

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


            modulo = importlib.import_module(nombres_modulo_completo)
            importlib.reload(modulo) # <--- FORZAR RECARGA PARA DESARROLLO

            if hasattr(modulo, 'mostrar_pagina'):
                # Pasamos el cliente Supabase para que las vistas puedan hacer consultas seguras
                # IMPORTANTE: Pasamos rol_db tmb para que las páginas sepan que es Gerencia supervisando
                modulo.mostrar_pagina(funcionalidad_seleccionada, rol_actual=rol_db, user_id=st.session_state.get('user_id'), supabase_client=supabase)
            else:
                 st.error(f"Error: El módulo {pagina_seleccionada_archivo} no tiene la función de entrada esperada.")
 
        except ImportError as e:
            st.error(f"Error de Carga: No se pudo importar el módulo {pagina_seleccionada_archivo}. Detalle del error: {e}")
        except Exception as e:
            st.error(f"Error General Inesperado durante la ejecución del módulo: {e}")

    st.sidebar.markdown("---")
    c_ref, c_out = st.sidebar.columns(2)
    if c_ref.button("🔄 Refrescar", use_container_width=True, help="Forzar actualización de datos"):
        st.rerun()
    if c_out.button("🚪 Salir", use_container_width=True):
        logout_user()

if __name__ == "__main__":
    main()