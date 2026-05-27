"""
Debug script para identificar por qué la carga de plantilla no guarda en BD
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from supabase import create_client, Client
import pandas as pd
from dotenv import load_dotenv
import streamlit as st

# Cargar credenciales
load_dotenv()
try:
    SUPABASE_URL = st.secrets["supabase"]["URL"]
    SUPABASE_ANON_KEY = st.secrets["supabase"]["ANON_KEY"]
except:
    print("⚠️ No st.secrets encontrado, intentando con variables de entorno")
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    print("❌ Credenciales de Supabase no encontradas")
    sys.exit(1)

client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

def debug_upload_flow():
    """Simula el flujo de carga de plantilla y detecta dónde falla"""
    
    print("\n=== INICIO DE DEBUG ===\n")
    
    # 1. Obtener una venta de ejemplo
    print("1️⃣  Buscando una venta para prueba...")
    try:
        res_v = client.table('venta').select('id_venta, moneda').limit(1).execute()
        if not res_v.data:
            print("❌ No hay ventas en la base de datos")
            return
        
        venta_test = res_v.data[0]
        id_venta_test = venta_test['id_venta']
        print(f"✅ Venta encontrada: ID={id_venta_test}, Moneda={venta_test.get('moneda', 'N/A')}")
    except Exception as e:
        print(f"❌ Error al obtener ventas: {e}")
        return
    
    # 2. Verificar que tenga servicios (venta_tour)
    print("\n2️⃣  Verificando servicios de la venta...")
    try:
        res_s = client.table('venta_tour').select('n_linea, id_itinerario_dia_index').eq('id_venta', id_venta_test).execute()
        servicios = res_s.data or []
        
        if not servicios:
            print(f"❌ La venta ID={id_venta_test} NO TIENE servicios (venta_tour)")
            print("   Esto es CRÍTICO - la plantilla no puede procesarse sin itinerario sincronizado")
            return
        
        print(f"✅ Servicios encontrados: {len(servicios)} líneas")
        for s in servicios[:3]:  # Mostrar primeras 3
            print(f"   - Línea: {s.get('n_linea')}, Día: {s.get('id_itinerario_dia_index')}")
    except Exception as e:
        print(f"❌ Error al obtener servicios: {e}")
        return
    
    # 3. Verificar proveedores activos
    print("\n3️⃣  Verificando proveedores activos...")
    try:
        res_p = client.table('proveedor').select('id_proveedor, nombre_comercial').eq('activo', True).execute()
        proveedores = res_p.data or []
        
        if not proveedores:
            print("❌ NO HAY PROVEEDORES ACTIVOS en el sistema")
            print("   Esto impide procesar cualquier plantilla")
            return
        
        print(f"✅ Proveedores activos: {len(proveedores)}")
        for p in proveedores[:3]:
            print(f"   - {p['nombre_comercial']}")
    except Exception as e:
        print(f"❌ Error al obtener proveedores: {e}")
        return
    
    # 4. Intentar insertar un registro de prueba
    print("\n4️⃣  Intentando INSERTAR registro de prueba...")
    try:
        test_data = {
            "id_venta": id_venta_test,
            "n_linea": servicios[0]['n_linea'],
            "id_proveedor": proveedores[0]['id_proveedor'],
            "tipo_servicio": "PRUEBA_DEBUG",
            "costo_unitario": 50.00,
            "moneda": "USD",
            "cantidad_pax": 2,
            "tipo_cambio": 3.80
        }
        
        print(f"   Datos de prueba: {test_data}")
        
        res_insert = client.table('venta_servicio_proveedor').insert(test_data).execute()
        
        # Verificar si la respuesta tiene datos o errores
        if hasattr(res_insert, 'data') and res_insert.data:
            print(f"✅ INSERT EXITOSO! ID del registro: {res_insert.data[0].get('id', 'N/A')}")
            
            # Limpiar: borrar el registro de prueba
            try:
                client.table('venta_servicio_proveedor').delete().eq('id_venta', id_venta_test).eq('tipo_servicio', 'PRUEBA_DEBUG').execute()
                print("✅ Registro de prueba eliminado")
            except:
                pass
        else:
            print(f"⚠️  Posible error en INSERT. Respuesta: {res_insert}")
    except Exception as e:
        print(f"❌ ERROR EN INSERT: {type(e).__name__}: {str(e)}")
        # Verificar si es un error de RLS
        if "permission" in str(e).lower() or "denied" in str(e).lower():
            print("\n🚨 PROBABLE CAUSA: Problema de permisos RLS (Row Level Security)")
            print("   Verifica las políticas de RLS en la tabla venta_servicio_proveedor")
        return
    
    # 5. Verificar si el registro se guardó
    print("\n5️⃣  Verificando si los datos se guardaron correctamente...")
    try:
        res_verify = client.table('venta_servicio_proveedor').select('*').eq('id_venta', id_venta_test).limit(5).execute()
        registros = res_verify.data or []
        
        print(f"✅ Registros en venta_servicio_proveedor para venta {id_venta_test}: {len(registros)}")
        for r in registros:
            print(f"   - Línea: {r.get('n_linea')}, Tipo: {r.get('tipo_servicio')}, Costo: {r.get('costo_unitario')}")
    except Exception as e:
        print(f"❌ Error al verificar: {e}")
    
    print("\n=== FIN DE DEBUG ===\n")

if __name__ == "__main__":
    debug_upload_flow()
