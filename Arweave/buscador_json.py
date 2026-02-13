from get_tickbar_data import get_clean_json_from_tickbar, save_json_to_file, get_json_from_tickbarr

tickbarr="092708105033"
mi_json=get_clean_json_from_tickbar(tickbarr)

save_json_to_file(mi_json,"json_rescatados.json")

json_completo=get_json_from_tickbarr(tickbarr)

save_json_to_file(json_completo,"json_completo.json")
