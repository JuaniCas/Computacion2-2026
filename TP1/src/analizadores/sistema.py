import time
import procfs

def loop_sistema(snapshot, intervalos):
    """Proceso independiente que actualiza la vista 'sistema'."""
    ticks_anteriores = None
    
    while True:
        intervalo = intervalos.get("sistema", 2.0)
        sys_data = procfs.leer_sistema_global()
        
        # Calcular % de CPU usando deltas
        cpu_pct = {"user": 0.0, "sys": 0.0, "idle": 0.0, "iowait": 0.0}
        ticks_actuales = sys_data.get('cpu_ticks')
        
        if ticks_actuales and ticks_anteriores:
            # deltas = [user, nice, system, idle, iowait]
            deltas = [actual - anterior for actual, anterior in zip(ticks_actuales, ticks_anteriores)]
            total_delta = sum(deltas)
            
            if total_delta > 0:
                cpu_pct['user'] = round((deltas[0] + deltas[1]) / total_delta * 100, 1)
                cpu_pct['sys'] = round(deltas[2] / total_delta * 100, 1)
                cpu_pct['idle'] = round(deltas[3] / total_delta * 100, 1)
                cpu_pct['iowait'] = round(deltas[4] / total_delta * 100, 1)
                
        ticks_anteriores = ticks_actuales
        sys_data['cpu_pct'] = cpu_pct
        
        resumen = snapshot.get("resumen", {})
        sys_data['total_procs'] = len(resumen)
        sys_data['zombies'] = sum(1 for p in resumen.values() if p.get('state') == 'Z')
        
        snapshot["sistema"] = sys_data
        time.sleep(intervalo)