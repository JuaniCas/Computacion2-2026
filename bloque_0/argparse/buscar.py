import argparse
import sys

def crear_parser():
    parser = argparse.ArgumentParser(description="Mini-grep: busca patrones en archivos o stdin.")
    
    parser.add_argument("patron", help="El texto o patrón a buscar")
    parser.add_argument("archivos", nargs="*", help="Archivos donde buscar")

    parser.add_argument("-i", "--ignore-case", action="store_true", help="Ignorar mayúsculas/minúsculas")
    parser.add_argument("-v", "--invert", action="store_true", help="Mostrar líneas que NO coinciden")
    parser.add_argument("-c", "--count", action="store_true", help="Solo mostrar el conteo de coincidencias")
    parser.add_argument("-n", "--line-number", action="store_true", help="Mostrar número de línea")

    return parser

def procesar_lineas(lineas, patron, args, nombre_fuente=None):
    coincidencias = 0
    lineas_resultado = []
    
    p = patron.lower() if args.ignore_case else patron

    for i, linea in enumerate(lineas, 1):
        linea_limpia = linea.rstrip('\n')
        contenido_busqueda = linea_limpia.lower() if args.ignore_case else linea_limpia
        
        existe = p in contenido_busqueda
        mostrar = (existe and not args.invert) or (not existe and args.invert)

        if mostrar:
            coincidencias += 1
            prefijo = ""
            if nombre_fuente:
                prefijo += f"{nombre_fuente}:"
            if args.line_number or (len(args.archivos) > 1 and not args.count):
                prefijo += f"{i}:"
            
            lineas_resultado.append(f"{prefijo}{linea_limpia}" if prefijo else linea_limpia)

    return coincidencias, lineas_resultado

def main():
    parser = crear_parser()
    args = parser.parse_args()
    total_general = 0

    if not args.archivos or not sys.stdin.isatty():
        if not args.archivos:
            cant, resultados = procesar_lineas(sys.stdin, args.patron, args)
            if args.count:
                print(f"{cant} coincidencias")
            else:
                for r in resultados: print(r)
            return

    for nombre in args.archivos:
        try:
            with open(nombre, 'r') as f:
                cant, resultados = procesar_lineas(f, args.patron, args, nombre)
                total_general += cant
                
                if args.count:
                    print(f"{nombre}: {cant} coincidencias")
                else:
                    for r in resultados: print(r)
        except Exception as e:
            print(f"Error al leer {nombre}: {e}", file=sys.stderr)

    if args.count and len(args.archivos) > 1:
        print(f"Total: {total_general} coincidencias")

if __name__ == "__main__":
    main()

