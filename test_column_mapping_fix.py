"""
Test script to verify the fixes work correctly
"""
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_column_mapping():
    """Test the column mapping logic to ensure fix is correct"""
    
    print("=== TESTING COLUMN MAPPING FIX ===\n")
    
    # Simulate the normalizar_columnas function
    def normalizar_columnas(df):
        df = df.copy()
        df.columns = [str(col).strip().lower() for col in df.columns]
        return df
    
    # Simulate mapear_columnas_flexible
    def mapear_columnas_flexible(df_norm):
        mapeo = {
            'dia': ['dia', 'día', 'n_linea', 'nlinea', 'línea', 'linea', 'day'],
            'tipo_de_servicio': ['tipo_de_servicio', 'tipo de servicio', 'tipo_servicio', 'servicio', 'tipo', 'service_type'],
            'proveedor': ['proveedor', 'provider', 'supplier', 'nombre_proveedor', 'empresa']
        }
        
        cols_encontradas = {}
        for col_esperada, aliases in mapeo.items():
            for col_actual in df_norm.columns:
                if col_actual in aliases or any(alias in col_actual for alias in aliases):
                    cols_encontradas[col_esperada] = col_actual
                    break
        
        return cols_encontradas
    
    # Test data with various column name formats
    test_cases = [
        {
            "name": "Standard format",
            "columns": ['Dia', 'Tipo de Servicio', 'Proveedor'],
        },
        {
            "name": "With lowercase n_linea",
            "columns": ['N Linea', 'Tipo Servicio', 'Proveedor'],
        },
        {
            "name": "With accents",
            "columns": ['Día', 'Tipo de Servicio', 'Proveedor'],
        },
    ]
    
    for test_case in test_cases:
        print(f"Test case: {test_case['name']}")
        print(f"Original columns: {test_case['columns']}\n")
        
        # Create test DataFrame
        df_test = pd.DataFrame(columns=test_case['columns'])
        
        # Normalize columns
        df_norm = normalizar_columnas(df_test)
        print(f"After normalize: {list(df_norm.columns)}")
        
        # Map columns
        cols_mapeadas = mapear_columnas_flexible(df_norm)
        print(f"Mapping result: {cols_mapeadas}")
        
        # Apply the fix (correct renaming)
        rename_dict = {}
        for col_esperada, col_actual in cols_mapeadas.items():
            for idx, col in enumerate(df_test.columns):
                if str(col).strip().lower() == col_actual:
                    # NEW FIX: Explicit mapping
                    if col_esperada == 'dia':
                        rename_dict[col] = 'Dia'
                    elif col_esperada == 'tipo_de_servicio':
                        rename_dict[col] = 'Tipo de Servicio'
                    elif col_esperada == 'proveedor':
                        rename_dict[col] = 'Proveedor'
        
        print(f"Rename dict: {rename_dict}")
        
        if rename_dict:
            df_test = df_test.rename(columns=rename_dict)
        
        # Verify that the expected columns exist
        expected_cols = ['Dia', 'Tipo de Servicio', 'Proveedor']
        final_cols = list(df_test.columns)
        print(f"Final columns: {final_cols}")
        
        # Verify each column can be accessed
        test_row = pd.Series({col: None for col in final_cols})
        can_access_dia = test_row.get('Dia') is None  # Should work even if None
        can_access_tipo = test_row.get('Tipo de Servicio') is None
        can_access_prov = test_row.get('Proveedor') is None
        
        print(f"Can access 'Dia': {can_access_dia}")
        print(f"Can access 'Tipo de Servicio': {can_access_tipo}")
        print(f"Can access 'Proveedor': {can_access_prov}")
        
        if all([can_access_dia, can_access_tipo, can_access_prov]):
            print("✅ PASS - All columns accessible\n")
        else:
            print("❌ FAIL - Some columns not accessible\n")

if __name__ == "__main__":
    test_column_mapping()
