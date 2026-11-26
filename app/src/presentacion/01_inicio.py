"""Vista 01 - Inicio: saludo, libro actual, acceso a biblioteca y cronómetro."""

import flet as ft
from dominio.models_sesion import EstadoSesion

from presentacion.ui_comun import (
    AZUL,
    BLANCO,
    NEGRO,
    ROJO,
    boton,
    contenido_boton,
    tarjeta,
    texto,
)


def construir(ui) -> ft.Control:
    libro = ui.libro_activo

    reloj = ft.Text(
        ui.cronometro_texto(), size=64, weight=ft.FontWeight.BOLD, color=NEGRO
    )
    aviso = ft.Text(ui.mensaje, size=13, color=AZUL, text_align=ft.TextAlign.CENTER)

    btn_inicio = boton("Inicio", icono=ft.Icons.PLAY_ARROW, expand=True)
    btn_pausa = boton("Pausa", icono=ft.Icons.PAUSE, expand=True)
    btn_stop = boton("Stop", icono=ft.Icons.STOP, expand=True)

    def _estado_botones() -> None:
        activa = ui.sesion_activa
        btn_inicio.disabled = activa or libro is None
        btn_pausa.disabled = not activa
        btn_stop.disabled = not activa
        if ui.sesion_pausada:
            btn_pausa.content = contenido_boton("Reanudar", ft.Icons.PLAY_ARROW)
        else:
            btn_pausa.content = contenido_boton("Pausa", ft.Icons.PAUSE)

    def refrescar() -> None:
        _estado_botones()
        reloj.value = ui.cronometro_texto()
        aviso.value = ui.mensaje
        ui.page.update()

    def tick() -> None:
        reloj.value = ui.cronometro_texto()
        reloj.update()

    def al_iniciar(e) -> None:
        ui.mostrar_dialogo(dialogo_pagina_inicial(ui, refrescar))

    def al_pausar(e) -> None:
        ui.alternar_pausa()
        refrescar()

    def al_detener(e) -> None:
        ui.mostrar_dialogo(dialogo_pagina_final(ui, refrescar))

    btn_inicio.on_click = al_iniciar
    btn_pausa.on_click = al_pausar
    btn_stop.on_click = al_detener
    _estado_botones()
    ui.tick_cb = tick

    tarjeta_libro = tarjeta(
        texto(
            libro.titulo if libro else "Aún no tienes libros",
            18,
            negrita=True,
            centrado=True,
        ),
    )
    tarjeta_libro.alignment = ft.Alignment(0, 0)

    return ft.Column(
        [
            texto(f"Hola {ui.usuario['apodo']}", 26, negrita=True),
            tarjeta_libro,
            boton(
                "Biblioteca",
                lambda e: ui.abrir_dialogo("12_lista_biblioteca"),
                icono=ft.Icons.MENU_BOOK,
            ),
            ft.Container(height=30),
            ft.Row([reloj], alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([btn_inicio, btn_pausa, btn_stop], spacing=8),
            ft.Row([aviso], alignment=ft.MainAxisAlignment.CENTER),
        ],
        spacing=14,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
    )


# --------------------------------------------------------------------------
# Diálogos flotantes del cronómetro
# --------------------------------------------------------------------------
def _leer_pagina(campo: ft.TextField):
    try:
        return int((campo.value or "").strip())
    except ValueError:
        return None


def dialogo_pagina_inicial(ui, al_terminar) -> ft.AlertDialog:
    libro = ui.libro_activo
    campo = ft.TextField(
        label="Página en la que partes",
        value=str(ui.pagina_sugerida()),
        keyboard_type=ft.KeyboardType.NUMBER,
        autofocus=True,
        color=NEGRO,
    )
    error = ft.Text("", color=ROJO, size=12)

    def aceptar(e) -> None:
        pagina = _leer_pagina(campo)
        if pagina is None:
            error.value = "Ingresa un número entero."
        elif pagina < 0 or pagina > libro.total_paginas:
            error.value = f"La página debe estar entre 0 y {libro.total_paginas}."
        else:
            ui.cerrar_dialogo()
            ui.comenzar_sesion(pagina)
            al_terminar()
            return
        ui.page.update()

    def cancelar(e) -> None:
        ui.cerrar_dialogo()

    return ft.AlertDialog(
        modal=True,
        bgcolor=BLANCO,
        title=ft.Text("Página inicial", color=NEGRO),
        content=ft.Column([campo, error], tight=True),
        actions=[boton("Cancelar", cancelar, rojo=True), boton("Comenzar", aceptar)],
    )


def dialogo_pagina_final(ui, al_terminar) -> ft.AlertDialog:
    sesion, libro = ui.sesion, ui.libro_activo

    # Se congela el tiempo mientras el usuario escribe la página final.
    estaba_leyendo = sesion.estado == EstadoSesion.LEYENDO
    if estaba_leyendo:
        sesion.pausar()

    campo = ft.TextField(
        label="Página en la que terminas",
        keyboard_type=ft.KeyboardType.NUMBER,
        autofocus=True,
        color=NEGRO,
    )
    error = ft.Text("", color=ROJO, size=12)

    def aceptar(e) -> None:
        pagina = _leer_pagina(campo)
        if pagina is None:
            error.value = "Ingresa un número entero."
        elif pagina < sesion.pagina_inicio or pagina > libro.total_paginas:
            error.value = f"La página debe estar entre {sesion.pagina_inicio} y {libro.total_paginas}."
        else:
            try:
                ui.finalizar_sesion(pagina)
            except ValueError as ex:
                error.value = str(ex)
            else:
                ui.cerrar_dialogo()
                al_terminar()
                return
        ui.page.update()

    def cancelar(e) -> None:
        ui.cerrar_dialogo()
        if estaba_leyendo:
            sesion.reanudar()
        al_terminar()

    return ft.AlertDialog(
        modal=True,
        bgcolor=BLANCO,
        title=ft.Text("Página final", color=NEGRO),
        content=ft.Column([campo, error], tight=True),
        actions=[boton("Cancelar", cancelar, rojo=True), boton("Guardar", aceptar)],
    )
