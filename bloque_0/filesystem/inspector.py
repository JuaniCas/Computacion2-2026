import os
import sys
import stat
import pwd
import grp
from datetime import datetime
from pathlib import Path

def formatear_permisos(mode):
    
    permisos_str = stat.filemode(mode)
    
    permisos_octal = oct(mode & 0o777)[2:]
    
    return f"{permisos_str} ({permisos_octal})"

def obtener_tipo(path_obj):
    if path_obj.is_symlink():
        destino = os.readlink(path_obj)
        return f"enlace simbólico -> {destino}"
    if path_obj.is_dir():
        return "directorio"
    if path_obj.is_block_device():
        return "dispositivo de bloques"
    if path_obj.is_char_device():
        return "dispositivo de caracteres"
    if path_obj.is_socket():
        return "socket"
    if path_obj.is_fifo():
        return "FIFO (pipe)"
    return "archivo regular"

def inspeccionar(ruta):
    path = Path(ruta)
    if not path.exists() and not path.is_symlink():
        print(f"Error: El archivo '{ruta}' no existe.", file=sys.stderr)
        return

    # Usamos lstat para no seguir el enlace si es un symlink
    st = path.lstat()
    
    print(f"Archivo: {path.absolute()}")
    print(f"Tipo: {obtener_tipo(path)}")
    
    
    tamano_bytes = st.st_size
    tamano_kb = tamano_bytes / 1024
    print(f"Tamaño: {tamano_bytes} bytes ({tamano_kb:.2f} KB)")
    
    print(f"Permisos: {formatear_permisos(st.st_mode)}")
    
    
    usuario = pwd.getpwuid(st.st_uid).pw_name
    grupo = grp.getgrgid(st.st_gid).gr_name
    print(f"Propietario: {usuario} (uid: {st.st_uid})")
    print(f"Grupo: {grupo} (gid: {st.st_gid})")
    
    print(f"Inodo: {st.st_ino}")
    print(f"Enlaces duros: {st.st_nlink}")
    
    formato_fecha = "%Y-%m-%d %H:%M:%S"
    print(f"Cambio metadatos (ctime): {datetime.fromtimestamp(st.st_ctime).strftime(formato_fecha)}")
    print(f"Última modificación (mtime): {datetime.fromtimestamp(st.st_mtime).strftime(formato_fecha)}")
    print(f"Último acceso (atime): {datetime.fromtimestamp(st.st_atime).strftime(formato_fecha)}")

    if path.is_dir():
        elementos = len(list(path.iterdir()))
        print(f"Contenido: {elementos} elementos")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 inspector.py <ruta_al_archivo>")
        sys.exit(1)
    
    inspeccionar(sys.argv[1])