# register_user.py
import streamlit as st
from supabase import create_client, Client
import toml

# Leer secretos manualmente si no corre vía Streamlit
try:
    secrets = toml.load(".streamlit/secrets.toml")
    URL = secrets["supabase"]["URL"]
    KEY = secrets["supabase"]["ANON_KEY"]
except Exception as e:
    print(f"Error leyendo secrets.toml: {e}")
    exit()

supabase: Client = create_client(URL, KEY)

def create_user(email, password):
    print(f"Intentando crear usuario: {email}...")
    try:
        # Intentamos registrar al usuario
        res = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        
        # Verificamos si requiere confirmación por correo
        if res.user and res.user.identities and res.user.identities[0].identity_data:
             print(f"✅ Usuario creado EXITOSAMENTE: {res.user.id}")
             print("ℹ️ IMPORTANTE: Si Supabase tiene activado 'Confirm Email', revisa tu bandeja.")
             print("   Si quieres entrar directo, ve al Dashboard -> Auth -> Users y dale a 'Confirm Email' manualmente.")
        else:
             print(f"✅ Usuario creado o ya existía: {res}")

    except Exception as e:
        print(f"❌ Error al crear usuario: {e}")

if __name__ == "__main__":
    print("--- HERRAMIENTA DE CREACIÓN DE USUARIOS ---")
    print("Usando Proyecto URL:", URL)
    
    email = input("Ingrese el correo (ej. ventas@demo.com): ")
    password = input("Ingrese la contraseña: ")
    
    if email and password:
        create_user(email, password)
    else:
        print("Datos incompletos.")
