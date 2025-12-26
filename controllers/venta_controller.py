# controllers/venta_controller.py

from ..models.venta_model import VentaModel
from .lead_controller import LeadController # Necesario para actualizar el Lead

class VentaController:
    """Controlador para manejar la lógica de negocio de las Ventas."""
    
    def __init__(self):
        self.venta_model = VentaModel()
        self.lead_controller = LeadController() # Usamos el LeadController para actualizar el estado

    def registrar_nueva_venta(self, lead_id, monto_total, tour_paquete, fecha_tour, vendedor):
        """
        Registra una venta y marca el Lead asociado como 'Convertido'.
        """
        
        # 1. Validación simple
        if not monto_total or not tour_paquete:
            return False, "Monto y nombre del Tour son obligatorios para la venta."
            
        # 2. Registrar la venta
        venta_id = self.venta_model.create_venta(
            lead_id, 
            monto_total, 
            tour_paquete, 
            fecha_tour, 
            vendedor
        )

        if venta_id:
            # 3. Marcar el Lead como Convertido (¡El paso clave!)
            exito_lead, mensaje_lead = self.lead_controller.actualizar_estado_lead(
                lead_id, 
                "Convertido (Vendido)"
            )
            
            if exito_lead:
                return True, f"Venta registrada (ID: {venta_id}) y Lead ID {lead_id} marcado como vendido."
            else:
                return True, f"Venta registrada (ID: {venta_id}), pero falló la actualización del estado del Lead."
        else:
            return False, "Error desconocido al registrar la Venta."