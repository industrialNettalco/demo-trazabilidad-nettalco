import pandas as pd
import os
import cx_Oracle
from dotenv import load_dotenv
import json
import math
import warnings
# Importamos tu nueva herramienta exitosa
from hash_utils import generar_hash_unico 

# Cargar variables
load_dotenv()
warnings.filterwarnings('ignore')

# Configuración DB
DBIN_USER = os.getenv("DBIN_USER")
DBIN_PASSWORD = os.getenv("DBIN_PASSWORD")
DBIN_HOST = os.getenv("DBIN_HOST")
DBIN_PORT = int(os.getenv("DBIN_PORT"))
DBIN_NAME = os.getenv("DBIN_NAME")

db_config = {
    'user': DBIN_USER, 'password': DBIN_PASSWORD,
    'dsn': cx_Oracle.makedsn(DBIN_HOST, DBIN_PORT, DBIN_NAME)
}

list_temp_dfs = [
    "tztotrazwebinfo", "tztotrazwebalma", "tztotrazwebacab", "tztotrazwebacabmedi",
    "tztotrazwebteje", "tztotrazwebtint", "tztodetateje", "tztotrazwebhilo",
    "tztotrazwebhilolote", "tztotrazwebhiloloteprin", "tztotrazwebcostoper",
    "tztotrazwebcost", "tztotrazwebcort", "tztotrazwebcortoper"
]

# --- FUNCIONES DE SOPORTE (Idénticas a tus scripts anteriores) ---

def connect():
    return cx_Oracle.connect(user=db_config['user'], password=db_config['password'], dsn=db_config['dsn'], encoding="UTF-8", nencoding="UTF-8")

def get_tickbarrs_yesterday():
    print("🔌 Conectando a Oracle...")
    conn = connect()
    try:
        # QUERY: Ajustada para buscar producción de ayer. 
        # Si no tienes datos de ayer, el script te avisará.
        query = "SELECT TTICKBARR FROM apdoprendas a WHERE trunc(a.tfechmovi) = trunc(sysdate - 1)"
        df = pd.read_sql(query, conn)
        return df['TTICKBARR'].tolist() if not df.empty else []
    except Exception as e:
        print(f"❌ Error DB: {e}")
        return []
    finally:
        conn.close()

def get_df_temp(table, conn):
    try:
        query = f"SELECT * FROM {table}"
        df = pd.read_sql(query, conn)
        df = df.apply(lambda x: x.str.normalize('NFKC').str.encode('utf-8').str.decode('utf-8') if x.dtype == 'object' else x)
        return df
    except:
        return ""

def get_tickbar_data(tickbarr):
    conn = connect()
    try:
        cursor = conn.cursor()
        p_menserro = cursor.var(cx_Oracle.STRING)
        cursor.callproc("tzprc_traztick", [tickbarr, "es", None, p_menserro])

        dicc_main = {}
        for temp_name in list_temp_dfs:
            df = get_df_temp(temp_name, conn)
            if not isinstance(df, str) and not df.empty:
                dicc_main[temp_name] = df.to_dict(orient="records")
        return dicc_main
    except Exception as e:
        return None
    finally:
        cursor.close()
        conn.close()

def clean_json_data(full_data):
    try:
        with open('relevant_data.json', 'r', encoding='utf-8') as f:
            filter_map = json.load(f)
    except:
        print("⚠️ Error: No encuentro 'relevant_data.json'")
        return {}

    cleaned = {}
    for table, fields in filter_map.items():
        if table in full_data and full_data[table]:
            cleaned_rows = []
            for row in full_data[table]:
                new_row = {}
                for field in fields:
                    if field in row:
                        val = row[field]
                        if val is not None and val != "NaT" and not (isinstance(val, float) and math.isnan(val)):
                            new_row[field] = val
                if new_row:
                    cleaned_rows.append(new_row)
            if cleaned_rows:
                cleaned[table] = cleaned_rows
    return cleaned

# --- EL CEREBRO DEL ANÁLISIS ---

def main():
    print("=========================================")
    print("📊 NETTALCO - ANÁLISIS DE REDUNDANCIA")
    print("   (Modo Auditoría: No se guarda nada)")
    print("=========================================")

    # 1. Obtener lista
    tickbarrs = get_tickbarrs_yesterday()
    total_prendas = len(tickbarrs)
    print(f"📦 Total prendas detectadas (Ayer): {total_prendas}")

    if total_prendas == 0:
        print("⚠️ No hay datos de producción de ayer para analizar.")
        print("💡 Sugerencia: Modifica la query en 'get_tickbarrs_yesterday' si quieres probar con otra fecha.")
        return

    # 2. Iniciar escaneo
    hashes_unicos = set() # 'set' es una colección que no permite duplicados automáticamente
    duplicados_detectados = 0
    
    print("\n🚀 Iniciando escaneo de huellas digitales...")

    for i, tick in enumerate(tickbarrs):
        # Feedback de progreso
        print(f"   Analizando [{i+1}/{total_prendas}]: {tick}...", end="\r")
        
        # Extraemos la data real
        raw_data = get_tickbar_data(tick)
        
        if raw_data:
            # Limpiamos con tu filtro
            clean_data = clean_json_data(raw_data)
            
            # --- MOMENTO DE LA VERDAD ---
            # Generamos el hash
            huella = generar_hash_unico(clean_data)
            
            if huella in hashes_unicos:
                duplicados_detectados += 1
            else:
                hashes_unicos.add(huella)

    # 3. Reporte Final
    print("\n\n=========================================")
    print("📉 RESULTADOS DEL ANÁLISIS")
    print("=========================================")
    print(f"🔹 Total Prendas Procesadas: {total_prendas}")
    print(f"🔹 Archivos Únicos (Reales): {len(hashes_unicos)}")
    print(f"🔹 Duplicados (Redundantes): {duplicados_detectados}")
    
    if total_prendas > 0:
        ahorro = (duplicados_detectados / total_prendas) * 100
        print(f"💰 PORCENTAJE DE AHORRO POTENCIAL: {ahorro:.2f}%")
        
        costo_sin_opt = total_prendas * 0.003
        costo_con_opt = len(hashes_unicos) * 0.003
        print(f"\n💵 Proyección de Costo Diario (Estimado):")
        print(f"   - Sin optimizar: ${costo_sin_opt:.4f} USD")
        print(f"   - Con Hash     : ${costo_con_opt:.4f} USD")
    print("=========================================")

if __name__ == "__main__":
    main()