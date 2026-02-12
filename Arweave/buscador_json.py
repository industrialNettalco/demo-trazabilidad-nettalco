from get_tickbar_data import get_clean_json_from_tickbar, save_json_to_file

mi_json=get_clean_json_from_tickbar("092746313179")

save_json_to_file(mi_json,"json_rescatados.json")