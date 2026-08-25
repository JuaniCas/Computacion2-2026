import multiprocessing
import time
import signal
import json
import os
import curses
from datetime import datetime

from procfs import listar_pids
from analizadores.resumen import loop_resumen
from analizadores.memoria import loop_memoria
from analizadores.fds import loop_fds
from analizadores.threads import loop_threads
from analizadores.senales import loop_senales
from analizadores.scheduling import loop_scheduling
from analizadores.sistema import loop_sistema
from display import iniciar_tui

# Variables globales para el manejo de señales en el main
procesos_hijos = []
snapshot_global = None
modo_verbose = multiprocessing.Value('b', False) # Variable compartida booleana para verbose
MAIN_PID = None #identificador del proceso principal

def manejador_senales(signum, frame):
    global procesos_hijos, snapshot_global, modo_verbose, MAIN_PID

    if os.getgid() != MAIN_PID:
        return
    
    if signum in (signal.SIGINT, signal.SIGTERM):
        # Liberamos la terminal de curses antes de imprimir o salir
        try:
            curses.endwin()
        except Exception:
            pass

        print("\n[Main] Señal de terminación recibida. Cerrando subprocesos...")
        for p in procesos_hijos:
            try:
                if p.is_alive():
                    p.terminate()
                    p.join(timeout=0.1)
            except Exception:
                pass
        print("[Main] Monitor cerrado limpiamente.")
        exit(0)
        
    elif signum == signal.SIGUSR1:
        # Dump del snapshot a JSON
        if snapshot_global is not None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_archivo = f"dump_{timestamp}.json"
            try:
                # Convertimos el diccionario proxy a un diccionario nativo para poder serializarlo
                datos_serializables = dict(snapshot_global)
                with open(nombre_archivo, 'w') as f:
                    json.dump(datos_serializables, f, indent=4)
                print(f"\n[Main] Dump guardado exitosamente en {nombre_archivo}")
            except Exception as e:
                print(f"\n[Main] Error al guardar el dump: {e}")
                
    elif signum == signal.SIGUSR2:
        # Toggle modo verbose
        modo_verbose.value = not modo_verbose.value
        estado = "ACTIVADO" if modo_verbose.value else "DESACTIVADO"
        print(f"\n[Main] Modo verbose {estado}")

def main():
    global procesos_hijos, snapshot_global, MAIN_PID
    MAIN_PID = os.getpid()

    manager = multiprocessing.Manager()
    snapshot_global = manager.dict()
    
    # Intervalos configurables por vista
    intervalos = manager.dict({
        "resumen": 2.0,
        "memoria": 2.0,
        "fds": 2.0,
        "threads": 2.0,
        "senales": 10.0,
        "scheduling": 10.0,
        "sistema": 2.0
    })

    # Instanciamos los procesos
    p_resumen = multiprocessing.Process(target=loop_resumen, args=(snapshot_global, intervalos), daemon=True)
    p_memoria = multiprocessing.Process(target=loop_memoria, args=(snapshot_global, intervalos), daemon=True)
    p_fds = multiprocessing.Process(target=loop_fds, args=(snapshot_global, intervalos), daemon=True)
    p_threads = multiprocessing.Process(target=loop_threads, args=(snapshot_global, intervalos), daemon=True)
    p_senales = multiprocessing.Process(target=loop_senales, args=(snapshot_global, intervalos), daemon=True)
    p_scheduling = multiprocessing.Process(target=loop_scheduling, args=(snapshot_global, intervalos), daemon=True)
    p_sistema = multiprocessing.Process(target=loop_sistema, args=(snapshot_global, intervalos), daemon=True)

    procesos_hijos = [p_resumen, p_memoria, p_fds, p_threads, p_senales, p_scheduling, p_sistema]

    # --- REGISTRO DE SEÑALES ---
    signal.signal(signal.SIGINT, manejador_senales)
    signal.signal(signal.SIGTERM, manejador_senales)
    signal.signal(signal.SIGUSR1, manejador_senales)
    signal.signal(signal.SIGUSR2, manejador_senales)

    # Lanzamos los procesos
    for p in procesos_hijos:
        p.start()

    # Iniciamos la interfaz gráfica TUI
    try:
        iniciar_tui(snapshot_global, intervalos)
    except Exception:
        pass
    finally:
        print("\n[Main] Cerrando monitor...")
        # Matamos de forma inmediata a los procesos hijos para que no alcancen a dar otra vuelta
        for p in procesos_hijos:
            try:
                p.terminate()
                p.kill() # Forzamos cierre inmediato
            except Exception:
                pass

if __name__ == "__main__":
    main()