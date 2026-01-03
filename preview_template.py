import os
from jinja2 import Environment, FileSystemLoader

# Configuración
template_dir = r"c:\Viajes_Cusco_Peru\App_Viajes_Cusco_Peru\templates"
env = Environment(loader=FileSystemLoader(template_dir))

# Mock Data
datos_render = {
    "cliente_nombre": "Juan Pérez",
    "fecha_viaje": "15/01/2026",
    "num_adultos": 2,
    "num_ninos": 1,
    "origen": "Facebook Ads",
    "itinerario": [
        {"nombre": "Recojo del Aeropuerto", "descripcion": "Traslado privado al hotel en Cusco.", "notas_operativas": "Esperar con cartel de la empresa."},
        {"nombre": "City Tour Cusco", "descripcion": "Visita a la Catedral, Qoricancha y ruinas aledañas.", "notas_operativas": "Incluye entradas."},
        {"nombre": "Machu Picchu Full Day", "descripcion": "Viaje en tren Vistadome y visita a la ciudadela.", "notas_operativas": "Almuerzo en Aguas Calientes incluido."}
    ],
    "total": 1250.50
}

# Renderizar
template = env.get_template('itinerario_template.html')
html_out = template.render(datos_render)

# Guardar vista previa
preview_path = os.path.join(template_dir, 'preview.html')
with open(preview_path, 'w', encoding='utf-8') as f:
    f.write(html_out)

print(f"Vista previa generada en: {preview_path}")
