from dominio.models_grupo import Grupo
from dominio.models_libro import Libro
from dominio.models_mensaje import Mensaje
from dominio.models_miembro import MiembroGrupo
from dominio.models_sesion import EstadoSesion, SesionLectura
from dominio.models_usuario import Usuario
from supabase import Client, create_client

from persistencia.repositorio import IRepositorioDatos


class RepositorioSupabase(IRepositorioDatos):
    """
    Implementación concreta de IRepositorioDatos para Supabase (PostgreSQL).
    """

    def __init__(self, supabase_url: str, supabase_key: str):
        self.client: Client = create_client(supabase_url, supabase_key)

    def guardar_libro(self, libro: Libro) -> bool:
        """Inserta o actualiza un libro en la tabla 'books' usando UPSERT."""
        try:
            datos = libro.to_dict()
            response = self.client.table("books").upsert(datos).execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"[Supabase Error] No se pudo guardar el libro '{libro.titulo}': {e}")
            raise e

    def obtener_libros(self, usuario_id: str) -> list[Libro]:
        """Obtiene todos los libros pertenecientes a un usuario desde la nube."""
        try:
            response = (
                self.client.table("books")
                .select("*")
                .eq("usuario_id", usuario_id)
                .execute()
            )
            return [Libro.from_dict(item) for item in response.data]
        except Exception as e:
            print(f"[Supabase Error] Error al consultar libros de {usuario_id}: {e}")
            return []

    def obtener_libro_por_id(self, id_libro: str) -> list[Libro | None]:
        """Consulta un libro específico por su UUID."""
        try:
            response = (
                self.client.table("books")
                .select("*")
                .eq("id_libro", id_libro)
                .single()
                .execute()
            )
            if response.data:
                return Libro.from_dict(response.data)
            return None
        except Exception:
            return None

    def registrar_sesion(self, sesion: SesionLectura) -> bool:
        """Inserta o actualiza una sesión en la tabla 'reading_sessions'."""
        try:
            datos = {
                "id_sesion": sesion.id_sesion,
                "libro_id": sesion.libro_id,
                "usuario_id": sesion.usuario_id,
                "pagina_inicio": sesion.pagina_inicio,
                "pagina_fin": sesion.pagina_fin,
                "inicio_utc": sesion.inicio_utc.isoformat()
                if sesion.inicio_utc
                else None,
                "fin_utc": sesion.fin_utc.isoformat() if sesion.fin_utc else None,
                "minutos_pausa": sesion.minutos_pausa,
                "estado": sesion.estado.value,
            }
            response = self.client.table("reading_sessions").upsert(datos).execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"[Supabase Error] Error al registrar sesión {sesion.id_sesion}: {e}")
            raise e

    def obtener_sesiones(self, libro_id: str) -> list[SesionLectura | None]:
        """Recupera el historial de sesiones de un libro desde la nube."""
        try:
            response = (
                self.client.table("reading_sessions")
                .select("*")
                .eq("libro_id", libro_id)
                .execute()
            )
            sesiones: list[SesionLectura] = []
            for item in response.data:
                sesion = SesionLectura(
                    id_sesion=item["id_sesion"],
                    libro_id=item["libro_id"],
                    usuario_id=item["usuario_id"],
                    pagina_inicio=item["pagina_inicio"],
                )
                sesion.pagina_fin = item.get("pagina_fin")
                sesion.minutos_pausa = item.get("minutos_pausa", 0.0)
                sesion.estado = EstadoSesion(item.get("estado", "INACTIVA"))
                sesiones.append(sesion)
            return sesiones
        except Exception as e:
            print(f"[Supabase Error] Error al obtener sesiones: {e}")
            return []
        # ----------Tabla usuario----------

    def guardar_usuario(self, usuario: Usuario) -> bool:
        try:
            datos = {
                "id_usuario": usuario.id_usuario,
                "email": usuario.email,
                "apodo": usuario.apodo,
                "clave_hash": usuario.clave_hash,
                "rol": usuario.rol,
            }
            res = self.client.table("profiles").upsert(datos).execute()
            return len(res.data) > 0
        except Exception as e:
            print(f"[Supabase Error] No se pudo guardar el usuario: {e}")
            raise e

    def obtener_usuario_por_apodo(self, apodo: str) -> list[Usuario | None]:
        try:
            res = (
                self.client.table("profiles")
                .select("*")
                .eq("apodo", apodo)
                .single()
                .execute()
            )
            if res.data:
                return Usuario.from_dict(res.data)
            return None
        except Exception:
            return None

    # --- Gestión de Grupos y Miembros ---

    def crear_grupo(self, grupo: Grupo) -> bool:
        try:
            res = self.client.table("groups").upsert(grupo.to_dict()).execute()
            return len(res.data) > 0
        except Exception as e:
            print(f"[Supabase Error] Error al crear grupo '{grupo.nombre}': {e}")
            raise e

    def obtener_grupo_por_codigo(self, codigo_acceso: str) -> list[Grupo | None]:
        try:
            res = (
                self.client.table("groups")
                .select("*")
                .eq("codigo_acceso", codigo_acceso.upper())
                .single()
                .execute()
            )
            if res.data:
                return Grupo.from_dict(res.data)
            return None
        except Exception:
            return None

    def obtener_grupos_usuario(self, id_usuario: str) -> list[Grupo]:
        try:
            # Consultar IDs de grupos a los que pertenece el usuario
            res_m = (
                self.client.table("group_members")
                .select("id_grupo")
                .eq("id_usuario", id_usuario)
                .execute()
            )
            ids_grupos = [item["id_grupo"] for item in res_m.data]

            if not ids_grupos:
                return []

            res_g = (
                self.client.table("groups")
                .select("*")
                .in_("id_grupo", ids_grupos)
                .execute()
            )
            return [Grupo.from_dict(g) for g in res_g.data]
        except Exception as e:
            print(f"[Supabase Error] Error al obtener grupos del usuario: {e}")
            return []

    def agregar_miembro_grupo(self, miembro: MiembroGrupo) -> bool:
        try:
            res = self.client.table("group_members").upsert(miembro.to_dict()).execute()
            return len(res.data) > 0
        except Exception as e:
            print(f"[Supabase Error] Error al agregar miembro: {e}")
            raise e

    def obtener_miembros_grupo(self, id_grupo: str) -> list[str]:
        try:
            res = (
                self.client.table("group_members")
                .select("id_usuario")
                .eq("id_grupo", id_grupo)
                .execute()
            )
            return [item["id_usuario"] for item in res.data]
        except Exception as e:
            print(f"[Supabase Error] Error al obtener miembros: {e}")
            return []

    # --- Gestión de Chat Grupal ---

    def guardar_mensaje(self, mensaje: Mensaje) -> bool:
        try:
            res = self.client.table("messages").upsert(mensaje.to_dict()).execute()
            return len(res.data) > 0
        except Exception as e:
            print(f"[Supabase Error] Error al guardar mensaje: {e}")
            raise e

    def obtener_mensajes_grupo(self, grupo_id: str) -> list[Mensaje]:
        try:
            res = (
                self.client.table("messages")
                .select("*")
                .eq("grupo_id", grupo_id)
                .order("fecha_envio", desc=False)
                .execute()
            )
            return [Mensaje.from_dict(m) for m in res.data]
        except Exception as e:
            print(f"[Supabase Error] Error al consultar chat: {e}")
            return []

    def eliminar_mensaje(self, id_mensaje: str) -> bool:
        try:
            res = (
                self.client.table("messages")
                .delete()
                .eq("id_mensaje", id_mensaje)
                .execute()
            )
            return len(res.data) > 0
        except Exception as e:
            print(f"[Supabase Error] Error al eliminar mensaje: {e}")
            return False
