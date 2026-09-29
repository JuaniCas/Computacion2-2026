import threading
import time

lock = threading.Lock()

def operacion_no_bloqueante(id):
    if lock.acquire(blocking=False):
        try:
            print(f"[{id}] Lock disponible, ejecutando...")
            time.sleep(1)
        finally:
            lock.release()
    else:
        print(f"[{id}] Lock ocupado, haciendo otra cosa...")

# 5 threads compiten: solo uno entra, los demás siguen de largo
hilos = [threading.Thread(target=operacion_no_bloqueante, args=(i,)) for i in range(5)]
for h in hilos: h.start()
for h in hilos: h.join()