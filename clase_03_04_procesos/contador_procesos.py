#!/usr/bin/env python3
"""Contador de procesos leyendo /proc."""
import os

def contar_procesos():
    entradas = os.listdir('/proc')
    
    pids = [e for e in entradas if e.isdigit()]
    
    return len(pids)

def main():
    total = contar_procesos()
    print(f"Hay {total} procesos corriendo.")
    
if __name__ == "__main__":
    main()