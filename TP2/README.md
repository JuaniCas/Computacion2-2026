# TP2 — Plataforma de Tareas Distribuidas

Computación II — Universidad de Mendoza — 2026

Servicio HTTP (FastAPI) que recibe tareas, las encola y las ejecuta con un pool de workers implementado con corrutinas y `asyncio.Queue`. Soporta tres tipos de tarea con naturalezas distintas (I/O real, CPU-bound e I/O simulado), cancelación, timeouts, apagado ordenado con volcado del estado a JSON y un `Dockerfile`/`docker-compose.yml` para levantarlo.

---

## 1. Descripción y uso

### Cómo levantarlo

Con Docker:

```bash
docker compose up --build        # API en http://localhost:8000
```

Sin Docker:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --port 8000
```

### Tipos de tarea

| Tipo | Naturaleza | `params` | Resultado |
|------|-----------|----------|-----------|
| `esperar` | I/O simulado | `{"segundos": 2}` | `{"durmio": 2.0}` |
| `descargar` | I/O-bound | `{"urls": ["https://...", ...]}` | lista con `url`, `status`, `bytes` y `segundos` de cada URL (o `error` si esa URL falló) |
| `hashear` | CPU-bound | `{"texto": "hola", "iteraciones": 5000000}` | SHA-256 aplicado N veces, en hexadecimal |

Estados posibles: `pendiente`, `ejecutando`, `completada`, `fallida`, `cancelada`.

### Endpoints

| Método | Ruta | Qué hace | Códigos |
|--------|------|----------|---------|
| `POST` | `/tareas` | Encola una tarea y responde al instante con su `id` | 201, 422 (body inválido), 503 (cola llena) |
| `GET` | `/tareas` | Lista las tareas; filtro opcional `?estado=` | 200, 422 |
| `GET` | `/tareas/{id}` | Estado y resultado de una tarea | 200, 404 |
| `DELETE` | `/tareas/{id}` | Cancela una tarea encolada o en ejecución | 200, 404, 409 (ya terminada) |
| `GET` | `/estadisticas` | Totales por estado, tiempo promedio, workers ocupados, tareas en cola | 200 |

El `POST` acepta además un `timeout` opcional (en segundos) para esa tarea.

### Ejemplos con `curl`

```bash
# Encolar una tarea que espera 2 segundos
curl -X POST localhost:8000/tareas -H 'content-type: application/json' \
  -d '{"tipo":"esperar","params":{"segundos":2}}'
# {"id":"7aca8b19","estado":"pendiente"}

# Descargar varias URLs concurrentemente
curl -X POST localhost:8000/tareas -H 'content-type: application/json' \
  -d '{"tipo":"descargar","params":{"urls":["https://httpbin.org/delay/2","https://httpbin.org/delay/2"]}}'

# Hash CPU-bound
curl -X POST localhost:8000/tareas -H 'content-type: application/json' \
  -d '{"tipo":"hashear","params":{"texto":"hola","iteraciones":5000000}}'

# Timeout propio de 1 segundo (la tarea de 5 s va a quedar "fallida")
curl -X POST localhost:8000/tareas -H 'content-type: application/json' \
  -d '{"tipo":"esperar","params":{"segundos":5},"timeout":1}'

