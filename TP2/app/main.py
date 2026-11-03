import asyncio
import os
import time
import hashlib
import httpx
import json
import logging
from contextlib import asynccontextmanager
from typing import Literal
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from app.modelos import Estado, Tarea

NUM_WORKERS = int(os.getenv("NUM_WORKERS", "4"))
MAX_COLA = int(os.getenv("MAX_COLA", "100"))
TIMEOUT_DEFAULT = float(os.getenv("TIMEOUT_DEFAULT", "30"))
GRACIA_APAGADO = float(os.getenv("GRACIA_APAGADO", "10"))
DIR_ESTADO = os.getenv("DIR_ESTADO", ".")
MODO_HASH = os.getenv("MODO_HASH", "executor")

log = logging.getLogger("uvicorn.error")
   
async def ejecutar_esperar(params: dict, ctx):
    segundos = float(params.get("segundos", 1))
    await asyncio.sleep(segundos)
    return {"durmio": segundos}


async def ejecutar_descargar(params: dict, ctx):
    urls = params.get("urls", [])

    async def una(url: str):
        t0 = time.perf_counter()
        try:
            r = await ctx.client.get(url)
            return {"url": url, "status": r.status_code,
                    "bytes": len(r.content),
                    "segundos": round(time.perf_counter() - t0, 3)}
        except httpx.HTTPError as e:
            return {"url": url, "error": f"{type(e).__name__}: {e}",
                    "segundos": round(time.perf_counter() - t0, 3)}

    async with asyncio.TaskGroup() as tg:
        tareas = [tg.create_task(una(u)) for u in urls]
    return [t.result() for t in tareas]


def hashear_cpu(texto: str, iteraciones: int) -> str:
    h = texto.encode()
    for _ in range(iteraciones):
        h = hashlib.sha256(h).digest()
    return h.hex()


async def ejecutar_hashear(params: dict, ctx):
    texto, n = params["texto"], int(params["iteraciones"])
    if MODO_HASH == "bloqueante":
        return hashear_cpu(texto, n)      # SOLO PARA MEDIR: bloquea el event loop
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(ctx.pool, hashear_cpu, texto, n)


EJECUTORES = {
    "esperar": ejecutar_esperar,
    "descargar": ejecutar_descargar,
    "hashear": ejecutar_hashear,
}

async def worker(nombre: str, estado_app):
    cola: asyncio.Queue = estado_app.cola
    while True:
        tarea: Tarea = await cola.get()
        try:
            if tarea.estado == Estado.CANCELADA:
                continue                      # la cancelaron antes de empezar
            tarea.estado = Estado.EJECUTANDO
            tarea.inicio = time.time()
            interna = asyncio.create_task(
                EJECUTORES[tarea.tipo](tarea.params, estado_app)
            )
            estado_app.handles[tarea.id] = interna
            tarea.resultado = await asyncio.wait_for(interna, tarea.timeout)
            tarea.estado = Estado.COMPLETADA
        except asyncio.TimeoutError:
            tarea.estado = Estado.FALLIDA
            tarea.error = f"timeout: superó {tarea.timeout}s"
        except asyncio.CancelledError:
            if tarea.estado != Estado.CANCELADA:
                raise                          # cancelaron al worker (apagado)
        except Exception as e:
            tarea.estado = Estado.FALLIDA
            tarea.error = f"{type(e).__name__}: {e}"
        finally:
            estado_app.handles.pop(tarea.id, None)
            tarea.fin = time.time()
            cola.task_done()

def reportar_volcado_previo():
    archivos = sorted(Path(DIR_ESTADO).glob("estado_*.json"))
    if not archivos:
        log.info("No hay volcado previo de estado")
        return
    ultimo = archivos[-1]
    try:
        n = len(json.loads(ultimo.read_text()))
    except Exception:
        n = "?"
    log.info("Volcado previo encontrado: %s (%s tareas)", ultimo.name, n)


def volcar_estado(tareas: dict) -> Path:
    ruta = Path(DIR_ESTADO) / f"estado_{datetime.now():%Y%m%d_%H%M%S}.json"
    datos = [asdict(t) for t in tareas.values()]
    ruta.write_text(json.dumps(datos, indent=2, default=str))
    return ruta


