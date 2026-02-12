import json
import os
from datetime import datetime

# --- CONFIGURACIÓN ---
# Carpeta donde están tus JSONs crudos (los que está generando el main_mariadb.py)
CARPETA_INPUT = "cola_de_envio"
# Nombre de UN archivo real que ya tengas ahí (cámbialo por uno que veas en tu carpeta)
ARCHIVO_EJEMPLO = "00c9776203b4b4368f62e31e3327db5156a7d95d6610a83bec1410538f22ffe2.json" 

def formatear_fecha(fecha_str):
    if not fecha_str or fecha_str == "NaT": return ""
    try:
        dt = datetime.strptime(str(fecha_str), "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%d %b %Y") # Ej: 28 Ene 2026
    except: return fecha_str

def procesar_personal(lista_cruda, campo_nombre, campo_id, rol_defecto):
    """Extrae personas únicas y elimina duplicados"""
    equipo = {}
    for item in lista_cruda:
        nombre = item.get(campo_nombre)
        codigo = item.get(campo_id)
        if nombre and nombre not in equipo:
            # Intentar deducir rol específico si existe, sino usar el defecto
            rol = item.get('TDESCOPERESPE', item.get('TDESCOPER', rol_defecto))
            equipo[nombre] = {
                "name": nombre.title(),
                "role": rol.title() if rol else rol_defecto,
                "id": codigo
            }
    return list(equipo.values())

