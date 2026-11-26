import uuid
from datetime import UTC, datetime


class Mensaje:
    """Entidad que representa un mensaje o reacción/sticker dentro del chat grupal."""

    def __init__(
        self,
        grupo_id: str,
        usuario_id: str,
        informacion: str,
        tipo: str = "TEXTO",  # 'TEXTO', 'STICKER', 'ANIMO'
        id_mensaje: str | None = None,
        fecha_envio: str | None = None,
    ):
        self.id_mensaje = id_mensaje if id_mensaje else str(uuid.uuid4())
        self.grupo_id = grupo_id
        self.usuario_id = usuario_id
        self.informacion = informacion
        self.tipo = tipo
        self.fecha_envio = fecha_envio if fecha_envio else datetime.now(UTC).isoformat()

    def to_dict(self) -> dict:
        return {
            "id_mensaje": self.id_mensaje,
            "grupo_id": self.grupo_id,
            "usuario_id": self.usuario_id,
            "informacion": self.informacion,
            "tipo": self.tipo,
            "fecha_envio": self.fecha_envio,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Mensaje":
        return cls(
            id_mensaje=data["id_mensaje"],
            grupo_id=data["grupo_id"],
            usuario_id=data["usuario_id"],
            informacion=data["informacion"],
            tipo=data.get("tipo", "TEXTO"),
            fecha_envio=data.get("fecha_envio"),
        )
