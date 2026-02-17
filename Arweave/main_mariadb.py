import pandas as pd
import os
import cx_Oracle
import mysql.connector
from dotenv import load_dotenv
import json
import math
import warnings
import csv
from hash_utils import generar_hash_unico 

load_dotenv()
warnings.filterwarnings('ignore')

# --- CONFIGURACIONES ---
db_config_oracle = {
    'user': os.getenv("DBIN_USER"),
    'password': os.getenv("DBIN_PASSWORD"),
    'dsn': cx_Oracle.makedsn(os.getenv("DBIN_HOST"), int(os.getenv("DBIN_PORT")), os.getenv("DBIN_NAME"))
}

mariadb_config = {
    'user': os.getenv("DB_PRENDAS_USER"),
    'password': os.getenv("DB_PRENDAS_PASSWORD"),
    'host': os.getenv("DB_PRENDAS_HOST"),
    'port': int(os.getenv("DB_PRENDAS_PORT")),
    'database': os.getenv("DB_PRENDAS_NAME")
}

list_temp_dfs = [
    "tztotrazwebinfo", "tztotrazwebhilo", "tztotrazwebhilolote", "tztotrazwebhiloloteprin",
    "tztotrazwebteje", "tztodetateje", "tztotrazwebtint", "tztotrazwebcort",
    "tztotrazwebcortoper", "tztotrazwebcost", "tztotrazwebcostoper", "tztotrazwebacabmodu", "tztotrazwebacab",
    "tztotrazwebacabmedi", "tztotrazwebalma", "tztotrazwebtintqyc"
]

# --- CONEXIONES ---
def connect_oracle():
    return cx_Oracle.connect(user=db_config_oracle['user'], password=db_config_oracle['password'], dsn=db_config_oracle['dsn'], encoding="UTF-8", nencoding="UTF-8")

def connect_mariadb():
    return mysql.connector.connect(**mariadb_config)

def cargar_maestro_quimicos():
    """ 
    Lee db_quimicos_simple.csv (Versión PROBADA)
    Detecta automáticamente si es ';' o ',' 
    """
    ruta_csv = "db_quimicos_simple.csv"
    dicc = {}
    
    if not os.path.exists(ruta_csv):
        print(f"⚠️ No se encontró {ruta_csv}. Se omitirá filtrado MRSL.")
        return {}

    try:
        # 1. Detectar separador automáticamente
        delimiter = ',' # Por defecto
        with open(ruta_csv, 'r', encoding='latin-1', errors='ignore') as f:
            if ';' in f.readline():
                delimiter = ';'
        
        print(f"📊 Maestro Químicos: Usando separador '{delimiter}'")

        # 2. Leer archivo
        with open(ruta_csv, mode='r', encoding='latin-1') as f:
            reader = csv.reader(f, delimiter=delimiter) 
            next(reader, None) # Saltar cabecera
            
            for row in reader:
                if len(row) >= 2: 
                    nombre = row[0].strip().upper() # Col A
                    estado = row[1].strip()         # Col B
                    if nombre: dicc[nombre] = estado
                        
        print(f"✅ Maestro Químicos cargado: {len(dicc)} registros.")
        return dicc
        
    except Exception as e:
        print(f"❌ Error leyendo CSV: {e}")
        return {}
    
# --- EXTRACCIÓN DE ORACLE (MODIFICADO PARA MANAGER) ---
def get_tickbarrs_yesterday():
    print("🔌 Conectando a Oracle para obtener lista...")
    
    # Busca la variable en el .env. Si no está, usa una por defecto.
    target_date = os.getenv('TARGET_DATE', '2026-01-28') 
    print(f"📅 FECHA OBJETIVO (Desde .env): {target_date}")

    conn = connect_oracle()
    try:
        # Usamos el formato validado YYYY-MM-DD
        query = f"""
            SELECT TTICKBARR, TNUMECAJA, TCODIESTICLIE, TCODIETIQCLIE, TCODITALL 
            FROM apdoprendas a 
            WHERE trunc(a.tfechmovi) = TO_DATE('{target_date}', 'YYYY-MM-DD')
        """
        df = pd.read_sql(query, conn)
        return df.to_dict(orient="records") if not df.empty else []
    except Exception as e:
        print(f"❌ Error Oracle Lista: {e}")
        return []
    finally:
        conn.close()

