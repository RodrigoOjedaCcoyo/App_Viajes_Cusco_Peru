# test_supabase.py
import toml
from supabase import create_client, Client

print("--- INICIANDO TEST DE CONEXIÓN SUPABASE ---")

try:
    # 1. Cargar Credenciales
    print("1. Leyendo secrets.toml...")
    secrets = toml.load(".streamlit/secrets.toml")
    url = secrets["supabase"]["URL"]
    key = secrets["supabase"]["ANON_KEY"]
    
    # Validar formato visualmente
    print(f"   URL detectada: {url}")
    print(f"   KEY detectada (primeros 10 caracteres): {key[:10]}...")
    
    if "sb_publishable" in key:
        print("   ⚠️ ADVERTENCIA: La clave empieza con 'sb_publishable'. Normalmente las claves de Supabase ('anon') empiezan con 'eyJh...' (son tokens JWT).")
        print("   -> Verifica si copiaste la clave correcta en Supabase > Project Settings > API > anon public.")

    # 2. Inicializar Cliente
    print("\n2. Conectando con Supabase...")
    supabase: Client = create_client(url, key)
    
    # 3. Prueba de Acceso a Datos (Tabla Pública)
    print("3. Intentando leer tabla 'lugar' (prueba de lectura pública)...")
    response = supabase.table('lugar').select("*").limit(1).execute()
    
    print("\n✅ ¡CONEXIÓN EXITOSA!")
    print(f"   Se pudieron leer datos. La URL y la API KEY son correctas.")
    print(f"   Datos recibidos: {response.data}")
    
    print("\n--- CONCLUSIÓN ---")
    print("Si este test pasó, el problema NO es Supabase ni tu conexión.")
    print("El error 'Invalid login credentials' se debe casi seguro a:")
    print("   a) El usuario no existe en ESTE proyecto nuevo.")
    print("   b) El email no ha sido confirmado (Revisa tu bandeja de spam o desactiva 'Confirm Email' en Supabase).")
    print("   c) Contraseña incorrecta.")

except Exception as e:
    print(f"\n❌ ERROR DE CONEXIÓN:")
    print(f"   {e}")
    print("\n--- DIAGNÓSTICO ---")
    print("Si el error menciona 'key', 'token' o '401', tu API KEY en secrets.toml está mal.")
    print("Si el error menciona 'Name or service not known', tu URL en secrets.toml está mal.")
