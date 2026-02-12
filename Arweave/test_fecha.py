import os
import pandas as pd
import cx_Oracle
from dotenv import load_dotenv

load_dotenv()

# Configuración Oracle (Copiada de tu script)
db_config_oracle = {
    'user': os.getenv("DBIN_USER"),
    'password': os.getenv("DBIN_PASSWORD"),
    'dsn': cx_Oracle.makedsn(os.getenv("DBIN_HOST"), int(os.getenv("DBIN_PORT")), os.getenv("DBIN_NAME"))
}

def connect_oracle():
    return cx_Oracle.connect(user=db_config_oracle['user'], password=db_config_oracle['password'], dsn=db_config_oracle['dsn'], encoding="UTF-8", nencoding="UTF-8")

def probar_consulta():
    print("🔌 Conectando a Oracle SOLO para probar la fecha...")
    
    # FECHA DE PRUEBA (Formato que usará el manager)
    fecha_test = "2026-01-29" 
    
    conn = connect_oracle()
    try:
        # Esta es la query exacta con el cambio TO_DATE y el formato YYYY-MM-DD
        query = f"""
            SELECT COUNT(*) as TOTAL
            FROM apdoprendas a 
            WHERE trunc(a.tfechmovi) = TO_DATE('{fecha_test}', 'YYYY-MM-DD')
        """
        
        print(f"\n🕵️ Enviando esta query a Oracle:\n{query}\n")
        
        df = pd.read_sql(query, conn)
        print("✅ ¡ÉXITO! Oracle respondió correctamente.")
        print(f"📊 Cantidad de prendas encontradas para {fecha_test}: {df.iloc[0]['TOTAL']}")
        
    except Exception as e:
        print(f"❌ ERROR: Oracle rechazó el formato. Detalle: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    probar_consulta()