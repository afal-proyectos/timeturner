from persistencia.repositorio import IRepositorioDatos

from dominio.models_grupo import Grupo
from dominio.models_mensaje import Mensaje
from dominio.models_miembro import MiembroGrupo


class GestorGrupos:
    """Servicio de dominio para gestionar comunidades, tableros cruzados y chat grupal."""

    def __init__(self, repositorio: IRepositorioDatos):
        self.repo = repositorio

    def crear_grupo(
        self, nombre: str, admin_id: str
    ) -> tuple[bool, str, list[Grupo | None]]:
        nombre = nombre.strip()
        if not nombre:
            return False, "El nombre del grupo no puede estar vacío.", None

        grupo = Grupo(nombre=nombre, admin_id=admin_id)

        # Guardar grupo e inscribir al administrador como primer miembro
        if self.repo.crear_grupo(grupo):
            miembro_admin = MiembroGrupo(id_grupo=grupo.id_grupo, id_usuario=admin_id)
            self.repo.agregar_miembro_grupo(miembro_admin)
            return (
                True,
                f"¡Grupo '{grupo.nombre}' creado con código {grupo.codigo_acceso}!",
                grupo,
            )

        return False, "Error al crear el grupo.", None

    def unirse_a_grupo(
        self, codigo_acceso: str, id_usuario: str
    ) -> tuple[bool, str, list[Grupo | None]]:
        codigo_acceso = codigo_acceso.strip().upper()
        grupo = self.repo.obtener_grupo_por_codigo(codigo_acceso)

        if not grupo:
            return False, "El código de acceso no es válido.", None

        miembros_ids = self.repo.obtener_miembros_grupo(grupo.id_grupo)
        if id_usuario in miembros_ids:
            return False, "Ya eres miembro de este grupo.", grupo

        miembro = MiembroGrupo(id_grupo=grupo.id_grupo, id_usuario=id_usuario)
        self.repo.agregar_miembro_grupo(miembro)
        return True, f"¡Te has unido exitosamente a '{grupo.nombre}'!", grupo

    def obtener_tablero_cruzado(self, id_grupo: str) -> list[dict[str, object]]:
        """
        Genera los datos del tablero cruzado respetando la visión de transparencia
        sin competencia ni rankings punitivos (HU-4.2).
        """
        miembros_ids = self.repo.obtener_miembros_grupo(id_grupo)
        tablero: list[dict[str, object]] = []

        for uid in miembros_ids:
            usuario = self.repo.obtener_usuario_por_apodo("")
            libros = self.repo.obtener_libros(uid)
            total_libros = len(libros)
            total_horas = 0.0
            lecturas_activas = []

            for libro in libros:
                sesiones = self.repo.obtener_sesiones(libro.id_libro)
                for s in sesiones:
                    total_horas += s.calcular_minutos_netos() / 60.0

                # Obtener la página más avanzada de cada libro
                paginas_validas = [
                    s.pagina_fin for s in sesiones if s.pagina_fin is not None
                ]
                pag_actual = max(paginas_validas) if paginas_validas else 0
                pct = libro.calcular_porcentaje_avance(pag_actual)
                lecturas_activas.append(
                    {
                        "titulo": libro.titulo,
                        "autor": libro.autor,
                        "porcentaje": pct,
                        "pagina_actual": pag_actual,
                        "total_paginas": libro.total_paginas,
                    }
                )

            tablero.append(
                {
                    "usuario_id": uid,
                    "total_libros": total_libros,
                    "total_horas_leidas": round(total_horas, 2),
                    "lecturas_activas": lecturas_activas,
                }
            )

        return tablero

    def enviar_mensaje(
        self, grupo_id: str, usuario_id: str, texto_o_sticker: str, tipo: str = "TEXTO"
    ) -> bool:
        mensaje = Mensaje(
            grupo_id=grupo_id,
            usuario_id=usuario_id,
            informacion=texto_o_sticker,
            tipo=tipo,
        )
        return self.repo.guardar_mensaje(mensaje)

    def obtener_chat_grupo(self, grupo_id: str) -> list[Mensaje]:
        return self.repo.obtener_mensajes_grupo(grupo_id)

    def moderar_eliminar_mensaje(
        self, id_mensaje: str, usuario_solicitante_id: str, grupo_id: str
    ) -> tuple[bool, str]:
        """Solo el Administrador del grupo puede borrar mensajes (HU-4.3)."""
        grupos = self.repo.obtener_grupos_usuario(usuario_solicitante_id)
        es_admin = any(
            g.id_grupo == grupo_id and g.admin_id == usuario_solicitante_id
            for g in grupos
        )

        if not es_admin:
            return (
                False,
                "Solo el Administrador del grupo puede moderar o eliminar mensajes.",
            )

        if self.repo.eliminar_mensaje(id_mensaje):
            return True, "Mensaje eliminado por el moderador."
        return False, "No se pudo eliminar el mensaje."
