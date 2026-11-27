"""Vista 04 - Estadísticas personales del usuario (año en curso)."""

from datetime import UTC, datetime

import flet as ft

from presentacion.estadisticas import contenido_estadistica_usuario


def construir(ui) -> ft.Control:
    anio = datetime.now(UTC).year
    return contenido_estadistica_usuario(
        ui,
        ui.usuario["id_usuario"],
        f"Mis estadísticas {anio}",
        on_volver=lambda e: ui.navegar("01_inicio"),
    )
