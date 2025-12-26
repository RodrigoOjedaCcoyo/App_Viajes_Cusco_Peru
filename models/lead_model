# models/lead_model.py
from .base_model import BaseModel
import pandas as pd

class LeadModel(BaseModel):
    def __init__(self):
        super().__init__()
        # Simulación de la tabla de Leads (estructura del Apps Script)
        self.leads_data = [
            {'numero': '51987654321', 'vendedor': 'Angel', 'estado': 'Interesado', 'whatsapp': '51987654321'},
            {'numero': '51999888777', 'vendedor': 'Angel', 'estado': 'Seguimiento', 'whatsapp': '51999888777'},
            {'numero': '51555444333', 'vendedor': 'Abel', 'estado': 'Nuevo', 'whatsapp': ''},
            {'numero': '51111222333', 'vendedor': 'Abel', 'estado': 'Vendido', 'whatsapp': '51111222333'},
        ]

    def get_active_leads(self, vendedor: str):
        """ Simula la obtención de leads activos por vendedor (como obtenerLeadsActivos en .gs) """
        activos = []
        for lead in self.leads_data:
            if lead['vendedor'] == vendedor and lead['estado'] not in ['Vendido', 'Perdido']:
                activos.append(lead)
        return activos

    def insert_new_lead(self, datos: dict):
        """ Simula el registro de un nuevo vendedor (como registrarVendedor en .gs) """
        # La tabla se actualizaría aquí
        print(f"MODEL: Insertando nuevo Lead: {datos}")
        return {"status": "success", "id": 1}

    def update_lead_state(self, numero: str, estado: str, detalle: str):
        """ Simula la actualización del estado y registro de historial (como registrarSeguimiento en .gs) """
        # 1. Actualizar estado del lead
        print(f"MODEL: Actualizando estado de {numero} a {estado}")
        # 2. Insertar en tabla de historial
        print(f"MODEL: Registrando historial de seguimiento: {detalle}")
        return {"status": "success"}