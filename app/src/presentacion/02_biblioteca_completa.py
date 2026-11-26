"""Vista 02 - Biblioteca completa (del último leído al más antiguo)."""

import flet as ft

from presentacion.ui_comun import (
    AZUL,
    BLANCO,
    GRIS_BARRA,
    NEGRO,
    encabezado,
    tarjeta,
    texto,
)


def construir(ui) -> ft.Control:
    filas = [encabezado("Biblioteca", lambda e: ui.navegar("01_inicio"))]
    resumen = ui.resumen_libros()

    if not resumen:
        filas.append(texto("Aún no hay libros registrados."))

    for r in resumen:
        libro = r["libro"]

        def elegir(e, libro=libro) -> None:
            ui.seleccionar_libro(libro)
            ui.navegar("01_inicio")

        def ver_estadisticas(e, libro=libro) -> None:
            ui.navegar("03_estadistica_libro", libro=libro)

        contenido = ft.Column(
            [
                texto(libro.autor, 12),
                texto(libro.titulo, 17, negrita=True),
                ft.ProgressBar(
                    value=r["porcentaje"] / 100, color=AZUL, bgcolor=GRIS_BARRA
                ),
                texto(f"{r['porcentaje']}%", 12),
            ],
            spacing=4,
        )
        boton_stats = ft.Container(
            content=ft.IconButton(
                icon=ft.Icons.SHOW_CHART,
                icon_color=BLANCO,
                tooltip="Estadísticas del libro",
                on_click=ver_estadisticas,
            ),
            bgcolor=AZUL,
            border_radius=8,
        )
        filas.append(
            ft.Row(
                [tarjeta(contenido, on_click=elegir, expand=True), boton_stats],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )

    return ft.Column(filas, spacing=10)
