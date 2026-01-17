# controllers/venta_controller.py (Nuevo archivo)

from models.venta_model import VentaModel
from supabase import Client
from datetime import date
from typing import Optional, Any

class VentaController:
    """Controlador para manejar la lógica de Ventas."""
    def __init__(self, supabase_client:Client):
        self.model = VentaModel(table_name='Ventas', supabase_client=supabase_client)

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
                                file_itinerario: Optional[Any] = None,
                                file_pago: Optional[Any] = None
                                ) -> tuple[bool, str]:
        """Registra una venta con todos los detalles extendidos."""
        
        # 1. Validaciones Básicas
        if not nombre_cliente or not telefono or not tour or monto_total <= 0:
             return False, "Campos obligatorios faltantes (Nombre, Teléfono, Tour o Monto)."

        # 2. Manejo de Archivos (Simulado por ahora - se guardaría en Storage)
        # En una implementación real, aquí se subirían los archivos a Supabase Storage
        url_itinerario = "pendiente_upload" if file_itinerario else None
        url_pago = "pendiente_upload" if file_pago else None
        
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
            "estado_pago": estado_pago,
            "tipo_comprobante": tipo_comprobante,
            "url_itinerario": url_itinerario,
            "url_comprobante_pago": url_pago,
        }
        
        # 4. Guardar
        nuevo_id = self.model.create_venta(venta_data)
        
        if nuevo_id:
            return True, f"Venta registrada. ID: {nuevo_id}. Saldo pendiente: ${saldo:.2f}"
        else:
            return False, "Error al guardar en base de datos."

    def registrar_venta_proveedor(self, 
                                  nombre_proveedor: str,
                                  nombre_cliente: str,
                                  telefono: str, 
                                  vendedor: str,
                                  tour: str, 
                                  monto_total: float,
                                  monto_depositado: float,
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
            "observaciones": f"Venta registrada vía: {nombre_proveedor}"
        }
        
        nuevo_id = self.model.create_venta(venta_data)
        
        if nuevo_id:
            return True, f"Venta de Proveedor ({nombre_proveedor}) registrada. ID: {nuevo_id}"
        else:
            return False, "Error al guardar en base de datos."