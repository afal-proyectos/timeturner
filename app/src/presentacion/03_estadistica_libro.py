"""Vista 03 - Estadísticas de un libro propio (gráfico con ajuste lineal + tarjetas)."""

import flet as ft

from presentacion.estadisticas import contenido_estadistica_libro


def construir(ui, libro) -> ft.Control:
    return contenido_estadistica_libro(
        ui, libro, on_volver=lambda e: ui.navegar("02_biblioteca_completa")
    )
