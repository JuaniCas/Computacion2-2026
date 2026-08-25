import sys

bytes_total = 0
lineas_total = 0

for linea in sys.stdin:
    bytes_total += len(linea.encode())  # contar bytes reales
    lineas_total += 1

    sys.stdout.write(linea)  # dejar pasar el dato

# Mostrar estadísticas al final (IMPORTANTE: stderr)
print(f"Procesados {bytes_total} bytes, {lineas_total} líneas", file=sys.stderr)