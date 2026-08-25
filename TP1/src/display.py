import curses

def mostrar_ayuda(stdscr, alto, ancho):
    """Dibuja un pop-up centrado con los atajos de teclado."""
    h_alto, h_ancho = 16, 65
    
    # Calculamos el centro de la pantalla
    start_y = max(0, (alto - h_alto) // 2)
    start_x = max(0, (ancho - h_ancho) // 2)
    
    win = curses.newwin(h_alto, h_ancho, start_y, start_x)
    win.box()
    win.addstr(0, 2, " AYUDA - Atajos de Teclado ", curses.A_BOLD | curses.A_REVERSE)
    
    lineas = [
        "[1 / r] : Vista Resumen",
        "[2 / m] : Vista Memoria",
        "[3 / f] : Vista File Descriptors",
        "[4 / t] : Vista Threads",
        "[5 / s] : Vista Señales",
        "[6 / p] : Vista Scheduling",
        "[7 / g] : Vista Sistema Global",
        "[ ↑/↓ ] : Navegar por la lista de procesos",
        "[Enter] : Fijar (Pin) el proceso seleccionado",
        "[  c  ] : Cambiar orden de la tabla (PID / Nombre)",
        "[ + / - ] : Acelerar o ralentizar la actualización",
        "[ / / u ] : Filtrar por comando o usuario",
        "[  q  ] : Salir del monitor"
    ]
    
    for i, linea in enumerate(lineas):
        if i + 2 < h_alto - 1:
            win.addstr(i + 2, 2, linea)
            
    win.addstr(h_alto - 2, 2, "Presiona cualquier tecla para cerrar...", curses.A_DIM)
    win.refresh()
    
    win.nodelay(False)
    win.getch()
    win.nodelay(True)

def leer_input(stdscr, prompt, alto, ancho):
    """Pausa la pantalla, muestra un prompt abajo de todo y lee lo que el usuario tipea."""
    curses.curs_set(1)
    stdscr.nodelay(False)
    
    stdscr.addstr(alto - 2, 0, " " * ancho, curses.A_REVERSE)
    stdscr.addstr(alto - 2, 0, prompt, curses.A_REVERSE)
    stdscr.refresh()
    
    texto = ""
    while True:
        try:
            tecla = stdscr.getkey()

            if tecla in ('\n', 'KEY_ENTER'): 
                break

            elif tecla == '\x1b': 
                texto = ""
                break

            elif tecla in ('KEY_BACKSPACE', '\b', '\x7f'): 
                texto = texto[:-1]

            elif len(tecla) == 1: 
                texto += tecla
                
            mostrar = f"{prompt}{texto}"
            stdscr.addstr(alto - 2, 0, " " * ancho, curses.A_REVERSE)
            stdscr.addstr(alto - 2, 0, mostrar[:ancho], curses.A_REVERSE)
            stdscr.refresh()
        except curses.error:
            pass

    curses.curs_set(0)
    stdscr.timeout(500)
    return texto

def loop_display(stdscr, snapshot, intervalos):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(500)
    stdscr.keypad(True)
    
    vista_actual = "resumen"
    desplazamiento = 0
    seleccion_idx = 0
    
    # Variables de estado para la interactividad
    modo_orden = "pid"
    pid_pineado = None
    filtro_cmd = ""
    filtro_usr = ""
    
    while True:
        stdscr.clear()
        alto, ancho = stdscr.getmaxyx()
        
        datos_resumen = snapshot.get("resumen", {})

        procesos_filtrados = []
        for p in datos_resumen.values():
            if filtro_cmd:
                comando = p.get('comm', '').lower()
                cmdline = p.get('cmdline', '').lower()
                if filtro_cmd.lower() not in comando and filtro_cmd.lower() not in cmdline:
                    continue
            if filtro_usr:
                usuario = p.get('usuario', '').lower()
                if filtro_usr.lower() not in usuario:
                    continue

            procesos_filtrados.append(p)

        #logica de ordenamiento 
        if modo_orden == "pid":
            procesos = sorted(procesos_filtrados, key=lambda x: x.get('pid', 0))
        elif modo_orden == "nombre":
            procesos = sorted(procesos_filtrados, key=lambda x: x.get('comm', '').lower())
        elif modo_orden == "cpu":
            procesos = sorted(procesos_filtrados, key=lambda x: x.get('cpu_pct', 0.0), reverse=True)
            
        total_procesos = len(procesos)
        
        # Lógica de Pin (mantener seleccionado el proceso fijado)
        if pid_pineado is not None:
            for i, p in enumerate(procesos):
                if p.get('pid') == pid_pineado:
                    seleccion_idx = i
                    if seleccion_idx < desplazamiento:
                        desplazamiento = seleccion_idx
                    elif seleccion_idx >= desplazamiento + (alto - 12):
                        desplazamiento = seleccion_idx - (alto - 12) + 1
                    break
        
        intervalo = intervalos.get(vista_actual, 2.0)
        
        # HEADER
        pin_texto = f" | PIN: {pid_pineado}" if pid_pineado else ""
        f_texto = ""
        if filtro_cmd: f_texto += f" | F:Cmd='{filtro_cmd}'"
        if filtro_usr: f_texto += f" | F:Usr='{filtro_usr}'"
        
        header = f"=== MONITOR TP1 | Vista: {vista_actual.upper()} | Upd: {intervalo:.1f}s | Ord: {modo_orden.upper()}{pin_texto}{f_texto} ==="
        stdscr.addstr(0, 0, header[:ancho], curses.A_REVERSE)
        
        # PANEL SUPERIOR
        if vista_actual != "sistema":

            alto_lista = alto - 12
            if alto_lista < 5: alto_lista = 5
        
            columnas = f"{'PID':<8} {'ESTADO':<8} {'PPID':<8} {'CPU%':<6} {'COMANDO'}"
            stdscr.addstr(2, 0, columnas[:ancho], curses.A_BOLD)
        
            fila_pantalla = 3
            for i in range(desplazamiento, min(desplazamiento + alto_lista, total_procesos)):
                p = procesos[i]
                texto = f"{p.get('pid', ''):<8} {p.get('state', ''):<8} {p.get('ppid', ''):<8} {p.get('cpu_pct', 0.0):<6} {p.get('comm', '')}"
            
                if p.get('pid') == pid_pineado:
                    stdscr.addstr(fila_pantalla, 0, texto[:ancho], curses.A_STANDOUT)
                elif i == seleccion_idx:
                    stdscr.addstr(fila_pantalla, 0, texto[:ancho], curses.A_REVERSE)
                else:
                    stdscr.addstr(fila_pantalla, 0, texto[:ancho])
                fila_pantalla += 1
            
            # SEPARADOR
            separador = "-" * ancho
            stdscr.addstr(fila_pantalla, 0, separador[:ancho])
            fila_panel_inf = fila_pantalla + 1
        
            # PANEL INFERIOR
            if total_procesos > 0 and seleccion_idx < total_procesos:
                pid_sel = procesos[seleccion_idx].get('pid')
                comm_sel = procesos[seleccion_idx].get('comm')
                
                stdscr.addstr(fila_panel_inf, 0, f"Detalle del PID {pid_sel} ({comm_sel}):", curses.A_BOLD)
                fila_panel_inf += 1
                
                if vista_actual == "resumen":
                    cmdline = procesos[seleccion_idx].get('cmdline', '')
                    stdscr.addstr(fila_panel_inf, 0, f"Cmdline : {cmdline}"[:ancho])
                elif vista_actual == "memoria":
                    datos_mem = snapshot.get("memoria", {}).get(pid_sel, {})
                    stdscr.addstr(fila_panel_inf, 0, f"VmSize  : {datos_mem.get('vmsize', 'N/A')}")
                    stdscr.addstr(fila_panel_inf+1, 0, f"VmRSS   : {datos_mem.get('vmrss', 'N/A')}")
                    stdscr.addstr(fila_panel_inf+2, 0, f"VmSwap  : {datos_mem.get('vmswap', 'N/A')}")
                elif vista_actual == "fds":
                    datos_fds = snapshot.get("fds", {}).get(pid_sel, {})
                    stdscr.addstr(fila_panel_inf, 0, f"Total FDs abiertos: {datos_fds.get('total_fds', 0)}")
                    for i, ej in enumerate(datos_fds.get('ejemplos', [])):
                        stdscr.addstr(fila_panel_inf + 1 + i, 2, f"- {ej}"[:ancho])
                elif vista_actual == "threads":
                    datos_thr = snapshot.get("threads", {}).get(pid_sel, {})
                    hilos = datos_thr.get('hilos', [])
                    
                    stdscr.addstr(fila_panel_inf, 0, f"Threads (LWPs): {len(hilos)} total:")
                    for i, h in enumerate(hilos):
                        if fila_panel_inf + 1 + i >= alto - 2:
                            break
                        
                        texto_hilo = f"  tid={h['tid']:<6} estado={h['estado']}  vol_ctx={h['vol']:<6} nonvol_ctx={h['nonvol']}"
                        stdscr.addstr(fila_panel_inf + 1 + i, 0, texto_hilo[:ancho])
                elif vista_actual == "senales":
                    datos_sig = snapshot.get("senales", {}).get(pid_sel, {}).get("senales", {})
                    stdscr.addstr(fila_panel_inf, 0, f"Señales bloqueadas (SigBlk) : {datos_sig.get('SigBlk', '-')}"[:ancho])
                    stdscr.addstr(fila_panel_inf+1, 0, f"Señales ignoradas  (SigIgn) : {datos_sig.get('SigIgn', '-')}"[:ancho])
                    stdscr.addstr(fila_panel_inf+2, 0, f"Señales capturadas (SigCgt) : {datos_sig.get('SigCgt', '-')}"[:ancho])
                    stdscr.addstr(fila_panel_inf+3, 0, f"Pendientes proceso (SigPnd) : {datos_sig.get('SigPnd', '-')}"[:ancho])
                    stdscr.addstr(fila_panel_inf+4, 0, f"Pendientes grupo   (ShdPnd) : {datos_sig.get('ShdPnd', '-')}"[:ancho])
                elif vista_actual == "scheduling":
                    datos_sch = snapshot.get("scheduling", {}).get(pid_sel, {}).get("sched", {})
                    
                    stdscr.addstr(fila_panel_inf, 0, f"Policy (POL) : {datos_sch.get('policy', '-')}")
                    stdscr.addstr(fila_panel_inf+1, 0, f"Priority (PRI): {datos_sch.get('pri', '-')} | Nice: {datos_sch.get('nice', '-')} | RT_Pri: {datos_sch.get('rtpri', '-')}")
                    stdscr.addstr(fila_panel_inf+2, 0, f"Afinidad CPU  : {datos_sch.get('cpus', '-')}")
                    stdscr.addstr(fila_panel_inf+3, 0, f"Context switch: {datos_sch.get('vol', '-')} voluntarios | {datos_sch.get('nonvol', '-')} involuntarios")
                    stdscr.addstr(fila_panel_inf+4, 0, f"Tiempos (jiff): user={datos_sch.get('utime', '-')} | sys={datos_sch.get('stime', '-')}")
                    stdscr.addstr(fila_panel_inf+5, 0, f"PGID / SID    : {datos_sch.get('pgid', '-')} / {datos_sch.get('sid', '-')}")
        else:
            datos_sys = snapshot.get("sistema", {})
            cpu = datos_sys.get('cpu_pct', {})
            
            stdscr.addstr(2, 0, "[INFO] Vista de Sistema Global", curses.A_BOLD)
            stdscr.addstr(4, 0, f"Procesos totales: {datos_sys.get('total_procs', 0)}")
            stdscr.addstr(5, 0, f"Procesos zombies: {datos_sys.get('zombies', 0)}")
            
            stdscr.addstr(7, 0, "--- MEMORIA ---", curses.A_BOLD)
            stdscr.addstr(8, 0, f"Total  : {datos_sys.get('mem_total', 'N/A')} kB")
            stdscr.addstr(9, 0, f"Libre  : {datos_sys.get('mem_free', 'N/A')} kB")
            stdscr.addstr(10, 0, f"Buffers: {datos_sys.get('buffers', 'N/A')} kB")
            stdscr.addstr(11, 0, f"Cached : {datos_sys.get('cached', 'N/A')} kB")
            
            stdscr.addstr(13, 0, "--- CPU & CARGA ---", curses.A_BOLD)
            stdscr.addstr(14, 0, f"Load Avg: {datos_sys.get('loadavg', 'N/A')}")
            stdscr.addstr(15, 0, f"Uptime  : {datos_sys.get('uptime', 0):.1f} s")
            stdscr.addstr(16, 0, f"User    : {cpu.get('user', 0.0)} %")
            stdscr.addstr(17, 0, f"System  : {cpu.get('sys', 0.0)} %")
            stdscr.addstr(18, 0, f"Idle    : {cpu.get('idle', 0.0)} %")
            stdscr.addstr(19, 0, f"IOWait  : {cpu.get('iowait', 0.0)} %")
        
        # FOOTER
        footer = "[1-7]/r/m/f/t/s/p/g Vistas | [↑/↓] Nav | [Enter] Pin | [c] Ord |[/] cmd [u] usr [x] limp | [+/-] Vel | [h/?] Ayuda | [q] Salir"
        stdscr.addstr(alto - 1, 0, footer[:ancho], curses.A_REVERSE)
        
        stdscr.refresh()
        
        # LEER TECLADO
        try:
            tecla = stdscr.getkey()
            if tecla == 'q':
                break
            elif tecla == '1' or tecla == 'r': vista_actual = "resumen"
            elif tecla == '2' or tecla == 'm': vista_actual = "memoria"
            elif tecla == '3' or tecla == 'f': vista_actual = "fds"
            elif tecla == '4' or tecla == 't': vista_actual = "threads"
            elif tecla == '5' or tecla == 's': vista_actual = "senales"
            elif tecla == '6' or tecla == 'p': vista_actual = "scheduling"
            elif tecla == '7' or tecla == 'g': vista_actual = "sistema"

            elif tecla == 'h' or tecla == '?':
                mostrar_ayuda(stdscr, alto, ancho)

            elif tecla == '/':
                filtro_cmd = leer_input(stdscr, "Filtrar por comando o usuario (Enter para aplicar, Esc para cancelar): ", alto, ancho)
                filtro_usr = ""
                seleccion_idx = 0
                desplazamiento = 0
            elif tecla == 'u':
                filtro_usr = leer_input(stdscr, "Filtrar por usuario (Enter para aplicar, Esc para cancelar): ", alto, ancho)
                filtro_cmd = ""
                seleccion_idx = 0
                desplazamiento = 0
            elif tecla == 'x':
                filtro_cmd = ""
                filtro_usr = ""
                seleccion_idx = 0
                desplazamiento = 0

            elif tecla == 'KEY_DOWN':
                if seleccion_idx < total_procesos - 1 and not pid_pineado:
                    seleccion_idx += 1
                    if seleccion_idx >= desplazamiento + alto_lista:
                        desplazamiento += 1
            elif tecla == 'KEY_UP':
                if seleccion_idx > 0 and not pid_pineado:
                    seleccion_idx -= 1
                    if seleccion_idx < desplazamiento:
                        desplazamiento -= 1
            
            # Controles interactivos
            elif tecla == '\n' or tecla == 'KEY_ENTER':
                if pid_pineado:
                    pid_pineado = None
                else:
                    pid_pineado = procesos[seleccion_idx].get('pid')
            
            elif tecla == 'c':
                if modo_orden == "pid": modo_orden = "nombre"
                elif modo_orden == "nombre": modo_orden = "cpu"
                else: modo_orden = "pid"
                
            elif tecla == '+':
                if intervalo > 0.5:
                    intervalos[vista_actual] = intervalo - 0.5
                    
            elif tecla == '-':
                if intervalo < 10.0:
                    intervalos[vista_actual] = intervalo + 0.5
                    
        except curses.error:
            pass

def iniciar_tui(snapshot, intervalos):
    curses.wrapper(loop_display, snapshot, intervalos)