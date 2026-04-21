#!/usr/bin/env python3
"""Ejecutor de comandos en paralelo."""
import os
import sys
import time

def main():
    if len(sys.argv) < 2:
        print(f"Uso: {sys.argv[0]} comando1 [comando2 ...]")
        sys.exit(1)

    comandos_lista = sys.argv[1:]
    pids_activos = {} # Diccionario para rastrear {pid: comando_original}
    exitosos = 0
    fallidos = 0

    inicio = time.time()

    
    for cmd in comandos_lista:
        pid = os.fork()

        if pid == 0:
            
            partes = cmd.split()
            try:
                
                os.execvp(partes[0], partes)
            except OSError as e:
                print(f"Error al ejecutar '{cmd}': {e}")
                os._exit(1)
        else:
            
            print(f"[{pid}] Iniciado: {cmd}")
            pids_activos[pid] = cmd

    while pids_activos:

        pid_terminado, status = os.wait()
        
        if pid_terminado in pids_activos:
            cmd_nombre = pids_activos.pop(pid_terminado)
            codigo = os.WEXITSTATUS(status)
            
            print(f"[{pid_terminado}] Terminado: {cmd_nombre} (código: {codigo})")
            
            if codigo == 0:
                exitosos += 1
            else:
                fallidos += 1

    fin = time.time()

    print("\nResumen:")
    print(f"- Comandos ejecutados: {len(comandos_lista)}")
    print(f"- Exitosos: {exitosos}")
    print(f"- Fallidos: {fallidos}")
    print(f"- Tiempo total: {fin - inicio:.2f}s")

if __name__ == "__main__":
    main()