# Consultar, listar (con y sin filtro), cancelar y ver estadísticas
curl localhost:8000/tareas/7aca8b19
curl localhost:8000/tareas
curl "localhost:8000/tareas?estado=completada"
curl -X DELETE localhost:8000/tareas/7aca8b19
curl localhost:8000/estadisticas
```

### Configuración (variables de entorno)

| Variable | Por defecto | Qué controla |
|----------|-------------|--------------|
| `NUM_WORKERS` | 4 | Cantidad de workers (corrutinas) que consumen la cola |
| `MAX_COLA` | 100 | Tamaño máximo de la cola; al llenarse, `POST` responde 503 |
| `TIMEOUT_DEFAULT` | 30 | Timeout (s) de una tarea si el `POST` no indica otro |
| `GRACIA_APAGADO` | 10 | Segundos que se espera a las tareas en curso al apagar |
| `DIR_ESTADO` | `.` (`/data` en Docker) | Carpeta donde se escribe/lee `estado_<timestamp>.json` |
| `MODO_HASH` | `executor` | Con `bloqueante`, `hashear` corre dentro del event loop (solo se usa para la medición 2) |

### Apagado ordenado y persistencia

Al recibir `SIGTERM` o `SIGINT` el servicio deja de aceptar conexiones, descarta las tareas aún en cola (quedan como `pendiente` en el volcado), espera hasta `GRACIA_APAGADO` segundos a las que están corriendo, interrumpe las que no terminaron (quedan `cancelada` con el motivo `interrumpida por el apagado`) y escribe el estado completo en `estado_<timestamp>.json`. Al arrancar, si existe un volcado previo, lo informa por log. En Docker la carpeta `./data` se monta como volumen, así que los volcados sobreviven al contenedor.

### Estructura del proyecto

```
TP2/
├── app/
│   ├── __init__.py
│   ├── main.py          # API, workers, ejecutores, lifespan, apagado
│   └── modelos.py       # Estado (enum) y Tarea (dataclass)
├── mediciones/
│   ├── medir1_io.py     # descargas secuenciales vs concurrentes
│   ├── medir2_loop.py   # latencia de la API con una tarea CPU-bound
│   ├── medir3_pool.py   # techo del pool
│   └── resultados.txt   # salida de las mediciones
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## 2. Arquitectura

```
cliente ──HTTP──► uvicorn (1 proceso, 1 event loop)
                  │
                  ├─ POST /tareas ──put_nowait──► asyncio.Queue (maxsize) ──get──► Workers 1..N (corrutinas)
                  │                                                                      │
                  ├─ GET / DELETE ◄──────── dict de Tareas (en memoria)                  ▼
                  │                                                         Task interna por tarea
                  │                                                         ├─ esperar   → asyncio.sleep
                  │                                                         ├─ descargar → httpx.AsyncClient (TaskGroup)
                  │                                                         └─ hashear   → run_in_executor ──► ProcessPoolExecutor
                  │
                  └─ SIGTERM / SIGINT ──► apagar() ──► estado_<timestamp>.json
```

**Flujo de una tarea:**

1. `POST /tareas` valida el body con Pydantic, crea una `Tarea` (estado `pendiente`) y la pone en la cola con `put_nowait`. Responde 201 con el `id` sin esperar a que se ejecute. Si la cola está llena responde 503.
2. Un worker libre, que estaba suspendido en `await cola.get()`, recibe la tarea y la marca `ejecutando`.
3. El worker no ejecuta la tarea directamente: la envuelve en una Task interna (`asyncio.create_task`), guarda su referencia en `app.state.handles` y espera su resultado con `asyncio.wait_for(interna, timeout)`.
4. El ejecutor correspondiente hace el trabajo (dormir, descargar o delegar el hash al pool de procesos).
5. Al terminar, el worker deja la tarea `completada` (con su resultado) o `fallida` (con el error o el motivo del timeout), registra el tiempo y llama a `task_done()` en un `finally`.
6. El cliente consulta con `GET /tareas/{id}`. Si hace `DELETE`, se marca `cancelada` y se llama a `cancel()` sobre la Task interna; el worker queda libre para la próxima tarea.

---

## 3. Decisiones de diseño

### ¿Por qué `asyncio.Queue` y no `queue.Queue`?

`queue.Queue.get()` es una llamada **bloqueante**: duerme al hilo que la invoca. Si un worker que corre en el event loop la usara, congelaría el único hilo del loop y con él toda la API. `asyncio.Queue.get()` es una corrutina: con `await` el worker se suspende y cede el control al event loop, que mientras tanto atiende requests u otros workers. Además, como todo corre en un solo hilo y el cambio de corrutina solo ocurre en un `await`, no hace falta ningún `Lock` para proteger la cola ni el estado de las tareas.

### ¿Cómo evito que una tarea CPU-bound congele la API?

