"""Componentes y colores compartidos por todas las vistas de LeerJuntos."""

import flet as ft

AZUL = "#1565C0"
ROJO = "#C62828"
NEGRO = "#000000"
BLANCO = "#FFFFFF"
GRIS_CLARO = "#F2F2F2"
GRIS_BARRA = "#D0D0D0"

# En Flet 1.x el botón se llama Button; en versiones anteriores, ElevatedButton.
_ClaseBoton = getattr(ft, "Button", None) or ft.ElevatedButton


def contenido_boton(texto: str, icono=None, tam: int = 14) -> ft.Control:
    """Contenido (icono + texto en blanco) de un botón."""
    hijos = []
    if icono:
        hijos.append(ft.Icon(icono, color=BLANCO, size=tam + 4))
    hijos.append(ft.Text(texto, color=BLANCO, size=tam))
    return ft.Row(
        hijos,
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=6,
        tight=True,
    )


def boton(
    texto: str,
    on_click=None,
    rojo: bool = False,
    icono=None,
    disabled: bool = False,
    expand: bool = False,
    tam: int = 14,
):
    """Botón estándar: azul con texto blanco, o rojo para acciones críticas."""
    return _ClaseBoton(
        content=contenido_boton(texto, icono, tam),
        bgcolor=ROJO if rojo else AZUL,
        color=BLANCO,
        on_click=on_click,
        disabled=disabled,
        expand=expand,
    )


def texto(valor: str, tam: int = 14, negrita: bool = False, centrado: bool = False):
    return ft.Text(
        valor,
        size=tam,
        color=NEGRO,
        weight=ft.FontWeight.BOLD if negrita else None,
        text_align=ft.TextAlign.CENTER if centrado else None,
    )


def tarjeta(contenido, ancho=None, alto=None, on_click=None, expand=False):
    return ft.Container(
        content=contenido,
        bgcolor=GRIS_CLARO,
        border_radius=12,
        padding=14,
        width=ancho,
        height=alto,
        on_click=on_click,
        expand=expand,
    )


def tarjeta_estadistica(titulo: str, valor: str, detalle: str = "", cuadrada=True):
    """Tarjeta con título pequeño, valor grande y detalle opcional."""
    contenido = ft.Column(
        [
            texto(titulo, 12),
            texto(valor, 24, negrita=True),
            texto(detalle, 11) if detalle else ft.Container(),
        ],
        spacing=6,
        alignment=ft.MainAxisAlignment.CENTER,
    )
    if cuadrada:
        return tarjeta(contenido, ancho=170, alto=170)
    return tarjeta(contenido)


def encabezado(titulo: str, on_volver) -> ft.Row:
    return ft.Row(
        [
            ft.IconButton(
                icon=ft.Icons.ARROW_BACK,
                icon_color=NEGRO,
                tooltip="Volver",
                on_click=on_volver,
            ),
            texto(titulo, 22, negrita=True),
        ],
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )


def fmt_minutos(minutos: float) -> str:
    total = int(round(minutos))
    horas, mins = divmod(total, 60)
    if horas:
        return f"{horas} h {mins} min"
    return f"{round(minutos, 1)} min"
