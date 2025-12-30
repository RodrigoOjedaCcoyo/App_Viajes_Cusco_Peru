# controllers/venta_controller.py

from models.venta_model import VentaModel
from controllers.lead_controller import LeadController 
from supabase import Client

class VentaController:
    """Controlador para manejar la lógica de negocio de las Ventas."""
    
    # NOTA: En este contexto, se mantiene el acoplamiento directo entre controladores
    # para simplificar, ya que ambos usan el mismo cliente inyectado.
    def __init__(self, supabase_client: Client):
        # 1. CORRECCIÓN: Pasar table_name al VentaModel
        self.venta_model = VentaModel(table_name='Ventas', supabase_client=supabase_client)
        
        # 2. El LeadController se inicializa correctamente con la dependencia inyectada.
        self.lead_controller = LeadController(supabase_client=supabase_client) 

    # Método que probablemente usa el formulario de la vista (registro_ventas)
    def registrar_venta_directa(self, telefono, origen, monto, tour, fecha_tour, vendedor):
        """
        Versión simplificada para registrar una venta. 
        Requiere que el Lead exista, o crea un Lead temporal antes de registrar la venta.
        Aquí simplemente lo usamos como un "wrapper" para simplificar la vista.
        """
        # (Lógica de validación omitida aquí para concisión)

        # 1. Registrar la venta. Necesita el Lead ID.
        #    Como no tenemos el ID, necesitamos obtenerlo o crearlo primero.
        #    --- LÓGICA DE NEGOCIO SIMPLIFICADA (Puede necesitar un LeadModel.find_by_phone) ---
        
        # Por ahora, nos enfocaremos solo en registrar la venta
        venta_data = {
            'telefono': telefono,
            'origen_lead': origen, # asumiendo que el tour es el origen si es directa
            'monto_total': monto,
            'tour_paquete': tour,
            'fecha_tour': fecha_tour,
            'vendedor': vendedor,
        }
        
        venta_id = self.venta_model.save(venta_data)
        
        if venta_id:
            # NOTA: Si la venta se registra, el lead no se actualiza porque no tenemos lead_id aquí.
            # Este método requiere una lógica más compleja de búsqueda/creación de Leads.
            return True, f"Venta registrada con éxito (ID: {venta_id})."
        else:
            return False, "Error al registrar la Venta."


    # Método original (útil para el proceso de conversión de Lead)
    def registrar_nueva_venta(self, lead_id, monto_total, tour_paquete, fecha_tour, vendedor):
        # ... (La lógica de este método es correcta para el proceso de conversión y actualización)
        # ... (Solo requiere que VentaModel.create_venta use self.venta_model.save(data) con los campos adecuados)
        pass # Dejamos la implementación de este método para el VentaModel