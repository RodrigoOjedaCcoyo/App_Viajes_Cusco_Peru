# controllers/proveedor_controller.py

from models.proveedor_model import ProveedorModel
from supabase import Client as SupabaseClient
from typing import List, Dict, Any, Tuple, Optional

class ProveedorController:
    def __init__(self, supabase_client: SupabaseClient):
        self.model = ProveedorModel(supabase_client)

    def obtener_proveedores(self, incluir_inactivos: bool = False) -> List[Dict[str, Any]]:
        """Obtiene la lista de proveedores (activos, o todos)."""
        return self.model.obtener_todos(incluir_inactivos=incluir_inactivos)

    def registrar_proveedor(self, nombre: str, servicios: List[str], contacto: str, pais: str = "Perú",
                            ruc: str = None, email: str = None, persona_contacto: str = None,
                            url_drive: str = None, cuentas_bancarias: List[Dict] = None,
                            puntos_operacion: List[str] = None, detalles_categoria: Dict = None,
                            tarifario: List[Dict] = None, tours_opera: List[int] = None) -> Tuple[bool, str]:
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
            "tarifario": tarifario if tarifario is not None else [],
            "tours_opera": tours_opera if tours_opera is not None else [],
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
                             puntos_operacion: List[str] = None, detalles_categoria: Dict = None,
                             tarifario: List[Dict] = None, tours_opera: List[int] = None) -> Tuple[bool, str]:
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
            "tarifario": tarifario if tarifario is not None else [],
            "tours_opera": tours_opera if tours_opera is not None else [],
            "activo": activo
        }

        try:
            exito = self.model.update_by_id(id_proveedor, data)
            if exito:
                if self.tabla_tours_disponible():
                    self.sync_tours_opera(id_proveedor)
                return True, "Proveedor actualizado exitosamente."
            else:
                return False, "No se encontraron cambios o el proveedor no existe."
        except Exception as e:
            return False, f"Error al actualizar: {str(e)}"

    def eliminar_proveedor(self, id_proveedor: int) -> Tuple[bool, str]:
        """
        Ya NO borra: desactiva (ver desactivar_proveedor). Se mantiene por compatibilidad.
        """
        return self.desactivar_proveedor(id_proveedor)

    # ═══════════════════════════════════════════════════════════════
    # DESACTIVAR EN VEZ DE BORRAR
    # Borrar un proveedor eliminaba también su historial de pagos (pago_operativo está en
    # ON DELETE CASCADE). Ahora solo se desactiva: deja de aparecer para trabajar, pero
    # sus pagos, ventas y tarifas se conservan y se puede reactivar.
    # ═══════════════════════════════════════════════════════════════
    def desactivar_proveedor(self, id_proveedor: int) -> Tuple[bool, str]:
        if not id_proveedor:
            return False, "ID de proveedor no proporcionado."
        try:
            ok = self.model.update_by_id(id_proveedor, {"activo": False})
            return (True, "Proveedor desactivado. Su historial de pagos y ventas se conserva.") if ok \
                else (False, "El proveedor no existe.")
        except Exception as e:
            return False, f"Error al desactivar: {str(e)}"

    def reactivar_proveedor(self, id_proveedor: int) -> Tuple[bool, str]:
        try:
            ok = self.model.update_by_id(id_proveedor, {"activo": True})
            return (True, "Proveedor reactivado.") if ok else (False, "El proveedor no existe.")
        except Exception as e:
            return False, f"Error al reactivar: {str(e)}"

    # ═══════════════════════════════════════════════════════════════
    # TARIFARIO (servicios genéricos: transporte, guía, tickets...)
    # Se guarda al instante para que no se pierda si se cambia de pestaña.
    # ═══════════════════════════════════════════════════════════════
    def guardar_tarifario(self, id_proveedor: int, tarifario: List[Dict]) -> Tuple[bool, str]:
        try:
            self.model.client.table('proveedor').update({"tarifario": tarifario}).eq('id_proveedor', id_proveedor).execute()
            return True, "Tarifario guardado."
        except Exception as e:
            return False, f"No se pudo guardar el tarifario: {str(e)}"

    # ═══════════════════════════════════════════════════════════════
    # TARIFAS POR TOUR (tabla proveedor_tour, compartida con el Constructor)
    # ═══════════════════════════════════════════════════════════════
    @staticmethod
    def _es_tabla_faltante(e: Exception) -> bool:
        txt = str(e)
        return 'proveedor_tour' in txt and ('does not exist' in txt or 'schema cache' in txt or '42P01' in txt or 'PGRST205' in txt)

    def tabla_tours_disponible(self) -> bool:
        """False si todavía no se ejecutó la migración migrations/add_proveedor_tour.sql."""
        try:
            self.model.client.table('proveedor_tour').select('id_proveedor_tour').limit(1).execute()
            return True
        except Exception as e:
            if self._es_tabla_faltante(e):
                return False
            raise

    def listar_ofertas(self, id_proveedor: int) -> List[Dict[str, Any]]:
        try:
            res = self.model.client.table('proveedor_tour').select('*, tour(nombre, activo)') \
                .eq('id_proveedor', id_proveedor).execute()
            filas = res.data or []
            filas.sort(key=lambda r: ((r.get('tour') or {}).get('nombre') or '').upper())
            return filas
        except Exception as e:
            if not self._es_tabla_faltante(e):
                print(f"Error listando tarifas por tour: {e}")
            return []

    def sync_tours_opera(self, id_proveedor: int) -> None:
        """proveedor.tours_opera (lo usa el Cotizador) = tours con tarifa activa."""
        try:
            res = self.model.client.table('proveedor_tour').select('id_tour') \
                .eq('id_proveedor', id_proveedor).eq('activo', True).execute()
            ids = sorted({int(r['id_tour']) for r in (res.data or [])})
            self.model.client.table('proveedor').update({"tours_opera": ids}).eq('id_proveedor', id_proveedor).execute()
        except Exception as e:
            if not self._es_tabla_faltante(e):
                print(f"Error sincronizando tours_opera: {e}")

    def guardar_oferta(self, id_oferta: Optional[int], data: Dict[str, Any]) -> Tuple[bool, str]:
        """Crea o actualiza la tarifa de un proveedor para un tour. Un solo preferido por tour."""
        try:
            if data.get('preferido') and data.get('activo', True):
                q = self.model.client.table('proveedor_tour').update({"preferido": False}) \
                    .eq('id_tour', data['id_tour']).eq('preferido', True)
                if id_oferta:
                    q = q.neq('id_proveedor_tour', id_oferta)
                q.execute()
            else:
                data['preferido'] = False if not data.get('activo', True) else bool(data.get('preferido'))
            if id_oferta:
                self.model.client.table('proveedor_tour').update(data).eq('id_proveedor_tour', id_oferta).execute()
            else:
                self.model.client.table('proveedor_tour').insert(data).execute()
            self.sync_tours_opera(data['id_proveedor'])
            return True, "Tarifa del tour guardada."
        except Exception as e:
            if self._es_tabla_faltante(e):
                return False, "Falta ejecutar la migración migrations/add_proveedor_tour.sql en Supabase."
            if 'proveedor_tour_unico' in str(e) or '23505' in str(e):
                return False, "Este proveedor ya tiene una tarifa para ese tour: edita la existente."
            return False, f"No se pudo guardar la tarifa: {str(e)}"

    def eliminar_oferta(self, id_oferta: int, id_proveedor: int) -> Tuple[bool, str]:
        try:
            self.model.client.table('proveedor_tour').delete().eq('id_proveedor_tour', id_oferta).execute()
            self.sync_tours_opera(id_proveedor)
            return True, "Tarifa eliminada."
        except Exception as e:
            return False, f"No se pudo eliminar la tarifa: {str(e)}"

    def vincular_tarifa_a_tour(self, id_proveedor: int, tarifario: List[Dict], idx: int, id_tour: int) -> Tuple[bool, str, List[Dict]]:
        """
        Pasa una tarifa antigua del tarifario (texto libre, p. ej. un ENDOSE) a la tabla de
        tarifas por tour, vinculada al tour del catálogo, y la quita del tarifario.
        Devuelve el tarifario actualizado.
        """
        if idx < 0 or idx >= len(tarifario):
            return False, "Tarifa no encontrada.", tarifario
        item = tarifario[idx]
        moneda = str(item.get('moneda') or 'USD').upper()
        precio = float(item.get('precio') or 0)
        por_grupo = item.get('unidad') == 'Por Grupo'
        incluye_txt = str(item.get('incluye') or '')
        incluye = [x.strip() for x in incluye_txt.replace('+', ',').replace('\n', ',').split(',') if x.strip()]
        data = {
            "id_proveedor": id_proveedor,
            "id_tour": int(id_tour),
            "modalidad": "GRUPO" if por_grupo else "PAX",
            "costo_adulto_nac": precio if (moneda == 'PEN' and not por_grupo) else 0,
            "costo_adulto_ext": precio if (moneda != 'PEN' and not por_grupo) else 0,
            "costo_adulto_can": precio if (moneda != 'PEN' and not por_grupo) else 0,
            "costo_grupo_nac": precio if (moneda == 'PEN' and por_grupo) else None,
            "costo_grupo_ext": precio if (moneda != 'PEN' and por_grupo) else None,
            "capacidad_grupo": int(item.get('capacidad_pax') or 1) if por_grupo else None,
            "incluye": incluye,
            "notas": item.get('notas') or None,
            "activo": True,
        }
        ok, msg = self.guardar_oferta(None, data)
        if not ok:
            return False, msg, tarifario
        nuevo = [t for i, t in enumerate(tarifario) if i != idx]
        ok2, msg2 = self.guardar_tarifario(id_proveedor, nuevo)
        if not ok2:
            return False, msg2, tarifario
        return True, "Tarifa vinculada al tour del catálogo.", nuevo
