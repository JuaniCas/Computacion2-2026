import os
import signal
import pwd

def listar_pids():
    """Retorna una lista de PIDs activos."""
    pids = []
    try:
        for entrada in os.listdir('/proc'):
            if entrada.isdigit():
                pids.append(int(entrada))
    except FileNotFoundError:
        pass
    return pids

def parsear_stat(pid):
    """Lee /proc/<pid>/stat y retorna un diccionario con datos básicos."""
    ruta = f'/proc/{pid}/stat'
    try:
        with open(ruta, 'r') as f:
            linea = f.read().strip()
    except (FileNotFoundError, PermissionError):
        return None

    inicio_comm = linea.find('(')
    fin_comm = linea.rfind(')')
    
    if inicio_comm == -1 or fin_comm == -1:
        return None

    pid_str = linea[:inicio_comm - 1]
    comm = linea[inicio_comm + 1:fin_comm]
    resto = linea[fin_comm + 2:].split()

    try:
        return {
            'pid': int(pid_str),
            'comm': comm,
            'state': resto[0],       # Campo 3 (Estado: R, S, Z, etc.)
            'ppid': int(resto[1]),   # Campo 4
            'utime': int(resto[11]), # Campo 14
            'stime': int(resto[12])  # Campo 15
        }
    except IndexError:
        return None

def leer_cmdline(pid):
    """Lee /proc/<pid>/cmdline y retorna el comando completo."""
    ruta = f'/proc/{pid}/cmdline'
    try:
        with open(ruta, 'r') as f:
            contenido = f.read()
            if not contenido:
                return ""
            return contenido.replace('\x00', ' ').strip()
    except (FileNotFoundError, PermissionError):
        return ""

def leer_status_memoria(pid):
    """Lee /proc/<pid>/status y extrae VmSize, VmRSS y VmSwap."""
    ruta = f'/proc/{pid}/status'
    mem_data = {"VmSize": "0 kB", "VmRSS": "0 kB", "VmSwap": "0 kB"}
    try:
        with open(ruta, 'r') as f:
            for linea in f:
                if linea.startswith("VmSize:"):
                    mem_data["VmSize"] = linea.split()[1] + " kB"
                elif linea.startswith("VmRSS:"):
                    mem_data["VmRSS"] = linea.split()[1] + " kB"
                elif linea.startswith("VmSwap:"):
                    mem_data["VmSwap"] = linea.split()[1] + " kB"
    except (FileNotFoundError, PermissionError):
        pass
    return mem_data

def leer_fds(pid):
    """Lee /proc/<pid>/fd/ y retorna una lista con los destinos de los descriptores."""
    ruta = f'/proc/{pid}/fd'
    fds_abiertos = []
    try:
        for fd in os.listdir(ruta):
            try:
                destino = os.readlink(f"{ruta}/{fd}")
                fds_abiertos.append(f"{fd}->{destino}")
            except (FileNotFoundError, PermissionError):
                continue
    except (FileNotFoundError, PermissionError):
        pass
    return fds_abiertos

def leer_threads(pid):
    """Lee /proc/<pid>/task/ y extrae la lista de hilos (TIDs) con su estado."""
    ruta_task = f'/proc/{pid}/task'
    hilos = []
    try:
        for tid_str in os.listdir(ruta_task):
            if not tid_str.isdigit():
                continue
            tid = int(tid_str)
            
            # Buscamos el estado leyendo el archivo stat del hilo
            try:
                with open(f'{ruta_task}/{tid}/stat', 'r') as f:
                    linea = f.read().strip()
                    fin_comm = linea.rfind(')')
                    resto = linea[fin_comm + 2:].split()
                    estado = resto[0]
            except:
                estado = "N/A"
                
            # Buscamos los context switches en el archivo status
            vol, nonvol = 0, 0
            try:
                with open(f'{ruta_task}/{tid}/status', 'r') as f:
                    for l in f:
                        if l.startswith('voluntary_ctxt_switches:'):
                            vol = int(l.split()[1])
                        elif l.startswith('nonvoluntary_ctxt_switches:'):
                            nonvol = int(l.split()[1])
            except:
                pass
                
            hilos.append({
                'tid': tid,
                'estado': estado,
                'vol': vol,
                'nonvol': nonvol
            })
    except (FileNotFoundError, PermissionError):
        pass
    
    return hilos

def decodificar_mascara(mascara_hex):
    """Convierte una máscara hex de 64 bits a una lista de nombres de señales."""
    if not mascara_hex or mascara_hex == "0000000000000000" or mascara_hex == "0":
        return "-"
        
    try:
        mascara = int(mascara_hex, 16)
    except ValueError:
        return "-"
    
    nombres = []
    for sig in signal.Signals:
        if mascara & (1 << (sig.value - 1)):
            nombres.append(sig.name)
            
    return ", ".join(nombres) if nombres else "-"

