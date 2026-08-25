#!/usr/bin/env python3
"""
Ejercicio 3: Suma paralela por rangos usando mmap anónimo.
Múltiples procesos hijos calculan sumas parciales y las escriben en memoria compartida.
"""
import mmap
import os
import struct

NUM_HIJOS = 4
RANGO_POR_HIJO = 25  # Cada hijo procesa 25 números (1-25, 26-50, 51-75, 76-100)

FORMATO = "i i q"
TAMAÑO_REGISTRO = struct.calcsize(FORMATO)  # 16 bytes
TAMAÑO_TOTAL = NUM_HIJOS * TAMAÑO_REGISTRO

# 1. Crear el mmap anónimo (fileno = -1)
mm = mmap.mmap(-1, TAMAÑO_TOTAL)

hijos = []

for i in range(NUM_HIJOS):
    pid = os.fork()
    if pid == 0:
        # === PROCESO HIJO ===
        inicio = (i * RANGO_POR_HIJO) + 1
        fin = (i + 1) * RANGO_POR_HIJO

        # Calcular la suma parcial de su rango
        suma_parcial = sum(range(inicio, fin + 1))

        # Calcular el offset correspondiente en el mmap anónimo
        offset = i * TAMAÑO_REGISTRO

        # Escribir ID, PID y Suma Parcial en su región asignada
        struct.pack_into(FORMATO, mm, offset, i, os.getpid(), suma_parcial)

        # Finalizar el proceso hijo ordenadamente
        os._exit(0)
    else:
        # === PROCESO PADRE ===
        hijos.append(pid)

# El padre espera a que todos los procesos hijos finalicen
for pid in hijos:
    os.waitpid(pid, 0)

# === PROCESAMIENTO Y LECTURA DE RESULTADOS EN EL PADRE ===
print("=== Resultados parciales recibidos en el Padre ===")
suma_total = 0

for i in range(NUM_HIJOS):
    offset = i * TAMAÑO_REGISTRO
    hijo_id, hijo_pid, suma_parcial = struct.unpack_from(FORMATO, mm, offset)
    
    inicio = (i * RANGO_POR_HIJO) + 1
    fin = (i + 1) * RANGO_POR_HIJO
    
    print(
        f"  Hijo {hijo_id} (PID {hijo_pid}): "
        f"Rango [{inicio:2d} - {fin:3d}] -> Suma Parcial = {suma_parcial}"
    )
    suma_total += suma_parcial

print("\n" + "=" * 50)
print(f"Suma Total Calculada: {suma_total}")


mm.close()