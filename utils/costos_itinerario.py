# utils/costos_itinerario.py
"""
Llenado automático del Estructurador de Gastos desde el itinerario del Constructor.

Cuando el vendedor elige el proveedor de cada día en el Constructor de Itinerarios, la cotización
guardada (itinerario_digital.datos_render.days[i]) trae:
    dia['id_tour']           -> tour del catálogo
    dia['proveedor']         -> {id_proveedor, nombre, modalidad, ...} ("foto" al momento de cotizar)
    dia['costo_operativo']   -> {PEN: total soles, USD: total dólares, pax_PEN, pax_USD}

Al registrar o sincronizar la venta, estas funciones:
  1. Completan la línea del día en venta_tour (tour, proveedor y marca de endoso).
  2. Crean la línea de costo en venta_servicio_proveedor (una por moneda), SOLO si todavía no
     existe: nunca pisan lo que Operaciones ya cargó o editó a mano.
Si el itinerario es antiguo (sin proveedor), no hacen nada.
"""

from typing import Any, Dict, List, Optional

TIPO_SERVICIO = "ENDOSE"
TIPO_SERVICIO_EXT = "ENDOSE (Ext/CAN)"


def _num(v: Any) -> float:
    try:
        return float(v or 0)
    except (TypeError, ValueError):
        return 0.0


def datos_dia(dia: Dict[str, Any]) -> Dict[str, Any]:
    """Campos extra para venta_tour a partir del día del itinerario (vacío si no hay datos)."""
    extra: Dict[str, Any] = {}
    try:
        id_tour = int(dia.get('id_tour') or 0)
        if id_tour > 0:
            extra['id_tour'] = id_tour
    except (TypeError, ValueError):
        pass
    prov = dia.get('proveedor') or {}
    try:
        id_prov = int(prov.get('id_proveedor') or 0)
    except (TypeError, ValueError):
        id_prov = 0
    if id_prov > 0:
        extra['id_proveedor'] = id_prov
        extra['es_endoso'] = True
    return extra


def lineas_costo(dia: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Líneas de costo (sin id_venta / n_linea) para un día con proveedor.
    Una línea por moneda con costo: soles (nacionales) y dólares (extranjeros + CAN).
    costo_unitario = costo promedio por pasajero, para que costo_unitario × cantidad_pax = total.
    """
    prov = dia.get('proveedor') or {}
    try:
        id_prov = int(prov.get('id_proveedor') or 0)
    except (TypeError, ValueError):
        id_prov = 0
    costo = dia.get('costo_operativo') or {}
    if id_prov <= 0 or not isinstance(costo, dict):
        return []

    nombre = prov.get('nombre') or 'Proveedor'
    titulo = dia.get('titulo') or 'Servicio'
    pen, usd = _num(costo.get('PEN')), _num(costo.get('USD'))
    pax_pen, pax_usd = int(_num(costo.get('pax_PEN'))), int(_num(costo.get('pax_USD')))

    lineas = []
    hay_dos = pen > 0 and usd > 0
    if pen > 0 and pax_pen > 0:
        lineas.append({
            "id_proveedor": id_prov,
            "tipo_servicio": TIPO_SERVICIO,
            "costo_unitario": round(pen / pax_pen, 2),
            "moneda": "PEN",
            "cantidad_pax": pax_pen,
            "observacion": f"{titulo} — {nombre} (desde el Constructor)",
        })
    if usd > 0 and pax_usd > 0:
        lineas.append({
            "id_proveedor": id_prov,
            # Si también hay línea en soles, se usa otro nombre: (venta, día, tipo) debe ser único.
            "tipo_servicio": TIPO_SERVICIO_EXT if hay_dos else TIPO_SERVICIO,
            "costo_unitario": round(usd / pax_usd, 2),
            "moneda": "USD",
            "cantidad_pax": pax_usd,
            "observacion": f"{titulo} — {nombre} (desde el Constructor)",
        })
    return lineas


def prellenar_costos_dia(client, id_venta: int, n_linea: int, dia: Dict[str, Any]) -> int:
    """
    Inserta en venta_servicio_proveedor las líneas de costo del día que aún no existan.
    Devuelve cuántas líneas creó. Nunca lanza excepción (un fallo aquí no debe frenar la venta).
    """
    creadas = 0
    try:
        for linea in lineas_costo(dia):
            existe = client.table('venta_servicio_proveedor').select('id') \
                .eq('id_venta', id_venta).eq('n_linea', n_linea) \
                .eq('tipo_servicio', linea['tipo_servicio']).limit(1).execute()
            if existe.data:
                continue  # Operaciones ya la tiene (posiblemente editada): no se toca.
            client.table('venta_servicio_proveedor').insert({
                **linea, "id_venta": id_venta, "n_linea": n_linea,
            }).execute()
            creadas += 1
    except Exception as e:
        print(f"[costos_itinerario] No se pudo prellenar el día {n_linea} de la venta {id_venta}: {e}")
    return creadas


def dias_del_render(render: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Lista de días del datos_render (mismas claves que usa el resto del sistema)."""
    if not isinstance(render, dict):
        return []
    dias = (render.get('itinerario_detalles') or render.get('itinerario_detales')
            or render.get('days') or render.get('itinerario') or [])
    return dias if isinstance(dias, list) else []
