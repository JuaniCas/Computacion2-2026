#!/usr/bin/env python3
import os

def obtener_procesos():
    procesos = {}

    for pid in os.listdir("/proc"):
        if pid.isdigit():
            try:
                with open(f"/proc/{pid}/status") as f:
                    nombre = ""
                    ppid = ""

                    for linea in f:
                        if linea.startswith("Name:"):
                            nombre = linea.split()[1]
                        elif linea.startswith("PPid:"):
                            ppid = linea.split()[1]

                    procesos[int(pid)] = {
                        "nombre": nombre,
                        "ppid": int(ppid)
                    }
            except:
                continue

    return procesos


def construir_arbol(procesos):
    arbol = {}

    for pid, info in procesos.items():
        ppid = info["ppid"]
        arbol.setdefault(ppid, []).append(pid)

    return arbol


def imprimir_arbol(arbol, procesos, pid=1, nivel=0):
    if pid not in procesos:
        return

    print("  " * nivel + f"{procesos[pid]['nombre']} ({pid})")

    for hijo in arbol.get(pid, []):
        imprimir_arbol(arbol, procesos, hijo, nivel + 1)


def main():
    procesos = obtener_procesos()
    arbol = construir_arbol(procesos)

    imprimir_arbol(arbol, procesos, pid=1)


if __name__ == "__main__":
    main()