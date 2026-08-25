#!/usr/bin/env python3

import multiprocessing
import time

def proceso_hijo(conn):
    """Proceso hijo: Recibe 'Ping' y responde con 'Pong'."""
    for i in range(5):
        # 1. El hijo se queda esperando recibir el "Ping" del padre
        mensaje_recibido = conn.recv()
        print(f"  [HIJO]  Recibió: '{mensaje_recibido}'")

        # 2. Responde al padre enviando el "Pong"
        respuesta = f"Pong #{i + 1}"

        print(f"  [HIJO]  Enviando: '{respuesta}'")
        conn.send(respuesta)

    # Buenas prácticas: cerrar la conexión al finalizar
    conn.close()

if __name__ == "__main__":
    # 1. Crear el Pipe. Retorna los dos extremos conectados: (extremo_1, extremo_2)
    padre_conn, hijo_conn = multiprocessing.Pipe()

    # 2. Le pasamos un extremo al hijo
    p = multiprocessing.Process(target=proceso_hijo, args=(hijo_conn,))
    p.start()

    print("=== Iniciando juego de Ping-Pong (5 rondas) ===\n")

    for i in range(5):
        mensaje = f"Ping #{i + 1}"
        print(f"[PADRE] Enviando: '{mensaje}'")
        
        # El padre envía su mensaje
        padre_conn.send(mensaje)

        # El padre espera a que el hijo le responda
        respuesta = padre_conn.recv()
        print(f"[PADRE] Recibió: '{respuesta}'\n")

        time.sleep(0.3)  # Pausa breve para apreciarlo en pantalla

    p.join()
    padre_conn.close()

    print("=== Juego terminado con éxito ===")