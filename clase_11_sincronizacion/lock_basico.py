import threading
import time

lock = threading.Lock()

def operacion_critica(id):
    print(f"[{id}] Intentando adquirir el lock...")
    # Intentar adquirir con timeout de 5 segundos
    if lock.acquire(timeout=5.0):
        try:
            print(f"[{id}] Lock adquirido, ejecutando operación...")
            time.sleep(3)  # Trabajo dentro de la sección crítica
        finally:
            lock.release()
            print(f"[{id}] Lock liberado")
    else:
        print(f"[{id}] No se pudo adquirir el lock en 5 segundos")

# Lanzar 3 threads: el primero agarra, los otros dos esperan
hilos = [threading.Thread(target=operacion_critica, args=(i,)) for i in range(3)]
for h in hilos: h.start()
for h in hilos: h.join()