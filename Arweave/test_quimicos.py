import csv
import os

# --- 1. SIMULAMOS LA DATA QUE VIENE DE ORACLE ---
# Estos son los datos tal cual me los mostraste en tu JSON
datos_oracle_simulados = [
    { "TDESCPROD": "ACIDO ACETICO GLACIAL", "TNOMBPROV": "COMINSA", "TORIGPROD": "CHINA" },
    { "TDESCPROD": "SAL MOLIDA EXTRA (NACL)/CLORUR", "TNOMBPROV": "QUIMPAC", "TORIGPROD": "PERÚ" },
    { "TDESCPROD": "SARABID LDR", "TNOMBPROV": "CHT", "TORIGPROD": "PERÚ" },
    { "TDESCPROD": "BEIZYM BPM 300", "TNOMBPROV": "CHT", "TORIGPROD": "PERÚ" },
    { "TDESCPROD": "QUIMICO FANTASMA INEXISTENTE", "TNOMBPROV": "X", "TORIGPROD": "X" } 
]

def cargar_maestro_quimicos():
    """ Lee tu CSV simplificado (Nombre, Estado) """
    ruta_csv = "db_quimicos_simple.csv"
    dicc = {}
    
    if not os.path.exists(ruta_csv):
        print(f"❌ ERROR: No encuentro '{ruta_csv}'")
        return {}

    try:
        # Detectar separador automáticamente
        delimiter = ','
        with open(ruta_csv, 'r', encoding='latin-1', errors='ignore') as f:
            if ';' in f.readline(): delimiter = ';'
        
        print(f"📊 Leyendo CSV con separador: '{delimiter}'")

        with open(ruta_csv, mode='r', encoding='latin-1') as f:
            reader = csv.reader(f, delimiter=delimiter)
            next(reader, None) # Saltar encabezado si existe
            for row in reader:
                if len(row) >= 2:
                    nombre = row[0].strip().upper()
                    estado = row[1].strip()
                    if nombre: dicc[nombre] = estado
        return dicc
    except Exception as e:
        print(f"❌ Error leyendo CSV: {e}")
        return {}

def probar_logica():
    print("--- 🧪 INICIANDO TEST DE QUÍMICOS ---")
    
    # 1. Cargamos el maestro
    maestro = cargar_maestro_quimicos()
    print(f"📚 Maestro cargado con {len(maestro)} registros.\n")

    print("--- 🔍 ANALIZANDO DATA SIMULADA ---")
    
    quimicos_certificados = []
    
    for q in datos_oracle_simulados:
        nombre_real = q["TDESCPROD"].strip().upper()
        estado_csv = maestro.get(nombre_real)
        
        print(f"Testing: '{nombre_real}'")
        
        if estado_csv:
            if estado_csv == "Cumple":
                print(f"   ✅ APROBADO (Estado: {estado_csv})")
                quimicos_certificados.append(q)
            else:
                print(f"   ⛔ RECHAZADO (Estado: {estado_csv}) -> No pasará a la web.")
        else:
            print(f"   ⚠️ NO ENCONTRADO en Excel -> Se reportará como error.")

    print("\n--- 🏁 RESULTADO FINAL (JSON PARA WEB) ---")
    print(f"Se mostrarán {len(quimicos_certificados)} químicos en la web:")
    for aprobado in quimicos_certificados:
        print(f"   🌟 {aprobado['TDESCPROD']}")

if __name__ == "__main__":
    probar_logica()