Una corrutina solo cede el control en un `await`. El bucle de `hashear` es cálculo puro y no tiene ninguno, así que ejecutarlo dentro del loop lo deja ocupado hasta terminar. Por eso `ejecutar_hashear` usa `loop.run_in_executor` con un `ProcessPoolExecutor`: el cálculo corre en **otro proceso**, con su propio intérprete y su propio GIL, y el loop sigue libre. Elegí procesos y no `asyncio.to_thread` porque con threads el GIL impide que dos cálculos Python puros corran realmente en paralelo. El pool se crea una sola vez en el lifespan (crear procesos es caro) y la función `hashear_cpu` es de nivel módulo porque lo que se envía al otro proceso tiene que poder serializarse (pickle).
### ¿Cómo implementé la cancelación y qué pasa con los recursos a medio usar?

El worker envuelve cada tarea en una Task interna y guarda su referencia. `DELETE` marca la tarea como `cancelada` y llama a `cancel()` sobre esa Task interna, que inyecta un `CancelledError` en el `await` donde esté suspendida. Eso cancela la tarea y no al worker, que sigue vivo. Si la tarea todavía estaba en la cola, el `DELETE` solo cambia su estado y el worker la descarta cuando la saca.

- **`CancelledError` hereda de `BaseException`**, así que no lo atrapa el `except Exception` del worker. El worker lo distingue por el estado: si la tarea figura `cancelada`, fue un `DELETE` y lo absorbe; si no, lo cancelaron a él (por ejemplo al apagar) y lo **relanza**. Tragarse una cancelación ajena dejaría al worker inmortal.
- **`descargar`** usa `asyncio.TaskGroup`: si cancelan la tarea, el grupo cancela todas las descargas hijas y no quedan corrutinas huérfanas. El `AsyncClient` es compartido y se cierra una sola vez en el apagado.- **El timeout** usa el mismo mecanismo: `wait_for` cancela la Task interna al vencer y la tarea queda `fallida` con el motivo.
- **Limitación importante:** cancelar un `hashear` que ya está corriendo en el `ProcessPoolExecutor` cancela la *espera* en el loop, pero el proceso hijo **sigue calculando** hasta terminar, porque `cancel()` no puede interrumpir código que corre en otro proceso.

### ¿Qué pasa si un worker lanza una excepción no capturada?

El cuerpo del worker está dentro de un `try/except Exception`: cualquier error de una tarea la deja `fallida` con `NombreDelError: mensaje` y el worker sigue con la próxima. Si el worker muriera, el pool se achicaría en silencio hasta quedar sin workers. El `finally` llama siempre a `task_done()`; si no lo hiciera, un fallo dejaría a `cola.join()` esperando para siempre durante el apagado. Esto está probado: una tarea con `NotImplementedError` quedó `fallida` y los 4 workers siguieron vivos.

### Otras decisiones

- **`httpx` y no `requests`:** `requests` es bloqueante, y dentro de una corrutina congelaría el event loop. `httpx.AsyncClient` tiene una API casi idéntica pero es asíncrono. Se crea **un solo cliente** en el lifespan para reutilizar conexiones, con un timeout de 10 s por pedido.
- **`put_nowait` y 503 (backpressure):** con `await put`, un `POST` con la cola llena quedaría colgado esperando lugar. Con `put_nowait` falla enseguida y el cliente sabe que tiene que reintentar. Es también lo que acota la memoria: si llegaran 10.000 tareas de golpe, se aceptan hasta `MAX_COLA` pendientes (más las que ya están ejecutando) y el resto recibe 503 inmediato.
- **Un solo proceso de uvicorn:** el estado vive en memoria. Con varios workers de uvicorn cada proceso tendría su propia cola y su propio diccionario, y un `GET` podría caer en un proceso que no conoce la tarea.
- **Apagado dentro del lifespan:** uvicorn ya captura `SIGTERM` y `SIGINT`, deja de aceptar conexiones y recién entonces ejecuta lo que sigue al `yield`. Instalar otro handler de señales habría pisado el suyo. En Docker, el `CMD` está en forma de lista para que uvicorn sea el proceso principal (PID 1) y reciba la señal directamente, y `stop_grace_period: 20s` le da margen sobre el `GRACIA_APAGADO` de 10 s antes de que Docker lo mate con `SIGKILL`.
- **Tarea `completada` aunque una URL falle:** en `descargar`, el error de una URL se devuelve como dato de esa URL y no tira abajo las demás ni la tarea.

