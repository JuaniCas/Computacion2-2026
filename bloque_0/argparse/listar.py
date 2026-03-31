import argparse
import os
import sys

def crear_parser():
    parser = argparse.ArgumentParser(description="Listador de archivos estilo ls.")

    parser.add_argument("directorio", nargs="?", default=".", help="Directorio a listar (por defecto: directorio actual)")

    parser.add_argument("-a", "--all", action="store_true", help="Incluir archivos ocultos")

    parser.add_argument("--extension", help="Filtrar por extensión de archivo (ejemplo: .txt)")

    return parser

def listar_archivos(args):
    try:
        contenido = os.listdir(args.directorio)

    except FileNotFoundError:
        print(f"Error: El directorio '{args.directorio}' no existe.", file=sys.stderr)
        return False
    
    except PermissionError:
        print(f"Error: No tienes permiso para acceder al directorio '{args.directorio}'.", file=sys.stderr)
        return False
    
    contenido.sort()

    for item in contenido:
        if not args.all and item.startswith('.'):
            continue
        
        if args.extension and not item.endswith(args.extension):
            continue
        
        ruta_completa = os.path.join(args.directorio, item)
        if os.path.isdir(ruta_completa):
            print(f"{item}/")
        else:
            print(item)
    return True

def main():
    parser = crear_parser()
    args = parser.parse_args()
    
    if listar_archivos(args):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()