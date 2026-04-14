import cowsay
import sys

mensaje = ' '.join(sys.argv[1:]) if len(sys.argv) > 1 else "Hola Docker! Este mensaje esta modificado n"
cowsay.cow(mensaje)