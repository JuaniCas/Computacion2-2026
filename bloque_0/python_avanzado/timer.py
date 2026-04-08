import time
from contextlib import contextmanager

class Timer:
    """Context Manager como clase para medir tiempo de ejecución."""
    def __init__(self, nombre=None):
        self.nombre = nombre
        self.inicio = None
        self.fin = None

    def __enter__(self):
        self.inicio = time.perf_counter()
        return self  

    @property
    def elapsed(self):
        """Calcula el tiempo transcurrido en tiempo real."""
        if self.fin is None:
            return time.perf_counter() - self.inicio
        return self.fin - self.inicio

    def __exit__(self, tipo_exc, valor_exc, traceback):
        self.fin = time.perf_counter()
        if self.nombre:
            print(f"[Timer] {self.nombre}: {self.elapsed:.3f}s")
        return False

class TimerData:
    def __init__(self):
        self.inicio = time.perf_counter()
        self.fin = None
    
    @property
    def elapsed(self):
        if self.fin is None:
            return time.perf_counter() - self.inicio
        return self.fin - self.inicio

@contextmanager
def timer_context(nombre=None):
    """Context Manager usando contextlib."""
    t = TimerData()
    try:
        yield t
    finally:
        t.fin = time.perf_counter()
        if nombre:
            print(f"[Timer] {nombre}: {t.elapsed:.3f}s")

if __name__ == "__main__":
    
    with Timer("Procesamiento de datos"):
        datos = [x**2 for x in range(1000000)]

    with Timer() as t:
        time.sleep(0.5)
    print(f"El bloque tardó {t.elapsed:.3f} segundos")

    with Timer() as t:
        time.sleep(0.2) 
        print(f"Después del paso 1: {t.elapsed:.3f}s")
        time.sleep(0.3) 
        print(f"Después del paso 2: {t.elapsed:.3f}s")