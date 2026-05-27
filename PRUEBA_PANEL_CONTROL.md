# ✅ Guía de Prueba - Panel de Control de Operaciones

## Problema Resuelto
El panel de control no cargaba ni guardaba archivos en la base de datos debido a:
- Variables de sesión no inicializadas
- Falta de validación previa antes de procesar
- Manejo insuficiente de errores

## Cambios Realizados

### 1. **Inicialización de Sesión** (`page_operaciones.py` línea ~1075)
```python
if 'last_loaded_id_venta' not in st.session_state:
    st.session_state['last_loaded_id_venta'] = None
if 'master_pax_count' not in st.session_state:
    st.session_state['master_pax_count'] = 1
```

### 2. **Validación Previa de Venta** (línea ~1340)
Antes de mostrar los uploader, ahora se valida que existe una venta seleccionada:
```python
id_venta_para_archivos = st.session_state.get('last_loaded_id_venta')
if not id_venta_para_archivos:
    # Mostrar advertencia y retornar
    return
```

### 3. **Mejor Feedback en Errores**
- Si `exitos = 0` pero no hay errores → Mensaje específico
- Si hay errores → Se muestran todos en expander
- Validación de estructura de respuesta

### 4. **Logging de Debug**
- `print()` agregados en puntos críticos
- Útil para diagnosticar problemas en los logs de Streamlit

---

## 📋 Pasos de Prueba

### Paso 1: Seleccionar Venta
1. Ve al módulo "OPERACIONES" → "Panel de Control Profesional"
2. En los selectbox superiores:
   - Selecciona tipo de venta (B2B o B2C)
   - Selecciona la agencia o ventas directas
   - **Selecciona una venta específica**

**Esperado:** Se debe establecer `last_loaded_id_venta` en sesión.

### Paso 2: Cargar Archivo de Endoses
1. Descarga la plantilla "📥 Descargar Plantilla Inteligente (Excel)"
2. Completa con datos de ejemplo:
   | Dia | Tipo de Servicio | Proveedor | Costo Unitario | Pax | Moneda |
   |-----|-----------------|-----------|---|---|---|
   | 1 | ENDOSE | CONSETTUR | 50 | 2 | USD |
   | 2 | GUIA | [Tu Proveedor] | 100 | 2 | USD |

3. Sube el archivo en "Cierre de Operaciones (Excel/CSV):"
4. Verifica que:
   - ✅ Se detecten las columnas correctamente
   - ✅ Se muestre previsualización
   - ✅ Se vea el input del Tipo de Cambio

5. Haz clic en "📦 Procesar y Guardar Endoses en DB"

**Esperado:** 
- Spinner mientras procesa
- ✅ Mensaje de éxito si se guardaron registros
- ⚠️ Advertencias específicas si hay filas con problemas
- 🎉 Globos si todo fue exitoso

### Paso 3: Cargar Pasajeros
1. Descarga plantilla "📥 Descargar Plantilla Rooming"
2. Completa con pasajeros:
   | Nombre | Apellidos | Documento | Tipo Doc | ... |
   |---|---|---|---|---|
   | Juan | Pérez | 12345678 | DNI | ... |

3. Sube en "Lista de Pasajeros / Rooming (Excel/CSV):"
4. Haz clic en "👥 Cargar Rooming a la DB"

**Esperado:**
- ✅ Mensaje de éxito con cantidad de pasajeros cargados
- ⚠️ Warnings específicas si hay filas con errores

---

## 🔍 Validaciones Internas

### Si NO seleccionas venta:
- Ambas columnas mostrarán: "⚠️ Selecciona una venta arriba para..."
- No será posible cargar archivos

### Si el archivo tiene columnas incorrectas:
- Error: "❌ No se encontraron todas las columnas requeridas"
- Se muestran las columnas esperadas vs detectadas
- Se sugiere descargar la plantilla

### Si la venta NO tiene itinerario sincronizado:
- Error: "❌ No se encontró itinerario sincronizado"
- Solución: Sincroniza el itinerario primero

### Si un proveedor no existe:
- Advertencia: "Proveedor 'XXXX' no encontrado. Disponibles: ..."
- Se listan los proveedores activos

---

## 🛠️ Debugging

Si algo no funciona, revisa los logs:
1. Abre la terminal de Streamlit
2. Busca líneas con `DEBUG -`
3. Estos mostrarán exactamente dónde está el error

Ejemplo:
```
DEBUG - Error en fila 2: ValueError: El Día '1a' no es un número válido.
```

---

## ✨ Mejoras Clave

| Antes | Después |
|---|---|
| Variables de sesión no inicializadas | ✅ Inicializadas al abrir dashboard |
| Error silencioso si no seleccionas venta | ✅ Mensaje claro: "Selecciona una venta" |
| Si `exitos=0` sin errores → sin feedback | ✅ Mensaje: "No se guardó ningún registro. Verifica que..." |
| Errores genéricos | ✅ Errores específicos por fila |
| No había logging | ✅ Logging de debug disponible |

---

## 📞 Próximos Pasos

Si después de estas pruebas aún hay problemas:
1. Verifica que la venta tiene itinerario sincronizado
2. Verifica que existen proveedores activos en el sistema
3. Revisa los logs de Streamlit para mensajes `DEBUG -`
4. Reporta con la línea exacta del log donde falló

