import time
import procfs

def loop_threads(snapshot, intervalos):
    """Proceso independiente que actualiza la vista 'threads'."""
    while True:
        intervalo = intervalos.get("threads", 2.0)
        nuevos_datos = {}
        pids = procfs.listar_pids()
        
        for pid in pids:
            stat = procfs.parsear_stat(pid)
            if not stat:
                continue
                
            hilos = procfs.leer_threads(pid)
            
            nuevos_datos[pid] = {
                "pid": stat["pid"],
                "comm": stat["comm"],
                "total_threads": len(hilos),
                "hilos": hilos
            }
        
        snapshot["threads"] = nuevos_datos
        time.sleep(intervalo)