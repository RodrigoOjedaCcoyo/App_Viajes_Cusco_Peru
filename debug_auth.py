# debug_auth.py
import toml
from supabase import create_client, Client
import sys

# Forzar codificación UTF-8 para evitar errores en Windows
sys.stdout.reconfigure(encoding='utf-8')

print("=== DIAGNÓSTICO DE AUTENTICACIÓN SUPABASE ===\n")

try:
    # 1. Cargar Secretos
    print("[1] Cargando secrets.toml...")
    secrets = toml.load(".streamlit/secrets.toml")
    url = secrets["supabase"]["URL"]
    key = secrets["supabase"]["ANON_KEY"]
    print(f"    URL: {url}")
    print("    Secretos cargados correctamente.\n")

    # 2. Inicializar Cliente
    supabase: Client = create_client(url, key)

    # 3. Solicitar Credenciales
    print("[2] Prueba de Inicio de Sesión Real")
    email = input("    Ingrese el correo del usuario: ").strip()
    password = input("    Ingrese la contraseña: ").strip()

    if not email or not password:
        print("    ❌ Debes ingresar correo y contraseña.")
        sys.exit()

    print(f"\n    Intentando conectar como '{email}'...")
    
    # 4. Intentar Login
    session = supabase.auth.sign_in_with_password({
        "email": email,
        "password": password
    })

    print("\n✅ ¡LOGIN EXITOSO!")
    user = session.user
    print(f"    UUID de Usuario: {user.id}")
    print(f"    Email: {user.email}")
    print("    Estado: Confirmado")

    # 5. Verificar Rol (Vinculación) ya que estamos aquí
    print("\n[3] Verificando Vinculación de Roles (Tu preocupación)")
    
    roles_encontrados = []
    
    # Verificar Vendedor
    res = supabase.table('vendedor_mapeo').select('*').eq('id_supabase_uuid', user.id).execute()
    if res.data: roles_encontrados.append(f"VENDEDOR (ID: {res.data[0]['id_vendedor_int']})")

    # Verificar Operador
    res = supabase.table('operador_mapeo').select('*').eq('id_supabase_uuid', user.id).execute()
    if res.data: roles_encontrados.append(f"OPERADOR (ID: {res.data[0]['id_operador_int']})")
    
    # Verificar Contador
    res = supabase.table('contador_mapeo').select('*').eq('id_supabase_uuid', user.id).execute()
    if res.data: roles_encontrados.append(f"CONTADOR (ID: {res.data[0]['id_contador_int']})")

    # Verificar Gerente
    res = supabase.table('gerente_mapeo').select('*').eq('id_supabase_uuid', user.id).execute()
    if res.data: roles_encontrados.append(f"GERENTE (ID: {res.data[0]['id_gerente_int']})")

    if roles_encontrados:
        print(f"    ✅ El usuario tiene los siguientes roles asignados: {', '.join(roles_encontrados)}")
    else:
        print("    ⚠️  ALERTA: El usuario NO tiene roles vinculados en la base de datos.")
        print("       (Esto explicaría por qué no entra a la app, aunque el login fue exitoso)")

except Exception as e:
    print(f"\n❌ FALLÓ EL LOGIN:")
    print(f"    Error: {str(e)}")
    
    if "Invalid login credentials" in str(e):
        print("\n    🔍 ANÁLISIS:")
        print("    1. El correo NO existe en este proyecto nuevo.")
        print("    2. O la contraseña es incorrecta.")
        print("    3. O el email no ha sido confirmado.")
    elif "Email not confirmed" in str(e):
        print("\n    🔍 ANÁLISIS: ¡El usuario existe pero no ha confirmado su correo!")

input("\nPresiona Enter para salir...")
