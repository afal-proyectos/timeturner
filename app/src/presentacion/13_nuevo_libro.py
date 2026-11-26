"""Diálogo 13 - Registrar un libro nuevo."""

import flet as ft

from presentacion.ui_comun import BLANCO, NEGRO, ROJO, boton


def crear_dialogo(ui) -> ft.AlertDialog:
    titulo = ft.TextField(label="Título", autofocus=True, color=NEGRO)
    autor = ft.TextField(label="Autor", color=NEGRO)
    genero = ft.TextField(label="Género literario", color=NEGRO)
    paginas = ft.TextField(
        label="Total de páginas", keyboard_type=ft.KeyboardType.NUMBER, color=NEGRO
    )
    error = ft.Text("", color=ROJO, size=12)

    def cancelar(e) -> None:
        ui.cerrar_dialogo()

    def guardar(e) -> None:
        if not (titulo.value or "").strip() or not (autor.value or "").strip():
            error.value = "El título y el autor son obligatorios."
            ui.page.update()
            return
        try:
            total = int((paginas.value or "").strip())
            libro = ui.controlador.registrar_libro(
                usuario_id=ui.usuario["id_usuario"],
                titulo=titulo.value.strip(),
                autor=autor.value.strip(),
                genero=(genero.value or "").strip(),
                total_paginas=total,
            )
        except ValueError as ex:
            # Cubre tanto un número inválido como "páginas <= 0" del modelo Libro.
            error.value = (
                str(ex)
                if "páginas" in str(ex)
                else "Ingresa un total de páginas válido."
            )
            ui.page.update()
            return

        if ui.libro_activo is None:
            ui.libro_activo = libro
        ui.cerrar_dialogo()
        ui.refrescar_vista()

    return ft.AlertDialog(
        modal=True,
        bgcolor=BLANCO,
        title=ft.Text("Nuevo libro", color=NEGRO),
        content=ft.Column(
            [titulo, autor, genero, paginas, error], tight=True, width=300
        ),
        actions=[boton("Cancelar", cancelar, rojo=True), boton("Guardar", guardar)],
    )
