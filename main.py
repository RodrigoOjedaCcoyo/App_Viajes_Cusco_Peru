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

# Aseguramos que Python encuentre las carpetas (Correcto)
sys.path.append(os.path.join(BASE_DIR, 'vistas'))
sys.path.append(os.path.join(BASE_DIR, 'controllers')) 
sys.path.append(os.path.join(BASE_DIR, 'models'))

# Mapeo de roles a las funcionalidades (Correcto)
MODULOS_VISIBLES = {
    "VENTAS": [
        ("Registro de Leads", "page_ventas"),    
        ("Seguimiento de Leads", "page_ventas"), 
        ("Registro de Ventas", "page_ventas")    
    ],
    "OPERACIONES": [
        ("Seguimiento de Tours", "page_operaciones"), 
        ("Actualización de Ventas", "page_operaciones") 
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

# --- 2. Lógica de Autenticación y Estado (Punto de Mejora Añadido) ---

if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'user_role' not in st.session_state:
    st.session_state['user_role'] = None
if 'vendedor_actual' not in st.session_state: # CRÍTICO: Necesario para el filtrado en page_ventas
    st.session_state['vendedor_actual'] = None 


def handle_login(password):
    """Verifica la contraseña y establece el rol en el estado de la sesión."""
    for role, clave in ROLES.items():
        if password == clave:
            st.session_state['authenticated'] = True
            st.session_state['user_role'] = role
            
            # 💡 PUNTO DE MEJORA: Asignación de Vendedor al hacer login
            if role == "VENTAS":
                # Asumimos que el vendedor es "Angel" para el rol VENTAS (usado en la simulación)
                st.session_state['vendedor_actual'] = "Angel" 
            
            st.rerun() 
            return
    st.error("Contraseña incorrecta. Acceso denegado.")

def main():
    st.set_page_config(page_title="SGVO - Cusco", layout="wide")

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
            
            # Pasamos la funcionalidad seleccionada a la vista
            modulo.mostrar_pagina(funcionalidad_seleccionada) 
            
        except ImportError as e:
            st.error(f"Error de Carga: No se pudo importar el módulo {pagina_seleccionada_archivo}. Revise la estructura de carpetas y el nombre del archivo.")
            st.code(e)
        except AttributeError:
             st.error(f"Error: La función 'mostrar_pagina()' no está definida en el módulo {pagina_seleccionada_archivo}.")

    st.sidebar.markdown("---")
    st.sidebar.button("Cerrar Sesión", on_click=lambda: st.session_state.clear())
    
if __name__ == "__main__":
    main()