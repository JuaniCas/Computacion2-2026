import functools
from datetime import datetime

def log_llamada(funcion):
    """
    Decorador que registra el tiempo, los argumentos y el retorno de una función.
    """
    @functools.wraps(funcion)
    def wrapper(*args, **kwargs):
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        args_repr = [repr(a) for a in args]
        kwargs_repr = [f"{k}={repr(v)}" for k, v in kwargs.items()]
        todos_los_args = ", ".join(args_repr + kwargs_repr)
        
        print(f"[{timestamp}] Llamando a {funcion.__name__}({todos_los_args})")
        
        resultado = funcion(*args, **kwargs)
        
        print(f"[{timestamp}] {funcion.__name__} retornó {repr(resultado)}")
        
        return resultado
    return wrapper

# --- Ejemplo de uso del profesor ---

@log_llamada
def sumar(a, b):
    return a + b

@log_llamada
def saludar(nombre, entusiasta=False):
    sufijo = "!" if entusiasta else "."
    return f"Hola, {nombre}{sufijo}"

if __name__ == "__main__":
    resultado = sumar(3, 5)
    saludar("Ana", entusiasta=True)