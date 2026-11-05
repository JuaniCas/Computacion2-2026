import sys
import time

import httpx

BASE = "http://localhost:8000"
TIPO = sys.argv[1] if len(sys.argv) > 1 else "esperar"

PARAMS = {
    "esperar": {"segundos": 1},
    "hashear": {"texto": "x", "iteraciones": 3_000_000},
}[TIPO]
NS = {
    "esperar": [1, 10, 25, 50, 100, 200],
    "hashear": [1, 4, 8, 12, 16, 24, 32],
}[TIPO]


def completadas(c):
    return c.get(f"{BASE}/estadisticas").json()["por_estado"]["completada"]


with httpx.Client(timeout=60) as c:
    print(f"tipo={TIPO}")
    for n in NS:
        base = completadas(c)
        t0 = time.perf_counter()
        for _ in range(n):
            c.post(f"{BASE}/tareas", json={"tipo": TIPO, "params": PARAMS})
        while completadas(c) - base < n:
            time.sleep(0.05)
        print(f"{n:>4} tareas -> {time.perf_counter() - t0:6.2f}s")