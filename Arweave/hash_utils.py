import hashlib
import json

def generar_hash_unico(data_json):
    """
    Recibe un diccionario (JSON), ordena sus llaves para asegurar consistencia
    y devuelve una huella digital única SHA-256.
    """
    # 1. Convertimos el diccionario a Texto (String)
    # sort_keys=True: OBLIGATORIO. Ordena las llaves (A-Z).
    # ensure_ascii=False: Respeta las tildes y ñ.
    # default=str: <--- ¡ESTA ES LA MAGIA! Si encuentra una Fecha/Timestamp, la vuelve texto.
    json_string = json.dumps(data_json, sort_keys=True, ensure_ascii=False, default=str)
    
    # 2. Creamos el Hash SHA-256 (Estándar de seguridad)
    hash_obj = hashlib.sha256(json_string.encode('utf-8'))
    
    # 3. Devolvemos la huella en formato hexadecimal
    return hash_obj.hexdigest()

# --- EJEMPLO DE USO RÁPIDO PARA PROBAR ---
if __name__ == "__main__":
    from datetime import datetime
    # Simulación con una fecha real para probar el fix
    prenda_A = { "producto": "Camiseta", "fecha": datetime.now() }
    
    try:
        hash_A = generar_hash_unico(prenda_A)
        print(f"Huella generada con éxito: {hash_A}")
        print("✅ ¡ERROR CORREGIDO! Ahora el sistema acepta Fechas/Timestamps.")
    except Exception as e:
        print(f"❌ Todavía falla: {e}")