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
                                monto: float, moneda: str, tasa_cambio: float, 
                                monto_equivalente: float, fecha: str, metodo: str, 
                                voucher_url: str = None, notas: str = "", id_usuario: int = None):
        """Prepara y registra un pago a proveedor con inteligencia multimoneda."""
        data = {
            "id_proveedor": id_proveedor,
            "id_venta": id_venta,
            "n_linea": n_linea,
            "monto_pagado": monto,
            "moneda": moneda,
            "tasa_cambio": tasa_cambio,
            "monto_en_moneda_costo": monto_equivalente,
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
            monto_str = f"{p['moneda']} {p['monto_pagado']:,.2f}"
            if p.get('tasa_cambio', 1.0) != 1.0:
                monto_str += f" (TC: {p['tasa_cambio']})"
                
            flat_data.append({
                "ID": p['id_pago_op'],
                "Fecha": p['fecha_pago'],
                "Monto": monto_str,
                "Abono a Deuda": p.get('monto_en_moneda_costo', p['monto_pagado']),
                "Método": p['metodo_pago'],
                "Tour/Venta": v_info.get('tour_nombre', 'Varios/General'),
                "Notas": p['observaciones']
            })
        return pd.DataFrame(flat_data)

    def obtener_resumen_saldos_proveedores(self):
        """
        Calcula balances: COSTOS (Deuda) vs PAGOS (Amortización en moneda de deuda).
        Optimizado para evitar consultas N+1.
        """
        try:
            # 1. Obtener todos los costos registrados (Lo que debemos)
            # Incluimos id_venta y n_linea para usarlos de llave en la vinculación de pagos
            res_costos = self.client.table('venta_servicio_proveedor')\
                .select('id_venta, n_linea, id_proveedor, costo_unitario, cantidad_pax, moneda, proveedor(nombre_comercial)')\
                .execute()
            
            # 2. Obtener todos los pagos realizados (Lo que amortizamos)
            res_pagos = self.client.table('pago_operativo')\
                .select('id_proveedor, monto_en_moneda_costo, moneda, id_venta, n_linea')\
                .execute()

            balances = {}
            mapa_monedas_servicios = {} # (id_v, nl) -> moneda
            
            # Cargar costos y construir mapa de monedas
            for c in res_costos.data:
                pid = c['id_proveedor']
                p_nom = c['proveedor']['nombre_comercial'] if c.get('proveedor') else "Desconocido"
                moneda_deuda = c['moneda'] # La moneda en la que se pactó el costo
                total_costo = float(c['costo_unitario'] or 0) * int(c['cantidad_pax'] or 1)
                
                # Guardar moneda para el lookup de pagos posterior
                if c.get('id_venta') and c.get('n_linea'):
                    mapa_monedas_servicios[(c['id_venta'], c['n_linea'])] = moneda_deuda

                key = (pid, p_nom, moneda_deuda)
                if key not in balances: balances[key] = {"debe": 0.0, "pagado": 0.0}
                balances[key]["debe"] += total_costo

            # Cargar pagos (amortizaciones en la moneda de la deuda)
            for p in res_pagos.data:
                pid = p['id_proveedor']
                id_v = p.get('id_venta')
                nl = p.get('n_linea')
                
                # Determinar la moneda de la deuda que este pago amortiza (USAR CACHE EN MEMORIA)
                moneda_amortizada = p['moneda'] # Default
                if id_v and nl:
                    # Lookup instantáneo en memoria sin ir a la DB
                    moneda_amortizada = mapa_monedas_servicios.get((id_v, nl), p['moneda'])
                
                monto_abono = float(p.get('monto_en_moneda_costo') or p['monto_pagado'] or 0)
                
                # Buscar en balances o crear
                key = None
                for k in balances.keys():
                    if k[0] == pid and k[2] == moneda_amortizada:
                        key = k
                        break
                
                if key:
                    balances[key]["pagado"] += monto_abono
                else:
                    # Pago sin costo previo detectado en esa moneda o pago general
                    # Solo buscamos el nombre del proveedor si no lo tenemos ya en otro balance
                    p_nom = "Desconocido"
                    for k in balances.keys(): 
                        if k[0] == pid: 
                            p_nom = k[1]
                            break
                    
                    if p_nom == "Desconocido":
                        res_prov = self.client.table('proveedor').select('nombre_comercial').eq('id_proveedor', pid).single().execute()
                        p_nom = res_prov.data['nombre_comercial'] if res_prov.data else "Desconocido"
                    
                    key = (pid, p_nom, moneda_amortizada)
                    if key not in balances:
                        balances[key] = {"debe": 0.0, "pagado": monto_abono}
                    else:
                        balances[key]["pagado"] += monto_abono

            # Convertir a lista para UI
            reporte = []
            for (pid, p_nom, moneda), data in balances.items():
                saldo = data["debe"] - data["pagado"]
                # Solo mostrar si hay algo pendiente o abonado (evitar filas vacías 0/0)
                if abs(data["debe"]) > 0.01 or abs(data["pagado"]) > 0.01:
                    reporte.append({
                        "Proveedor": p_nom,
                        "Moneda": moneda if moneda and str(moneda) != 'nan' else 'PEN',
                        "Total Costos": round(data["debe"], 2),
                        "Abonado": round(data["pagado"], 2),
                        "Saldo Pendiente": round(saldo, 2)
                    })
            
            return pd.DataFrame(reporte)
        except Exception as e:
            print(f"Error generando reporte de saldos: {e}")
            return pd.DataFrame()
