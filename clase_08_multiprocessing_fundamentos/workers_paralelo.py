#!/usr/bin/env python3

import multiprocessing
import random
import time

def worker(worker_id):
    # Generar un tiempo aleatorio entre 0.5 y 2.0 segundos
    duracion = random.uniform(0.5, 2.0)
    print(f"[Worker-{worker_id}] Iniciado. Dormirá {duracion:.2f}s...")
    time.sleep(duracion)
    print(f"[Worker-{worker_id}] Finalizado.")

if __name__ == "__main__":
    NUM_WORKERS = 5
    procesos = []

    # 1. Registrar el tiempo de inicio
    inicio = time.perf_counter()

    print(f"[PADRE] Lanzando {NUM_WORKERS} workers en paralelo...\n")

    # 2. Crear y arrancar todos los procesos
    for i in range(NUM_WORKERS):
        p = multiprocessing.Process(target=worker, args=(i + 1,))
        p.start()
        procesos.append(p)

    # 3. Esperar a que TODOS los procesos terminen
    for p in procesos:
        p.join()

    # 4. Registrar el tiempo final y calcular el total
    tiempo_total = time.perf_counter() - inicio

    print("\n" + "=" * 50)
    print(f"[PADRE] Todos los workers terminaron.")
    print(f"[PADRE] Tiempo total de ejecución: {tiempo_total:.2f} segundos")