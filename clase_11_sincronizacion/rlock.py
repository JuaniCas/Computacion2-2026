import threading

class CuentaBancaria:
    def __init__(self, saldo_inicial):
        self.saldo = saldo_inicial
        self.lock = threading.RLock()

    def depositar(self, cantidad):
        with self.lock:
            self.saldo += cantidad
            print(f"Depositados {cantidad}. Saldo: {self.saldo}")

    def retirar(self, cantidad):
        with self.lock:
            if self.saldo >= cantidad:
                self.saldo -= cantidad
                print(f"Retirados {cantidad}. Saldo: {self.saldo}")
                return True
            return False

    def transferir_a(self, otra_cuenta, cantidad):
        # Este método adquiere self.lock Y llama a retirar()
        # que también adquiere self.lock. Con Lock normal: DEADLOCK.
        # Con RLock: funciona, porque es el mismo thread.
        with self.lock:
            if self.retirar(cantidad):
                otra_cuenta.depositar(cantidad)
                return True
            return False


cuenta_a = CuentaBancaria(1000)
cuenta_b = CuentaBancaria(500)

# Transferencia en un thread
t = threading.Thread(target=cuenta_a.transferir_a, args=(cuenta_b, 300))
t.start()
t.join()

print(f"Saldo A: {cuenta_a.saldo}")  # 700
print(f"Saldo B: {cuenta_b.saldo}")  # 800