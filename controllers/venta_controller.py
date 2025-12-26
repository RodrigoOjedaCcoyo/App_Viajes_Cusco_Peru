# controllers/venta_controller.py
from models.venta_model import VentaModel
# NOTA: En un futuro, importaremos un servicio de almacenamiento (Drive/S3/Supabase Storage)
# from services.storage_service import StorageService 

class VentaController:
    def __init__(self):
        self.model = VentaModel()
        # self.storage = StorageService() # Inicialización futura

    def registrar_nueva_venta(self, datos: dict, archivos: list):
        """
        Registra la venta y maneja la subida de archivos (simulación del .gs).
        """
        documentos_url = "SIMULACION_DRIVE_FOLDER_URL"
        
        if archivos:
            # En el futuro, aquí iría la lógica de subida real:
            # documentos_url = self.storage.upload_files(archivos, datos)
            print(f"CONTROLADOR: {len(archivos)} archivos recibidos. Subida simulada a: {documentos_url}")
        
        # Llama al modelo para registrar la venta con la URL de los documentos
        return self.model.insert_new_sale(datos, documentos_url)