def get_tickbar_data(tickbarr, conn):
    try:
        cursor = conn.cursor()
        p_menserro = cursor.var(cx_Oracle.STRING)
        cursor.callproc("tzprc_traztick", [tickbarr, "es", None, p_menserro])

        dicc_main = {}
        
        def get_df(table):
            try:
                return pd.read_sql(f"SELECT * FROM {table}", conn)
            except: 
                return pd.DataFrame()

        for temp_name in list_temp_dfs:
            df = get_df(temp_name)
            if not df.empty:
                df = df.apply(lambda x: x.str.normalize('NFKC').str.encode('utf-8').str.decode('utf-8') if x.dtype == 'object' else x)
                dicc_main[temp_name] = df.to_dict(orient="records")
        
        cursor.close()
        return dicc_main
    except Exception as e:
        raise e

def clean_json_data(full_data):
    try:
        with open('relevant_data.json', 'r', encoding='utf-8') as f:
            filter_map = json.load(f)
    except: return full_data

    cleaned = {}
    for table, fields in filter_map.items():
        if table in full_data:
            cleaned_rows = []
            for row in full_data[table]:
                new_row = {}
                for field in fields:
                    if field in row:
                        val = row[field]
                        if val is not None and val != "NaT" and not (isinstance(val, float) and math.isnan(val)):
                            new_row[field] = val
                if new_row: cleaned_rows.append(new_row)
            if cleaned_rows: cleaned[table] = cleaned_rows
    return cleaned

def safe_extract(data, table, key):
    try:
        return data.get(table, [{}])[0].get(key, None)
    except:
        return None

