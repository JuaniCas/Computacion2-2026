import sys

def main():

    total = 0

    for arg in sys.argv[1:]:
        try:
            total += float(arg)
        except ValueError:
            print(f"Advertencia: '{arg}' no es un número válido y se omitirá.")
            continue
    
    if total.is_integer():
        print(f"La suma total es: {int(total)}")
    else:
        print(f"La suma total es: {total}")

if __name__ == "__main__":
    main()