def leer_senales(pid):
    """Lee /proc/<pid>/status y extrae las máscaras de señales decodificadas."""
    ruta = f'/proc/{pid}/status'
    senales = {'SigBlk': '-', 'SigIgn': '-', 'SigCgt': '-', 'SigPnd': '-', 'ShdPnd': '-'}
    try:
        with open(ruta, 'r') as f:
            for linea in f:
                if linea.startswith(('SigBlk:', 'SigIgn:', 'SigCgt:', 'SigPnd:', 'ShdPnd:')):
                    partes = linea.split()
                    if len(partes) == 2:
                        clave = partes[0][:-1] # Le sacamos los dos puntos ':' del final
                        senales[clave] = decodificar_mascara(partes[1])
    except (FileNotFoundError, PermissionError):
        pass
    return senales

def leer_scheduling(pid):
    """Lee /proc/<pid>/stat y status para extraer datos del scheduler."""
    datos = {
        'nice': 0, 'pri': 0, 'rtpri': 0, 'policy': 'OTHER', 
        'pgid': 0, 'sid': 0, 'utime': 0, 'stime': 0,
        'cpus': '-', 'vol': 0, 'nonvol': 0
    }
    
    try:
        with open(f'/proc/{pid}/stat', 'r') as f:
            linea = f.read().strip()
            fin_comm = linea.rfind(')')
            if fin_comm != -1:
                resto = linea[fin_comm + 2:].split()
                
                try:
                    datos['pgid'] = int(resto[2])
                    datos['sid'] = int(resto[3])
                    datos['utime'] = int(resto[11])
                    datos['stime'] = int(resto[12])
                    datos['pri'] = int(resto[15])
                    datos['nice'] = int(resto[16])
                    
                    if len(resto) > 38:
                        datos['rtpri'] = int(resto[37])
                        pol_num = int(resto[38])
                        politicas = {0: 'OTHER', 1: 'FIFO', 2: 'RR', 3: 'BATCH', 5: 'IDLE', 6: 'DEADLINE'}
                        datos['policy'] = politicas.get(pol_num, str(pol_num))
                except IndexError:
                    pass
    except:
        pass

    try:
        with open(f'/proc/{pid}/status', 'r') as f:
            for linea in f:
                if linea.startswith('Cpus_allowed_list:'):
                    datos['cpus'] = linea.split()[1]
                elif linea.startswith('voluntary_ctxt_switches:'):
                    datos['vol'] = int(linea.split()[1])
                elif linea.startswith('nonvoluntary_ctxt_switches:'):
                    datos['nonvol'] = int(linea.split()[1])
    except:
        pass

    return datos

def leer_sistema_global():
    """Lee estadísticas globales del sistema."""
    datos = {
        'uptime': 0.0, 'loadavg': 'N/A', 'btime': 0,
        'mem_total': '0', 'mem_free': '0', 'buffers': '0', 'cached': '0',
        'swap_total': '0', 'swap_free': '0', 'cpu_ticks': []
    }
    
    try:
        with open('/proc/uptime', 'r') as f:
            datos['uptime'] = float(f.read().split()[0])
    except: pass
    
    try:
        with open('/proc/loadavg', 'r') as f:
            partes = f.read().split()
            datos['loadavg'] = f"{partes[0]}, {partes[1]}, {partes[2]}"
    except: pass
    
    try:
        with open('/proc/meminfo', 'r') as f:
            for linea in f:
                if linea.startswith('MemTotal:'): datos['mem_total'] = linea.split()[1]
                elif linea.startswith('MemFree:'): datos['mem_free'] = linea.split()[1]
                elif linea.startswith('Buffers:'): datos['buffers'] = linea.split()[1]
                elif linea.startswith('Cached:'): datos['cached'] = linea.split()[1]
                elif linea.startswith('SwapTotal:'): datos['swap_total'] = linea.split()[1]
                elif linea.startswith('SwapFree:'): datos['swap_free'] = linea.split()[1]
    except: pass

    try:
        with open('/proc/stat', 'r') as f:
            for linea in f:
                if linea.startswith('cpu '):
                    # user, nice, system, idle, iowait
                    datos['cpu_ticks'] = [int(x) for x in linea.split()[1:6]]
                elif linea.startswith('btime '):
                    datos['btime'] = int(linea.split()[1])
    except: pass

    return datos

def leer_usuario(pid):
    """Obtiene el nombre de usuario dueño del proceso desde /proc/<pid>/status."""
    try:
        with open(f'/proc/{pid}/status', 'r') as f:
            for linea in f:
                if linea.startswith('Uid:'):
                    uid = int(linea.split()[1])
                    try:
                        return pwd.getpwuid(uid).pw_name
                    except KeyError:
                        return str(uid)
    except (FileNotFoundError, PermissionError):
        pass
    return "-"

def leer_uptime():
    """Lee el tiempo de actividad del sistema en segundos."""
    try:
        with open('/proc/uptime', 'r') as f:
            return float(f.read().split()[0])
    except:
        return 0.0

def leer_ticks_proceso(pid):
    """Lee los ticks (utime + stime) que consumió un proceso."""
    try:
        with open(f'/proc/{pid}/stat', 'r') as f:
            linea = f.read().strip()
            fin_comm = linea.rfind(')')
            if fin_comm != -1:
                resto = linea[fin_comm + 2:].split()
                # resto[11] es utime, resto[12] es stime
                return int(resto[11]) + int(resto[12])
    except:
        pass
    return 0