# --- LÓGICA DE SINCRONIZACIÓN (MODO PRODUCCIÓN - ORIGINAL) ---
def procesar_prenda(prenda_oracle, hash_interno, json_data, output_folder, conn_mariadb):
    try:
        cursor = conn_mariadb.cursor()
        tickbar = prenda_oracle['TTICKBARR']
        
        # ... (La parte de extracción de datos complementarios tcodiclie, etc. sigue igual) ...
        # (Asegúrate de tener las variables tcodiclie, tdescclie, etc. definidas aquí como en tu código actual)
        tcodiclie = safe_extract(json_data, 'tztotrazwebinfo', 'TCODICLIE')
        tdescclie = safe_extract(json_data, 'tztotrazwebinfo', 'TNOMBCLIE')
        ttipopren = safe_extract(json_data, 'tztotrazwebinfo', 'TTIPOPREN')
        ttipoedad = safe_extract(json_data, 'tztotrazwebinfo', 'TINDIEDAD')
        ttipogene = safe_extract(json_data, 'tztotrazwebinfo', 'TINDIGENE')
        tlugadest = safe_extract(json_data, 'tztotrazwebalma', 'TDESCDEST')
        ttipoteji = safe_extract(json_data, 'tztotrazwebteje', 'TTIPOTEJI')
        arweave_status = "PENDIENTE_SUBIDA"

        sql_insert = """
            INSERT INTO apdobloctrazhashtemp 
            (TTICKBARR, TNUMECAJA, TESTICLIE, TETIQCLIE, TCODITALL, 
             TTICKHASH, THASHINTE, TCODICLIE, TDESCCLIE, TTIPOPREN, 
             TTIPOEDAD, TTIPOGENE, TLUGADEST, TTIPOTEJI)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        valores = (
            tickbar, 
            prenda_oracle.get('TNUMECAJA'), 
            prenda_oracle.get('TCODIESTICLIE'), 
            prenda_oracle.get('TCODIETIQCLIE'), 
            prenda_oracle.get('TCODITALL'),
            arweave_status,
            hash_interno,
            tcodiclie, tdescclie, ttipopren, ttipoedad, ttipogene, tlugadest, ttipoteji
        )
        
        try:
            cursor.execute(sql_insert, valores)
            conn_mariadb.commit()
            
            # --- AQUÍ ESTÁ LA CLAVE: SOLO CREAMOS EL ARCHIVO SI ES NUEVO ---
            with open(f"{output_folder}/{hash_interno}.json", "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False, default=str)
            return "NUEVO"
            
        except mysql.connector.Error as err:
            if err.errno == 1062: # Duplicate entry
                return "RECICLADO" # No creamos archivo, ahorramos tiempo
            raise err

    except Exception as e:
        print(f"❌ Error MariaDB ({prenda_oracle.get('TTICKBARR')}): {e}")
        return "ERROR"
    finally:
        try: cursor.close() 
        except: pass

# --- MAIN INDUSTRIAL ROBUSTO (CON FILTRO MRSL) ---
def main():
    print("=========================================")
    print("🐬 NETTALCO - SINCRONIZACIÓN V5 (DOBLE PERSISTENCIA)")
    print("=========================================")

    folder_salida = "cola_de_envio"
    if not os.path.exists(folder_salida):
        os.makedirs(folder_salida)

    # 1. CARGAR MAESTRO DE QUÍMICOS (NUEVO)
    maestro_quimicos = cargar_maestro_quimicos()
    errores_quimicos = set() # Para no repetir alertas

    prendas_lista = get_tickbarrs_yesterday()
    total = len(prendas_lista)
    print(f"📦 Procesando lote de {total} prendas...")

    if total == 0: return

    print("🔌 Estableciendo túnel persistente Oracle <-> MariaDB...")
    try:
        conn_oracle = connect_oracle()
        conn_mariadb = connect_mariadb()
    except Exception as e:
        print(f"❌ Error fatal conectando bases de datos: {e}")
        return

    contadores = {"NUEVO": 0, "RECICLADO": 0, "ERROR": 0}

    for i, prenda in enumerate(prendas_lista):
        tick = prenda['TTICKBARR']
        print(f"   [{i+1}/{total}] {tick}", end="\r")
        
        try:
            if not conn_mariadb.is_connected():
                print(f"\n⚠️ Re-conectando MariaDB...")
                conn_mariadb.reconnect(attempts=3, delay=1)

            raw = get_tickbar_data(tick, conn_oracle)
            
            if raw:
                clean = clean_json_data(raw)

                # ### INICIO LÓGICA DE QUÍMICOS ###
                # Obtenemos la lista sucia de químicos del JSON
                lista_raw_q = clean.get("tztotrazwebtintqyc", [])
                lista_certificada = []

                for q in lista_raw_q:
                    nombre_real = q.get("TDESCPROD", "").strip().upper()
                    
                    # 1. Buscamos en el Excel
                    estado_mrsl = maestro_quimicos.get(nombre_real)

                    if estado_mrsl:
                        # 2. Solo pasa si dice EXACTAMENTE "Cumple"
                        if estado_mrsl == "Cumple":
                            lista_certificada.append({
                                "nombre": nombre_real,
                                "proveedor": q.get("TNOMBPROV", ""),
                                "origen": q.get("TORIGPROD", ""),
                                "certificado": True # Flag para el frontend
                            })
                    else:
                        # 3. No existe en el Excel -> A la lista de errores
                        if nombre_real: errores_quimicos.add(nombre_real)

                # 4. Guardamos la lista limpia en el JSON final
                clean["quimicos_certificados"] = lista_certificada
                # ### FIN LÓGICA DE QUÍMICOS ###

                huella = generar_hash_unico(clean)
                estado = procesar_prenda(prenda, huella, clean, folder_salida, conn_mariadb)
                contadores[estado] += 1
        
        except (cx_Oracle.DatabaseError, cx_Oracle.InterfaceError) as e:
            print(f"\n⚠️ Fallo Oracle en {tick}. Intentando reconectar... {e}")
            try: conn_oracle = connect_oracle() 
            except: pass
            contadores["ERROR"] += 1
        except Exception as e2:
            print(f"\n❌ Error genérico en {tick}: {e2}")
            contadores["ERROR"] += 1

    try:
        conn_oracle.close()
        conn_mariadb.close()
    except: pass

    # ### REPORTE DE ERRORES DE QUÍMICOS ###
    if errores_quimicos:
        with open("alertas_quimicos.txt", "a", encoding="utf-8") as f: # "a" para append
            f.write(f"\n--- EJECUCIÓN {pd.Timestamp.now()} ---\n")
            for err in sorted(errores_quimicos):
                f.write(f"NO ENCONTRADO EN EXCEL: {err}\n")
        print(f"\n⚠️ Se detectaron {len(errores_quimicos)} químicos desconocidos. Ver alertas_quimicos.txt")

    print("\n\n✅ PROCESO COMPLETADO")
    print(f"   🆕 Generados: {contadores['NUEVO']}")
    print(f"   ♻️  Reciclados: {contadores['RECICLADO']}")
    print(f"   ⚠️ Errores: {contadores['ERROR']}")

if __name__ == "__main__":
    main()