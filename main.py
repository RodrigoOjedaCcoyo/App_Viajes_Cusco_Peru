# main.py
import streamlit as st
import sys
import os
import importlib

# --- 1. Configuración de Roles y Rutas ---

# Definición de ROLES (Contraseñas de ejemplo para el acceso)
ROLES = {
    "VENTAS": "1234",
    "OPERACIONES": "5678",
    "CONTABLE": "9012",
    "GERENCIA": "0000"
}

# Añadir la carpeta raíz al PATH para que Python encuentre 'controllers' y 'models'
# ESTO ES CRÍTICO. Si su aplicación está en un subdirectorio, esta línea ayuda.
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mapeo de roles a los módulos que pueden ver (RBAC)
MODULOS_VISIBLES = {
    "VENTAS": [("Ventas", "pages.1_Ventas")],
    "OPERACIONES": [("Ventas", "pages.1_Ventas"), ("Operaciones", "pages.2_Operaciones")],
    "CONTABLE": [("Ventas", "pages.1_Ventas"), ("Operaciones", "pages.2_Operaciones"), ("Contabilidad", "pages.3_Contabilidad")],
    "GERENCIA": [("Ventas", "pages.1_Ventas"), ("Operaciones", "pages.2_Operaciones"), ("Contabilidad", "pages.3_Contabilidad"), ("Gerencia", "pages.4_Gerencia")]
}

# --- 2. Lógica de Autenticación y Estado ---

if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'user_role' not in st.session_state:
    st.session_state['user_role'] = None

def handle_login(password):
    """Verifica la contraseña y establece el rol en el estado de la sesión."""
    for role, clave in ROLES.items():
        if password == clave:
            st.session_state['authenticated'] = True
            st.session_state['user_role'] = role
            st.rerun() 
            return
    st.error("Contraseña incorrecta. Acceso denegado.")

def main():
    st.set_page_config(page_title="SGVO - Cusco", layout="wide")

    if not st.session_state['authenticated']:
        # Muestra el formulario de LOGIN
        st.title("🔐 Sistema VCP - Iniciar Sesión")
        st.warning("Ingrese la contraseña de su área para acceder .")
        
        with st.form("login_form"):
            password = st.text_input("Contraseña de Acceso", type="password")
            if st.form_submit_button("Entrar"):
                handle_login(password)
        return

    # --- 3. Lógica Principal de Navegación (para autenticados) ---
    rol = st.session_state['user_role']
    
    st.sidebar.title("Navegación")
    st.sidebar.write(f"**Rol Actual:** {rol}")

    paginas_permitidas = MODULOS_VISIBLES.get(rol, [])
    
    if paginas_permitidas:
        nombres_modulos = [nombre for nombre, _ in paginas_permitidas]
        
        # Seleccion de página en el sidebar
        index_seleccionado = st.sidebar.selectbox(
            "Seleccione Módulo", 
            range(len(nombres_modulos)), 
            format_func=lambda i: nombres_modulos[i]
        )
        
        pagina_seleccionada = paginas_permitidas[index_seleccionado][1]

        try:
            # Importa y ejecuta la función principal del módulo seleccionado
            modulo = importlib.import_module(pagina_seleccionada)
            modulo.mostrar_pagina() 
        except ImportError as e:
            # Este error es lo que hemos estado viendo.
            st.error(f"Error de Carga: No se pudo importar el módulo {pagina_seleccionada}. La arquitectura MVC está incompleta o con errores de ruta.")
            st.code(e)
        except AttributeError:
             st.error(f"Error: La función 'mostrar_pagina()' no está definida en el módulo {pagina_seleccionada}.")

    st.sidebar.button("Cerrar Sesión", on_click=lambda: st.session_state.clear())
    
if __name__ == "__main__":
    main()