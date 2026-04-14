from flask import Flask
import redis
import os

app = Flask(__name__)
r = redis.Redis(host=os.getenv('REDIS_HOST', 'redis'), port=6379)

@app.route('/')
def home():
    valor = r.get('contador_global')
    valor = valor.decode() if valor else "0"
    return f"<h1>Proyecto Integrador</h1><p>El worker ha procesado: <b>{valor}</b> ticks.</p>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)