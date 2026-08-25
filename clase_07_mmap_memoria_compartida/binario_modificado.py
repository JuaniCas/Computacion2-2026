#!/usr/bin/env python3
"""Ejercicio 2: Estructura binaria de registros con mmap y struct."""
import mmap
import os
import struct

RUTA_ARCHIVO = "/tmp/registros.bin"
FORMATO = "i f 20s"  # int (id), float (nota), 20 bytes (nombre)
TAMAÑO_REGISTRO = struct.calcsize(FORMATO)  # 28 bytes
NUM_REGISTROS = 5
TAMAÑO_TOTAL = TAMAÑO_REGISTRO * NUM_REGISTROS

# Datos de prueba para los 5 registros
estudiantes = [
    (101, 8.5, "Juan Perez"),
    (102, 9.2, "Maria Gomez"),
    (103, 6.8, "Carlos Lopez"),
    (104, 10.0, "Ana Martinez"),
    (105, 7.4, "Lucas Rodriguez"),
]

# 1. Crear el archivo binario con el tamaño exacto requerido
with open(RUTA_ARCHIVO, "wb") as f:
    f.write(b"\x00" * TAMAÑO_TOTAL)

# 2. Mapear y escribir/leer los registros
with open(RUTA_ARCHIVO, "r+b") as f:
    mm = mmap.mmap(f.fileno(), TAMAÑO_TOTAL)

    print(
        f"Escribiendo {NUM_REGISTROS} registros (tamaño por registro: {TAMAÑO_REGISTRO} bytes)..."
    )
    for i, (est_id, nota, nombre) in enumerate(estudiantes):
        offset = i * TAMAÑO_REGISTRO
        # '20s' requiere que el texto esté codificado a bytes
        nombre_bytes = nombre.encode("utf-8")

        # Empaquetar y escribir directamente en la posición de memoria
        struct.pack_into(FORMATO, mm, offset, est_id, nota, nombre_bytes)
        print(f"  [Pos {i}] Escrito ID={est_id}, Nota={nota}, Nombre='{nombre}'")

    print("\n" + "=" * 50 + "\n")

    print("Leyendo registros desde memoria mapeada...")
    for i in range(NUM_REGISTROS):
        offset = i * TAMAÑO_REGISTRO

        # Desempaquetar los campos desde la posición de memoria
        est_id, nota, nombre_raw = struct.unpack_from(FORMATO, mm, offset)

        # Decodificar los bytes del string y quitar el relleno de ceros (null bytes)
        nombre = nombre_raw.decode("utf-8").rstrip("\x00")

        print(
            f"  [Registro {i}] ID: {est_id} | Nota: {nota:.1f} | Nombre: {nombre}"
        )

    # Modificación puntual: cambiar la nota del estudiante en el registro 3
    offset_reg3 = 3 * TAMAÑO_REGISTRO
    _, nota_actual, nom_raw = struct.unpack_from(FORMATO, mm, offset_reg3)
    struct.pack_into(
        FORMATO,
        mm,
        offset_reg3,
        104,
        9.8,
        nom_raw,  # Se mantiene el ID 104 y el mismo nombre en bytes
    )

    print(
        f"\n[Modificación] Registro 3 actualizado. Nueva nota: {struct.unpack_from(FORMATO, mm, offset_reg3)[1]:.1f}"
    )

    mm.close()

os.unlink(RUTA_ARCHIVO)