#!/usr/bin/env python3

import multiprocessing
import time
import random

# Elemento centinela para avisar al consumidor que no habrá más datos
POISON_PILL = None

def productor(cola, num_items):
    """Genera datos y los coloca en la cola compartida."""
    print("[PRODUCTOR] Iniciado. Generando datos...")
    
    for i in range(num_items):
        item = f"Producto #{i + 1}"
        print(f"[PRODUCTOR] Colocando en cola: {item}")
        cola.put(item)
        time.sleep(random.uniform(0.1, 0.3))  # Simula tiempo de producción

    # Enviar la "píldora de veneno" para notificar el fin de la producción
    print("[PRODUCTOR] Finalizado. Enviando señal de fin (POISON_PILL)...")
    cola.put(POISON_PILL)

def consumidor(cola):
    """Lee datos de la cola y los procesa hasta recibir la señal de fin."""
    print("[CONSUMIDOR] Esperando datos...")
    
    while True:
        # q.get() se bloquea automáticamente hasta que haya un elemento disponible
        item = cola.get()
        
        # Verificar si recibimos la señal de parada
        if item is POISON_PILL:
            print("[CONSUMIDOR] Señal de fin recibida. Terminando proceso.")
            break

        print(f"  [CONSUMIDOR] Procesando: {item}")
        time.sleep(random.uniform(0.2, 0.4))  # Simula trabajo de procesamiento

if __name__ == "__main__":
    # 1. Crear la cola compartida
    cola_trabajo = multiprocessing.Queue()

    # 2. Crear los procesos
    p_prod = multiprocessing.Process(target=productor, args=(cola_trabajo, 10))
    p_cons = multiprocessing.Process(target=consumidor, args=(cola_trabajo,))

    # 3. Arrancar ambos procesos
    p_prod.start()
    p_cons.start()

    # 4. Esperar a que ambos terminen
    p_prod.join()
    p_cons.join()

    print("\n[PADRE] Flujo Productor-Consumidor completado con éxito.")