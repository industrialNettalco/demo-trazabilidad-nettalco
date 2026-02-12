import os
import pandas as pd
import cx_Oracle
from dotenv import load_dotenv
import json
import math
import warnings

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
    "tztotrazwebalma",
    "tztotrazwebacab",
    "tztotrazwebacabmedi",
    "tztotrazwebteje",
    "tztotrazwebtint",
    "tztodetateje",
    "tztotrazwebhilo",
    "tztotrazwebhilolote",
    "tztotrazwebhiloloteprin",
    "tztotrazwebcostoper",
    "tztotrazwebcost",
    "tztotrazwebcort",
    "tztotrazwebcortoper",
    "tztotrazwebtintqyc"
]


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


def get_json_from_tickbarr(tickbarr: str):
    dicc_df = get_tickbar(tickbarr, "es", None)
    if dicc_df is None:
        print(f"Error: No se pudo obtener datos para el tickbarr {tickbarr}")
        return None

    first_json = make_json_from_dfs(dicc_df)
    if first_json is None:
        print(f"Error: No se pudo convertir datos a JSON para el tickbarr {tickbarr}")
        return None

    main_json = clean_relevant_json(json.loads(first_json))
    return main_json


def clean_relevant_json(json_data):
    with open('relevant_data.json', 'r', encoding='utf-8') as file:
        campos_por_clave = json.load(file)

    resultado = {}
    for clave_principal, campos_a_conservar in campos_por_clave.items():
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
    dicc_df = get_tickbar(tickbarr, "es", None)
    main_json = make_json_from_dfs(dicc_df)
    clean_json = clean_relevant_json(json.loads(main_json))
    # #print(clean_json)
    return clean_json


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