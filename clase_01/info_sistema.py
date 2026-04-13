import os
import sys
import platform
import multiprocessing

def mostrar_info():
    print("="*40)
    print("INFO DEL SISTEMA")
    print("="*40)

    print(f"Version de Python: {platform.python_version()}")

    print(f"SO: {platform.system()} ({platform.node()})")

    print(f"CPUs disponibles: {multiprocessing.cpu_count()}")

    try:

        with open('/proc/meminfo', 'r') as f:
            lines = f.readlines()
            for line in lines:
                if "MemAvailable" in line or "MemTotal" in line:
                    print(f"Memoria: {line.strip()}")
    except FileNotFoundError:
        print("Memoria: No disponible")

    print("\n Variables de entorno 'PYTHON*':")
    env_vars = {k: v for k, v in os.environ.items() if k.startswith("PYTHON")}
    if env_vars:
        for k, v in env_vars.items():
            print(f"   {k}={v}")
    else:
        print("   (Ninguna encontrada)")
    print("="*40)

if __name__ == "__main__":
    mostrar_info()