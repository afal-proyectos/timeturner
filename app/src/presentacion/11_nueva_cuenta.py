"""Diálogo 11 - Crear cuenta nueva. Cancelar y Guardar vuelven al diálogo 10."""

import flet as ft

from presentacion.ui_comun import BLANCO, NEGRO, ROJO, boton


def crear_dialogo(ui) -> ft.AlertDialog:
    correo = ft.TextField(
        label="Correo", keyboard_type=ft.KeyboardType.EMAIL, autofocus=True, color=NEGRO
    )
    apodo = ft.TextField(label="Apodo (máx. 8)", max_length=8, color=NEGRO)
    clave = ft.TextField(
        label="Contraseña (4 a 8)",
        password=True,
        can_reveal_password=True,
        max_length=8,
        color=NEGRO,
    )
    error = ft.Text("", color=ROJO, size=12)

    def cancelar(e) -> None:
        ui.abrir_dialogo("10_cuenta")

    def guardar(e) -> None:
        exito, mensaje, _usuario = ui.servicio_auth.registrar_usuario(
            correo.value or "", apodo.value or "", clave.value or ""
        )
        if not exito:
            error.value = mensaje
            ui.page.update()
            return
        ui.abrir_dialogo(
            "10_cuenta", mensaje="Cuenta creada. Ingresa con tu apodo y contraseña."
        )

    return ft.AlertDialog(
        modal=True,
        bgcolor=BLANCO,
        title=ft.Text("Nueva cuenta", color=NEGRO),
        content=ft.Column([correo, apodo, clave, error], tight=True, width=300),
        actions=[boton("Cancelar", cancelar, rojo=True), boton("Guardar", guardar)],
    )
