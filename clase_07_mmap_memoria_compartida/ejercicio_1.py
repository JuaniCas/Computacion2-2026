#!/usr/bin/env python3
"""Ejercicio 1: Reemplazo de palabras en un archivo usando mmap."""
import mmap
import os

RUTA_ARCHIVO = "/tmp/ejercicio_mmap.txt"

# 1. Crear el archivo con 5 líneas de texto
lineas = [
    b"Linea 1: Iniciando el sistema operativo Linux.\n",
    b"Linea 2: Mapear archivos a memoria es rapido.\n",
    b"Linea 3: Usamos Python para sistemas oper.\n",
    b"Linea 4: La memoria compartida evita copias.\n",
    b"Linea 5: Finalizando prueba de mmap aqui.\n"
]

with open(RUTA_ARCHIVO, "wb") as f:
    f.writelines(lineas)

# 2. Mapear en modo lectura/escritura y realizar el reemplazo
PALABRA_ORIGINAL = b"Python"
PALABRA_NUEVA    = b"C++11 "  # Mismo largo: 6 bytes

with open(RUTA_ARCHIVO, "r+b") as f:
    # 0 indica mapear el archivo completo
    mm = mmap.mmap(f.fileno(), 0)

    print("=== Contenido Original en Memoria ===")
    print(mm[:].decode())

    # Buscar la posición de la palabra
    pos = mm.find(PALABRA_ORIGINAL)
    
    if pos != -1:
        print(f"Palabra '{PALABRA_ORIGINAL.decode()}' encontrada en el byte {pos}.")
        
        # Posicionar el puntero y sobrescribir los bytes exactos
        mm.seek(pos)
        mm.write(PALABRA_NUEVA)
        
        print("Reemplazo realizado con éxito.\n")
    else:
        print("Palabra no encontrada.")

    # Cerrar el mapeo
    mm.close()