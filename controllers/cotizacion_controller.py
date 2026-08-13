# controllers/cotizacion_controller.py

from supabase import Client
from typing import List, Dict, Any, Tuple, Optional


class CotizacionController:
    """Controlador del Cotizador de Costos interno (Operaciones)."""

    def __init__(self, supabase_client: Client):
        self.client = supabase_client

    def obtener_proveedores_por_tipo_servicio(self, tipo_servicio: str) -> List[Dict[str, Any]]:
        """
        Devuelve los proveedores activos que tienen al menos una tarifa cargada
        de ese tipo de servicio en su tarifario, junto con esas tarifas.
        """
        try:
            res = self.client.table('proveedor').select('id_proveedor, nombre_comercial, tarifario, tours_opera').eq('activo', True).execute()
            resultado = []
            for p in (res.data or []):
                tarifario = p.get('tarifario') or []
                items_tipo = [t for t in tarifario if t.get('tipo_servicio') == tipo_servicio]
                if items_tipo:
                    resultado.append({
                        'id_proveedor': p['id_proveedor'],
                        'nombre_comercial': p['nombre_comercial'],
                        'tarifas': items_tipo,
                        'tours_opera': p.get('tours_opera') or []
                    })
            return resultado
        except Exception as e:
            print(f"Error obteniendo proveedores por tipo de servicio: {e}")
            return []

    def guardar_cotizacion(self, nombre: str, creado_por: Optional[str], items: List[Dict],
                            moneda: str, total_estimado: float) -> Tuple[bool, Optional[str]]:
        """Guarda una cotización de costos armada en el Cotizador."""
        try:
            data = {
                "nombre": nombre.strip(),
                "creado_por": creado_por,
                "items": items,
                "moneda": moneda,
                "total_estimado": round(total_estimado, 2)
            }
            res = self.client.table('cotizacion_costos').insert(data).execute()
            if res.data:
                return True, res.data[0].get('id_cotizacion')
            return False, None
        except Exception as e:
            print(f"Error guardando cotización de costos: {e}")
            return False, None

    def obtener_cotizaciones(self) -> List[Dict[str, Any]]:
        """Lista las cotizaciones de costos guardadas, más recientes primero."""
        try:
            res = self.client.table('cotizacion_costos').select('*').order('created_at', desc=True).execute()
            return res.data or []
        except Exception as e:
            print(f"Error obteniendo cotizaciones de costos: {e}")
            return []

    def eliminar_cotizacion(self, id_cotizacion: str) -> bool:
        """Elimina una cotización de costos guardada."""
        try:
            self.client.table('cotizacion_costos').delete().eq('id_cotizacion', id_cotizacion).execute()
            return True
        except Exception as e:
            print(f"Error eliminando cotización de costos: {e}")
            return False
