import sys

if len(sys.argv) != 2:
    print("Uso: python3 mi_tee.py archivo.txt")
    sys.exit(1)

archivo = sys.argv[1]

with open(archivo, "a") as f:  # append como tee real
    for linea in sys.stdin:
        sys.stdout.write(linea)  # mostrar en pantalla
        f.write(linea)           # guardar en archivo