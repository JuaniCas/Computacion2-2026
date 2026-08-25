import time
import procfs

def loop_memoria(snapshot, intervalos):
    """Proceso independiente que actualiza la vista 'memoria'."""
    while True:
        intervalo = intervalos.get("memoria", 3.0)
        nuevos_datos = {}
        pids = procfs.listar_pids()
        
        for pid in pids:
            stat = procfs.parsear_stat(pid)
            if not stat:
                continue
                
            mem = procfs.leer_status_memoria(pid)
            
            nuevos_datos[pid] = {
                "pid": stat["pid"],
                "comm": stat["comm"],
                "vmsize": mem["VmSize"],
                "vmrss": mem["VmRSS"],
                "vmswap": mem["VmSwap"]
            }
        
        snapshot["memoria"] = nuevos_datos
        time.sleep(intervalo)