# controllers/venta_controller.py
from models.venta_model import VentaModel
from models.lead_model import LeadModel 

class VentaController:
    """Controlador para manejar la lógica de negocio de las Ventas."""
    
    def __init__(self):
        self.venta_model = VentaModel()
        self.lead_model = LeadModel() 
        
    def registrar_nueva_venta(self, lead_id, monto_total, tour_paquete, fecha_tour, vendedor):
        """
        Registra la venta y marca el lead asociado como 'Convertido'.
        """
        
        # 1. Validación de Datos (Controlador)
        if not lead_id or monto_total <= 0:
            return False, "ID de Lead y Monto Total deben ser válidos y mayores que cero."
            
        # 2. Creación de la Venta (Llama al VentaModel)
        new_id = self.venta_model.create_venta(
            lead_id, 
            monto_total, 
            tour_paquete, 
            fecha_tour, 
            vendedor
        )
        
        # 3. Actualizar el estado del Lead (Llama al LeadModel)
        if new_id:
            try:
                leads = self.lead_model.get_all()
                for lead in leads:
                    # Busca el lead y actualiza su estado
                    if lead.get('id') == lead_id:
                        lead['estado'] = 'Convertido (Venta ID: ' + str(new_id) + ')'
                        break
            except Exception as e:
                # La venta se creó, pero la actualización del lead falló
                print(f"Advertencia: No se pudo actualizar el lead {lead_id}: {e}")
                
            return True, f"Venta registrada con éxito. Venta ID: {new_id}. Lead actualizado."
        else:
            return False, "Error desconocido al registrar la Venta."