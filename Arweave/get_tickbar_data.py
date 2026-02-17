import os
import pandas as pd
import cx_Oracle
from dotenv import load_dotenv
import json
import math
import warnings
import csv

load_dotenv()
os.environ["NLS_LANG"] = ".AL32UTF8"
warnings.filterwarnings('ignore')

DBIN_USER = os.getenv("DBIN_USER")
DBIN_PASSWORD = os.getenv("DBIN_PASSWORD")
DBIN_HOST = os.getenv("DBIN_HOST")
DBIN_PORT = int(os.getenv("DBIN_PORT"))
DBIN_NAME = os.getenv("DBIN_NAME")

db_config = {
    'user': DBIN_USER,
    'password': DBIN_PASSWORD,
    'dsn': cx_Oracle.makedsn(DBIN_HOST, DBIN_PORT, DBIN_NAME)
}

# select * from tztotrazwebinfo;
# select * from tztotrazwebalma;
# select * from tztotrazwebacabmedi;
# select * from tztotrazwebteje;
# select * from tztotrazwebtint;
# select * from tztodetateje;
# select * from tztotrazwebhilo;
# select * from tztotrazwebhilolote;
# select * from tztotrazwebhiloloteprin;
# select * from tztodetatintguia;
# select * from tztodetatint;
# select * from tztodetateje;
# select * from factconvxob a where a.tnumeob in (3403038,3403037);
# select * from tztotrazwebcostoper;
# select * from tztotrazwebcost;
# select * from tzdotrazwebcostoper;
# select * from tztotrazwebpurcdeta;
# select * from tztotrazwebalma;
# select * from tztotrazlotehann a where a.tpurcorde = 'PO-000021354';

list_temp_dfs = [
    "tztotrazwebinfo",
    "tztotrazwebhilo",
    "tztotrazwebhilolote",
    "tztotrazwebhiloloteprin",
    "tztotrazwebteje",
    "tztodetateje",
    "tztotrazwebtint",
    "tztotrazwebcort",
    "tztotrazwebcortoper",
    "tztotrazwebcost",
    "tztotrazwebcostoper",
    "tztotrazwebacabmodu",
    "tztotrazwebacab",
    "tztotrazwebacabmedi",
    "tztotrazwebalma",
    "tztotrazwebtintqyc"
]


