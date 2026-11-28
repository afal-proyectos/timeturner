"""Diálogo 10 - Ingreso con usuario existente (o paso a crear cuenta)."""

import flet as ft

from presentacion.ui_comun import AZUL, BLANCO, NEGRO, ROJO, boton


def crear_dialogo(ui, mensaje: str = "") -> ft.AlertDialog:
    error = ft.Text("", color=ROJO, size=12)

    def ingresar(e) -> None:
        exito, mensaje, usuario = ui.servicio_auth.iniciar_sesion(
            apodo.value or "", clave.value or ""
        )
        if not exito:
            error.value = mensaje
            ui.page.update()
            return
        ui.iniciar_sesion_usuario(usuario)

    def nueva_cuenta(e) -> None:
        ui.abrir_dialogo("11_nueva_cuenta")

    apodo = ft.TextField(label="Apodo", max_length=8, autofocus=True, color=NEGRO)
    clave = ft.TextField(
        label="Contraseña",
        password=True,
        can_reveal_password=True,
        max_length=8,
        color=NEGRO,
        on_submit=ingresar,
    )

    return ft.AlertDialog(
        modal=True,
        bgcolor=BLANCO,
        title=ft.Text("LeerJuntos", color=NEGRO),
        content=ft.Column(
            [ft.Text(mensaje, color=AZUL, size=12), apodo, clave, error],
            tight=True,
            width=300,
        ),
        actions=[boton("Crear cuenta", nueva_cuenta), boton("Ingresar", ingresar)],
    )
