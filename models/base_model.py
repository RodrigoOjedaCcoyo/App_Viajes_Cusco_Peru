# models/base_model.py

class BaseModel:
    """
    Clase base para manejar la conexión a Supabase.
    Por ahora, solo simula el estado de la conexión.
    """
    def __init__(self):
        # Aquí se inicializaría la conexión a Supabase en el futuro
        print("BaseModel inicializado. Conexión pendiente.")

    def get_db_client(self):
        # En el futuro, devolvería el cliente Supabase
        # Por ahora, devolvemos un objeto de simulación
        return "SimulacionDBClient"