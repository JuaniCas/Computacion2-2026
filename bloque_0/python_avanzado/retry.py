import time
import random
import functools

def retry(max_attempts=3, delay=1, exceptions=(Exception,)):
    """
    Decorador que reintenta una función si lanza las excepciones especificadas.
    """
    def decorador(funcion):
        @functools.wraps(funcion)
        def wrapper(*args, **kwargs):
            ultima_excepcion = None
            
            for intento in range(1, max_attempts + 1):
                try:
                    return funcion(*args, **kwargs)
                except exceptions as e:
                    ultima_excepcion = e

                    if intento < max_attempts:
                        print(f"Intento {intento}/{max_attempts} falló: {e}. Esperando {delay}s...")
                        time.sleep(delay)
                    else:
                        print(f"Intento {intento}/{max_attempts} falló: {e}.")
            
            # Si agotó los intentos, lanza la última excepción capturada
            raise ultima_excepcion
            
        return wrapper
    return decorador

if __name__ == "__main__":
    
    @retry(max_attempts=3, delay=1, exceptions=(ConnectionError,))
    def conectar_servidor():
        if random.random() < 0.7:
            raise ConnectionError("Servidor no disponible")
        return "Conectado exitosamente"

    try:
        resultado = conectar_servidor()
        print(f"Resultado final: {resultado}")
    except ConnectionError:
        print("Falló después de 3 intentos")