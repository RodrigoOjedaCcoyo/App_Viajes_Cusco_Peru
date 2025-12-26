# controllers/operacion_controller.py
from models.venta_model import VentaModel
from models.lead_model import LeadModel # Para referencia, si se necesitara

class OperacionController:
    """
    Controlador encargado de gestionar las tareas post-venta: 
    programación, estado del tour, y actualización del estado de pago.
    """
    
    def __init__(self):
        self.venta_model = VentaModel()
        
    def obtener_tours_pendientes(self):
        """Devuelve todas las ventas que aún no han sido marcadas como 'Operado'."""
        
        todas_las_ventas = self.venta_model.get_all()
        
        # Filtramos por un estado de operación (podríamos añadir un campo 'estado_tour' en el modelo)
        # Por ahora, asumimos que todas las ventas son 'pendientes' hasta que se actualicen.
        return todas_las_ventas

    def actualizar_estado_tour(self, venta_id, nuevo_estado):
        """Busca la venta y actualiza su estado (simulado)."""
        
        ventas = self.venta_model.get_all()
        
        # Lógica para encontrar y actualizar el registro
        for venta in ventas:
            if venta.get('id') == venta_id:
                # 💡 NOTA: En un sistema real, el modelo tendría un método 'update'
                # Aquí, la actualización directa sobre el objeto en la lista de st.session_state funciona.
                venta['estado_pago'] = nuevo_estado 
                return True, f"Venta ID {venta_id} actualizada a estado: {nuevo_estado}"
                
        return False, f"Venta ID {venta_id} no encontrada."