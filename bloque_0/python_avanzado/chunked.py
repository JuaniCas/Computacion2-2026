def chunked(iterable, tamaño):
    """
    Generador que divide un iterable en lotes de un tamaño fijo.
    """
    chunk = []
    for elemento in iterable:
        chunk.append(elemento)
        if len(chunk) == tamaño:
            yield chunk
            chunk = []
    
    if chunk:
        yield chunk

if __name__ == "__main__":

    print(list(chunked(range(10), 3)))

    print(list(chunked("abcdefgh", 3)))

    