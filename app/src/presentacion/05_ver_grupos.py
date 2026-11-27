"""Vista 05 - Mis grupos de lectura. Crear (14) y unirse (15) son diálogos flotantes."""

import flet as ft

from presentacion.ui_comun import boton, encabezado, tarjeta, texto


def construir(ui) -> ft.Control:
    volver = lambda e: ui.navegar("01_inicio")  # noqa: E731

    if ui.gestor_grupos is None:
        return ft.Column(
            [
                encabezado("Mis grupos", volver),
                texto("Los grupos aún no están conectados."),
            ]
        )

    yo = ui.usuario["id_usuario"]
    grupos = ui.gestor_grupos.repo.obtener_grupos_usuario(yo)

    filas = [
        encabezado("Mis grupos", volver),
        ft.Row(
            [
                boton(
                    "Crear grupo",
                    lambda e: ui.abrir_dialogo("14_crear_grupos"),
                    icono=ft.Icons.ADD,
                    expand=True,
                ),
                boton(
                    "Unirse",
                    lambda e: ui.abrir_dialogo("15_unirse_grupos"),
                    icono=ft.Icons.VPN_KEY,
                    expand=True,
                ),
            ],
            spacing=8,
        ),
    ]

    if not grupos:
        filas.append(texto("No perteneces a ningún grupo aún."))

    for g in grupos:
        rol = "Moderador" if g.admin_id == yo else "Miembro"
        contenido = ft.Column(
            [
                texto(g.nombre, 17, negrita=True),
                texto(f"{rol} · Código de acceso: {g.codigo_acceso}", 12),
                ft.Row(
                    [
                        boton(
                            "Lecturas",
                            lambda e, g=g: ui.navegar(
                                "06_ver_estadisticas_grupo", grupo=g
                            ),
                            icono=ft.Icons.PEOPLE,
                            expand=True,
                            tam=13,
                        ),
                        boton(
                            "Chat",
                            lambda e, g=g: ui.navegar("09_chat_grupo", grupo=g),
                            icono=ft.Icons.CHAT,
                            expand=True,
                            tam=13,
                        ),
                    ],
                    spacing=8,
                ),
            ],
            spacing=8,
        )
        filas.append(tarjeta(contenido))

    return ft.Column(
        filas, spacing=10, horizontal_alignment=ft.CrossAxisAlignment.STRETCH
    )
