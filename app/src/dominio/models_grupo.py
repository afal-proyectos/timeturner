import random
import string
import uuid
from datetime import UTC, datetime


class Grupo:
    """Entidad que representa un club de lectura o grupo cerrado."""

    def __init__(
        self,
        nombre: str,
        admin_id: str,
        codigo_acceso: str | None = None,
        id_grupo: str | None = None,
        fecha_creacion: str | None = None,
    ):
        self.id_grupo = id_grupo if id_grupo else str(uuid.uuid4())
        self.nombre = nombre
        self.admin_id = admin_id
        self.codigo_acceso = codigo_acceso if codigo_acceso else self.generar_codigo()
        self.fecha_creacion = (
            fecha_creacion if fecha_creacion else datetime.now(UTC).isoformat()
        )

    @staticmethod
    def generar_codigo() -> str:
        """Genera un código aleatorio único de 6 caracteres alfanuméricos en mayúsculas."""
        return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))

    def to_dict(self) -> dict:
        return {
            "id_grupo": self.id_grupo,
            "nombre": self.nombre,
            "codigo_acceso": self.codigo_acceso,
            "admin_id": self.admin_id,
            "fecha_creacion": self.fecha_creacion,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Grupo":
        return cls(
            id_grupo=data["id_grupo"],
            nombre=data["nombre"],
            codigo_acceso=data["codigo_acceso"],
            admin_id=data["admin_id"],
            fecha_creacion=data.get("fecha_creacion"),
        )
