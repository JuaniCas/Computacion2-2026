#!/usr/bin/env python3

import multiprocessing
import os
import time

def tarea_hijo(nombre):
    print(f"[{nombre}] Hola desde el proceso hijo!")
    print(f"[{nombre}] PID hijo: {os.getpid()} | PID padre: {os.getppid()}")
    time.sleep(1)

if __name__ == "__main__":
    print(f"[PADRE] Proceso principal PID: {os.getpid()}")

    # 1. Crear el objeto Process especificando la función y sus argumentos
    p = multiprocessing.Process(target=tarea_hijo, args=("Worker-1",))

    # 2. Iniciar la ejecución del subproceso
    p.start()

    # 3. Esperar a que el subproceso termine
    p.join()

    print(f"[PADRE] El hijo (PID {p.pid}) terminó limpiamente con exitcode: {p.exitcode}")