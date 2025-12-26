# models/venta_model.py
from .base_model import BaseModel

class VentaModel(BaseModel):
    def __init__(self):
        super().__init__()

    def insert_new_sale(self, datos: dict, documentos_url: str):
        """ Simula el registro de una nueva venta (como registrarVenta en .gs) """
        # Aquí se insertaría la fila en la tabla 'Ventas'
        print(f"MODEL: Insertando nueva Venta para {datos.get('nombre')}")
        print(f"MODEL: URL de documentos (Drive/Storage): {documentos_url}")
        return {"status": "success", "venta_id": 101}