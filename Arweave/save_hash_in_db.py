import pandas as pd
import os
import pymysql
import warnings

from dotenv import load_dotenv


# Cargar las variables de entorno
load_dotenv()

DB_USER = os.getenv("DB_PRENDAS_USER")
warnings.filterwarnings('ignore')

DB_PASSWORD = os.getenv("DB_PRENDAS_PASSWORD")
DB_HOST = os.getenv("DB_PRENDAS_HOST")
DB_PORT = int(os.getenv("DB_PRENDAS_PORT"))
DB_NAME = os.getenv("DB_PRENDAS_NAME")

db_config = {
    'host': DB_HOST,
    'port': DB_PORT,
    'user': DB_USER,
    'password': DB_PASSWORD,
    'database': DB_NAME,
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_general_ci'
}

def connect_to_my_db():
    try:
        conn = pymysql.connect(**db_config)
        return conn
    except Exception as e:
        print("falló al conectarse a la base de datos de MariaDB")
        return None

def get_version_from_same_tickbarr(tickbarr):
    conn = connect_to_my_db()
    if conn:
        try:
            query = "SELECT * FROM apdobloctrazhash WHERE TTICKBARR = %s"
            df = pd.read_sql(query, conn, params=(tickbarr,))
            if df.empty:
                return 1
            else:
                version = df['TNUMEVERS'].max() + 1
                return version
        except Exception as e:
            print(e)
            return 0
        
def get_version_from_same_tickbarr_error(tickbarr):
    conn = connect_to_my_db()
    if conn:
        try:
            query = "SELECT * FROM apdoblochasherror WHERE TTICKBARR = %s"
            df = pd.read_sql(query, conn, params=(tickbarr,))
            if df.empty:
                return 1
            else:
                version = df['TNUMEVERS'].max() + 1
                return version
        except Exception as e:
            print(e)
            return 0

def save_tickbarr_hash_to_db(tickbarr, num_box, code_esty_clie, code_etiq_clie, code_tall, hash, cod_clie, desc_clie, tipo_pren, edad, genero, destino, tipo_tejido, mi_hash):
    conn = connect_to_my_db()
    if conn:
        try:
            query = "INSERT INTO apdobloctrazhash (TTICKBARR, TNUMEVERS, TNUMECAJA, TESTICLIE, TETIQCLIE, TCODITALL, TTICKHASH, TCODICLIE, TDESCCLIE, TTIPOPREN, TTIPOEDAD, TTIPOGENE, TLUGADEST, TTIPOTEJI, THASHINTE) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            version = get_version_from_same_tickbarr(tickbarr)
            with conn.cursor() as cursor:
                cursor.execute(query, (tickbarr, version, num_box, code_esty_clie, code_etiq_clie, code_tall, hash, cod_clie ,desc_clie ,tipo_pren ,edad ,genero ,destino ,tipo_tejido, mi_hash))
            conn.commit()
            conn.close()
        except Exception as e:
            print(e)

def save_failed_tickbarr(tickbarr, error_message):
    conn = connect_to_my_db()
    if conn:
        try:
            query = "INSERT INTO apdoblochasherror (TTICKBARR, TNUMEVERS, TMENSERRO) VALUES (%s, %s, %s)"
            version = get_version_from_same_tickbarr_error(tickbarr)
            with conn.cursor() as cursor:
                cursor.execute(query, (tickbarr, version, error_message))
            conn.commit()
            conn.close()
        except Exception as e:
            print(e)

# df = pd.read_excel('Tickbarrs_small.xlsx')


# for i in range(len(df)):
#     tickbarr = '0' + str(df.loc[i, 'TTICKBARR'])
#     print("tickbarr:", tickbarr)
#     hash = upload_to_swarm(tickbarr, "742bfeab75365749b4a909f1bc384a06ae98a8cb9e9d2850aa4c3209bbdd4a0e")
#     save_tickbarr_hash_to_db(tickbarr, hash)
#     print(tickbarr, " : ", hash)

# Mostrar las primeras filas del DataFrame
#print(df)

#print(get_version_from_same_tickbarr("072936309633"))