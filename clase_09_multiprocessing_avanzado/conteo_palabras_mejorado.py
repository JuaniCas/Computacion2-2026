#!/usr/bin/env python3
"""Map-Reduce para conteo de palabras en archivos grandes (procesamiento por chunks)."""
from multiprocessing import Pool
from functools import reduce
import os

def mapper(texto):
    """Cuenta palabras en un texto (etapa map)."""
    conteo = {}
    for palabra in texto.lower().split():
        conteo[palabra] = conteo.get(palabra, 0) + 1
    return conteo

def reducer(dict1, dict2):
    """Combina dos diccionarios de conteo (etapa reduce)."""
    resultado = dict1.copy()
    for palabra, count in dict2.items():
        resultado[palabra] = resultado.get(palabra, 0) + count
    return resultado

def generador_chunks(ruta_archivo, lineas_por_chunk=1000):
    """Lee el archivo progresivamente desde el disco sin saturar la RAM."""
    with open(ruta_archivo, 'r', encoding='utf-8') as f:
        chunk = []
        for linea in f:
            chunk.append(linea)
            # Cuando el chunk llega al límite, se lo pasamos a un worker
            if len(chunk) >= lineas_por_chunk:
                yield " ".join(chunk)
                chunk = []
        # Si quedaron líneas residuales que no completaron un chunk, las enviamos al final
        if chunk:  
            yield " ".join(chunk)

def crear_archivo_prueba(ruta):
    """Helper: Crea un archivo pesado de prueba si no existe en el sistema."""
    texto_base = "el rapido zorro marron salta sobre el perro perezoso y el perro duerme bajo el arbol\n"
    with open(ruta, 'w', encoding='utf-8') as f:
        # Genera un archivo con 50,000 líneas para simular carga
        for _ in range(50000):  
            f.write(texto_base)

if __name__ == "__main__":
    archivo_prueba = "log_gigante.txt"
    
    # Preparamos el entorno de prueba
    if not os.path.exists(archivo_prueba):
        print(f"Creando archivo de prueba: {archivo_prueba}...")
        crear_archivo_prueba(archivo_prueba)

    conteo_total = {}

    print("Procesando archivo por chunks con Map-Reduce...")
    
    # Inicializamos el Pool de subprocesos
    with Pool(4) as pool:
        # imap_unordered va pidiendo chunks al generador bajo demanda y los reparte
        conteos_parciales = pool.imap_unordered(
            mapper, 
            generador_chunks(archivo_prueba, lineas_por_chunk=2000)
        )
        
        # Etapa Reduce: actualizamos el diccionario global al vuelo 
        # a medida que los workers van terminando sus chunks
        for conteo in conteos_parciales:
            conteo_total = reducer(conteo_total, conteo)
            
    # Ordenamiento analítico de mayor a menor frecuencia
    palabras_ordenadas = sorted(conteo_total.items(), key=lambda x: -x[1])

    print("\nTop palabras más frecuentes:")
    for palabra, count in palabras_ordenadas[:10]:
        print(f"  {palabra:15s} {count}")