---

## 4. Mediciones

**Equipo:** HP Pavilion Gaming 15, AMD Ryzen 5 4600H (6 núcleos / 12 hilos), Python 3.14.4, servidor con `uvicorn` local (sin Docker). Los números crudos están en `mediciones/resultados.txt`.

### 4.1 Concurrencia I/O: 20 descargas secuenciales vs 20 concurrentes

Script `mediciones/medir1_io.py`: 20 pedidos a `https://httpbin.org/delay/1`, primero en un `for` con `await` y después con `asyncio.gather`.

| Corrida | Secuencial | Concurrente | Speedup |
|---------|-----------|-------------|---------|
| 1 | 23.43 s | 1.66 s | 14.1x |
| 2 | 24.73 s | 2.32 s | 10.6x |
| 3 | 24.45 s | 1.91 s | 12.8x |

**Interpretación.** En secuencial cada `await` espera a que termine su descarga antes de pedir la siguiente, así que los tiempos se suman: unos 1.2 s por pedido (1 s de espera del servidor más latencia de red). En concurrente, `gather` lanza las 20 a la vez y el total es el de la más lenta, más un sobrecosto. El speedup ideal sería 20x y se obtuvo entre 10.6x y 14.1x (12.8x en la corrida intermedia). La diferencia se explica por el costo de abrir 20 conexiones TCP+TLS simultáneas (en secuencial se reutiliza una sola) y por la variabilidad de un servicio externo, que se ve en la dispersión entre corridas.

### 4.2 El event loop bloqueado

Script `mediciones/medir2_loop.py`: lanza un `hashear` de 10 millones de iteraciones y, mientras corre, consulta `GET /tareas` cada 0.1 s midiendo cuánto tarda en responder. Se repite con `MODO_HASH=bloqueante` (el cálculo corre directamente en la corrutina) y en modo normal (con `run_in_executor`).

| | Duración de la tarea | `GET /tareas` medidos | Latencia media | Peor latencia |
|---|---|---|---|---|
| Sin executor | 8.47 s | 1 | 8470 ms | 8470 ms |
| Con executor | 8.84 s | 83 | 5.1 ms | 164.9 ms |

**Interpretación.** Sin executor el script logró medir un solo `GET` y tardó 8.47 s, exactamente lo que duró la tarea: mientras el hash corría dentro de la corrutina no hubo ningún `await` donde el loop pudiera atender otra cosa, y toda la API quedó congelada. Con executor el cálculo salió del loop y se atendieron 83 consultas con una latencia media de 5.1 ms. La duración de la tarea casi no cambia (8.47 s vs 8.84 s; la diferencia es el costo de serializar y comunicarse con el otro proceso): el executor no acelera el hash, lo que mejora es que la API sigue respondiendo.

La peor latencia con executor (164.9 ms) es mucho mayor que la media. Mi hipótesis es que corresponde al arranque de los procesos del pool, que se crean recién en el primer uso y desde el hilo del loop. Es una hipótesis que no verifiqué (habría que repetir la medición sin reiniciar el servidor y ver si baja).

### 4.3 Techo del pool

Script `mediciones/medir3_pool.py`: se lanzan N tareas simultáneas y se mide el tiempo hasta que todas terminan, con `NUM_WORKERS=50` y `MAX_COLA=1000`.

**`esperar` (1 s por tarea, I/O simulado):**

| Tareas | 1 | 10 | 25 | 50 | 100 | 200 |
|--------|---|----|----|----|-----|-----|
| Tiempo | 1.02 s | 1.04 s | 1.08 s | 1.15 s | 2.18 s | 4.16 s |