async def apagar(app: FastAPI):
    st = app.state

    # 1. Las pendientes no se ejecutan: se sacan de la cola y quedan
    #    como "pendiente" en el volcado.
    descartadas = 0
    while True:
        try:
            st.cola.get_nowait()
        except asyncio.QueueEmpty:
            break
        st.cola.task_done()
        descartadas += 1
    log.info("Apagado: %d tareas pendientes descartadas, %d en curso",
             descartadas, len(st.handles))

    # 2. Esperar (con límite) a las que están en curso
    en_curso = dict(st.handles)
    if en_curso:
        _, colgadas = await asyncio.wait(en_curso.values(),
                                         timeout=GRACIA_APAGADO)
        for id_, interna in en_curso.items():
            if interna in colgadas:
                tarea = st.tareas[id_]
                tarea.estado = Estado.CANCELADA
                tarea.error = "interrumpida por el apagado"
                interna.cancel()

    # 3. Dejar que los workers terminen de cerrar sus tareas, y apagarlos
    try:
        await asyncio.wait_for(st.cola.join(), timeout=5)
    except asyncio.TimeoutError:
        log.warning("Algunos workers no cerraron a tiempo")
    for w in st.workers:
        w.cancel()
    await asyncio.gather(*st.workers, return_exceptions=True)

    # 4. Liberar recursos y volcar el estado
    await st.client.aclose()
    st.pool.shutdown(wait=False, cancel_futures=True)
    ruta = volcar_estado(st.tareas)
    log.info("Estado volcado en %s", ruta)

@asynccontextmanager
async def ciclo(app: FastAPI):
    reportar_volcado_previo()
    app.state.tareas = {}
    app.state.handles = {}
    app.state.cola = asyncio.Queue(maxsize=MAX_COLA)
    app.state.client = httpx.AsyncClient(timeout=10.0)
    app.state.pool = ProcessPoolExecutor(max_workers=os.cpu_count())
    app.state.workers = [
        asyncio.create_task(worker(f"w{i}", app.state))
        for i in range(NUM_WORKERS)
    ]
    yield
    await apagar(app)

app = FastAPI(title="Plataforma de tareas", lifespan=ciclo)


class TareaNueva(BaseModel):
    tipo: Literal["descargar", "hashear", "esperar"]
    params: dict = Field(default_factory=dict)
    timeout: float | None = Field(default=None, gt=0)


@app.post("/tareas", status_code=201)
async def crear(nueva: TareaNueva, request: Request):
    tarea = Tarea(tipo=nueva.tipo, params=nueva.params, timeout=nueva.timeout or TIMEOUT_DEFAULT)
    try:
        request.app.state.cola.put_nowait(tarea)
    except asyncio.QueueFull:
        raise HTTPException(503, "cola llena, reintentá más tarde")
    request.app.state.tareas[tarea.id] = tarea
    return {"id": tarea.id, "estado": tarea.estado}


@app.get("/tareas")
async def listar(request: Request, estado: Estado | None = None):
    tareas = request.app.state.tareas.values()
    return [t for t in tareas if estado is None or t.estado == estado]


@app.get("/tareas/{tarea_id}")
async def obtener(tarea_id: str, request: Request):
    tarea = request.app.state.tareas.get(tarea_id)
    if tarea is None:
        raise HTTPException(404, "No existe esa tarea")
    return tarea

@app.delete("/tareas/{tarea_id}")
async def cancelar(tarea_id: str, request: Request):
    tarea = request.app.state.tareas.get(tarea_id)
    if tarea is None:
        raise HTTPException(404, "No existe esa tarea")
    if tarea.estado in (Estado.COMPLETADA, Estado.FALLIDA, Estado.CANCELADA):
        raise HTTPException(409, f"la tarea ya está {tarea.estado.value}")
    tarea.estado = Estado.CANCELADA
    interna = request.app.state.handles.get(tarea.id)
    if interna:
        interna.cancel()
    return {"id": tarea.id, "estado": tarea.estado}

@app.get("/estadisticas")
async def estadisticas(request: Request):
    st = request.app.state
    tareas = list(st.tareas.values())
    por_estado = {e.value: 0 for e in Estado}
    for t in tareas:
        por_estado[t.estado.value] += 1
    duraciones = [t.fin - t.inicio for t in tareas
                  if t.estado == Estado.COMPLETADA]
    return {
        "total": len(tareas),
        "por_estado": por_estado,
        "tiempo_promedio_s": (round(sum(duraciones) / len(duraciones), 3)
                              if duraciones else None),
        "workers_ocupados": len(st.handles),
        "workers_total": NUM_WORKERS,
        "en_cola": st.cola.qsize(),
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

