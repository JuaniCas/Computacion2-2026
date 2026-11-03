import asyncio
import time

import httpx

URL = "https://httpbin.org/delay/1"
N = 20


async def secuencial(client):
    t0 = time.perf_counter()
    for _ in range(N):
        await client.get(URL)
    return time.perf_counter() - t0


async def concurrente(client):
    t0 = time.perf_counter()
    await asyncio.gather(*(client.get(URL) for _ in range(N)))
    return time.perf_counter() - t0


async def main():
    async with httpx.AsyncClient(timeout=30) as client:
        await client.get(URL)                  # calentamiento de la conexión
        seq = await secuencial(client)
        con = await concurrente(client)
    print(f"{N} descargas secuenciales: {seq:.2f}s")
    print(f"{N} descargas concurrentes: {con:.2f}s")
    print(f"speedup: {seq / con:.1f}x")


asyncio.run(main())