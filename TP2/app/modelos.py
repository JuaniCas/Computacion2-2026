import time
import uuid
from dataclasses import dataclass, field
from enum import Enum


class Estado(str, Enum):
    PENDIENTE = "pendiente"
    EJECUTANDO = "ejecutando"
    COMPLETADA = "completada"
    FALLIDA = "fallida"
    CANCELADA = "cancelada"


@dataclass
class Tarea:
    tipo: str
    params: dict
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    estado: Estado = Estado.PENDIENTE
    resultado: object = None
    error: str | None = None
    creada: float = field(default_factory=time.time)
    inicio: float | None = None
    fin: float | None = None
    timeout: float = 30.0