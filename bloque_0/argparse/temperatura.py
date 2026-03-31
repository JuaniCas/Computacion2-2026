import argparse
import sys

def crear_parser():
    parser = argparse.ArgumentParser(description="convierte temperaturas entre Celsius y Fahrenheit")
    parser.add_argument("valor", type=float, help="Temperatura a convertir")
    parser.add_argument("-t", "--to", required=True, choices=["celsius", "fahrenheit"], help="Unidad de destino")
    return parser

def convertir (valor, destino):
    if destino == "celsius":
        resultado = (valor - 32) * 5/9
        print (f"{valor}°F = {round(resultado, 2)}°C")
    else:
        resultado = (valor * 9/5) + 32
        print (f"{valor}°C = {round(resultado, 2)}°F")
    return True

def main():
    parser = crear_parser()
    args = parser.parse_args()
    
    try:
        convertir(args.valor, args.to)
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()