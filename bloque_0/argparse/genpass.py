import argparse
import secrets
import string
import sys

def crear_parser():
    parser = argparse.ArgumentParser(description='Generador de contraseñas seguras.')

    parser.add_argument("-n", "--length", type=int, default=12, help="Longitud de la contraseña (por defecto: 12)")

    parser.add_argument("--no-symbols", action="store_true", help="Excluir símbolos especiales de la contraseña")

    parser.add_argument("--no-numbers", action="store_true", help="Excluir números de la contraseña")

    parser.add_argument("--count", type=int, default=1, help="Número de contraseñas a generar (por defecto: 1)")

    return parser

def generar_password(longitud, usar_simbolos, usar_numeros):
    caracteres = string.ascii_letters
    
    if usar_numeros:
        caracteres += string.digits
    
    if usar_simbolos:
        caracteres += "!@#$%&*"

    password = "".join(secrets.choice(caracteres) for _ in range(longitud))
    return password

def main():
    parser = crear_parser()
    args = parser.parse_args()

    if args.length < 1:
        print("Error: La longitud de la contraseña debe ser al menos 1.", file=sys.stderr)
        sys.exit(1)

    for _ in range(args.count):
        password = generar_password(args.length, not args.no_symbols, not args.no_numbers)
        print(password)

if __name__ == "__main__":
    main()

