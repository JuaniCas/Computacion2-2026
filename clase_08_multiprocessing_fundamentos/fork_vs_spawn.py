#!/usr/bin/env python3

import multiprocessing
import time

def tarea_vacia():
    """Una función rápida que no hace nada para aislar el overhead de creación."""
    pass

def medir_creacion(metodo, num_procesos):
    # Obtenemos el contexto específico ('fork' o 'spawn')
    ctx = multiprocessing.get_context(metodo)
    procesos = []

    inicio = time.perf_counter()

    # 1. Crear y arrancar N procesos
    for _ in range(num_procesos):
        p = ctx.Process(target=tarea_vacia)
        p.start()
        procesos.append(p)

    # 2. Esperar a que todos terminen
    for p in procesos:
        p.join()

    fin = time.perf_counter()
    return fin - inicio

if __name__ == "__main__":
    NUM_PROCESOS = 100

    print(f"=== Creando y destruyendo {NUM_PROCESOS} procesos en Linux ===\n")

    # Medir 'fork'
    tiempo_fork = medir_creacion("fork", NUM_PROCESOS)
    print(f"[FORK]  Tiempo total: {tiempo_fork:.4f} segundos")

    # Medir 'spawn'
    tiempo_spawn = medir_creacion("spawn", NUM_PROCESOS)
    print(f"[SPAWN] Tiempo total: {tiempo_spawn:.4f} segundos")

    # Comparación
    if tiempo_fork > 0:
        veces_mas_lento = tiempo_spawn / tiempo_fork
        print(f"\nResultado: 'spawn' fue aproximadamente {veces_mas_lento:.1f} veces más lento que 'fork'.")