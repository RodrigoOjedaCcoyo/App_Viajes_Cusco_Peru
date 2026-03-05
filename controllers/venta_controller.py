# controllers/venta_controller.py

from models.venta_model import VentaModel
from supabase import Client
from datetime import date
from typing import Optional, Any
import pandas as pd

class VentaController:
    """Controlador para manejar la lógica de Ventas."""
    def __init__(self, supabase_client:Client):
        self.client = supabase_client
        self.model = VentaModel(supabase_client)

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
                                moneda: str = "USD",
                                tipo_cambio: Optional[float] = None,
                                id_itinerario_digital: Optional[str] = None,
                                id_lead: Optional[int] = None,
                                items_ingreso: Optional[list] = None,
                                metodo_pago: str = "OTRO",
                                cantidad_pax: int = 1
                                ) -> tuple[bool, str]:
        """Registra una venta con todos los detalles extendidos."""
        
        # 1. Validaciones Básicas
        if not nombre_cliente or not telefono or not tour or monto_total <= 0:
             return False, "Campos obligatorios faltantes (Nombre, Teléfono, Tour o Monto)."

        # 2. Preparar datos
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
            "tipo_comprobante": tipo_comprobante,
            "moneda": moneda,
            "tipo_cambio": tipo_cambio,
            "id_itinerario_digital": id_itinerario_digital,
            "id_lead": id_lead,
            "items_ingreso": items_ingreso,
            "metodo_pago": metodo_pago,
            "cantidad": cantidad_pax
        }
        
        # Corregir typo detectado
        venta_data["estado_pago"] = estado_pago
        
        # 4. Guardar
        try:
            nuevo_id = self.model.create_venta(venta_data)
            if nuevo_id:
                return True, f"Venta registrada. ID: {nuevo_id}. Saldo pendiente: {moneda} {float(saldo or 0):.2f}"
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
                                  cantidad_pax: int = 1,
                                  id_itinerario_digital: Optional[str] = None,
                                  id_lead: Optional[int] = None,
                                  tipo_comprobante: str = "RECIBO",
                                  tipo_cambio: Optional[float] = None,
                                  items_ingreso: Optional[list] = None,
                                  metodo_pago: str = "OTRO"
                                  ) -> tuple[bool, str]:
        """Registra una venta proveniente de una agencia externa (B2B)."""
        try:
            # 1. Lógica de Pago
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
                "cantidad": cantidad_pax,
                "id_itinerario_digital": id_itinerario_digital,
                "tipo_comprobante": tipo_comprobante,
                "tipo_cambio": tipo_cambio,
                "items_ingreso": items_ingreso,
                "metodo_pago": metodo_pago
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
            # Join con cliente para obtener el nombre - Excluir finalizadas
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

    def obtener_ventas_directas(self) -> list:
        """Obtiene las ventas directas (B2C) que NO tienen agencia aliada."""
        try:
            # Join con cliente - Excluir finalizadas
            res = self.client.table('venta').select('*, cliente(nombre)').is_('id_agencia_aliada', 'null').order('fecha_venta', desc=True).execute()
            
            data = []
            for v in (res.data or []):
                v['nombre_cliente'] = v.get('cliente', {}).get('nombre', 'Desconocido')
                data.append(v)
            return data
        except Exception as e:
            print(f"Error obteniendo ventas directas: {e}")
            return []

    def obtener_detalles_itinerario_venta(self, id_venta: int) -> list:
        """Obtiene el desglose de días/servicios de una venta específica (venta_tour)."""
        try:
            res = self.client.table('venta_tour').select('*').eq('id_venta', id_venta).order('n_linea').execute()
            return res.data or []
        except Exception as e:
            print(f"Error obteniendo detalles de itinerario: {e}")
            return []

    def obtener_todas_ventas_b2b(self) -> list:
        """Obtiene todas las ventas registradas vía agencias aliadas para el dashboard global."""
        try:
            res = self.client.table('venta').select('*, agencia_aliada(nombre), cliente(nombre)').not_.is_('id_agencia_aliada', 'null').order('fecha_venta', desc=True).execute()
            data = []
            for v in (res.data or []):
                v['nombre_agencia'] = v.get('agencia_aliada', {}).get('nombre', 'Desconocido')
                v['nombre_cliente'] = v.get('cliente', {}).get('nombre', 'Desconocido')
                data.append(v)
            return data
        except Exception as e:
            print(f"Error obteniendo ventas B2B globales: {e}")
            return []

    def obtener_venta_por_id(self, id_venta: int) -> Optional[dict]:
        """Obtiene los datos básicos de una venta por su ID."""
        try:
            res = self.client.table('venta').select('id_venta, moneda, precio_total_cierre, tour_nombre').eq('id_venta', id_venta).single().execute()
            return res.data
        except Exception as e:
            print(f"Error obteniendo venta {id_venta}: {e}")
            return None

    def registrar_pago(self, 
                       id_venta: int, 
                       monto_pagado: float, 
                       moneda_pago: str, 
                       tasa_cambio: float, 
                       fecha_pago: str, 
                       metodo: str, 
                       tipo_pago: str, 
                       comprobante: str = "RECIBO") -> tuple[bool, str]:
        """Registra un pago individual manejando la conversión de moneda si es necesario."""
        try:
            # 1. Obtener la moneda de la venta
            venta = self.obtener_venta_por_id(id_venta)
            if not venta:
                return False, f"No se encontró la venta con ID {id_venta}"
            
            moneda_venta = venta.get('moneda', 'USD')
            
            # 2. Calcular monto equivalente en moneda de la venta
            monto_equivalente = monto_pagado
            if moneda_pago != moneda_venta:
                if tasa_cambio <= 0:
                    return False, "El tipo de cambio debe ser mayor a 0 para monedas distintas."
                monto_equivalente = round(monto_pagado / tasa_cambio, 2)
            else:
                tasa_cambio = 1.0
            
            # 3. Preparar data
            pago_data = {
                "id_venta": id_venta,
                "fecha_pago": fecha_pago,
                "monto_pagado": monto_pagado,
                "moneda": moneda_pago,
                "metodo_pago": metodo,
                "tipo_pago": tipo_pago,
                "tipo_comprobante": comprobante,
                "tasa_cambio": tasa_cambio,
                "monto_moneda_venta": monto_equivalente
            }
            
            # 4. Insertar
            self.client.table('pago').insert(pago_data).execute()
            
            return True, f"Pago de {moneda_pago} {monto_pagado:,.2f} registrado exitosamente. Abono a cuenta: {moneda_venta} {monto_equivalente:,.2f}"
            
        except Exception as e:
            return False, f"Error al registrar pago: {e}"

    def vincular_pagos_masivos(self, df: Any) -> dict:
        """Procesa un DataFrame de Excel/CSV para registrar múltiples pagos a la vez con soporte multimoneda."""
        exitos = 0
        errores = []
        
        # Cache de monedas de venta para evitar consultas repetitivas
        cache_monedas = {}
        
        for idx, row in df.iterrows():
            try:
                id_v = row.get('ID Venta')
                monto = row.get('Monto')
                
                if pd.isna(id_v) or pd.isna(monto):
                    continue
                
                id_v = int(id_v)
                monto = float(monto)
                moneda_pago = str(row.get('Moneda') or 'USD').strip().upper()
                tc_row = row.get('TC') or row.get('Tipo de Cambio') or 1.0
                
                # Obtener moneda de la venta (con cache)
                if id_v not in cache_monedas:
                    v = self.obtener_venta_por_id(id_v)
                    cache_monedas[id_v] = v.get('moneda', 'USD') if v else 'USD'
                
                moneda_venta = cache_monedas[id_v]
                
                # Conversión
                tasa_cambio = float(tc_row) if moneda_pago != moneda_venta else 1.0
                monto_equivalente = round(monto / tasa_cambio, 2) if moneda_pago != moneda_venta else monto
                
                pago_data = {
                    "id_venta": id_v,
                    "fecha_pago": str(row.get('Fecha') or date.today()),
                    "monto_pagado": monto,
                    "moneda": moneda_pago,
                    "metodo_pago": str(row.get('Metodo') or 'TRANSFERENCIA').strip().upper(),
                    "tipo_pago": str(row.get('Tipo') or 'ABONO').strip().upper(),
                    "tipo_comprobante": str(row.get('Comprobante') or 'RECIBO').strip().upper(),
                    "tasa_cambio": tasa_cambio,
                    "monto_moneda_venta": monto_equivalente
                }
                
                # Validaciones de enums
                if pago_data['moneda'] not in ['USD', 'PEN', 'EUR']: pago_data['moneda'] = 'USD'
                if pago_data['metodo_pago'] not in ['EFECTIVO', 'TRANSFERENCIA', 'TARJETA', 'PAYPAL', 'YAPE', 'PLIN', 'OTRO']: pago_data['metodo_pago'] = 'TRANSFERENCIA'
                if pago_data['tipo_pago'] not in ['ADELANTO', 'SALDO', 'TOTAL', 'PARCIAL', 'REEMBOLSO']: pago_data['tipo_pago'] = 'PARCIAL'
                if pago_data['tipo_comprobante'] not in ['BOLETA', 'FACTURA', 'RECIBO', 'RECIBO SIMPLE', 'SIN_COMPROBANTE']: pago_data['tipo_comprobante'] = 'RECIBO'
                
                self.client.table('pago').insert(pago_data).execute()
                exitos += 1
                
            except Exception as e:
                errores.append(f"Fila {idx+2}: {str(e)}")
        
        return {"exitos": exitos, "errores": errores}
