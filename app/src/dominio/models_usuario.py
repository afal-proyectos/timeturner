import uuid
from datetime import UTC, datetime


class Usuario:
    """Entidad de dominio que representa a un lector registrado."""

    def __init__(
        self,
        email: str,
        apodo: str,
        clave_hash: str,
        id_usuario: str | None = None,
        rol: str = "Lector",
        fecha_registro: str | None = None,
    ):
        self.id_usuario = id_usuario if id_usuario else str(uuid.uuid4())
        self.email = email
        self.apodo = apodo
        self.clave_hash = clave_hash
        self.rol = rol
        self.fecha_registro = (
            fecha_registro if fecha_registro else datetime.now(UTC).isoformat()
        )

    def to_dict(self) -> dict:
        return {
            "id_usuario": self.id_usuario,
            "email": self.email,
            "apodo": self.apodo,
            "clave_hash": self.clave_hash,
            "rol": self.rol,
            "fecha_registro": self.fecha_registro,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Usuario":
        return cls(
            id_usuario=data["id_usuario"],
            email=data["email"],
            apodo=data["apodo"],
            clave_hash=data["clave_hash"],
            rol=data.get("rol", "Lector"),
            fecha_registro=data.get("fecha_registro"),
        )
