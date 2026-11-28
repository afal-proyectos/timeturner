import json
import os

from dominio.models_grupo import Grupo
from dominio.models_libro import Libro
from dominio.models_mensaje import Mensaje
from dominio.models_miembro import MiembroGrupo
from dominio.models_sesion import EstadoSesion, SesionLectura
from dominio.models_usuario import Usuario

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
        repo_nube: RepositorioSupabase | None = None,
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

    def obtener_libro_por_id(self, id_libro: str) -> Libro | None:
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

    # --- Operaciones de Usuarios ---

    def guardar_usuario(self, usuario: Usuario) -> bool:
        """Guarda el usuario localmente en JSON y sincroniza con Supabase."""
        # 1. Guardar primero en el almacenamiento local (JSON)
        exito_local = self.local.guardar_usuario(usuario)

        # 2. Replicar en Supabase si hay conexión disponible
        if self.nube:
            try:
                self.nube.guardar_usuario(usuario)
                self._desmarcar_pendiente(usuario.id_usuario)
                print(
                    f"☁️ [Sync OK] Perfil de '{usuario.apodo}' respaldado en Supabase."
                )
            except Exception:
                print(
                    f"📶 [Modo Offline] Perfil de '{usuario.apodo}' guardado localmente."
                )
                self._marcar_pendiente(usuario.id_usuario, "usuario")
        else:
            self._marcar_pendiente(usuario.id_usuario, "usuario")

        return exito_local

    def obtener_usuario_por_apodo(self, apodo: str) -> Usuario | None:
        """Busca el usuario en el almacenamiento local; si no existe, lo busca en la nube."""
        # 1. Buscar primero en local para máxima velocidad
        usuario = self.local.obtener_usuario_por_apodo(apodo)

        # 2. Si no se encuentra en JSON pero hay conexión a la nube, consultar Supabase
        if not usuario and self.nube:
            try:
                usuario = self.nube.obtener_usuario_por_apodo(apodo)
                if usuario:
                    # Descargar y guardar localmente para futuras consultas sin red
                    self.local.guardar_usuario(usuario)
            except Exception as e:
                print(f"No se a encontrado el apodo: {e}")

        return usuario

    def obtener_usuario_por_id(self, id_usuario: str) -> Usuario | None:
        usuario = self.local.obtener_usuario_por_id(id_usuario)
        if not usuario and self.nube:
            try:
                usuario = self.nube.obtener_usuario_por_id(id_usuario)
                if usuario:
                    self.local.guardar_usuario(usuario)
            except Exception as e:
                print(f"No se ha encontrado el usuario: {e}")
        return usuario

    # --- Operaciones de Grupos y Miembros ---

    def crear_grupo(self, grupo: Grupo) -> bool:
        exito_local = self.local.crear_grupo(grupo)
        if self.nube:
            try:
                self.nube.crear_grupo(grupo)
                self._desmarcar_pendiente(grupo.id_grupo)
                print(f"☁️ [Sync OK] Grupo '{grupo.nombre}' creado en Supabase.")
            except Exception:
                self._marcar_pendiente(grupo.id_grupo, "grupo")
        else:
            self._marcar_pendiente(grupo.id_grupo, "grupo")
        return exito_local

    def obtener_grupo_por_codigo(self, codigo_acceso: str) -> Grupo | None:
        grupo = self.local.obtener_grupo_por_codigo(codigo_acceso)
        if not grupo and self.nube:
            try:
                grupo = self.nube.obtener_grupo_por_codigo(codigo_acceso)
                if grupo:
                    self.local.crear_grupo(grupo)
            except Exception as e:
                print(f"error{e}")
        return grupo

    def obtener_grupos_usuario(self, id_usuario: str) -> list[Grupo]:
        grupos = self.local.obtener_grupos_usuario(id_usuario)
        if not grupos and self.nube:
            try:
                grupos = self.nube.obtener_grupos_usuario(id_usuario)
                for g in grupos:
                    self.local.crear_grupo(g)
            except Exception as e:
                print(f"error{e}")
        return grupos

    def agregar_miembro_grupo(self, miembro: MiembroGrupo) -> bool:
        exito_local = self.local.agregar_miembro_grupo(miembro)
        if self.nube:
            try:
                self.nube.agregar_miembro_grupo(miembro)
                self._desmarcar_pendiente(f"{miembro.id_grupo}_{miembro.id_usuario}")
            except Exception:
                self._marcar_pendiente(
                    f"{miembro.id_grupo}_{miembro.id_usuario}", "miembro"
                )
        else:
            self._marcar_pendiente(
                f"{miembro.id_grupo}_{miembro.id_usuario}", "miembro"
            )
        return exito_local

    def obtener_miembros_grupo(self, id_grupo: str) -> list[str]:
        miembros = self.local.obtener_miembros_grupo(id_grupo)
        if not miembros and self.nube:
            try:
                miembros = self.nube.obtener_miembros_grupo(id_grupo)
                for uid in miembros:
                    self.local.agregar_miembro_grupo(MiembroGrupo(id_grupo, uid))
            except Exception as e:
                print(f"error{e}")
        return miembros

    # --- Operaciones de Chat Grupal ---

    def guardar_mensaje(self, mensaje: Mensaje) -> bool:
        exito_local = self.local.guardar_mensaje(mensaje)
        if self.nube:
            try:
                self.nube.guardar_mensaje(mensaje)
                self._desmarcar_pendiente(mensaje.id_mensaje)
            except Exception:
                self._marcar_pendiente(mensaje.id_mensaje, "mensaje")
        else:
            self._marcar_pendiente(mensaje.id_mensaje, "mensaje")
        return exito_local

    def obtener_mensajes_grupo(self, grupo_id: str) -> list[Mensaje]:
        mensajes = self.local.obtener_mensajes_grupo(grupo_id)
        if not mensajes and self.nube:
            try:
                mensajes = self.nube.obtener_mensajes_grupo(grupo_id)
                for m in mensajes:
                    self.local.guardar_mensaje(m)
            except Exception as e:
                print(f"error{e}")
        return mensajes

    def eliminar_mensaje(self, id_mensaje: str) -> bool:
        exito_local = self.local.eliminar_mensaje(id_mensaje)
        if self.nube:
            try:
                self.nube.eliminar_mensaje(id_mensaje)
            except Exception as e:
                print(f"error{e}")
        return exito_local

    # --- Proceso de Sincronización al recuperar conexión ---

    def sincronizar_pendientes(self) -> dict[str, int]:
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
                        ids_exitosos.append(id_obj)
                        sincronizados += 1

                elif tipo == "sesion":
                    sesiones_raw = self.local._leer_archivo(self.local.ruta_sesiones)
                    for item in sesiones_raw:
                        if item.get("id_sesion") == id_obj:
                            for s in self.local.obtener_sesiones(item["libro_id"]):
                                if s.id_sesion == id_obj:
                                    self.nube.registrar_sesion(s)
                                    ids_exitosos.append(id_obj)
                                    sincronizados += 1
                                    break
                            break

                elif tipo == "usuario":
                    usuarios_raw = self.local._leer_archivo(self.local.ruta_usuario)
                    for item in usuarios_raw:
                        if item.get("id_usuario") == id_obj:
                            self.nube.guardar_usuario(Usuario.from_dict(item))
                            ids_exitosos.append(id_obj)
                            sincronizados += 1
                            break

                elif tipo == "grupo":
                    grupos_raw = self.local._leer_archivo(self.local.ruta_grupos)
                    for item in grupos_raw:
                        if item.get("id_grupo") == id_obj:
                            self.nube.crear_grupo(Grupo.from_dict(item))
                            ids_exitosos.append(id_obj)
                            sincronizados += 1
                            break

                elif tipo == "miembro":
                    miembros_raw = self.local._leer_archivo(self.local.ruta_miembros)
                    for item in miembros_raw:
                        key = f"{item.get('id_grupo')}_{item.get('id_usuario')}"
                        if key == id_obj:
                            self.nube.agregar_miembro_grupo(
                                MiembroGrupo.from_dict(item)
                            )
                            ids_exitosos.append(id_obj)
                            sincronizados += 1
                            break

                elif tipo == "mensaje":
                    mensajes_raw = self.local._leer_archivo(self.local.ruta_mensajes)
                    for item in mensajes_raw:
                        if item.get("id_mensaje") == id_obj:
                            self.nube.guardar_mensaje(Mensaje.from_dict(item))
                            ids_exitosos.append(id_obj)
                            sincronizados += 1
                            break

            except Exception as e:
                print(f"error{e}")

        for id_ok in ids_exitosos:
            self._desmarcar_pendiente(id_ok)

        return {"exitosos": sincronizados, "pendientes": len(self.pendientes_sync)}