def cargar_maestro_quimicos():
    """
    Lee db_quimicos_simple.csv
    Detecta automáticamente si es ';' o ','
    Retorna un diccionario {NOMBRE_QUIMICO: ESTADO_MRSL}
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
                    if nombre:
                        dicc[nombre] = estado

        print(f"✅ Maestro Químicos cargado: {len(dicc)} registros.")
        return dicc

    except Exception as e:
        print(f"❌ Error leyendo CSV: {e}")
        return {}


def connect():
    connection = cx_Oracle.connect(
        user=db_config['user'],
        password=db_config['password'],
        dsn=db_config['dsn'],
        encoding="UTF-8",
        nencoding="UTF-8"
    )
    return connection


def get_df_temp(table, conn):
    try:
        query = f"SELECT * FROM {table}"
        df = pd.read_sql(query, conn)
        df = df.apply(lambda x: x.str.normalize('NFKC').str.encode('utf-8').str.decode('utf-8') if x.dtype == 'object' else x)
        return df
    except Exception as e:
        print(e)
        return ""


def get_tickbar(tickbarr: str, idioma: str, sector: str):
    conn = connect()
    try:
        cursor = conn.cursor()
        p_menserro = cursor.var(cx_Oracle.STRING)
        cursor.callproc("tzprc_traztick", [tickbarr, idioma, sector, p_menserro])

        if p_menserro.getvalue():
            print("Error en procedimiento:")
            print(f"{p_menserro.getvalue()}")
            print("Intentando obtener data...")
            dicc_df = {}
            for temp_names in list_temp_dfs:
                dicc_df[temp_names] = get_df_temp(temp_names, conn)
            return dicc_df
        else:
            dicc_df = {}
            for temp_names in list_temp_dfs:
                dicc_df[temp_names] = get_df_temp(temp_names, conn)
            return dicc_df

    except Exception as e:
        print(f"Error en get_tickbar: {e}")
        return {}
    finally:
        cursor.close()
        conn.close()


def convert_df_to_json(df):
    lista_dicc = df.to_dict(orient="records")  # Convierte todas las filas a una lista de diccionarios
    result_json = json.dumps(lista_dicc, indent=1, default=str)  # Serializa a JSON
    return result_json


def make_json_from_dfs(dicc_df):
    if dicc_df is None:
        print("Error: dicc_df es None. No se puede convertir a JSON.")
        return None

    dicc_main = {}
    for temp_name in list_temp_dfs:
        if temp_name in dicc_df and dicc_df[temp_name] is not None:  # Check if key exists and DataFrame is not None
            json_value = convert_df_to_json(dicc_df[temp_name])
            dicc_main[temp_name] = json.loads(json_value)
    
    main_json = json.dumps(dicc_main, ensure_ascii=False, indent=1)
    return main_json


def save_json_to_file(json_data, filename="output.json"):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(json_data)  # Guarda el JSON en el archivo
    # print(f"JSON guardado en {filename}")


def validar_quimicos_mrsl(clean_json_dict, tickbarr):
    """
    Valida químicos contra ZDHC MRSL y agrega resultados al JSON
    """
    print(f"\n[MRSL] Validando quimicos para {tickbarr}...")
    maestro_quimicos = cargar_maestro_quimicos()

    # Obtener lista de químicos de la prenda
    lista_raw_q = clean_json_dict.get("tztotrazwebtintqyc", [])
    lista_todos_quimicos = []
    contador_cumple = 0
    contador_total = 0
    errores_quimicos = set()

    for q in lista_raw_q:
        nombre_real = q.get("TDESCPROD", "").strip().upper()

        if not nombre_real:
            continue

        contador_total += 1

        # Buscar en el CSV maestro
        estado_mrsl = maestro_quimicos.get(nombre_real)

        if estado_mrsl:
            # Agregar químico con su estado real
            cumple = (estado_mrsl == "Cumple")
            if cumple:
                contador_cumple += 1

            lista_todos_quimicos.append({
                "nombre": q.get("TDESCPROD", ""),
                "proveedor": q.get("TPROVPROD", ""),
                "origen": q.get("TORIGPROD", ""),
                "estado_mrsl": estado_mrsl,
                "cumple": cumple
            })

            if not cumple:
                print(f"   [!] {nombre_real}: {estado_mrsl}")
        else:
            # No existe en el CSV - marcarlo como "Sin datos"
            lista_todos_quimicos.append({
                "nombre": q.get("TDESCPROD", ""),
                "proveedor": q.get("TPROVPROD", ""),
                "origen": q.get("TORIGPROD", ""),
                "estado_mrsl": "Sin datos",
                "cumple": False
            })
            errores_quimicos.add(nombre_real)

    # Calcular porcentaje de cumplimiento
    porcentaje_cumplimiento = (contador_cumple / contador_total * 100) if contador_total > 0 else 0

    # Agregar lista completa y stats al JSON
    clean_json_dict["quimicos_certificados"] = lista_todos_quimicos
    clean_json_dict["stats_mrsl"] = {
        "total": contador_total,
        "cumple": contador_cumple,
        "no_cumple": contador_total - contador_cumple,
        "porcentaje": round(porcentaje_cumplimiento, 2)
    }

    # Reportar estadísticas
    print(f"   [OK] {contador_cumple}/{contador_total} quimicos cumplen ZDHC MRSL ({porcentaje_cumplimiento:.2f}%)")

    # Reportar errores si existen
    if errores_quimicos:
        print(f"   [!] {len(errores_quimicos)} quimicos sin datos en CSV:")
        for err in sorted(errores_quimicos):
            print(f"      - {err}")

        # Guardar en archivo de alertas
        with open("alertas_quimicos.txt", "a", encoding="utf-8") as f:
            f.write(f"\n--- Tickbarr: {tickbarr} ---\n")
            for err in sorted(errores_quimicos):
                f.write(f"NO ENCONTRADO: {err}\n")

    return clean_json_dict


def get_json_from_tickbarr(tickbarr: str):
    """
    Obtiene JSON completo de un tickbarr específico
    Incluye validación de químicos contra ZDHC MRSL
    """
    dicc_df = get_tickbar(tickbarr, "es", None)
    if dicc_df is None:
        print(f"Error: No se pudo obtener datos para el tickbarr {tickbarr}")
        return None

    first_json = make_json_from_dfs(dicc_df)
    if first_json is None:
        print(f"Error: No se pudo convertir datos a JSON para el tickbarr {tickbarr}")
        return None

    main_json = clean_relevant_json(json.loads(first_json))
    clean_json_dict = json.loads(main_json)

    # Validar químicos ZDHC MRSL
    clean_json_dict = validar_quimicos_mrsl(clean_json_dict, tickbarr)

    return json.dumps(clean_json_dict, ensure_ascii=False, indent=1)


def clean_relevant_json(json_data):
    with open('relevant_data.json', 'r', encoding='utf-8') as file:
        campos_por_clave = json.load(file)

    resultado = {}
    # Usar list_temp_dfs para mantener el orden correcto
    for clave_principal in list_temp_dfs:
        if clave_principal in campos_por_clave:
            campos_a_conservar = campos_por_clave[clave_principal]
            if clave_principal in json_data and json_data[clave_principal]:
                datos_filtrados = []
                for i in range(len(json_data[clave_principal])):
                    filtrar = {}
                    for campo in campos_a_conservar:
                        if campo in json_data[clave_principal][i]:
                            valor = json_data[clave_principal][i][campo]
                            if valor is not None and valor != "NaT" and not (isinstance(valor, float) and math.isnan(valor)):
                                filtrar[campo] = valor

                    # Se agrega el diccionario filtrado a la lista (indentado dentro del for i)
                    datos_filtrados.append(filtrar)

                resultado[clave_principal] = datos_filtrados

    resultado = json.dumps(resultado, ensure_ascii=False, indent=1)
    return resultado

def get_clean_json_from_tickbar(tickbarr: str):
    """
    Obtiene JSON limpio de un tickbarr específico
    Incluye validación de químicos contra ZDHC MRSL
    """
    # 1. Obtener datos de Oracle
    dicc_df = get_tickbar(tickbarr, "es", None)
    main_json = make_json_from_dfs(dicc_df)
    clean_json_dict = json.loads(clean_relevant_json(json.loads(main_json)))

    # 2. Validar químicos ZDHC MRSL
    clean_json_dict = validar_quimicos_mrsl(clean_json_dict, tickbarr)

    # 3. Retornar JSON final con químicos validados y estadísticas
    return json.dumps(clean_json_dict, ensure_ascii=False, indent=1)


# mi_json = get_clean_json_from_tickbar("089853705010")
# save_json_to_file(mi_json, "mi_json.json")

# tickbarrs por probar: 089853705010 - 088932801353

# dicc_df = get_tickbar("092069706078", "es", None)
# # print(dicc_df)
# main_json = make_json_from_dfs(dicc_df)
# clean_json = clean_relevant_json(json.loads(main_json))
# # #print(clean_json)
# save_json_to_file(main_json, "segundo.json")
# save_json_to_file(clean_json, "clean.json")
# print(main_json)


# info_json = convert_df_to_json(df1)
# print(info_json)