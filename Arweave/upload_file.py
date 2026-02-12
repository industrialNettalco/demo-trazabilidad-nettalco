import requests
import json
from get_tickbar_data import get_json_from_tickbarr  # Tu función que obtiene el JSON

def get_data_json(tickbarr: str):
    # Configuración
    # bee_api_url = "http://localhost:1633"  # URL de tu nodo Bee
    # batch_id = batch_stamp  # Tu lote de postage

    # Obtener el JSON desde la función
    json_data = get_json_from_tickbarr(tickbarr)  # Esta función debe devolver un diccionario en Python

    # Subir el JSON a Swarm
    # response = requests.post(
    #     f"{bee_api_url}/bzz",
    #     headers={
    #         "swarm-postage-batch-id": batch_id,
    #         "Content-Type": "application/json"  # Asegura que se visualice en el navegador
    #     },
    #     data=json_data  # Pasamos directamente el JSON como string
    # )

    index_dicc = {}
    data = json.loads(json_data)

    index_dicc['cod_cliente'] = data['tztotrazwebinfo'][0]['TCODICLIE']
    index_dicc['cliente'] = data['tztotrazwebinfo'][0]['TNOMBCLIE']
    index_dicc['etiq_cliente'] = data['tztotrazwebinfo'][0]['TDESCETIQCLIE']
    index_dicc['talla'] = data['tztotrazwebinfo'][0]['TCODITALL']
    index_dicc['tipo_prenda'] = data['tztotrazwebinfo'][0]['TDESCTIPOPREN']
    index_dicc['edad'] = data['tztotrazwebinfo'][0]['TDESCEDAD']
    index_dicc['genero'] = data['tztotrazwebinfo'][0]['TDESCGENE']
    index_dicc['caja'] = data['tztotrazwebalma'][0]['TNUMECAJA']
    index_dicc['destino'] = data['tztotrazwebalma'][0]['TDESCDEST']
    index_dicc['tipo_tejido'] = data['tztotrazwebteje'][0]['TDESCTIPOTEJI']

    #print(index_dicc)

    # Verificar la respuesta
    try:
        # response_data = response.json()
        # swarm_hash = response_data["reference"]
        # print("Subido Correctamente.")
        # print("Tickbarr:", tickbarr)
        # print("Hash Swarm:", swarm_hash)
        return index_dicc
    except requests.exceptions.JSONDecodeError:
        print("Error: la respuesta no contiene JSON válido. Respuesta completa:", response.text)


def get_blockchain_hash(hash):
    conn = connect_db_telas()
    if conn:
        try:
            query = "SELECT ttickbarr FROM apdobloctrazhashtemp WHERE thashinte = :1"
            df = pd.read_sql(query, conn, params=(hash, ))
            if not df.empty:
                return df
            else:
                return pd.DataFrame()
        except Exception as e:
            print("error obteniendo valores de prisma:", e)
            return pd.DataFrame()
        finally:
            conn.close()

#print(query_aldo("prueba"))
#dicc, swarm_hash = upload_to_swarm("089744701145", "2403c0c5e09cc8c3c8a7bb4daebe5a7ab74bd861a91f58a1eeeb57e58b93e59c")