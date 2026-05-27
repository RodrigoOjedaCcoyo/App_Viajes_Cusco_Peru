# 📋 Guía de Uso: Panel de Control de Operaciones (Upload de Plantilla)

## 🎯 ¿Qué Arreglamos?

El sistema **ahora es más flexible** con:
- ✅ Nombres de columnas con variaciones (mayúsculas, espacios, acentos)
- ✅ Búsqueda inteligente de proveedores
- ✅ Mensajes de error claros y específicos
- ✅ Validación robusta de datos antes de guardar

---

## 📥 Pasos para Cargar la Plantilla

### 1️⃣ **Descarga la Plantilla Inteligente**
- En el Panel de Control, haz clic en **"Descargar Plantilla Inteligente (Excel)"**
- Se descargará: `plantilla_endoses_inteligente.xlsx`

### 2️⃣ **Completa la Plantilla**

**Columnas que DEBES llenar:**

| Columna | Valores Aceptados | Ejemplo | Requerido |
|---------|------------------|---------|-----------|
| **Dia** | Número (1-12 aprox.) | 1, 2, 3... | ✅ SÍ |
| **Tipo de Servicio** | TRANSPORTE, GUIA, TICKETS, ALOJAMIENTO, ALIMENTACION, OTROS | TRANSPORTE | ✅ SÍ |
| **Proveedor** | Nombre exacto del proveedor registrado | MIGUEL PAQARI | ✅ SÍ |
| **Costo Unitario** | Número decimal | 50.50, 100.00 | ⚠️ Opcional |
| **Pax** | Número entero | 4, 5, 10 | ⚠️ Opcional |
| **Moneda** | USD, PEN | USD | ⚠️ Opcional |
| **Hora** | Hora en formato 24h | 08:00, 14:30 | ⚠️ Opcional |
| **Nombre del Guia** | Nombre del guía | Juan García | ⚠️ Opcional |
| **Observacion** | Notas adicionales | Servicio confirmado | ⚠️ Opcional |

---

## 📝 Ejemplo Completo

```
Dia | Tipo de Servicio | Proveedor              | Costo Unitario | Pax | Moneda
----|------------------|------------------------|----------------|-----|-------
1   | TRANSPORTE       | CONSETTUR SUBIDA MAPI  | 50.00          | 4   | USD
1   | GUIA             | MIGUEL PAQARI          | 0.00           | 4   | USD
2   | TRANSPORTE       | CONSETTUR              | 50.00          | 4   | USD
2   | TICKETS          | COSITUC                | 75.00          | 4   | USD
3   | ALOJAMIENTO      | FENIX MACHUPICCHU      | 0.00           | 4   | PEN
3   | ALIMENTACION     | RESTAURANTE            | 45.00          | 4   | USD
```

---

## ✅ Validaciones que Hace el Sistema

### Antes de procesar, verifica:

1. **Archivo no está vacío** → Si sí, muestra error
2. **Columnas requeridas existen** → Detecta variaciones automáticamente
3. **Valores en Dia, Tipo, Proveedor no estén vacíos** → Si no, marca fila
4. **Dia sea un número** → Si es texto, rechaza
5. **Proveedor existe en BD** → Si no, lista alternativos
6. **Tipo de Cambio > 0** → Valida antes de usar en conversión

---

## 🔍 Si Hay Errores

### Mensaje: "❌ No se encontraron todas las columnas requeridas"

**Causa:** El archivo no tiene las columnas esperadas.

**Solución:**
1. Verifica que TU archivo tenga:
   - `Dia` o variación (`Día`, `N Linea`, `Línea`, etc.)
   - `Tipo de Servicio` o variación (`Tipo Servicio`, `Servicio`, etc.)
   - `Proveedor` o variación (`Provider`, `Supplier`, etc.)

2. El sistema te mostrará:
   - ✅ Qué columnas SÍ detectó
   - ❌ Qué columnas FALTAN
   - 📋 Las columnas que tiene tu archivo

### Mensaje: "Proveedor 'XXXX' no encontrado"

**Causa:** El nombre del proveedor no coincide con los registrados.

**Solución:**
- El sistema listará los proveedores disponibles
- Copia el nombre exacto y repite

### Mensaje: "El Día X no existe en el itinerario"

**Causa:** Intentaste cargar datos para un día que no está en el viaje.

**Solución:**
- Verifica que el viaje tenga ese día (ej: viaje de 3 días = días 1, 2, 3)
- Si es incorrecto, cambia el Dia en la plantilla

---

## 💡 Consejos

✅ **Descarga la plantilla predefinida** → Tiene la estructura correcta

✅ **Usa exactamente los mismos nombres de proveedores** → Los de la plantilla en el dropdown

✅ **Completa desde la fila 2 en adelante** → La fila 1 tiene encabezados

✅ **Verifica que no haya filas vacías** → El sistema ignora archivos vacíos

✅ **Si tienes dudas, mira el ejemplo arriba** → Copia el formato

---

## 📊 Después de Cargar

Una vez cargado exitosamente:

1. ✅ Se mostrará: **"Se vincularon X registros correctamente"**
2. ✅ Se verá el resumen de **Hoja de Servicio Maestra**
3. ✅ Los costos se actualizarán automáticamente
4. ✅ Los proveedores quedarán vinculados

---

## 🆘 ¿Aún No Funciona?

**Contacta al equipo técnico con:**
1. El archivo que intentaste cargar
2. El mensaje de error exacto
3. El ID de la venta

---

**Última actualización:** 27/05/2026
**Versión:** 2.0 (Mejorada)
