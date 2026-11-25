import json
import os
from datetime import datetime

from dominio.models_libro import Libro
from dominio.models_sesion import EstadoSesion, SesionLectura
from dominio.models_usuario import Usuario

from persistencia.repositorio import IRepositorioDatos


class RepositorioJSON(IRepositorioDatos):
    """
    Implementación concreta de IRepositorioDatos basada en archivos JSON locales.
    """

    def __init__(self, ruta_base: str = "data"):
        self.ruta_base = ruta_base
        self.ruta_libros = os.path.join(self.ruta_base, "libros.json")
        self.ruta_sesiones = os.path.join(self.ruta_base, "sesiones.json")
        self.ruta_usuario = os.path.join(self.ruta_base, "usuario.json")

        # Asegura la existencia del directorio data/ y de los archivos base
        self._inicializar_almacenamiento()

    def _inicializar_almacenamiento(self) -> None:
        """Crea la carpeta de datos y los archivos JSON vacíos si no existen."""
        if not os.path.exists(self.ruta_base):
            os.makedirs(self.ruta_base, exist_ok=True)

        if not os.path.exists(self.ruta_libros):
            with open(self.ruta_libros, "w", encoding="utf-8") as f:
                json.dump([], f, indent=4)

        if not os.path.exists(self.ruta_sesiones):
            with open(self.ruta_sesiones, "w", encoding="utf-8") as f:
                json.dump([], f, indent=4)

    # --- Métodos Auxiliares de Lectura/Escritura JSON ---

    def _leer_archivo(self, ruta: str) -> list:
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _escribir_archivo(self, ruta: str, datos: list) -> bool:
        try:
            with open(ruta, "w", encoding="utf-8") as f:
                json.dump(datos, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"[Error RepositorioJSON] Error al escribir en {ruta}: {e}")
            return False

    # --- Implementación de IRepositorioDatos: Libros ---

    def guardar_libro(self, libro: Libro) -> bool:
        libros_dict = self._leer_archivo(self.ruta_libros)

        # Buscar si el libro ya existe para actualizarlo
        actualizado = False
        for i, item in enumerate(libros_dict):
            if item.get("id_libro") == libro.id_libro:
                libros_dict[i] = libro.to_dict()
                actualizado = True
                break

        if not actualizado:
            libros_dict.append(libro.to_dict())

        return self._escribir_archivo(self.ruta_libros, libros_dict)

    def obtener_libros(self, usuario_id: str) -> list[Libro]:
        libros_dict = self._leer_archivo(self.ruta_libros)
        return [
            Libro.from_dict(item)
            for item in libros_dict
            if item.get("usuario_id") == usuario_id
        ]

    def obtener_libro_por_id(self, id_libro: str) -> list[Libro | None]:
        libros_dict = self._leer_archivo(self.ruta_libros)
        for item in libros_dict:
            if item.get("id_libro") == id_libro:
                return Libro.from_dict(item)
        return None

    # --- Implementación de IRepositorioDatos: Sesiones ---

    def registrar_sesion(self, sesion: SesionLectura) -> bool:
        sesiones_dict = self._leer_archivo(self.ruta_sesiones)

        # Convertir objeto SesionLectura a formato JSON-serializable
        sesion_data = {
            "id_sesion": sesion.id_sesion,
            "libro_id": sesion.libro_id,
            "usuario_id": sesion.usuario_id,
            "pagina_inicio": sesion.pagina_inicio,
            "pagina_fin": sesion.pagina_fin,
            "inicio_utc": sesion.inicio_utc.isoformat() if sesion.inicio_utc else None,
            "fin_utc": sesion.fin_utc.isoformat() if sesion.fin_utc else None,
            "minutos_pausa": sesion.minutos_pausa,
            "estado": sesion.estado.value,
        }

        # Actualizar si existe, o agregar uno nuevo
        actualizado = False
        for i, item in enumerate(sesiones_dict):
            if item.get("id_sesion") == sesion.id_sesion:
                sesiones_dict[i] = sesion_data
                actualizado = True
                break

        if not actualizado:
            sesiones_dict.append(sesion_data)

        return self._escribir_archivo(self.ruta_sesiones, sesiones_dict)

    def obtener_sesiones(self, libro_id: str) -> list[SesionLectura]:
        sesiones_dict = self._leer_archivo(self.ruta_sesiones)
        resultado: list[SesionLectura] = []

        for item in sesiones_dict:
            if item.get("libro_id") == libro_id:
                # Reconstrucción de la entidad SesionLectura desde JSON
                sesion = SesionLectura(
                    id_sesion=item["id_sesion"],
                    libro_id=item["libro_id"],
                    usuario_id=item["usuario_id"],
                    pagina_inicio=item["pagina_inicio"],
                )
                sesion.pagina_fin = item.get("pagina_fin")
                sesion.minutos_pausa = item.get("minutos_pausa", 0.0)
                sesion.estado = EstadoSesion(item.get("estado", "INACTIVA"))

                if item.get("inicio_utc"):
                    sesion.inicio_utc = datetime.fromisoformat(item["inicio_utc"])
                if item.get("fin_utc"):
                    sesion.fin_utc = datetime.fromisoformat(item["fin_utc"])

                resultado.append(sesion)

        return resultado

    # --------------CRUD de Usuario-------------------------
    def guardar_usuario(self, usuario: Usuario) -> bool:
        usuarios = self._leer_archivo(self.ruta_usuario)
        actualizado = False
        for i, u in enumerate(usuarios):
            if u.get("id_usuario") == usuario.id_usuario:
                usuarios[i] = usuario.to_dict()
                actualizado = True
                break
        if not actualizado:
            usuarios.append(usuario.to_dict())
        return self._escribir_archivo(self.ruta_usuario, usuarios)

    def obtener_usuario_por_apodo(self, apodo: str) -> list[Usuario | None]:
        usuarios = self._leer_archivo(self.ruta_usuario)
        for u in usuarios:
            if u.get("apodo").lower() == apodo.lower():
                return Usuario.from_dict(u)
        return None
