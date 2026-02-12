import schedule
import time
import datetime

#from uploadFile import upload_to_swarm
from oracle_tickbarrs import get_tickbarrs_yesterday
from save_hash_in_db import save_tickbarr_hash_to_db, save_failed_tickbarr

from get_tickbar_data import get_clean_json_from_tickbar
from hash_utils import generar_hash_unico
from upload_file import get_data_json, get_blockchain_hash


def up_tickbarr_to_swarm():
    #df = get_tickbarrs_yesterday().head(16)
    df = get_tickbarrs_yesterday()
    #print(df)

    # Iterar sobre las filas del DataFrame
    for index, row in df.iterrows():
        tickbarr = row['TTICKBARR']
        num_box = row['TNUMECAJA']
        code_esty_clie = row['TCODIESTICLIE']
        code_etiq_clie = row['TCODIETIQCLIE']
        code_tall = row['TCODITALL']

        data_json = get_clean_json_from_tickbar(tickbarr)
        mi_hash = generar_hash_unico(data_json)
        blockchain_hash = get_blockchain_hash(mi_hash)
        data_columns = get_data_json(tickbarr)
        print(mi_hash)

        try:
            save_tickbarr_hash_to_db(tickbarr, data_columns['caja'], code_esty_clie, code_etiq_clie, data_columns['talla'], hash, data_columns['cod_cliente'], data_columns['cliente'], data_columns['tipo_prenda'], data_columns['edad'], data_columns['genero'], data_columns['destino'], data_columns['tipo_tejido'], mi_hash)
            print(f"✓ Tickbarr {tickbarr} procesado exitosamente")
        except Exception as e:
            # Si falla, guardar el error y continuar con el siguiente
            save_failed_tickbarr(tickbarr, str(e))
            print(f"✗ Error en tickbarr {tickbarr}, continuando con el siguiente...")

def run_program_at_scheduled_time(stamp, scheduled_time="05:00"):
    schedule.every().day.at(scheduled_time).do(up_tickbarr_to_swarm, stamp=stamp)
    print(f"Programa programado para ejecutarse diariamente a las {scheduled_time}.")
    while True:
        try:
            schedule.run_pending()
            print("Esperando la siguiente ejecución programada...", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            time.sleep(59)  # Esperar un minuto antes de verificar nuevamente
        except KeyboardInterrupt:
            print("\nPrograma terminada por el usuario")
            break

#run_program_at_scheduled_time("51179dfdae435f60e8b1a127cd7364ef560a6873d04ad2830e24630bff815d2e", "09:57")
up_tickbarr_to_swarm()