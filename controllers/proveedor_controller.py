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

    def registrar_proveedor(self, nombre: str, servicios: List[str], contacto: str, pais: str = "Perú") -> Tuple[bool, str]:
        """
        Registra un nuevo proveedor en la base de datos.
        Retorna (exito, mensaje).
        """
        if not nombre:
            return False, "El nombre comercial es obligatorio."
        
        data = {
            "nombre_comercial": nombre.strip(),
            "servicios_ofrecidos": servicios,
            "contacto_telefono": contacto.strip() if contacto else None,
            "pais": pais.strip() if pais else "Perú",
            "activo": True
        }
        
        try:
            nuevo_id = self.model.crear_proveedor(data)
            if nuevo_id:
                return True, f"Proveedor '{nombre}' registrado exitosamente con ID {nuevo_id}."
            else:
                return False, "No se pudo registrar el proveedor en la base de datos."
        except Exception as e:
            return False, f"Error al registrar proveedor: {str(e)}"

    def actualizar_proveedor(self, id_proveedor: int, nombre: str, servicios: List[str], contacto: str, pais: str, activo: bool) -> Tuple[bool, str]:
        """
        Actualiza un proveedor existente.
        """
        if not id_proveedor:
            return False, "ID de proveedor no proporcionado."
        
        data = {
            "nombre_comercial": nombre.strip(),
            "servicios_ofrecidos": servicios,
            "contacto_telefono": contacto.strip() if contacto else None,
            "pais": pais.strip() if pais else "Perú",
            "activo": activo
        }

        try:
            exito = self.model.update_by_id(id_proveedor, data)
            if exito:
                return True, "Proveedor actualizado exitosamente."
            else:
                return False, "No se encontró el proveedor o no se realizaron cambios."
        except Exception as e:
            return False, f"Error al actualizar proveedor: {str(e)}"
