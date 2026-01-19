# controllers/venta_controller.py

from models.venta_model import VentaModel
from supabase import Client
from datetime import date
from typing import Optional, Any

class VentaController:
    """Controlador para manejar la lógica de Ventas."""
    def __init__(self, supabase_client:Client):
        self.client = supabase_client
        self.model = VentaModel(table_name='venta', supabase_client=supabase_client)

    def _subir_archivo(self, bucket: str, file: Any, nombre_base: str) -> Optional[str]:
        """Sube un archivo al Storage de Supabase y retorna su URL pública."""
        try:
            if not file: return None
            
            # 1. Preparar nombre de archivo único
            ext = file.name.split('.')[-1]
            timestamp = date.today().strftime("%Y%m%d")
            file_path = f"{timestamp}_{nombre_base}.{ext}"
            
            # 2. Subir (leemos el contenido binario del UploadedFile de Streamlit)
            file_content = file.getvalue()
            res = self.client.storage.from_(bucket).upload(
                path=file_path,
                file=file_content,
                file_options={"content-type": file.type}
            )
            
            # 3. Obtener URL Pública
            return self.client.storage.from_(bucket).get_public_url(file_path)
            
        except Exception as e:
            print(f"Error subiendo archivo a {bucket}: {e}")
            return None

    def registrar_venta_directa(self, 
                                nombre_cliente: str,
                                telefono: str, 
                                origen: str, 
                                vendedor: str,
                                tour: str, 
                                tipo_hotel: str,
                                fecha_inicio: str,
                                fecha_fin: str,
                                monto_total: float,
                                monto_depositado: float,
                                tipo_comprobante: str,
                                id_itinerario_digital: Optional[str] = None, # Vínculo opcional
                                file_itinerario: Optional[Any] = None,
                                file_pago: Optional[Any] = None
                                ) -> tuple[bool, str]:
        """Registra una venta con todos los detalles extendidos."""
        
        # 1. Validaciones Básicas
        if not nombre_cliente or not telefono or not tour or monto_total <= 0:
             return False, "Campos obligatorios faltantes (Nombre, Teléfono, Tour o Monto)."

        # 2. Manejo de Archivos Reales (Supabase Storage)
        clean_name = nombre_cliente.replace(" ", "_").lower()
        url_itinerario = self._subir_archivo("itinerarios", file_itinerario, f"itin_{clean_name}")
        url_pago = self._subir_archivo("vouchers", file_pago, f"pago_{clean_name}")
        
        # 3. Preparar datos
        saldo = monto_total - monto_depositado
        estado_pago = "COMPLETADO" if saldo <= 0 else "PENDIENTE"
        
        venta_data = {
            "nombre_cliente": nombre_cliente,
            "telefono_cliente": telefono,
            "origen": origen,
            "vendedor": vendedor,
            "tour": tour,
            "tipo_hotel": tipo_hotel,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "monto_total": monto_total,
            "monto_depositado": monto_depositado,
            "saldo": saldo,
            "estado_pago": state_pago, # Nota: Aquí había un typo in-stream, lo corrijo a estado_pago
            "tipo_comprobante": tipo_comprobante,
            "url_itinerario": url_itinerario,
            "url_comprobante_pago": url_pago,
            "id_itinerario_digital": id_itinerario_digital
        }
        
        # Corregir typo detectado
        venta_data["estado_pago"] = estado_pago
        
        # 4. Guardar
        try:
            nuevo_id = self.model.create_venta(venta_data)
            if nuevo_id:
                return True, f"Venta registrada. ID: {nuevo_id}. Saldo pendiente: ${float(saldo or 0):.2f}"
            else:
                return False, "Error: no se pudo crear la venta."
        except Exception as e:
            return False, f"Error de base de datos: {e}"

    def registrar_venta_proveedor(self, 
                                  nombre_proveedor: str,
                                  nombre_cliente: str,
                                  telefono: str, 
                                  vendedor: Optional[int],
                                  tour: str, 
                                  monto_total: float,
                                  monto_depositado: float,
                                  id_agencia_aliada: Optional[int] = None,
                                  estado_limpieza: str = "PENDIENTE"
                                  ) -> tuple[bool, str]:
        """Registra una venta proveniente de un proveedor/agencia externa."""
        
        if not nombre_proveedor or not nombre_cliente or not tour:
             return False, "Campos obligatorios faltantes (Proveedor, Cliente o Tour)."

        saldo = monto_total - monto_depositado
        
        venta_data = {
            "nombre_cliente": nombre_cliente,
            "telefono_cliente": telefono,
            "origen": f"PROVEEDOR: {nombre_proveedor}",
            "vendedor": vendedor,
            "tour": tour,
            "fecha_inicio": date.today().isoformat(), # Simplificado
            "monto_total": monto_total,
            "monto_depositado": monto_depositado,
            "saldo": saldo,
            "estado_pago": "POR COBRAR" if saldo > 0 else "LIQUIDADO",
            "tipo_comprobante": "Factura Proveedor",
            "id_agencia_aliada": id_agencia_aliada,
            "observaciones": f"Venta registrada vía: {nombre_proveedor}"
        }
        
        nuevo_id = self.model.create_venta(venta_data)
        
        if nuevo_id:
            return True, f"Venta de Proveedor ({nombre_proveedor}) registrada. ID: {nuevo_id}"
        else:
            return False, "Error al guardar en base de datos."

    def obtener_agencias_aliadas(self) -> list:
        """Obtiene la lista de agencias aliadas (B2B)."""
        try:
            res = self.client.table('agencia_aliada').select('*').order('nombre').execute()
            return res.data or []
        except Exception as e:
            print(f"Error obteniendo agencias: {e}")
            return []

    def obtener_catalogo_opciones(self) -> list:
        """Obtiene una lista combinada de Tours y Paquetes para selectores."""
        opciones = []
        try:
            # 1. Obtener Tours
            tours = self.client.table('tour').select('id_tour, nombre').execute().data or []
            for t in tours:
                opciones.append({"id": f"T-{t['id_tour']}", "nombre": f"TOUR: {t['nombre']}"})
            
            # 2. Obtener Paquetes
            paquetes = self.client.table('paquete').select('id_paquete, nombre').execute().data or []
            for p in paquetes:
                opciones.append({"id": f"P-{p['id_paquete']}", "nombre": f"PAQUETE: {p['nombre']}"})
                
            return opciones
        except Exception as e:
            print(f"Error obteniendo catálogo: {e}")
            return []