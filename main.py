# main.py (Corregido)
import streamlit as st
import sys
import os
import importlib

# --- 1. Configuración de Roles y Rutas ---
ROLES = {
    "VENTAS": "1234",
    "OPERACIONES": "5678",
    "CONTABLE": "9012",
    "GERENCIA": "0000"
}
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 🚨 CORRECCIÓN CLAVE: REEMPLAZA sys.path.append(BASE_DIR) por ESTE BLOQUE 🚨
# 1. Aseguramos que Python encuentre las carpetas, dándole la MÁXIMA PRIORIDAD
if BASE_DIR in sys.path:
    sys.path.remove(BASE_DIR)
# 2. Insertamos la ruta en la posición 0 (el primer lugar donde buscar)
sys.path.insert(0, BASE_DIR)

# Mapeo de roles a las funcionalidades (Correcto)
MODULOS_VISIBLES = {
    "VENTAS": [
        ("Registro de Leads", "vistas.page_ventas"),    
        ("Seguimiento de Leads", "vistas.page_ventas"), 
        ("Registro de Ventas", "vistas.page_ventas")
    ],
    "OPERACIONES": [
        ("Dashboard Operaciones", "vistas.page_operaciones")
    ],
    "CONTABLE": [
        ("Reporte de Montos", "vistas.page_contabilidad"), 
        ("Auditoría de Pagos", "vistas.page_contabilidad")
    ],
    "GERENCIA": [
        ("Dashboard Ejecutivo", "vistas.page_gerencia"), 
        ("Auditoría Completa", "vistas.page_gerencia")
    ]
}
# --- 2. Lógica de Autenticación y Estado (Punto de Mejora Añadido) ---

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
    st.set_page_config(page_title="SGVO - Cusco", layout="wide") # Nombre de la pestaña

    if not st.session_state['authenticated']:
        # ... Lógica de Login (Correcta) ...
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
        # Se renombra 'nombres_modulos' a 'nombres_funcionalidades' para claridad
        nombres_funcionalidades = [nombre for nombre, _ in paginas_permitidas] 
        
        # Seleccion de página en el sidebar
        index_seleccionado = st.sidebar.selectbox(
            "Seleccione Módulo", 
            range(len(nombres_funcionalidades)), # <<-- CORRECCIÓN A: nombres_funcionalidades
            format_func=lambda i: nombres_funcionalidades[i]
        )
        
        # Capturamos el nombre de la funcionalidad (Ej. "Registro de Leads")
        funcionalidad_seleccionada = paginas_permitidas[index_seleccionado][0] # <<-- CORRECCIÓN A: funcionalidad_seleccionada
        pagina_seleccionada_archivo = paginas_permitidas[index_seleccionado][1]

        try:
            # Importa y ejecuta la función principal del módulo seleccionado
            modulo = importlib.import_module(pagina_seleccionada_archivo)
            
            if pagina_seleccionada_archivo == "vistas.page_operaciones":
                modulo.main_operaciones() # Llama a la función principal del dashboard
            # Si es otro módulo (como page_ventas), usa la lógica original con el argumento funcionalidad.
            elif hasattr(modulo, 'mostrar_pagina'):
                modulo.mostrar_pagina(funcionalidad_seleccionada) 
            else:
                 st.error(f"Error: El módulo {pagina_seleccionada_archivo} no tiene la función de entrada esperada.")
 
            
        except ImportError as e:
            st.error(f"Error de Carga: No se pudo importar el módulo {pagina_seleccionada_archivo}. Revise la estructura de carpetas y el nombre del archivo.")
        except AttributeError as e:
            st.error(f"Error General Inesperado durante la ejecución del módulo: {e}")
            
    st.sidebar.markdown("---")
    st.sidebar.button("Cerrar Sesión", on_click=lambda: st.session_state.clear())
    
if __name__ == "__main__":
    main()