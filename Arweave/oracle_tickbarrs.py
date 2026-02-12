import pandas as pd
import os
import cx_Oracle
from dotenv import load_dotenv
import warnings

# Cargar las variables de entorno
load_dotenv()
warnings.filterwarnings('ignore')

DBIN_USER = os.getenv("DBIN_USER")
DBIN_PASSWORD = os.getenv("DBIN_PASSWORD")
DBIN_HOST = os.getenv("DBIN_HOST")
DBIN_PORT = int(os.getenv("DBIN_PORT"))
DBIN_NAME = os.getenv("DBIN_NAME")

def connect_to_oracle_dbin():
    try:
        dsn = cx_Oracle.makedsn(DBIN_HOST, DBIN_PORT, sid=DBIN_NAME)
        conn = cx_Oracle.connect(user=DBIN_USER, password=DBIN_PASSWORD, dsn=dsn)
        return conn
    except Exception as e:
        print(f"Failed to connect to Oracle database: {e}")
        return None

def get_tickbarrs_yesterday():
    conn = connect_to_oracle_dbin()
    if conn:
        try:
            query = "SELECT TTICKBARR, TNUMECAJA, TCODIESTICLIE, TCODIETIQCLIE, TCODITALL FROM apdoprendas a WHERE trunc(a.tfechmovi) = trunc(sysdate - 1)"
            df = pd.read_sql(query, conn)
            if not df.empty:
                return df
            else:
                return pd.DataFrame()
        except Exception as e:
            print(e)
        finally:
            conn.close()

#print(get_tickbarrs_yesterday())