def generar_product_data(raw):
    # 1. Header Info
    info = raw.get('tztotrazwebinfo', [{}])[0]
    alma = raw.get('tztotrazwebalma', [{}])[0]
    
    # 2. Extraer Fechas y Personas por Etapa
    
    # Etapa 1: Origen (Hilo)
    hilo = raw.get('tztotrazwebhiloloteprin', [{}])[0]
    fecha_hilo = formatear_fecha(hilo.get('TFECHGUIAHILO'))
    
    # Etapa 2: Tejeduría
    tejedores = procesar_personal(raw.get('tztotrazwebteje', []), 'TNOMBPERS', 'TCODIPERS', 'Tejedor')
    fecha_teje = formatear_fecha(raw.get('tztotrazwebteje', [{}])[0].get('TFECHTEJE'))

    # Etapa 3: Tintorería
    tintoreros = []
    tinte_data = raw.get('tztotrazwebtint', [])
    for t in tinte_data:
        # Extraer operarios de tinte (a veces vienen en campos distintos)
        if t.get('TNOMBOPERCORTINIC'): tintoreros.append({"name": t['TNOMBOPERCORTINIC'].title(), "role": "Apertura", "id": t.get('TOPERCORTINIC')})
        if t.get('TNOMBOPERSECAINIC'): tintoreros.append({"name": t['TNOMBOPERSECAINIC'].title(), "role": "Secado", "id": t.get('TOPERSECAINIC')})
        if t.get('TNOMBOPERACABINIC'): tintoreros.append({"name": t['TNOMBOPERACABINIC'].title(), "role": "Acabado Tela", "id": t.get('TOPERACABINIC')})
    fecha_tinte = formatear_fecha(tinte_data[0].get('TFECHTENIINIC')) if tinte_data else ""

    # Etapa 4: Corte
    cortadores = procesar_personal(raw.get('tztotrazwebcortoper', []), 'TNOMBPERS', 'TCODIPERS', 'Corte')
    fecha_corte = formatear_fecha(raw.get('tztotrazwebcort', [{}])[0].get('TFECHDESPCORT'))

    # Etapa 5: Confección (El equipo grande)
    confeccionistas = procesar_personal(raw.get('tztotrazwebcostoper', []), 'TNOMBPERS', 'TCODIPERS', 'Confección')
    # Añadimos supervisora si existe
    cost_meta = raw.get('tztotrazwebcost', [{}])[0]
    if cost_meta.get('TNOMBPERSSUPE'):
        confeccionistas.append({"name": cost_meta['TNOMBPERSSUPE'].title(), "role": "Supervisora", "id": cost_meta.get('TCODIPERSSUPE')})
    
    # Etapa 6: Acabado/Logística
    acabadores = []
    acab_data = raw.get('tztotrazwebacab', [{}])[0]
    if acab_data.get('TNOMBRECEBANDCOST'): acabadores.append({"name": acab_data['TNOMBRECEBANDCOST'].title(), "role": "Recepción", "id": acab_data.get('TCODIRECEBANDCOST')})
    if acab_data.get('TNOMBPERSPESA'): acabadores.append({"name": acab_data['TNOMBPERSPESA'].title(), "role": "Empaque Final", "id": acab_data.get('TCODIPERSPESA')})
    fecha_acab = formatear_fecha(acab_data.get('TFECHEMPA'))

    # CONSTRUIR EL OBJETO FINAL
    product_data = {
        "header": {
            "brand": info.get('TNOMBCLIE', 'LACOSTE'),
            "collection": f"Temporada {alma.get('TCODITEMP', '2026')}",
            "item": info.get('TDESCPREN', 'Prenda Nettalco').title(),
            "ref": info.get('TCODIESTICLIE', ''),
            "color": f"{info.get('TDESCETIQCLIE', '')}",
            "img": "https://image.uniqlo.com/UQ/ST3/Latam/imagesgoods/422992/item/lggoods_12_422992.jpg?width=1600&impolicy=quality_75"
        },
        "steps": [
            {
                "id": 1, "stage": "ORIGEN", "title": "La Fibra Inicial", "date": fecha_hilo,
                "location": "Lima, Perú", "desc": "Fibra de algodón de alta calidad recepcionada en almacenes.",
                "icon": "Icons.MapPin", "people": []
            },
            {
                "id": 2, "stage": "TEJEDURÍA", "title": "Arquitectos del Tejido", "date": fecha_teje,
                "location": "Planta Tejido", "desc": "Tejido en máquinas circulares de alta precisión.",
                "icon": "Icons.Shirt", "people": tejedores
            },
            {
                "id": 3, "stage": "TINTORERÍA", "title": "Maestros del Color", "date": fecha_tinte,
                "location": "Planta Tintorería", "desc": "Proceso de teñido y acabado de la tela.",
                "icon": "Icons.Droplets", "people": tintoreros
            },
            {
                "id": 4, "stage": "CORTE", "title": "Geometría y Precisión", "date": fecha_corte,
                "location": "Área de Corte", "desc": "Corte automatizado de piezas.",
                "icon": "Icons.Scissors", "people": cortadores
            },
            {
                "id": 5, "stage": "CONFECCIÓN", "title": "Las Manos que Crean", "date": "Proceso Manual",
                "location": "Línea de Costura", "desc": f"Un equipo de {len(confeccionistas)} especialistas ensambló esta prenda.",
                "icon": "Icons.CheckCircle2", "people": confeccionistas
            },
            {
                "id": 6, "stage": "LOGÍSTICA", "title": "Listo para el Mundo", "date": fecha_acab,
                "location": "Centro de Distribución", "desc": "Empaque y certificación final.",
                "icon": "Icons.Box", "people": acabadores
            }
        ]
    }
    return product_data

def main():
    path = os.path.join(CARPETA_INPUT, ARCHIVO_EJEMPLO)
    if not os.path.exists(path):
        # Si no encuentra el archivo específico, toma el primero que encuentre
        archivos = [f for f in os.listdir(CARPETA_INPUT) if f.endswith('.json')]
        if archivos:
            path = os.path.join(CARPETA_INPUT, archivos[0])
            print(f"⚠️ Usando primer archivo encontrado: {archivos[0]}")
        else:
            print("❌ No hay archivos JSON en la carpeta cola_de_envio")
            return

    with open(path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    data_limpia = generar_product_data(raw_data)

    # Imprimir en formato JavaScript para copiar y pegar
    print("\n✅ COPIA ESTE CÓDIGO EN TU HTML (Reemplaza 'const productData = ...'):\n")
    print("const productData = " + json.dumps(data_limpia, indent=4, ensure_ascii=False) + ";")
    
    # Pequeño hack para que los iconos no queden como strings
    print("\n⚠️ NOTA: Después de pegar, quita las comillas de los íconos (ej: 'Icons.MapPin' -> Icons.MapPin)")

if __name__ == "__main__":
    main()