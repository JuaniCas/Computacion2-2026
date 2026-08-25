#!/usr/bin/env python3
"""Lector de información de procesos desde /proc."""
import os
import sys

def obtener_info_proceso(pid):
    ruta_base = f"/proc/{pid}"
    
    if not os.path.exists(ruta_base):
        print(f"Error: El proceso {pid} no existe.")
        return

    print(f"--- Información del Proceso {pid} ---")

    try:
        with open(f"{ruta_base}/cmdline", "r") as f:
            cmd = f.read().replace('\0', ' ').strip()
            print(f"Comando (cmdline): {cmd if cmd else '[Kernel Process]'}")
    except Exception as e:
        print(f"No se pudo leer cmdline: {e}")

    try:
        print("\nEstado (status):")
        with open(f"{ruta_base}/status", "r") as f:
            for linea in f:

                if any(k in linea for k in ("State:", "PPid:", "VmRSS:", "Threads:")):
                    print(f"  {linea.strip()}")
    except Exception as e:
        print(f"No se pudo leer status: {e}")

    try:
        fds = os.listdir(f"{ruta_base}/fd")

        print(f"\nFile Descriptors abiertos: {len(fds)}")

        for fd in fds:
            ruta = os.readlink(f"{ruta_base}/fd/{fd}")
            print(f"  fd/{fd} -> {ruta}")
    except Exception as e:
        print(f"No se pudo acceder a /fd (permisos): {e}")

def main():
    if len(sys.argv) != 2:
        print(f"Uso: {sys.argv[0]} <PID>")

        sys.exit(1)

    obtener_info_proceso(sys.argv[1])

if __name__ == "__main__":
    main()