**`hashear` (3.000.000 de iteraciones por tarea, pool de 12 procesos):**

| Tareas | 1 | 4 | 8 | 12 | 16 | 24 | 32 |
|--------|---|---|---|----|----|----|----|
| Tiempo | 3.09 s | 2.91 s | 3.59 s | 3.32 s | 4.76 s | 6.28 s | 8.73 s |

**Interpretación.**

- **`esperar`:** el tiempo es casi plano (~1 s) hasta 50 tareas y después sube en escalones: 100 son dos tandas y 200 son cuatro. **El techo es `NUM_WORKERS`** (50): cada worker retiene una tarea mientras duerme y las demás esperan en la cola. Es un límite de configuración y no de hardware: como una tarea que solo espera no consume CPU, se podría subir mucho más. Lo que acota de verdad es la memoria y `MAX_COLA` (503).
- **`hashear`:** se mantiene alrededor de 3 s hasta 12 tareas (ejecución paralela real en procesos distintos) y a partir de ahí crece linealmente: 24 son dos tandas (~6.3 s) y 32 son tres (~8.7 s). **El techo es la cantidad de procesos del pool** (`os.cpu_count()` = 12), no los 50 workers: los workers restantes solo esperan el resultado. Tener más procesos que CPUs no ayudaría, porque se repartirían el tiempo de CPU. En N=16 dio 4.76 s y no ~6.3 s porque la segunda tanda tiene solo 4 tareas y corre más liviana. La leve suba en N=8 (3.59 s) frente a N=4 (2.91 s) posiblemente se deba a que, con más de 6 tareas, dos hilos comparten un mismo núcleo físico (SMT), pero no lo medí.
- **En ambos casos el rendimiento llega a un tope** (unas 43–48 tareas/s en `esperar`, unas 3.6 tareas/s en `hashear`) y a partir de ahí agregar tareas solo aumenta la espera. Lo que cambia es qué lo limita: en I/O, un número configurable; en CPU, el hardware.

---

## 5. Conceptos del curso aplicados

| Concepto / clase | Dónde está en el código y cómo se vincula |
|---|---|
| Sockets TCP y servidores concurrentes (13–14) | La API es HTTP sobre TCP: Uvicorn acepta y atiende muchos clientes a la vez sin un hilo por conexión. |
| I/O multiplexing, `select`/`epoll` (17) | Es la base del event loop de asyncio: un solo hilo vigila muchos sockets y solo atiende los que están listos. |
| Corrutinas, `async`/`await` (18) | `worker`, `ejecutar_esperar`, `ejecutar_descargar`, `ejecutar_hashear` y los endpoints son `async def`. Cada `await` es un punto donde el control vuelve al event loop. |
| HTTP y FastAPI (19) | Rutas `/tareas`, `/tareas/{id}`, `/estadisticas`; validación del body con Pydantic (`Literal` → 422 si el tipo no existe); códigos 201, 404, 409 (cancelar algo ya terminado) y 503 (cola llena). |
| asyncio en red y avanzado (20–21) | `asyncio.Queue` con `maxsize`; `create_task`; `wait_for` para el timeout; `task.cancel()` y `CancelledError` para la cancelación; `TaskGroup` y `gather` para concurrencia; `httpx.AsyncClient` para I/O de red. |
| `concurrent.futures` (22) | `ProcessPoolExecutor` creado una vez en el lifespan y `loop.run_in_executor` en `ejecutar_hashear`, para que el cálculo CPU-bound salga del event loop. |
| Context managers y generadores (bloque 0) | `lifespan` (`@asynccontextmanager`): lo anterior al `yield` es el arranque y lo posterior es el apagado; `async with asyncio.TaskGroup()` en `ejecutar_descargar`. |
| Señales y apagado ordenado | Uvicorn captura `SIGTERM`/`SIGINT` y ejecuta lo que sigue al `yield` del lifespan, donde `apagar()` descarta pendientes, espera a las que corren (con límite) y vuelca el estado a JSON. |

