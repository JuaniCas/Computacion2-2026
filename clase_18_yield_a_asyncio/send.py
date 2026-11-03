def acumulador():
    total = 0
    while True:
        n = yield total
        total += n

a = acumulador()

#1. ¿Qué pasa si hacés a.send(10) sin llamar antes a next(a)? Probalo y leé el error.
#2. Después del next(a) inicial, ¿qué devuelve? ¿Por qué ese valor?
#3. Hacé tres send() seguidos y explicá de dónde sale cada resultado.

