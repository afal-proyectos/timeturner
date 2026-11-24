import json
import os

from dominio.models_libro import Libro
from dominio.models_sesion import SesionLectura

from persistencia.repo_json import RepositorioJSON
from persistencia.repo_supabase import RepositorioSupabase
from persistencia.repositorio import IRepositorioDatos


class RepositorioHibrido(IRepositorioDatos):
    """
    Repositorio Híbrido con arquitectura Offline-First.
    Garantiza persistencia local en JSON inmediata y sincronización asíncrona/resiliente con Supabase.
    Repositorio Híbrido Offline-First con cola de sincronización persistente en disco.
    """

    def __init__(
        self,
        repo_local: RepositorioJSON,
        repo_nube: list[RepositorioSupabase | None] | None = None,
    ):
        self.local = repo_local
        self.nube = repo_nube
        self.ruta_cola = os.path.join(self.local.ruta_base, "cola_sync.json")
        self.pendientes_sync: dict[str, str] = self._cargar_cola_disk()

    # --- Gestión de la cola persistente ---
    def _cargar_cola_disk(
        self,
    ) -> dict[str, str]:
        "Cargar los UUID>S pendientes de subir a la nube desde archivos JSON"
        if os.path.exists(self.ruta_cola):
            try:
                with open(self.ruta_cola, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _guardar_cola_disk(self) -> None:
        """Persiste la lista de pendientes en disco."""
        try:
            with open(self.ruta_cola, "w", encoding="utf-8") as f:
                json.dump(self.pendientes_sync, f, indent=4)
        except Exception as e:
            print(f"[Error Cola Sync] No se pudo guardar la cola en disco: {e}")

    def _marcar_pendiente(self, id_obj: str, tipo: str) -> None:
        self.pendientes_sync[id_obj] = tipo
        self._guardar_cola_disk()

    def _desmarcar_pendiente(self, id_obj: str) -> None:
        if id_obj in self.pendientes_sync:
            del self.pendientes_sync[id_obj]
            self._guardar_cola_disk()

    def set_repositorio_nube(self, repo_nube: RepositorioSupabase) -> None:
        """Permite inyectar o actualizar la conexión a la nube dinámicamente."""
        self.nube = repo_nube

    # --- Operaciones de Libros ---

    def guardar_libro(self, libro: Libro) -> bool:
        # 1. Guardado obligatorio e inmediato en local
        exito_local = self.local.guardar_libro(libro)

        # 2. Intento de sincronización con la nube
        if self.nube:
            try:
                self.nube.guardar_libro(libro)
                self._desmarcar_pendiente(libro.id_libro)
                print(f"☁️ [Sync OK] Libro '{libro.titulo}' respaldado en Supabase.")
            except Exception:
                print(
                    f"📶 [Modo Offline] Libro '{libro.titulo}' guardado localmente. Pendiente de sincronizar."
                )
                self._marcar_pendiente(libro.id_libro, "libro")
        else:
            self._marcar_pendiente(libro.id_libro, "libro")

        return exito_local

    def obtener_libros(self, usuario_id: str) -> list[Libro]:
        """
        Prioriza la lectura local por velocidad. Si el almacenamiento local está vacío
        e hay conexión a la nube, descarga y pobla la base local.
        """
        libros_locales = self.local.obtener_libros(usuario_id)
        if not libros_locales and self.nube:
            try:
                libros_nube = self.nube.obtener_libros(usuario_id)
                for libro in libros_nube:
                    self.local.guardar_libro(libro)
                return libros_nube
            except Exception:
                print("No se ha podido encontrar los libros")

        return libros_locales

    def obtener_libro_por_id(self, id_libro: str) -> list[Libro | None]:
        libro = self.local.obtener_libro_por_id(id_libro)
        if not libro and self.nube:
            try:
                libro = self.nube.obtener_libro_por_id(id_libro)
                if libro:
                    self.local.guardar_libro(libro)
            except Exception:
                print("No se ha encontrado el libro buscado")
        return libro

    # --- Operaciones de Sesiones de Lectura ---

    def registrar_sesion(self, sesion: SesionLectura) -> bool:
        # 1. Guardar siempre primero en el almacenamiento local
        exito_local = self.local.registrar_sesion(sesion)

        # 2. Replicación en la nube
        if self.nube:
            try:
                self.nube.registrar_sesion(sesion)
                self._desmarcar_pendiente(sesion.id_sesion)
                print(
                    f"☁️ [Sync OK] Sesión {sesion.id_sesion[:8]} sincronizada con Supabase."
                )
            except Exception:
                print(
                    f"📶 [Modo Offline] Sesión {sesion.id_sesion[:8]} guardada localmente."
                )
                self._marcar_pendiente(sesion.id_sesion, "sesion")
        else:
            self._marcar_pendiente(sesion.id_sesion, "sesion")

        return exito_local

    def obtener_sesiones(self, libro_id: str) -> list[SesionLectura]:
        sesiones_locales = self.local.obtener_sesiones(libro_id)
        if not sesiones_locales and self.nube:
            try:
                sesiones_nube = self.nube.obtener_sesiones(libro_id)
                for s in sesiones_nube:
                    self.local.registrar_sesion(s)
                return sesiones_nube
            except Exception:
                print("No se han encontrado sesiones")

        return sesiones_locales

    # --- Proceso de Sincronización al recuperar conexión ---

    def sincronizar_pendientes(self) -> dict[str, int]:
        """
        Recorre todos los registros pendientes y los envía a Supabase.
        Retorna un resumen con el conteo de elementos sincronizados.
        """
        if not self.nube:
            return {"exitosos": 0, "fallidos": len(self.pendientes_sync)}

        sincronizados = 0
        ids_exitosos = []

        for id_obj, tipo in list(self.pendientes_sync.items()):
            try:
                if tipo == "libro":
                    libro = self.local.obtener_libro_por_id(id_obj)
                    if libro:
                        self.nube.guardar_libro(libro)
                        sincronizados += 1
                        ids_exitosos.append(id_obj)
                elif tipo == "sesion":
                    # Leer directamente las sesiones locales
                    sesiones_raw = self.local._leer_archivo(self.ruta_sesiones)
                    for item in sesiones_raw:
                        if item.get("id_sesion") == id_obj:
                            # Reconstruir entidad SesionLectura y subir
                            sesion = self.local.obtener_sesiones(item["libro_id"])
                            for s in sesion:
                                if s.id_sesion == id_obj:
                                    self.nube.registrar_sesion(s)
                                    sincronizados += 1
                                    ids_exitosos.append(id_obj)
                                    break
            except Exception:  # noqa: BLE001, S112
                continue

        for id_ok in ids_exitosos:
            self._desmarcar_pendiente(id_ok)

        return {"exitosos": sincronizados, "pendientes": len(self.pendientes_sync)}
