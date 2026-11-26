from datetime import UTC, datetime


class MiembroGrupo:
    """Entidad intermedia que vincula a un Usuario con un Grupo."""

    def __init__(
        self,
        id_grupo: str,
        id_usuario: str,
        fecha_union: str | None = None,
    ):
        self.id_grupo = id_grupo
        self.id_usuario = id_usuario
        self.fecha_union = fecha_union if fecha_union else datetime.now(UTC).isoformat()

    def to_dict(self) -> dict:
        return {
            "id_grupo": self.id_grupo,
            "id_usuario": self.id_usuario,
            "fecha_union": self.fecha_union,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MiembroGrupo":
        return cls(
            id_grupo=data["id_grupo"],
            id_usuario=data["id_usuario"],
            fecha_union=data.get("fecha_union"),
        )
