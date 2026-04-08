import functools
from collections import namedtuple

CacheInfo = namedtuple('CacheInfo', ['hits', 'misses', 'size'])

def memoize(funcion):
    """
    Decorador que implementa cache manual y estadísticas de uso.
    """
    cache = {}
    stats = {'hits': 0, 'misses': 0}

    @functools.wraps(funcion)
    def wrapper(*args):
        
        if args in cache:
            stats['hits'] += 1
            return cache[args]
        
        
        stats['misses'] += 1
        resultado = funcion(*args)
        cache[args] = resultado
        return resultado

    
    wrapper.cache = cache
    
    def cache_info():
        return CacheInfo(hits=stats['hits'], misses=stats['misses'], size=len(cache))
    
    def clear_cache():
        cache.clear()
        stats['hits'] = 0
        stats['misses'] = 0

    wrapper.cache_info = cache_info
    wrapper.clear_cache = clear_cache

    return wrapper

if __name__ == "__main__":
    
    @memoize
    def fibonacci(n):
        if n < 2:
            return n
        return fibonacci(n-1) + fibonacci(n-2)

    
    print(f"Fibonacci(100): {fibonacci(100)}")

    
    print(f"\nPrimeros elementos del cache: {list(fibonacci.cache.items())[:5]}")

    
    print(f"Estadísticas: {fibonacci.cache_info()}")

    
    print("\nLimpiando cache...")
    fibonacci.clear_cache()
    print(f"Estadísticas post-limpieza: {fibonacci.cache_info()}")