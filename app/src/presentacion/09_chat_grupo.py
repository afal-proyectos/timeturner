"""Vista 09 - Chat del grupo: texto, mensajes de ánimo predefinidos y moderación."""

import flet as ft

from presentacion.ui_comun import (
    AZUL,
    GRIS_CLARO,
    NEGRO,
    ROJO,
    boton,
    encabezado,
    tarjeta,
    texto,
)

# Mensajes de ánimo predefinidos: (etiqueta del botón, mensaje enviado)
ANIMOS = [
    ("👏 ¡Dale!", "👏 ¡Excelente ritmo de lectura!"),
    ("📚 ¡Gran libro!", "📚 ¡Excelente elección de libro!"),
    ("⭐ ¡Ánimo!", "⭐ ¡Sigue así, vas muy bien!"),
]


def construir(ui, grupo) -> ft.Control:
    gestor = ui.gestor_grupos
    yo = ui.usuario["id_usuario"]
    es_moderador = grupo.admin_id == yo

    lista = ft.Column(spacing=6)
    campo = ft.TextField(label="Escribe un mensaje...", color=NEGRO, expand=True)

    def pintar() -> None:
        """Reconstruye la lista de mensajes (sin actualizar la página)."""
        lista.controls.clear()
        mensajes = gestor.obtener_chat_grupo(grupo.id_grupo)
        if not mensajes:
            lista.controls.append(texto("Aún no hay mensajes. ¡Anima al grupo!", 12))
        for m in mensajes:
            autor = "Tú" if m.usuario_id == yo else ui.apodo_de(m.usuario_id)
            fila = [
                ft.Column(
                    [texto(autor, 11, negrita=True), texto(m.informacion, 14)],
                    spacing=2,
                    expand=True,
                )
            ]
            if es_moderador:
                fila.append(
                    ft.IconButton(
                        icon=ft.Icons.DELETE,
                        icon_color=ROJO,
                        tooltip="Eliminar mensaje",
                        on_click=lambda e, mid=m.id_mensaje: borrar(mid),
                    )
                )
            lista.controls.append(tarjeta(ft.Row(fila)))

    def cargar() -> None:
        pintar()
        ui.page.update()

    def enviar(contenido: str, tipo: str) -> None:
        gestor.enviar_mensaje(grupo.id_grupo, yo, contenido, tipo=tipo)
        cargar()

    def enviar_texto(e) -> None:
        valor = (campo.value or "").strip()
        if valor:
            campo.value = ""
            enviar(valor, "TEXTO")

    def borrar(id_mensaje) -> None:
        gestor.moderar_eliminar_mensaje(id_mensaje, yo, grupo.id_grupo)
        cargar()

    campo.on_submit = enviar_texto

    cabecera = ft.Row(
        [
            ft.Container(
                content=encabezado(
                    f"Chat: {grupo.nombre}", lambda e: ui.navegar("05_ver_grupos")
                ),
                expand=True,
            ),
            ft.IconButton(
                icon=ft.Icons.REFRESH,
                icon_color=AZUL,
                tooltip="Actualizar",
                on_click=lambda e: cargar(),
            ),
        ]
    )

    animos = ft.Row(
        [
            boton(etiqueta, lambda e, t=msg: enviar(t, "STICKER"), tam=12)
            for etiqueta, msg in ANIMOS
        ],
        scroll=ft.ScrollMode.AUTO,
    )

    vista = ft.Column(
        [
            cabecera,
            lista,
            animos,
            ft.Row([campo, boton("Enviar", enviar_texto)]),
        ],
        spacing=10,
    )
    pintar()
    return vista
