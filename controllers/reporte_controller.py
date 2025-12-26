# controllers/reporte_controller.py
from models.venta_model import VentaModel
from models.lead_model import LeadModel

class ReporteController:
    """
    Controlador encargado de obtener datos agregados y reportes
    para las áreas de Gerencia y Contabilidad.
    """
    
    def __init__(self):
        self.venta_model = VentaModel()
        self.lead_model = LeadModel()
        
    def obtener_resumen_ventas(self):
        """Devuelve todas las ventas con información clave para reportes."""
        
        # 1. Obtener los datos sin procesar
        todas_las_ventas = self.venta_model.get_all()
        
        # 2. Calcular métricas clave
        total_ventas = len(todas_las_ventas)
        monto_total_usd = sum(v['monto_total'] for v in todas_las_ventas)
        
        # 3. Formatear la salida
        resumen = {
            "total_ventas_registradas": total_ventas,
            "monto_total_acumulado": monto_total_usd,
            "detalle_ventas": todas_las_ventas
        }
        return resumen

    def obtener_detalle_auditoria(self):
        """
        Devuelve una lista combinada de Leads y Ventas para auditoría 
        (ejemplo simple, en una DB real sería un JOIN).
        """
        ventas = self.venta_model.get_all()
        
        # En una auditoría real, buscarías el Lead asociado, pero por ahora 
        # devolvemos el detalle de ventas directamente.
        
        return ventas