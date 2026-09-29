#!/usr/bin/env python3
"""Filósofos comensales: del deadlock a la solución."""

import threading
import time
import random

NUM = 5
COMIDAS = 3


# ============================================================
# PARTE A: VERSIÓN INGENUA - PRODUCE DEADLOCK
# ============================================================

tomaron_izq = threading.Barrier(NUM)


def filosofo_ingenuo(id, tenedores):
    for _ in range(COMIDAS):
        izq = id
        der = (id + 1) % NUM

        with tenedores[izq]:
            # Esperamos a que los 5 tengan su tenedor izquierdo.
            # Esto fuerza el escenario de deadlock.
            tomaron_izq.wait()

            # Todos intentan obtener el tenedor derecho,
            # pero cada uno está siendo utilizado por otro filósofo.
            with tenedores[der]:
                print(f"[Ingenuo] Filósofo {id} come")


def ejecutar_ingenua():
    print("\n===== PARTE A: VERSIÓN INGENUA =====")

    tenedores = [threading.Lock() for _ in range(NUM)]

    threads = []

    for i in range(NUM):
        t = threading.Thread(
            target=filosofo_ingenuo,
            args=(i, tenedores)
        )
        threads.append(t)

    for t in threads:
        t.start()

    for t in threads:
        t.join(timeout=3)

    if any(t.is_alive() for t in threads):
        print("DEADLOCK: los filósofos quedaron bloqueados.")
    else:
        print("Todos terminaron.")


# ============================================================
# PARTE B: JERARQUÍA DE RECURSOS
# ============================================================

def filosofo_jerarquia(id, tenedores, estadisticas):
    for _ in range(COMIDAS):
        izq = id
        der = (id + 1) % NUM

        # IMPORTANTE:
        # Se ordenan los ÍNDICES, no los Locks.
        primero = min(izq, der)
        segundo = max(izq, der)

        inicio_espera = time.perf_counter()

        with tenedores[primero]:
            with tenedores[segundo]:

                fin_espera = time.perf_counter()
                estadisticas[id]["espera"] += fin_espera - inicio_espera

                print(
                    f"[Jerarquía] Filósofo {id} come "
                    f"(tenedores {primero}, {segundo})"
                )

                time.sleep(random.uniform(0.05, 0.15))

        time.sleep(random.uniform(0.05, 0.15))


def ejecutar_jerarquia():
    print("\n===== PARTE B: JERARQUÍA DE RECURSOS =====")

    tenedores = [threading.Lock() for _ in range(NUM)]

    estadisticas = {
        i: {
            "comidas": 0,
            "espera": 0.0
        }
        for i in range(NUM)
    }

    inicio = time.perf_counter()

    threads = []

    for i in range(NUM):
        t = threading.Thread(
            target=filosofo_jerarquia,
            args=(i, tenedores, estadisticas)
        )
        threads.append(t)

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    fin = time.perf_counter()

    print("\nTodos terminaron.")
    print(f"Tiempo total: {fin - inicio:.4f} segundos")

    for i in range(NUM):
        print(
            f"Filósofo {i}: "
            f"comidas={COMIDAS}, "
            f"tiempo de espera={estadisticas[i]['espera']:.4f}s"
        )


# ============================================================
# PARTE C: SEMÁFORO N-1
# ============================================================

def filosofo_semaforo(id, tenedores, comensales, estadisticas):
    for _ in range(COMIDAS):

        inicio_espera = time.perf_counter()

        # Como máximo NUM - 1 filósofos pueden intentar
        # adquirir tenedores al mismo tiempo.
        with comensales:

            izq = id
            der = (id + 1) % NUM

            with tenedores[izq]:
                with tenedores[der]:

                    fin_espera = time.perf_counter()
                    estadisticas[id]["espera"] += (
                        fin_espera - inicio_espera
                    )

                    print(
                        f"[Semaphore] Filósofo {id} come "
                        f"(tenedores {izq}, {der})"
                    )

                    time.sleep(random.uniform(0.05, 0.15))

        time.sleep(random.uniform(0.05, 0.15))


def ejecutar_semaforo():
    print("\n===== PARTE C: SEMÁFORO N-1 =====")

    tenedores = [threading.Lock() for _ in range(NUM)]

    # Como NUM = 5, permitimos como máximo 4 filósofos.
    comensales = threading.Semaphore(NUM - 1)

    estadisticas = {
        i: {
            "comidas": 0,
            "espera": 0.0
        }
        for i in range(NUM)
    }

    inicio = time.perf_counter()

    threads = []

    for i in range(NUM):
        t = threading.Thread(
            target=filosofo_semaforo,
            args=(i, tenedores, comensales, estadisticas)
        )
        threads.append(t)

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    fin = time.perf_counter()

    print("\nTodos terminaron.")
    print(f"Tiempo total: {fin - inicio:.4f} segundos")

    for i in range(NUM):
        print(
            f"Filósofo {i}: "
            f"comidas={COMIDAS}, "
            f"tiempo de espera={estadisticas[i]['espera']:.4f}s"
        )


# ============================================================
# PARTE D: COMPARACIÓN
# ============================================================

def main():
    # --------------------------------------------------------
    # PARTE A
    # --------------------------------------------------------
    # OJO: esta función está diseñada para quedarse bloqueada.
    # Si la ejecutamos junto con las demás, el programa no
    # avanzaría hasta que termine el timeout.
    #
    # Para probarla:
    # ejecutar_ingenua()
    #
    # Luego presionar Ctrl+C.
    # --------------------------------------------------------

    ejecutar_jerarquia()
    ejecutar_semaforo()


if __name__ == "__main__":
    main()


# ¿Por qué la Barrier convierte un deadlock esporádico en uno seguro?
# En condiciones normales, la velocidad dispar de la CPU hace que algún filósofo agarre ambos tenedores y termine de comer antes de que el último siquiera intente tomar el suyo. La Barrier congela la ejecución forzando el peor escenario de entrelazado (interleaving): obliga a que los cinco tomen su tenedor izquierdo simultáneamente antes de que cualquiera pueda pedir el derecho.

# ¿Cuál condición de Coffman rompe la solución del semáforo?
# Rompe la espera circular. Al restringir la mesa a 4 filósofos para 5 tenedores, es físicamente imposible cerrar un ciclo de dependencias donde todos estén esperando indefinidamente por el vecino; siempre habrá al menos un filósofo con ambos tenedores disponibles.

# Si un filósofo come menos veces que los demás, ¿es deadlock o starvation?
# Es starvation (inanición). El deadlock es un bloqueo total y permanente de todo el sistema (nadie avanza). La inanición ocurre cuando el sistema continúa funcionando y progresando, pero un hilo en particular es postergado indefinidamente por falta de equidad en la asignación de recursos.