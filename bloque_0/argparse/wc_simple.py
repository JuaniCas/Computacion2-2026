import sys
import os


def main():

    if len(sys.argv) < 2:
        print("Error: Debe especificar un archivo")

    nombre_archivo = sys.argv[1]

    if not os.path.exists(nombre_archivo):
        print(f"Error: No se puede leer {nombre_archivo}")
    
    archivo = open(nombre_archivo, "r")
    lineas = archivo.readlines()
    print(f"{len(lineas)} lineas")
    archivo.close()

if __name__ == "__main__":
    main()

