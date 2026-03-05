# controllers/pago_operativo_controller.py
from models.pago_operativo_model import PagoOperativoModel
from supabase import Client
from typing import Dict, Any, List
import pandas as pd

class PagoOperativoController:
    """Controlador para la gestión de Pagos Operativos (Egresos a Proveedores)."""

    def __init__(self, supabase_client: Client):
        self.client = supabase_client
        self.model = PagoOperativoModel(supabase_client)

    def registrar_pago_operativo(self, id_proveedor: int, id_venta: int, n_linea: int, 
                                monto: float, moneda: str, fecha: str, metodo: str, 
                                voucher_url: str = None, notas: str = "", id_usuario: int = None):
        """Prepara y registra un pago a proveedor."""
        data = {
            "id_proveedor": id_proveedor,
            "id_venta": id_venta,
            "n_linea": n_linea,
            "monto_pagado": monto,
            "moneda": moneda,
            "fecha_pago": fecha,
            "metodo_pago": metodo,
            "comprobante_url": voucher_url,
            "observaciones": notas,
            "id_usuario_registro": id_usuario
        }
        return self.model.registrar_pago(data)

    def obtener_historial_pagos_proveedor(self, id_proveedor: int):
        """Retorna un DataFrame con el historial de pagos a un proveedor."""
        pagos = self.model.obtener_pagos_por_proveedor(id_proveedor)
        if not pagos:
            return pd.DataFrame()
        
        # Aplanar para el DataFrame
        flat_data = []
        for p in pagos:
            v_info = p.get('venta') or {}
            flat_data.append({
                "ID": p['id_pago_op'],
                "Fecha": p['fecha_pago'],
                "Monto": p['monto_pagado'],
                "Moneda": p['moneda'],
                "Método": p['metodo_pago'],
                "Tour/Venta": v_info.get('tour_nombre', 'Varios/General'),
                "Notas": p['observaciones']
            })
        return pd.DataFrame(flat_data)

    def obtener_resumen_saldos_proveedores(self):
        """
        Lógica compleja: Compara VENTAS_SERVICIO_PROVEEDOR (Costo) 
        vs PAGO_OPERATIVO (Pagado) para ver cuánto se debe.
        """
        try:
            # 1. Obtener todos los costos registrados (Lo que debemos)
            res_costos = self.client.table('venta_servicio_proveedor')\
                .select('id_proveedor, costo_unitario, cantidad_pax, moneda, proveedor(nombre_comercial)')\
                .execute()
            
            # 2. Obtener todos los pagos realizados (Lo que pagamos)
            res_pagos = self.client.table('pago_operativo')\
                .select('id_proveedor, monto_pagado, moneda')\
                .execute()

            # Procesar balances (esto es una versión simplificada, ideal por moneda)
            balances = {}
            
            for c in res_costos.data:
                pid = c['id_proveedor']
                p_nom = c['proveedor']['nombre_comercial'] if c.get('proveedor') else "Desconocido"
                moneda = c['moneda']
                total_costo = float(c['costo_unitario'] or 0) * int(c['cantidad_pax'] or 1)
                
                key = (pid, p_nom, moneda)
                if key not in balances: balances[key] = {"debe": 0.0, "pagado": 0.0}
                balances[key]["debe"] += total_costo

            for p in res_pagos.data:
                pid = p['id_proveedor']
                # Buscar nombre si no está en costos
                moneda = p['moneda']
                monto = float(p['monto_pagado'] or 0)
                
                # Buscar en balances o crear
                found = False
                for k in balances.keys():
                    if k[0] == pid and k[2] == moneda:
                        balances[k]["pagado"] += monto
                        found = True
                        break
                
                if not found:
                    # Pago sin costo previo detectado (adelanto o error)
                    res_prov = self.client.table('proveedor').select('nombre_comercial').eq('id_proveedor', pid).single().execute()
                    p_nom = res_prov.data['nombre_comercial'] if res_prov.data else "Desconocido"
                    key = (pid, p_nom, moneda)
                    balances[key] = {"debe": 0.0, "pagado": monto}

            # Convertir a lista para UI
            reporte = []
            for (pid, p_nom, moneda), data in balances.items():
                saldo = data["debe"] - data["pagado"]
                reporte.append({
                    "Proveedor": p_nom,
                    "Moneda": moneda,
                    "Total Costos": data["debe"],
                    "Total Pagado": data["pagado"],
                    "Saldo Pendiente": saldo
                })
            
            return pd.DataFrame(reporte)
        except Exception as e:
            print(f"Error generando reporte de saldos: {e}")
            return pd.DataFrame()
