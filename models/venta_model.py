# models/venta_model.py

from .base_model import BaseModel
from datetime import datetime, timedelta
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
        if not nombre: 
            raise Exception("El nombre del cliente es obligatorio")
        
        # 1. Buscar existente
        res = self.client.table('cliente').select('id_cliente').eq('nombre', nombre).limit(1).execute()
        if res.data:
            return res.data[0]['id_cliente']
        
        # 2. Crear nuevo (esto lanzará excepción si falla)
        nuevo_cliente = {
            "nombre": nombre,
            "tipo_cliente": "B2C",
            "pais": "Desconocido", 
            "genero": "N/A"
        }
        res_insert = self.client.table('cliente').insert(nuevo_cliente).execute()
        if res_insert.data and len(res_insert.data) > 0:
            return res_insert.data[0].get('id_cliente')
        else:
            raise Exception("Supabase no devolvió el ID del cliente creado")

    # --- MÉTODO PRINCIPAL DE CREACIÓN DE VENTA ---
    def create_venta(self, venta_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Orquesta la creación de la Venta Relacional según esquema SQL:
        """
        
        # 1. Obtener IDs Relacionales
        id_cliente = self.get_or_create_cliente(venta_data.get('nombre_cliente'), venta_data.get('telefono_cliente'), venta_data.get('origen'))
        
        if not id_cliente:
            raise Exception("No se pudo crear o encontrar el cliente. Verifique la tabla 'cliente'.")
        
        id_vendedor = self.get_vendedor_id_by_query(venta_data.get('vendedor'))
        
        if not id_vendedor:
            # Fallback: Usar el primer vendedor si no se encuentra ninguno por nombre
            res_fb = self.client.table('vendedor').select('id_vendedor').limit(1).execute()
            if res_fb.data:
                id_vendedor = res_fb.data[0]['id_vendedor']
            else:
                raise Exception("No hay vendedores en la base de datos.")
        
        tour_raw = venta_data.get('tour', '')
        id_paquete = None
        id_tour_catalogo = None
        
        if str(tour_raw).startswith("P-"):
            try: id_paquete = int(tour_raw.replace("P-", ""))
            except: pass
        elif str(tour_raw).startswith("T-"):
            try: id_tour_catalogo = int(tour_raw.replace("T-", ""))
            except: pass
            
        if not id_tour_catalogo and not id_paquete:
            id_tour_catalogo = self.get_tour_id_by_name(tour_raw)

        # 2. Preparar Payload para tabla 'venta' (Columnas del esquema SQL)
        id_itin = venta_data.get("id_itinerario_digital")
        num_pax_final = 1
        
        # Intentar extraer info extra del itinerario si existe
        if id_itin:
            try:
                res_it = self.client.table('itinerario_digital').select('datos_render').eq('id_itinerario_digital', id_itin).single().execute()
                if res_it.data:
                    render = res_it.data.get('datos_render', {})
                    # Extraer Pax
                    num_pax_final = int(render.get('cantidad_pax') or render.get('pax_count') or 1)
            except: pass

        datos_venta_sql = {
            "id_cliente": id_cliente,
            "id_vendedor": id_vendedor,
            "fecha_venta": venta_data.get("fecha_registro", datetime.now().strftime("%Y-%m-%d")),
            "canal_venta": venta_data.get("origen", "DIRECTO"),
            "precio_total_cierre": venta_data.get("monto_total"),
            "moneda": venta_data.get("moneda", "USD"),
            "estado_pago": "COMPLETADO" if (venta_data.get("monto_total", 0) - venta_data.get("monto_depositado", 0)) <= 0 else "PENDIENTE",
            "estado_venta": "CONFIRMADO",
            "id_paquete": id_paquete,
            "tour_nombre": tour_raw,
            "num_pasajeros": num_pax_final,
            "id_agencia_aliada": venta_data.get("id_agencia_aliada"),
            "id_itinerario_digital": id_itin
        }

        # 3. Insertar Venta (esto lanzará excepción si falla)
        nuevo_id_venta = self.save(datos_venta_sql)
        
        if not nuevo_id_venta:
            raise Exception("El método save() devolvió None. Error desconocido al insertar en la tabla 'venta'.")
        
        # 4. Registrar Pago Inicial (Tabla 'pago')
        if venta_data.get("monto_depositado", 0) > 0:
            try:
                pago_data = {
                    "id_venta": nuevo_id_venta,
                    "fecha_pago": datetime.now().strftime("%Y-%m-%d"),
                    "monto_pagado": venta_data.get("monto_depositado"),
                    "moneda": venta_data.get("moneda", "USD"),
                    "metodo_pago": "OTRO",
                    "tipo_pago": "ADELANTO",
                    "observacion": f"Pago inicial registrado. Saldo: {venta_data.get('saldo')}"
                }
                self.client.table('pago').insert(pago_data).execute()
            except Exception as e:
                # No fallar toda la venta si el pago no se registra
                print(f"Advertencia: Error registrando pago inicial: {e}")

        # 5. Registrar Detalles venta_tour (Expansión de Días para Operaciones)
        try:
            f_inicio = datetime.strptime(venta_data.get("fecha_inicio"), "%Y-%m-%d").date()
            f_fin = datetime.strptime(venta_data.get("fecha_fin"), "%Y-%m-%d").date()
            num_dias = (f_fin - f_inicio).days + 1
            if num_dias < 1: num_dias = 1
            
            # Intentar obtener detalles del itinerario digital si existe
            itin_detalles = []
            id_itin = venta_data.get("id_itinerario_digital")
            if id_itin:
                res_itin = self.client.table('itinerario_digital').select('datos_render').eq('id_itinerario_digital', id_itin).single().execute()
                if res_itin.data:
                    render = res_itin.data.get('datos_render', {})
                    # Soportar todas las estructuras: 'itinerario_detalles' (nuevo), 'itinerario_detales' (viejo) o 'days' (externo)
                    itin_detalles = render.get('itinerario_detalles', []) or render.get('itinerario_detales', []) or render.get('days', [])

            for i in range(num_dias):
                f_servicio = f_inicio + timedelta(days=i)
                
                # Determinar nombre del servicio para este día
                nombre_servicio_dia = venta_data.get("tour") # Default
                if i < len(itin_detalles):
                    dia_info = itin_detalles[i]
                    # Soportar todas las estructuras: 'nombre', 'titulo' (el tuyo) o 'title'
                    nombre_servicio_dia = dia_info.get('titulo') or dia_info.get('nombre') or dia_info.get('title') or nombre_servicio_dia

                detalle_tour = {
                    "id_venta": nuevo_id_venta,
                    "n_linea": i + 1,
                    "id_tour": id_tour_catalogo if i == 0 else None, # Solo vinculamos al catálogo el primer día por ahora
                    "fecha_servicio": f_servicio.isoformat(),
                    "precio_applied": venta_data.get("monto_total") if i == 0 else 0,
                    "precio_vendedor": venta_data.get("monto_total") if i == 0 else 0, # Guardar el original
                    "costo_applied": 0,
                    "cantidad_pasajeros": num_pax_final,
                    "observaciones": nombre_servicio_dia, # Usamos observaciones para guardar el nombre del tour diario
                    "id_itinerario_dia_index": i + 1
                }
                self.client.table('venta_tour').insert(detalle_tour).execute()
        except Exception as e:
            print(f"Advertencia: Error expandiendo detalle tour: {e}")

        return nuevo_id_venta
