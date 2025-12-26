# vistas/page_ventas.py (Corregido)

import streamlit as st
import pandas as pd
# Importar el controlador
from controllers.venta_controller import VentaController
# <<-- CORRECCIÓN CRÍTICA: Debe ser 'lead_controller' (todo minúscula)
from controllers.lead_controller import LeadController 

# Inicializar el controlador (se hace una sola vez)
venta_controller = VentaController()
# <<-- CORRECCIÓN: Debe ser 'lead_controller'
lead_controller = LeadController() 

# ... (El resto del código de _mostrar_formulario_leads, _mostrar_seguimiento, etc., es correcto)
# ...

def mostrar_pagina(funcionalidad_seleccionada):
    """
    Función que recibe el nombre del menú seleccionado y llama a la UI específica.
    """
    st.title("Módulo de Leads y Ventas")
    st.caption(f"Funcionalidad actual: **{funcionalidad_seleccionada}**")
    st.markdown("---")
    
    if funcionalidad_seleccionada == "Registro de Leads":
        _mostrar_formulario_leads()
        
    elif funcionalidad_seleccionada == "Seguimiento de Leads":
        _mostrar_seguimiento()
        
    elif funcionalidad_seleccionada == "Registro de Ventas":
        _mostrar_registro_ventas()
        
    else:
        st.error(f"Funcionalidad '{funcionalidad_seleccionada}' no implementada para este módulo.")