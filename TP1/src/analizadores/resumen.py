import time
import procfs

def loop_resumen(snapshot, intervalos):
    """
    Proceso independiente que actualiza la vista 'resumen'.
    """
    print("[Resumen] Analizador iniciado...")

    historial_cpu = {}
    HERTZ = 100
    
    while True:
        # Obtenemos el intervalo actual desde el diccionario compartido
        intervalo = intervalos.get("resumen", 2.0)
        uptime_actual = procfs.leer_uptime()
        
        nuevos_datos = {}
        pids = procfs.listar_pids()
        
        for pid in pids:
            stat = procfs.parsear_stat(pid)
            if not stat:
                continue
                
            cmd = procfs.leer_cmdline(pid)
            usuario = procfs.leer_usuario(pid)

            ticks_actuales = procfs.leer_ticks_proceso(pid)
            cpu_pct = 0.0
            
            if pid in historial_cpu:
                ticks_ant, uptime_ant = historial_cpu[pid]
                delta_ticks = ticks_actuales - ticks_ant
                delta_segundos = uptime_actual - uptime_ant
                
                if delta_segundos > 0:
                    cpu_pct = 100.0 * (delta_ticks / HERTZ) / delta_segundos
            
            historial_cpu[pid] = (ticks_actuales, uptime_actual)
            
            # Armamos el diccionario para este proceso
            nuevos_datos[pid] = {
                "pid": stat["pid"],
                "ppid": stat["ppid"],
                "comm": stat["comm"],
                "state": stat["state"],
                "cmdline": cmd,
                "usuario": usuario,
                "cpu_pct": round(cpu_pct, 1),
            }

        # Limpiamos el historial de los procesos que ya murieron para no llenar la RAM
        pids_set = set(pids)
        historial_cpu = {k: v for k, v in historial_cpu.items() if k in pids_set}
        
        # Actualizamos el snapshot global de un solo golpe para evitar race conditions
        snapshot["resumen"] = nuevos_datos
        
        # Dormimos hasta el próximo ciclo
        time.sleep(intervalo)