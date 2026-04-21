# controllers/proveedor_controller.py

from models.proveedor_model import ProveedorModel
from supabase import Client as SupabaseClient
from typing import List, Dict, Any, Tuple

class ProveedorController:
    def __init__(self, supabase_client: SupabaseClient):
        self.model = ProveedorModel(supabase_client)

    def obtener_proveedores(self) -> List[Dict[str, Any]]:
        """Obtiene la lista de proveedores."""
        return self.model.obtener_todos()

    def registrar_proveedor(self, nombre: str, servicios: List[str], contacto: str, pais: str = "Perú", 
                            ruc: str = None, email: str = None, persona_contacto: str = None, 
                            url_drive: str = None, cuentas_bancarias: List[Dict] = None,
                            puntos_operacion: List[str] = None, detalles_categoria: Dict = None) -> Tuple[bool, str]:
        """
        Registra un nuevo proveedor con soporte para campos extendidos y JSONB.
        """
        if not nombre:
            return False, "El nombre comercial es obligatorio."
        
        data = {
            "nombre_comercial": nombre.strip(),
            "servicios_ofrecidos": servicios,
            "contacto_telefono": contacto.strip() if contacto else None,
            "pais": pais.strip() if pais else "Perú",
            "ruc": ruc.strip() if ruc else None,
            "email": email.strip() if email else None,
            "persona_contacto": persona_contacto.strip() if persona_contacto else None,
            "url_drive": url_drive.strip() if url_drive else None,
            "cuentas_bancarias": cuentas_bancarias if cuentas_bancarias is not None else [],
            "puntos_operacion": puntos_operacion if puntos_operacion is not None else [],
            "detalles_categoria": detalles_categoria if detalles_categoria is not None else {},
            "activo": True
        }
        
        try:
            nuevo_id = self.model.crear_proveedor(data)
            if nuevo_id:
                return True, f"Proveedor '{nombre}' registrado exitosamente."
            else:
                return False, "No se pudo registrar en la base de datos."
        except Exception as e:
            return False, f"Error al registrar: {str(e)}"

    def actualizar_proveedor(self, id_proveedor: int, nombre: str, servicios: List[str], contacto: str, pais: str, activo: bool,
                             ruc: str = None, email: str = None, persona_contacto: str = None, 
                             url_drive: str = None, cuentas_bancarias: List[Dict] = None,
                             puntos_operacion: List[str] = None, detalles_categoria: Dict = None) -> Tuple[bool, str]:
        """
        Actualiza los datos de un proveedor existente, incluyendo campos dinámicos JSON.
        """
        if not id_proveedor:
            return False, "ID de proveedor no proporcionado."
        
        data = {
            "nombre_comercial": nombre.strip(),
            "servicios_ofrecidos": servicios,
            "contacto_telefono": contacto.strip() if contacto else None,
            "pais": pais.strip() if pais else "Perú",
            "ruc": ruc.strip() if ruc else None,
            "email": email.strip() if email else None,
            "persona_contacto": persona_contacto.strip() if persona_contacto else None,
            "url_drive": url_drive.strip() if url_drive else None,
            "cuentas_bancarias": cuentas_bancarias if cuentas_bancarias is not None else [],
            "puntos_operacion": puntos_operacion if puntos_operacion is not None else [],
            "detalles_categoria": detalles_categoria if detalles_categoria is not None else {},
            "activo": activo
        }

        try:
            exito = self.model.update_by_id(id_proveedor, data)
            if exito:
                return True, "Proveedor actualizado exitosamente."
            else:
                return False, "No se encontraron cambios o el proveedor no existe."
        except Exception as e:
            return False, f"Error al actualizar: {str(e)}"
