# models/venta_model.py

from .base_model import BaseModel
from datetime import datetime
from supabase import Client
from typing import Dict, Any, Optional

class VentaModel(BaseModel):
    """Modelo para la gestión de Ventas (Conversiones de Leads)."""

    def __init__(self, table_name: str, supabase_client: Client): 
        # Sincronizado con esquema SQL: tabla 'venta', PK 'id_venta'
        super().__init__('venta', supabase_client, primary_key='id_venta') 

    # --- MÉTODOS DE BÚSQUEDA DE IDs (HELPERS) ---
    def get_vendedor_id_by_query(self, query: str) -> Optional[int]:
        """Busca el ID del vendedor por su nombre o email."""
        if not query: return None
        try:
            # 1. Intentar por Email (exacto)
            res_e = self.client.table('vendedor').select('id_vendedor').eq('email', query).execute()
            if res_e.data:
                return res_e.data[0]['id_vendedor']
            
            # 2. Intentar por Nombre (parcial)
            res_n = self.client.table('vendedor').select('id_vendedor').ilike('nombre', f"%{query}%").limit(1).execute()
            if res_n.data:
                return res_n.data[0]['id_vendedor']
        except Exception as e:
            print(f"Error buscando vendedor {query}: {e}")
        return None

    def get_tour_id_by_name(self, nombre: str) -> Optional[int]:
        """Busca el ID del tour por su nombre exacto o parcial."""
        if not nombre: return None
        try:
            res = self.client.table('tour').select('id_tour').ilike('nombre', f"%{nombre}%").limit(1).execute()
            if res.data:
                return res.data[0]['id_tour']
        except Exception as e:
            print(f"Error buscando tour {nombre}: {e}")
        return None

    def get_or_create_cliente(self, nombre: str, celular: str, origen: str) -> Optional[int]:
        """Busca un cliente por nombre (simplicidad), si no existe lo crea."""
        if not nombre: return None
        try:
            # 1. Buscar existente
            res = self.client.table('cliente').select('id_cliente').eq('nombre', nombre).limit(1).execute()
            if res.data:
                return res.data[0]['id_cliente']
            
            # 2. Crear nuevo
            nuevo_cliente = {
                "nombre": nombre,
                "tipo_cliente": "B2C",
                "pais": "Desconocido", 
                "genero": "N/A"
            }
            res_insert = self.client.table('cliente').insert(nuevo_cliente).select('id_cliente').execute()
            if res_insert.data:
                return res_insert.data[0]['id_cliente']
        except Exception as e:
            print(f"Error creando/buscando cliente: {e}")
        return None

    # --- MÉTODO PRINCIPAL DE CREACIÓN DE VENTA ---
    def create_venta(self, venta_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Orquesta la creación de la Venta Relacional según esquema SQL:
        """
        
        # 1. Obtener IDs Relacionales
        id_cliente = self.get_or_create_cliente(venta_data.get('nombre_cliente'), venta_data.get('telefono_cliente'), venta_data.get('origen'))
        id_vendedor = self.get_vendedor_id_by_query(venta_data.get('vendedor'))
        id_tour_paquete = self.get_tour_id_by_name(venta_data.get('tour'))

        if not id_cliente:
            print("Falla Venta: Cliente no pudo ser creado/encontrado.")
            return None
        
        if not id_vendedor:
            # Fallback: Usar el primer vendedor si no se encuentra ninguno por nombre
            res_fb = self.client.table('vendedor').select('id_vendedor').limit(1).execute()
            if res_fb.data:
                id_vendedor = res_fb.data[0]['id_vendedor']
            else:
                print("Falla Venta: No hay vendedores en la base de datos.")
                return None

        # 2. Preparar Payload para tabla 'venta' (Columnas del esquema SQL)
        datos_venta_sql = {
            "id_cliente": id_cliente,
            "id_vendedor": id_vendedor,
            "fecha_venta": venta_data.get("fecha_registro", datetime.now().strftime("%Y-%m-%d")),
            "canal_venta": venta_data.get("origen", "DIRECTO"),
            "precio_total_cierre": venta_data.get("monto_total"),
            "moneda": "USD",
            "estado_venta": "CONFIRMADO",
            "id_paquete": None,
            "tour_nombre": venta_data.get("tour"),  # Guardar nombre directamente
            "id_itinerario_digital": venta_data.get("id_itinerario_digital") # Sincronizado: Vínculo con Itinerario Digital
        }

        # 3. Insertar Venta
        nuevo_id_venta = self.save(datos_venta_sql) 
        
        if nuevo_id_venta:
            # 4. Registrar Pago Inicial (Tabla 'pago')
            if venta_data.get("monto_depositado", 0) > 0:
                try:
                    pago_data = {
                        "id_venta": nuevo_id_venta,
                        "fecha_pago": datetime.now().strftime("%Y-%m-%d"),
                        "monto_pagado": venta_data.get("monto_depositado"),
                        "moneda": "USD",
                        "metodo_pago": "OTRO",
                        "tipo_pago": "ADELANTO",
                        "observacion": f"Pago inicial registrado. Saldo: {venta_data.get('saldo')}"
                    }
                    self.client.table('pago').insert(pago_data).execute()
                except Exception as e:
                    print(f"Error registrando pago inicial: {e}")

            # 5. Registrar Detalle venta_tour
            if id_tour_paquete:
                 try:
                    detalle_tour = {
                        "id_venta": nuevo_id_venta,
                        "n_linea": 1,
                        "id_tour": id_tour_paquete,
                        "precio_aplicado": venta_data.get("monto_total"),
                        "costo_aplicado": 0,
                        "cantidad_pasajeros": 1,
                        "fecha_servicio": venta_data.get("fecha_inicio"),
                        "id_itinerario_dia_index": venta_data.get("itinerario_dia_index", 1) # Vínculo cronológico
                    }
                    self.client.table('venta_tour').insert(detalle_tour).execute()
                 except Exception as e:
                     print(f"Error insertando detalle tour: {e}")

        return nuevo_id_venta
