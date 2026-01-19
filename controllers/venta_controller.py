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
            "estado_pago": estado_pago,
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
                                  telefono: Optional[str], 
                                  vendedor: Optional[int],
                                  tour: str, 
                                  monto_total: float,
                                  monto_depositado: float,
                                  id_agencia_aliada: Optional[int] = None,
                                  estado_limpieza: str = "PENDIENTE",
                                  fecha_inicio: Optional[date] = None,
                                  fecha_fin: Optional[date] = None,
                                  cantidad_pax: int = 1
                                  ) -> tuple[bool, str]:
        """Registra una venta proveniente de una agencia externa (B2B)."""
        try:
            # Sincronizado: saldo = monto_total - monto_depositado
            saldo = monto_total - monto_depositado
            estado_pago = "PAGADO" if saldo <= 0 else "DEBITO"
            
            venta_data = {
                "nombre_cliente": nombre_cliente,
                "telefono_cliente": telefono,
                "vendedor": vendedor,
                "tour": tour,
                "monto_total": monto_total,
                "monto_depositado": monto_depositado,
                "saldo": saldo,
                "estado_pago": estado_pago,
                "origen": f"B2B: {nombre_proveedor}",
                "id_agencia_aliada": id_agencia_aliada,
                "fecha_inicio": (fecha_inicio or date.today()).isoformat(),
                "fecha_fin": (fecha_fin or date.today()).isoformat(),
                "cantidad_pasajeros": cantidad_pax
            }
            
            res_id = self.model.create_venta(venta_data)
            
            if res_id:
                return True, f"Venta B2B de {nombre_proveedor} registrada éxito (ID: {res_id})"
            return False, "No se pudo registrar la venta en la base de datos."
            
        except Exception as e:
            print(f"Error en registro B2B: {e}")
            return False, f"Error de base de datos: {e}"

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

    def obtener_ventas_agencia(self, id_agencia: int) -> list:
        """Obtiene las ventas vinculadas a una agencia aliada específica con nombre de cliente."""
        try:
            # Join con cliente para obtener el nombre
            res = self.client.table('venta').select('*, cliente(nombre)').eq('id_agencia_aliada', id_agencia).order('fecha_venta', desc=True).execute()
            
            # Aplanar el resultado para que 'nombre_cliente' esté al primer nivel
            data = []
            for v in (res.data or []):
                v['nombre_cliente'] = v.get('cliente', {}).get('nombre', 'Desconocido')
                data.append(v)
            return data
        except Exception as e:
            print(f"Error obteniendo ventas de agencia: {e}")
            return []