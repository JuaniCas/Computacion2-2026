import threading

# Semaphore: no chequea
sem = threading.Semaphore(2)
sem.release()  # OK, contador = 3 (¡error silencioso!)
print(f"Semaphore contador: ahora {sem._value}")

# BoundedSemaphore: lanza ValueError
bsem = threading.BoundedSemaphore(2)
try:
    bsem.release()  # Excede el valor inicial
except ValueError as e:
    print(f"BoundedSemaphore detectó el error: {e}")