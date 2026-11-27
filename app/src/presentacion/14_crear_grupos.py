"""Diálogo 14 - Crear un grupo nuevo (quien lo crea queda como moderador)."""

import flet as ft

from presentacion.ui_comun import BLANCO, NEGRO, ROJO, boton


def crear_dialogo(ui) -> ft.AlertDialog:
    nombre = ft.TextField(label="Nombre del grupo", autofocus=True, color=NEGRO)
    error = ft.Text("", color=ROJO, size=12)

    def crear(e) -> None:
        exito, mensaje, _grupo = ui.gestor_grupos.crear_grupo(
            nombre.value or "", ui.usuario["id_usuario"]
        )
        if exito:
            ui.cerrar_dialogo()
            ui.refrescar_vista()  # la lista de grupos (05) se actualiza
        else:
            error.value = mensaje
            ui.page.update()

    return ft.AlertDialog(
        modal=True,
        bgcolor=BLANCO,
        title=ft.Text("Crear grupo", color=NEGRO),
        content=ft.Column([nombre, error], tight=True, width=300),
        actions=[
            boton("Cancelar", lambda e: ui.cerrar_dialogo(), rojo=True),
            boton("Crear", crear),
        ],
    )
