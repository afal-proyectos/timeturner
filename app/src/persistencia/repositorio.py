from abc import ABC, abstractmethod

from dominio.models_libro import Libro
from dominio.models_sesion import SesionLectura
from dominio.models_usuario import Usuario


class IRepositorioDatos(ABC):
    """
    Contrato abstracto que define las operaciones de persistencia del sistema.
    Cualquier almacenamiento (JSON, Supabase, etc.) debe implementar esta interfaz.
    """

    # --- Gestión de Libros ---

    @abstractmethod
    def guardar_libro(self, libro: Libro) -> bool:
        """Persiste o actualiza un libro en el almacenamiento."""

    @abstractmethod
    def obtener_libros(self, usuario_id: str) -> list[Libro]:
        """Obtiene la lista de libros registrados por un usuario específico."""

    @abstractmethod
    def obtener_libro_por_id(self, id_libro: str) -> list[Libro | None]:
        """Busca y retorna un libro por su ID único (UUID)."""

    # --- Gestión de Sesiones de Lectura ---

    @abstractmethod
    def registrar_sesion(self, sesion: SesionLectura) -> bool:
        """Guarda o actualiza una sesión de lectura."""

    @abstractmethod
    def obtener_sesiones(self, libro_id: str) -> list[SesionLectura]:
        """Obtiene el historial de sesiones asociadas a un libro especifico."""

        # --- Gestión de Sesiones de usuarios ---

    @abstractmethod
    def guardar_usuario(self, usuario: Usuario) -> bool:
        pass

    @abstractmethod
    def obtener_usuario_por_apodo(self, apodo: str) -> list[Usuario | None]:
        pass
