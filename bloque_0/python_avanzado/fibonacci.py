def fibonacci(limite=None):
    """
    Generador que produce la secuencia de Fibonacci.
    Si se proporciona un límite, se detiene al alcanzarlo.
    """
    a, b = 0, 1
    
    while True:

        if limite is not None and a > limite:
            break
            
        yield a
        
        a, b = b, a + b

if __name__ == "__main__":
    
    fib = fibonacci()
    print("Primeros 10 números:")
    for _ in range(10):
        print(next(fib))
    
    print("podemos seguir obteniendo números:")
    print(next(fib))
    print(next(fib))

    print("\n" + "-"*20 + "\n")

    for n in fibonacci(limite=100):
        print(n)