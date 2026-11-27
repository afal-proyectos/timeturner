"""
Vista 06 - Lecturas del grupo (antes "Tablero cruzado").

Muestra a cada miembro con acceso a sus estadísticas personales (07) y a sus
últimos 4 libros leídos (08). Sin rankings ni comparaciones: la idea es compartir
lecturas, no competir. Los miembros se ordenan por apodo.
"""

import flet as ft

from presentacion.ui_comun import (
    AZUL,
    BLANCO,
    GRIS_BARRA,
    encabezado,
    tarjeta,
    texto,
)


def construir(ui, grupo) -> ft.Control:
    filas = [
        encabezado(grupo.nombre, lambda e: ui.navegar("05_ver_grupos")),
        texto("Lo que está leyendo cada miembro del grupo", 12),
    ]
    yo = ui.usuario["id_usuario"]

    for miembro in ui.miembros_grupo(grupo):
        etiqueta = miembro["apodo"] + (" (tú)" if miembro["id_usuario"] == yo else "")

        def ver_usuario(e, m=miembro) -> None:
            ui.navegar("07_ver_estadistica_amigo", grupo=grupo, miembro=m)

        boton_stats = ft.Container(
            content=ft.IconButton(
                icon=ft.Icons.BAR_CHART,
                icon_color=BLANCO,
                tooltip="Estadísticas de " + miembro["apodo"],
                on_click=ver_usuario,
            ),
            bgcolor=AZUL,
            border_radius=8,
        )

        contenido = [
            ft.Row(
                [texto(etiqueta, 17, negrita=True), boton_stats],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )
        ]

        recientes = ui.resumen_libros(miembro["id_usuario"])[:4]
        if not recientes:
            contenido.append(texto("Aún no ha registrado libros.", 12))

        for r in recientes:
            libro = r["libro"]

            def ver_libro(e, m=miembro, l=libro) -> None:
                ui.navegar(
                    "08_ver_estadistica_libro_amigo", grupo=grupo, miembro=m, libro=l
                )

            contenido.append(
                ft.Container(
                    content=ft.Column(
                        [
                            texto(libro.titulo, 14, negrita=True),
                            ft.ProgressBar(
                                value=r["porcentaje"] / 100,
                                color=AZUL,
                                bgcolor=GRIS_BARRA,
                            ),
                            texto(f"{libro.autor} · {r['porcentaje']}%", 11),
                        ],
                        spacing=3,
                    ),
                    on_click=ver_libro,
                    padding=6,
                )
            )

        filas.append(tarjeta(ft.Column(contenido, spacing=6)))

    return ft.Column(
        filas, spacing=10, horizontal_alignment=ft.CrossAxisAlignment.STRETCH
    )
