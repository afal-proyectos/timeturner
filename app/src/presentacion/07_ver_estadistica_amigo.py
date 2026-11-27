"""Vista 07 - Estadísticas personales de un miembro del grupo."""

from datetime import UTC, datetime

import flet as ft

from presentacion.estadisticas import contenido_estadistica_usuario


def construir(ui, grupo, miembro) -> ft.Control:
    anio = datetime.now(UTC).year
    return contenido_estadistica_usuario(
        ui,
        miembro["id_usuario"],
        f"{miembro['apodo']} · {anio}",
        on_volver=lambda e: ui.navegar("06_ver_estadisticas_grupo", grupo=grupo),
    )
