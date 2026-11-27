"""Vista 08 - Avance de un libro específico de un miembro del grupo."""

import flet as ft

from presentacion.estadisticas import contenido_estadistica_libro


def construir(ui, grupo, miembro, libro) -> ft.Control:
    return contenido_estadistica_libro(
        ui,
        libro,
        on_volver=lambda e: ui.navegar("06_ver_estadisticas_grupo", grupo=grupo),
        subtitulo=f"Lectura de {miembro['apodo']}",
    )
