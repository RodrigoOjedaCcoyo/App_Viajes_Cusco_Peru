import os

def search_text(directory, text):
    for root, dirs, files in os.walk(directory):
        if '.git' in root or '__pycache__' in root:
            continue
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        for i, line in enumerate(lines):
                            if text.lower() in line.lower():
                                print(f"Found in {path} at line {i+1}: {line.strip()}")
                except Exception as e:
                    pass

search_text(r'd:\App_Viaje_Cusco\App_Viajes_Cusco_Peru', 'Canal de Venta')
search_text(r'd:\App_Viaje_Cusco\App_Viajes_Cusco_Peru', 'Estrategia de Venta')
search_text(r'd:\App_Viaje_Cusco\App_Viajes_Cusco_Peru', 'Fuente del Lead')
