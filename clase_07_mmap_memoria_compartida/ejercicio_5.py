#!/usr/bin/env python3
"""
Ejercicio 5: Cálculo paralelo con Array y Value compartidos (multiprocessing).
Calcula valores de seno en paralelo y demuestra la race condition al acumular.
"""
from multiprocessing import Process, Array, Value
import math
import time

# Constantes del problema
TAMAÑO_ARRAY = 100
NUM_PROCESOS = 4
CHUNK = TAMAÑO_ARRAY // NUM_PROCESOS  # 25 elementos por proceso

def worker_calculo(id_proc, array_compartido, valor_suma_compartido, inicio, fin):
    """
    Cada worker procesa un rango del Array y acumula su suma parcial
    en un Value compartido (sin sincronización, provocando race condition).
    """
    suma_local = 0.0

    for i in range(inicio, fin):
        # 1. Calcular el valor e insertarlo directamente en el Array compartido
        val = math.sin(i * 0.01)
        array_compartido[i] = val
        suma_local += val

        # 2. Intentar acumular inmediatamente en el Value compartido.
        #    ESTO CAUSA RACE CONDITION: '+= 1' o '+=' no es una operación atómica.
        valor_suma_compartido.value += val

    print(f"[Worker {id_proc}] Rango [{inicio:2d} - {fin:3d}] procesado. Suma local: {suma_local:.6f}")


def main():
    # 1. Crear estructuras de memoria compartida
    # 'd' representa tipo double (flotante de precisión doble, 8 bytes)
    array_senos = Array('d', TAMAÑO_ARRAY)
    suma_acumulada = Value('d', 0.0)

    print("=== Iniciando cálculo paralelo de senos (4 procesos) ===")
    
    procesos = []
    
    # 2. Crear y lanzar los 4 procesos
    for i in range(NUM_PROCESOS):
        ini = i * CHUNK
        fin = (i + 1) * CHUNK if i < NUM_PROCESOS - 1 else TAMAÑO_ARRAY
        
        p = Process(
            target=worker_calculo,
            args=(i, array_senos, suma_acumulada, ini, fin)
        )
        p.start()
        procesos.append(p)

    # 3. El padre espera a que todos los trabajadores terminen
    for p in procesos:
        p.join()

    # 4. Mostrar los primeros 20 resultados almacenados en el Array
    print("\n=== Primeros 20 resultados del Array ('d') ===")
    for i in range(20):
        print(f"  sin({i:2d} * 0.01) = {array_senos[i]:.6f}")

    # 5. Verificación del Bonus (Suma en Value compartido vs Suma Secuencial)
    suma_real_array = sum(array_senos)
    
    print("\n" + "=" * 55)
    print(f"Suma esperada (sumando el Array en el Padre): {suma_real_array:.10f}")
    print(f"Suma obtenida (acumulada en el Value):        {suma_acumulada.value:.10f}")
    
    diferencia = abs(suma_real_array - suma_acumulada.value)
    print(f"Diferencia (Pérdida por Race Condition):      {diferencia:.10f}")

if __name__ == "__main__":
    main()