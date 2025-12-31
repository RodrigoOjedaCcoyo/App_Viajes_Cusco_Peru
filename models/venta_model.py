# models/venta_model.py

from .base_model import BaseModel
from datetime import datetime
from supabase import Client
from typing import Dict, Any, Optional

class VentaModel(BaseModel):
    """Modelo para la gestión de Ventas (Conversiones de Leads)."""

    # CORRECCIÓN: El constructor debe recibir table_name y pasarlo a BaseModel.
    def __init__(self, table_name: str, supabase_client: Client): 
        # Llama al constructor de BaseModel, pasando el nombre de la tabla (ej: 'Venta') y el cliente.
        super().__init__('Venta', supabase_client) 

    # --- MÉTODOS DE BÚSQUEDA DE IDs (HELPERS) ---
    def get_vendedor_id_by_name(self, nombre: str) -> Optional[int]:
        """Busca el ID del vendedor por su nombre."""
        try:
            # Nota: Ajusta 'nombre' si en tu BD es 'nombre_vendedor' o similar
            res = self.client.table('Vendedor').select('id_vendedor').ilike('nombre', f"%{nombre}%").limit(1).execute()
            if res.data:
                return res.data[0]['id_vendedor']
        except Exception as e:
            print(f"Error buscando vendedor {nombre}: {e}")
        return None

    def get_tour_id_by_name(self, nombre: str) -> Optional[int]:
        """Busca el ID del tour por su nombre exacto o parcial."""
        try:
            res = self.client.table('Tour').select('id_tour').ilike('nombre', f"%{nombre}%").limit(1).execute()
            if res.data:
                return res.data[0]['id_tour']
        except Exception as e:
            print(f"Error buscando tour {nombre}: {e}")
        return None

    def get_or_create_cliente(self, nombre: str, celular: str, origen: str) -> Optional[int]:
        """Busca un cliente por celular, si no existe lo crea."""
        try:
            # 1. Buscar existente
            res = self.client.table('Cliente').select('id_cliente').eq('nombre', nombre).limit(1).execute()
            if res.data:
                return res.data[0]['id_cliente']
            
            # 2. Crear nuevo (Valores por defecto para campos obligatorios)
            # Asumimos que la tabla Cliente requiere: nombre, tipo_cliente (B2C), pais (Desconocido), genero (N/A)
            nuevo_cliente = {
                "nombre": nombre,
                "tipo_cliente": "B2C",
                "pais": "Desconocido", 
                "genero": "N/A"
                # Nota: 'numero_celular' no está en la tabla Cliente según tu esquema, 
                # parece estar en Lead. Por simplicidad, guardamos lo básico para que inserte.
            }
            res_insert = self.client.table('Cliente').insert(nuevo_cliente).select('id_cliente').execute()
            if res_insert.data:
                return res_insert.data[0]['id_cliente']
        except Exception as e:
            print(f"Error creando/buscando cliente: {e}")
        return None

    # --- MÉTODO PRINCIPAL DE CREACIÓN DE VENTA ---
    def create_venta(self, venta_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Orquesta la creación de la Venta Relacional:
        1. Obtiene/Crea Cliente
        2. Obtiene ID Vendedor y ID Tour
        3. Inserta Venta
        4. Inserta Pago (si hay monto depositado)
        """
        
        # 1. Obtener IDs Relacionales
        id_cliente = self.get_or_create_cliente(venta_data.get('nombre_cliente'), venta_data.get('telefono_cliente'), venta_data.get('origen'))
        id_vendedor = self.get_vendedor_id_by_name(venta_data.get('vendedor'))
        id_tour_paquete = self.get_tour_id_by_name(venta_data.get('tour')) # Si es paquete o tour individual

        if not id_cliente or not id_vendedor:
            print(f"Falla de integridad referencial: ClienteID={id_cliente}, VendedorID={id_vendedor}")
            return None

        # 2. Preparar Payload para tabla 'Venta' (Solo columnas que existen en el esquema SQL)
        datos_venta_sql = {
            "id_cliente": id_cliente,
            "id_vendedor": id_vendedor,
            "fecha_venta": venta_data.get("fecha_registro", datetime.now().strftime("%Y-%m-%d")),
            "canal_venta": venta_data.get("origen", "DIRECTO"), # Mapeamos Origen -> Canal
            "precio_total_cierre": venta_data.get("monto_total"),
            "moneda": "USD",
            "estado_venta": "CONFIRMADO - PENDIENTE DATA",
            # Nota: id_paquete se deja NULL por ahora asumiendo venta de Tour Individual
            # Si 'tour' fuera un paquete, habría que buscar en tabla Paquete.
            "id_paquete": None 
        }

        # 3. Insertar Venta
        nuevo_id_venta = self.save(datos_venta_sql) # Usa el método save base a la tabla 'Venta'
        
        if nuevo_id_venta:
            # 4. Registrar Pago Inicial (Si existe depósito)
            if venta_data.get("monto_depositado", 0) > 0:
                try:
                    pago_data = {
                        "id_venta": nuevo_id_venta,
                        "fecha_pago": datetime.now().strftime("%Y-%m-%d"),
                        "monto_pagado": venta_data.get("monto_depositado"),
                        "moneda": "USD",
                        "metodo_pago": "OTRO", # Se podría pedir en formulario
                        "tipo_pago": "ADELANTO",
                        "observacion": f"Pago inicial. Saldo: {venta_data.get('saldo')}"
                    }
                    self.client.table('Pago').insert(pago_data).execute()
                except Exception as e:
                    print(f"Error registrando pago inicial: {e}")

            # 5. Registrar Detalle Venta_Tour (Opcional, pero recomendado para consistencia)
            if id_tour_paquete:
                 try:
                    detalle_tour = {
                        "id_venta": nuevo_id_venta,
                        "n_linea": 1,
                        "id_tour": id_tour_paquete,
                        "precio_aplicado": venta_data.get("monto_total"),
                        "costo_aplicado": 0, # Dato desconocido
                        "cantidad_pasajeros": 1, # Dato desconocido, asumimos 1
                        "fecha_servicio": venta_data.get("fecha_inicio")
                    }
                    self.client.table('Venta_Tour').insert(detalle_tour).execute()
                 except Exception as e:
                     print(f"Error insertando detalle tour: {e}")

        return nuevo_id_venta