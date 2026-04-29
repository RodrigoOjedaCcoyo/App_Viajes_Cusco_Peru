
import pandas as pd

file_path = r"c:\Sistema Viajes Cusco\App_Viajes_Cusco_Peru\NATHALIA SOAVE X8 de FICHA DE CONTROLE DE TOUR PARA GRUPOS.xlsx"

try:
    # Leer las primeras filas para ver la cabecera
    df_head = pd.read_excel(file_path, header=None, nrows=15)
    print("--- ESTRUCTURA DE CABECERA (Primeras 15 filas) ---")
    print(df_head)
    
    # Buscar la tabla de pasajeros
    # Usualmente empieza después de una fila que diga 'Nº' o 'PASAJEROS'
    df_full = pd.read_excel(file_path, header=None)
    for i, row in df_full.iterrows():
        if 'Nº' in row.values or 'APELLIDOS' in str(row.values).upper():
            print(f"\n--- POSIBLE TABLA DE PASAJEROS (Inicia en fila {i+1}) ---")
            print(df_full.iloc[i:i+5]) # Ver las primeras 5 filas de la tabla
            break

    # Ver nombres de las hojas
    xl = pd.ExcelFile(file_path)
    print(f"\n--- HOJAS DEL ARCHIVO ---")
    print(xl.sheet_names)

except Exception as e:
    print(f"Error analizando el archivo: {e}")
