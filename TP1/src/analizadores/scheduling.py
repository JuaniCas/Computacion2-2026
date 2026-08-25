import time
import procfs

def loop_scheduling(snapshot, intervalos):
    """Proceso independiente que actualiza la vista 'scheduling'."""
    while True:
        intervalo = intervalos.get("scheduling", 10.0)
        nuevos_datos = {}
        pids = procfs.listar_pids()
        
        for pid in pids:
            stat = procfs.parsear_stat(pid)
            if not stat:
                continue
                
            sched = procfs.leer_scheduling(pid)
            
            nuevos_datos[pid] = {
                "pid": stat["pid"],
                "comm": stat["comm"],
                "sched": sched
            }
        
        snapshot["scheduling"] = nuevos_datos
        time.sleep(intervalo)