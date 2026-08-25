import time
import procfs

def loop_fds(snapshot, intervalos):
    """Proceso independiente que actualiza la vista 'fds'."""
    while True:
        intervalo = intervalos.get("fds", 5.0)
        nuevos_datos = {}
        pids = procfs.listar_pids()
        
        for pid in pids:
            stat = procfs.parsear_stat(pid)
            if not stat:
                continue
                
            fds = procfs.leer_fds(pid)
            
            nuevos_datos[pid] = {
                "pid": stat["pid"],
                "comm": stat["comm"],
                "total_fds": len(fds),
                "ejemplos": fds[:4]
            }
        
        snapshot["fds"] = nuevos_datos
        time.sleep(intervalo)