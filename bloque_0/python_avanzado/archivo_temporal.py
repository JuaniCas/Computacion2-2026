import os
from contextlib import contextmanager

@contextmanager
def archivo_temporal(nombre):
    """
    Context manager que crea un archivo temporal y lo borra al salir.
    """
    f = open(nombre, "w+")
    try:
        yield f  
    finally:
        f.close()
        if os.path.exists(nombre):
            os.remove(nombre)

if __name__ == "__main__":
    
    with archivo_temporal("test.txt") as f:
        f.write("Datos de prueba\n")
        f.write("Más datos\n")
        # Leer lo que escribimos
        f.seek(0)
        print(f.read())
    # Acá el archivo ya no existe

    # Verificar que realmente se borró
    assert not os.path.exists("test.txt")