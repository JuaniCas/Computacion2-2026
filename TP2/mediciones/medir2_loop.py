import sys
import time

import httpx

BASE = "http://localhost:8000"
ITER = int(sys.argv[1]) if len(sys.argv) > 1 else 10_000_000

with httpx.Client(timeout=120) as c:
    r = c.post(f"{BASE}/tareas", json={
        "tipo": "hashear",
        "params": {"texto": "hola", "iteraciones": ITER},
    })
    id_ = r.json()["id"]

    latencias = []
    t0 = time.perf_counter()
    while True:
        t = time.perf_counter()
        c.get(f"{BASE}/tareas")
        latencias.append(time.perf_counter() - t)
        estado = c.get(f"{BASE}/tareas/{id_}").json()["estado"]
        if estado in ("completada", "fallida", "cancelada"):
            break
        time.sleep(0.1)
    total = time.perf_counter() - t0

print(f"duración de la tarea:  {total:.2f}s")
print(f"GET /tareas medidos:   {len(latencias)}")
print(f"latencia media:        {sum(latencias) / len(latencias) * 1000:.1f} ms")
print(f"peor latencia:         {max(latencias) * 1000:.1f} ms")