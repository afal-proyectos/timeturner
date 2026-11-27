"""Diálogo 15 - Unirse a un grupo con su código de acceso de 6 dígitos."""

import flet as ft

from presentacion.ui_comun import BLANCO, NEGRO, ROJO, boton


def crear_dialogo(ui) -> ft.AlertDialog:
    codigo = ft.TextField(
        label="Código de 6 dígitos", max_length=6, autofocus=True, color=NEGRO
    )
    error = ft.Text("", color=ROJO, size=12)

    def unirse(e) -> None:
        exito, mensaje, _grupo = ui.gestor_grupos.unirse_a_grupo(
            codigo.value or "", ui.usuario["id_usuario"]
        )
        if exito:
            ui.cerrar_dialogo()
            ui.refrescar_vista()
        else:
            error.value = mensaje
            ui.page.update()

    return ft.AlertDialog(
        modal=True,
        bgcolor=BLANCO,
        title=ft.Text("Unirse a un grupo", color=NEGRO),
        content=ft.Column([codigo, error], tight=True, width=300),
        actions=[
            boton("Cancelar", lambda e: ui.cerrar_dialogo(), rojo=True),
            boton("Unirse", unirse),
        ],
    )