**Productor-consumidor (clase 11).** El `POST /tareas` es el productor: pone la tarea en la `asyncio.Queue` con `put_nowait`. Los N `worker` son los consumidores: hacen `await cola.get()`. Es el mismo patrón que con threads, pero con corrutinas. Si la cola se llena, `put_nowait` lanza `QueueFull` y el endpoint responde 503, o sea que la cola impone un límite (backpressure).

**Por qué no hace falta un `Lock`.** El event loop corre en un solo hilo y solo cambia de corrutina en un `await`. En `cancelar` y en el `worker` no hay ningún `await` entre cambiar el estado de la tarea y usar su handle, así que esas secciones no se pueden interrumpir a la mitad. Con threads habría una condición de carrera.

**`await` y `gather`.** Un `for` con `await` adentro espera cada elemento en orden (suma de tiempos); `gather` o `TaskGroup` los lanzan a la vez y esperan al más lento. La medición 1 lo muestra: 20 descargas pasaron de unos 24 s a unos 2 s.

---

## 6. Limitaciones conocidas

- **Cancelar o dar timeout a un `hashear` en ejecución no detiene el proceso hijo:** la tarea figura `cancelada` o `fallida`, pero el cálculo sigue consumiendo CPU hasta terminar, porque `cancel()` no alcanza a código que corre en otro proceso. Una solución sería un flag compartido (`multiprocessing.Event`) que el bucle consulte cada tanto, que no implementé.
- **El apagado puede demorarse por un `hashear` en curso:** por la misma razón, el proceso del pool puede retrasar la salida hasta terminar su cálculo.
- **El estado vive en memoria y el diccionario de tareas crece sin límite:** no hay expiración de tareas viejas.
- **El volcado solo se informa, no se recarga:** al arrancar se avisa por log que existe un volcado previo, pero las tareas no se restauran. Con `SIGKILL` no hay volcado.
- **Un solo proceso de uvicorn:** escalar a varios procesos requeriría estado compartido (por ejemplo, una base de datos o Redis), que la consigna excluye.
- **Una tarea cancelada mientras espera en la cola ocupa su lugar** hasta que un worker la saca, por lo que sigue contando en `en_cola`.
- **`descargar` guarda en memoria el contenido completo de cada respuesta** (solo devuelve su tamaño), por lo que una descarga muy grande consumiría mucha memoria. El timeout de `httpx` es fijo (10 s por pedido).
- **Sin autenticación ni rate limiting,** y sin tests automatizados: las pruebas fueron manuales con `curl`.

---

## 7. Lo que aprendí

Lo que más aprendí en este trabajo es a medir en lugar de suponer. Varias veces el resultado no fue el que yo esperaba y tuve que leer los datos para entender por qué. En la prueba del apagado ordenado terminaron 4 tareas canceladas y ninguna pendiente, cuando esperaba ver también algunas sin arrancar; el log (`0 tareas pendientes descartadas, 4 en curso`) mostró que los workers que habían terminado sus tareas cortas ya habían tomado las siguientes de la cola antes de que apretara Ctrl+C. Con las descargas pasó algo parecido: esperaba un speedup cercano a 20x y obtuve entre 10.6x y 14.1x, y solo al pensar en el costo de abrir 20 conexiones a la vez la diferencia tuvo sentido.

Lo que más me costó fue diseñar el apagado ordenado, porque lo difícil es el orden de las cosas. Primero hay que dejar de aceptar trabajo y vaciar la cola; después esperar con un límite a las tareas que están corriendo; cancelar las que no terminan a tiempo; dejar que los workers cierren el estado de cada tarea antes de cancelarlos (si no, el volcado queda con estados desactualizados); y recién al final cerrar el cliente HTTP y el pool y escribir el JSON. También tuve que entender que uvicorn ya captura `SIGTERM` y `SIGINT`, así que no podía instalar un handler propio sin pisar el suyo y el lugar correcto era el código posterior al `yield` del lifespan. Y en Docker había que cuidar que la señal llegara a uvicorn (por eso el `CMD` en forma de lista) y que Docker esperara lo suficiente antes de matar el contenedor (`stop_grace_period`).
