import time
import procfs

def loop_senales(snapshot, intervalos):
    """Proceso independiente que actualiza la vista 'senales'."""
    while True:
        intervalo = intervalos.get("senales", 10.0)
        nuevos_datos = {}
        pids = procfs.listar_pids()
        
        for pid in pids:
            stat = procfs.parsear_stat(pid)
            if not stat:
                continue
                
            senales = procfs.leer_senales(pid)
            
            nuevos_datos[pid] = {
                "pid": stat["pid"],
                "comm": stat["comm"],
                "senales": senales
            }
        
        snapshot["senales"] = nuevos_datos
        time.sleep(intervalo)