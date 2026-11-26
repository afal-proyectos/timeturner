"""Diálogo 12 - Últimos 4 libros leídos (incluye el actual) y acceso a la biblioteca."""

import flet as ft

from presentacion.ui_comun import (
    AZUL,
    BLANCO,
    GRIS_BARRA,
    NEGRO,
    boton,
    tarjeta,
    texto,
)


def crear_dialogo(ui) -> ft.AlertDialog:
    def elegir(libro) -> None:
        ui.seleccionar_libro(libro)  # si hay sesión en curso, deja un aviso en Inicio
        ui.cerrar_dialogo()
        ui.navegar("01_inicio")

    def ver_toda(e) -> None:
        ui.cerrar_dialogo()
        ui.navegar("02_biblioteca_completa")

    items = []
    for r in ui.resumen_libros()[:4]:
        libro = r["libro"]
        contenido = ft.Column(
            [
                texto(libro.autor, 11),
                texto(libro.titulo, 16, negrita=True),
                ft.ProgressBar(
                    value=r["porcentaje"] / 100, color=AZUL, bgcolor=GRIS_BARRA
                ),
                texto(
                    f"{r['pagina_actual']}/{libro.total_paginas} págs · {r['porcentaje']}%",
                    11,
                ),
            ],
            spacing=3,
        )
        items.append(tarjeta(contenido, on_click=lambda e, l=libro: elegir(l)))

    if not items:
        items.append(texto("Aún no tienes libros registrados."))

    items.append(boton("Ver toda la biblioteca", ver_toda, icono=ft.Icons.MENU_BOOK))

    return ft.AlertDialog(
        modal=True,
        bgcolor=BLANCO,
        title=ft.Text("Mis últimos libros", color=NEGRO),
        content=ft.Column(
            items, tight=True, spacing=8, width=340, scroll=ft.ScrollMode.AUTO
        ),
        actions=[boton("Cerrar", lambda e: ui.cerrar_dialogo())],
    )
