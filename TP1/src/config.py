import json
import os

def cargar_intervalos(ruta_config="config.json"):
    """
    Lee el archivo de configuración y retorna un diccionario con los intervalos.
    Si falla, retorna valores por defecto.
    """
    defaults = {
        "resumen": 2.0,
        "memoria": 3.0,
        "fds": 5.0,
        "threads": 2.0,
        "senales": 10.0,
        "scheduling": 10.0,
        "sistema": 2.0
    }
    
    if not os.path.exists(ruta_config):
        return defaults

    try:
        with open(ruta_config, "r") as f:
            data = json.load(f)
            # Retornamos lo que hay en el JSON, o los defaults si falta algo
            return {k: data.get(k, defaults[k]) for k in defaults.keys()}
    except (json.JSONDecodeError, KeyError):
        return defaults