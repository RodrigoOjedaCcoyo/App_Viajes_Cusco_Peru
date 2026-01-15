
import sys
import os

# Add current directory to path
sys.path.append('c:\\Itinerario')

from App_Ventas import generar_pdf_web
from datos_tours import tours_db

# Mock data
tours = [t for t in tours_db if t['titulo'] == "RECEPCIÓN Y CITY TOUR CUSCO IMPERIAL"]
pasajero = "Cliente De Prueba"
fechas = "12/01 - 15/01"
categoria = "Standard"
modo = "Privado"
vendedor = "Antigravity"
celular = "999-999-999"

print("Generating PDF...")
try:
    pdf_path = generar_pdf_web(tours, pasajero, fechas, categoria, modo, vendedor, celular)
    print(f"PDF Generated successfully at: {pdf_path}")
except Exception as e:
    print(f"Error generating PDF: {e}")
